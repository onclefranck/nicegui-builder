from nicegui_builder.core.datetime_inputs import DateTimeInput
from nicegui_builder.core.models import CollectionSpec, FieldSpec

from .filters import format_filter_value


def default_builder_state(spec: CollectionSpec) -> dict[str, object]:
    if not spec.filters:
        return {
            "field_name": "",
            "operator": "equals",
            "value": "",
        }

    initial_field = spec.filters[0]
    initial_operator = initial_field.source_meta.get("filter_default_operator", "equals")
    initial_value = ["", ""] if initial_operator == "between" else ""
    return {
        "field_name": initial_field.name,
        "operator": initial_operator,
        "value": initial_value,
    }


def set_select_options(control, options: dict[str, str]) -> None:
    if hasattr(control, "set_options"):
        control.set_options(options)
    else:
        control.options = options
    if hasattr(control, "update"):
        control.update()


def render_filter_value_controls(ui_module, datetime_input_factory, field: FieldSpec, operator: str, state: dict[str, object], state_key: str) -> None:
    def set_state_value(value) -> None:
        state[state_key] = value

    if operator == "between":
        values = state.get(state_key)
        if not isinstance(values, (list, tuple)) or len(values) != 2:
            values = ["", ""]
        left_value, right_value = list(values)

        def set_range_item(index: int, value) -> None:
            next_values = [left_value, right_value]
            current = state.get(state_key)
            if isinstance(current, (list, tuple)) and len(current) == 2:
                next_values = list(current)
            next_values[index] = value
            state[state_key] = next_values

        with ui_module.row().classes("items-end gap-2"):
            if field.source_meta.get("filter_kind", "text") == "number":
                left_control = ui_module.number(label="From")
                right_control = ui_module.number(label="To")
                if left_value not in (None, "") and hasattr(left_control, "value"):
                    left_control.value = left_value
                if right_value not in (None, "") and hasattr(right_control, "value"):
                    right_control.value = right_value
                left_control.on_value_change(lambda event: set_range_item(0, event.value))
                right_control.on_value_change(lambda event: set_range_item(1, event.value))
                return

            with ui_module.column().classes("gap-2"):
                datetime_input_factory(
                    value=left_value,
                    on_value_change=lambda event: set_range_item(0, event.value),
                    date_options={"label": "From date"},
                    time_options={"label": "From time"},
                )
            with ui_module.column().classes("gap-2"):
                datetime_input_factory(
                    value=right_value,
                    on_value_change=lambda event: set_range_item(1, event.value),
                    date_options={"label": "To date"},
                    time_options={"label": "To time"},
                )
        return

    filter_kind = field.source_meta.get("filter_kind", "text")

    if operator in {"in", "notIn"}:
        control = ui_module.input(label="Values").props("clearable")
    elif filter_kind == "select" and operator in {"equals", "notEquals"}:
        control = ui_module.select(
            options=field.choices,
            label="Value",
            clearable=True,
        )
    elif filter_kind == "number":
        control = ui_module.number(label="Value")
    elif filter_kind == "boolean":
        control = ui_module.select(
            options=[True, False],
            label="Value",
            clearable=True,
        )
    elif filter_kind == "datetime":
        datetime_input_factory(
            value=state.get(state_key, ""),
            on_value_change=lambda event: set_state_value(event.value),
        )
        return
    else:
        control = ui_module.input(label="Value").props("clearable")

    current_value = state.get(state_key, "")
    if current_value not in (None, "") and hasattr(control, "value"):
        control.value = current_value
    control.on_value_change(lambda event: set_state_value(event.value))


def render_active_filters_list(
    ui_module,
    active_filters_host,
    filter_values: dict[str, object],
    filter_fields: dict[str, FieldSpec],
    filter_operator_symbols: dict[str, object],
    on_toggle,
    on_remove,
) -> None:
    active_filters_host.clear()
    with active_filters_host:
        ui_module.label("Active filters").classes("text-subtitle2")
        if not filter_values:
            ui_module.label("No active filters").classes("text-body2 text-grey-6")
            return

        for field_name, clause in filter_values.items():
            if not isinstance(clause, dict):
                continue
            field = filter_fields.get(field_name)
            if field is None:
                continue
            operator = str(clause.get("op", "equals"))
            symbol = filter_operator_symbols.get(operator, filter_operator_symbols["equals"]).symbol
            value = clause.get("value")
            enabled = clause.get("enabled", True)

            with ui_module.row().classes("w-full items-center gap-2"):
                ui_module.checkbox(
                    value=enabled,
                    on_change=lambda event, name=field_name: on_toggle(name, event.value),
                )
                ui_module.button(icon="delete", on_click=lambda *_args, name=field_name, **_kwargs: on_remove(name)).props("flat round dense")
                ui_module.label(
                    f"{field.title or field.name} {symbol} {format_filter_value(field, value)}"
                ).classes("text-body2")
