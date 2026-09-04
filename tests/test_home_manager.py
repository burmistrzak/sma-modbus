"""Tests for the Sunny Home Manager grid meter."""

import pytest
from modbus_connection.mock import MockModbusUnit

from sma_modbus import SunnyHomeManager
from sma_modbus.home_manager import SystemStatus
from sma_modbus.testing import set_input_registers


async def test_grid_energy_and_power(mock_modbus_unit: MockModbusUnit) -> None:
    """Test the four meter values are read and scaled."""
    device = SunnyHomeManager(mock_modbus_unit)
    set_input_registers(
        mock_modbus_unit,
        device,
        {
            "system_status": 307,
            "grid_import_energy": 123456,
            "grid_export_energy": 654321,
            "grid_import_power": -500,
            "grid_export_power": 750,
        },
    )
    await device.async_update()

    assert device.system_status is SystemStatus.OK
    assert device.grid_import_energy == 123456
    assert device.grid_export_energy == 654321
    assert device.grid_import_power == -500
    assert device.grid_export_power == 750


async def test_nan_values(mock_modbus_unit: MockModbusUnit) -> None:
    """Test the not-a-value sentinels decode to None."""
    device = SunnyHomeManager(mock_modbus_unit)
    set_input_registers(
        mock_modbus_unit,
        device,
        {
            "system_status": None,
            "grid_import_energy": None,
            "grid_export_energy": None,
            "grid_import_power": None,
            "grid_export_power": None,
        },
    )
    await device.async_update()

    assert device.system_status is None
    assert device.grid_import_energy is None
    assert device.grid_export_energy is None
    assert device.grid_import_power is None
    assert device.grid_export_power is None


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (307, SystemStatus.OK),
        (455, SystemStatus.WARNING),
        (35, SystemStatus.ERROR),
    ],
)
async def test_system_status(
    mock_modbus_unit: MockModbusUnit, raw: int, expected: SystemStatus
) -> None:
    """Test the system status decodes to the enum member."""
    device = SunnyHomeManager(mock_modbus_unit)
    set_input_registers(mock_modbus_unit, device, {"system_status": raw})
    await device.async_update()
    assert device.system_status is expected


async def test_system_status_nan(mock_modbus_unit: MockModbusUnit) -> None:
    """Test the system status sentinel decodes to None."""
    device = SunnyHomeManager(mock_modbus_unit)
    set_input_registers(mock_modbus_unit, device, {"system_status": None})
    await device.async_update()
    assert device.system_status is None


async def test_pooled_read(mock_modbus_unit: MockModbusUnit) -> None:
    """Test the three served blocks are read, not bridged into one request."""
    device = SunnyHomeManager(mock_modbus_unit)
    set_input_registers(
        mock_modbus_unit,
        device,
        {
            "system_status": 307,
            "grid_import_energy": 10,
            "grid_export_energy": 20,
            "grid_import_power": 1,
            "grid_export_power": 2,
        },
    )
    await device.async_update()

    # three served ranges => three input-register reads
    input_reads = [
        e for e in mock_modbus_unit.read_events if e.register_type == "input"
    ]
    assert len(input_reads) == 3
    assert {(e.address, e.count) for e in input_reads} == {
        (30201, 2),
        (30581, 4),
        (30865, 4),
    }
