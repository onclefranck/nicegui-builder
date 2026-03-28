from .inspect import build_field_context
from nicegui_builder.core.models import ResolvedFieldNode
from .mapping import build_layout_node, resolve_widget_spec


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
        node=build_layout_node(field_ctx, widget, value),
    )
