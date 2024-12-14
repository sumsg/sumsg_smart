
import logging
import async_timeout  # type: ignore

from .api import SumsgApi
from homeassistant.helpers.device_registry import DeviceEntry # type: ignore
from homeassistant.helpers.typing import ConfigType # type: ignore
from homeassistant.core import HomeAssistant  # type: ignore
from .mqtt_client import MqttClient
import homeassistant.helpers.config_validation as cv # type: ignore
from homeassistant.config_entries import ConfigEntry  # type: ignore

_LOGGER = logging.getLogger(__name__)
from .const import  DOMAIN, CONF_USER_NAME, CONF_PASSWORD
from .models import ( 
    MQTT_C,
    MQTT_DATA,
)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Setup the Hello State component. """
    _LOGGER.info("sumsg async_setup")
    return True

#hass.config_entries
async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> bool:
    """Set up platform from a ConfigEntry."""
    _LOGGER.info("sumsg 启动")
    # 
    token = config_entry.data.get("token")
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
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setups(config_entry, ["switch","sensor","button"])
    )
    return True

async def async_update_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    _LOGGER.info(f"{DOMAIN} update_entry")
    return True
# unload_entry
async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    _LOGGER.info(f"{DOMAIN} unload_entry")
    mqtt_data: MQTT_DATA
    if DOMAIN in hass.data:
        mqtt_data = hass.data[DOMAIN][MQTT_C]
        client = mqtt_data.client
        client.disconnect()
        client.clear_entities()
    unload_ok = await hass.config_entries.async_unload_platforms(config_entry, ["switch", "sensor", "button"])
    return unload_ok
# remove_entry
async def async_remove_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    _LOGGER.info(f"{DOMAIN} remove_entry")
    if not hass.data[DOMAIN]:
        hass.data.pop(DOMAIN)
    return True
async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: ConfigEntry, device_entry: DeviceEntry
) -> bool:
    """Remove a config entry from a device."""
    return True