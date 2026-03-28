from nicegui_builder.core.datetime_inputs import DateTimeInput
from nicegui_builder.core.filter_operators import (
    FILTER_OPERATORS,
    canonical_filter_clause,
    normalize_filter_operator,
)
from nicegui_builder.core.models import FieldSpec


def _import_pandas():
    try:
        import pandas as pd
    except ImportError:
        return None

    return pd


def _is_numeric_dtype(dtype) -> bool:
    pd = _import_pandas()
    return pd is not None and pd.api.types.is_numeric_dtype(dtype)


def _is_datetime_dtype(dtype) -> bool:
    pd = _import_pandas()
    return pd is not None and pd.api.types.is_datetime64_any_dtype(dtype)


def normalize_filter_clause(value, column: FieldSpec):
    default_op = column.source_meta.get("filter_default_operator")
    if default_op is None:
        default_op = "contains" if column.source_meta.get("filter_kind") == "text" else "equals"
    return canonical_filter_clause(value, default_op=default_op)


def parse_csv_values(raw_value):
    if isinstance(raw_value, str):
        return [item.strip() for item in raw_value.split(",") if item.strip()]
    if isinstance(raw_value, (list, tuple, set)):
        return [item for item in raw_value if item not in (None, "")]
    return [raw_value]


def coerce_datetime_value(raw_value):
    pd = _import_pandas()
    if pd is None:
        return raw_value
    return pd.to_datetime(raw_value)


def coerce_filter_values(column: FieldSpec, operator: str, raw_value):
    operator = normalize_filter_operator(operator)

    if operator == "between":
        if not isinstance(raw_value, (list, tuple)) or len(raw_value) != 2:
            raise ValueError("between operator expects a two-item list or tuple")
        lower, upper = raw_value
        if column.python_type == "datetime":
            return [coerce_datetime_value(lower), coerce_datetime_value(upper)]
        if column.python_type in {int, float}:
            caster = int if column.python_type is int else float
            return [caster(lower), caster(upper)]
        return [lower, upper]

    if operator in {"in", "notIn"}:
        values = parse_csv_values(raw_value)
        if column.python_type == "datetime":
            return [coerce_datetime_value(value) for value in values]
        if column.python_type in {int, float}:
            caster = int if column.python_type is int else float
            return [caster(value) for value in values]
        return values

    if column.python_type == "datetime" and raw_value not in (None, ""):
        return coerce_datetime_value(raw_value)

    return raw_value


def is_empty_filter_value(operator: str, value) -> bool:
    operator = normalize_filter_operator(operator)
    if operator == "between":
        if not isinstance(value, (list, tuple)) or len(value) != 2:
            return True
        return any(item in (None, "") for item in value)
    return value in (None, "", [])


def validated_coerced_clause(column: FieldSpec, clause: dict[str, object]) -> dict[str, object]:
    operator = normalize_filter_operator(str(clause["op"]))
    allowed = column.source_meta.get("filter_operators", [])
    if operator not in allowed:
        raise ValueError(f"unsupported filter operator for {column.name}: {operator}")

    raw_value = clause["value"]
    if is_empty_filter_value(operator, raw_value):
        return {
            "op": operator,
            "value": raw_value,
            "enabled": clause.get("enabled", True),
        }

    return {
        "op": operator,
        "value": coerce_filter_values(column, operator, raw_value),
        "enabled": clause.get("enabled", True),
    }


def apply_text_filter(filtered, column_name: str, operator: str, raw_value):
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
        values = parse_csv_values(raw_value)
        normalized = {str(item).lower() for item in values}
        return filtered[series.str.lower().isin(normalized)]

    if operator == "notIn":
        values = parse_csv_values(raw_value)
        normalized = {str(item).lower() for item in values}
        return filtered[~series.str.lower().isin(normalized)]

    if operator == "regex":
        return filtered[series.str.contains(str(raw_value), case=False, na=False, regex=True)]

    raise ValueError(f"unsupported text filter operator: {operator}")


def apply_scalar_filter(filtered, column_name: str, operator: str, raw_value):
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
        values = parse_csv_values(raw_value)
        if _is_datetime_dtype(series.dtype):
            values = [coerce_datetime_value(value) for value in values]
        elif _is_numeric_dtype(series.dtype):
            caster = int if "int" in str(series.dtype) else float
            values = [caster(value) for value in values]
        return filtered[series.isin(values)]

    if operator == "notIn":
        values = parse_csv_values(raw_value)
        if _is_datetime_dtype(series.dtype):
            values = [coerce_datetime_value(value) for value in values]
        elif _is_numeric_dtype(series.dtype):
            caster = int if "int" in str(series.dtype) else float
            values = [caster(value) for value in values]
        return filtered[~series.isin(values)]

    raise ValueError(f"unsupported scalar filter operator: {operator}")


def build_operator_options(field: FieldSpec) -> dict[str, str]:
    return {
        operator: FILTER_OPERATORS[operator].symbol
        for operator in field.source_meta.get("filter_operators", [])
        if operator in FILTER_OPERATORS
    }


def format_filter_value(field: FieldSpec, value) -> str:
    filter_kind = field.source_meta.get("filter_kind")
    if filter_kind == "datetime":
        if isinstance(value, (list, tuple)):
            return " .. ".join(DateTimeInput.format_for_display(item) for item in value)
        return DateTimeInput.format_for_display(value)
    if isinstance(value, (list, tuple)):
        return " .. ".join(str(item) for item in value)
    return str(value)
