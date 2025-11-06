import asyncio
import json
import logging

from .switch_rest import SumsgApi, SumsgSwitchRest
from .switch_mqtt import SumsgSwitchMQTT # type: ignore
from .models import MQTT_C, MQTT_DATA
from homeassistant.components.switch import SwitchEntity # type: ignore
from homeassistant.core import HomeAssistant # type: ignore
from homeassistant.config_entries import ConfigEntry # type: ignore
from .const import  DOMAIN,DEVICE_TYPE_CLOUD,DEVICE_TYPE_LAN
from homeassistant.helpers.device_registry import DeviceInfo # type: ignore
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
                        device_entities = SumsgSwitchMQTT(paras)
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
                            #
                if model=="powerSwitch1":
                    power_state = last_msg.get('ps') == 1
                    paras["state"] = power_state
                    # paras["entity_name"] = name
                    device_entities = SumsgSwitchMQTT(paras)
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
        for control_id in [2,5,6]:
            entity_id = f"{DOMAIN}_{control_id}_{device_id}"
            paras["control_id"] = control_id
            paras["entity_id"] = entity_id
            if control_id==2:
                paras["entity_name"] = "电源开关"
                paras["entity_icon"] = "mdi:power"
            if control_id==5:
                paras["entity_name"] = "来电自启"
                paras["entity_icon"] = "mdi:auto-mode"
            if control_id==6:
                paras["entity_name"] = "童锁"
                paras["entity_icon"] = "mdi:lock"
            device_entities = SumsgSwitchRest(paras)
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

        task = asyncio.create_task(
            _periodic_update_task(hass, device_ip, token, device_id)
        )
        hass.data[DOMAIN][device_id]["task"] = task

    async_add_entities(entities)

    return True

async def _periodic_update_task(hass, device_ip, token, device_id):
    api = SumsgApi(hass)
    while True:
        try:
            await asyncio.sleep(2)
            states = await api.lan_get_device_state(device_ip, token)
            # _LOGGER.debug(f"[{states}] 状态同步成功")
            if isinstance(states, dict):
                entities = hass.data[DOMAIN][device_id]["entities"]
                for device_entity in entities:
                    control_id = device_entity.get_control_id()
                    if control_id == 0:
                        device_entity.update_state(states.get('tP', 0))
                    if control_id == 2:
                        device_entity.update_state(states.get('pW', False))
                    if control_id == 5:
                        device_entity.update_state(states.get('aS', False))
                    if control_id == 6:
                        device_entity.update_state(states.get('cL', False))
        except Exception as e:
            _LOGGER.warning(f"[{device_ip}] 状态同步失败: {e}")