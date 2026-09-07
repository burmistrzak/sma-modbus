"""Dump SMA Modbus Type Label registers for debugging.

Usage:
    uv run scripts/dump_registers.py <host> [--port 502] [--units 1 2 3]

Reads the Type Label input registers (30001-30008, 30051-30060) and the
Unit ID query holding register block at 42109 from each given unit ID,
printing the raw 16-bit words plus the combined 32-bit values.
Use this to find out which unit ID actually serves the device identification
registers on a given device.
"""

import argparse
import asyncio
import logging
import sys

from modbus_connection import ModbusError
from modbus_connection.tmodbus import connect_tcp

# Input registers: Type Label fields (30001-30008, 30051-30060).
INPUT_REGISTERS: list[tuple[int, str, int]] = [
    (30001, "Modbus profile revision", 2),
    (30003, "SUSyID", 2),
    (30005, "Serial number (30005)", 2),
    (30007, "Register 30007", 2),
    (30051, "Device class", 2),
    (30053, "Device type / model", 2),
    (30055, "Manufacturer", 2),
    (30057, "Serial number (30057)", 2),
    #    (30059, "Firmware version", 2),
]

# Holding registers: SMA Modbus TI section 5.2.1 "Unit ID assignment".
# 42109 = SUSy ID (U16), 42110 = serial number (U32), 42112 = Unit ID (U16).
HOLDING_REGISTERS: list[tuple[int, str, int]] = [
    (42109, "SUSyID (42109)", 1),
    (42110, "Serial number (42110)", 2),
    (42112, "Data unit ID (42112)", 1),
]

NAN_SENTINELS = {0xFFFFFFFF, 0x00FFFFFD, 0xFFFFFFFE, 0x80000000}


def _combine_u32(words: list[int]) -> int:
    return (words[0] << 16) | words[1]


async def dump_unit(unit, unit_id: int) -> None:
    """Read and print Type Label and Unit ID registers for one unit ID."""
    print(f"\n--- Unit ID {unit_id} ---")
    print("  Input registers (Type Label):")
    for address, label, count in INPUT_REGISTERS:
        await _dump_register(unit.read_input_registers, address, label, count)
    print("  Holding registers (Query of Unit ID):")
    for address, label, count in HOLDING_REGISTERS:
        await _dump_register(unit.read_holding_registers, address, label, count)


async def _dump_register(read_func, address: int, label: str, count: int) -> None:
    try:
        words = await read_func(address, count)
    except ModbusError as err:
        print(f"  {address:>5}  {label + ':':28}ERROR: {err}")
        return
    raw = " ".join(f"{w:04X}" for w in words)
    if count == 2:
        u32 = _combine_u32(words)
        value_str = f"0x{u32:08X}" if u32 in NAN_SENTINELS else str(u32)
        print(f"  {address:>5}  {label + ':':28}{value_str}  (raw: {raw})")
    else:
        print(f"  {address:>5}  {label + ':':28}{words[0]}  (raw: {raw})")


async def main() -> int:
    """Run the dump tool."""
    parser = argparse.ArgumentParser(description="Dump SMA Modbus Type Label registers")
    parser.add_argument("host", help="IP address or hostname of the device")
    parser.add_argument("--port", type=int, default=502, help="Modbus TCP port")
    parser.add_argument(
        "--units",
        type=int,
        nargs="+",
        default=[1, 2, 3],
        help="Unit IDs to probe (default: 1 2 3)",
    )
    parser.add_argument(
        "--debug", action="store_true", help="enable verbose protocol logging"
    )
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.getLogger("tmodbus").setLevel(logging.CRITICAL)

    print(f"=== {args.host}:{args.port} ===")
    try:
        connection = await connect_tcp(args.host, port=args.port)
    except ModbusError as err:
        print(f"Connection failed: {err}")
        print("Is Modbus TCP enabled on the device?")
        return 1

    try:
        for unit_id in args.units:
            unit = connection.for_unit(unit_id)
            await dump_unit(unit, unit_id)
        return 0
    finally:
        await connection.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
