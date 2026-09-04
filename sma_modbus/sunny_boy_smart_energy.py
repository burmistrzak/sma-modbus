"""SMA Sunny Boy Smart Energy 3.6-6.0.

A single-phase hybrid PV inverter three MPPT trackers and DC string inputs.
Battery storage is connected to a dedicated DC input.
"""

from modbus_connection.model import int32, uint32, uint64

from ._base import SmaComponent


class SunnyBoySmartEnergy(SmaComponent):
    """PV yield, battery and per-string DC data of a Sunny Boy Smart Energy."""

    register_ranges = (
        (30771, 30774),  # DC string 1 voltage + power
        (30845, 30848),  # battery state of charge + nominal capacity
        (30959, 30962),  # DC string 2 voltage + power
        (30965, 30968),  # DC string 3 voltage + power
        (31393, 31404),  # battery power + battery energy
        (32209, 32220),  # per-string DC lifetime energy
        (35469, 35474),  # PV power + PV energy
    )

    # PV
    pv_power = uint32(35469, unit="W", nan=0xFFFFFFFF)
    """Current PV power (Measurement.PvGen.PvW)."""

    pv_energy_total = uint64(35471, unit="Wh", nan=0xFFFFFFFFFFFFFFFF)
    """Total PV yield (Measurement.PvGen.PvWh)."""

    # Battery energy counters
    battery_charge_energy = uint64(31397, unit="Wh", nan=0xFFFFFFFFFFFFFFFF)
    """Total battery charge energy (Measurement.BatChrg.BatChrg)."""

    battery_discharge_energy = uint64(31401, unit="Wh", nan=0xFFFFFFFFFFFFFFFF)
    """Total battery discharge energy (Measurement.BatDsch.BatDsch)."""

    # Battery power
    battery_charge_power = uint32(31393, unit="W", nan=0xFFFFFFFF)
    """Current battery charge power (Measurement.BatChrg.CurBatCha)."""

    battery_discharge_power = uint32(31395, unit="W", nan=0xFFFFFFFF)
    """Current battery discharge power (Measurement.BatDsch.CurBatDsch)."""

    # Battery state
    battery_state_of_charge = uint32(30845, unit="%", nan=0xFFFFFFFF)
    """Battery state of charge (Measurement.Bat.ChaStt)."""

    battery_nominal_capacity = uint32(30847, unit="%", nan=0xFFFFFFFF)
    """Nominal battery capacity (Measurement.Bat.Diag.ActlCapacNom)."""

    # Per-string DC power (Measurement.DcMs.Watt[n])
    dc_power_1 = int32(30773, unit="W", nan=0x80000000)
    """DC power, string 1."""

    dc_power_2 = int32(30961, unit="W", nan=0x80000000)
    """DC power, string 2."""

    dc_power_3 = int32(30967, unit="W", nan=0x80000000)
    """DC power, string 3."""

    # Per-string DC lifetime energy (Measurement.DcMs.TotDcEnCntWh[n])
    dc_energy_total_1 = uint64(32209, unit="Wh", nan=0xFFFFFFFFFFFFFFFF)
    """Lifetime DC energy, string 1."""

    dc_energy_total_2 = uint64(32213, unit="Wh", nan=0xFFFFFFFFFFFFFFFF)
    """Lifetime DC energy, string 2."""

    dc_energy_total_3 = uint64(32217, unit="Wh", nan=0xFFFFFFFFFFFFFFFF)
    """Lifetime DC energy, string 3."""

    # Per-string DC voltage (Measurement.DcMs.Vol[n]), scaled to volts
    dc_voltage_1 = int32(30771, scale=0.01, unit="V", nan=0x80000000)
    """DC voltage, string 1."""

    dc_voltage_2 = int32(30959, scale=0.01, unit="V", nan=0x80000000)
    """DC voltage, string 2."""

    dc_voltage_3 = int32(30965, scale=0.01, unit="V", nan=0x80000000)
    """DC voltage, string 3."""
