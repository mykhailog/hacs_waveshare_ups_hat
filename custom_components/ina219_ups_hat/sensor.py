"""Details about the INA219 UPS Hat sensor"""
import logging
import os

import voluptuous as vol

from homeassistant.components.sensor import SensorEntity, PLATFORM_SCHEMA
from homeassistant.const import (
    DEVICE_CLASS_BATTERY,
    PERCENTAGE,
    CONF_NAME,
    CONF_UNIQUE_ID,
)
import homeassistant.helpers.config_validation as cv


_LOGGER = logging.getLogger(__name__)

from .ina219 import INA219
from .ina219_wrapper import INA219Wrapper
from .const import (
    MIN_CHARGING_CURRENT,
    MIN_ONLINE_CURRENT,
    MIN_BATTERY_CONNECTED_CURRENT,
    LOW_BATTERY_PERCENTAGE,
)

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
CONF_MAX_SOC = "max_soc"
CONF_SMA_SAMPLES = "sma_samples"
CONF_BATTERIES_COUNT = "batteries_count"
DEFAULT_NAME = "ina219_ups_hat"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_MAX_SOC, default=100): cv.positive_int,
        vol.Optional(CONF_BATTERY_CAPACITY): cv.positive_int,
        vol.Optional(CONF_BATTERIES_COUNT, default=2): cv.positive_int,
        vol.Optional(CONF_SMA_SAMPLES, default=5): cv.positive_int,
        vol.Optional(CONF_UNIQUE_ID): cv.string,
    }
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the INA219 UPS Hat sensor."""
    name = config.get(CONF_NAME)
    unique_id = config.get(CONF_UNIQUE_ID)
    max_soc = config.get(CONF_MAX_SOC)
    battery_capacity = config.get(CONF_BATTERY_CAPACITY)
    batteries_count = config.get(CONF_BATTERIES_COUNT)
    sma_samples = config.get(CONF_SMA_SAMPLES)
    add_entities([INA219UpsHat(name, unique_id, max_soc, battery_capacity, batteries_count, sma_samples)], True)


class INA219UpsHat(SensorEntity):
    """Representation of a INA219 UPS Hat."""

    def __init__(self, name, unique_id=None, max_soc=None, battery_capacity=None, batteries_count=None, sma_samples=None):
        """Initialize the sensor."""
        self._name = name
        self._unique_id = unique_id
        if max_soc > 100:
            max_soc = 100
        elif max_soc < 1:
            max_soc = 1
        self._max_soc = max_soc
        self._battery_capacity = battery_capacity
        self._batteries_count = batteries_count
        self._ina219 = INA219(addr=0x41)
        self._ina219_wrapper = INA219Wrapper(self._ina219, sma_samples)
        self._attrs = {}

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def device_class(self):
        """Return the device class of the sensor."""
        return DEVICE_CLASS_BATTERY

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
        """Get the latest data and updates the states."""
        ina219_wrapper = self._ina219_wrapper
        ina219_wrapper.measureINAValues()

        bus_voltage = ina219_wrapper.getBusVoltageSMA_V()  # voltage on V- (load side)
        shunt_voltage = (ina219_wrapper.getShuntVoltageSMA_mV() / 1000)  # voltage between V+ and V- across the shunt
        current = ina219_wrapper.getCurrentSMA_mA()  # current in mA
        power = ina219_wrapper.getPowerSMA_W()  # power in W

        smooth_bus_voltage = ina219_wrapper.getBusVoltageSMAx2_V()
        smooth_current = ina219_wrapper.getCurrentSMAx2_mA()

        soc_c1 = 3 * self._batteries_count
        soc_c2 = 1.2 * self._batteries_count
        real_soc = (smooth_bus_voltage - soc_c1) / soc_c2 * 100
        soc = (smooth_bus_voltage - soc_c1) / (soc_c2 * (self._max_soc / 100.0)) * 100

        if soc > 100:
            soc = 100
        if soc < 0:
            soc = 0

        # battery_connected = current > MIN_BATTERY_CONNECTED_CURRENT

        online = bool(current > MIN_ONLINE_CURRENT)
        charging = bool(current > MIN_CHARGING_CURRENT)

        low_battery = bool(online and (soc < LOW_BATTERY_PERCENTAGE))
        power_calculated = bus_voltage * (current / 1000)

        if self._battery_capacity is None:
            remaining_battery_capacity = None
            remaining_time = None
        else:
            remaining_battery_capacity = (real_soc / 100.0) * self._battery_capacity
            if not online:
                remaining_time = round(
                    (remaining_battery_capacity / -smooth_current) * 60.0, 0
                )
            else:
                remaining_time = None

        # if not battery_connected:
        #    capacity = 0.0  # no battery no capacity

        self._attrs = {
            ATTR_CAPACITY: round(soc, 0),
            ATTR_SOC: round(soc, 0),
            ATTR_REAL_SOC: real_soc,
            ATTR_PSU_VOLTAGE: round(bus_voltage + shunt_voltage, 5),
            ATTR_LOAD_VOLTAGE: round(bus_voltage, 5),
            ATTR_SHUNT_VOLTAGE: round(shunt_voltage, 5),
            ATTR_CURRENT: round(current / 1000, 5),
            ATTR_POWER: round(power, 5),
            ATTR_POWER_CALCULATED: round(power_calculated, 5),
            ATTR_CHARGING: charging,
            ATTR_ONLINE: online,
            ATTR_REMAINING_BATTERY_CAPACITY: remaining_battery_capacity,
            ATTR_REMAINING_TIME: remaining_time,
            #            ATTR_BATTERY_CONNECTED: battery_connected,
            ATTR_LOW_BATTERY: low_battery,
        }
