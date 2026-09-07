"""Library for SMA Modbus TCP interface.

Consumes a ``modbus_connection.ModbusConnection`` — the library opens its own
unit handles and knows which unit IDs to poll. Each device is a single
:class:`~modbus_connection.model.Component` read from input registers; call
:meth:`async_update` to refresh every field in as few requests as the register
layout allows.

Use :func:`discover` to auto-detect the device type, serial number, and unit ID
from just a connection to the device's IP address.
"""

import logging
from dataclasses import dataclass
from enum import StrEnum

from modbus_connection import ModbusConnection, ModbusError, ModbusUnit

from ._base import SmaComponent, SystemStatus, Vendor
from .home_manager import DeviceClass as SunnyHomeManagerDeviceClass
from .home_manager import SunnyHomeManager, SunnyHomeManagerModel
from .sunny_boy import DeviceClass as SunnyBoyDeviceClass
from .sunny_boy import SunnyBoy, SunnyBoyModel
from .sunny_boy_smart_energy import (
    BatteryHealth,
    CmpBmsStatus,
    SunnyBoySmartEnergy,
    SunnyBoySmartEnergyModel,
)
from .sunny_boy_smart_energy import (
    DeviceClass as SunnyBoySmartEnergyDeviceClass,
)
from .sunny_tripower import SunnyTripower, SunnyTripowerModel

_LOGGER = logging.getLogger(__name__)

__all__ = [
    "DEVICE_CLASSES",
    "BatteryHealth",
    "CmpBmsStatus",
    "DeviceType",
    "DiscoveryInfo",
    "SmaComponent",
    "SunnyBoy",
    "SunnyBoyDeviceClass",
    "SunnyBoyModel",
    "SunnyBoySmartEnergy",
    "SunnyBoySmartEnergyDeviceClass",
    "SunnyBoySmartEnergyModel",
    "SunnyHomeManager",
    "SunnyHomeManagerDeviceClass",
    "SunnyHomeManagerModel",
    "SunnyTripower",
    "SunnyTripowerModel",
    "SystemStatus",
    "Vendor",
    "discover",
]


class DeviceType(StrEnum):
    """The SMA device models this library supports."""

    SUNNY_HOME_MANAGER = "sunny_home_manager"
    SUNNY_BOY_SMART_ENERGY = "sunny_boy_smart_energy"
    SUNNY_BOY = "sunny_boy"
    SUNNY_TRIPOWER = "sunny_tripower"


DEVICE_CLASSES: dict[DeviceType, type[SmaComponent]] = {
    DeviceType.SUNNY_HOME_MANAGER: SunnyHomeManager,
    DeviceType.SUNNY_BOY_SMART_ENERGY: SunnyBoySmartEnergy,
    DeviceType.SUNNY_BOY: SunnyBoy,
    DeviceType.SUNNY_TRIPOWER: SunnyTripower,
}


# Device class values from input register 30051 (Nameplate.MainModel).
_DEVICE_CLASS_SHM = SunnyHomeManagerDeviceClass.COMMUNICATION_PRODUCTS.value
_DEVICE_CLASS_SB = SunnyBoyDeviceClass.SOLAR_INVERTERS.value
_DEVICE_CLASS_SBSE = SunnyBoySmartEnergyDeviceClass.HYBRID_INVERTER.value

# Sunny Tripower and Sunny Boy share device class 8001 (Solar Inverters).
# Distinguish by device model (Nameplate.Model, register 30053).
_STP_MODELS = frozenset(SunnyTripowerModel)


@dataclass(frozen=True, slots=True)
class DiscoveryInfo:
    """Result of auto-discovering an SMA device on the network.

    ``device_type`` selects the :class:`SmaComponent` subclass to use;
    ``serial_number`` is the device's physical serial;
    ``unit_id`` is the Modbus unit ID the measurement registers answer on;
    the remaining fields are the raw Type Label values.
    """

    device_type: DeviceType
    serial_number: int
    unit_id: int
    susy_id: int
    modbus_profile_revision: int
    device_class: int
    device_model: int
    vendor: int


def _combine_u32(words: list[int]) -> int:
    """Combine two big-endian 16-bit words into a 32-bit unsigned value."""
    return (words[0] << 16) | words[1]


def _is_nan(value: int) -> bool:
    """Check if a 32-bit value is a NaN sentinel."""
    return value in (0xFFFFFFFF, 0x00FFFFFD, 0xFFFFFFFE, 0x80000000)


async def _read_type_label(unit: ModbusUnit) -> dict[str, int] | None:
    """Read the Type Label from a Modbus unit.

    Returns the decoded fields as a dict, or ``None`` if the serial number
    or device class is a NaN sentinel (the unit is not serving valid data).
    Raises :class:`~modbus_connection.ModbusError` if the read itself fails.
    """
    words = await unit.read_input_registers(30001, 6)
    revision = _combine_u32(words[0:2])
    susy_id = _combine_u32(words[2:4])
    serial = _combine_u32(words[4:6])

    words = await unit.read_input_registers(30051, 6)
    device_class = _combine_u32(words[0:2])
    device_model = _combine_u32(words[2:4])
    vendor = _combine_u32(words[4:6])

    if _is_nan(serial) or _is_nan(device_class):
        return None

    return {
        "modbus_profile_revision": revision,
        "susy_id": susy_id,
        "serial_number": serial,
        "device_class": device_class,
        "device_model": device_model,
        "vendor": vendor,
    }


async def discover(
    connection: ModbusConnection,
    *,
    unit_id: int | None = None,
) -> DiscoveryInfo:
    """Auto-detect the SMA device at the other end of ``connection``.

    Reads the Type Label (input registers 30001-30006 and 30051-30056) to
    determine the device class, model, serial number, SUSy ID, manufacturer,
    and Modbus profile revision.

    When ``unit_id`` is not provided, the Type Label is probed on unit ID 1
    first, then unit ID 3.  Some devices (e.g. the Sunny Boy) do not serve
    the Type Label on unit 1; unit 3 is the standard measurement unit for SMA
    inverters.  Unit 2 is never probed — it is reserved for PV plant-wide
    parameters.

    When ``unit_id`` is provided, the Type Label is read from that unit
    directly, and it is used as the measurement unit ID.  This covers
    inverters that have been reconfigured to a non-default unit ID.

    The device class is mapped to a :class:`DeviceType`.  Returns a
    :class:`DiscoveryInfo` with all Type Label fields and the unit ID to
    use for measurements.
    Raises :class:`~modbus_connection.ModbusError` if the device cannot be
    discovered or is not a supported SMA device.
    """
    probe_ids = [unit_id] if unit_id is not None else [1, 3]

    label: dict[str, int] | None = None
    for probe_unit_id in probe_ids:
        unit = connection.for_unit(probe_unit_id)
        try:
            label = await _read_type_label(unit)
        except ModbusError:
            continue
        if label is not None:
            _LOGGER.debug("Type Label read from unit ID %d", probe_unit_id)
            break

    if label is None:
        raise ModbusError(
            f"Could not read Type Label from unit ID {probe_ids[-1]}"
        )

    device_class = label["device_class"]

    # Map device class to DeviceType.
    if device_class == _DEVICE_CLASS_SHM:
        device_type = DeviceType.SUNNY_HOME_MANAGER
    elif device_class == _DEVICE_CLASS_SBSE:
        device_type = DeviceType.SUNNY_BOY_SMART_ENERGY
    elif device_class == _DEVICE_CLASS_SB:
        # Sunny Boy and Sunny Tripower share device class 8001.
        # Distinguish by device model (Nameplate.Model).
        if label["device_model"] in _STP_MODELS:
            device_type = DeviceType.SUNNY_TRIPOWER
        else:
            device_type = DeviceType.SUNNY_BOY
    else:
        raise ModbusError(f"Unknown device class: {device_class}")

    if unit_id is None:
        unit_id = DEVICE_CLASSES[device_type].default_unit_id

    return DiscoveryInfo(
        device_type=device_type,
        serial_number=label["serial_number"],
        unit_id=unit_id,
        susy_id=label["susy_id"],
        modbus_profile_revision=label["modbus_profile_revision"],
        device_class=device_class,
        device_model=label["device_model"],
        vendor=label["vendor"],
    )
