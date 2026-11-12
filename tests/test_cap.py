"""Unit tests for CAP parsing (no Home Assistant runtime required)."""

from __future__ import annotations

from pathlib import Path

import pytest

from custom_components.ha_allerta_er.cap import (
    PARAMETER_KEYS,
    _parameter_base_name,
    parse_cap,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def test_parameter_base_name_accepts_legacy_and_suffixed_names() -> None:
    assert _parameter_base_name("IDRAULICO") == "IDRAULICO"
    assert _parameter_base_name("IDRAULICO_2436") == "IDRAULICO"
    assert _parameter_base_name("VENTO_1224") == "VENTO"
    assert _parameter_base_name("UNKNOWN_FOO") is None


def test_parse_live_cap_merges_horizons_per_phenomenon() -> None:
    payload = (FIXTURES / "live_cap_20261111.xml").read_bytes()
    feed = parse_cap(payload)
    c1 = feed.area("Emil-C1")
    assert c1 is not None
    assert c1.event == "arancione"
    assert c1.parameters["IDRAULICO"] == "arancione"
    assert c1.parameters["IDROGEOLOGICO"] == "arancione"
    assert c1.parameters["TEMPORALI"] == "verde"
    assert c1.parameters["VENTO"] == "giallo"

    a1 = feed.area("Emil-A1")
    assert a1 is not None
    assert a1.parameters["IDRAULICO"] == "giallo"
    assert a1.parameters["VENTO"] == "giallo"


def test_parse_legacy_cap_without_suffixes() -> None:
    xml = b"""<?xml version="1.0" encoding="UTF-8"?>
<alert xmlns="urn:oasis:names:tc:emergency:cap:1.2">
  <identifier>1/2026</identifier>
  <sent>2026-10-01T10:00:00+02:00[Europe/Rome]</sent>
  <info>
    <language>it-IT</language>
    <event>VERDE</event>
    <onset>2026-10-01T10:00:00+02:00[Europe/Rome]</onset>
    <expires>2026-10-02T00:00:00+02:00[Europe/Rome]</expires>
    <parameter><valueName>IDRAULICO</valueName><value>VERDE</value></parameter>
    <parameter><valueName>IDROGEOLOGICO</valueName><value>GIALLO</value></parameter>
    <parameter><valueName>TEMPORALI</valueName><value>VERDE</value></parameter>
    <parameter><valueName>VENTO</valueName><value>VERDE</value></parameter>
    <parameter><valueName>TEMPERATURE_ESTREME</valueName><value>VERDE</value></parameter>
    <parameter><valueName>NEVE</valueName><value>VERDE</value></parameter>
    <parameter><valueName>GHIACCIO_PIOGGIA_CHE_GELA</valueName><value>VERDE</value></parameter>
    <parameter><valueName>STATO_MARE</valueName><value/></parameter>
    <parameter><valueName>MAREGGIATE</valueName><value/></parameter>
    <area><areaDesc>Emil-A1</areaDesc></area>
  </info>
</alert>
"""
    area = parse_cap(xml).area("Emil-A1")
    assert area is not None
    assert area.parameters["IDRAULICO"] == "verde"
    assert area.parameters["IDROGEOLOGICO"] == "giallo"
    for base in PARAMETER_KEYS:
        assert base in area.parameters


@pytest.mark.parametrize(
    ("area", "expected_idraulico"),
    [
        ("Emil-E1", "arancione"),
        ("Emil-F3", "arancione"),
    ],
)
def test_parse_live_cap_sample_areas(area: str, expected_idraulico: str) -> None:
    payload = (FIXTURES / "live_cap_20261111.xml").read_bytes()
    info = parse_cap(payload).area(area)
    assert info is not None
    assert info.parameters["IDRAULICO"] == expected_idraulico
