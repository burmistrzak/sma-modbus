"""Read SMA Modbus data for testing.

Usage:
    uv run scripts/read_device.py <host> --type <device> [--port 502] [--unit 3]

``--type`` selects the device model:
  sunny_home_manager       SMA Sunny Home Manager (grid meter)
  sunny_boy_smart_energy   SMA Sunny Boy Smart Energy (hybrid inverter)
  sunny_boy                SMA Sunny Boy (PV inverter)
"""

import argparse
import asyncio
import logging
import sys

from modbus_connection import ModbusError
from modbus_connection.tmodbus import connect_tcp

from sma_modbus import DEVICE_CLASSES, DeviceType

# Default Modbus unit ID per device type: the Sunny Home Manager answers on
# unit 2, inverters on unit 3.
DEFAULT_UNIT_IDS: dict[DeviceType, int] = {
    DeviceType.SUNNY_HOME_MANAGER: 2,
    DeviceType.SUNNY_BOY_SMART_ENERGY: 3,
    DeviceType.SUNNY_BOY: 3,
}

# human-friendly labels for each field, in declaration order
LABELS: dict[DeviceType, dict[str, str]] = {
    DeviceType.SUNNY_HOME_MANAGER: {
        "system_status": "System status",
        "grid_import_energy": "Grid import energy",
        "grid_export_energy": "Grid export energy",
        "grid_import_power": "Grid import power",
        "grid_export_power": "Grid export power",
    },
    DeviceType.SUNNY_BOY_SMART_ENERGY: {
        "pv_power": "PV power",
        "pv_energy_total": "PV energy total",
        "battery_charge_energy": "Battery charge energy",
        "battery_discharge_energy": "Battery discharge energy",
        "battery_charge_power": "Battery charge power",
        "battery_discharge_power": "Battery discharge power",
        "battery_state_of_charge": "Battery state of charge",
        "battery_nominal_capacity": "Battery nominal capacity",
        "dc_power_1": "DC power string 1",
        "dc_power_2": "DC power string 2",
        "dc_power_3": "DC power string 3",
        "dc_energy_total_1": "DC energy total string 1",
        "dc_energy_total_2": "DC energy total string 2",
        "dc_energy_total_3": "DC energy total string 3",
        "dc_voltage_1": "DC voltage string 1",
        "dc_voltage_2": "DC voltage string 2",
        "dc_voltage_3": "DC voltage string 3",
    },
    DeviceType.SUNNY_BOY: {
        "pv_power": "PV power",
        "pv_energy_total": "PV energy total",
        "dc_power_1": "DC power string A",
        "dc_power_2": "DC power string B",
        "dc_voltage_1": "DC voltage string A",
        "dc_voltage_2": "DC voltage string B",
    },
}


async def read_device(
    host: str, port: int, unit_id: int, device_type: DeviceType
) -> int:
    """Read and print the data of one SMA Modbus unit."""
    print(f"\n=== {host}:{port} unit {unit_id} ({device_type.value}) ===")
    try:
        connection = await connect_tcp(host, port=port)
    except ModbusError as err:
        print(f"Connection failed: {err}")
        print("Is Modbus TCP enabled on the device?")
        return 1

    try:
        device = DEVICE_CLASSES[device_type](connection.for_unit(unit_id))
        try:
            await device.async_update()
        except ModbusError as err:
            print(f"Reading data failed: {err}")
            return 1

        labels = LABELS[device_type]
        for name in device.declared_fields:
            value = getattr(device, name)
            unit = device.declared_fields[name].unit
            label = labels.get(name, name)
            suffix = f" {unit}" if unit else ""
            print(f"  {label + ':':32}{value}{suffix}")
        return 0
    finally:
        await connection.close()


async def main() -> int:
    """Run the reader."""
    parser = argparse.ArgumentParser(description="Read SMA Modbus data")
    parser.add_argument("host", help="IP address or hostname of the device")
    parser.add_argument(
        "--type",
        required=True,
        choices=[t.value for t in DeviceType],
        help="SMA device model",
    )
    parser.add_argument("--port", type=int, default=502, help="Modbus TCP port")
    parser.add_argument(
        "--unit",
        type=int,
        default=None,
        help="Modbus unit ID (default: 2 for sunny_home_manager, 3 otherwise)",
    )
    parser.add_argument(
        "--debug", action="store_true", help="enable verbose protocol logging"
    )
    args = parser.parse_args()

    device_type = DeviceType(args.type)
    unit_id = args.unit if args.unit is not None else DEFAULT_UNIT_IDS[device_type]

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.getLogger("tmodbus").setLevel(logging.CRITICAL)

    return await read_device(args.host, args.port, unit_id, device_type)


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
