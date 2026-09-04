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
from enum import IntEnum

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
        "modbus_profile_revision": "Modbus profile revision",
        "susy_id": "SUSyID",
        "device_class": "Device class",
        "device_type": "Device type",
        "vendor": "Manufacturer",
        "serial_number": "Serial number",
        "firmware_version": "Firmware version",
        "rated_power_out": "Rated active power (WMaxOutRtg)",
        "rated_power_in": "Rated active power (WMaxInRtg)",
        "rated_apparent_power_out": "Rated apparent power (VAMaxOutRtg)",
        "rated_apparent_power_in": "Rated apparent power (VAMaxInRtg)",
        "rated_reactive_power_q1": "Rated reactive power Q1",
        "rated_reactive_power_q2": "Rated reactive power Q2",
        "rated_reactive_power_q3": "Rated reactive power Q3",
        "rated_reactive_power_q4": "Rated reactive power Q4",
        "rated_pf_min_q1": "Rated cos phi Q1",
        "rated_pf_min_q2": "Rated cos phi Q2",
        "rated_pf_min_q3": "Rated cos phi Q3",
        "rated_pf_min_q4": "Rated cos phi Q4",
        "ac_power": "AC power",
        "ac_power_l1": "AC power L1",
        "ac_power_l2": "AC power L2",
        "ac_power_l3": "AC power L3",
        "ac_voltage_l1": "AC voltage L1",
        "ac_voltage_l2": "AC voltage L2",
        "ac_voltage_l3": "AC voltage L3",
        "ac_voltage_l1_l2": "AC voltage L1-L2",
        "ac_voltage_l2_l3": "AC voltage L2-L3",
        "ac_voltage_l3_l1": "AC voltage L3-L1",
        "ac_current": "AC current",
        "ac_current_l1": "AC current L1",
        "ac_current_l2": "AC current L2",
        "ac_current_l3": "AC current L3",
        "grid_frequency": "Grid frequency",
        "ac_reactive_power": "AC reactive power",
        "ac_reactive_power_l1": "AC reactive power L1",
        "ac_reactive_power_l2": "AC reactive power L2",
        "ac_reactive_power_l3": "AC reactive power L3",
        "ac_apparent_power": "AC apparent power",
        "ac_apparent_power_l1": "AC apparent power L1",
        "ac_apparent_power_l2": "AC apparent power L2",
        "ac_apparent_power_l3": "AC apparent power L3",
        "power_factor": "Power factor",
        "power_factor_eei": "Power factor (EEI)",
        "battery_charge_energy": "Battery charge energy",
        "battery_discharge_energy": "Battery discharge energy",
        "battery_charge_power": "Battery charge power",
        "battery_discharge_power": "Battery discharge power",
        "battery_state_of_charge": "Battery state of charge",
        "battery_nominal_capacity": "Battery nominal capacity",
        "battery_temperature": "Battery temperature",
        "battery_health": "Battery health",
        "bms_firmware_version": "BMS firmware version",
        "bms_charge_energy": "BMS charge energy",
        "bms_discharge_energy": "BMS discharge energy",
        "battery_end_of_charge_voltage": "Battery end-of-charge voltage",
        "battery_end_of_discharge_voltage": "Battery end-of-discharge voltage",
        "battery_max_charge_current": "Battery max charge current",
        "battery_max_discharge_current": "Battery max discharge current",
        "battery_charge_control_available": "Battery charge control available",
        "bms_operating_status": "BMS operating status",
        "dc_power_0": "DC power string 0",
        "dc_power_1": "DC power string 1",
        "dc_power_2": "DC power string 2",
        "dc_energy_total_0": "DC energy total string 0",
        "dc_energy_total_1": "DC energy total string 1",
        "dc_energy_total_2": "DC energy total string 2",
        "dc_voltage_0": "DC voltage string 0",
        "dc_voltage_1": "DC voltage string 1",
        "dc_voltage_2": "DC voltage string 2",
        "dc_current_0": "DC current string 0",
        "dc_current_1": "DC current string 1",
        "dc_current_2": "DC current string 2",
        "insulation_resistance": "Insulation resistance",
        "insulation_residual_current": "Insulation residual current",
    },
    DeviceType.SUNNY_BOY: {
        "pv_power": "PV power",
        "pv_energy_total": "PV energy total",
        "modbus_profile_revision": "Modbus profile revision",
        "susy_id": "SUSyID",
        "device_class": "Device class",
        "device_type": "Device type",
        "vendor": "Manufacturer",
        "serial_number": "Serial number",
        "firmware_version": "Firmware version",
        "rated_power_in": "Rated active power (WMaxInRtg)",
        "rated_apparent_power_out": "Rated apparent power (VAMaxOutRtg)",
        "rated_apparent_power_in": "Rated apparent power (VAMaxInRtg)",
        "rated_reactive_power_q1": "Rated reactive power Q1",
        "rated_reactive_power_q2": "Rated reactive power Q2",
        "rated_reactive_power_q3": "Rated reactive power Q3",
        "rated_reactive_power_q4": "Rated reactive power Q4",
        "rated_pf_min_q1": "Rated cos phi Q1",
        "rated_pf_min_q2": "Rated cos phi Q2",
        "rated_pf_min_q3": "Rated cos phi Q3",
        "rated_pf_min_q4": "Rated cos phi Q4",
        "ac_power": "AC power",
        "ac_power_l1": "AC power L1",
        "ac_power_l2": "AC power L2",
        "ac_power_l3": "AC power L3",
        "ac_voltage_l1": "AC voltage L1",
        "ac_voltage_l2": "AC voltage L2",
        "ac_voltage_l3": "AC voltage L3",
        "ac_voltage_l1_l2": "AC voltage L1-L2",
        "ac_voltage_l2_l3": "AC voltage L2-L3",
        "ac_voltage_l3_l1": "AC voltage L3-L1",
        "ac_current": "AC current",
        "ac_current_l1": "AC current L1",
        "ac_current_l2": "AC current L2",
        "ac_current_l3": "AC current L3",
        "grid_frequency": "Grid frequency",
        "ac_reactive_power": "AC reactive power",
        "ac_reactive_power_l1": "AC reactive power L1",
        "ac_reactive_power_l2": "AC reactive power L2",
        "ac_reactive_power_l3": "AC reactive power L3",
        "ac_apparent_power": "AC apparent power",
        "ac_apparent_power_l1": "AC apparent power L1",
        "ac_apparent_power_l2": "AC apparent power L2",
        "ac_apparent_power_l3": "AC apparent power L3",
        "power_factor": "Power factor",
        "power_factor_eei": "Power factor (EEI)",
        "dc_power_0": "DC power string 0",
        "dc_power_1": "DC power string 1",
        "dc_voltage_0": "DC voltage string 0",
        "dc_voltage_1": "DC voltage string 1",
        "dc_current_0": "DC current string 0",
        "dc_current_1": "DC current string 1",
        "insulation_resistance": "Insulation resistance",
        "insulation_residual_current": "Insulation residual current",
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
            if isinstance(value, IntEnum):
                value_str = f"{value.name} ({value.value})"
            elif value is None:
                value_str = "N/A"
            else:
                value_str = str(value)
            print(f"  {label + ':':32}{value_str}{suffix}")
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
