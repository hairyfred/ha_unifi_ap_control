"""Config flow for HA UniFi AP Control integration."""

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

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
from .unifi_api import UniFiController, UniFiAPIError

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CONTROLLER_URL, default="https://192.168.1.1:8443"): str,
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Optional(CONF_SITE, default=DEFAULT_SITE): str,
        vol.Optional(CONF_VERIFY_SSL, default=DEFAULT_VERIFY_SSL): bool,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    api = UniFiController(
        controller_url=data[CONF_CONTROLLER_URL],
        username=data[CONF_USERNAME],
        password=data[CONF_PASSWORD],
        site=data.get(CONF_SITE, DEFAULT_SITE),
        verify_ssl=data.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL),
    )

    try:
        # Test connection in executor to avoid blocking
        result = await hass.async_add_executor_job(api.test_connection)
        if not result:
            raise CannotConnect("Failed to connect to UniFi controller")

        # Get AP count for title
        aps = await hass.async_add_executor_job(api.get_access_points)
        return {"title": f"UniFi Controller ({len(aps)} APs)"}

    except UniFiAPIError as err:
        _LOGGER.error("Failed to connect to UniFi controller: %s", err)
        raise CannotConnect(str(err)) from err


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HA UniFi AP Control."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Check if already configured
                await self.async_set_unique_id(user_input[CONF_CONTROLLER_URL])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
