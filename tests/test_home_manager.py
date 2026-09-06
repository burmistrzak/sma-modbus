"""Tests for the Sunny Home Manager grid meter."""

import pytest
from modbus_connection.mock import MockModbusConnection

from sma_modbus import SunnyHomeManager, Vendor
from sma_modbus.home_manager import DeviceClass, SunnyHomeManagerModel, SystemStatus
from sma_modbus.testing import set_input_registers

# Raw register values for the Type Label fields (unit 1)
TYPE_LABEL_VALUES = {
    "modbus_profile_revision": 1,
    "susy_id": 270,
    "device_class": 8128,
    "device_type": 9343,
    "vendor": 461,
    "serial_number": 12345678,
}

# Raw register values for the measurement fields (unit 2)
MEASUREMENT_VALUES = {
    "system_status": 307,
    "grid_import_energy": 123456,
    "grid_export_energy": 654321,
    "grid_import_power": -500,
    "grid_export_power": 750,
}


async def test_grid_energy_and_power(
    mock_modbus_connection: MockModbusConnection,
) -> None:
    """Test the four meter values are read and scaled."""
    device = SunnyHomeManager(mock_modbus_connection)
    set_input_registers(
        mock_modbus_connection,
        device,
        {**TYPE_LABEL_VALUES, **MEASUREMENT_VALUES},
    )
    await device.async_update()

    assert device.system_status is SystemStatus.OK
    assert device.grid_import_energy == 123456
    assert device.grid_export_energy == 654321
    assert device.grid_import_power == -500
    assert device.grid_export_power == 750


async def test_type_label(mock_modbus_connection: MockModbusConnection) -> None:
    """Test the Type Label fields are read from unit 1."""
    device = SunnyHomeManager(mock_modbus_connection)
    set_input_registers(
        mock_modbus_connection,
        device,
        {**TYPE_LABEL_VALUES, **MEASUREMENT_VALUES},
    )
    await device.async_update()

    assert device.modbus_profile_revision == 1
    assert device.susy_id == 270
    assert device.device_class is DeviceClass.COMMUNICATION_PRODUCTS
    assert device.device_type is SunnyHomeManagerModel.SUNNY_HOME_MANAGER
    assert device.vendor is Vendor.SMA
    assert device.serial_number == 12345678


async def test_nan_values(mock_modbus_connection: MockModbusConnection) -> None:
    """Test the not-a-value sentinels decode to None."""
    device = SunnyHomeManager(mock_modbus_connection)
    set_input_registers(
        mock_modbus_connection,
        device,
        {
            "system_status": None,
            "grid_import_energy": None,
            "grid_export_energy": None,
            "grid_import_power": None,
            "grid_export_power": None,
            "vendor": None,
            "serial_number": None,
        },
    )
    await device.async_update()

    assert device.system_status is None
    assert device.grid_import_energy is None
    assert device.grid_export_energy is None
    assert device.grid_import_power is None
    assert device.grid_export_power is None
    assert device.vendor is None
    assert device.serial_number is None


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (307, SystemStatus.OK),
        (455, SystemStatus.WARNING),
        (35, SystemStatus.ERROR),
    ],
)
async def test_system_status(
    mock_modbus_connection: MockModbusConnection,
    raw: int,
    expected: SystemStatus,
) -> None:
    """Test the system status decodes to the enum member."""
    device = SunnyHomeManager(mock_modbus_connection)
    set_input_registers(mock_modbus_connection, device, {"system_status": raw})
    await device.async_update()
    assert device.system_status is expected


async def test_system_status_nan(mock_modbus_connection: MockModbusConnection) -> None:
    """Test the system status sentinel decodes to None."""
    device = SunnyHomeManager(mock_modbus_connection)
    set_input_registers(mock_modbus_connection, device, {"system_status": None})
    await device.async_update()
    assert device.system_status is None


async def test_pooled_read(mock_modbus_connection: MockModbusConnection) -> None:
    """Test the three measurement blocks are read, not bridged into one request."""
    device = SunnyHomeManager(mock_modbus_connection)
    set_input_registers(
        mock_modbus_connection,
        device,
        {**TYPE_LABEL_VALUES, **MEASUREMENT_VALUES},
    )
    await device.async_update()

    # Three measurement ranges on unit 2 + one Type Label range on unit 1.
    unit1 = mock_modbus_connection.for_unit(1)
    unit2 = mock_modbus_connection.for_unit(2)
    unit1_reads = [e for e in unit1.read_events if e.register_type == "input"]
    unit2_reads = [e for e in unit2.read_events if e.register_type == "input"]
    # Type Label: two blocks (30001-30004, 30051-30058) on unit 1.
    # The ManualComponent uses gap-based planning (no declared ranges),
    # so the gap between the blocks is too large to merge — two reads.
    assert len(unit1_reads) == 2
    assert {(e.address, e.count) for e in unit1_reads} == {
        (30001, 4),
        (30051, 8),
    }
    # Three measurement blocks on unit 2.
    assert len(unit2_reads) == 3
    assert {(e.address, e.count) for e in unit2_reads} == {
        (30201, 2),
        (30581, 4),
        (30865, 4),
    }
