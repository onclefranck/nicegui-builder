from .inspect import build_field_context
from nicegui_builder.core.datetime_inputs import build_split_datetime_node
from .mapping import (
    build_validation_props,
    get_defaults_from_map,
    resolve_map_type,
    select_default_variant,
)


def _build_datetime_split_node(field_ctx: dict, default_info: dict, value: dict | None) -> dict:
    value = value or {}
    label = field_ctx.get("attributes_title") or field_ctx["fieldname"]
    raw_value = field_ctx.get("fieldvalue")
    container_methods = value.get("container", default_info.get("methods"))
    container_params = dict(default_info.get("params", {}))
    container_params.update(value.get("params") or {})
    container_classes = " ".join(
        part
        for part in [
            default_info.get("classes", ""),
            value.get("classes", ""),
        ]
        if part
    )
    container_props = " ".join(
        part
        for part in [
            default_info.get("props", ""),
            value.get("props", ""),
        ]
        if part
    )

    return build_split_datetime_node(
        field_name=field_ctx["fieldname"],
        label=label,
        raw_value=raw_value,
        container_methods=container_methods,
        container_params=container_params,
        container_props=container_props,
        container_classes=container_classes,
    )


def resolve_field_node(model_class, model_instance, fieldname: str, value: dict | None) -> dict:
    value = value or {}

    field_ctx = build_field_context(model_class, model_instance, fieldname)
    field_info = field_ctx["field_info"]
    requested_variant = value.get("methods", "std")

    map_type = resolve_map_type(field_info.annotation)
    effective_variant = select_default_variant(field_info, map_type, requested_variant)
    default_info = get_defaults_from_map(map_type, effective_variant)
    methods = default_info.get("methods")
    validation_props = build_validation_props(field_info, methods)

    if map_type == "datetime" and effective_variant == "split":
        return {
            "field_ctx": field_ctx,
            "default_info": default_info,
            "node": _build_datetime_split_node(field_ctx, default_info, value),
        }

    params = dict(default_info.get("params", {}))
    params.update(value.get("params") or {})

    props = " ".join(
        part for part in [
            default_info.get("props", ""),
            validation_props,
            value.get("props", ""),
        ]
        if part
    )
    classes = " ".join(
        part for part in [
            default_info.get("classes", ""),
            value.get("classes", ""),
        ]
        if part
    )

    return {
        "field_ctx": field_ctx,
        "default_info": default_info,
        "node": {
            "methods": methods,
            "params": params,
            "props": props,
            "classes": classes,
        },
    }
