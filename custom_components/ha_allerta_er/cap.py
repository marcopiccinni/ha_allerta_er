"""CAP 1.2 client for the Allerta Emilia-Romagna integration.

Fetches and parses the public CAP document published by AllertaMeteoER
(Regione Emilia-Romagna). The document contains a single ``<alert>`` with one
alert-level ``<note>`` and one ``<info>`` block per alert area; the integration
exposes one config entry per area.

Verified live behaviour (see ``docs/ARCHITECTURE.md``):

* ``GET /o/xmlcap`` -> ``application/xml``, CAP 1.2, ~18.7 kB, gzip via CDN.
* No ``ETag`` / ``Last-Modified`` headers, so no conditional requests.
* Timestamps use the ``<iso>[<Zone>]`` form; the bracketed zone must be
  stripped before :func:`datetime.datetime.fromisoformat`.
"""

from __future__ import annotations

import asyncio
import logging
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Final

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CAP_URL, DOMAIN, FEED_TTL, USER_AGENT

_LOGGER = logging.getLogger(__name__)

_TIMEOUT = aiohttp.ClientTimeout(total=30)

CAP_NAMESPACE: Final = "urn:oasis:names:tc:emergency:cap:1.2"
_NS: Final = {"cap": CAP_NAMESPACE}

# CAP ``<parameter><valueName>`` -> entity key used by the sensor platform.
PARAMETER_KEYS: Final = {
    "IDRAULICO": "idraulico",
    "IDROGEOLOGICO": "idrogeologico",
    "TEMPORALI": "temporali",
    "VENTO": "vento",
    "TEMPERATURE_ESTREME": "temperature_estreme",
    "NEVE": "neve",
    "GHIACCIO_PIOGGIA_CHE_GELA": "pioggia_che_gela",
    "STATO_MARE": "stato_mare",
    "MAREGGIATE": "mareggiate",
}

# Relative severity for merging multi-horizon CAP parameters (e.g. ``_2436``).
_LEVEL_RANK: Final = {
    "verde": 0,
    "bianco": 0,
    "giallo": 1,
    "arancione": 2,
    "rosso": 3,
}


def parse_timestamp(value: str | None) -> datetime | None:
    """Parse a CAP timestamp (``<iso>[<Zone>]``) into an aware datetime."""
    if not value:
        return None
    text = value.strip()
    # CAP 1.2 appends the IANA zone in square brackets, e.g.
    # ``2026-10-15T00:00+02:00[Europe/Rome]``; fromisoformat rejects it.
    if "[" in text:
        text = text.split("[", 1)[0].strip()
    if not text:
        return None
    if text[-1] in ("Z", "z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed


def _normalize(value: str | None) -> str | None:
    """Normalize an alert level (``VERDE`` -> ``verde``, empty -> ``None``)."""
    if value is None:
        return None
    value = value.strip().lower()
    return value or None


def _parameter_base_name(value_name: str) -> str | None:
    """Map a CAP ``valueName`` to a known :data:`PARAMETER_KEYS` entry.

    AllertaMeteoER used bare names (``IDRAULICO``) until Nov 2026; the feed then
    switched to suffixed horizons (``IDRAULICO_2436``, ``IDRAULICO_1224``, …).
    """
    if value_name in PARAMETER_KEYS:
        return value_name
    if "_" in value_name:
        base, suffix = value_name.rsplit("_", 1)
        if suffix.isdigit() and base in PARAMETER_KEYS:
            return base
    return None


def _merge_level(current: str | None, new: str | None) -> str | None:
    """Keep the more severe of two normalized alert levels."""
    if new is None:
        return current
    if current is None:
        return new
    if _LEVEL_RANK.get(new, -1) > _LEVEL_RANK.get(current, -1):
        return new
    return current


def _ingest_parameters(
    info: ET.Element, area: str
) -> dict[str, str | None]:
    """Parse and merge ``<parameter>`` blocks for one ``<info>`` area."""
    parameters: dict[str, str | None] = {}
    recognized_bases: set[str] = set()
    unrecognized: set[str] = set()

    for parameter in info.findall("cap:parameter", _NS):
        raw_name = _text(parameter, "cap:valueName")
        if not raw_name:
            continue
        base = _parameter_base_name(raw_name)
        if base is None:
            unrecognized.add(raw_name)
            continue
        recognized_bases.add(base)
        value = _normalize(_text(parameter, "cap:value"))
        parameters[base] = _merge_level(parameters.get(base), value)

    if unrecognized:
        _LOGGER.warning(
            "Unrecognized CAP parameter valueName in area %s: %s",
            area,
            ", ".join(sorted(unrecognized)),
        )

    for base in PARAMETER_KEYS:
        if base not in recognized_bases:
            parameters[base] = "verde"

    return parameters


def _text(element: ET.Element | None, path: str) -> str | None:
    """Return the stripped text of ``path`` under ``element`` (``None`` if empty)."""
    if element is None:
        return None
    value = element.findtext(path, namespaces=_NS)
    if value is None:
        return None
    value = value.strip()
    return value or None


@dataclass(slots=True)
class AreaInfo:
    """Alert data for a single area (one ``<info>`` block)."""

    area: str
    event: str | None = None
    onset: datetime | None = None
    expires: datetime | None = None
    parameters: dict[str, str | None] = field(default_factory=dict)


@dataclass(slots=True)
class AlertFeed:
    """Snapshot of the CAP document."""

    identifier: str | None = None
    sent: datetime | None = None
    status: str | None = None
    msg_type: str | None = None
    source: str | None = None
    scope: str | None = None
    note: str | None = None
    language: str | None = None
    areas: dict[str, AreaInfo] = field(default_factory=dict)

    def area(self, area: str) -> AreaInfo | None:
        """Return the ``<info>`` block of ``area``, if present."""
        return self.areas.get(area)


def parse_cap(xml_bytes: bytes) -> AlertFeed:
    """Parse a CAP 1.2 document into an :class:`AlertFeed`."""
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as err:
        raise ValueError(f"Malformed CAP document: {err}") from err

    feed = AlertFeed(
        identifier=_text(root, "cap:identifier"),
        sent=parse_timestamp(_text(root, "cap:sent")),
        status=_text(root, "cap:status"),
        msg_type=_text(root, "cap:msgType"),
        source=_text(root, "cap:source"),
        scope=_text(root, "cap:scope"),
        note=_text(root, "cap:note"),
    )

    for info in root.findall("cap:info", _NS):
        area = _text(info, "cap:area/cap:areaDesc")
        if not area:
            continue

        if feed.language is None:
            feed.language = _text(info, "cap:language")

        parameters = _ingest_parameters(info, area)

        feed.areas[area] = AreaInfo(
            area=area,
            event=_normalize(_text(info, "cap:event")),
            onset=parse_timestamp(_text(info, "cap:onset")),
            expires=parse_timestamp(_text(info, "cap:expires")),
            parameters=parameters,
        )

    if not feed.areas:
        raise ValueError("CAP document contains no <info> area")
    return feed


async def async_fetch_cap(session: aiohttp.ClientSession) -> AlertFeed:
    """Fetch and parse the CAP document."""
    async with session.get(
        CAP_URL, headers={"User-Agent": USER_AGENT}, timeout=_TIMEOUT
    ) as response:
        response.raise_for_status()
        payload = await response.read()
    return parse_cap(payload)


class CapFeedCache:
    """Shared, short-lived cache around the CAP document.

    Every area comes from the same document, so a burst of area coordinators
    refreshing at (almost) the same time results in one HTTP request.
    """

    def __init__(self, hass: HomeAssistant) -> None:
        self._session = async_get_clientsession(hass)
        self._feed: AlertFeed | None = None
        self._timestamp = 0.0
        self._lock = asyncio.Lock()

    def _is_fresh(self) -> bool:
        return (
            self._feed is not None
            and (time.monotonic() - self._timestamp) < FEED_TTL.total_seconds()
        )

    async def async_get(self, force: bool = False) -> AlertFeed:
        """Return the cached feed, fetching it when stale (or forced)."""
        if not force and self._is_fresh():
            assert self._feed is not None
            return self._feed

        async with self._lock:
            if force or not self._is_fresh():
                self._feed = await async_fetch_cap(self._session)
                self._timestamp = time.monotonic()
            assert self._feed is not None
            return self._feed


def async_get_feed_cache(hass: HomeAssistant) -> CapFeedCache:
    """Return the shared, per-instance CAP feed cache."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    cache = domain_data.get("feed")
    if not isinstance(cache, CapFeedCache):
        cache = CapFeedCache(hass)
        domain_data["feed"] = cache
    return cache
