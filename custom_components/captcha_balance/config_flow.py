"""Config flow for RuCaptcha integration."""
from __future__ import annotations

import http.client
import json
import logging
import urllib.parse
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN, CURRENCIES, API_DOMAINS, DEFAULT_API_DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("api_key"): str,
        vol.Optional("api_domain", default=DEFAULT_API_DOMAIN): vol.In(list(API_DOMAINS.keys())),
        vol.Optional("update_interval", default=1): vol.All(vol.Coerce(int), vol.Range(min=1, max=1440)),
        vol.Optional("currency", default="RUB"): vol.In(CURRENCIES),
    }
)


class CaptchaHub:
    """Captcha API client for validation (RuCaptcha/2Captcha)."""

    def __init__(self, api_key: str, api_domain: str = DEFAULT_API_DOMAIN) -> None:
        """Initialize."""
        self.api_key = api_key
        self.api_domain = api_domain

    async def authenticate(self, hass: HomeAssistant) -> bool:
        """Test if we can authenticate with the RuCaptcha API."""
        result = await hass.async_add_executor_job(self._validate_api_key)
        return result

    def _validate_api_key(self) -> bool:
        """Validate API key by making a test request."""
        conn = None
        try:
            # Create connection
            conn = http.client.HTTPSConnection(self.api_domain, 443, timeout=10)

            # Parameters
            params = urllib.parse.urlencode({
                'key': self.api_key,
                'action': 'getbalance',
                'json': '1'
            })

            # Make request
            conn.request("GET", f"/res.php?{params}")

            # Get response
            response = conn.getresponse()
            
            if response.status != 200:
                _LOGGER.error("HTTP error: %s", response.status)
                raise CannotConnect(f"HTTP error: {response.status}")

            data = response.read().decode('utf-8')

            # Parse JSON
            result = json.loads(data)

            # Check if API key is valid
            if result.get('status') == 1:
                return True
            else:
                error_msg = result.get('request', 'Unknown error')
                _LOGGER.error("%s API validation failed: %s", API_DOMAINS[self.api_domain], error_msg)
                # Invalid API key typically returns status 0
                raise InvalidAuth(f"API validation failed: {error_msg}")

        except (InvalidAuth, CannotConnect):
            # Re-raise these specific exceptions
            raise
        except Exception as e:
            _LOGGER.error("Error validating %s API key: %s", API_DOMAINS[self.api_domain], e)
            raise CannotConnect(f"Connection error: {e}") from e
        finally:
            if conn:
                conn.close()


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    hub = CaptchaHub(data["api_key"], data.get("api_domain", DEFAULT_API_DOMAIN))

    # The authenticate method will raise InvalidAuth or CannotConnect
    # if validation fails, so we just need to call it
    await hub.authenticate(hass)

    return {"title": API_DOMAINS[data.get("api_domain", DEFAULT_API_DOMAIN)]}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for RuCaptcha."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)

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
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for RuCaptcha."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle options flow."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options_schema = vol.Schema(
            {
                vol.Optional(
                    "update_interval",
                    default=self.config_entry.options.get(
                        "update_interval", self.config_entry.data.get("update_interval", 1)
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=1440)),
                vol.Optional(
                    "currency",
                    default=self.config_entry.options.get(
                        "currency", self.config_entry.data.get("currency", "RUB")
                    ),
                ): vol.In(CURRENCIES),
            }
        )

        return self.async_show_form(step_id="init", data_schema=options_schema)