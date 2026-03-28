from datetime import date, datetime

from nicegui import ui

from nicegui_builder.core.datetime_inputs import (
    DateTimeInput,
)
from nicegui_builder.core.filter_operators import (
    FILTER_OPERATORS,
    active_filter_clauses,
    normalize_filter_operator,
)
from nicegui_builder.core.models import CollectionSpec, FieldSpec, TableSpec, WidgetSpec
from .filters import (
    apply_scalar_filter,
    apply_text_filter,
    build_operator_options,
    is_empty_filter_value,
    normalize_filter_clause,
    validated_coerced_clause,
)
from .filter_ui import (
    default_builder_state,
    render_active_filters_list,
    render_filter_value_controls,
    set_select_options,
)

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
        self, spec: CollectionSpec, flavor: str = "std"
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
            variant=flavor,
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

            clause = validated_coerced_clause(column, normalize_filter_clause(value, column))
            operator = clause["op"]
            raw_value = clause["value"]
            if is_empty_filter_value(operator, raw_value):
                continue

            if column.source_meta.get("filter_kind") in {"select", "boolean"}:
                filtered = apply_scalar_filter(filtered, column.name, operator, raw_value)
                continue

            if column.python_type in {int, float} or column.python_type == "datetime":
                filtered = apply_scalar_filter(filtered, column.name, operator, raw_value)
                continue

            filtered = apply_text_filter(filtered, column.name, operator, raw_value)

        return _rows_from_dataframe(filtered)

    def render_collection(
        self,
        source,
        spec: CollectionSpec,
        flavor: str = "std",
        table_spec: TableSpec | None = None,
    ):
        if flavor != "filters":
            return None

        widget = table_spec.widget_spec if table_spec is not None else self.resolve_collection_widget(
            spec, flavor=flavor
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

        builder_state = default_builder_state(spec)

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
                        options=build_operator_options(initial_field),
                        value=builder_state["operator"],
                        clearable=False,
                    )
                    value_host = ui.column().classes("gap-2")

                    def _render_builder_value_controls():
                        value_host.clear()
                        with value_host:
                            render_filter_value_controls(
                                ui,
                                DateTimeInput,
                                filter_fields[str(builder_state["field_name"])],
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
                        set_select_options(operator_control, build_operator_options(field))
                        _set_operator(field.source_meta.get("filter_default_operator", "equals"))

                    def _on_operator_change(event):
                        if syncing_controls["operator"]:
                            return
                        _set_operator(str(event.value))

                    def _add_filter():
                        field_name = str(builder_state["field_name"])
                        operator = str(builder_state["operator"])
                        value = builder_state["value"]
                        if is_empty_filter_value(operator, value):
                            return
                        filter_values[field_name] = validated_coerced_clause(
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
                    render_active_filters_list(
                        ui,
                        active_filters_host,
                        filter_values,
                        filter_fields,
                        FILTER_OPERATORS,
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
