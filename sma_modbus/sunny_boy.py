"""SMA Sunny Boy 3.0-6.0.

A single-phase PV inverter with four DC string inputs acrosss two MPPT trackers.
"""

from modbus_connection.model import int32, uint32, uint64

from ._base import SmaComponent


class SunnyBoy(SmaComponent):
    """PV yield and per-string DC data of a Sunny Boy inverter."""

    register_ranges = (
        (30771, 30774),  # DC string A voltage + power
        (30959, 30962),  # DC string B voltage + power
        (35469, 35474),  # PV power + PV energy
    )

    pv_power = uint32(35469, unit="W", nan=0xFFFFFFFF)
    """Current PV power (PvGen.PvW)."""

    pv_energy_total = uint64(35471, unit="Wh", nan=0xFFFFFFFFFFFFFFFF)
    """Total PV yield (PvGen.PvWh)."""

    dc_power_1 = int32(30773, unit="W", nan=0x80000000)
    """DC power, string A (DcMs.Watt[A])."""

    dc_power_2 = int32(30961, unit="W", nan=0x80000000)
    """DC power, string B (DcMs.Watt[B])."""

    dc_voltage_1 = int32(30771, scale=0.01, unit="V", nan=0x80000000)
    """DC voltage, string A (DcMs.Vol[A]), scaled to volts."""

    dc_voltage_2 = int32(30959, scale=0.01, unit="V", nan=0x80000000)
    """DC voltage, string B (DcMs.Vol[B]), scaled to volts."""
