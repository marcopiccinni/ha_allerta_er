"""Sensor platform for the Allerta Emilia-Romagna integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN, SITE_URL
from .coordinator import AreaAlertCoordinator, AreaAlertData

PARALLEL_UPDATES = 1

# Home Assistant enforces a hard 255-character limit on entity states, so the
# (potentially very long) CAP note is exposed in full as an attribute and only
# a truncated preview is used as the state.
NOTE_STATE_MAX: int = 250


def _short_note(data: AreaAlertData) -> str | None:
    """Return a preview of the note that fits the 255-character state limit."""
    note = (data.note or "").strip()
    if not note:
        return None
    if len(note) <= NOTE_STATE_MAX:
        return note
    return f"{note[: NOTE_STATE_MAX - 1].rstrip()}\u2026"


@dataclass(frozen=True, kw_only=True)
class AllertaSensorEntityDescription(SensorEntityDescription):
    """Describes an Allerta sensor."""

    value_fn: Callable[[AreaAlertData], Any]


CORE_SENSORS: tuple[AllertaSensorEntityDescription, ...] = (
    AllertaSensorEntityDescription(
        key="event",
        translation_key="event",
        icon="mdi:alert",
        value_fn=lambda data: data.event,
    ),
    AllertaSensorEntityDescription(
        key="note",
        translation_key="note",
        icon="mdi:text-box-outline",
        value_fn=_short_note,
    ),
    AllertaSensorEntityDescription(
        key="onset",
        translation_key="onset",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: data.onset,
    ),
    AllertaSensorEntityDescription(
        key="expires",
        translation_key="expires",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: data.expires,
    ),
    AllertaSensorEntityDescription(
        key="sent",
        translation_key="sent",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: data.sent,
    ),
    AllertaSensorEntityDescription(
        key="identifier",
        translation_key="identifier",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        icon="mdi:file-document-outline",
        value_fn=lambda data: data.identifier,
    ),
)

# CAP parameters exposed as one sensor per hazard. ``stato_mare`` and
# ``mareggiate`` are only meaningful for coastal areas, so they are disabled
# by default and can be enabled where relevant.
PARAMETER_SENSORS: tuple[AllertaSensorEntityDescription, ...] = (
    AllertaSensorEntityDescription(
        key="idraulico",
        translation_key="idraulico",
        icon="mdi:water",
        value_fn=lambda data: data.parameter("idraulico"),
    ),
    AllertaSensorEntityDescription(
        key="idrogeologico",
        translation_key="idrogeologico",
        icon="mdi:landslide",
        value_fn=lambda data: data.parameter("idrogeologico"),
    ),
    AllertaSensorEntityDescription(
        key="temporali",
        translation_key="temporali",
        icon="mdi:weather-lightning",
        value_fn=lambda data: data.parameter("temporali"),
    ),
    AllertaSensorEntityDescription(
        key="vento",
        translation_key="vento",
        icon="mdi:weather-windy",
        value_fn=lambda data: data.parameter("vento"),
    ),
    AllertaSensorEntityDescription(
        key="temperature_estreme",
        translation_key="temperature_estreme",
        icon="mdi:thermometer-alert",
        value_fn=lambda data: data.parameter("temperature_estreme"),
    ),
    AllertaSensorEntityDescription(
        key="neve",
        translation_key="neve",
        icon="mdi:weather-snowy",
        value_fn=lambda data: data.parameter("neve"),
    ),
    AllertaSensorEntityDescription(
        key="pioggia_che_gela",
        translation_key="pioggia_che_gela",
        icon="mdi:weather-snowy-rainy",
        value_fn=lambda data: data.parameter("pioggia_che_gela"),
    ),
    AllertaSensorEntityDescription(
        key="stato_mare",
        translation_key="stato_mare",
        icon="mdi:waves",
        entity_registry_enabled_default=False,
        value_fn=lambda data: data.parameter("stato_mare"),
    ),
    AllertaSensorEntityDescription(
        key="mareggiate",
        translation_key="mareggiate",
        icon="mdi:wave",
        entity_registry_enabled_default=False,
        value_fn=lambda data: data.parameter("mareggiate"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensors of an alert area."""
    coordinator: AreaAlertCoordinator = entry.runtime_data
    descriptions = [*CORE_SENSORS, *PARAMETER_SENSORS]
    async_add_entities(
        AllertaSensor(coordinator, description) for description in descriptions
    )


class AllertaSensor(CoordinatorEntity[AreaAlertCoordinator], SensorEntity):
    """A single Allerta sensor."""

    entity_description: AllertaSensorEntityDescription
    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION

    def __init__(
        self,
        coordinator: AreaAlertCoordinator,
        description: AllertaSensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.area}_{description.key}"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.area)},
            name=f"Allerta ER {self.coordinator.area.removeprefix('Emil-')}",
            manufacturer="AllertaMeteoER - Regione Emilia-Romagna",
            model="Area di allertamento",
            configuration_url=SITE_URL,
        )

    @property
    def native_value(self) -> Any:
        if self.coordinator.data is None:
            return None
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        data = self.coordinator.data
        if data is None:
            return None

        if self.entity_description.key == "event":
            return {
                "identifier": data.identifier,
                "sent": data.sent,
                "onset": data.onset,
                "expires": data.expires,
                "status": data.status,
                "msg_type": data.msg_type,
                "scope": data.scope,
                "source": data.source,
                "area": data.area,
            }

        if self.entity_description.key == "note":
            # Full text lives here: attributes have no 255-character limit.
            return {
                "testo": data.note,
                "identifier": data.identifier,
                "sent": data.sent,
            }

        return None
