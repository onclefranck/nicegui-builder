from nicegui_builder.core.models import FieldSpec, LayoutNode, WidgetSpec


def default_field_classes(spec: FieldSpec, widget: WidgetSpec) -> str:
    if spec.source_meta.get("section") == "structured":
        return "col-span-12"

    if widget.component in {"textarea", "radio", "checkbox", "switch"}:
        return "col-span-12"

    if spec.constraints.get("max_length", 0) and spec.constraints["max_length"] > 120:
        return "col-span-12"

    if widget.component in {"input", "number", "select", "date", "time", "color_input"}:
        return "col-span-6"

    return "col-span-12"


def filters_field_classes(spec: FieldSpec, widget: WidgetSpec) -> str:
    if widget.component in {"textarea", "radio"}:
        return "col-span-12"

    if widget.component in {"input", "number", "select", "date", "time"}:
        return "col-span-6"

    return "col-span-12"


def field_group_label(spec: FieldSpec) -> str:
    meta = spec.source_meta
    if "group_label" in meta:
        return meta["group_label"]
    if meta.get("is_nested_model"):
        return "Nested models"
    if meta.get("is_collection"):
        return "Collections"
    if meta.get("is_structured"):
        return "Structured data"
    return "General"


def filter_variant_for_field(spec: FieldSpec) -> str:
    return spec.source_meta.get("filter_variant", "search")


def group_fields_by_section(fields: list[FieldSpec]) -> list[tuple[str, list[FieldSpec]]]:
    grouped: dict[str, list[FieldSpec]] = {}
    for field in fields:
        grouped.setdefault(field_group_label(field), []).append(field)

    ordered_sections = ["General", "Nested models", "Collections", "Structured data"]
    results: list[tuple[str, list[FieldSpec]]] = []

    for section in ordered_sections:
        section_fields = grouped.pop(section, [])
        if section_fields:
            results.append((section, section_fields))

    for section, section_fields in grouped.items():
        results.append((section, section_fields))

    return results


def build_section_node(
    title: str,
    fields: list[FieldSpec],
    resolve_widget,
    field_classes_resolver,
    *,
    flavor: str,
):
    field_children = []
    for field in fields:
        if flavor == "detail":
            widget_variant = "label"
        elif flavor == "filters":
            widget_variant = filter_variant_for_field(field)
        else:
            widget_variant = "std"
        widget = resolve_widget(field, variant=widget_variant)
        field_children.append(
            LayoutNode(
                methods=f"field__{field.name}",
                classes=field_classes_resolver(field, widget),
                context={
                    "builder_value": {
                        "classes": field_classes_resolver(field, widget),
                        "methods": widget_variant,
                    }
                },
            )
        )

    section_children = [
        LayoutNode(
            methods="label",
            params={"text": title},
            classes="text-subtitle2 text-primary",
        )
    ]

    if flavor == "compact":
        section_children.extend(field_children)
    else:
        section_children.append(
            LayoutNode(
                methods="grid",
                params={"columns": 12},
                classes="w-full gap-3",
                children=field_children,
            )
        )

    return LayoutNode(
        methods="column",
        classes="w-full gap-2",
        children=section_children,
    )
