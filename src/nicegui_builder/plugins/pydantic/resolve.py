from .inspect import build_field_context
from nicegui_builder.core.models import LayoutNode, ResolvedFieldNode
from nicegui_builder.core.datetime_inputs import DateTimeInput, build_split_datetime_node
from .mapping import (
    resolve_map_type,
    resolve_widget_spec,
)


def _build_datetime_split_node(field_ctx: dict, default_info: dict, value: dict | None) -> LayoutNode:
    value = value or {}
    label = field_ctx.get("attributes_title") or field_ctx["fieldname"]
    raw_value = field_ctx.get("fieldvalue")
    logical_ref = value.get("ref") or f"field:{field_ctx['fieldname']}"
    raw_params = dict(value.get("params") or {})
    raw_container = raw_params.pop("container", None)
    container = DateTimeInput.normalize_container(raw_container)
    if raw_container is None or "methods" not in raw_container:
        container["methods"] = default_info.get("methods", container["methods"])
    default_params = dict(default_info.get("params", {}))
    container["params"] = {
        **default_params,
        **dict(container.get("params") or {}),
    }
    if raw_container is None or "classes" not in raw_container:
        container["classes"] = default_info.get("classes", container.get("classes", ""))
    if raw_container is None or "props" not in raw_container:
        container["props"] = default_info.get("props", container.get("props", ""))

    return LayoutNode.from_dict(
        build_split_datetime_node(
            field_name=field_ctx["fieldname"],
            label=label,
            raw_value=raw_value,
            ref=logical_ref,
            container=container,
            component_props=value.get("props", ""),
            component_classes=value.get("classes", ""),
        )
    )


def resolve_field_node(
    model_class, model_instance, fieldname: str, value: dict | None
) -> ResolvedFieldNode:
    value = value or {}

    field_ctx = build_field_context(model_class, model_instance, fieldname)
    field_info = field_ctx["field_info"]
    requested_variant = value.get("methods", "std")

    map_type = resolve_map_type(field_info.annotation)
    widget, default_info = resolve_widget_spec(
        field_info, field_info.annotation, requested_variant
    )

    if map_type == "datetime" and widget.variant == "split":
        return ResolvedFieldNode(
            field_ctx=field_ctx,
            node=_build_datetime_split_node(field_ctx, default_info, value),
        )

    params = dict(widget.params)
    params.update(value.get("params") or {})

    props = " ".join(
        part for part in [
            widget.props,
            value.get("props", ""),
        ]
        if part
    )
    classes = " ".join(
        part for part in [
            widget.classes,
            value.get("classes", ""),
        ]
        if part
    )

    return ResolvedFieldNode(
        field_ctx=field_ctx,
        node=LayoutNode(
            methods=widget.component,
            params=params,
            props=props,
            classes=classes,
        ),
    )
