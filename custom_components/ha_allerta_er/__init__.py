"""The Allerta Emilia-Romagna integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .cap import async_get_feed_cache
from .coordinator import AreaAlertCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
]

type AllertaErConfigEntry = ConfigEntry[AreaAlertCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: AllertaErConfigEntry) -> bool:
    """Set up an alert area from a config entry."""
    cache = async_get_feed_cache(hass)
    coordinator = AreaAlertCoordinator(hass, entry, cache)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: AllertaErConfigEntry) -> bool:
    """Unload an alert area config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
