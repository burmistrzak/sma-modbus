"""SMA Sunny Home Manager 2.0.

A home energy management system (HEMS) in form of a three-phase energy meter.
Only a few Modbus registers are readable without a SMA-issued Grid Guard-Code (GGC).

The meter's measurement registers answer on Modbus unit 2, but its Type Label
block (vendor, serial, firmware) is on unit 1 — SMA serves the same Type Label
registers on the shared bus at unit 1 for every device on the network.
"""

from enum import IntEnum
from typing import ClassVar

from modbus_connection.model import enum as enum_field
from modbus_connection.model import int32, uint32

from ._base import SmaComponent, SystemStatus, Vendor


class DeviceClass(IntEnum):
    """Device class (Nameplate.MainModel, register 30051)."""

    COMMUNICATION_PRODUCTS = 8128


class SunnyHomeManagerModel(IntEnum):
    """Home Manager model (Nameplate.Model, register 30053)."""

    SUNNY_HOME_MANAGER = 9343


class SunnyHomeManager(SmaComponent):
    """Read-only registers without Grid Guard-Code."""

    default_unit_id = 2

    # Type Label fields are served on unit 1, not on the measurement unit 2.
    field_unit_ids: ClassVar[dict[str, int]] = {
        "modbus_profile_revision": 1,
        "susy_id": 1,
        "device_class": 1,
        "device_type": 1,
        "vendor": 1,
        "serial_number": 1,
    }

    # Measurement ranges (unit 2); Type Label ranges (30001-30004, 30051-30058)
    # are listed too so restrict_fields can narrow the primary plan to them
    # before routing those fields to a secondary component on unit 1.
    register_ranges = (
        (30001, 30004),  # Type Label: Modbus profile revision, SUSyID
        (30051, 30058),  # Type Label: device class, model, vendor, serial
        (30201, 30202),  # system status
        (30581, 30584),  # grid energy counters
        (30865, 30868),  # grid power
    )

    # Type Label: Modbus header (unit 1)
    modbus_profile_revision = uint32(30001, nan=0xFFFFFFFF)
    """SMA Modbus profile revision."""

    susy_id = uint32(30003, nan=0xFFFFFFFF)
    """SUSyID (Parameter.Nameplate.SusyId)."""

    # Type Label: device identification (unit 1)
    device_class = enum_field(30051, DeviceClass, count=2, nan=0xFFFFFFFF)
    """Device class (Nameplate.MainModel)."""

    device_type = enum_field(30053, SunnyHomeManagerModel, count=2, nan=0xFFFFFFFF)
    """Device type (Nameplate.Model)."""

    vendor = enum_field(30055, Vendor, count=2, nan=0xFFFFFFFF)
    """Manufacturer (Nameplate.Vendor)."""

    serial_number = uint32(30057, nan=0xFFFFFFFF)
    """Serial number (Nameplate.SerNum)."""

    # Measurement registers (unit 2)
    system_status = enum_field(30201, SystemStatus, count=2, nan=0x00FFFFFD)
    """System status"""

    grid_import_energy = uint32(30581, unit="Wh", nan=0xFFFFFFFF)
    """Energy drawn from the utility grid (Wh) on all phases."""

    grid_export_energy = uint32(30583, unit="Wh", nan=0xFFFFFFFF)
    """Energy fed in the utility grid (Wh) on all phases."""

    grid_import_power = int32(30865, unit="W", nan=0x80000000)
    """Active power (W) drawn from the utility grid on all phases."""

    grid_export_power = int32(30867, unit="W", nan=0x80000000)
    """Active power (W) fed in the utility grid on all phases."""
