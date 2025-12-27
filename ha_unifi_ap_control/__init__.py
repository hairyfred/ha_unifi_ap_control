"""The HA UniFi AP Control integration."""

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import (
    DOMAIN,
    CONF_CONTROLLER_URL,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_SITE,
    CONF_VERIFY_SSL,
    DEFAULT_SITE,
    DEFAULT_VERIFY_SSL,
)
from .coordinator import UniFiAPCoordinator
from .unifi_api import UniFiController

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SELECT, Platform.SWITCH]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up HA UniFi AP Control from a config entry."""
    _LOGGER.info("Setting up HA UniFi AP Control integration")

    # Create API client
    api = UniFiController(
        controller_url=entry.data[CONF_CONTROLLER_URL],
        username=entry.data[CONF_USERNAME],
        password=entry.data[CONF_PASSWORD],
        site=entry.data.get(CONF_SITE, DEFAULT_SITE),
        verify_ssl=entry.data.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL),
    )

    # Login to controller
    try:
        await hass.async_add_executor_job(api.login)
    except Exception as err:
        _LOGGER.error("Failed to login to UniFi controller: %s", err)
        return False

    # Create coordinator
    coordinator = UniFiAPCoordinator(hass, api)

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    _LOGGER.info(
        "Found %d access points on UniFi controller",
        len(coordinator.data),
    )

    # Store coordinator
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
