"""Tests for the Sunny Boy PV inverter."""

from modbus_connection.mock import MockModbusUnit

from sma_modbus import SunnyBoy
from sma_modbus.testing import set_input_registers


async def test_pv_and_dc(mock_modbus_unit: MockModbusUnit) -> None:
    """Test PV totals and per-string DC power and voltage."""
    device = SunnyBoy(mock_modbus_unit)
    set_input_registers(
        mock_modbus_unit,
        device,
        {
            "pv_power": 4000,
            "pv_energy_total": 9876543,
            "dc_power_1": -250,
            "dc_power_2": 180,
            "dc_voltage_1": 35000,
            "dc_voltage_2": 34950,
        },
    )
    await device.async_update()

    assert device.pv_power == 4000
    assert device.pv_energy_total == 9876543
    assert device.dc_power_1 == -250
    assert device.dc_power_2 == 180
    assert device.dc_voltage_1 == 350.0
    assert device.dc_voltage_2 == 349.5


async def test_nan_values(mock_modbus_unit: MockModbusUnit) -> None:
    """Test the sentinels decode to None."""
    device = SunnyBoy(mock_modbus_unit)
    set_input_registers(
        mock_modbus_unit,
        device,
        {
            "pv_power": None,
            "pv_energy_total": None,
            "dc_power_1": None,
            "dc_voltage_1": None,
        },
    )
    await device.async_update()

    assert device.pv_power is None
    assert device.pv_energy_total is None
    assert device.dc_power_1 is None
    assert device.dc_voltage_1 is None


async def test_pooled_read(mock_modbus_unit: MockModbusUnit) -> None:
    """Test the three served blocks are each read in one request."""
    device = SunnyBoy(mock_modbus_unit)
    set_input_registers(
        mock_modbus_unit,
        device,
        {
            "pv_power": 1,
            "pv_energy_total": 2,
            "dc_power_1": 3,
            "dc_power_2": 4,
            "dc_voltage_1": 5,
            "dc_voltage_2": 6,
        },
    )
    await device.async_update()

    input_reads = [
        e for e in mock_modbus_unit.read_events if e.register_type == "input"
    ]
    assert len(input_reads) == len(device.register_ranges)
    assert {e.address for e in input_reads} == {
        span[0] for span in device.register_ranges
    }
