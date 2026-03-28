import typing as t

from pydantic import BaseModel

from nicegui_builder.core.models import FieldSpec, LayoutNode, WidgetSpec

from .inspect import build_field_context
from .layout import (
    build_section_node,
    default_field_classes,
    filters_field_classes,
    group_fields_by_section,
)
from .mapping import (
    extract_options,
    resolve_map_type,
    resolve_widget_spec,
)
from .resolve import resolve_field_node as resolve_pydantic_field_node


def _extract_constraints(field_info) -> dict:
    constraints = {}
    supported_keys = {
        "min_length",
        "max_length",
        "pattern",
        "gt",
        "ge",
        "lt",
        "le",
        "multiple_of",
    }

    for metadata in field_info.metadata:
        for key in supported_keys:
            value = getattr(metadata, key, None)
            if value is not None:
                constraints[key] = value

    return constraints
def _is_pydantic_model_type(annotation) -> bool:
    try:
        return isinstance(annotation, type) and issubclass(annotation, BaseModel)
    except TypeError:
        return False


def _is_collection_annotation(annotation) -> bool:
    origin = t.get_origin(annotation)
    return origin in {list, tuple, set, dict}


class PydanticPlugin:
    name = "pydantic"

    def supports(self, source) -> bool:
        if isinstance(source, type):
            return issubclass(source, BaseModel)
        return isinstance(source, BaseModel)

    def inspect_fields(self, source) -> list[FieldSpec]:
        model_class = source if isinstance(source, type) else source.__class__
        fields: list[FieldSpec] = []

        for fieldname, field_info in model_class.model_fields.items():
            metadata = field_info.asdict()
            attributes = metadata.get("attributes", {})
            map_type = resolve_map_type(field_info.annotation)
            nullable = field_info.default is None
            choices: list[object] = []
            annotation = field_info.annotation
            is_nested_model = _is_pydantic_model_type(annotation)
            is_collection = _is_collection_annotation(annotation)
            is_structured = map_type in {"dict", "list", "set", "tuple", "Json"} or is_nested_model
            section = "structured" if is_structured else "general"

            if is_nested_model:
                group_label = "Nested models"
            elif is_collection:
                group_label = "Collections"
            elif is_structured:
                group_label = "Structured data"
            else:
                group_label = "General"

            if map_type in {"Literal", "Enum"}:
                choices = extract_options(field_info)

            if annotation is bool:
                filter_variant = "select"
            elif choices or annotation in {int, float}:
                filter_variant = "std"
            else:
                filter_variant = "search"

            fields.append(
                FieldSpec(
                    name=fieldname,
                    python_type=field_info.annotation,
                    required=field_info.is_required(),
                    nullable=nullable,
                    default=None if field_info.is_required() else field_info.default,
                    title=attributes.get("title") or fieldname,
                    description=attributes.get("description") or "",
                    examples=list(attributes.get("examples") or []),
                    choices=choices,
                    constraints=_extract_constraints(field_info),
                    source_meta={
                        "field_info": field_info,
                        "is_nested_model": is_nested_model,
                        "is_collection": is_collection,
                        "is_structured": is_structured,
                        "section": section,
                        "group_label": group_label,
                        "filter_variant": filter_variant,
                    },
                )
            )

        return fields

    def build_layout(self, source, flavor: str = ""):
        title = source.__name__ if isinstance(source, type) else source.__class__.__name__
        fields = self.inspect_fields(source)
        flavor = flavor or ""
        if flavor == "compact":
            field_classes_resolver = lambda _field, _widget: "w-full"
        elif flavor == "detail":
            field_classes_resolver = lambda _field, _widget: "col-span-12"
        elif flavor == "filters":
            field_classes_resolver = filters_field_classes
        elif flavor == "actionable":
            field_classes_resolver = default_field_classes
        else:
            field_classes_resolver = default_field_classes
        children = [
            LayoutNode(
                methods="label",
                params={"text": title},
                classes="text-lg",
            )
        ]

        for section_title, section_fields in group_fields_by_section(fields):
            children.append(
                build_section_node(
                    section_title,
                    section_fields,
                    self.resolve_widget,
                    field_classes_resolver,
                    flavor=flavor,
                )
            )

        if flavor == "actionable":
            children.extend(
                [
                    LayoutNode(methods="separator"),
                    LayoutNode(
                        methods="column",
                        ref="form:errors",
                        classes="w-full gap-2",
                    ),
                    LayoutNode(
                        methods="row",
                        classes="w-full items-center justify-between gap-2",
                        children=[
                            LayoutNode(
                                methods="row",
                                ref="form:status",
                                classes="items-center gap-2",
                            ),
                            LayoutNode(
                                methods="row",
                                ref="form:actions",
                                classes="items-center justify-end gap-2",
                            ),
                        ],
                    ),
                ]
            )

        return [
            LayoutNode(
                methods="card.tight",
                classes="w-full p-4 gap-3",
                children=children,
            )
        ]

    def resolve_widget(self, spec: FieldSpec, variant: str = "std") -> WidgetSpec:
        field_info = spec.source_meta["field_info"]
        widget, _ = resolve_widget_spec(field_info, spec.python_type, variant)
        return widget

    def build_field_context(self, model_class, model_instance, fieldname: str) -> dict:
        return build_field_context(model_class, model_instance, fieldname)

    def resolve_field_node(
        self, model_class, model_instance, fieldname: str, value: dict | None
    ) -> dict:
        return resolve_pydantic_field_node(model_class, model_instance, fieldname, value)

    def render_form(self, source, flavor: str = ""):
        return None
