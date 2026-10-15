"""Binary sensor platform for the Allerta Emilia-Romagna integration."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN, SITE_URL
from .coordinator import AreaAlertCoordinator

PARALLEL_UPDATES = 1

DESCRIPTION = BinarySensorEntityDescription(
    key="alert_active",
    translation_key="alert_active",
    device_class=BinarySensorDeviceClass.SAFETY,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary sensors of an alert area."""
    coordinator: AreaAlertCoordinator = entry.runtime_data
    async_add_entities([AlertActiveBinarySensor(coordinator)])


class AlertActiveBinarySensor(
    CoordinatorEntity[AreaAlertCoordinator], BinarySensorEntity
):
    """Whether a non-normal alert is currently in force for the area."""

    entity_description = DESCRIPTION
    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION

    def __init__(self, coordinator: AreaAlertCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.area}_{DESCRIPTION.key}"

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
    def is_on(self) -> bool | None:
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.active
