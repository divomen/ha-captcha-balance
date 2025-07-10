"""RuCaptcha / 2Captcha balance sensor."""
from __future__ import annotations

import http.client
import json
import logging
import urllib.parse
from datetime import timedelta
import asyncio

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.helpers.entity import EntityCategory
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN, API_DOMAINS, DEFAULT_API_DOMAIN

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=1)


class CaptchaDataUpdateCoordinator(DataUpdateCoordinator):
    """Data update coordinator for RuCaptcha/2Captcha."""

    def __init__(self, hass: HomeAssistant, api_key: str, api_domain: str = DEFAULT_API_DOMAIN, update_interval: int = 1, currency: str = "RUB") -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=update_interval),
        )
        self.api_key = api_key
        self.api_domain = api_domain
        self.currency = currency

    async def _async_update_data(self) -> float:
        """Update data via library."""
        for attempt in range(3):  # Retry up to 3 times
            try:
                return await self.hass.async_add_executor_job(
                    self._get_balance_http_client, self.api_key, self.api_domain
                )
            except UpdateFailed as exception:
                if attempt == 2:  # Last attempt
                    raise exception
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            except Exception as exception:
                if attempt == 2:  # Last attempt
                    raise UpdateFailed(f"Error communicating with API: {exception}") from exception
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

    def _get_balance_http_client(self, api_key: str, api_domain: str) -> float:
        """Get balance using http.client."""
        conn = None
        try:
            # Create connection
            conn = http.client.HTTPSConnection(api_domain, 443, timeout=15)

            # Parameters
            params = urllib.parse.urlencode({
                'key': api_key,
                'action': 'getbalance',
                'json': '1'
            })

            # Make request
            conn.request("GET", f"/res.php?{params}")

            # Get response
            response = conn.getresponse()
            
            if response.status != 200:
                _LOGGER.error("%s HTTP error: %s", API_DOMAINS[api_domain], response.status)
                raise UpdateFailed(f"HTTP error: {response.status}")
                
            data = response.read().decode('utf-8')

            # Parse JSON
            try:
                result = json.loads(data)
            except json.JSONDecodeError as e:
                _LOGGER.error("%s Invalid JSON response: %s", API_DOMAINS[api_domain], data)
                raise UpdateFailed(f"Invalid JSON response: {e}") from e

            if result.get('status') == 1:
                balance = result.get('request')
                try:
                    return float(balance)
                except (ValueError, TypeError) as e:
                    _LOGGER.error("%s Invalid balance value: %s", API_DOMAINS[api_domain], balance)
                    raise UpdateFailed(f"Invalid balance value: {balance}") from e
            else:
                error_msg = result.get('request', 'Unknown error')
                _LOGGER.error("%s API error: %s", API_DOMAINS[api_domain], error_msg)
                # Check for specific error codes
                if 'key does not exist' in str(error_msg).lower():
                    raise UpdateFailed(f"Invalid API key: {error_msg}")
                elif 'zero balance' in str(error_msg).lower():
                    return 0.0  # Zero balance is valid
                else:
                    raise UpdateFailed(f"{API_DOMAINS[api_domain]} API error: {error_msg}")

        except UpdateFailed:
            # Re-raise UpdateFailed exceptions
            raise
        except Exception as e:
            _LOGGER.error("Error getting %s balance: %s", API_DOMAINS[api_domain], e)
            raise UpdateFailed(f"Error getting {API_DOMAINS[api_domain]} balance: {e}") from e
        finally:
            if conn:
                conn.close()


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the RuCaptcha/2Captcha sensor."""
    api_key = config_entry.data["api_key"]
    api_domain = config_entry.data.get("api_domain", DEFAULT_API_DOMAIN)
    update_interval = config_entry.options.get(
        "update_interval", config_entry.data.get("update_interval", 1)
    )
    currency = config_entry.options.get(
        "currency", config_entry.data.get("currency", "RUB")
    )
    
    coordinator = CaptchaDataUpdateCoordinator(hass, api_key, api_domain, update_interval, currency)
    await coordinator.async_config_entry_first_refresh()

    async_add_entities([CaptchaBalanceSensor(coordinator)], True)

    # Set up options update listener
    config_entry.async_on_unload(
        config_entry.add_update_listener(async_reload_entry)
    )


async def async_reload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Reload the config entry when options change."""
    await hass.config_entries.async_reload(config_entry.entry_id)


class CaptchaBalanceSensor(SensorEntity):
    """Representation of a RuCaptcha/2Captcha balance sensor."""

    def __init__(self, coordinator: CaptchaDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        self.coordinator = coordinator
        service_name = API_DOMAINS[coordinator.api_domain]
        self._attr_name = f"{service_name} Balance"
        self._attr_unique_id = "captcha_balance"
        self._attr_native_unit_of_measurement = coordinator.currency
        self._attr_icon = "mdi:cash"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.api_domain)},
            name=service_name,
            manufacturer=service_name,
            model="Balance Monitor",
        )

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        return self.coordinator.data

    @property
    def icon(self) -> str:
        """Return the icon based on balance level."""
        if self.coordinator.data is None:
            return "mdi:cash-off"
        elif self.coordinator.data < 10:
            return "mdi:cash-remove"
        elif self.coordinator.data < 100:
            return "mdi:cash-minus"
        else:
            return "mdi:cash-multiple"

    @property
    def extra_state_attributes(self) -> dict[str, any]:
        """Return additional state attributes."""
        attrs = {}
        if self.coordinator.last_update_success:
            attrs["last_update_success"] = self.coordinator.last_update_success
        if self.coordinator.data is not None:
            if self.coordinator.data < 10:
                attrs["balance_status"] = "low"
            elif self.coordinator.data < 100:
                attrs["balance_status"] = "medium"
            else:
                attrs["balance_status"] = "high"
        return attrs

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success

    async def async_update(self) -> None:
        """Update the entity."""
        await self.coordinator.async_request_refresh()