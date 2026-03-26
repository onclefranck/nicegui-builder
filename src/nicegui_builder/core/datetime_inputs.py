from datetime import date as date_type, datetime, time as time_type
import locale
from typing import Callable

from nicegui import ui


def _coerce_datetime_like(value):
    if hasattr(value, "to_pydatetime"):
        return value.to_pydatetime()
    return value


def _parse_datetime_string(value: str):
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def _time_to_string(value) -> str:
    if not isinstance(value, time_type):
        return str(value)

    if value.microsecond:
        return value.isoformat(timespec="microseconds")
    if value.second:
        return value.isoformat(timespec="seconds")
    return value.isoformat(timespec="minutes")


def split_datetime_value(value) -> tuple[str | None, str | None]:
    if value in (None, ""):
        return (None, None)

    value = _coerce_datetime_like(value)

    if isinstance(value, datetime):
        return (value.date().isoformat(), _time_to_string(value.time()))

    if isinstance(value, date_type) and not isinstance(value, datetime):
        return (value.isoformat(), None)

    if isinstance(value, str):
        text = value.strip()
        if not text:
            return (None, None)

        parsed = _parse_datetime_string(text)
        if parsed is None:
            if "T" in text:
                date_value, time_value = text.split("T", 1)
                return (date_value or None, time_value or None)
            if " " in text:
                date_value, time_value = text.split(" ", 1)
                return (date_value or None, time_value or None)
            return (text, None)

        return (parsed.date().isoformat(), _time_to_string(parsed.time()))

    return (str(value), None)


def combine_datetime_value(date_value, time_value):
    if date_value in (None, "") and time_value in (None, ""):
        return None
    if date_value in (None, ""):
        return time_value
    if time_value in (None, ""):
        return date_value
    return f"{date_value}T{time_value}"


def normalize_datetime_input(raw_value):
    if raw_value in (None, ""):
        return raw_value
    raw_value = _coerce_datetime_like(raw_value)
    if isinstance(raw_value, datetime):
        return raw_value
    if isinstance(raw_value, date_type):
        return datetime.combine(raw_value, datetime.min.time())
    if isinstance(raw_value, str):
        parsed = _parse_datetime_string(raw_value)
        if parsed is not None:
            return parsed
        return raw_value
    return raw_value


def datetime_to_input_value(value) -> str:
    date_value, time_value = split_datetime_value(value)
    return combine_datetime_value(date_value, time_value) or ""


def format_datetime_for_display(value) -> str:
    normalized = normalize_datetime_input(value)
    if not isinstance(normalized, datetime):
        return str(value)

    try:
        current_locale = locale.setlocale(locale.LC_TIME)
        locale.setlocale(locale.LC_TIME, "")
        try:
            formatted = normalized.strftime("%x %X").strip()
        finally:
            locale.setlocale(locale.LC_TIME, current_locale)
        if formatted:
            return formatted
    except locale.Error:
        pass

    return normalized.strftime("%Y-%m-%d %H:%M")


def build_split_datetime_node(
    *,
    field_name: str,
    label: str,
    raw_value=None,
    container_methods: str = "row",
    container_params: dict | None = None,
    container_props: str = "",
    container_classes: str = "w-full items-end gap-2",
    date_ref: str | None = None,
    time_ref: str | None = None,
    date_label: str | None = None,
    time_label: str | None = None,
    date_props: str = "clearable",
    time_props: str = "clearable",
    date_classes: str = "col",
    time_classes: str = "col",
) -> dict:
    date_value = None
    time_value = None
    if raw_value not in (None, ""):
        date_value, time_value = split_datetime_value(raw_value)

    return {
        "methods": container_methods,
        "params": dict(container_params or {}),
        "props": container_props,
        "classes": container_classes,
        "children": [
            {
                "date_input": {
                    "ref": date_ref or f"field:{field_name}:date",
                    "params": {
                        "value": date_value,
                        "label": date_label or f"{label} date",
                    },
                    "props": date_props,
                    "classes": date_classes,
                }
            },
            {
                "time_input": {
                    "ref": time_ref or f"field:{field_name}:time",
                    "params": {
                        "value": time_value,
                        "label": time_label or f"{label} time",
                    },
                    "props": time_props,
                    "classes": time_classes,
                }
            },
        ],
    }


def render_split_datetime_inputs(
    *,
    value,
    on_change: Callable[[object], None],
    date_label: str = "Date",
    time_label: str = "Time",
    row_classes: str = "items-end gap-2",
    date_props: str = "clearable",
    time_props: str = "clearable",
):
    date_value, time_value = split_datetime_value(value)
    state = {
        "date": date_value,
        "time": time_value,
    }

    with ui.row().classes(row_classes):
        date_control = ui.date_input(value=date_value, label=date_label).props(date_props)
        time_control = ui.time_input(value=time_value, label=time_label).props(time_props)

        def _emit():
            combined = combine_datetime_value(state["date"], state["time"])
            on_change(normalize_datetime_input(combined))

        def _on_date_change(event):
            state["date"] = event.value
            _emit()

        def _on_time_change(event):
            state["time"] = event.value
            _emit()

        date_control.on_value_change(_on_date_change)
        time_control.on_value_change(_on_time_change)

    return date_control, time_control
