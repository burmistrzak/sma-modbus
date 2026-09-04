"""SMA Sunny Boy Smart Energy 3.6-6.0.

A single-phase hybrid PV inverter with three MPPT trackers and DC string
inputs. Battery storage is connected to a dedicated DC input.
"""

from enum import IntEnum

from modbus_connection.model import NumberField, int32, uint32, uint64
from modbus_connection.model import enum as enum_field

from ._base import SmaComponent, Vendor, decode_firmware_version


class DeviceClass(IntEnum):
    """Device class (Nameplate.MainModel, register 30051)."""

    HYBRID_INVERTER = 8009


class BatteryHealth(IntEnum):
    """Battery status (Operation.Bat.Health, register 31391)."""

    FAULT = 35
    OFF = 303
    OK = 307
    WARNING = 455


class CmpBmsStatus(IntEnum):
    """BMS operating status (Operation.CmpBMS.OpStt, register 34659)."""

    DEVICE_FAULT = 71
    OFF = 303
    WAITING = 388
    STANDBY = 1295
    BATTERY_WAIT = 2291


class SunnyBoySmartEnergyModel(IntEnum):
    """Inverter model (Nameplate.Model, register 30053)."""

    SBSE_3_6 = 19128
    SBSE_3_8_US = 19088
    SBSE_4_0 = 19129
    SBSE_4_8_US = 19087
    SBSE_5_0 = 19130
    SBSE_5_8_US = 19086
    SBSE_6_0 = 19085
    SBSE_7_7_US = 19084
    SBSE_8_0 = 19103
    SBSE_9_6_US = 19105
    SBSE_9_9 = 19166
    SBSE_11_5_US = 19134


class SunnyBoySmartEnergy(SmaComponent):
    """PV, battery, per-string DC and AC grid data of a Sunny Boy Smart Energy."""

    register_ranges = (
        (30001, 30004),  # Type Label: Modbus profile revision, SUSyID
        (30051, 30060),  # Type Label: device class, model, vendor, serial, firmware
        (30225, 30226),  # insulation resistance
        (30769, 30796),  # DC string 0 + AC power/voltage/current
        (30803, 30804),  # AC frequency
        (30807, 30820),  # AC reactive/apparent power
        (30843, 30852),  # battery current/SoC/capacity/temp/voltage
        (30949, 30950),  # AC power factor
        (30955, 30956),  # battery operating status
        (30957, 30968),  # DC strings 1+2 current/voltage/power
        (30977, 30982),  # AC grid current per phase
        (31001, 31002),  # battery max voltage
        (31221, 31222),  # AC EEI power factor
        (31247, 31248),  # insulation residual current
        (31389, 31404),  # BMS firmware + battery health + power + energy
        (31497, 31498),  # AC reactive power total
        (32209, 32220),  # per-string DC lifetime energy
        (32221, 32228),  # battery temp min/max
        (32239, 32276),  # battery setpoints + cell voltages
        (33017, 33044),  # Type Label: rated power ratings
        (34659, 34668),  # BMS status + current charge/discharge energy
        (35469, 35474),  # PV power + PV energy
    )

    # PV
    pv_power = uint32(35469, unit="W", nan=0xFFFFFFFF)
    """Current PV power (Measurement.PvGen.PvW)."""

    pv_energy_total = uint64(35471, unit="Wh", nan=0xFFFFFFFFFFFFFFFF)
    """Total PV yield (Measurement.PvGen.PvWh)."""

    # Type Label: Modbus header
    modbus_profile_revision = uint32(30001, nan=0xFFFFFFFF)
    """SMA Modbus profile revision."""

    susy_id = uint32(30003, nan=0xFFFFFFFF)
    """SUSyID (Parameter.Nameplate.SusyId)."""

    # Type Label: device identification
    device_class = enum_field(30051, DeviceClass, count=2, nan=0xFFFFFFFF)
    """Device class (Nameplate.MainModel)."""

    device_type = enum_field(30053, SunnyBoySmartEnergyModel, count=2, nan=0xFFFFFFFF)
    """Device type (Nameplate.Model)."""

    vendor = enum_field(30055, Vendor, count=2, nan=0xFFFFFFFF)
    """Manufacturer (Nameplate.Vendor)."""

    serial_number = uint32(30057, nan=0xFFFFFFFF)
    """Serial number (Nameplate.SerNum)."""

    firmware_version: NumberField[str] = NumberField(
        30059, count=2, convert=decode_firmware_version, nan=0xFFFFFFFF
    )
    """Firmware version (Nameplate.PkgRev), decoded as Major.Minor.Build.Suffix."""

    # Type Label: rated power ratings
    rated_power_out = int32(33017, unit="W", nan=0x80000000)
    """Rated active power WMaxOutRtg."""

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

    # Battery measurements
    battery_current = int32(30843, scale=0.001, unit="A", nan=0x80000000)
    """Battery current (Bat.Amp), FIX3."""

    battery_state_of_charge = uint32(30845, unit="%", nan=0xFFFFFFFF)
    """Battery state of charge (Bat.ChaStt)."""

    battery_nominal_capacity = uint32(30847, unit="%", nan=0xFFFFFFFF)
    """Nominal battery capacity (Bat.Diag.ActlCapacNom)."""

    battery_temperature = int32(30849, scale=0.1, unit="°C", nan=0x80000000)
    """Battery temperature (Bat.TmpVal), TEMPERATURE format."""

    battery_voltage = uint32(30851, scale=0.01, unit="V", nan=0xFFFFFFFF)
    """Battery voltage (Bat.Vol), FIX2."""

    battery_operating_status = uint32(30955, nan=0x00FFFFFD)
    """Battery operating status (Bat.OpStt), TAGLIST."""

    battery_max_voltage = uint32(31001, scale=0.01, unit="V", nan=0xFFFFFFFF)
    """Max. occurred battery voltage (Bat.Diag.VolMax), FIX2."""

    # Battery power
    battery_charge_power = uint32(31393, unit="W", nan=0xFFFFFFFF)
    """Current battery charge power (BatChrg.CurBatCha)."""

    battery_discharge_power = uint32(31395, unit="W", nan=0xFFFFFFFF)
    """Current battery discharge power (BatDsch.CurBatDsch)."""

    # Battery energy counters
    battery_charge_energy = uint64(31397, unit="Wh", nan=0xFFFFFFFFFFFFFFFF)
    """Total battery charge energy (BatChrg.BatChrg)."""

    battery_discharge_energy = uint64(31401, unit="Wh", nan=0xFFFFFFFFFFFFFFFF)
    """Total battery discharge energy (BatDsch.BatDsch)."""

    # Battery health (Operation.Bat.Health)
    battery_health = enum_field(31391, BatteryHealth, count=2, nan=0x00FFFFFD)
    """Battery health status (Operation.Bat.Health)."""

    # BMS firmware version (Nameplate.CmpBMS.SwRev)
    bms_firmware_version: NumberField[str] = NumberField(
        31389, count=2, convert=decode_firmware_version, nan=0xFFFFFFFF
    )
    """BMS firmware version (Nameplate.CmpBMS.SwRev).

    Decoded as Major.Minor.Build.Suffix.
    """

    # Battery temperature extremes
    battery_temperature_max = int32(32221, scale=0.1, unit="°C", nan=0x80000000)
    """Highest measured battery temperature (Bat.TmpValMax)."""

    battery_temperature_min = int32(32227, scale=0.1, unit="°C", nan=0x80000000)
    """Lowest measured battery temperature (Bat.TmpValMin)."""

    # Battery voltage setpoints (Bat.*SptDmd)
    battery_end_of_charge_voltage = uint32(32239, scale=0.01, unit="V", nan=0xFFFFFFFF)
    """End-of-charge voltage (Bat.ChaVolSptDmd), FIX2."""

    battery_end_of_discharge_voltage = uint32(
        32245, scale=0.01, unit="V", nan=0xFFFFFFFF
    )
    """End-of-discharge voltage (Bat.DschVolSptDmd), FIX2."""

    # Battery current setpoints (Bat.*AmpSptDmd)
    battery_max_charge_current = uint32(32251, scale=0.001, unit="A", nan=0xFFFFFFFF)
    """Maximum charging current (Bat.ChaAmpSptDmd), FIX3."""

    battery_max_discharge_current = uint32(32257, scale=0.001, unit="A", nan=0xFFFFFFFF)
    """Maximum discharging current (Bat.DschAmpSptDmd), FIX3."""

    # Battery cell voltages
    battery_cell_voltage_sum = uint32(32263, scale=0.01, unit="V", nan=0xFFFFFFFF)
    """Sum of cell voltages (Bat.CelVolSum), FIX2."""

    battery_cell_voltage_min = uint32(32269, scale=0.001, unit="V", nan=0xFFFFFFFF)
    """Lowest measured cell voltage (Bat.CelVolMin), FIX3."""

    battery_cell_voltage_max = uint32(32275, scale=0.001, unit="V", nan=0xFFFFFFFF)
    """Highest measured cell voltage (Bat.CelVolMax), FIX3."""

    # BMS operating status (Operation.CmpBMS.OpStt)
    bms_operating_status = enum_field(34659, CmpBmsStatus, count=2, nan=0x00FFFFFD)
    """BMS operating status (Operation.CmpBMS.OpStt)."""

    # BMS current charge/discharge energy
    battery_current_charge_energy = uint64(34661, unit="Wh", nan=0xFFFFFFFFFFFFFFFF)
    """Charge of current battery (BatChrg.ActBatChrg)."""

    battery_current_discharge_energy = uint64(34665, unit="Wh", nan=0xFFFFFFFFFFFFFFFF)
    """Battery discharge of current battery (BatDsch.ActBatDsch)."""

    # Per-string DC power (Measurement.DcMs.Watt[n]), FIX0
    dc_power_0 = int32(30773, unit="W", nan=0x80000000)
    """DC power, string 0."""

    dc_power_1 = int32(30961, unit="W", nan=0x80000000)
    """DC power, string 1."""

    dc_power_2 = int32(30967, unit="W", nan=0x80000000)
    """DC power, string 2."""

    # Per-string DC lifetime energy (Measurement.DcMs.TotDcEnCntWh[n]), FIX0
    dc_energy_total_0 = uint64(32209, unit="Wh", nan=0xFFFFFFFFFFFFFFFF)
    """Lifetime DC energy, string 0."""

    dc_energy_total_1 = uint64(32213, unit="Wh", nan=0xFFFFFFFFFFFFFFFF)
    """Lifetime DC energy, string 1."""

    dc_energy_total_2 = uint64(32217, unit="Wh", nan=0xFFFFFFFFFFFFFFFF)
    """Lifetime DC energy, string 2."""

    # Per-string DC voltage (Measurement.DcMs.Vol[n]), FIX2
    dc_voltage_0 = int32(30771, scale=0.01, unit="V", nan=0x80000000)
    """DC voltage, string 0."""

    dc_voltage_1 = int32(30959, scale=0.01, unit="V", nan=0x80000000)
    """DC voltage, string 1."""

    dc_voltage_2 = int32(30965, scale=0.01, unit="V", nan=0x80000000)
    """DC voltage, string 2."""

    # Per-string DC current (Measurement.DcMs.Amp[n]), FIX3
    dc_current_0 = int32(30769, scale=0.001, unit="A", nan=0x80000000)
    """DC current, string 0."""

    dc_current_1 = int32(30957, scale=0.001, unit="A", nan=0x80000000)
    """DC current, string 1."""

    dc_current_2 = int32(30963, scale=0.001, unit="A", nan=0x80000000)
    """DC current, string 2."""

    # Insulation monitoring (DC Side)
    insulation_resistance = uint32(30225, unit="ohm", nan=0xFFFFFFFF)
    """Insulation resistance of the PV array (Isolation.LeakRis)."""

    insulation_residual_current = int32(31247, scale=0.001, unit="A", nan=0x80000000)
    """Residual current from insulation monitoring (Isolation.FltA), FIX3."""
