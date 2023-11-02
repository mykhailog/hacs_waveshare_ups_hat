"""Details about the INA219 UPS Hat sensor"""

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.components.sensor.const import SensorDeviceClass, SensorStateClass
from homeassistant import core
from homeassistant.components.sensor import SensorEntity, PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_NAME,
    CONF_UNIQUE_ID,
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfPower,
    UnitOfTime,
)

import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.entity_platform import AddEntitiesCallback
import logging
import voluptuous as vol

from .entity import INA219UpsHatEntity
from .coordinator import INA219UpsHatCoordinator
from .const import (
    CONF_BATTERIES_COUNT,
    CONF_BATTERY_CAPACITY,
    CONF_MAX_SOC,
    CONF_SCAN_INTERVAL,
    CONF_SMA_SAMPLES,
    DEFAULT_NAME,
)


_LOGGER = logging.getLogger(__name__)


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


async def async_setup_platform(
    hass: core.HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    coordinator = INA219UpsHatCoordinator(hass, config)
    await coordinator.async_refresh()

    sensors = [
        VoltageSensor(coordinator),
        CurrentSensor(coordinator),
        PowerSensor(coordinator),
        SocSensor(coordinator),
        RemainingCapacitySensor(coordinator),
        RemainingTimeSensor(coordinator),
        OnlineBinarySensor(coordinator),
        ChargingBinarySensor(coordinator),
    ]
    async_add_entities(sensors)

    async def async_update_data(now):
        await coordinator.async_request_refresh()

    async_track_time_interval(hass, async_update_data,
                              config.get(CONF_SCAN_INTERVAL))


# SENSORS


class INA219UpsHatSensor(INA219UpsHatEntity, SensorEntity):
    """Base sensor"""

    def __init__(self, coordinator: INA219UpsHatCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_suggested_display_precision = 2


class VoltageSensor(INA219UpsHatSensor):
    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._name = "Voltage"
        self._attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT
        self._attr_device_class = SensorDeviceClass.VOLTAGE

    @property
    def native_value(self):
        return self._coordinator.data["voltage"]


class CurrentSensor(INA219UpsHatSensor):
    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._name = "Current"
        self._attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
        self._attr_device_class = SensorDeviceClass.CURRENT

    @property
    def native_value(self):
        return self._coordinator.data["current"]


class PowerSensor(INA219UpsHatSensor):
    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._name = "Power"
        self._attr_native_unit_of_measurement = UnitOfPower.WATT
        self._attr_device_class = SensorDeviceClass.POWER

    @property
    def native_value(self):
        return self._coordinator.data["power"]


class SocSensor(INA219UpsHatSensor):
    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._name = "SoC"
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_device_class = SensorDeviceClass.BATTERY
        self._attr_suggested_display_precision = 1

    @property
    def native_value(self):
        return self._coordinator.data["soc"]


class RemainingCapacitySensor(INA219UpsHatSensor):
    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._name = "Remaining Capacity"
        self._attr_native_unit_of_measurement = "mAh"
        self._attr_suggested_display_precision = 0

    @property
    def native_value(self):
        return self._coordinator.data["remaining_battery_capacity"]


class RemainingTimeSensor(INA219UpsHatSensor):
    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._name = "Remaining Time"
        self._attr_native_unit_of_measurement = UnitOfTime.SECONDS
        self._attr_device_class = SensorDeviceClass.DURATION
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_suggested_display_precision = 0

    @property
    def native_value(self):
        return self._coordinator.data["remaining_time"]


# BINARY SENSORS


class INA219UpsHatBinarySensor(INA219UpsHatEntity, BinarySensorEntity):
    """Base binary sensor"""

    def __init__(self, coordinator: INA219UpsHatCoordinator) -> None:
        super().__init__(coordinator)


class OnlineBinarySensor(INA219UpsHatBinarySensor):
    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._name = "Online"
        self._attr_device_class = BinarySensorDeviceClass.PLUG

    @property
    def is_on(self):
        return self._coordinator.data["online"]


class ChargingBinarySensor(INA219UpsHatBinarySensor):
    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._name = "Charging"
        self._attr_device_class = BinarySensorDeviceClass.BATTERY_CHARGING

    @property
    def is_on(self):
        return self._coordinator.data["charging"]
