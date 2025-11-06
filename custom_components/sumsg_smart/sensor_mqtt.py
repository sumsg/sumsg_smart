import logging
import json
from homeassistant.components.sensor import SensorEntity # type: ignore
from homeassistant.core import HomeAssistant # type: ignore
from homeassistant.config_entries import ConfigEntry # type: ignore
from homeassistant.helpers.device_registry import DeviceInfo # type: ignore
from .const import  DOMAIN, MANUFACTURER
from .models import MQTT_C, MQTT_DATA
_LOGGER = logging.getLogger(__name__)

class SumsgSensorMQTT(SensorEntity):
    def __init__(self,paras):
        self._paras = paras
        self._device_id = paras["device_id"]
        self._mqtt = paras["mqtt"]
        self._name = paras["name"]
        self._model = paras["model"]
        self._available = paras["online"]
        self._topic = paras["topic"]
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
    @property
    def state(self):
        return self._state
    # @property
    # def extra_state_attributes(self):
    #     """返回额外的属性，用于显示多个数值。"""
    #     return {
    #         "value2": 121,
    #         "value3": 44,
    #     }
    @property
    def unit_of_measurement(self):
        return self._entity_unit
    @property
    def device_info(self):
        return DeviceInfo(
            name=self._name,
            identifiers={(DOMAIN, self._device_id)},
            manufacturer=MANUFACTURER,
            model=self._model,
            # sw_version="1.0.0",
            hw_version="2.0.4",
            configuration_url="https://u.sumsg.com/home_assistant",
        )
    def set_online(self,state):
        self._available = state
        self.hass.loop.call_soon_threadsafe(self.async_write_ha_state)
    def update_state(self, state):
        self._state = state
        self.hass.loop.call_soon_threadsafe(self.async_write_ha_state)
    def sync_system_data(self):
        pass
    def set_system_data(self,device_id,control_id,model,payload):
        if self._control_id==control_id and self._device_id==device_id:
            type = payload.get("t")
            if type=="M":
                self.set_online(True)
                temp_value = payload.get("tp")
                self.update_state(temp_value)
            if type=="DVOFF":
                self.set_online(False)
