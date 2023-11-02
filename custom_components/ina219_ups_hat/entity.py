
from .const import DOMAIN
from .coordinator import INA219UpsHatCoordinator
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo


class INA219UpsHatEntity():
    def __init__(self, coordinator: INA219UpsHatCoordinator) -> None:
        self._coordinator = coordinator
        self._device_id = self._coordinator.id_prefix

    @property
    def name(self):
        return self._coordinator.name_prefix + ' ' + self._name

    @property
    def unique_id(self):
        return self._coordinator.id_prefix + '_' + self._name

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device_info of the device."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._coordinator.id_prefix)},
            name=self._coordinator.name_prefix,
            manufacturer="Some Chinese factory",
            sw_version="0.3.0",
        )

    async def async_update(self):
        await self._coordinator.async_request_refresh()
