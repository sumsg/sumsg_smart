"""Config flow for SUMSG integration."""
from __future__ import annotations
from typing import Any
import asyncio
import logging
from .api import SumsgApi
from homeassistant import config_entries  # type: ignore
from homeassistant.data_entry_flow import FlowResult  # type: ignore
from homeassistant.helpers import config_validation as cv  # type: ignore
import voluptuous as vol  # type: ignore
import async_timeout  # type: ignore
from homeassistant.helpers.selector import SelectSelector, SelectSelectorConfig

from .const import (
    CONF_USER_NAME, CONF_PASSWORD, DOMAIN,
    CONF_DEVICE_TYPE, CONF_DEVICE_IP, CONF_WIFI_PASSWORD,
    DEVICE_TYPE_LAN, DEVICE_TYPE_CLOUD
)

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)
STEP_DEVICE_TYPE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DEVICE_TYPE, default=DEVICE_TYPE_CLOUD): vol.In(
            [DEVICE_TYPE_CLOUD, DEVICE_TYPE_LAN]
        )
    }
)
STEP_CLOUD_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USER_NAME, default=""): vol.All(cv.string, vol.Length(min=1, max=40)),
        vol.Required(CONF_PASSWORD): vol.All(cv.string, vol.Length(min=6, max=32)),
    }
)

STEP_LAN_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DEVICE_IP): cv.string,
        vol.Required(CONF_WIFI_PASSWORD): cv.string,
    }
)

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow"""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize flow."""
        self.device_type = None
        self.username = None
        self.password = None
        self.device_ip = None
        self.wifi_password = None
        self.token = None
        self.key = None
        self.secret = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step - device type selection."""
        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema({
                    vol.Required("device_type"): SelectSelector(
                        SelectSelectorConfig(
                            options=[
                                DEVICE_TYPE_CLOUD,
                                DEVICE_TYPE_LAN
                            ],
                            translation_key="device_type"
                        )
                    )
                })
            )# type: ignore

        self.device_type = user_input[CONF_DEVICE_TYPE]
        
        # 根据设备类型跳转到不同的配置步骤
        if self.device_type == DEVICE_TYPE_CLOUD:
            return await self.async_step_cloud_config()
        else:
            return await self.async_step_lan_config()

    async def async_step_cloud_config(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle cloud device configuration."""
        errors = {}
        
        if user_input is None:
            return self.async_show_form(
                step_id="cloud_config", 
                data_schema=STEP_CLOUD_DATA_SCHEMA,
                description_placeholders={"message": "请输入网络版本设备的账号密码"}
            )# type: ignore

        username = user_input[CONF_USER_NAME]
        password = user_input[CONF_PASSWORD]
        
        sumsgApi = SumsgApi(self.hass)
        try:
            async with async_timeout.timeout(10):
                user_info = await sumsgApi.login(username, password)
                code = user_info.get("code")
                msg = user_info.get("msg")
                if code != 200:
                    errors["base"] = msg
                    return self.async_show_form(
                        step_id="cloud_config", 
                        data_schema=STEP_CLOUD_DATA_SCHEMA, 
                        errors=errors
                    )# type: ignore
                
                self.username = username
                self.password = password
                self.token = user_info.get("body", {}).get("token")
                auth_info = user_info.get("body", {}).get("auth", {})
                self.key = auth_info.get("user")
                self.secret = auth_info.get("pass")
                
                await self.async_set_unique_id(f"cloud_{username}")
                self._abort_if_unique_id_configured()
                
                return self.async_create_entry(
                    title=f"Sumsg Cloud User {username}",
                    data={
                        "device_type": self.device_type,
                        "username": self.username,
                        "password": self.password,
                        "token": self.token,
                        "key": self.key,
                        "secret": self.secret,
                    }
                )# type: ignore
                
        except asyncio.TimeoutError:
            errors["base"] = "登录超时."
        except Exception as exc:
            _LOGGER.error("Cloud login error: %s", exc)
            errors["base"] = "未知错误"
        
        return self.async_show_form(
            step_id="cloud_config", 
            data_schema=STEP_CLOUD_DATA_SCHEMA, 
            errors=errors
        )# type: ignore

    async def async_step_lan_config(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle LAN device configuration."""
        errors = {}
        
        if user_input is None:
            return self.async_show_form(
                step_id="lan_config", 
                data_schema=STEP_LAN_DATA_SCHEMA,
                description_placeholders={"message": "请输入局域网版本设备的IP地址和WiFi密码"}
            )# type: ignore

        self.device_ip = user_input[CONF_DEVICE_IP]
        self.wifi_password = user_input[CONF_WIFI_PASSWORD]
        
        try:
            parts = self.device_ip.split('.')
            if len(parts) != 4 or not all(0 <= int(part) <= 255 for part in parts):
                errors["base"] = "无效的 IP 地址"
                return self.async_show_form(
                    step_id="lan_config", 
                    data_schema=STEP_LAN_DATA_SCHEMA, 
                    errors=errors
                )# type: ignore
        except ValueError:
            errors["base"] = "无效的 IP 地址"
            return self.async_show_form(
                step_id="lan_config", 
                data_schema=STEP_LAN_DATA_SCHEMA, 
                errors=errors
            )# type: ignore
        
        sumsgApi = SumsgApi(self.hass)
        lan_login = await sumsgApi.lan_login(self.device_ip, self.wifi_password)
        status = lan_login.get("status")
        if status != "ok":
            errors["base"] = "登录失败,请检查设备是否在线."
            return self.async_show_form(
                step_id="lan_config", 
                data_schema=STEP_LAN_DATA_SCHEMA, 
                errors=errors
            )# type: ignore
        self.token = lan_login.get("tK")
        unique_id = f"lan_{self.device_ip}"
        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured()
        return self.async_create_entry(
            title=f"Sumsg LAN Device {self.device_ip}",
            data={
                "device_type": self.device_type,
                "device_ip": self.device_ip,
                "token": self.token,
            }
        )# type: ignore