import asyncio
import logging
from .models import MQTT_C, MQTT_DATA
import voluptuous as vol # type: ignore
from .api import SumsgApi
from homeassistant.components.button import ButtonEntity  # type: ignore
from homeassistant.core import HomeAssistant  # type: ignore
from homeassistant.config_entries import ConfigEntry  # type: ignore
from homeassistant.helpers.device_registry import DeviceInfo # type: ignore
from .const import  DOMAIN
_LOGGER = logging.getLogger(__name__)

class SumsgButtonRest(ButtonEntity):
    def __init__(self,paras):
        self.api = SumsgApi(self.hass)
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
    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
        )
    def set_online(self,state):
        self._available = state
        self.hass.loop.call_soon_threadsafe(self.async_write_ha_state)
    def update_state(self, state):
        self._state = state
        self._available = True
        self.hass.loop.call_soon_threadsafe(self.async_write_ha_state)
    def press(self):
        self._state = not self._state
        asyncio.run(self.update_publish_state())
    async def update_publish_state(self):
        control_id = self._control_id
        _LOGGER.debug(f"{self._name} {self._control_id} {self._state}")
        try:
            if control_id == 3:
                await self.api.lan_set_reboot_state(self._device_ip, self._token)
            elif control_id == 4:
                await self.api.lan_set_force_shutdown(self._device_ip, self._token)
        except Exception as e:
            _LOGGER.error(f"控制设备失败: {e}")
