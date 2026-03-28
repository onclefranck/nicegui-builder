from .inspect import build_field_context
from nicegui_builder.core.models import LayoutNode, ResolvedFieldNode
from nicegui_builder.core.datetime_inputs import DateTimeInput, build_split_datetime_node
from .mapping import resolve_widget_spec


def _build_datetime_input_node(field_ctx: dict, params: dict, props: str, classes: str, ref: str | None) -> LayoutNode:
    label = field_ctx.get("attributes_title") or field_ctx["fieldname"]
    raw_value = field_ctx.get("fieldvalue")
    logical_ref = ref or f"field:{field_ctx['fieldname']}"
    raw_params = dict(params)
    raw_container = raw_params.pop("container", None)
    container = DateTimeInput.normalize_container(raw_container)

    return LayoutNode.from_dict(
        build_split_datetime_node(
            field_name=field_ctx["fieldname"],
            label=label,
            raw_value=raw_value,
            ref=logical_ref,
            container=container,
            component_props=props,
            component_classes=classes,
            date_ref=raw_params.pop("date_ref", None),
            time_ref=raw_params.pop("time_ref", None),
            date_options=raw_params.pop("date_options", None),
            time_options=raw_params.pop("time_options", None),
        )
    )


def _build_node_from_widget(
    field_ctx: dict, widget, value: dict | None
) -> LayoutNode:
    value = value or {}
    params = dict(widget.params)
    params.update(value.get("params") or {})
    props = " ".join(part for part in [widget.props, value.get("props", "")] if part)
    classes = " ".join(part for part in [widget.classes, value.get("classes", "")] if part)
    ref = value.get("ref")

    if widget.component == "datetime_input":
        return _build_datetime_input_node(field_ctx, params, props, classes, ref)

    return LayoutNode(
        methods=widget.component,
        params=params,
        props=props,
        classes=classes,
        ref=ref,
    )


def resolve_field_node(
    model_class, model_instance, fieldname: str, value: dict | None
) -> ResolvedFieldNode:
    value = value or {}

    field_ctx = build_field_context(model_class, model_instance, fieldname)
    field_info = field_ctx["field_info"]
    requested_variant = value.get("methods", "std")

    widget, _default_info = resolve_widget_spec(field_info, field_info.annotation, requested_variant)

    return ResolvedFieldNode(
        field_ctx=field_ctx,
        node=_build_node_from_widget(field_ctx, widget, value),
    )
