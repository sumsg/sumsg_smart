import logging
import json
import hashlib
from .models import MQTT_C, MQTT_DATA
import voluptuous as vol # type: ignore
from .button_mqtt import SumsgButtonMQTT # type: ignore
from .button_rest import SumsgButtonRest
from homeassistant.components.button import ButtonEntity  # type: ignore
from homeassistant.core import HomeAssistant  # type: ignore
from homeassistant.config_entries import ConfigEntry  # type: ignore
from homeassistant.helpers.device_registry import DeviceInfo # type: ignore
from .const import  DOMAIN,DEVICE_TYPE_CLOUD,DEVICE_TYPE_LAN
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities,
):

    device_type = config_entry.data.get("device_type")
    if device_type == DEVICE_TYPE_CLOUD:
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
                        device_entities = SumsgButtonMQTT(paras)
                        entities.append(device_entities)
                        if mqtt is not None:
                            mqtt.entities_append(entity_id,device_entities)
                        if device_id not in hass.data[DOMAIN]:
                            hass.data[DOMAIN][device_id] = {
                                "entities": [],
                                "mqtt": mqtt,
                            }
                        hass.data[DOMAIN][device_id]["entities"].append(device_entities)
    elif device_type == DEVICE_TYPE_LAN:
        entities = []
        device_ip = config_entry.data.get('device_ip')
        token = config_entry.data.get('token')
        device_id = f"{device_ip}_{token}"
        paras = {
            "hass":hass,
            "model":"HA_WBC_2",
            "device_ip":config_entry.data.get('device_ip'),
            "token":config_entry.data.get('token'),
            "name":"远程WiFi开机卡",
            "device_id":device_id,
            "entity_icon":"mdi:power",
            "state":False,
            "control_id":0,
            "entity_name":"",
            "entity_id":f"{DOMAIN}_0_{device_id}"
        }
        for control_id in [3,4]:
            entity_id = f"{DOMAIN}_{control_id}_{device_id}"
            paras["control_id"] = control_id
            paras["entity_id"] = entity_id
            if control_id==3:
                paras["entity_name"] = "重启"
                paras["entity_icon"] = "mdi:restart"
            if control_id==4:
                paras["entity_name"] = "强制关机"
                paras["entity_icon"] = "mdi:television-stop"
            device_entities = SumsgButtonRest(paras)
            entities.append(device_entities)
            ##
            if DOMAIN not in hass.data:
                hass.data[DOMAIN] = {}
            if device_id not in hass.data[DOMAIN]:
                hass.data[DOMAIN][device_id] = {
                    "entities": [],
                    "task": None,
                }
            hass.data[DOMAIN][device_id]["entities"].append(device_entities)

    async_add_entities(entities)
    return True
