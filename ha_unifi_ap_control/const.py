"""Constants for the HA UniFi AP Control integration."""

DOMAIN = "ha_unifi_ap_control"

CONF_CONTROLLER_URL = "controller_url"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_SITE = "site"
CONF_VERIFY_SSL = "verify_ssl"

DEFAULT_SITE = "default"
DEFAULT_VERIFY_SSL = False

# Power levels supported by UniFi
POWER_LEVELS = ["auto", "low", "medium", "high"]

# Radio band patterns - maps band name to radio name patterns
BAND_MAP = {
    "2.4GHz": ["ra0", "wifi0", "ng"],
    "5GHz": ["rai0", "wifi1", "na"],
    "6GHz": ["ra6", "wifi2", "6e"],
}

# Update interval in seconds
SCAN_INTERVAL = 60

# LED override modes
LED_MODE_DEFAULT = "default"  # Use site setting
LED_MODE_ON = "on"
LED_MODE_OFF = "off"
