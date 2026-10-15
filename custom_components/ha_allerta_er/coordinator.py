"""Data update coordinator for the Allerta Emilia-Romagna integration."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .cap import PARAMETER_KEYS, CapFeedCache, async_get_feed_cache
from .const import (
    CONF_AREA,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

# Alert levels below which the area is considered in a normal situation.
NORMAL_LEVELS: frozenset[str] = frozenset({"verde", "bianco"})


def area_label(area: str) -> str:
    """Return a short, human friendly area label (``Emil-A1`` -> ``A1``)."""
    return area.removeprefix("Emil-")


@dataclass(slots=True)
class AreaAlertData:
    """Snapshot of one area's alert state."""

    area: str
    label: str
    identifier: str | None = None
    sent: datetime | None = None
    status: str | None = None
    msg_type: str | None = None
    source: str | None = None
    scope: str | None = None
    note: str | None = None
    event: str | None = None
    onset: datetime | None = None
    expires: datetime | None = None
    parameters: dict[str, str | None] = field(default_factory=dict)

    def parameter(self, key: str) -> str | None:
        """Return the value of the CAP parameter mapped to ``key``."""
        for name, mapped in PARAMETER_KEYS.items():
            if mapped == key:
                return self.parameters.get(name)
        return None

    @property
    def active(self) -> bool:
        """Whether a non-normal alert is currently in force for the area.

        The level must not be a "normal" colour and the validity window must
        not have expired.
        """
        if self.event is None or self.event in NORMAL_LEVELS:
            return False
        return self.expires is None or datetime.now(UTC) < self.expires


class AreaAlertCoordinator(DataUpdateCoordinator[AreaAlertData]):
    """Coordinator exposing the CAP data of a single alert area."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        cache: CapFeedCache | None = None,
    ) -> None:
        self.area: str = str(entry.data[CONF_AREA])
        scan_interval = int(
            entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        )
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN} {self.area}",
            update_interval=timedelta(seconds=scan_interval),
            config_entry=entry,
        )
        self.entry = entry
        self.cache = cache or async_get_feed_cache(hass)
        entry.async_on_unload(entry.add_update_listener(self._async_options_updated))

    async def _async_options_updated(
        self, hass: HomeAssistant, entry: ConfigEntry
    ) -> None:
        self.update_interval = timedelta(
            seconds=int(entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
        )
        await self.async_request_refresh()

    async def _async_update_data(self) -> AreaAlertData:
        try:
            feed = await self.cache.async_get()
        except TimeoutError as err:
            raise UpdateFailed("Timeout while fetching the CAP feed") from err
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error fetching the CAP feed: {err}") from err
        except ValueError as err:
            raise UpdateFailed(f"Invalid CAP feed: {err}") from err

        info = feed.area(self.area)
        if info is None:
            raise UpdateFailed(
                f"Area {self.area} is not present in the CAP feed"
            )

        return AreaAlertData(
            area=self.area,
            label=area_label(self.area),
            identifier=feed.identifier,
            sent=feed.sent,
            status=feed.status,
            msg_type=feed.msg_type,
            source=feed.source,
            scope=feed.scope,
            note=feed.note,
            event=info.event,
            onset=info.onset,
            expires=info.expires,
            parameters=dict(info.parameters),
        )
