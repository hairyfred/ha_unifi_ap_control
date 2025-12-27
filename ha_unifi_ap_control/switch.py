"""Switch entities for UniFi AP LED Control."""

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, LED_MODE_ON, LED_MODE_OFF
from .coordinator import UniFiAPCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up UniFi AP LED switch entities."""
    coordinator: UniFiAPCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = []

    for mac, ap_data in coordinator.data.items():
        entities.append(
            UniFiAPLEDSwitch(
                coordinator=coordinator,
                mac=mac,
                ap_name=ap_data["name"],
                ap_model=ap_data["model"],
            )
        )

    async_add_entities(entities)


class UniFiAPLEDSwitch(CoordinatorEntity[UniFiAPCoordinator], SwitchEntity):
    """Switch entity for controlling AP LED."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:led-on"

    def __init__(
        self,
        coordinator: UniFiAPCoordinator,
        mac: str,
        ap_name: str,
        ap_model: str,
    ) -> None:
        """Initialize the switch entity."""
        super().__init__(coordinator)

        self._mac = mac
        self._ap_name = ap_name
        self._ap_model = ap_model

        # Create unique ID
        mac_short = mac.replace(":", "")
        self._attr_unique_id = f"{mac_short}_led"
        self._attr_name = "LED"

        # Device info groups all entities for this AP together
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, mac)},
            name=ap_name,
            manufacturer="Ubiquiti",
            model=ap_model,
        )

    @property
    def is_on(self) -> bool | None:
        """Return true if LED is on."""
        if self._mac not in self.coordinator.data:
            return None

        ap_data = self.coordinator.data[self._mac]
        led_override = ap_data.get("led_override", "default")

        # "on" or "default" means LED is on, "off" means LED is off
        return led_override != LED_MODE_OFF

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
        return {
            "led_override": ap_data.get("led_override", "default"),
            "mac": self._mac,
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the LED on."""
        _LOGGER.info("Turning LED on for %s", self._ap_name)

        success = await self.coordinator.async_set_led(
            mac=self._mac,
            mode=LED_MODE_ON,
        )

        if not success:
            _LOGGER.error("Failed to turn LED on for %s", self._ap_name)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the LED off."""
        _LOGGER.info("Turning LED off for %s", self._ap_name)

        success = await self.coordinator.async_set_led(
            mac=self._mac,
            mode=LED_MODE_OFF,
        )

        if not success:
            _LOGGER.error("Failed to turn LED off for %s", self._ap_name)
