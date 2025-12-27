"""Data coordinator for UniFi AP Power Control."""

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, SCAN_INTERVAL
from .unifi_api import UniFiController, UniFiAPIError

_LOGGER = logging.getLogger(__name__)


class UniFiAPCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to manage fetching UniFi AP data."""

    def __init__(self, hass: HomeAssistant, api: UniFiController) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=SCAN_INTERVAL),
        )
        self.api = api

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the UniFi controller."""
        try:
            aps = await self.hass.async_add_executor_job(self.api.get_access_points)

            # Index by MAC address for easy lookup
            return {ap["mac"]: ap for ap in aps}

        except UniFiAPIError as err:
            raise UpdateFailed(f"Error communicating with UniFi controller: {err}") from err

    async def async_set_power(
        self, mac: str, band: str, power: str
    ) -> bool:
        """Set power level for a specific AP and band."""
        if mac not in self.data:
            _LOGGER.error("AP with MAC %s not found", mac)
            return False

        ap = self.data[mac]

        try:
            success = await self.hass.async_add_executor_job(
                self.api.set_radio_power,
                ap["id"],
                mac,
                ap["raw_radio_table"],
                band,
                power,
            )

            if success:
                # Refresh data to get new state
                await self.async_request_refresh()

            return success

        except UniFiAPIError as err:
            _LOGGER.error("Failed to set power: %s", err)
            return False

    async def async_set_led(self, mac: str, mode: str) -> bool:
        """Set LED mode for a specific AP.

        Args:
            mac: The AP MAC address
            mode: One of "default", "on", or "off"
        """
        if mac not in self.data:
            _LOGGER.error("AP with MAC %s not found", mac)
            return False

        ap = self.data[mac]

        try:
            success = await self.hass.async_add_executor_job(
                self.api.set_led_override,
                ap["id"],
                mac,
                mode,
            )

            if success:
                # Refresh data to get new state
                await self.async_request_refresh()

            return success

        except UniFiAPIError as err:
            _LOGGER.error("Failed to set LED: %s", err)
            return False
