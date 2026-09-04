"""SMA Sunny Home Manager 2.0.

A home energy management system (HEMS) in form of a three-phase energy meter.
Only a few Modbus registers are readable without a SMA-issued Grid Guard-Code (GGC).
"""

from enum import IntEnum

from modbus_connection.model import enum, int32, uint32

from ._base import SmaComponent


class SystemStatus(IntEnum):
    """SMA system status (register 30201)."""

    OK = 307
    WARNING = 455
    ERROR = 35


class SunnyHomeManager(SmaComponent):
    """Read-only registers without Grid Guard-Code."""

    # Three contiguous served blocks; the planner fetches each in one request.
    register_ranges = (
        (30201, 30202),  # system status
        (30581, 30584),  # grid energy counters
        (30865, 30868),  # grid power
    )

    system_status = enum(30201, SystemStatus, count=2, nan=0x00FFFFFD)
    """System status"""

    grid_import_energy = uint32(30581, unit="Wh", nan=0xFFFFFFFF)
    """Energy drawn from the utility grid (Wh) on all phases."""

    grid_export_energy = uint32(30583, unit="Wh", nan=0xFFFFFFFF)
    """Energy fed in the utility grid (Wh) on all phases."""

    grid_import_power = int32(30865, unit="W", nan=0x80000000)
    """Active power (W) drawn from the utility grid on all phases."""

    grid_export_power = int32(30867, unit="W", nan=0x80000000)
    """Active power (W) fed in the utility grid on all phases."""
