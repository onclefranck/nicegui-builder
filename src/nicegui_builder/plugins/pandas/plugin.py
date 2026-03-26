from datetime import date, datetime

from nicegui import ui

from nicegui_builder.core.datetime_inputs import (
    DateTimeInput,
)
from nicegui_builder.core.filter_operators import (
    FILTER_OPERATORS,
    active_filter_clauses,
    canonical_filter_clause,
    normalize_filter_operator,
)
from nicegui_builder.core.models import CollectionSpec, FieldSpec, TableSpec, WidgetSpec

INTERNAL_ROW_ID = "nicegui_builder_row_id"


def _import_pandas():
    try:
        import pandas as pd
    except ImportError:
        return None

    return pd


def _is_numeric_dtype(dtype) -> bool:
    pd = _import_pandas()
    return pd is not None and pd.api.types.is_numeric_dtype(dtype)


def _is_bool_dtype(dtype) -> bool:
    pd = _import_pandas()
    return pd is not None and pd.api.types.is_bool_dtype(dtype)


def _is_datetime_dtype(dtype) -> bool:
    pd = _import_pandas()
    return pd is not None and pd.api.types.is_datetime64_any_dtype(dtype)


def _python_type_from_dtype(dtype):
    if _is_bool_dtype(dtype):
        return bool
    if _is_numeric_dtype(dtype):
        if "int" in str(dtype):
            return int
        return float
    if _is_datetime_dtype(dtype):
        return "datetime"
    return str


def _build_column_spec(column_name, series) -> FieldSpec:
    dtype = series.dtype
    non_null = series.dropna()
    choices: list[object] = []
    distinct_count = int(non_null.nunique()) if len(non_null) else 0

    if distinct_count and distinct_count <= 12:
        choices = non_null.astype(str).drop_duplicates().tolist()

    constraints = {}
    if _is_numeric_dtype(dtype) and len(non_null):
        constraints["min"] = non_null.min()
        constraints["max"] = non_null.max()

    return FieldSpec(
        name=column_name,
        python_type=_python_type_from_dtype(dtype),
        required=bool(series.notna().all()),
        nullable=bool(series.isna().any()),
        title=column_name,
        choices=choices,
        constraints=constraints,
        source_meta={
            "dtype": str(dtype),
            "distinct_count": distinct_count,
        },
    )


def _build_filter_spec(column: FieldSpec) -> FieldSpec:
    filter_kind = "text"
    operators = ["contains", "equals", "notEquals", "startsWith", "endsWith", "in", "notIn", "regex"]
    if column.python_type is bool:
        filter_kind = "boolean"
        operators = ["equals", "notEquals"]
    elif column.python_type in {int, float}:
        filter_kind = "number"
        operators = ["equals", "notEquals", "gt", "gte", "lt", "lte", "in", "notIn", "between"]
    elif column.python_type == "datetime":
        filter_kind = "datetime"
        operators = ["equals", "notEquals", "gt", "gte", "lt", "lte", "between"]
    elif column.choices and column.python_type is not str:
        filter_kind = "select"
        operators = ["equals", "notEquals", "in", "notIn"]

    return FieldSpec(
        name=column.name,
        python_type=column.python_type,
        title=column.title,
        choices=list(column.choices),
        constraints=dict(column.constraints),
        source_meta={
            **column.source_meta,
            "filter": True,
            "filter_kind": filter_kind,
            "filter_operators": operators,
            "filter_default_operator": "contains" if filter_kind == "text" else "equals",
        },
    )


def _normalize_filter_clause(value, column: FieldSpec):
    default_op = column.source_meta.get("filter_default_operator")
    if default_op is None:
        default_op = "contains" if column.source_meta.get("filter_kind") == "text" else "equals"
    return canonical_filter_clause(value, default_op=default_op)


def _parse_csv_values(raw_value):
    if isinstance(raw_value, str):
        return [item.strip() for item in raw_value.split(",") if item.strip()]
    if isinstance(raw_value, (list, tuple, set)):
        return [item for item in raw_value if item not in (None, "")]
    return [raw_value]


def _coerce_datetime_value(raw_value):
    pd = _import_pandas()
    if pd is None:
        return raw_value
    return pd.to_datetime(raw_value)


def _coerce_filter_values(column: FieldSpec, operator: str, raw_value):
    operator = normalize_filter_operator(operator)

    if operator == "between":
        if not isinstance(raw_value, (list, tuple)) or len(raw_value) != 2:
            raise ValueError("between operator expects a two-item list or tuple")
        lower, upper = raw_value
        if column.python_type == "datetime":
            return [_coerce_datetime_value(lower), _coerce_datetime_value(upper)]
        if column.python_type in {int, float}:
            caster = int if column.python_type is int else float
            return [caster(lower), caster(upper)]
        return [lower, upper]

    if operator in {"in", "notIn"}:
        values = _parse_csv_values(raw_value)
        if column.python_type == "datetime":
            return [_coerce_datetime_value(value) for value in values]
        if column.python_type in {int, float}:
            caster = int if column.python_type is int else float
            return [caster(value) for value in values]
        return values

    if column.python_type == "datetime" and raw_value not in (None, ""):
        return _coerce_datetime_value(raw_value)

    return raw_value


def _validated_coerced_clause(column: FieldSpec, clause: dict[str, object]) -> dict[str, object]:
    operator = normalize_filter_operator(str(clause["op"]))
    allowed = column.source_meta.get("filter_operators", [])
    if operator not in allowed:
        raise ValueError(f"unsupported filter operator for {column.name}: {operator}")

    raw_value = clause["value"]
    if _is_empty_filter_value(operator, raw_value):
        return {
            "op": operator,
            "value": raw_value,
            "enabled": clause.get("enabled", True),
        }

    return {
        "op": operator,
        "value": _coerce_filter_values(column, operator, raw_value),
        "enabled": clause.get("enabled", True),
    }


def _apply_text_filter(filtered, column_name: str, operator: str, raw_value):
    operator = normalize_filter_operator(operator)
    series = filtered[column_name].astype(str)

    if operator == "contains":
        return filtered[series.str.contains(str(raw_value), case=False, na=False)]

    if operator == "equals":
        return filtered[series.str.lower() == str(raw_value).lower()]

    if operator == "notEquals":
        return filtered[series.str.lower() != str(raw_value).lower()]

    if operator == "startsWith":
        return filtered[series.str.lower().str.startswith(str(raw_value).lower(), na=False)]

    if operator == "endsWith":
        return filtered[series.str.lower().str.endswith(str(raw_value).lower(), na=False)]

    if operator == "in":
        values = _parse_csv_values(raw_value)
        normalized = {str(item).lower() for item in values}
        return filtered[series.str.lower().isin(normalized)]

    if operator == "notIn":
        values = _parse_csv_values(raw_value)
        normalized = {str(item).lower() for item in values}
        return filtered[~series.str.lower().isin(normalized)]

    if operator == "regex":
        return filtered[series.str.contains(str(raw_value), case=False, na=False, regex=True)]

    raise ValueError(f"unsupported text filter operator: {operator}")


def _apply_scalar_filter(filtered, column_name: str, operator: str, raw_value):
    operator = normalize_filter_operator(operator)
    series = filtered[column_name]

    if operator == "equals":
        return filtered[series == raw_value]

    if operator == "notEquals":
        return filtered[series != raw_value]

    if operator == "gt":
        return filtered[series > raw_value]

    if operator == "gte":
        return filtered[series >= raw_value]

    if operator == "lt":
        return filtered[series < raw_value]

    if operator == "lte":
        return filtered[series <= raw_value]

    if operator == "between":
        if not isinstance(raw_value, (list, tuple)) or len(raw_value) != 2:
            raise ValueError("between operator expects a two-item list or tuple")
        lower, upper = raw_value
        return filtered[series.between(lower, upper)]

    if operator == "in":
        values = _parse_csv_values(raw_value)
        if _is_datetime_dtype(series.dtype):
            values = [_coerce_datetime_value(value) for value in values]
        elif _is_numeric_dtype(series.dtype):
            caster = int if "int" in str(series.dtype) else float
            values = [caster(value) for value in values]
        return filtered[series.isin(values)]

    if operator == "notIn":
        values = _parse_csv_values(raw_value)
        if _is_datetime_dtype(series.dtype):
            values = [_coerce_datetime_value(value) for value in values]
        elif _is_numeric_dtype(series.dtype):
            caster = int if "int" in str(series.dtype) else float
            values = [caster(value) for value in values]
        return filtered[~series.isin(values)]

    raise ValueError(f"unsupported scalar filter operator: {operator}")


def _build_operator_options(field: FieldSpec) -> dict[str, str]:
    return {
        operator: FILTER_OPERATORS[operator].symbol
        for operator in field.source_meta.get("filter_operators", [])
        if operator in FILTER_OPERATORS
    }


def _is_empty_filter_value(operator: str, value) -> bool:
    operator = normalize_filter_operator(operator)
    if operator == "between":
        if not isinstance(value, (list, tuple)) or len(value) != 2:
            return True
        return any(item in (None, "") for item in value)
    return value in (None, "", [])


def _format_filter_value(field: FieldSpec, value) -> str:
    filter_kind = field.source_meta.get("filter_kind")
    if filter_kind == "datetime":
        if isinstance(value, (list, tuple)):
            return " .. ".join(DateTimeInput.format_for_display(item) for item in value)
        return DateTimeInput.format_for_display(value)
    if isinstance(value, (list, tuple)):
        return " .. ".join(str(item) for item in value)
    return str(value)


def _normalize_range_value(value) -> list[object]:
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        return ["", ""]
    return list(value)


def _set_range_item(state: dict[str, object], state_key: str, index: int, value) -> None:
    values = _normalize_range_value(state.get(state_key))
    values[index] = value
    state[state_key] = values


def _set_select_options(control, options: dict[str, str]) -> None:
    if hasattr(control, "set_options"):
        control.set_options(options)
    else:
        control.options = options
    if hasattr(control, "update"):
        control.update()


def _default_builder_state(spec: CollectionSpec) -> dict[str, object]:
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


def _bind_textual_value_control(control, state: dict[str, object], state_key: str) -> None:
    current_value = state.get(state_key, "")
    if current_value not in (None, "") and hasattr(control, "value"):
        control.value = current_value

    def _on_change(event):
        state[state_key] = event.value

    control.on_value_change(_on_change)


def _render_between_value_controls(filter_kind: str, state: dict[str, object], state_key: str) -> None:
    left_value, right_value = _normalize_range_value(state.get(state_key))

    with ui.row().classes("items-end gap-2"):
        if filter_kind == "number":
            left_control = ui.number(label="From")
            right_control = ui.number(label="To")
            if left_value not in (None, "") and hasattr(left_control, "value"):
                left_control.value = left_value
            if right_value not in (None, "") and hasattr(right_control, "value"):
                right_control.value = right_value

            left_control.on_value_change(lambda event: _set_range_item(state, state_key, 0, event.value))
            right_control.on_value_change(lambda event: _set_range_item(state, state_key, 1, event.value))
            return

        with ui.column().classes("gap-2"):
            DateTimeInput(
                value=left_value,
                on_value_change=lambda event: _set_range_item(state, state_key, 0, event.value),
                date_options={"label": "From date"},
                time_options={"label": "From time"},
            )
        with ui.column().classes("gap-2"):
            DateTimeInput(
                value=right_value,
                on_value_change=lambda event: _set_range_item(state, state_key, 1, event.value),
                date_options={"label": "To date"},
                time_options={"label": "To time"},
            )


def _render_single_value_control(field: FieldSpec, operator: str, state: dict[str, object], state_key: str) -> None:
    filter_kind = field.source_meta.get("filter_kind", "text")

    if operator in {"in", "notIn"}:
        _bind_textual_value_control(ui.input(label="Values").props("clearable"), state, state_key)
        return

    if filter_kind == "select" and operator in {"equals", "notEquals"}:
        control = ui.select(
            options=field.choices,
            label="Value",
            clearable=True,
        )
        _bind_textual_value_control(control, state, state_key)
        return

    if filter_kind == "number":
        _bind_textual_value_control(ui.number(label="Value"), state, state_key)
        return

    if filter_kind == "boolean":
        control = ui.select(
            options=[True, False],
            label="Value",
            clearable=True,
        )
        _bind_textual_value_control(control, state, state_key)
        return

    if filter_kind == "datetime":
        DateTimeInput(
            value=state.get(state_key, ""),
            on_value_change=lambda event: state.__setitem__(state_key, event.value),
        )
        return

    _bind_textual_value_control(ui.input(label="Value").props("clearable"), state, state_key)


def _render_filter_value_controls(field: FieldSpec, operator: str, state: dict[str, object], state_key: str) -> None:
    if operator == "between":
        _render_between_value_controls(field.source_meta.get("filter_kind", "text"), state, state_key)
        return

    _render_single_value_control(field, operator, state, state_key)


def _rows_from_dataframe(source) -> list[dict]:
    rows = []
    for row_id, record in enumerate(source.to_dict(orient="records")):
        row = {}
        for key, value in dict(record).items():
            if isinstance(value, (datetime, date)):
                row[key] = value.isoformat(timespec="minutes") if isinstance(value, datetime) else value.isoformat()
            else:
                row[key] = value
        row[INTERNAL_ROW_ID] = row_id
        rows.append(row)
    return rows


def _render_active_filters_list(
    active_filters_host,
    filter_values: dict[str, object],
    filter_fields: dict[str, FieldSpec],
    on_toggle,
    on_remove,
) -> None:
    active_filters_host.clear()
    with active_filters_host:
        ui.label("Active filters").classes("text-subtitle2")
        if not filter_values:
            ui.label("No active filters").classes("text-body2 text-grey-6")
            return

        for field_name, clause in filter_values.items():
            if not isinstance(clause, dict):
                continue
            field = filter_fields.get(field_name)
            if field is None:
                continue
            operator = normalize_filter_operator(clause.get("op", "equals"))
            symbol = FILTER_OPERATORS.get(operator, FILTER_OPERATORS["equals"]).symbol
            value = clause.get("value")
            enabled = clause.get("enabled", True)

            with ui.row().classes("w-full items-center gap-2"):
                ui.checkbox(
                    value=enabled,
                    on_change=lambda event, name=field_name: on_toggle(name, event.value),
                )
                ui.button(icon="delete", on_click=lambda *_args, name=field_name, **_kwargs: on_remove(name)).props("flat round dense")
                ui.label(
                    f"{field.title or field.name} {symbol} {_format_filter_value(field, value)}"
                ).classes("text-body2")


class PandasPlugin:
    name = "pandas"

    def supports(self, source) -> bool:
        pd = _import_pandas()
        if pd is None:
            return False

        return isinstance(source, pd.DataFrame)

    def inspect_collection(self, source) -> CollectionSpec:
        columns = [
            _build_column_spec(column_name, source[column_name])
            for column_name in source.columns
        ]
        filters = [
            _build_filter_spec(column)
            for column in columns
        ]

        return CollectionSpec(
            name=getattr(source, "__class__", type(source)).__name__,
            columns=columns,
            filters=filters,
            source_meta={
                "rows": len(source),
                "columns": len(columns),
            },
        )

    def resolve_collection_widget(
        self, spec: CollectionSpec, variant: str = "std"
    ) -> WidgetSpec:
        columns = [
            {
                "name": INTERNAL_ROW_ID,
                "label": INTERNAL_ROW_ID,
                "field": INTERNAL_ROW_ID,
                "sortable": False,
                "classes": "hidden",
                "headerClasses": "hidden",
            }
        ] + [
            {
                "name": column.name,
                "label": column.title or column.name,
                "field": column.name,
                "align": "right" if column.python_type in {int, float} else "left",
                "sortable": True,
            }
            for column in spec.columns
        ]

        default_sort_by = spec.columns[0].name if spec.columns else "id"
        return WidgetSpec(
            component="table",
            variant=variant,
            params={
                "columns": columns,
                "rows": [],
                "row_key": INTERNAL_ROW_ID,
                "selection": "multiple",
                "pagination": {
                    "rowsPerPage": 10,
                    "sortBy": default_sort_by,
                    "descending": False,
                },
            },
            props="flat bordered wrap-cells",
            classes="w-full",
        )

    def prepare_rows(self, source) -> list[dict]:
        return _rows_from_dataframe(source)

    def filter_rows(self, source, filter_values: dict[str, object]) -> list[dict]:
        filtered = source

        for column in self.inspect_collection(source).filters:
            value = filter_values.get(column.name)
            if value in (None, "", []):
                continue
            if isinstance(value, dict) and value.get("enabled") is False:
                continue

            clause = _validated_coerced_clause(column, _normalize_filter_clause(value, column))
            operator = clause["op"]
            raw_value = clause["value"]
            if _is_empty_filter_value(operator, raw_value):
                continue

            if column.source_meta.get("filter_kind") in {"select", "boolean"}:
                filtered = _apply_scalar_filter(filtered, column.name, operator, raw_value)
                continue

            if column.python_type in {int, float} or column.python_type == "datetime":
                filtered = _apply_scalar_filter(filtered, column.name, operator, raw_value)
                continue

            filtered = _apply_text_filter(filtered, column.name, operator, raw_value)

        return _rows_from_dataframe(filtered)

    def render_collection(
        self,
        source,
        spec: CollectionSpec,
        variant: str = "std",
        table_spec: TableSpec | None = None,
    ):
        if variant != "filters":
            return None

        widget = table_spec.widget_spec if table_spec is not None else self.resolve_collection_widget(
            spec, variant=variant
        )
        rows = self.prepare_rows(source)
        filter_values: dict[str, object] = {}
        filter_fields = {field.name: field for field in spec.filters}
        field_options = {
            field.name: field.title or field.name
            for field in spec.filters
        }
        table_component = None

        def apply_filters():
            table_component.rows = self.filter_rows(source, active_filter_clauses(filter_values))
            table_component.update()

        builder_state = _default_builder_state(spec)

        with ui.card().classes("w-full gap-4"):
            if spec.filters:
                with ui.row().classes("w-full items-end gap-3"):
                    syncing_controls = {
                        "field": False,
                        "operator": False,
                    }
                    initial_field = filter_fields[str(builder_state["field_name"])]
                    field_control = ui.select(
                        options=field_options,
                        value=builder_state["field_name"],
                        clearable=False,
                        label="Field",
                    )
                    operator_control = ui.select(
                        options=_build_operator_options(initial_field),
                        value=builder_state["operator"],
                        clearable=False,
                    )
                    value_host = ui.column().classes("gap-2")

                    def _current_field() -> FieldSpec:
                        return filter_fields[str(builder_state["field_name"])]

                    def _render_builder_value_controls():
                        value_host.clear()
                        with value_host:
                            _render_filter_value_controls(
                                _current_field(),
                                str(builder_state["operator"]),
                                builder_state,
                                "value",
                            )

                    def _reset_builder_value():
                        builder_state["value"] = ["", ""] if builder_state["operator"] == "between" else ""

                    def _set_operator(operator_name: str):
                        builder_state["operator"] = normalize_filter_operator(operator_name)
                        _reset_builder_value()
                        syncing_controls["operator"] = True
                        try:
                            operator_control.value = builder_state["operator"]
                        finally:
                            syncing_controls["operator"] = False
                        _render_builder_value_controls()
                        if hasattr(operator_control, "update"):
                            operator_control.update()

                    def _on_field_change(event):
                        if syncing_controls["field"]:
                            return
                        field_name = str(event.value)
                        builder_state["field_name"] = field_name
                        field = filter_fields[field_name]
                        _set_select_options(operator_control, _build_operator_options(field))
                        _set_operator(field.source_meta.get("filter_default_operator", "equals"))

                    def _on_operator_change(event):
                        if syncing_controls["operator"]:
                            return
                        _set_operator(str(event.value))

                    def _add_filter():
                        field_name = str(builder_state["field_name"])
                        operator = str(builder_state["operator"])
                        value = builder_state["value"]
                        if _is_empty_filter_value(operator, value):
                            return
                        filter_values[field_name] = _validated_coerced_clause(
                            filter_fields[field_name],
                            {"op": operator, "value": value, "enabled": True},
                        )
                        render_active_filters()
                        apply_filters()

                    field_control.on_value_change(_on_field_change)
                    operator_control.on_value_change(_on_operator_change)
                    _render_builder_value_controls()
                    ui.button("Add filter", on_click=lambda *_args, **_kwargs: _add_filter())

                active_filters_host = ui.column().classes("w-full gap-2")

                def _toggle_filter(field_name: str, enabled: bool | None = None):
                    current = filter_values.get(field_name)
                    if not isinstance(current, dict):
                        return
                    if enabled is None:
                        enabled = not current.get("enabled", True)
                    current["enabled"] = enabled
                    render_active_filters()
                    apply_filters()

                def _remove_filter(field_name: str):
                    filter_values.pop(field_name, None)
                    render_active_filters()
                    apply_filters()

                def render_active_filters():
                    _render_active_filters_list(
                        active_filters_host,
                        filter_values,
                        filter_fields,
                        _toggle_filter,
                        _remove_filter,
                    )

                render_active_filters()

            with ui.element("div").classes("w-full"):
                table_component = ui.table(
                    columns=widget.params["columns"],
                    rows=rows,
                    row_key=widget.params["row_key"],
                    selection=widget.params.get("selection"),
                    pagination=widget.params.get("pagination"),
                )
                if widget.classes:
                    table_component.classes(widget.classes)
                if widget.props:
                    table_component.props(widget.props)

        if table_spec is not None:
            table_component.table_spec = table_spec
            table_component.filter_values = filter_values
            table_component.refresh_filters_ui = render_active_filters if spec.filters else (lambda: None)

        return table_component
