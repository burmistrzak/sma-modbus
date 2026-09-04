"""Common base for SMA Modbus components.

SMA devices expose their measurements as Modbus *input
registers* (function code 4). Every component in this library reads from that
space, so the base class fixes ``register_space = "input"`` once here.
"""

from enum import IntEnum

from modbus_connection.model import Component

# Release-type code -> suffix letter, per "SMA Firmware Data Formats".
_RELEASE_TYPES = {0: "N", 1: "E", 2: "A", 3: "B", 4: "R", 5: "S"}


def decode_firmware_version(raw: int) -> str:
    """Decode an SMA firmware DWORD into ``Major.Minor.Build.Suffix``.

    Bytes 1-2 are BCD-coded Major.Minor, byte 3 is Build (binary), byte 4
    is the release-type code.  See "SMA Firmware Data Formats" in the SMA
    Modbus Technical Information.
    """
    major = (raw >> 24) & 0xFF
    minor = (raw >> 16) & 0xFF
    build = (raw >> 8) & 0xFF
    release_code = raw & 0xFF
    # BCD decode: each nibble is a decimal digit.
    major_dec = (major >> 4) * 10 + (major & 0x0F)
    minor_dec = (minor >> 4) * 10 + (minor & 0x0F)
    suffix = _RELEASE_TYPES.get(release_code, str(release_code))
    return f"{major_dec}.{minor_dec:02d}.{build}.{suffix}"


class Vendor(IntEnum):
    """Manufacturer (Nameplate.Vendor, register 30055)."""

    SMA = 461


class SmaComponent(Component):
    """An SMA device modelled on its input-register block.

    Subclasses declare one typed field per measurement and a ``register_ranges``
    tuple naming the contiguous register blocks the device actually answers.
    The read planner then fetches each block in a single request and never
    bridges a gap the device does not serve.
    """

    register_space = "input"
