from datetime import timedelta
import logging
from typing import Dict

from homeassistant import config_entries
from homeassistant.const import (
    CONF_EMAIL,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
)
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

from .const import (
    CONF_API_REGION,
    CONF_DEBUG,
    CONF_ENTITY_PREFIX,
    CONF_GRACE_PERIOD,
    DOMAIN,
)

_LOGGING = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_API_REGION, default="eu"): cv.string,
    }
)


def validate(info) -> bool:
    return True


class SonoffConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, info):
        errors: Dict[str, str] = {}
        if info is not None:
            if not validate(info):
                errors["base"] = "auth"

            if not errors:
                self.data = info
                return self.async_create_entry(title="eWeLink Sonoff", data=self.data)

            pass  # TODO: process info

        return self.async_show_form(
            step_id="user", data_schema=CONFIG_SCHEMA, errors=errors
        )
