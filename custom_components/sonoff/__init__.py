import asyncio
from datetime import timedelta
import logging

from homeassistant import config_entries, core
from homeassistant.const import (
    CONF_EMAIL,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

from .api import EWeLinkApi
from .const import (
    CONF_API_REGION,
    CONF_DEBUG,
    CONF_ENTITY_PREFIX,
    CONF_GRACE_PERIOD,
    DOMAIN,
    EWELINK_API,
)

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Exclusive(CONF_USERNAME, CONF_PASSWORD): cv.string,
                vol.Exclusive(CONF_EMAIL, CONF_PASSWORD): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
                vol.Optional(CONF_API_REGION, default="eu"): cv.string,
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=timedelta(seconds=30)
                ): cv.time_period,
                vol.Optional(CONF_GRACE_PERIOD, default=600): cv.positive_int,
                vol.Optional(CONF_ENTITY_PREFIX, default=True): cv.boolean,
                vol.Optional(CONF_DEBUG, default=False): cv.boolean,
            },
            extra=vol.ALLOW_EXTRA,
        ),
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup_entry(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry
) -> bool:
    """Set up platform from a ConfigEntry."""
    hass.data.setdefault(DOMAIN, {})
    hass_data = dict(entry.data)
    # Registers update listener to update config entry when options are updated.
    unsub_options_update_listener = entry.add_update_listener(options_update_listener)
    # Store a reference to the unsubscribe function to cleanup if an entry is unloaded.
    hass_data["unsub_options_update_listener"] = unsub_options_update_listener
    hass.data[DOMAIN][entry.entry_id] = hass_data
    ewelink_api = EWeLinkApi(hass_data["username"], hass_data["password"], hass_data["api_region"])
    hass_data[EWELINK_API] = ewelink_api
    session = async_get_clientsession(hass)
    await ewelink_api.do_login(session)
    # Forward the setup to the sensor platform.
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "switch")
    )
    return True


async def options_update_listener(
    hass: core.HomeAssistant, config_entry: config_entries.ConfigEntry
):
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_unload_entry(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry
) -> bool:
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, "sensor"),
                hass.config_entries.async_forward_entry_unload(entry, "switch"),
            ]
        )
    )
    # Remove options_update_listener.
    hass.data[DOMAIN][entry.entry_id]["unsub_options_update_listener"]()

    # Remove config entry from domain.
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_setup(hass: core.HomeAssistant, config: dict) -> bool:
    """Set up the eWeLink Sonoff component."""
    # for component in ["switch", "sensor"]:
    #     discovery.load_platform(hass, component, DOMAIN, {}, config)

    hass.data.setdefault(DOMAIN, {})
    return True
