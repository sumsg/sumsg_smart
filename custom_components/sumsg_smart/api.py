
import ssl
import logging
import uuid
import aiohttp # type: ignore
from homeassistant.core import HomeAssistant # type: ignore
from typing import Any, Dict
from .router import BASE_URL, DEVICE_LIST, SINGIN
SSL_CONTEXT = ssl.create_default_context()
SSL_CONTEXT.check_hostname = False
SSL_CONTEXT.verify_mode = ssl.CERT_NONE
_LOGGER = logging.getLogger(__name__)

DevicesDictType = Dict[int, Dict[str, Any]]
class SumsgApi:
    def __init__(
        self,
        hass: HomeAssistant,
    ):
        """Initialize SumsgApi."""
        self.hass = hass
    async def login(self, username, password) -> dict[str, Any]:
        payload = {
            "path":SINGIN,
            "body":{
                "account": username,
                "password": password,
                "device": {
                    "deviceId": str(uuid.uuid5(uuid.NAMESPACE_DNS, username+password)),
                }
            }
        }
        headers = {"Content-Type": "application/json"}
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(BASE_URL+SINGIN, json=payload, headers=headers, ssl=SSL_CONTEXT) as response:
                    data = await response.json()
                    return data
            except aiohttp.ClientError as e:
                _LOGGER.error(f"HTTP Request failed: {e}")
        return {}
    async def get_devices(self,token) -> dict[str, Any]:
        payload = {
            "path":DEVICE_LIST,
            "body":{}
        }
        headers = {"Content-Type": "application/json","x-token":token}
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(BASE_URL+DEVICE_LIST, json=payload, headers=headers, ssl=SSL_CONTEXT) as response:
                    data = await response.json()
                    return data
            except aiohttp.ClientError as e:
                _LOGGER.error(f"HTTP Request failed: {e}")
        return {}