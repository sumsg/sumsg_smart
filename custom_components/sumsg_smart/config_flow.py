"""Config flow for pulsatrix (MQTT) integration."""
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
from .const import CONF_USER_NAME, CONF_PASSWORD, DOMAIN, DEFAULT_NAME

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USER_NAME, default=""): vol.All(cv.string, vol.Length(min=1, max=40)),
        vol.Required(CONF_PASSWORD): vol.All(cv.string, vol.Length(min=6, max=32)),
    }
)

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow"""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize flow."""
        self.username = None
        self.password = None
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}
        username = user_input[CONF_USER_NAME]
        password = user_input[CONF_PASSWORD]
        sumsgApi = SumsgApi( self.hass )
        try:
            async with async_timeout.timeout(5):
                user_info = await sumsgApi.login(username, password )
                code = user_info.get("code")
                msg = user_info.get("msg")
                if code != 200:
                    errors["base"] = msg
                    return self.async_show_form(
                        step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
                    )
                # token
                token = user_info.get("body", {}).get("token")
                # user and pass
                auth_info = user_info.get("body", {}).get("auth", {})
                key = auth_info.get("user")
                secret = auth_info.get("pass")
                # save config_entry
                return self.async_create_entry(
                    title=f"Sumsg User {username}",
                    data={
                        "token": token,
                        "key": key,
                        "secret": secret,
                    }
                )
        except asyncio.TimeoutError as exc:
            errors["timeout"] = "Timeout"
        except Exception:
            errors["unknown"] = "unknown"
        else:
            await self.async_set_unique_id(user_input[CONF_USER_NAME])
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=DEFAULT_NAME, data=user_input)

        #
        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

