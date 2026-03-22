import typing as t

from pydantic import BaseModel

from nicegui_builder.core.models import FieldSpec, WidgetSpec

from .inspect import build_field_context
from .mapping import (
    build_validation_props,
    extract_options,
    get_defaults_from_map,
    resolve_map_type,
    select_default_variant,
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


def _default_field_classes(spec: FieldSpec, widget: WidgetSpec) -> str:
    if spec.source_meta.get("section") == "structured":
        return "col-span-12"

    if widget.component in {"textarea", "radio", "checkbox", "switch"}:
        return "col-span-12"

    if spec.constraints.get("max_length", 0) and spec.constraints["max_length"] > 120:
        return "col-span-12"

    if widget.component in {"input", "number", "select", "date", "time", "color_input"}:
        return "col-span-6"

    return "col-span-12"


def _compact_field_classes(spec: FieldSpec, widget: WidgetSpec) -> str:
    return "w-full"


def _detail_field_classes(spec: FieldSpec, widget: WidgetSpec) -> str:
    return "col-span-12"


def _filters_field_classes(spec: FieldSpec, widget: WidgetSpec) -> str:
    if widget.component in {"textarea", "radio"}:
        return "col-span-12"

    if widget.component in {"input", "number", "select", "date", "time"}:
        return "col-span-6"

    return "col-span-12"


def _actionable_field_classes(spec: FieldSpec, widget: WidgetSpec) -> str:
    return _default_field_classes(spec, widget)


def _filter_variant_for_field(spec: FieldSpec) -> str:
    if spec.python_type is bool:
        return "select"

    if spec.choices:
        return "std"

    if spec.python_type in {int, float}:
        return "std"

    return "search"


def _is_pydantic_model_type(annotation) -> bool:
    try:
        return isinstance(annotation, type) and issubclass(annotation, BaseModel)
    except TypeError:
        return False


def _is_collection_annotation(annotation) -> bool:
    origin = t.get_origin(annotation)
    return origin in {list, tuple, set, dict}


def _section_for_field(spec: FieldSpec) -> str:
    if spec.source_meta.get("is_nested_model"):
        return "Nested models"
    if spec.source_meta.get("is_collection"):
        return "Collections"
    if spec.source_meta.get("is_structured"):
        return "Structured data"
    return "General"


def _group_fields_by_section(fields: list[FieldSpec]) -> list[tuple[str, list[FieldSpec]]]:
    grouped: dict[str, list[FieldSpec]] = {}
    for field in fields:
        grouped.setdefault(_section_for_field(field), []).append(field)

    ordered_sections = ["General", "Nested models", "Collections", "Structured data"]
    results: list[tuple[str, list[FieldSpec]]] = []

    for section in ordered_sections:
        section_fields = grouped.pop(section, [])
        if section_fields:
            results.append((section, section_fields))

    for section, section_fields in grouped.items():
        results.append((section, section_fields))

    return results


def _build_section_node(
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
            widget_variant = _filter_variant_for_field(field)
        else:
            widget_variant = "std"
        widget = resolve_widget(field, variant=widget_variant)
        field_children.append(
            {
                f"field__{field.name}": {
                    "classes": field_classes_resolver(field, widget),
                    "methods": widget_variant,
                }
            }
        )

    section_children = [
        {
            "label": {
                "params": {"text": title},
                "classes": "text-subtitle2 text-primary",
            }
        }
    ]

    if flavor == "compact":
        section_children.extend(field_children)
    else:
        section_children.append(
            {
                "grid": {
                    "params": {"columns": 12},
                    "classes": "w-full gap-3",
                    "children": field_children,
                }
            }
        )

    return {
        "column": {
            "classes": "w-full gap-2",
            "children": section_children,
        }
    }


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

            if map_type in {"Literal", "Enum"}:
                choices = extract_options(field_info)

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
                        "section": "structured" if is_structured else "general",
                    },
                )
            )

        return fields

    def build_layout(self, source, flavor: str = ""):
        title = source.__name__ if isinstance(source, type) else source.__class__.__name__
        fields = self.inspect_fields(source)
        flavor = flavor or ""
        if flavor == "compact":
            field_classes_resolver = _compact_field_classes
        elif flavor == "detail":
            field_classes_resolver = _detail_field_classes
        elif flavor == "filters":
            field_classes_resolver = _filters_field_classes
        elif flavor == "actionable":
            field_classes_resolver = _actionable_field_classes
        else:
            field_classes_resolver = _default_field_classes
        children = [
            {
                "label": {
                    "params": {
                        "text": title,
                    },
                    "classes": "text-lg",
                }
            }
        ]

        for section_title, section_fields in _group_fields_by_section(fields):
            children.append(
                _build_section_node(
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
                    {"separator": None},
                    {
                        "column": {
                            "ref": "form:errors",
                            "classes": "w-full gap-2",
                        }
                    },
                    {
                        "row": {
                            "classes": "w-full items-center justify-between gap-2",
                            "children": [
                                {
                                    "row": {
                                        "ref": "form:status",
                                        "classes": "items-center gap-2",
                                    }
                                },
                                {
                                    "row": {
                                        "ref": "form:actions",
                                        "classes": "items-center justify-end gap-2",
                                    }
                                },
                            ],
                        }
                    },
                ]
            )

        return [
            {
                "card.tight": {
                    "classes": "w-full p-4 gap-3",
                    "children": children,
                }
            }
        ]

    def resolve_widget(self, spec: FieldSpec, variant: str = "std") -> WidgetSpec:
        field_info = spec.source_meta["field_info"]
        map_type = resolve_map_type(spec.python_type)
        effective_variant = select_default_variant(field_info, map_type, variant)
        default_info = get_defaults_from_map(map_type, effective_variant)
        methods = default_info.get("methods")
        validation_props = build_validation_props(field_info, methods)
        props = " ".join(
            part for part in [default_info.get("props", ""), validation_props] if part
        )

        return WidgetSpec(
            component=methods,
            variant=effective_variant,
            params=dict(default_info.get("params", {})),
            props=props,
            classes=default_info.get("classes", ""),
        )

    def build_field_context(self, model_class, model_instance, fieldname: str) -> dict:
        return build_field_context(model_class, model_instance, fieldname)

    def resolve_field_node(
        self, model_class, model_instance, fieldname: str, value: dict | None
    ) -> dict:
        return resolve_pydantic_field_node(model_class, model_instance, fieldname, value)

    def render_form(self, source, flavor: str = ""):
        return None
