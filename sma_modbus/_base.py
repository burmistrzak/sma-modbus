"""Common base for SMA Modbus components.

SMA devices expose their measurements as Modbus *input
registers* (function code 4). Every component in this library reads from that
space, so the base class fixes ``register_space = "input"`` once here.

Some SMA devices serve their Type Label block (vendor, serial, firmware) on a
different Modbus unit ID than their measurement registers. The Sunny Home
Manager, for example, answers measurements on unit 2 but its Type Label on
unit 1. Subclasses declare which fields live on a non-default unit through
``field_unit_ids``; the base class then splits the read across the units and
merges the decoded values transparently.
"""

from enum import IntEnum
from typing import ClassVar

from modbus_connection import ModbusConnection
from modbus_connection.model import Component, ManualComponent
from modbus_connection.model.fields import RegisterField

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


class SystemStatus(IntEnum):
    """SMA system status (Operation.Health, register 30201)."""

    FAULT = 35
    OFF = 303
    OK = 307
    WARNING = 455


class SmaComponent(Component):
    """An SMA device modelled on its input-register block.

    Subclasses declare one typed field per measurement and a ``register_ranges``
    tuple naming the contiguous register blocks the device actually answers.
    The read planner then fetches each block in a single request and never
    bridges a gap the device does not serve.

    Fields that live on a different Modbus unit ID than ``default_unit_id``
    are declared normally (as class-level descriptors) and listed in
    ``field_unit_ids``.  The constructor removes them from the primary read
    plan and routes them to a :class:`~modbus_connection.model.ManualComponent`
    on the correct unit; ``async_update`` reads both and merges the values,
    so the descriptors still resolve transparently.
    """

    register_space = "input"

    # The unit ID this device's measurement registers answer on.
    default_unit_id: int = 3

    # Fields served on a unit ID other than ``default_unit_id``.
    # Subclasses override: ``{"field_name": unit_id, ...}``
    field_unit_ids: ClassVar[dict[str, int]] = {}

    def __init__(
        self,
        connection: ModbusConnection,
        unit_id: int | None = None,
    ) -> None:
        """Initialize the SMA component.

        ``unit_id`` overrides ``default_unit_id`` when the caller needs to
        target a specific unit (e.g. for testing). The connection is kept so
        secondary components can open their own unit handles.
        """
        self._connection = connection
        uid = unit_id if unit_id is not None else self.default_unit_id
        super().__init__(connection.for_unit(uid))

        # Group cross-unit fields by their target unit ID.
        by_unit: dict[int, list[str]] = {}
        for name, target_uid in self.field_unit_ids.items():
            if target_uid != uid:
                by_unit.setdefault(target_uid, []).append(name)

        # Remove cross-unit fields from the primary component so it does not
        # try to read registers the primary unit does not serve.
        if by_unit:
            cross_unit_names = {n for names in by_unit.values() for n in names}
            self.restrict_fields(
                name for name in self.declared_fields if name not in cross_unit_names
            )

        # Build a ManualComponent for each extra unit ID.
        self._extras: dict[int, ManualComponent] = {}
        for target_uid, names in by_unit.items():
            extra = ManualComponent(connection.for_unit(target_uid))
            for name in names:
                field = self.declared_fields[name]
                assert isinstance(field, RegisterField)
                extra.add(name, field, space="input")
            self._extras[target_uid] = extra

    async def async_update(self, *, notify: bool = True) -> None:
        """Read this component and every secondary unit, then merge values.

        Raises ``ModbusExceptionError`` if any unit rejects a block.
        """
        await super().async_update(notify=False)
        for extra in self._extras.values():
            await extra.async_update(notify=False)
            self._values.update(extra.values)
        if notify:
            self.notify()
