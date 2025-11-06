import logging
import json

from .sensor_rest import SumsgSensorRest
from .sensor_mqtt import SumsgSensorMQTT
from homeassistant.components.sensor import SensorEntity # type: ignore
from homeassistant.core import HomeAssistant # type: ignore
from homeassistant.config_entries import ConfigEntry # type: ignore
from homeassistant.helpers.device_registry import DeviceInfo # type: ignore
from .const import   DOMAIN,DEVICE_TYPE_CLOUD,DEVICE_TYPE_LAN
from .models import MQTT_C, MQTT_DATA
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
            if model=="pcSw3" or model=="pcSw1" or model == "pcHealth1":
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
                    "entity_icon":"mdi:tag",
                    "topic":topic,
                    "state":False,
                    "control_id":0,
                    "entity_name":name,
                    "entity_id":f"{DOMAIN}_0_{device_id}",
                    "entity_unit":"°C"
                }
                last_msg_str = device.get('lastMsg', '{}')
                try:
                    last_msg = json.loads(last_msg_str) if last_msg_str else {}
                except json.JSONDecodeError as exc:
                    _LOGGER.error("Failed to parse JSON: %s", exc)
                    last_msg = {}
                #
                if model=="pcSw3" or model=="pcSw1":
                    control_id = 0
                    entity_id = f"{DOMAIN}_{control_id}_{device_id}"
                    paras["control_id"] = control_id
                    paras["state"] = last_msg.get('tp')
                    paras["entity_name"] = "机箱温度"
                    paras["entity_icon"] = "mdi:thermometer"
                    device_entities = SumsgSensorMQTT(paras)
                    entities.append(device_entities)
                    if mqtt is not None:
                        mqtt.entities_append(entity_id,device_entities)
                    if DOMAIN not in hass.data:
                        hass.data[DOMAIN] = {}
                    if device_id not in hass.data[DOMAIN]:
                        hass.data[DOMAIN][device_id] = {
                            "entities": [],
                            "mqtt": mqtt,
                        }
                    hass.data[DOMAIN][device_id]["entities"].append(device_entities)
                # if model == "pcHealth1":
                #     control_id = 0
                #     entity_id = f"{DOMAIN}_{control_id}_{device_id}"
                #     paras["control_id"] = control_id
                #     paras["online"] = True
                #     paras["state"] = "60% | 12.8 | 12.8" #last_msg.get('tp')
                #     paras["entity_name"] = "server"
                #     paras["entity_icon"] = "mdi:thermometer"
                #     device_entities = SumsgSensor(paras)
                #     entities.append(device_entities)
                #     mqtt.entities_append(entity_id,device_entities)

    elif device_type == DEVICE_TYPE_LAN:
        entities = []
        device_ip = config_entry.data.get('device_ip')
        token = config_entry.data.get('token')
        device_id = f"{device_ip}_{token}"
        paras = {
            "hass":hass,
            "device_ip":config_entry.data.get('device_ip'),
            "token":config_entry.data.get('token'),
            "model":"HA_WBC_2",
            "name":"远程WiFi开机卡",
            "device_id":device_id,
            "entity_icon":"mdi:thermometer",
            "state":False,
            "control_id":0,
            "entity_name":"机箱温度",
            "entity_id":f"{DOMAIN}_0_{device_id}",
            "entity_unit":"°C"
        }

        device_entities = SumsgSensorRest(paras)
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