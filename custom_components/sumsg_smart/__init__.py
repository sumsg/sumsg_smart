import logging
import async_timeout  # type: ignore

from .api import SumsgApi
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.typing import ConfigType # type: ignore
from homeassistant.core import HomeAssistant  # type: ignore
from .mqtt_client import MqttClient
import homeassistant.helpers.config_validation as cv # type: ignore
from homeassistant.config_entries import ConfigEntry  # type: ignore

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)
from .const import DOMAIN, DEVICE_TYPE_LAN, DEVICE_TYPE_CLOUD
from .models import MQTT_C, MQTT_DATA

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Setup the Hello State component. """
    _LOGGER.info("sumsg async_setup")
    return True

#hass.config_entries
async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> bool:
    """Set up platform from a ConfigEntry."""
    _LOGGER.info("sumsg start")
    # 
    device_type = config_entry.data.get("device_type")
    token = config_entry.data.get("token")
    _LOGGER.debug(f"device_type: {device_type}")
    if device_type == DEVICE_TYPE_CLOUD:
        key = config_entry.data.get("key")
        secret = config_entry.data.get("secret")
        if token is None or key is None or secret is None:
            return False
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][config_entry.entry_id] = config_entry.data
        # 
        sumsgApi = SumsgApi( hass )
        try:
            async with async_timeout.timeout(10):
                user_info = await sumsgApi.get_devices(token)
                code = user_info.get("code")
                if code == 200:
                    devices = user_info.get("body", {}).get("deviceList")
                    hass.data[DOMAIN]["devices"] = devices
                    mqttC = MqttClient( hass, key, secret, devices)
                    await mqttC.connect()
                    hass.data[DOMAIN][MQTT_C] = MQTT_DATA( client=mqttC)
                    # _LOGGER.info(devices)
                else:
                    msg = user_info.get("msg")
                    _LOGGER.error(msg)
        except Exception:
            _LOGGER.error(f"{DOMAIN} get_devices fail")
        # load platforms
        await hass.config_entries.async_forward_entry_setups(config_entry, ["switch","sensor","button"])
    elif device_type == DEVICE_TYPE_LAN:
        await hass.config_entries.async_forward_entry_setups(config_entry, ["switch","sensor","button"])
    else:
        _LOGGER.error(f"Unknown device type: {device_type}")
        return False
    _LOGGER.info("sumsg setup completed successfully")
    return True

async def async_update_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    _LOGGER.info(f"{DOMAIN} 更新条目")
    return True
# unload_entry
async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    device_type = config_entry.data.get("device_type")
    _LOGGER.info(f"{DOMAIN} 禁用条目:{device_type}")
    device_registry = dr.async_get(hass)
    devices = dr.async_entries_for_config_entry(device_registry, config_entry.entry_id)
    for device_entry in devices:
        device_id = _extract_device_id_from_identifiers(device_entry.identifiers)
        device_data = hass.data[DOMAIN].get(device_id)
        if device_type == DEVICE_TYPE_LAN:
            if device_data["task"] is not None:
                device_data["task"].cancel()
        if device_type == DEVICE_TYPE_CLOUD:
            if device_data["mqtt"] is not None:
                device_data["mqtt"].disconnect()
        hass.data[DOMAIN].pop(device_id, None)
    unload_ok = await hass.config_entries.async_unload_platforms(
            config_entry, ["switch", "sensor", "button"]
        )
    return unload_ok
# remove_entry
async def async_remove_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    device_type = config_entry.data.get("device_type")
    device_registry = dr.async_get(hass)
    devices = dr.async_entries_for_config_entry(device_registry, config_entry.entry_id)
    for device_entry in devices:
        device_id = _extract_device_id_from_identifiers(device_entry.identifiers)
        device_data = hass.data[DOMAIN].get(device_id)
        if not device_data:
            continue 
        if device_type == DEVICE_TYPE_LAN:
            if device_data["task"] is not None:
                device_data["task"].cancel()
        if device_type == DEVICE_TYPE_CLOUD:
            if device_data["mqtt"] is not None:
                device_data["mqtt"].disconnect()
        hass.data[DOMAIN].pop(device_id, None)
    for device_entry in devices:
        device_registry.async_remove_device(device_entry.id)
    return True
async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: ConfigEntry, device_entry: dr.DeviceEntry
) -> bool:
    """Remove a device from a config entry."""
    device_registry = dr.async_get(hass)
    entity_registry = er.async_get(hass)
    device_id= device_entry.id
    # 删除设备关联的所有实体
    for entity in er.async_entries_for_device(entity_registry, device_id):
        entity_registry.async_remove(entity.entity_id)

    # 删除设备
    if device_registry.async_get(device_id):
        device_registry.async_remove_device(device_id)

    device_type = config_entry.data.get("device_type")
    if device_type == DEVICE_TYPE_LAN:
        await hass.config_entries.async_remove(config_entry.entry_id)
    return True
def _extract_device_id_from_identifiers(identifiers: set) -> str | None:
    try:
        for identifier_tuple in identifiers:
            if identifier_tuple[0] == DOMAIN:
                return identifier_tuple[1]
        return None
    except (IndexError, TypeError) as ex:
        _LOGGER.error(f"Error extracting device ID from identifiers {identifiers}: {ex}")
        return None