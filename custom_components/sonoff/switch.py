import logging
from homeassistant.helpers import device_registry as dr
from homeassistant import config_entries, core
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN, SwitchEntity
from .api import EWeLinkApi, SonoffDevice
from .const import DOMAIN, EWELINK_API, SCAN_INTERVAL
from .mixins import EntityDeviceInfoMixin

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = SCAN_INTERVAL


async def async_setup_entry(
    hass: core.HomeAssistant,
    entry: config_entries.ConfigEntry,
    async_add_entities,
):
    """Set up entry."""
    api: EWeLinkApi = hass.data[DOMAIN][entry.entry_id][EWELINK_API]
    switches = []
    for device in api.devices:
        for entity in map_device_to_entity(api, device):
            switches.append(entity)
    async_add_entities(switches, update_before_add=True)


class SonoffSwitch(SwitchEntity, EntityDeviceInfoMixin):
    def __init__(self, api: EWeLinkApi, channel: int, device: SonoffDevice) -> None:
        super().__init__()
        #  , i, f"{device.name} {i}", switch, device.available
        self._api = api
        self._device = device
        self._device_id = device.device_id
        self._channel = channel

    @property
    def available(self):
        return self._device.available

    @property
    def name(self):
        return self._device.name

    @property
    def is_on(self):
        return self._device.switches[self._channel]

    @property
    def unique_id(self):
        return f"{SWITCH_DOMAIN}.{DOMAIN}_{self._device.device_id}_{self._channel}"

    async def async_turn_on(self, **kwargs):
        self._api.switch(self._device_id, self._channel, True)
        self._state = True

    async def async_turn_off(self, **kwargs):
        self._api.switch(self._device_id, self._channel, False)
        self._state = False

    async def async_toggle(self, **kwargs):
        self._api.switch(self._device_id, self._channel, not self._state)
        self._state = not self._state

    async def async_update(self):
        self._device = self._api.device(self._device_id)


def map_device_to_entity(api: EWeLinkApi, device: SonoffDevice):
    for i in range(len(device.switches)):
        yield SonoffSwitch(api, i, device)
