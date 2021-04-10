"""Details about the Waveshare UPS Hat sensor"""
import logging
import os

import voluptuous as vol

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import DEVICE_CLASS_BATTERY, PERCENTAGE
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

from .ina219 import INA219
from .const import (
    MIN_CHARGING_CURRENT,
    MIN_ONLINE_CURRENT,
    MIN_BATTERY_CONNECTED_POWER,
    LOW_BATTERY_PERCENTAGE,
)

ATTR_CAPACITY = "capacity"
ATTR_PSU_VOLTAGE = "psu_voltage"
ATTR_SHUNT_VOLTAGE = "shunt_voltage"
ATTR_LOAD_VOLTAGE = "load_voltage"
ATTR_CURRENT = "current"
ATTR_POWER = "power"
ATTR_CHARGING = "charging"
ATTR_ONLINE = "online"
ATTR_BATTERY_CONNECTED = "battery_connected"
ATTR_LOW_BATTERY = "low_battery"

DEFAULT_NAME = "waveshare_ups_hat"


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Waveshare UPS Hat sensor."""

    add_entities([WaveshareUpsHat()], True)


class WaveshareUpsHat(SensorEntity):
    """Representation of a Waveshare UPS Hat."""

    def __init__(self):
        """Initialize the sensor."""

        self._name = DEFAULT_NAME
        self._ina219 = INA219(addr=0x42)
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
        return self._attrs.get(ATTR_CAPACITY)

    @property
    def unit_of_measurement(self):
        """Return the unit the value is expressed in."""
        return PERCENTAGE

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""
        return self._attrs

    def update(self):
        """Get the latest data and updates the states."""
        ina219 = self._ina219
        bus_voltage = ina219.getBusVoltage_V()  # voltage on V- (load side)
        shunt_voltage = (
            ina219.getShuntVoltage_mV() / 1000
        )  # voltage between V+ and V- across the shunt
        current = ina219.getCurrent_mA()  # current in mA
        power = ina219.getPower_W()  # power in W
        percent = (bus_voltage - 6) / 2.4 * 100

        if percent > 100:
            percent = 100
        if percent < 0:
            percent = 0

        battery_connected = power > MIN_BATTERY_CONNECTED_POWER
        capacity = round(percent, 0)
        online = current > MIN_ONLINE_CURRENT
        charging = current > MIN_CHARGING_CURRENT
        low_battery = online and capacity < LOW_BATTERY_PERCENTAGE

        if not battery_connected:
            capacity = 0.0  # no battery no capacity

        self._attrs = {
            ATTR_CAPACITY: capacity,
            ATTR_PSU_VOLTAGE: bus_voltage + shunt_voltage,
            ATTR_SHUNT_VOLTAGE: shunt_voltage,
            ATTR_CURRENT: current,
            ATTR_POWER: power,
            ATTR_CHARGING: charging,
            ATTR_ONLINE: online,
            ATTR_BATTERY_CONNECTED: battery_connected,
            ATTR_LOW_BATTERY: low_battery
        }
