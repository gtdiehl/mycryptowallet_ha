"""The MyCryptoWallet integration."""
from __future__ import annotations

from datetime import timedelta
import logging

from debankpy.debank import Debank
from httpx import AsyncClient

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_SCAN_INTERVAL,
    DEVICE_CLASS_ENERGY,
    CURRENCY_DOLLAR,
    DEVICE_CLASS_MONETARY,
)
from homeassistant.components.sensor import STATE_CLASS_MEASUREMENT, SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady, PlatformNotReady
from homeassistant.helpers import entity, entity_registry, update_coordinator
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import COORDINATOR, DEFAULT_ICON, DOMAIN, MYCRYPTOWALLET_API

_LOGGER = logging.getLogger(__name__)

# TODO List the platforms that you want to support.
# For your initial PR, limit it to 1 platform.
PLATFORMS = ["sensor"]


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the MyCryptoWallet component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up MyCryptoWallet from a config entry."""
    # TODO Store an API object for your platforms to access
    # hass.data[DOMAIN][entry.entry_id] = MyApi(...)

    # hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    polling_interval = 10
    session = AsyncClient()

    api = Debank(entry.data["name"], session)

    coordinator = MyCryptoWalletUpdater(
        hass,
        api=api,
        name="MyCryptoWallet",
        update_interval=polling_interval,
    )

    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    hass.data[DOMAIN][entry.entry_id] = {
        COORDINATOR: coordinator,
        MYCRYPTOWALLET_API: api,
    }

    for component in PLATFORMS:
        _LOGGER.info(f"Setting up platform: {component}")
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, component)
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class MyCryptoWalletUpdater(DataUpdateCoordinator):
    """Class to manage fetching update data for the Crypto Wallet"""

    def __init__(self, hass: HomeAssistant, api: str, name: str, update_interval: int):
        self.api = api
        self.sensorlist = {}

        super().__init__(
            hass=hass,
            logger=_LOGGER,
            name=name,
            update_interval=timedelta(minutes=update_interval),
        )

    async def _async_update_data(self):
        """Fetch sensors from Wallet cloud endpoints"""

        sensors = {}

        await self.api.connect()
        await self.api.update()
        sensors["sensors"] = self.api.getDefiWalletItems()
        for sensor in sensors["sensors"]:
            if sensor not in self.sensorlist:
                to_add = {
                    "entity": sensor,
                    "name": sensors["sensors"][sensor],
                }

        return sensors


class MyCryptoWalletEntity(update_coordinator.CoordinatorEntity, SensorEntity):
    """Defines the base Crypto Wallet entity."""

    def __init__(self, coordinator: MyCryptoWalletUpdater, entity, name):
        """Initialize the IoTaWatt Entity."""
        super().__init__(coordinator)

        self._entity = entity
        self._name = name
        self._icon = "mdi:currency-usd"
        self._attr_unit_of_measurement = CURRENCY_DOLLAR
        self._attr_device_class = DEVICE_CLASS_MONETARY
        self._attr_state_class = STATE_CLASS_MEASUREMENT

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._name

    @property
    def icon(self):
        """Return the icon for the entity."""
        return self._icon
