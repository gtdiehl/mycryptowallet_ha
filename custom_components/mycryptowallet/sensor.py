"""Support for IoTaWatt Energy monitor."""
from datetime import timedelta
from functools import partial
import logging

from homeassistant.core import callback
from homeassistant.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from . import MyCryptoWalletEntity, MyCryptoWalletUpdater
from .const import COORDINATOR, DOMAIN, SIGNAL_ADD_DEVICE, SIGNAL_DELETE_DEVICE

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add sensors for passed config_entry in HA."""

    coordinator = hass.data[DOMAIN][config_entry.entry_id][COORDINATOR]
    entities = []

    for idx, ent in enumerate(coordinator.data["sensors"]):
        entity = MyCryptoWalletSensor(
            coordinator=coordinator,
            entity=ent,
            name=ent,
        )
        entities.append(entity)

    async_add_entities(entities)

    async def async_new_entities(sensor_info):
        """Remove an entity."""
        ent = sensor_info["entity"]
        name = sensor_info["name"]

        entity = MyCryptoWalletSensor(
            coordinator=coordinator,
            entity=ent,
            name=name,
        )
        entities = [entity]
        async_add_entities(entities)

    async_dispatcher_connect(hass, SIGNAL_ADD_DEVICE, async_new_entities)


class MyCryptoWalletSensor(MyCryptoWalletEntity):
    """Defines a MyCryptoWallet Sensor."""

    def __init__(self, coordinator, entity, name):
        """Initialize the sensor."""
        super().__init__(coordinator=coordinator, entity=entity, name=name)

        self._ent = entity
        self._name = name
        self._state = None

    @property
    def device_state_attributes(self):
        """Return the state attributes of the device."""
        if "price" in self.coordinator.data["sensors"][self._ent]:
            return {"Price": self.coordinator.data["sensors"][self._ent]["price"]}
        else:
            return None

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.coordinator.data["sensors"][self._ent]["value"]

    @property
    def name(self):
        """Return the name of the sensor."""
        return "My Crypto Wallet " + self._name
