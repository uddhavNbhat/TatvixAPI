from typing import Any


def append_or_clear(existing: list[Any] | None, updates: list[Any] | None) -> list[Any]:
    """
    Append incoming updates to existing list state.
    If the incoming updates contain the string "clear", reset existing state first.
    """
    current = list(existing or [])
    incoming = list(updates or [])

    if "clear" in incoming:
        return [item for item in incoming if item != "clear"]

    return current + incoming
