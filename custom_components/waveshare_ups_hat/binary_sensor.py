import voluptuous as vol
from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
import homeassistant.helpers.config_validation as cv
from .ina219 import INA219
from .const import MIN_ONLINE_CURRENT

DEFAULT_NAME = "waveshare_ups_hat_online"

def setup_platform(
    hass,
    config,
    add_entities,
    discovery_info=None,
):
    """Set up an Online Status binary sensor."""
    add_entities([OnlineStatus(config, {})], True)

class OnlineStatus(BinarySensorEntity):
    """Representation of an UPS online status."""

    def __init__(self, config, data):
        """Initialize the UPS online status binary device."""
        self._name = DEFAULT_NAME
        self._ina219 = INA219(addr=0x42)
        self._state = True

    @property
    def name(self):
        """Return the name of the UPS online status sensor."""
        return self._name

    @property
    def device_class(self):
        """Return the device class of the binary sensor."""
        return BinarySensorDeviceClass.POWER

    @property
    def is_on(self):
        """Return true if the UPS is online, else false."""
        return self._state

    def update(self):
        """Get the status from UPS online status and set this entity's state."""
        self._state = self._ina219.getCurrent_mA() > MIN_ONLINE_CURRENT
