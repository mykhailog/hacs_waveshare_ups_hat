import logging
from .const import CONF_BATTERIES_COUNT, CONF_BATTERY_CAPACITY, CONF_MAX_SOC, CONF_SMA_SAMPLES, MIN_CHARGING_CURRENT, MIN_ONLINE_CURRENT
from .ina219 import INA219
from .ina219_wrapper import INA219Wrapper
from homeassistant import core
from homeassistant.const import CONF_NAME, CONF_UNIQUE_ID
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
import random

_LOGGER = logging.getLogger(__name__)


class INA219UpsHatCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: core.HomeAssistant, config: ConfigType) -> None:
        """Initialize coordinator"""

        self.name_prefix = config.get(CONF_NAME)
        self.id_prefix = config.get(CONF_UNIQUE_ID)

        self._max_soc = config.get(CONF_MAX_SOC)
        self._battery_capacity = config.get(CONF_BATTERY_CAPACITY)
        self._batteries_count = config.get(CONF_BATTERIES_COUNT)
        self._sma_samples = config.get(CONF_SMA_SAMPLES)

        self._ina219 = INA219(addr=0x41)
        self._ina219_wrapper = INA219Wrapper(self._ina219, self._sma_samples)

        super().__init__(
            hass,
            _LOGGER,
            name="ina219_ups_hat",
            update_method=self._update_data,
        )

    async def _update_data(self):
        try:
            ina219_wrapper = self._ina219_wrapper
            ina219_wrapper.measureINAValues()

            bus_voltage = ina219_wrapper.getBusVoltageSMA_V()  # voltage on V- (load side)
            shunt_voltage = (ina219_wrapper.getShuntVoltageSMA_mV() / 1000) # voltage between V+ and V- across the shunt
            current = ina219_wrapper.getCurrentSMA_mA()  # current in mA
            power = ina219_wrapper.getPowerSMA_W()  # power in W

            smooth_bus_voltage = ina219_wrapper.getBusVoltageSMAx2_V()
            smooth_current = ina219_wrapper.getCurrentSMAx2_mA()

            soc_c1 = 3 * self._batteries_count
            soc_c2 = 1.2 * self._batteries_count
            real_soc = (smooth_bus_voltage - soc_c1) / soc_c2 * 100
            soc = (
                (smooth_bus_voltage - soc_c1) /
                (soc_c2 * (self._max_soc / 100.0)) * 100
            )
            if soc > 100:
                soc = 100
            if soc < 0:
                soc = 0

            power_calculated = bus_voltage * (current / 1000)

            online = bool(current > MIN_ONLINE_CURRENT)
            charging = bool(current > MIN_CHARGING_CURRENT)

            if self._battery_capacity is None:
                remaining_battery_capacity = None
                remaining_time = None
            else:
                remaining_battery_capacity = (
                    real_soc / 100.0) * self._battery_capacity
                if not online:
                    remaining_time = round(
                        (remaining_battery_capacity / -smooth_current) * 60.0, 0
                    )
                else:
                    remaining_time = None

            return {
                "voltage": round(bus_voltage + shunt_voltage, 2),
                "current": round(current / 1000, 5),
                "power": round(power_calculated, 2),
                "soc": round(soc, 1),
                "remaining_battery_capacity": round(remaining_battery_capacity, 0),
                "remaining_time": remaining_time,
                "online": online,
                "charging": charging,
            }
        except Exception as e:
            raise UpdateFailed(f"Error updating data: {e}")
