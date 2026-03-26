from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class FilterOperator:
    name: str
    symbol: str


FILTER_OPERATORS: dict[str, FilterOperator] = {
    "contains": FilterOperator(name="contains", symbol="∋"),
    "equals": FilterOperator(name="equals", symbol="="),
    "notEquals": FilterOperator(name="notEquals", symbol="≠"),
    "gt": FilterOperator(name="gt", symbol=">"),
    "gte": FilterOperator(name="gte", symbol="≥"),
    "lt": FilterOperator(name="lt", symbol="<"),
    "lte": FilterOperator(name="lte", symbol="≤"),
    "startsWith": FilterOperator(name="startsWith", symbol="⋖"),
    "endsWith": FilterOperator(name="endsWith", symbol="⋗"),
    "in": FilterOperator(name="in", symbol="∈"),
    "notIn": FilterOperator(name="notIn", symbol="∉"),
    "regex": FilterOperator(name="regex", symbol="≈"),
    "between": FilterOperator(name="between", symbol="⋯"),
}


LEGACY_FILTER_OPERATOR_NAMES = {
    "ge": "gte",
    "le": "lte",
}


def normalize_filter_operator(name: str) -> str:
    return LEGACY_FILTER_OPERATOR_NAMES.get(name, name)


def canonical_filter_clause(raw_value, *, default_op: str = "equals") -> dict[str, Any]:
    if isinstance(raw_value, dict):
        operator = raw_value.get("op", default_op)
        value = raw_value.get("value")
        enabled = raw_value.get("enabled", True)
    else:
        operator = default_op
        value = raw_value
        enabled = True

    return {
        "op": normalize_filter_operator(operator),
        "value": value,
        "enabled": bool(enabled),
    }


def canonical_filter_store(
    filter_values: dict[str, object],
    *,
    default_op: str = "equals",
) -> dict[str, dict[str, Any]]:
    return {
        field_name: canonical_filter_clause(raw_value, default_op=default_op)
        for field_name, raw_value in filter_values.items()
    }


def active_filter_clauses(
    filter_values: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    return {
        field_name: clause
        for field_name, clause in filter_values.items()
        if clause.get("enabled", True)
    }
