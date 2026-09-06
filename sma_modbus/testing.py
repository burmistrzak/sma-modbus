"""Helpers to populate a mock Modbus unit for tests.

Tests build an in-memory :class:`~modbus_connection.mock.MockModbusConnection`
and load it with *raw* register words - the unsigned integers the device would
return on the wire, before any scaling is applied. A field's own ``decode``
then applies sign handling, scaling and the not-a-value sentinel.

``set_input_registers`` writes the big-endian words for a component's fields
into the correct mock unit.  Fields on a non-default unit ID (declared via
``SmaComponent.field_unit_ids``) are written to that unit's ``input`` store;
the rest go to the component's primary unit.  Pass the raw register value, or
``None`` to write the field's sentinel (``nan``) pattern so it decodes to
``None``.
"""

from typing import TYPE_CHECKING, Any

from modbus_connection import ModbusConnection
from modbus_connection.model import NumberField

if TYPE_CHECKING:
    from ._base import SmaComponent

__all__ = ["set_input_registers"]


def _encode_words(field: NumberField[Any], raw: int | None) -> list[int]:
    """Encode a raw register value to big-endian 16-bit words."""
    count = field.count
    if raw is None:
        # the field's not-a-value sentinel, or zero when it has none
        raw = next(iter(field.nan)) if field.nan else 0
    # mask to the field's width and split into big-endian words
    raw &= (1 << (16 * count)) - 1
    return [(raw >> (16 * (count - 1 - i))) & 0xFFFF for i in range(count)]


def set_input_registers(
    connection: "ModbusConnection",
    component: "SmaComponent",
    values: dict[str, int | None],
) -> None:
    """Write raw input-register words for ``component``'s fields into mock units.

    ``values`` maps a field's attribute name to its raw register value (the
    integer the device returns, *before* scaling). ``None`` writes the field's
    sentinel so it decodes to ``None``.

    Fields declared in ``component.field_unit_ids`` are written to the mock
    unit for their target unit ID; all others go to the component's primary
    unit (``component.default_unit_id``).

    Raises ``KeyError`` for an unknown field name.
    """
    field_unit_ids = getattr(component, "field_unit_ids", {})
    primary_uid = component.default_unit_id

    for name, raw in values.items():
        field = component.declared_fields[name]
        assert isinstance(field, NumberField)
        uid = field_unit_ids.get(name, primary_uid)
        unit = connection.for_unit(uid)
        for offset, word in enumerate(_encode_words(field, raw)):
            unit.input[field.address + offset] = word  # type: ignore[attr-defined]
