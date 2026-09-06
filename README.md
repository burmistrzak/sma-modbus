# sma-modbus

Async Python library for the Modbus TCP interface of SMA devices, built on
[modbus-connection](https://github.com/home-assistant-libs/modbus-connection).

> [!WARNING]
>
> **Developer Preview**
>
> Working, but **do not** use in production. Please report any issues you come across.

> [!NOTE]
>
> Based on a partial agentic port of [fronius-modbus](https://github.com/farmio/fronius-modbus). 🫶

Supports the following SMA devices (so far):

- **Sunny Home Manager 2.0**
- **Sunny Boy Smart Energy 3.6-6.0**
- **Sunny Boy 3.0-6.0**

Not all Modbus parameters have been added, _yet_. Support for read/write registers _maybe_ later.

The SMA register map is mostly fixed, but it has been slightly modified with firmware updates in the past.


## Reading

The library consumes a `ModbusConnection` and manages its own unit handles
internally — each device class knows which unit IDs to poll:

```python
import asyncio

from modbus_connection.tmodbus import connect_tcp

from sma_modbus import SunnyBoySmartEnergy


async def main() -> None:
    connection = await connect_tcp("192.168.1.50", port=502)
    inverter = SunnyBoySmartEnergy(connection)

    # one pooled read refreshes the whole device, block by block
    await inverter.async_update()

    print("PV power:", inverter.pv_power, "W")
    print("PV energy:", inverter.pv_energy_total, "Wh")
    print("Battery SoC:", inverter.battery_state_of_charge, "%")
    print("DC string 1:", inverter.dc_voltage_1, "V", inverter.dc_power_1, "W")

    await connection.close()


asyncio.run(main())
```

A field reads as `None` when the device reports its not-a-value sentinel, so a
powered-down or unsupported measurement is distinct from a real zero.

## Testing on real hardware

`scripts/read_device.py` is a one-shot dump of everything the library reads:

```
uv run scripts/read_device.py <host> --type sunny_boy_smart_energy [--port 502]
uv run scripts/read_device.py <host> --type sunny_home_manager
uv run scripts/read_device.py <host> --type sunny_boy
```

Modbus must be enabled on the device.

## Testing support

`sma_modbus.testing` provides `set_input_registers()` to load a
`modbus_connection.mock.MockModbusConnection` with raw register words for a
component:

```python
from modbus_connection.mock import MockModbusConnection
from sma_modbus import SunnyHomeManager
from sma_modbus.testing import set_input_registers

connection = MockModbusConnection()
device = SunnyHomeManager(connection)
set_input_registers(
    connection,
    device,
    {"grid_import_energy": 123456, "grid_export_power": 750},
)
await device.async_update()
assert device.grid_import_energy == 123456
```

The `mock_modbus_connection` fixture (shipped by `modbus_connection`'s pytest
plugin) hands a ready-to-configure connection to each test.

## Disclaimer

This is an unofficial library and in no way affiliated with SMA Solar Technology AG.
