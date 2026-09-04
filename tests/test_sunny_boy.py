"""Tests for the Sunny Boy PV inverter."""

from modbus_connection.mock import MockModbusUnit

from sma_modbus import SunnyBoy, Vendor
from sma_modbus.sunny_boy import DeviceClass, SunnyBoyModel
from sma_modbus.testing import set_input_registers

# raw register values (before scaling) for every field, in declaration order
RAW_VALUES = {
    "pv_power": 4000,
    "pv_energy_total": 9876543,
    "device_class": 8001,
    "device_type": 9402,
    "vendor": 461,
    "firmware_version": 17107460,
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
    "dc_power_0": -250,
    "dc_power_1": 180,
    "dc_voltage_0": 35000,
    "dc_voltage_1": 34950,
    "dc_current_0": 7000,
    "dc_current_1": 5000,
    "insulation_resistance": 500000,
    "insulation_residual_current": 29000,
}


async def test_all_fields(mock_modbus_unit: MockModbusUnit) -> None:
    """Test every field decodes with sign handling and scaling."""
    device = SunnyBoy(mock_modbus_unit)
    set_input_registers(mock_modbus_unit, device, RAW_VALUES)
    await device.async_update()

    assert device.pv_power == 4000
    assert device.pv_energy_total == 9876543
    assert device.device_class is DeviceClass.SOLAR_INVERTERS
    assert device.device_type is SunnyBoyModel.SB_3_6
    assert device.vendor is Vendor.SMA
    assert device.firmware_version == "1.05.10.R"
    assert device.ac_power == 4000
    assert device.ac_power_l1 == 4000
    assert device.ac_power_l2 == 0
    assert device.ac_power_l3 == 0
    assert device.ac_voltage_l1 == 230.0
    assert device.ac_voltage_l2 == 0.0
    assert device.ac_voltage_l3 == 0.0
    assert device.ac_current == 17.0
    assert device.ac_current_l1 == 17.0
    assert device.ac_current_l2 == 0
    assert device.ac_current_l3 == 0
    assert device.grid_frequency == 50.0
    assert device.ac_reactive_power == 100
    assert device.ac_reactive_power_l1 == 100
    assert device.ac_reactive_power_l2 == 0
    assert device.ac_reactive_power_l3 == 0
    assert device.ac_apparent_power == 4100
    assert device.ac_apparent_power_l1 == 4100
    assert device.ac_apparent_power_l2 == 0
    assert device.ac_apparent_power_l3 == 0
    assert device.power_factor == 0.98
    assert device.power_factor_eei == 0.98
    assert device.dc_power_0 == -250
    assert device.dc_power_1 == 180
    assert device.dc_voltage_0 == 350.0
    assert device.dc_voltage_1 == 349.5
    assert device.dc_current_0 == 7.0
    assert device.dc_current_1 == 5.0
    assert device.insulation_resistance == 500000
    assert device.insulation_residual_current == 29.0


async def test_nan_values(mock_modbus_unit: MockModbusUnit) -> None:
    """Test the sentinels decode to None."""
    device = SunnyBoy(mock_modbus_unit)
    set_input_registers(
        mock_modbus_unit,
        device,
        {
            "pv_power": None,
            "pv_energy_total": None,
            "ac_power": None,
            "ac_voltage_l1": None,
            "power_factor": None,
            "dc_power_0": None,
            "dc_voltage_1": None,
        },
    )
    await device.async_update()

    assert device.pv_power is None
    assert device.pv_energy_total is None
    assert device.ac_power is None
    assert device.ac_voltage_l1 is None
    assert device.power_factor is None
    assert device.dc_power_0 is None
    assert device.dc_voltage_1 is None


async def test_pooled_read(mock_modbus_unit: MockModbusUnit) -> None:
    """Test reads only touch declared register ranges."""
    device = SunnyBoy(mock_modbus_unit)
    set_input_registers(mock_modbus_unit, device, RAW_VALUES)
    await device.async_update()

    input_reads = [
        e for e in mock_modbus_unit.read_events if e.register_type == "input"
    ]
    # every read must start at a declared range start
    range_starts = {span[0] for span in device.register_ranges}
    for read in input_reads:
        assert read.address in range_starts, f"unexpected read at {read.address}"
