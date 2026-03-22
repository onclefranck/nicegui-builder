from nicegui import ui

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
    operators = ["contains", "equals", "in"]
    if column.python_type is bool:
        filter_kind = "boolean"
        operators = ["equals", "in"]
    elif column.python_type in {int, float}:
        filter_kind = "number"
        operators = ["equals", "gt", "ge", "lt", "le", "between", "in"]
    elif column.choices and column.python_type is not str:
        filter_kind = "select"
        operators = ["equals", "in"]

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
        },
    )


def _normalize_filter_clause(value, column: FieldSpec):
    if isinstance(value, dict):
        return {
            "op": value.get("op", "equals"),
            "value": value.get("value"),
        }

    default_op = "equals"
    if column.source_meta.get("filter_kind") == "text":
        default_op = "contains"

    return {
        "op": default_op,
        "value": value,
    }


def _apply_text_filter(filtered, column_name: str, operator: str, raw_value):
    series = filtered[column_name].astype(str)

    if operator == "contains":
        return filtered[series.str.contains(str(raw_value), case=False, na=False)]

    if operator == "equals":
        return filtered[series.str.lower() == str(raw_value).lower()]

    if operator == "in":
        values = raw_value if isinstance(raw_value, list) else [raw_value]
        normalized = {str(item).lower() for item in values}
        return filtered[series.str.lower().isin(normalized)]

    raise ValueError(f"unsupported text filter operator: {operator}")


def _apply_scalar_filter(filtered, column_name: str, operator: str, raw_value):
    series = filtered[column_name]

    if operator == "equals":
        return filtered[series == raw_value]

    if operator == "gt":
        return filtered[series > raw_value]

    if operator == "ge":
        return filtered[series >= raw_value]

    if operator == "lt":
        return filtered[series < raw_value]

    if operator == "le":
        return filtered[series <= raw_value]

    if operator == "between":
        if not isinstance(raw_value, (list, tuple)) or len(raw_value) != 2:
            raise ValueError("between operator expects a two-item list or tuple")
        lower, upper = raw_value
        return filtered[series.between(lower, upper)]

    if operator == "in":
        values = raw_value if isinstance(raw_value, list) else [raw_value]
        return filtered[series.isin(values)]

    raise ValueError(f"unsupported scalar filter operator: {operator}")


def _rows_from_dataframe(source) -> list[dict]:
    rows = []
    for row_id, record in enumerate(source.to_dict(orient="records")):
        row = dict(record)
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

            clause = _normalize_filter_clause(value, column)
            operator = clause["op"]
            raw_value = clause["value"]
            if raw_value in (None, "", []):
                continue

            if column.source_meta.get("filter_kind") in {"select", "boolean"}:
                filtered = _apply_scalar_filter(filtered, column.name, operator, raw_value)
                continue

            if column.python_type in {int, float}:
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
        table_component = None

        def apply_filters():
            table_component.rows = self.filter_rows(source, filter_values)
            table_component.update()

        with ui.card().classes("w-full gap-4"):
            with ui.row().classes("w-full items-end gap-3"):
                for field in spec.filters:
                    label = field.title or field.name
                    filter_kind = field.source_meta.get("filter_kind", "text")

                    if filter_kind == "select":
                        control = ui.select(
                            options=field.choices,
                            label=label,
                            clearable=True,
                        )
                    elif filter_kind == "number":
                        control = ui.number(label=label)
                    elif filter_kind == "boolean":
                        control = ui.select(
                            options=[True, False],
                            label=label,
                            clearable=True,
                        )
                    else:
                        control = ui.input(label=label).props("clearable")

                    def _on_change(event, field_name=field.name):
                        filter_values[field_name] = event.value
                        apply_filters()

                    control.on_value_change(_on_change)

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
            try:
                table_component.table_spec = table_spec
            except Exception:
                pass
            try:
                table_component.filter_values = filter_values
            except Exception:
                pass

        return table_component
