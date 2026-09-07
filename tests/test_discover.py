"""Tests for the SMA device discovery protocol."""

from modbus_connection.mock import MockModbusConnection

from sma_modbus import DEVICE_CLASSES, DeviceType, discover
from sma_modbus.home_manager import DeviceClass as ShmDeviceClass
from sma_modbus.sunny_boy import DeviceClass as SbDeviceClass
from sma_modbus.sunny_boy_smart_energy import DeviceClass as SbseDeviceClass
from sma_modbus.sunny_tripower import SunnyTripowerModel as StpModel
from sma_modbus.testing import set_input_registers


def _set_u32(unit: object, address: int, value: int, space: str = "input") -> None:
    """Write a 32-bit big-endian value into a mock unit's register space."""
    store = getattr(unit, space)
    store[address] = (value >> 16) & 0xFFFF
    store[address + 1] = value & 0xFFFF


def _setup_type_label(
    unit: object,
    *,
    serial: int,
    device_class: int,
    device_model: int = 0,
    vendor: int = 461,
    susy_id: int = 270,
    revision: int = 1,
) -> None:
    """Write a full Type Label into a mock unit's input registers."""
    _set_u32(unit, 30001, revision)  # modbus profile revision
    _set_u32(unit, 30003, susy_id)  # SUSy ID
    _set_u32(unit, 30005, serial)  # serial number
    _set_u32(unit, 30051, device_class)  # device class
    _set_u32(unit, 30053, device_model)  # device model
    _set_u32(unit, 30055, vendor)  # manufacturer


async def test_discover_sunny_home_manager(
    mock_modbus_connection: MockModbusConnection,
) -> None:
    """Test discovering a Sunny Home Manager (device class 8128, unit 2)."""
    unit1 = mock_modbus_connection.for_unit(1)
    _setup_type_label(
        unit1,
        serial=12345678,
        device_class=ShmDeviceClass.COMMUNICATION_PRODUCTS.value,
        device_model=9343,
    )

    info = await discover(mock_modbus_connection)

    assert info.device_type is DeviceType.SUNNY_HOME_MANAGER
    assert info.serial_number == 12345678
    assert info.unit_id == 2
    assert info.device_class == ShmDeviceClass.COMMUNICATION_PRODUCTS.value
    assert info.device_model == 9343
    assert info.vendor == 461
    assert info.susy_id == 270
    assert info.modbus_profile_revision == 1


async def test_discover_sunny_boy(
    mock_modbus_connection: MockModbusConnection,
) -> None:
    """Test discovering a Sunny Boy (device class 8001, default unit 3).

    The Sunny Boy does not serve the Type Label on unit 1 (returns NaN),
    so discovery falls through to unit 3.
    """
    unit1 = mock_modbus_connection.for_unit(1)
    _setup_type_label(
        unit1,
        serial=0xFFFFFFFE,
        device_class=0x00FFFFFD,
    )
    unit3 = mock_modbus_connection.for_unit(3)
    _setup_type_label(
        unit3,
        serial=98765432,
        device_class=SbDeviceClass.SOLAR_INVERTERS.value,
        device_model=9402,
    )

    info = await discover(mock_modbus_connection)

    assert info.device_type is DeviceType.SUNNY_BOY
    assert info.serial_number == 98765432
    assert info.unit_id == 3
    assert info.device_class == SbDeviceClass.SOLAR_INVERTERS.value
    assert info.device_model == 9402


async def test_discover_sunny_boy_smart_energy(
    mock_modbus_connection: MockModbusConnection,
) -> None:
    """Test discovering a Sunny Boy Smart Energy (device class 8009, default unit 3)."""
    unit1 = mock_modbus_connection.for_unit(1)
    _setup_type_label(
        unit1,
        serial=55554444,
        device_class=SbseDeviceClass.HYBRID_INVERTER.value,
        device_model=19085,
    )

    info = await discover(mock_modbus_connection)

    assert info.device_type is DeviceType.SUNNY_BOY_SMART_ENERGY
    assert info.serial_number == 55554444
    assert info.unit_id == 3
    assert info.device_class == SbseDeviceClass.HYBRID_INVERTER.value
    assert info.device_model == 19085


async def test_discover_sunny_tripower(
    mock_modbus_connection: MockModbusConnection,
) -> None:
    """Test discovering a Sunny Tripower (device class 8001, model 9344)."""
    unit1 = mock_modbus_connection.for_unit(1)
    _setup_type_label(
        unit1,
        serial=11223344,
        device_class=SbDeviceClass.SOLAR_INVERTERS.value,
        device_model=StpModel.STP_4_0.value,
    )

    info = await discover(mock_modbus_connection)

    assert info.device_type is DeviceType.SUNNY_TRIPOWER
    assert info.serial_number == 11223344
    assert info.unit_id == 3
    assert info.device_class == SbDeviceClass.SOLAR_INVERTERS.value
    assert info.device_model == StpModel.STP_4_0.value


async def test_discover_with_unit_id_override(
    mock_modbus_connection: MockModbusConnection,
) -> None:
    """Test that the unit_id parameter reads the Type Label from that unit."""
    unit5 = mock_modbus_connection.for_unit(5)
    _setup_type_label(
        unit5,
        serial=98765432,
        device_class=SbDeviceClass.SOLAR_INVERTERS.value,
    )

    info = await discover(mock_modbus_connection, unit_id=5)

    assert info.device_type is DeviceType.SUNNY_BOY
    assert info.serial_number == 98765432
    assert info.unit_id == 5


async def test_discover_sunny_boy_smart_energy_custom_unit_id_and_read(
    mock_modbus_connection: MockModbusConnection,
) -> None:
    """Test discovering a SBSE and reading its data with a custom unit ID.

    The Type Label is read from unit 4 (the provided unit_id) and the
    measurement data is read back from the same unit.
    """
    unit4 = mock_modbus_connection.for_unit(4)
    _setup_type_label(
        unit4,
        serial=30001234,
        device_class=SbseDeviceClass.HYBRID_INVERTER.value,
        device_model=19085,
    )

    info = await discover(mock_modbus_connection, unit_id=4)
    assert info.device_type is DeviceType.SUNNY_BOY_SMART_ENERGY
    assert info.serial_number == 30001234
    assert info.unit_id == 4

    # Construct the device with the discovered unit ID and read it.
    device = DEVICE_CLASSES[info.device_type](mock_modbus_connection, info.unit_id)
    set_input_registers(
        mock_modbus_connection,
        device,
        {
            "vendor": 461,
            "serial_number": 30001234,
            "firmware_version": 17107460,
            "pv_power": 5000,
            "pv_energy_total": 123456789,
            "ac_power": 4000,
            "battery_state_of_charge": 85,
            "battery_voltage": 53000,
        },
    )
    await device.async_update()

    assert device.vendor is not None
    assert device.serial_number == 30001234
    assert device.firmware_version == "1.05.10.R"
    assert device.pv_power == 5000
    assert device.pv_energy_total == 123456789
    assert device.ac_power == 4000
    assert device.battery_state_of_charge == 85
    assert device.battery_voltage == 530.0


async def test_discover_nan_serial(
    mock_modbus_connection: MockModbusConnection,
) -> None:
    """Test that a NaN serial on all probed units raises ModbusError."""
    from modbus_connection import ModbusError

    for uid in (1, 3):
        unit = mock_modbus_connection.for_unit(uid)
        _setup_type_label(
            unit,
            serial=0xFFFFFFFF,
            device_class=SbDeviceClass.SOLAR_INVERTERS.value,
        )

    try:
        await discover(mock_modbus_connection)
    except ModbusError:
        pass
    else:
        raise AssertionError("Expected ModbusError for NaN serial")


async def test_discover_nan_device_class(
    mock_modbus_connection: MockModbusConnection,
) -> None:
    """Test that a NaN device class on all probed units raises ModbusError."""
    from modbus_connection import ModbusError

    for uid in (1, 3):
        unit = mock_modbus_connection.for_unit(uid)
        _setup_type_label(
            unit,
            serial=12345678,
            device_class=0xFFFFFFFF,
        )

    try:
        await discover(mock_modbus_connection)
    except ModbusError:
        pass
    else:
        raise AssertionError("Expected ModbusError for NaN device class")


async def test_discover_unknown_device_class(
    mock_modbus_connection: MockModbusConnection,
) -> None:
    """Test that an unknown device class raises ModbusError."""
    from modbus_connection import ModbusError

    unit1 = mock_modbus_connection.for_unit(1)
    _setup_type_label(
        unit1,
        serial=12345678,
        device_class=9999,
    )

    try:
        await discover(mock_modbus_connection)
    except ModbusError:
        pass
    else:
        raise AssertionError("Expected ModbusError for unknown device class")
