import logging
from homeassistant.components.sensor import SensorEntity # type: ignore
from homeassistant.config_entries import ConfigEntry # type: ignore
from homeassistant.helpers.device_registry import DeviceInfo # type: ignore
from .const import  DOMAIN, MANUFACTURER
from .models import MQTT_C, MQTT_DATA
_LOGGER = logging.getLogger(__name__)

class SumsgSensorRest(SensorEntity):
    def __init__(self,paras):
        self._paras = paras
        self._device_ip = paras["device_ip"]
        self._token = paras["token"]
        self._device_id = paras["device_id"]
        self._name = paras["name"]
        self._model = paras["model"]
        self._available = True
        self._state = paras["state"]
        self._control_id = paras["control_id"]
        self._entity_name = paras["entity_name"]
        self._entity_id = paras["entity_id"]
        self._entity_icon = paras["entity_icon"]
        self._entity_unit = paras["entity_unit"]

    @property
    def name(self):
        return self._entity_name
    @property
    def available(self):
        return self._available
    @property
    def icon(self):
        return self._entity_icon
    @property
    def unique_id(self):
        return self._entity_id
    def get_control_id(self):
        return self._control_id
    @property
    def state(self):
        return self._state
    @property
    def unit_of_measurement(self):
        return self._entity_unit
    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
        )
    def set_online(self,state):
        self._available = state
        self.hass.loop.call_soon_threadsafe(self.async_write_ha_state)
    def update_state(self, state):
        self._state = state
        self.hass.loop.call_soon_threadsafe(self.async_write_ha_state)