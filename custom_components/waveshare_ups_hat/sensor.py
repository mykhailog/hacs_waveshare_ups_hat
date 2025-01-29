import logging
import os
import voluptuous as vol

from homeassistant.components.sensor import SensorEntity, PLATFORM_SCHEMA, SensorDeviceClass
from homeassistant.const import PERCENTAGE, CONF_NAME, CONF_UNIQUE_ID
import homeassistant.helpers.config_validation as cv

from .ina219 import INA219
from .const import (
    MIN_CHARGING_CURRENT,
    MIN_ONLINE_CURRENT,
    MIN_BATTERY_CONNECTED_CURRENT,
    LOW_BATTERY_PERCENTAGE
)

_LOGGER = logging.getLogger(__name__)

ATTR_CAPACITY = "capacity"
ATTR_SOC = "soc"
ATTR_REAL_SOC = "real_soc"
ATTR_PSU_VOLTAGE = "psu_voltage"
ATTR_SHUNT_VOLTAGE = "shunt_voltage"
ATTR_LOAD_VOLTAGE = "load_voltage"
ATTR_CURRENT = "current"
ATTR_POWER = "power"
ATTR_CHARGING = "charging"
ATTR_ONLINE = "online"
ATTR_BATTERY_CONNECTED = "battery_connected"
ATTR_LOW_BATTERY = "low_battery"
ATTR_POWER_CALCULATED = "power_calculated"

ATTR_REMAINING_BATTERY_CAPACITY = "remaining_battery_capacity"
ATTR_REMAINING_TIME = "remaining_time_min"

CONF_BATTERY_CAPACITY = "battery_capacity"
CONF_MAX_SOC = 'max_soc'
DEFAULT_NAME = "waveshare_ups_hat"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_MAX_SOC, default=100): cv.positive_int,
    vol.Optional(CONF_BATTERY_CAPACITY): cv.positive_int,
    vol.Optional(CONF_UNIQUE_ID): cv.string,
})

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Waveshare UPS Hat sensor."""
    name = config.get(CONF_NAME)
    unique_id = config.get(CONF_UNIQUE_ID)
    max_soc = config.get(CONF_MAX_SOC)
    battery_capacity = config.get(CONF_BATTERY_CAPACITY)
    add_entities([WaveshareUpsHat(name, unique_id, max_soc, battery_capacity)], True)

class WaveshareUpsHat(SensorEntity):
    """Representation of a Waveshare UPS Hat."""

    def __init__(self, name, unique_id=None, max_soc=None, battery_capacity=None):
        """Initialize the sensor."""
        self._name = name
        self._unique_id = unique_id
        if max_soc > 100:
            max_soc = 100
        elif max_soc < 1:
            max_soc = 1
        self._max_soc = max_soc
        self._battery_capacity = battery_capacity
        self._ina219 = INA219(addr=0x42)
        self._attrs = {}

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def device_class(self):
        """Return the device class of the sensor."""
        return SensorDeviceClass.BATTERY

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._attrs.get(ATTR_SOC)

    @property
    def unit_of_measurement(self):
        """Return the unit the value is expressed in."""
        return PERCENTAGE

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""
        return self._attrs

    @property
    def unique_id(self):
        """Return the unique id of the sensor."""
        return self._unique_id

    def update(self):
        """Get the latest data and update the states."""
        ina219 = self._ina219
        bus_voltage = ina219.getBusVoltage_V()  # Voltage on V- (load side)
        shunt_voltage = (
            ina219.getShuntVoltage_mV() / 1000
        )  # Voltage between V+ and V- across the shunt
        current = ina219.getCurrent_mA()  # Current in mA
        power = ina219.getPower_W()  # Power in W

        real_soc = (bus_voltage - 6) / 2.4 * 100
        soc = (bus_voltage - 6) / (2.4 * (self._max_soc / 100.0)) * 100

        soc = min(max(soc, 0), 100)

        online = current > MIN_ONLINE_CURRENT
        charging = current > MIN_CHARGING_CURRENT
        low_battery = online and soc < LOW_BATTERY_PERCENTAGE
        power_calculated = bus_voltage * (current / 1000)

        if self._battery_capacity is None:
            remaining_battery_capacity = None
            remaining_time = None
        else:
            remaining_battery_capacity = (real_soc / 100.0) * self._battery_capacity
            if current < 0:
                remaining_time = round((remaining_battery_capacity / -current) * 60.0, 0)
            else:
                remaining_time = None

        self._attrs = {
            ATTR_CAPACITY: round(soc, 0),
            ATTR_SOC: round(soc, 0),
            ATTR_REAL_SOC: real_soc,
            ATTR_PSU_VOLTAGE: round(bus_voltage + shunt_voltage, 5),
            ATTR_LOAD_VOLTAGE: round(bus_voltage, 5),
            ATTR_SHUNT_VOLTAGE: round(shunt_voltage, 5),
            ATTR_CURRENT: round(current, 5),
            ATTR_POWER: round(power, 5),
            ATTR_POWER_CALCULATED: round(power_calculated, 5),
            ATTR_CHARGING: charging,
            ATTR_ONLINE: online,
            ATTR_REMAINING_BATTERY_CAPACITY: remaining_battery_capacity,
            ATTR_REMAINING_TIME: remaining_time,
            ATTR_LOW_BATTERY: low_battery
        }
