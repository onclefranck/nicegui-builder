from nicegui_builder.plugins.pydantic import pydantic_plugin

from .support import DemoModel, DemoStructuredModel


def test_pydantic_plugin_inspects_fields():
    fields = pydantic_plugin.inspect_fields(DemoModel)
    by_name = {field.name: field for field in fields}

    assert by_name["name"].title == "Name"
    assert by_name["name"].constraints["min_length"] == 2
    assert by_name["age"].constraints["ge"] == 0
    assert by_name["active"].python_type is bool
    assert by_name["role"].choices == ["admin", "user"]


def test_pydantic_plugin_inspects_structured_fields():
    fields = pydantic_plugin.inspect_fields(DemoStructuredModel)
    by_name = {field.name: field for field in fields}

    assert by_name["address"].source_meta["is_nested_model"] is True
    assert by_name["address"].source_meta["is_structured"] is True
    assert by_name["tags"].source_meta["is_collection"] is True
    assert by_name["tags"].source_meta["is_structured"] is True
