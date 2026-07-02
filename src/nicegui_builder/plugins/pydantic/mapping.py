import enum
from functools import cache
import types
import typing as t

from pydantic import BaseModel
from nicegui_builder.core.datetime_inputs import DateTimeInput
from nicegui_builder.core.models import LayoutNode, WidgetSpec

from ...utils import load_layout


NoneType = type(None)


def extract_options(field_info):
    annotation = unwrap_optional_annotation(field_info.annotation)
    origin = t.get_origin(annotation)

    if origin is t.Literal:
        return list(t.get_args(annotation))

    if isinstance(annotation, type) and issubclass(annotation, enum.Enum):
        return [member.value for member in annotation]

    return []


def select_default_variant(field_info, map_type: str, requested_variant: str) -> str:
    if requested_variant != "std":
        return requested_variant

    metadata = field_info.asdict()
    attributes = metadata.get("attributes", {})
    annotation = unwrap_optional_annotation(field_info.annotation)
    origin = t.get_origin(annotation)

    if map_type == "str":
        max_length = attributes.get("max_length")
        field_name = (attributes.get("title") or "").lower()
        description = (attributes.get("description") or "").lower()
        text_hints = ("description", "message", "content", "notes", "comment", "body")
        if max_length and max_length > 120:
            return "textarea"
        if any(hint in field_name or hint in description for hint in text_hints):
            return "textarea"

    if map_type in {"date", "time"}:
        return "picker"

    if map_type == "datetime":
        return "split"

    if origin is t.Literal:
        options = t.get_args(annotation)
        if 0 < len(options) <= 4:
            return "radio"

    if isinstance(annotation, type) and issubclass(annotation, enum.Enum):
        if len(annotation) <= 4:
            return "radio"

    return requested_variant


def build_validation_props(field_info, methods: str) -> str:
    attributes = field_info.asdict().get("attributes", {})
    props: list[str] = []

    if methods in {"input", "textarea"}:
        min_length = attributes.get("min_length")
        max_length = attributes.get("max_length")
        if min_length is not None:
            props.append(f"minlength={min_length}")
        if max_length is not None:
            props.append(f"maxlength={max_length}")
            props.append("counter")

    if methods in {"number", "slider", "knob"}:
        for source_key, target_key in (("ge", "min"), ("gt", "min"), ("le", "max"), ("lt", "max")):
            value = attributes.get(source_key)
            if value is not None:
                props.append(f"{target_key}={value}")

        multiple_of = attributes.get("multiple_of")
        if multiple_of is not None:
            props.append(f"step={multiple_of}")

    return " ".join(dict.fromkeys(props))


def unwrap_optional_annotation(annotation):
    origin = t.get_origin(annotation)

    if origin in (t.Union, types.UnionType):
        args = [arg for arg in t.get_args(annotation) if arg is not NoneType]
        if len(args) == 1:
            return unwrap_optional_annotation(args[0])

    return annotation


@cache
def load_pydantic_widget_map():
    return load_layout("pydantic-nicegui.yml", caller_file=__file__)


@cache
def available_map_types():
    return {key.split("|", 1)[0] for key in load_pydantic_widget_map()}


def resolve_map_type(annotation) -> str:
    annotation = unwrap_optional_annotation(annotation)
    origin = t.get_origin(annotation)
    candidates: list[str] = []

    if origin is t.Literal:
        candidates.append("Literal")
    elif origin is not None and hasattr(origin, "__name__"):
        candidates.append(origin.__name__)

    if isinstance(annotation, type):
        if issubclass(annotation, BaseModel):
            return "dict"

        candidates.append(annotation.__name__)

        if issubclass(annotation, enum.Enum):
            candidates.append("Enum")

        candidates.extend(base.__name__ for base in annotation.__mro__[1:] if base is not object)
    elif hasattr(annotation, "__name__"):
        candidates.append(annotation.__name__)

    known_types = available_map_types()
    for candidate in candidates:
        if candidate in known_types:
            return candidate

    if candidates:
        return candidates[0]

    return str(annotation)


def get_defaults_from_map(map_type: str, variant: str = "std"):
    mapping = load_pydantic_widget_map()
    if not map_type:
        error = (
            f'can\'t resolve a key from map_type: "{map_type}" and variant: "{variant}" to handle pydantic-nicegui.yml'
        )
        raise ValueError(error)

    variant = variant or "std"
    map_key = f"{map_type}|{variant}"
    fallback_key = f"{map_type}|std"

    if map_key in mapping:
        return mapping[map_key]

    if fallback_key in mapping:
        return mapping[fallback_key]

    error = f'can\'t resolve a key from map_type: "{map_type}" and variant: "{variant}" to handle pydantic-nicegui.yml'
    raise KeyError(error)


def _build_datetime_widget_spec(variant: str, methods: str, default_info: dict) -> WidgetSpec:
    return WidgetSpec(
        component="datetime_input",
        variant=variant,
        params={
            "container": {
                "methods": methods,
                "params": dict(default_info.get("params", {})),
                "classes": default_info.get("classes", ""),
                "props": default_info.get("props", ""),
            }
        },
    )


def resolve_widget_spec(field_info, python_type, variant: str = "std", map_type: str | None = None) -> WidgetSpec:
    map_type = map_type or resolve_map_type(python_type)
    effective_variant = select_default_variant(field_info, map_type, variant)
    default_info = get_defaults_from_map(map_type, effective_variant)
    methods = default_info.get("methods")

    if map_type == "datetime" and effective_variant == "split":
        return _build_datetime_widget_spec(effective_variant, methods, default_info)

    validation_props = build_validation_props(field_info, methods)
    props = " ".join(part for part in [default_info.get("props", ""), validation_props] if part)

    return WidgetSpec(
        component=methods,
        variant=effective_variant,
        params=dict(default_info.get("params", {})),
        props=props,
        classes=default_info.get("classes", ""),
    )


def build_layout_node(field_ctx: dict, widget: WidgetSpec, value: dict | None = None) -> LayoutNode:
    value = value or {}
    params = dict(widget.params)
    params.update(value.get("params") or {})
    props = " ".join(part for part in [widget.props, value.get("props", "")] if part)
    classes = " ".join(part for part in [widget.classes, value.get("classes", "")] if part)
    ref = value.get("ref")

    if widget.component == "datetime_input":
        label = field_ctx.get("attributes_title") or field_ctx["fieldname"]
        raw_value = field_ctx.get("fieldvalue")
        logical_ref = ref or f"field:{field_ctx['fieldname']}"
        raw_params = dict(params)
        raw_container = raw_params.pop("container", None)
        container = DateTimeInput.normalize_container(raw_container)
        normalized_date_options = DateTimeInput.normalize_part_options(
            raw_params.pop("date_options", None),
            defaults={
                **DateTimeInput.DEFAULT_DATE_OPTIONS,
                "label": f"{label} date",
                "classes": "col",
            },
        )
        normalized_time_options = DateTimeInput.normalize_part_options(
            raw_params.pop("time_options", None),
            defaults={
                **DateTimeInput.DEFAULT_TIME_OPTIONS,
                "label": f"{label} time",
                "classes": "col",
            },
        )

        return LayoutNode(
            methods="datetime_input",
            ref=logical_ref,
            params={
                "value": raw_value,
                "container": container,
                "date_ref": raw_params.pop("date_ref", None) or f"{logical_ref}:date",
                "time_ref": raw_params.pop("time_ref", None) or f"{logical_ref}:time",
                "date_options": normalized_date_options,
                "time_options": normalized_time_options,
            },
            props=props,
            classes=classes,
        )

    return LayoutNode(
        methods=widget.component,
        params=params,
        props=props,
        classes=classes,
        ref=ref,
    )
