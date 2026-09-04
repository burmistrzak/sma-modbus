"""Common base for SMA Modbus components.

SMA devices expose their measurements as Modbus *input
registers* (function code 4). Every component in this library reads from that
space, so the base class fixes ``register_space = "input"`` once here.
"""

from enum import IntEnum

from modbus_connection.model import Component


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
