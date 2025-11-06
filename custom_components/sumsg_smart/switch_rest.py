import asyncio
import logging
from .api import SumsgApi
from homeassistant.components.switch import SwitchEntity # type: ignore
from homeassistant.core import HomeAssistant # type: ignore
from homeassistant.config_entries import ConfigEntry # type: ignore
from .const import DOMAIN, MANUFACTURER
from homeassistant.helpers.device_registry import DeviceInfo # type: ignore
from homeassistant.helpers.entity_platform import AddEntitiesCallback

_LOGGER = logging.getLogger(__name__)
# _LOGGER.setLevel(logging.DEBUG)

class SumsgSwitchRest(SwitchEntity):
    def __init__(self, paras):
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
        
    @property
    def is_on(self):
        return self._state

    @property
    def state(self):
        return "on" if self._state else "off"
    
    def set_online(self, state):
        self._available = state
        self.hass.loop.call_soon_threadsafe(self.async_write_ha_state)
    def get_control_id(self):
        return self._control_id
    @property
    def device_info(self) -> DeviceInfo:
        """Return device registry information for this entity."""
        # 修复字符串引号问题
        if self._available == False:
            display_name = f"{self._paras['name']} (已离线)"
        else:
            display_name = self._paras['name']
            
        if self._control_id == 2 or self._control_id == 0:
            return DeviceInfo(
                name=display_name,
                identifiers={(DOMAIN, self._device_id)},
                manufacturer=MANUFACTURER,
                model=self._model,
                hw_version="1.0.0",
                configuration_url="https://www.sumsg.com/HA-WBC-2/docs",
            )
        else:
            return DeviceInfo(
                identifiers={(DOMAIN, self._device_id)},
            )
            
    def update_state(self, state):
        self._state = state
        self._available = True
        self.hass.loop.call_soon_threadsafe(self.async_write_ha_state)
        
    def turn_on(self, **kwargs):
        self._state = True
        asyncio.run(self.update_publish_state())
        
    def turn_off(self, **kwargs): 
        self._state = False
        asyncio.run(self.update_publish_state())
        
    async def update_publish_state(self):
        control_id = self._control_id
        try:
            if control_id == 2:
                await self.api.lan_set_power_state(self._device_ip, self._token, self._state)
            elif control_id == 5:
                await self.api.lan_set_auto_start_state(self._device_ip, self._token, self._state)
            elif control_id == 6:
                await self.api.lan_set_child_lock_state(self._device_ip, self._token, self._state)
        except Exception as e:
            _LOGGER.error(f"控制设备失败: {e}")