"""Tests for the Sunny Tripower three-phase PV inverter."""

from modbus_connection.mock import MockModbusConnection

from sma_modbus import SunnyTripower, Vendor
from sma_modbus.sunny_tripower import DeviceClass, SunnyTripowerModel, SystemStatus
from sma_modbus.testing import set_input_registers

# raw register values (before scaling) for every field, in declaration order
RAW_VALUES = {
    "pv_energy_total": 123456789,
    "device_class": 8001,
    "device_type": 9344,
    "vendor": 461,
    "firmware_version": 17107460,
    "system_status": 307,
    "rated_power_out": 6000,
    "rated_power_in": 0,
    "rated_apparent_power_out": 6600,
    "rated_apparent_power_in": 0,
    "rated_reactive_power_q1": 2000,
    "rated_reactive_power_q2": 2000,
    "rated_reactive_power_q3": 2000,
    "rated_reactive_power_q4": 2000,
    "rated_pf_min_q1": 9500,
    "rated_pf_min_q2": 9500,
    "rated_pf_min_q3": 9500,
    "rated_pf_min_q4": 9500,
    "grid_import_energy": 0,
    "grid_export_energy": 987654,
    "ac_power": 5500,
    "ac_power_l1": 1833,
    "ac_power_l2": 1834,
    "ac_power_l3": 1833,
    "ac_voltage_l1": 23000,
    "ac_voltage_l2": 23100,
    "ac_voltage_l3": 22900,
    "ac_voltage_l1_l2": 40000,
    "ac_voltage_l2_l3": 40100,
    "ac_voltage_l3_l1": 39900,
    "ac_current": 8000,
    "ac_current_l1": 8000,
    "ac_current_l2": 7900,
    "ac_current_l3": 8100,
    "grid_frequency": 5000,
    "ac_reactive_power": 500,
    "ac_reactive_power_l1": 170,
    "ac_reactive_power_l2": 160,
    "ac_reactive_power_l3": 170,
    "ac_apparent_power": 5600,
    "ac_apparent_power_l1": 1900,
    "ac_apparent_power_l2": 1850,
    "ac_apparent_power_l3": 1850,
    "power_factor": 990,
    "power_factor_eei": 990,
    "grid_import_power": 0,
    "grid_export_power": 5500,
    "dc_power_0": 2750,
    "dc_power_1": 2750,
    "dc_voltage_0": 60000,
    "dc_voltage_1": 59900,
    "dc_current_0": 4580,
    "dc_current_1": 4590,
    "dc_current_2": 0,
    "dc_current_3": 0,
    "insulation_resistance": 1000000,
    "insulation_residual_current": 29000,
    "internal_temperature": 450,
    "intermediate_circuit_voltage": 65000,
}


async def test_all_fields(mock_modbus_connection: MockModbusConnection) -> None:
    """Test every field decodes with sign handling and scaling."""
    device = SunnyTripower(mock_modbus_connection)
    set_input_registers(mock_modbus_connection, device, RAW_VALUES)
    await device.async_update()

    assert device.pv_energy_total == 123456789
    assert device.device_class is DeviceClass.SOLAR_INVERTERS
    assert device.device_type is SunnyTripowerModel.STP_4_0
    assert device.vendor is Vendor.SMA
    assert device.firmware_version == "1.05.10.R"
    assert device.system_status is SystemStatus.OK
    assert device.rated_power_out == 6000
    assert device.rated_power_in == 0
    assert device.rated_apparent_power_out == 6600
    assert device.rated_reactive_power_q1 == 2000
    assert device.rated_pf_min_q1 == 0.95
    assert device.grid_import_energy == 0
    assert device.grid_export_energy == 987654
    assert device.ac_power == 5500
    assert device.ac_power_l1 == 1833
    assert device.ac_power_l2 == 1834
    assert device.ac_power_l3 == 1833
    assert device.ac_voltage_l1 == 230.0
    assert device.ac_voltage_l2 == 231.0
    assert device.ac_voltage_l3 == 229.0
    assert device.ac_voltage_l1_l2 == 400.0
    assert device.ac_voltage_l2_l3 == 401.0
    assert device.ac_voltage_l3_l1 == 399.0
    assert device.ac_current == 8.0
    assert device.ac_current_l1 == 8.0
    assert device.ac_current_l2 == 7.9
    assert device.ac_current_l3 == 8.1
    assert device.grid_frequency == 50.0
    assert device.ac_reactive_power == 500
    assert device.ac_reactive_power_l1 == 170
    assert device.ac_reactive_power_l2 == 160
    assert device.ac_reactive_power_l3 == 170
    assert device.ac_apparent_power == 5600
    assert device.ac_apparent_power_l1 == 1900
    assert device.ac_apparent_power_l2 == 1850
    assert device.ac_apparent_power_l3 == 1850
    assert device.power_factor == 0.99
    assert device.power_factor_eei == 0.99
    assert device.grid_import_power == 0
    assert device.grid_export_power == 5500
    assert device.dc_power_0 == 2750
    assert device.dc_power_1 == 2750
    assert device.dc_voltage_0 == 600.0
    assert device.dc_voltage_1 == 599.0
    assert device.dc_current_0 == 4.58
    assert device.dc_current_1 == 4.59
    assert device.dc_current_2 == 0.0
    assert device.dc_current_3 == 0.0
    assert device.insulation_resistance == 1000000
    assert device.insulation_residual_current == 29.0
    assert device.internal_temperature == 45.0
    assert device.intermediate_circuit_voltage == 650.0


async def test_nan_values(mock_modbus_connection: MockModbusConnection) -> None:
    """Test the sentinels decode to None."""
    device = SunnyTripower(mock_modbus_connection)
    set_input_registers(
        mock_modbus_connection,
        device,
        {
            "pv_energy_total": None,
            "device_class": None,
            "device_type": None,
            "vendor": None,
            "system_status": None,
            "ac_power": None,
            "ac_voltage_l1": None,
            "dc_power_0": None,
            "internal_temperature": None,
            "insulation_residual_current": None,
        },
    )
    await device.async_update()

    assert device.pv_energy_total is None
    assert device.device_class is None
    assert device.device_type is None
    assert device.vendor is None
    assert device.system_status is None
    assert device.ac_power is None
    assert device.ac_voltage_l1 is None
    assert device.dc_power_0 is None
    assert device.internal_temperature is None
    assert device.insulation_residual_current is None
