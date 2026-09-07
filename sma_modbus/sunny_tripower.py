"""SMA Sunny Tripower 3.0-6.0.

A three-phase PV inverter with up to four MPPT trackers and DC string inputs.
"""

from enum import IntEnum

from modbus_connection.model import NumberField, int32, uint32, uint64
from modbus_connection.model import enum as enum_field

from ._base import SmaComponent, SystemStatus, Vendor, decode_firmware_version


class DeviceClass(IntEnum):
    """Device class (Nameplate.MainModel, register 30051)."""

    SOLAR_INVERTERS = 8001


class SunnyTripowerModel(IntEnum):
    """Inverter model (Nameplate.Model, register 30053)."""

    STP_3_0 = 9366
    STP_4_0 = 9344
    STP_5_0 = 9345
    STP_6_0 = 9346


class SunnyTripower(SmaComponent):
    """PV yield, per-string DC and three-phase AC grid data of a Sunny Tripower."""

    register_ranges = (
        (30001, 30004),  # Type Label: Modbus profile revision, SUSyID
        (30051, 30060),  # Type Label: device class, model, vendor, serial, firmware
        (30201, 30202),  # system status
        (30225, 30226),  # insulation resistance
        (30231, 30232),  # rated active power WMaxOutRtg
        (30513, 30516),  # total yield (64-bit)
        (30581, 30584),  # energy counters
        (30769, 30796),  # DC string 1 + AC power/voltage/current
        (30803, 30820),  # AC frequency + reactive/apparent power
        (30865, 30868),  # power drawn/feed-in
        (30949, 30950),  # AC power factor
        (30953, 30954),  # internal temperature
        (30957, 30962),  # DC string 2 current/voltage/power
        (30975, 30982),  # intermediate circuit voltage + AC grid current per phase
        (31221, 31222),  # AC EEI power factor
        (31247, 31248),  # insulation residual current
        (31497, 31500),  # AC reactive power total + EEI
        (31793, 31796),  # DC strings 3-4 current
        (33019, 33044),  # Type Label: rated power ratings
    )

    # Total yield
    pv_energy_total = uint64(30513, unit="Wh", nan=0xFFFFFFFFFFFFFFFF)
    """Total yield (Metering.TotWhOut)."""

    # Type Label: device identification
    modbus_profile_revision = uint32(30001, nan=0xFFFFFFFF)
    """SMA Modbus profile revision."""

    susy_id = uint32(30003, nan=0xFFFFFFFF)
    """SUSyID (Parameter.Nameplate.SusyId)."""

    device_class = enum_field(30051, DeviceClass, count=2, nan=0xFFFFFFFF)
    """Device class (Nameplate.MainModel)."""

    device_type = enum_field(30053, SunnyTripowerModel, count=2, nan=0xFFFFFFFF)
    """Device type (Nameplate.Model)."""

    vendor = enum_field(30055, Vendor, count=2, nan=0xFFFFFFFF)
    """Manufacturer (Nameplate.Vendor)."""

    serial_number = uint32(30057, nan=0xFFFFFFFF)
    """Serial number (Nameplate.SerNum)."""

    firmware_version: NumberField[str] = NumberField(
        30059, count=2, convert=decode_firmware_version, nan=0xFFFFFFFF
    )
    """Firmware version (Nameplate.PkgRev), decoded as Major.Minor.Build.Suffix."""

    # System status
    system_status = enum_field(30201, SystemStatus, count=2, nan=0x00FFFFFD)
    """System status (Operation.Health)."""

    # Type Label: rated power ratings
    rated_power_out = uint32(30231, unit="W", nan=0xFFFFFFFF)
    """Rated active power WMaxOutRtg (Inverter.WLim)."""

    rated_power_in = int32(33019, unit="W", nan=0x80000000)
    """Rated active power WMaxInRtg."""

    rated_apparent_power_out = uint32(33025, unit="VA", nan=0xFFFFFFFF)
    """Rated apparent power VAMaxOutRtg."""

    rated_apparent_power_in = uint32(33027, unit="VA", nan=0xFFFFFFFF)
    """Rated apparent power VAMaxInRtg."""

    rated_reactive_power_q1 = int32(33029, unit="var", nan=0x80000000)
    """Rated reactive power VArMaxQ1Rtg."""

    rated_reactive_power_q2 = int32(33031, unit="var", nan=0x80000000)
    """Rated reactive power VArMaxQ2Rtg."""

    rated_reactive_power_q3 = int32(33033, unit="var", nan=0x80000000)
    """Rated reactive power VArMaxQ3Rtg."""

    rated_reactive_power_q4 = int32(33035, unit="var", nan=0x80000000)
    """Rated reactive power VArMaxQ4Rtg."""

    rated_pf_min_q1 = uint32(33037, scale=0.0001, nan=0xFFFFFFFF)
    """Rated cos phi PFMinQ1Rtg, FIX4."""

    rated_pf_min_q2 = uint32(33039, scale=0.0001, nan=0xFFFFFFFF)
    """Rated cos phi PFMinQ2Rtg, FIX4."""

    rated_pf_min_q3 = uint32(33041, scale=0.0001, nan=0xFFFFFFFF)
    """Rated cos phi PFMinQ3Rtg, FIX4."""

    rated_pf_min_q4 = uint32(33043, scale=0.0001, nan=0xFFFFFFFF)
    """Rated cos phi PFMinQ4Rtg, FIX4."""

    # Energy counters
    grid_import_energy = uint32(30581, unit="Wh", nan=0xFFFFFFFF)
    """Energy drawn from the utility grid (Metering.GridMs.TotWhIn)."""

    grid_export_energy = uint32(30583, unit="Wh", nan=0xFFFFFFFF)
    """Energy fed into the utility grid (Metering.GridMs.TotWhOut)."""

    # AC power (GridMs.TotW / GridMs.W.phs*), FIX0
    ac_power = int32(30775, unit="W", nan=0x80000000)
    """Total active power (GridMs.TotW)."""

    ac_power_l1 = int32(30777, unit="W", nan=0x80000000)
    """Active power, phase L1 (GridMs.W.phsA)."""

    ac_power_l2 = int32(30779, unit="W", nan=0x80000000)
    """Active power, phase L2 (GridMs.W.phsB)."""

    ac_power_l3 = int32(30781, unit="W", nan=0x80000000)
    """Active power, phase L3 (GridMs.W.phsC)."""

    # AC voltage (GridMs.PhV.phs*), FIX2
    ac_voltage_l1 = uint32(30783, scale=0.01, unit="V", nan=0xFFFFFFFF)
    """Grid voltage, phase L1 (GridMs.PhV.phsA)."""

    ac_voltage_l2 = uint32(30785, scale=0.01, unit="V", nan=0xFFFFFFFF)
    """Grid voltage, phase L2 (GridMs.PhV.phsB)."""

    ac_voltage_l3 = uint32(30787, scale=0.01, unit="V", nan=0xFFFFFFFF)
    """Grid voltage, phase L3 (GridMs.PhV.phsC)."""

    ac_voltage_l1_l2 = uint32(30789, scale=0.01, unit="V", nan=0xFFFFFFFF)
    """Grid voltage, L1 against L2 (GridMs.PhV.phsA2B)."""

    ac_voltage_l2_l3 = uint32(30791, scale=0.01, unit="V", nan=0xFFFFFFFF)
    """Grid voltage, L2 against L3 (GridMs.PhV.phsB2C)."""

    ac_voltage_l3_l1 = uint32(30793, scale=0.01, unit="V", nan=0xFFFFFFFF)
    """Grid voltage, L3 against L1 (GridMs.PhV.phsC2A)."""

    # AC current (GridMs.TotA / GridMs.A.phs*), FIX3
    ac_current = uint32(30795, scale=0.001, unit="A", nan=0xFFFFFFFF)
    """Total grid current (GridMs.TotA)."""

    ac_current_l1 = int32(30977, scale=0.001, unit="A", nan=0x80000000)
    """Grid current, phase L1 (GridMs.A.phsA)."""

    ac_current_l2 = int32(30979, scale=0.001, unit="A", nan=0x80000000)
    """Grid current, phase L2 (GridMs.A.phsB)."""

    ac_current_l3 = int32(30981, scale=0.001, unit="A", nan=0x80000000)
    """Grid current, phase L3 (GridMs.A.phsC)."""

    # AC frequency (GridMs.Hz), FIX2
    grid_frequency = uint32(30803, scale=0.01, unit="Hz", nan=0xFFFFFFFF)
    """Grid frequency (GridMs.Hz)."""

    # AC reactive power (GridMs.TotVAr / GridMs.VAr.phs*), FIX0
    ac_reactive_power = int32(31497, unit="var", nan=0x80000000)
    """Total reactive power (GridMs.TotVAr)."""

    ac_reactive_power_l1 = int32(30807, unit="var", nan=0x80000000)
    """Reactive power, phase L1 (GridMs.VAr.phsA)."""

    ac_reactive_power_l2 = int32(30809, unit="var", nan=0x80000000)
    """Reactive power, phase L2 (GridMs.VAr.phsB)."""

    ac_reactive_power_l3 = int32(30811, unit="var", nan=0x80000000)
    """Reactive power, phase L3 (GridMs.VAr.phsC)."""

    # AC apparent power (GridMs.TotVA / GridMs.VA.phs*), FIX0
    ac_apparent_power = int32(30813, unit="VA", nan=0x80000000)
    """Total apparent power (GridMs.TotVA)."""

    ac_apparent_power_l1 = int32(30815, unit="VA", nan=0x80000000)
    """Apparent power, phase L1 (GridMs.VA.phsA)."""

    ac_apparent_power_l2 = int32(30817, unit="VA", nan=0x80000000)
    """Apparent power, phase L2 (GridMs.VA.phsB)."""

    ac_apparent_power_l3 = int32(30819, unit="VA", nan=0x80000000)
    """Apparent power, phase L3 (GridMs.VA.phsC)."""

    # AC power factor (GridMs.TotPFPrc / GridMs.TotPFEEI), FIX3
    power_factor = uint32(30949, scale=0.001, nan=0xFFFFFFFF)
    """Displacement power factor (GridMs.TotPFPrc)."""

    power_factor_eei = int32(31221, scale=0.001, nan=0x80000000)
    """EEI displacement power factor (GridMs.TotPFEEI)."""

    # Grid power (Metering.GridMs.TotW*), FIX0
    grid_import_power = int32(30865, unit="W", nan=0x80000000)
    """Active power drawn from the grid (Metering.GridMs.TotWIn)."""

    grid_export_power = int32(30867, unit="W", nan=0x80000000)
    """Active power fed into the grid (Metering.GridMs.TotWOut)."""

    # Per-string DC power (DcMs.Watt[n]), FIX0
    dc_power_0 = int32(30773, unit="W", nan=0x80000000)
    """DC power, string 1."""

    dc_power_1 = int32(30961, unit="W", nan=0x80000000)
    """DC power, string 2."""

    # Per-string DC voltage (DcMs.Vol[n]), FIX2
    dc_voltage_0 = int32(30771, scale=0.01, unit="V", nan=0x80000000)
    """DC voltage, string 1."""

    dc_voltage_1 = int32(30959, scale=0.01, unit="V", nan=0x80000000)
    """DC voltage, string 2."""

    # Per-string DC current (DcMs.Amp[n]), FIX3
    dc_current_0 = int32(30769, scale=0.001, unit="A", nan=0x80000000)
    """DC current, string 1."""

    dc_current_1 = int32(30957, scale=0.001, unit="A", nan=0x80000000)
    """DC current, string 2."""

    dc_current_2 = int32(31793, scale=0.001, unit="A", nan=0x80000000)
    """DC current, string 3."""

    dc_current_3 = int32(31795, scale=0.001, unit="A", nan=0x80000000)
    """DC current, string 4."""

    # Insulation monitoring (DC Side)
    insulation_resistance = uint32(30225, unit="ohm", nan=0xFFFFFFFF)
    """Insulation resistance of the PV array (Isolation.LeakRis)."""

    insulation_residual_current = int32(31247, scale=0.001, unit="A", nan=0x80000000)
    """Residual current from insulation monitoring (Isolation.FltA), FIX3."""

    # Internal temperature (Coolsys.Cab.TmpVal), TEMPERATURE format
    internal_temperature = int32(30953, scale=0.1, unit="\u00b0C", nan=0x80000000)
    """Internal inverter temperature (Coolsys.Cab.TmpVal)."""

    # Intermediate circuit voltage (Inverter.DclVol), FIX2
    intermediate_circuit_voltage = int32(30975, scale=0.01, unit="V", nan=0x80000000)
    """Intermediate circuit voltage (Inverter.DclVol)."""
