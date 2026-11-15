"""Tests for coordinator fast-poll recovery after a failed update."""

from __future__ import annotations

from datetime import timedelta

from custom_components.ha_allerta_er.const import (
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    RECOVERY_SCAN_INTERVAL,
)
from custom_components.ha_allerta_er.coordinator import AreaAlertCoordinator


class _CoordinatorStub:
    """Minimal stand-in to exercise interval helpers without Home Assistant."""

    area = "Emil-A1"
    _recovery_mode = False
    update_interval = timedelta(seconds=DEFAULT_SCAN_INTERVAL)

    def __init__(self, scan_interval: int = DEFAULT_SCAN_INTERVAL) -> None:
        self.entry = type(
            "Entry",
            (),
            {"options": {CONF_SCAN_INTERVAL: scan_interval}},
        )()


def _bind_interval_helpers(stub: _CoordinatorStub) -> _CoordinatorStub:
    for name in (
        "_scan_interval_seconds",
        "_apply_configured_interval",
        "_apply_recovery_interval",
        "_clear_recovery_interval",
    ):
        method = AreaAlertCoordinator.__dict__[name]
        setattr(stub, name, method.__get__(stub, _CoordinatorStub))
    return stub


def test_recovery_interval_then_restore_configured() -> None:
    stub = _bind_interval_helpers(_CoordinatorStub(scan_interval=3600))
    stub._apply_recovery_interval()
    assert stub._recovery_mode is True
    assert stub.update_interval == timedelta(seconds=RECOVERY_SCAN_INTERVAL)

    stub._clear_recovery_interval()
    assert stub._recovery_mode is False
    assert stub.update_interval == timedelta(seconds=3600)