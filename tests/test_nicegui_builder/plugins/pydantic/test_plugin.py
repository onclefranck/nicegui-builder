from pydantic import BaseModel

from nicegui_builder.plugins.pydantic import pydantic_plugin
from nicegui_builder.plugins.pydantic.layout import (
    build_section_node,
    default_field_classes,
    filters_field_classes,
    group_fields_by_section,
)
import nicegui_builder.plugins.pydantic.plugin as plugin_module
from nicegui_builder.core.models import FieldSpec, LayoutNode, WidgetSpec

from .support import (
    DemoDateTimeModel,
    DemoModel,
    DemoStructuredModel,
    extract_section,
    extract_section_fields,
)


def test_pydantic_plugin_resolves_literal_to_radio():
    fields = pydantic_plugin.inspect_fields(DemoModel)
    role_field = next(field for field in fields if field.name == "role")

    widget = pydantic_plugin.resolve_widget(role_field)

    assert widget.component == "radio"
    assert widget.variant == "radio"


def test_pydantic_plugin_builds_default_layout():
    layout = pydantic_plugin.build_layout(DemoModel)

    assert layout[0].methods == "card.tight"
    assert layout[0].children[0].methods == "label"
    assert layout[0].children[0].params["text"] == "DemoModel"
    general_section = extract_section(layout, "General")
    by_key = extract_section_fields(general_section)

    assert by_key["field__name"].classes == "col-span-6"
    assert by_key["field__age"].classes == "col-span-6"
    assert by_key["field__active"].classes == "col-span-12"
    assert by_key["field__role"].classes == "col-span-12"


def test_pydantic_plugin_builds_compact_layout():
    layout = pydantic_plugin.build_layout(DemoModel, flavor="compact")

    children = layout[0].children
    general_section = next(child for child in children[1:] if child.methods == "column")
    by_key = {
        child.methods: child
        for child in general_section.children[1:]
    }
    assert by_key["field__name"].classes == "w-full"
    assert by_key["field__role"].classes == "w-full"


def test_pydantic_plugin_builds_detail_layout():
    layout = pydantic_plugin.build_layout(DemoModel, flavor="detail")

    general_section = extract_section(layout, "General")
    by_key = extract_section_fields(general_section)

    assert by_key["field__name"].context["builder_value"]["methods"] == "label"
    assert by_key["field__age"].context["builder_value"]["methods"] == "label"
    assert by_key["field__active"].context["builder_value"]["methods"] == "label"
    assert by_key["field__role"].context["builder_value"]["methods"] == "label"
    assert by_key["field__name"].classes == "col-span-12"


def test_pydantic_plugin_builds_filters_layout():
    layout = pydantic_plugin.build_layout(DemoModel, flavor="filters")

    general_section = extract_section(layout, "General")
    by_key = extract_section_fields(general_section)

    assert by_key["field__name"].context["builder_value"]["methods"] == "search"
    assert by_key["field__age"].context["builder_value"]["methods"] == "std"
    assert by_key["field__active"].context["builder_value"]["methods"] == "select"
    assert by_key["field__role"].context["builder_value"]["methods"] == "std"
    assert by_key["field__name"].classes == "col-span-6"
    assert by_key["field__active"].classes == "col-span-6"


def test_pydantic_plugin_builds_actionable_layout():
    layout = pydantic_plugin.build_layout(DemoModel, flavor="actionable")

    children = layout[0].children
    assert children[1].methods == "column"
    assert children[2].methods == "separator"
    assert children[3].methods == "column"
    assert children[3].ref == "form:errors"
    assert children[4].methods == "row"
    action_row_children = children[4].children
    assert action_row_children[0].ref == "form:status"
    assert action_row_children[1].ref == "form:actions"


def test_pydantic_plugin_builds_structured_sections():
    layout = pydantic_plugin.build_layout(DemoStructuredModel)

    general_fields = extract_section_fields(extract_section(layout, "General"))
    nested_fields = extract_section_fields(extract_section(layout, "Nested models"))
    collection_fields = extract_section_fields(extract_section(layout, "Collections"))

    assert "field__name" in general_fields
    assert nested_fields["field__address"].classes == "col-span-12"
    assert collection_fields["field__tags"].classes == "col-span-12"


def test_pydantic_plugin_resolves_nested_models_and_collections_as_structured_widgets():
    fields = pydantic_plugin.inspect_fields(DemoStructuredModel)
    by_name = {field.name: field for field in fields}

    address_widget = pydantic_plugin.resolve_widget(by_name["address"])
    tags_widget = pydantic_plugin.resolve_widget(by_name["tags"])

    assert address_widget.component == "textarea"
    assert "font-mono" in address_widget.classes
    assert tags_widget.component == "textarea"
    assert by_name["address"].source_meta["group_label"] == "Nested models"
    assert by_name["tags"].source_meta["group_label"] == "Collections"
    assert by_name["tags"].source_meta["filter_variant"] == "search"


def test_pydantic_plugin_resolves_datetime_to_split_widget():
    field = next(
        field for field in pydantic_plugin.inspect_fields(DemoDateTimeModel) if field.name == "starts_at"
    )

    widget = pydantic_plugin.resolve_widget(field)

    assert widget.component == "datetime_input"
    assert widget.variant == "split"
    assert widget.params["container"]["methods"] == "row"
    assert field.source_meta["filter_variant"] == "search"


def test_pydantic_plugin_supports_model_types_and_instances_but_not_other_values():
    assert pydantic_plugin.supports(DemoModel) is True
    assert pydantic_plugin.supports(DemoModel(name="Ada", age=12, active=True, role="user")) is True
    assert pydantic_plugin.supports("not-a-model") is False


def test_pydantic_plugin_can_group_unknown_sections_after_known_ones():
    general = FieldSpec(name="general", python_type=str, source_meta={})
    mystery = FieldSpec(name="mystery", python_type=str, source_meta={"group_label": "mystery"})
    structured = FieldSpec(name="payload", python_type=dict, source_meta={"is_structured": True})

    grouped = group_fields_by_section([mystery, general, structured])

    assert [section for section, _ in grouped] == ["General", "Structured data", "mystery"]


def test_pydantic_plugin_field_class_helpers_cover_remaining_variants():
    plain = FieldSpec(name="name", python_type=str, source_meta={}, constraints={})
    long_text = FieldSpec(name="bio", python_type=str, source_meta={}, constraints={"max_length": 200})
    structured = FieldSpec(name="payload", python_type=dict, source_meta={"section": "structured"})

    assert default_field_classes(plain, WidgetSpec(component="color_input")) == "col-span-6"
    assert default_field_classes(long_text, WidgetSpec(component="input")) == "col-span-12"
    assert default_field_classes(structured, WidgetSpec(component="input")) == "col-span-12"
    assert default_field_classes(plain, WidgetSpec(component="slider")) == "col-span-12"
    assert filters_field_classes(plain, WidgetSpec(component="checkbox")) == "col-span-12"


def test_pydantic_plugin_build_section_node_returns_column_wrapper():
    field = FieldSpec(name="nickname", python_type=str)

    node = build_section_node(
        "General",
        [field],
        lambda spec, variant="std": WidgetSpec(component="input"),
        lambda spec, widget: "col-span-6",
        flavor="std",
    )

    assert isinstance(node, LayoutNode)
    assert node.methods == "column"
    assert node.classes == "w-full gap-2"
    assert node.children[0].methods == "label"
    assert node.children[0].classes == "text-subtitle2 text-primary"


def test_pydantic_plugin_build_field_context_and_resolve_field_node_delegate(monkeypatch):
    calls = {}

    def fake_build_field_context(model_class, model_instance, fieldname):
        calls["context"] = (model_class, model_instance, fieldname)
        return {"field": fieldname}

    def fake_resolve_field_node(model_class, model_instance, fieldname, value):
        calls["node"] = (model_class, model_instance, fieldname, value)
        return {"node": fieldname}

    monkeypatch.setattr("nicegui_builder.plugins.pydantic.plugin.build_field_context", fake_build_field_context)
    monkeypatch.setattr(
        "nicegui_builder.plugins.pydantic.plugin.resolve_pydantic_field_node",
        fake_resolve_field_node,
    )

    instance = DemoModel(name="Ada", age=12, active=True, role="user")

    assert pydantic_plugin.build_field_context(DemoModel, instance, "name") == {"field": "name"}
    assert pydantic_plugin.resolve_field_node(DemoModel, instance, "name", {"classes": "w-full"}) == {
        "node": "name"
    }
    assert calls["context"] == (DemoModel, instance, "name")
    assert calls["node"] == (DemoModel, instance, "name", {"classes": "w-full"})


def test_pydantic_plugin_render_form_returns_none():
    assert pydantic_plugin.render_form(DemoModel) is None


def test_is_pydantic_model_type_handles_typeerror_branch():
    from nicegui_builder.plugins.pydantic.plugin import _is_pydantic_model_type

    original_base_model = plugin_module.BaseModel
    plugin_module.BaseModel = 123  # force issubclass(..., BaseModel) to raise TypeError
    try:
        assert _is_pydantic_model_type(type("WeirdBase", (), {})) is False
    finally:
        plugin_module.BaseModel = original_base_model
