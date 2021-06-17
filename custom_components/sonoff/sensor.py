import logging

from homeassistant.helpers import device_registry as dr
from homeassistant import config_entries, core
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN, SensorEntity

from .api import EWeLinkApi, SonoffDevice
from .const import DOMAIN, EWELINK_API, SONOFF_SENSORS_MAP, SCAN_INTERVAL
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
    sensors = []
    for device in api.devices:
        for entity in map_device_to_entity(api, device):
            sensors.append(entity)
    async_add_entities(sensors, update_before_add=True)


class SonoffSensor(SensorEntity, EntityDeviceInfoMixin):
    """Representation of a Sonoff sensor."""

    def __init__(self, api: EWeLinkApi, sensor, device: SonoffDevice):
        super().__init__()
        self._api = api
        self._sensor = sensor
        self._device = device
        self._device_id = device.device_id
        _LOGGER.warning(f"{self.device_info}")

    @property
    def available(self):
        return self._device.available

    @property
    def name(self):
        device_class = SONOFF_SENSORS_MAP[self._sensor]["device_class"]
        return f"{self._device.name} {device_class}"

    @property
    def state(self):
        if self._sensor == "power":
            return self._device.power
        if self._sensor == "current":
            return self._device.current
        if self._sensor == "voltage":
            return self._device.voltage

    @property
    def device_class(self):
        return SONOFF_SENSORS_MAP[self._sensor]["device_class"]

    @property
    def unit_of_measurement(self):
        return SONOFF_SENSORS_MAP[self._sensor]["uom"]

    @property
    def unique_id(self):
        device_class = SONOFF_SENSORS_MAP[self._sensor]["device_class"]
        return f"{SENSOR_DOMAIN}.{DOMAIN}_{self._device.device_id}_{device_class}"

    @property
    def icon(self):
        return SONOFF_SENSORS_MAP[self._sensor]["icon"]

    @property
    def device_info(self):
        return self.device_info_property()
    #     return {
    #         "identifiers": {
    #             # Serial numbers are unique identifiers within a specific domain
    #             (DOMAIN, self._device_id)
    #         },
    #         "name": self.name,
    #         "manufacturer": "eWeLink",
    #     }

    async def async_update(self):
        self._device = self._api.device(self._device_id)


def map_device_to_entity(api: EWeLinkApi, device: SonoffDevice):
    if device.power:
        yield SonoffSensor(api, "power", device)
    if device.voltage:
        yield SonoffSensor(api, "voltage", device)
    if device.current:
        yield SonoffSensor(api, "current", device)
