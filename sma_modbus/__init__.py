"""Library for SMA Modbus TCP interface.

Consumes a ``modbus_connection.ModbusUnit`` - connection lifecycle stays with
the caller. Each device is a single :class:`~modbus_connection.model.Component`
read from input registers; call :meth:`async_update` to refresh every field in
as few requests as the register layout allows.
"""

from enum import StrEnum

from ._base import SmaComponent
from .home_manager import SunnyHomeManager
from .sunny_boy import SunnyBoy
from .sunny_boy_smart_energy import SunnyBoySmartEnergy

__all__ = [
    "DEVICE_CLASSES",
    "DeviceType",
    "SmaComponent",
    "SunnyBoy",
    "SunnyBoySmartEnergy",
    "SunnyHomeManager",
]


class DeviceType(StrEnum):
    """The SMA device models this library supports."""

    SUNNY_HOME_MANAGER = "sunny_home_manager"
    SUNNY_BOY_SMART_ENERGY = "sunny_boy_smart_energy"
    SUNNY_BOY = "sunny_boy"


DEVICE_CLASSES: dict[DeviceType, type[SmaComponent]] = {
    DeviceType.SUNNY_HOME_MANAGER: SunnyHomeManager,
    DeviceType.SUNNY_BOY_SMART_ENERGY: SunnyBoySmartEnergy,
    DeviceType.SUNNY_BOY: SunnyBoy,
}
