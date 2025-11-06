
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
_LOGGER.setLevel(logging.DEBUG)
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
    async def lan_login(self, device_ip, password) -> dict[str, Any]:
        form_data = {
            "password": password
        }
        url = f"http://{device_ip}/api/login"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.post(url, data=form_data, headers=headers, ssl=SSL_CONTEXT) as response:
                    data = await response.json()
                    return data
            except aiohttp.ClientError as e:
                _LOGGER.error(f"HTTP Request failed: {e}")
        return {}
    async def lan_get_device_state(self, device_ip: str, token: str):
        url = f"http://{device_ip}/api/getDeviceState"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        async with aiohttp.ClientSession() as session:
                    try:
                        async with session.get(url,  headers=headers, ssl=SSL_CONTEXT) as response:
                            data = await response.json()
                            return data
                    except aiohttp.ClientError as e:
                        _LOGGER.error(f"HTTP Request failed: {e}")
    async def lan_set_power_state(self, device_ip: str, token: str, state: bool):
        url = f"http://{device_ip}/api/setPowerState"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        form_data = {"state": "true" if state else "false"}
        async with aiohttp.ClientSession() as session:
                    try:
                        async with session.post(url,  headers=headers, data=form_data, ssl=SSL_CONTEXT) as response:
                            data = await response.json()
                            return data
                    except aiohttp.ClientError as e:
                        _LOGGER.error(f"HTTP Request failed: {e}")
    async def lan_set_auto_start_state(self, device_ip: str, token: str, state: bool) -> dict[str, Any]:
        """Set auto start state on LAN device."""
        url = f"http://{device_ip}/api/setAutoStartState"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        form_data = {"state": "true" if state else "false"}
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, headers=headers, data=form_data, ssl=SSL_CONTEXT) as response:
                    data = await response.json()

                    return data
            except aiohttp.ClientError as e:
                _LOGGER.error(f"HTTP Request failed: {e}")
        return {}

    async def lan_set_reboot_state(self, device_ip: str, token: str) -> dict[str, Any]:
        """Reboot LAN device."""
        url = f"http://{device_ip}/api/setRebootState"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        form_data = {"reboot": "true"}
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, headers=headers, data=form_data, ssl=SSL_CONTEXT) as response:
                    data = await response.json()
                    return data
            except aiohttp.ClientError as e:
                _LOGGER.error(f"HTTP Request failed: {e}")
        return {}

    async def lan_set_child_lock_state(self, device_ip: str, token: str, state: bool) -> dict[str, Any]:
        """Set child lock state on LAN device."""
        url = f"http://{device_ip}/api/setChildLockState"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        form_data = {"state": "true" if state else "false"}
        _LOGGER.debug(f"Set child lock state to {state}")
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, headers=headers, data=form_data, ssl=SSL_CONTEXT) as response:
                    data = await response.json()
                    return data
            except aiohttp.ClientError as e:
                _LOGGER.error(f"HTTP Request failed: {e}")
        return {}

    async def lan_set_force_shutdown(self, device_ip: str, token: str) -> dict[str, Any]:
        """Force shutdown LAN device."""
        url = f"http://{device_ip}/api/setForceShutdown"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        form_data = {"shutdown": "true"}
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, headers=headers, data=form_data, ssl=SSL_CONTEXT) as response:
                    data = await response.json()
                    return data
            except aiohttp.ClientError as e:
                _LOGGER.error(f"HTTP Request failed: {e}")
        return {}