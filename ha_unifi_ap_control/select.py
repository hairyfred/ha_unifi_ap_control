"""Select entities for UniFi AP Power Control."""

import logging
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, POWER_LEVELS
from .coordinator import UniFiAPCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up UniFi AP Power select entities."""
    coordinator: UniFiAPCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = []

    for mac, ap_data in coordinator.data.items():
        # Create a select entity for each radio band on each AP
        for band, radio_info in ap_data.get("radios", {}).items():
            entities.append(
                UniFiAPPowerSelect(
                    coordinator=coordinator,
                    mac=mac,
                    band=band,
                    ap_name=ap_data["name"],
                    ap_model=ap_data["model"],
                )
            )

    async_add_entities(entities)


class UniFiAPPowerSelect(CoordinatorEntity[UniFiAPCoordinator], SelectEntity):
    """Select entity for controlling AP radio power."""

    _attr_options = POWER_LEVELS
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: UniFiAPCoordinator,
        mac: str,
        band: str,
        ap_name: str,
        ap_model: str,
    ) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator)

        self._mac = mac
        self._band = band
        self._ap_name = ap_name
        self._ap_model = ap_model

        # Create unique ID and entity ID
        mac_short = mac.replace(":", "")
        band_clean = band.replace(".", "_").replace("GHz", "").strip()

        self._attr_unique_id = f"{mac_short}_{band_clean}_power"
        self._attr_name = f"{band} Power"

        # Device info groups all entities for this AP together
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, mac)},
            name=ap_name,
            manufacturer="Ubiquiti",
            model=ap_model,
        )

    @property
    def current_option(self) -> str | None:
        """Return the current power level."""
        if self._mac not in self.coordinator.data:
            return None

        ap_data = self.coordinator.data[self._mac]
        radios = ap_data.get("radios", {})

        if self._band in radios:
            return radios[self._band].get("power", "unknown")

        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self._mac in self.coordinator.data
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        if self._mac not in self.coordinator.data:
            return {}

        ap_data = self.coordinator.data[self._mac]
        radios = ap_data.get("radios", {})

        if self._band in radios:
            radio = radios[self._band]
            return {
                "radio_name": radio.get("radio_name"),
                "channel": radio.get("channel"),
                "mac": self._mac,
            }

        return {}

    async def async_select_option(self, option: str) -> None:
        """Change the power level."""
        _LOGGER.info(
            "Setting %s %s power to %s",
            self._ap_name,
            self._band,
            option,
        )

        success = await self.coordinator.async_set_power(
            mac=self._mac,
            band=self._band,
            power=option,
        )

        if not success:
            _LOGGER.error(
                "Failed to set %s %s power to %s",
                self._ap_name,
                self._band,
                option,
            )
