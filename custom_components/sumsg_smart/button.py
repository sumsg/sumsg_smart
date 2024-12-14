import logging
import json
import hashlib
from .models import MQTT_C, MQTT_DATA
import voluptuous as vol # type: ignore
from homeassistant.components.button import ButtonEntity  # type: ignore
from homeassistant.core import HomeAssistant  # type: ignore
from homeassistant.config_entries import ConfigEntry  # type: ignore
from homeassistant.helpers.device_registry import DeviceInfo # type: ignore
from .const import  DOMAIN
_LOGGER = logging.getLogger(__name__)

class SumsgButton(ButtonEntity):
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
    def press(self):
        self._state = not self._state
        self.update_publish_state("SW")
    def get_tk(self,action): 
        return hashlib.md5(f"{self._device_id}{self._model}{action}".encode('utf-8')).hexdigest()
    def update_publish_state(self,action):
        payload = None
        control_id = self._control_id
        if action=="SW":
            payload = {
                "c": action,
                "s": control_id,
                "tk": self.get_tk(action),
            }
        if payload is not None:
            self._mqtt.publish(self._topic,payload)
    def sync_system_data(self):
        pass
    def set_system_data(self,device_id,control_id,model,payload):
        if self._control_id==control_id and self._device_id==device_id:
            type = payload.get("t")
            if type=="M":
                state = payload.get("ps")==1
                self.set_online(state)
                self.update_state(state)
            if type=="DVOFF":
                self.set_online(False)
async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities,
):
    """Add sensors for passed config_entry in HA."""
    devices =  hass.data[DOMAIN]["devices"]
    entities = []
    mqtt = None
    mqtt_data: MQTT_DATA
    if DOMAIN in hass.data:
        mqtt_data = hass.data[DOMAIN][MQTT_C]
        mqtt = mqtt_data.client
    for device in devices:
        model = device.get('productName')
        if model=="pcSw3" or model=="pcSw1":
            name = device.get('deviceName')
            online = device.get('onStatus')
            device_id = device.get('token')
            topic = f"su/{model}/{device_id}/client"
            paras = {
                "hass":hass,
                "mqtt":mqtt,
                "model":model,
                "name":name,
                "online":online==1,
                "device_id":device_id,
                "entity_icon":"mdi:power",
                "topic":topic,
                "state":False,
                "control_id":0,
                "entity_name":name,
                "entity_id":f"{DOMAIN}_0_{device_id}"
            }
            last_msg_str = device.get('lastMsg', '{}')
            last_msg = json.loads(last_msg_str)
            #
            if model=="pcSw3" or model=="pcSw1":
                for control_id in [3,4]:
                    entity_id = f"{DOMAIN}_{control_id}_{device_id}"
                    paras["control_id"] = control_id
                    paras["entity_id"] = entity_id
                    if control_id==3:
                        paras["state"] = last_msg.get('ps') == 1
                        paras["entity_name"] = "重启"
                        paras["entity_icon"] = "mdi:restart"
                    if control_id==4:
                        paras["state"] = last_msg.get('au') == 1
                        paras["entity_name"] = "强制关机"
                        paras["entity_icon"] = "mdi:television-stop"
                    device_entities = SumsgButton(paras)
                    entities.append(device_entities)
                    mqtt.entities_append(entity_id,device_entities)
    async_add_entities(entities)
    return True
