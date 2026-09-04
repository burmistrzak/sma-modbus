"""Tests for the Sunny Boy Smart Energy hybrid inverter."""

from modbus_connection.mock import MockModbusUnit

from sma_modbus import SunnyBoySmartEnergy
from sma_modbus.testing import set_input_registers

# raw register values (before scaling) for every field, in declaration order
RAW_VALUES = {
    "pv_power": 5000,
    "pv_energy_total": 123456789,
    "battery_charge_energy": 1000,
    "battery_discharge_energy": 2000,
    "battery_charge_power": 300,
    "battery_discharge_power": 400,
    "battery_state_of_charge": 85,
    "battery_nominal_capacity": 95,
    "dc_power_1": -100,
    "dc_power_2": -200,
    "dc_power_3": 50,
    "dc_energy_total_1": 111,
    "dc_energy_total_2": 222,
    "dc_energy_total_3": 333,
    "dc_voltage_1": 40210,
    "dc_voltage_2": 40150,
    "dc_voltage_3": 39990,
}


async def test_all_fields(mock_modbus_unit: MockModbusUnit) -> None:
    """Test every field decodes with sign handling and scaling."""
    device = SunnyBoySmartEnergy(mock_modbus_unit)
    set_input_registers(mock_modbus_unit, device, RAW_VALUES)
    await device.async_update()

    assert device.pv_power == 5000
    assert device.pv_energy_total == 123456789
    assert device.battery_charge_energy == 1000
    assert device.battery_discharge_energy == 2000
    assert device.battery_charge_power == 300
    assert device.battery_discharge_power == 400
    assert device.battery_state_of_charge == 85
    assert device.battery_nominal_capacity == 95
    assert device.dc_power_1 == -100
    assert device.dc_power_2 == -200
    assert device.dc_power_3 == 50
    assert device.dc_energy_total_1 == 111
    assert device.dc_energy_total_2 == 222
    assert device.dc_energy_total_3 == 333
    assert device.dc_voltage_1 == 402.1
    assert device.dc_voltage_2 == 401.5
    assert device.dc_voltage_3 == 399.9


async def test_voltage_scaling(mock_modbus_unit: MockModbusUnit) -> None:
    """Test the 0.01 scale factor rounds to two decimals."""
    device = SunnyBoySmartEnergy(mock_modbus_unit)
    set_input_registers(mock_modbus_unit, device, {**RAW_VALUES, "dc_voltage_1": 0})
    await device.async_update()
    assert device.dc_voltage_1 == 0


async def test_nan_values(mock_modbus_unit: MockModbusUnit) -> None:
    """Test the uint64 and int32 sentinels decode to None."""
    device = SunnyBoySmartEnergy(mock_modbus_unit)
    set_input_registers(
        mock_modbus_unit,
        device,
        {
            "pv_energy_total": None,
            "battery_charge_energy": None,
            "dc_power_1": None,
            "dc_voltage_2": None,
        },
    )
    await device.async_update()

    assert device.pv_energy_total is None
    assert device.battery_charge_energy is None
    assert device.dc_power_1 is None
    assert device.dc_voltage_2 is None


async def test_pooled_read(mock_modbus_unit: MockModbusUnit) -> None:
    """Test the seven served blocks are each read in one request."""
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
