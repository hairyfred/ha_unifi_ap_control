"""UniFi Controller API client."""

import logging
import requests
import urllib3
from typing import Any

from .const import BAND_MAP

_LOGGER = logging.getLogger(__name__)

# Suppress SSL warnings for self-signed certs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class UniFiAPIError(Exception):
    """Exception for UniFi API errors."""
    pass


class UniFiController:
    """Handles communication with the UniFi Controller API."""

    def __init__(
        self,
        controller_url: str,
        username: str,
        password: str,
        site: str = "default",
        verify_ssl: bool = False,
    ):
        """Initialize the UniFi controller connection."""
        self.controller = controller_url.rstrip("/")
        self.username = username
        self.password = password
        self.site = site
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        self.session.verify = verify_ssl
        self._logged_in = False

    def login(self) -> bool:
        """Authenticate with the controller."""
        try:
            response = self.session.post(
                f"{self.controller}/api/login",
                json={"username": self.username, "password": self.password},
                timeout=10,
            )
            response.raise_for_status()
            result = response.json()

            if result.get("meta", {}).get("rc") != "ok":
                msg = result.get("meta", {}).get("msg", "Unknown error")
                raise UniFiAPIError(f"Login failed: {msg}")

            self._logged_in = True
            return True

        except requests.exceptions.ConnectionError as err:
            raise UniFiAPIError(f"Cannot connect to {self.controller}") from err
        except requests.exceptions.Timeout as err:
            raise UniFiAPIError("Connection timed out") from err
        except requests.exceptions.HTTPError as err:
            raise UniFiAPIError(f"HTTP error: {err}") from err

    def _ensure_logged_in(self) -> None:
        """Ensure we're logged in."""
        if not self._logged_in:
            self.login()

    def get_access_points(self) -> list[dict[str, Any]]:
        """Fetch all access points from the controller."""
        self._ensure_logged_in()

        try:
            response = self.session.get(
                f"{self.controller}/api/s/{self.site}/stat/device",
                timeout=10,
            )
            response.raise_for_status()
            devices = response.json().get("data", [])

            # Filter to only APs (devices with radio_table)
            aps = []
            for device in devices:
                if device.get("radio_table"):
                    aps.append(self._parse_ap(device))

            return aps

        except requests.exceptions.RequestException as err:
            self._logged_in = False
            raise UniFiAPIError(f"Failed to fetch devices: {err}") from err

    def _parse_ap(self, device: dict) -> dict[str, Any]:
        """Parse AP data into a cleaner format."""
        radios = {}

        for radio in device.get("radio_table", []):
            radio_name = radio.get("name", "")
            band = self._get_band_for_radio(radio_name)
            if band:
                radios[band] = {
                    "radio_name": radio_name,
                    "power": radio.get("tx_power_mode", "unknown"),
                    "channel": radio.get("channel", "auto"),
                }

        # LED state: led_override can be "default", "on", or "off"
        # If not set, check if LED is disabled at device level
        led_override = device.get("led_override", "default")

        return {
            "id": device.get("_id"),
            "mac": device.get("mac", "").lower(),
            "name": device.get("name", "Unknown"),
            "model": device.get("model", "Unknown"),
            "radios": radios,
            "raw_radio_table": device.get("radio_table", []),
            "led_override": led_override,
        }

    def _get_band_for_radio(self, radio_name: str) -> str | None:
        """Determine which band a radio belongs to."""
        radio_lower = radio_name.lower()
        for band, patterns in BAND_MAP.items():
            if any(pattern.lower() in radio_lower for pattern in patterns):
                return band
        return None

    def set_radio_power(
        self, device_id: str, mac: str, radio_table: list, band: str, power: str
    ) -> bool:
        """Set the power level for a specific radio band."""
        self._ensure_logged_in()

        # Find and update the correct radio in the table
        updated_table = []
        changed = False

        for radio in radio_table:
            radio_copy = radio.copy()
            radio_name = radio_copy.get("name", "")

            if self._get_band_for_radio(radio_name) == band:
                radio_copy["tx_power_mode"] = power
                changed = True

            updated_table.append(radio_copy)

        if not changed:
            _LOGGER.warning("No radio found for band %s on device %s", band, mac)
            return False

        try:
            response = self.session.put(
                f"{self.controller}/api/s/{self.site}/rest/device/{device_id}",
                json={"radio_table": updated_table},
                timeout=10,
            )

            if response.status_code == 200:
                _LOGGER.info("Set %s power to %s on %s", band, power, mac)
                return True
            else:
                _LOGGER.error(
                    "Failed to set power: HTTP %s - %s",
                    response.status_code,
                    response.text[:100],
                )
                return False

        except requests.exceptions.RequestException as err:
            self._logged_in = False
            raise UniFiAPIError(f"Failed to update device: {err}") from err

    def set_led_override(self, device_id: str, mac: str, mode: str) -> bool:
        """Set the LED override mode for a device.

        Args:
            device_id: The UniFi device ID
            mac: The device MAC address (for logging)
            mode: One of "default", "on", or "off"
        """
        self._ensure_logged_in()

        try:
            response = self.session.put(
                f"{self.controller}/api/s/{self.site}/rest/device/{device_id}",
                json={"led_override": mode},
                timeout=10,
            )

            if response.status_code == 200:
                _LOGGER.info("Set LED to %s on %s", mode, mac)
                return True
            else:
                _LOGGER.error(
                    "Failed to set LED: HTTP %s - %s",
                    response.status_code,
                    response.text[:100],
                )
                return False

        except requests.exceptions.RequestException as err:
            self._logged_in = False
            raise UniFiAPIError(f"Failed to update LED: {err}") from err

    def test_connection(self) -> bool:
        """Test the connection to the controller."""
        try:
            self.login()
            self.get_access_points()
            return True
        except UniFiAPIError:
            return False
