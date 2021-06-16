from .api import SonoffDevice
from .const import DOMAIN


class EntityDeviceInfoMixin:
    _device: SonoffDevice
    _device_id: str
    name: str

    @property
    def device_info(self):
        return {
            "identifiers": {
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self._device_id)
            },
            "name": self.name,
            "manufacturer": "eWeLink",
            "model": self._device.model,
            "sw_version": self._device.firmware_version,
        }
