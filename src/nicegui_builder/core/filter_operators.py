from dataclasses import dataclass


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
