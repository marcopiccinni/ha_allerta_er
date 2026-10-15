"""Config flow for the Allerta Emilia-Romagna integration."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .cap import async_get_feed_cache
from .const import (
    CONF_AREA,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DISCLAIMER,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
    SITE_URL,
)
from .coordinator import area_label

_LOGGER = logging.getLogger(__name__)


class AllertaErConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the UI configuration flow (one alert area per entry)."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Let the user pick one of the alert areas from the live CAP feed."""
        errors: dict[str, str] = {}
        areas: list[str] = []

        try:
            feed = await async_get_feed_cache(self.hass).async_get()
        except (aiohttp.ClientError, TimeoutError, ValueError):
            errors["base"] = "cannot_connect"
        else:
            areas = sorted(feed.areas)

        if user_input is not None and not errors:
            area = str(user_input.get(CONF_AREA, ""))
            if area in areas:
                await self.async_set_unique_id(f"area:{area}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"Allerta ER {area_label(area)}",
                    data={CONF_AREA: area},
                )
            errors["base"] = "invalid_area"

        if areas:
            schema: vol.Schema = vol.Schema(
                {vol.Required(CONF_AREA): vol.In({area: area for area in areas})}
            )
        else:
            schema = vol.Schema({})

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "disclaimer": DISCLAIMER,
                "site": SITE_URL,
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Return the options flow."""
        return AllertaErOptionsFlow()


class AllertaErOptionsFlow(OptionsFlow):
    """Options: refresh interval."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        entry = self.config_entry
        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=entry.options.get(
                        CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                    ),
                ): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL),
                ),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
