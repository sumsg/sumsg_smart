import logging
import json
import hashlib
from .models import MQTT_C, MQTT_DATA
from homeassistant.components.switch import SwitchEntity # type: ignore
from homeassistant.core import HomeAssistant # type: ignore
from homeassistant.config_entries import ConfigEntry # type: ignore
from .const import  DOMAIN, MANUFACTURER
from homeassistant.helpers.device_registry import DeviceInfo # type: ignore
_LOGGER = logging.getLogger(__name__)

class SumsgSwitch(SwitchEntity):
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
    def state(self):
        return "on" if self._state else "off"
    def set_online(self,state):
        self._available = state
        self.hass.loop.call_soon_threadsafe(self.async_write_ha_state)
    @property
    def device_info(self) -> DeviceInfo:
        """Return device registry information for this entity."""
        if self._available==False:
            self._name = f"{self._paras["name"]} (已离线)"
        else:
            self._name = self._paras["name"]
        if self._control_id==2 or self._control_id==0:
            return DeviceInfo(
                name=self._name,
                identifiers={(DOMAIN, self._device_id)},
                manufacturer=MANUFACTURER,
                model=self._model,
                # sw_version="1.0.0",
                hw_version="2.0.4",
                configuration_url="https://u.sumsg.com",
            )
        else:
            return DeviceInfo(
                identifiers={(DOMAIN, self._device_id)},
            )
    def update_state(self, state):
        self._state = state
        self.hass.loop.call_soon_threadsafe(self.async_write_ha_state)
    def turn_on(self):
        self._state = True
        self.update_publish_state("SW")
    def turn_off(self):
        self._state = False
        self.update_publish_state("SW")
    def get_tk(self,action): 
        return hashlib.md5(f"{self._device_id}{self._model}{action}".encode('utf-8')).hexdigest()
    def update_publish_state(self,action):
        payload = None
        control_id = self._control_id
        if action=="SW":
            if self._model=="pcSw1" or self._model=="pcSw3":
                if self._control_id==2:
                    if self._state==False:
                        control_id = 1
                payload = {
                    "c": action,
                    "s": control_id,
                    "tk": self.get_tk(action),
                }
            if self._model=="powerSwitch1":
                if self._state==False:
                    control_id = 0
                else:
                    control_id = 1
                payload = {
                    "c": action,
                    "on":control_id,
                    "tk": self.get_tk(action),
                }
        if action=="S" or action=="N":
            payload = {
                "c": action,
                "tk": self.get_tk(action),
            }
        payload2 = {
            "c": "M",
            "tk": self.get_tk("M"),
        }
        if payload is not None:
            self._mqtt.publish(self._topic,payload)
            self._mqtt.publish(self._topic,payload2)
    def sync_system_data(self):
        if self._control_id==2:
            self.update_publish_state("S")
    def set_system_data(self,device_id,control_id,model,payload):
        if self._control_id==control_id and self._device_id==device_id:
            type = payload.get("t")
            if type=="M":
                self.set_online(True)
                state = False
                if model=="pcSw3" or model=="pcSw1" :
                    if control_id==2:
                        state = payload.get("ps")==1
                    if control_id==5:
                        state = payload.get("au")==1
                    if control_id==6:
                        state = payload.get("lc")==1
                if model == "powerSwitch1":
                    state = payload.get("ps")==1
                self.update_state(state)
            
            if type=="DVOFF":
                self.set_online(False)
            if type=="S" or type=="N":
                if control_id==2:
                    pass
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
        if model=="pcSw3" or model=="pcSw1" or model == "powerSwitch1":
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
                for control_id in [2,5,6]:
                    entity_id = f"{DOMAIN}_{control_id}_{device_id}"
                    paras["control_id"] = control_id
                    paras["entity_id"] = entity_id
                    if control_id==2:
                        paras["state"] = last_msg.get('ps') == 1
                        paras["entity_name"] = "电源开关"
                        paras["entity_icon"] = "mdi:power"
                    if control_id==5:
                        paras["state"] = last_msg.get('au') == 1
                        paras["entity_name"] = "来电自启"
                        paras["entity_icon"] = "mdi:auto-mode"
                    if control_id==6:
                        paras["state"] = last_msg.get('lc') == 1
                        paras["entity_name"] = "童锁"
                        paras["entity_icon"] = "mdi:lock"
                    device_entities = SumsgSwitch(paras)
                    entities.append(device_entities)
                    mqtt.entities_append(entity_id,device_entities)
            #
            if model=="powerSwitch1":
                power_state = last_msg.get('ps') == 1
                paras["state"] = power_state
                # paras["entity_name"] = name
                device_entities = SumsgSwitch(paras)
                entities.append(device_entities)
                mqtt.entities_append(paras["entity_id"],device_entities)

    async_add_entities(entities)

    return True
