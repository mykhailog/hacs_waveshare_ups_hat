import numpy as np
from collections import deque
from .ina219 import INA219

COEF_SMAx2 = 2

class INA219Wrapper:
    def __init__(self, ina219 : INA219, samples_cnt : int):
        self._ina219 = ina219
        self._bus_voltage_buf = deque(maxlen=samples_cnt * COEF_SMAx2)
        self._shunt_voltage_buf = deque(maxlen=samples_cnt)
        self._current_buf = deque(maxlen=samples_cnt * COEF_SMAx2)
        self._power_buf = deque(maxlen=samples_cnt)
        self._attrs = {}

    def measureINAValues(self):
        self._current_buf.append(self._ina219.getCurrent_mA())
        self._bus_voltage_buf.append(self._ina219.getBusVoltage_V())
        self._shunt_voltage_buf.append(self._ina219.getShuntVoltage_mV())
        self._power_buf.append(self._ina219.getPower_W())

    def getCurrentSMA_mA(self):
        return self._getSMAValue(self._current_buf)

    def getBusVoltageSMA_V(self):
        return self._getSMAValue(self._bus_voltage_buf)

    def getShuntVoltageSMA_mV(self):
        return self._getSMAValue(self._shunt_voltage_buf)

    def getPowerSMA_W(self):
        return self._getSMAValue(self._power_buf)

    def getCurrentSMAx2_mA(self):
        return self._getSMAValue(self._current_buf, COEF_SMAx2)

    def getBusVoltageSMAx2_V(self):
        return self._getSMAValue(self._bus_voltage_buf, COEF_SMAx2)

    def isBusVoltageBufFilled(self):
        if len(self._bus_voltage_buf) == self._bus_voltage_buf.maxlen:
            return True
        return False

    def _getSMAValue(self, buf:deque, divider:int=1):
        if divider > 1:
            return np.mean(self._getBufTail(buf, divider))
        return np.mean(buf)

    def _getSMMValue(self, buf:deque, divider:int=1):
        if divider > 1:
            return np.median(self._getBufTail(buf, divider))
        return np.median(buf)

    def _getBufTail(self, buf: deque, divider: int):
        slice_start = len(buf) - int(len(buf) / divider) - 1
        slice_end = len(buf)
        return list(buf)[slice_start:slice_end]
