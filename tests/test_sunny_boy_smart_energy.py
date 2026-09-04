"""Tests for the Sunny Boy Smart Energy hybrid inverter."""

from modbus_connection.mock import MockModbusUnit

from sma_modbus import SunnyBoySmartEnergy, Vendor
from sma_modbus.sunny_boy_smart_energy import (
    BatteryHealth,
    CmpBmsStatus,
    DeviceClass,
    SunnyBoySmartEnergyModel,
)
from sma_modbus.testing import set_input_registers

# raw register values (before scaling) for every field, in declaration order
RAW_VALUES = {
    "pv_power": 5000,
    "pv_energy_total": 123456789,
    "device_class": 8009,
    "device_type": 19085,
    "vendor": 461,
    "ac_power": 4000,
    "ac_power_l1": 4000,
    "ac_power_l2": 0,
    "ac_power_l3": 0,
    "ac_voltage_l1": 23000,
    "ac_voltage_l2": 0,
    "ac_voltage_l3": 0,
    "ac_voltage_l1_l2": 0,
    "ac_voltage_l2_l3": 0,
    "ac_voltage_l3_l1": 0,
    "ac_current": 17000,
    "ac_current_l1": 17000,
    "ac_current_l2": 0,
    "ac_current_l3": 0,
    "grid_frequency": 5000,
    "ac_reactive_power": 100,
    "ac_reactive_power_l1": 100,
    "ac_reactive_power_l2": 0,
    "ac_reactive_power_l3": 0,
    "ac_apparent_power": 4100,
    "ac_apparent_power_l1": 4100,
    "ac_apparent_power_l2": 0,
    "ac_apparent_power_l3": 0,
    "power_factor": 980,
    "power_factor_eei": 980,
    "battery_current": 5000,
    "battery_state_of_charge": 85,
    "battery_nominal_capacity": 95,
    "battery_temperature": 250,
    "battery_voltage": 53000,
    "battery_operating_status": 307,
    "battery_max_voltage": 55000,
    "battery_charge_power": 300,
    "battery_discharge_power": 400,
    "battery_charge_energy": 1000,
    "battery_discharge_energy": 2000,
    "battery_health": 307,
    "bms_firmware_version": 1040901,
    "battery_temperature_max": 350,
    "battery_temperature_min": 180,
    "battery_end_of_charge_voltage": 5880,
    "battery_end_of_discharge_voltage": 4200,
    "battery_max_charge_current": 50000,
    "battery_max_discharge_current": 50000,
    "battery_cell_voltage_sum": 53000,
    "battery_cell_voltage_min": 3300,
    "battery_cell_voltage_max": 3700,
    "bms_operating_status": 303,
    "battery_current_charge_energy": 500,
    "battery_current_discharge_energy": 600,
    "dc_power_0": -100,
    "dc_power_1": -200,
    "dc_power_2": 50,
    "dc_energy_total_0": 111,
    "dc_energy_total_1": 222,
    "dc_energy_total_2": 333,
    "dc_voltage_0": 40210,
    "dc_voltage_1": 40150,
    "dc_voltage_2": 39990,
    "dc_current_0": 12000,
    "dc_current_1": 8000,
    "dc_current_2": 6000,
    "insulation_resistance": 500000,
    "insulation_residual_current": 29000,
}


async def test_all_fields(mock_modbus_unit: MockModbusUnit) -> None:
    """Test every field decodes with sign handling and scaling."""
    device = SunnyBoySmartEnergy(mock_modbus_unit)
    set_input_registers(mock_modbus_unit, device, RAW_VALUES)
    await device.async_update()

    assert device.pv_power == 5000
    assert device.pv_energy_total == 123456789
    assert device.device_class is DeviceClass.HYBRID_INVERTER
    assert device.device_type is SunnyBoySmartEnergyModel.SBSE_6_0
    assert device.vendor is Vendor.SMA
    assert device.ac_power == 4000
    assert device.ac_power_l1 == 4000
    assert device.ac_power_l2 == 0
    assert device.ac_power_l3 == 0
    assert device.ac_voltage_l1 == 230.0
    assert device.ac_current == 17.0
    assert device.ac_current_l1 == 17.0
    assert device.grid_frequency == 50.0
    assert device.ac_reactive_power == 100
    assert device.ac_apparent_power == 4100
    assert device.power_factor == 0.98
    assert device.power_factor_eei == 0.98
    assert device.battery_current == 5.0
    assert device.battery_state_of_charge == 85
    assert device.battery_nominal_capacity == 95
    assert device.battery_temperature == 25.0
    assert device.battery_voltage == 530.0
    assert device.battery_operating_status == 307
    assert device.battery_max_voltage == 550.0
    assert device.battery_charge_power == 300
    assert device.battery_discharge_power == 400
    assert device.battery_charge_energy == 1000
    assert device.battery_discharge_energy == 2000
    assert device.battery_health is BatteryHealth.OK
    assert device.bms_firmware_version == 1040901
    assert device.battery_temperature_max == 35.0
    assert device.battery_temperature_min == 18.0
    assert device.battery_end_of_charge_voltage == 58.8
    assert device.battery_end_of_discharge_voltage == 42.0
    assert device.battery_max_charge_current == 50.0
    assert device.battery_max_discharge_current == 50.0
    assert device.battery_cell_voltage_sum == 530.0
    assert device.battery_cell_voltage_min == 3.3
    assert device.battery_cell_voltage_max == 3.7
    assert device.bms_operating_status is CmpBmsStatus.OFF
    assert device.battery_current_charge_energy == 500
    assert device.battery_current_discharge_energy == 600
    assert device.dc_power_0 == -100
    assert device.dc_power_1 == -200
    assert device.dc_power_2 == 50
    assert device.dc_energy_total_0 == 111
    assert device.dc_energy_total_1 == 222
    assert device.dc_energy_total_2 == 333
    assert device.dc_voltage_0 == 402.1
    assert device.dc_voltage_1 == 401.5
    assert device.dc_voltage_2 == 399.9
    assert device.dc_current_0 == 12.0
    assert device.dc_current_1 == 8.0
    assert device.dc_current_2 == 6.0
    assert device.insulation_resistance == 500000
    assert device.insulation_residual_current == 29.0


async def test_voltage_scaling(mock_modbus_unit: MockModbusUnit) -> None:
    """Test the 0.01 scale factor rounds to two decimals."""
    device = SunnyBoySmartEnergy(mock_modbus_unit)
    set_input_registers(mock_modbus_unit, device, {**RAW_VALUES, "dc_voltage_0": 0})
    await device.async_update()
    assert device.dc_voltage_0 == 0


async def test_nan_values(mock_modbus_unit: MockModbusUnit) -> None:
    """Test the sentinels decode to None."""
    device = SunnyBoySmartEnergy(mock_modbus_unit)
    set_input_registers(
        mock_modbus_unit,
        device,
        {
            "pv_energy_total": None,
            "battery_charge_energy": None,
            "ac_power": None,
            "ac_voltage_l1": None,
            "power_factor": None,
            "battery_current": None,
            "battery_voltage": None,
            "dc_power_0": None,
            "dc_voltage_1": None,
        },
    )
    await device.async_update()

    assert device.pv_energy_total is None
    assert device.battery_charge_energy is None
    assert device.ac_power is None
    assert device.ac_voltage_l1 is None
    assert device.power_factor is None
    assert device.battery_current is None
    assert device.battery_voltage is None
    assert device.dc_power_0 is None
    assert device.dc_voltage_1 is None


async def test_pooled_read(mock_modbus_unit: MockModbusUnit) -> None:
    """Test every served block is read in one request."""
    device = SunnyBoySmartEnergy(mock_modbus_unit)
    set_input_registers(mock_modbus_unit, device, RAW_VALUES)
    await device.async_update()

    input_reads = [
        e for e in mock_modbus_unit.read_events if e.register_type == "input"
    ]
    assert len(input_reads) == len(device.register_ranges)
    assert {e.address for e in input_reads} == {
        span[0] for span in device.register_ranges
    }
