import enum
import pathlib
import types
import typing as t

import pytest

from nicegui_builder.plugins.pydantic import mapping as mapping_module


class DemoEnum(enum.Enum):
    ALPHA = "alpha"
    BETA = "beta"


class LargeDemoEnum(enum.Enum):
    ONE = "one"
    TWO = "two"
    THREE = "three"
    FOUR = "four"
    FIVE = "five"


class DemoModel(mapping_module.BaseModel):
    name: str


class FakeFieldInfo:
    def __init__(self, annotation, *, attributes=None):
        self.annotation = annotation
        self._attributes = attributes or {}

    def asdict(self):
        return {"attributes": dict(self._attributes)}


def test_extract_options_supports_literal_enum_and_default_empty():
    literal_field = FakeFieldInfo(t.Literal["alpha", "beta"])
    enum_field = FakeFieldInfo(DemoEnum)
    plain_field = FakeFieldInfo(str)

    assert mapping_module.extract_options(literal_field) == ["alpha", "beta"]
    assert mapping_module.extract_options(enum_field) == ["alpha", "beta"]
    assert mapping_module.extract_options(plain_field) == []


def test_select_default_variant_covers_textual_temporal_and_choice_cases():
    long_text = FakeFieldInfo(
        str,
        attributes={"max_length": 240, "title": "Notes", "description": "Long content"},
    )
    description_text = FakeFieldInfo(
        str,
        attributes={"title": "Status", "description": "Comment body"},
    )
    literal_field = FakeFieldInfo(t.Literal["a", "b", "c"])
    enum_field = FakeFieldInfo(DemoEnum)
    date_field = FakeFieldInfo(t.Any)
    datetime_field = FakeFieldInfo(t.Any)

    assert mapping_module.select_default_variant(long_text, "str", "std") == "textarea"
    assert mapping_module.select_default_variant(description_text, "str", "std") == "textarea"
    assert mapping_module.select_default_variant(date_field, "date", "std") == "picker"
    assert mapping_module.select_default_variant(date_field, "time", "std") == "picker"
    assert mapping_module.select_default_variant(datetime_field, "datetime", "std") == "split"
    assert mapping_module.select_default_variant(literal_field, "Literal", "std") == "radio"
    assert mapping_module.select_default_variant(enum_field, "Enum", "std") == "radio"
    assert mapping_module.select_default_variant(FakeFieldInfo(LargeDemoEnum), "Enum", "std") == "std"
    assert mapping_module.select_default_variant(FakeFieldInfo(str), "str", "compact") == "compact"


def test_build_validation_props_covers_text_number_and_empty_cases():
    text_field = FakeFieldInfo(str, attributes={"min_length": 2, "max_length": 10})
    number_field = FakeFieldInfo(int, attributes={"ge": 1, "le": 10, "multiple_of": 2})
    gt_lt_field = FakeFieldInfo(float, attributes={"gt": 1.5, "lt": 5.5})

    assert mapping_module.build_validation_props(text_field, "input") == "minlength=2 maxlength=10 counter"
    assert mapping_module.build_validation_props(text_field, "textarea") == "minlength=2 maxlength=10 counter"
    assert mapping_module.build_validation_props(number_field, "number") == "min=1 max=10 step=2"
    assert mapping_module.build_validation_props(gt_lt_field, "slider") == "min=1.5 max=5.5"
    assert mapping_module.build_validation_props(FakeFieldInfo(str), "radio") == ""


def test_unwrap_optional_annotation_covers_union_and_passthrough():
    assert mapping_module.unwrap_optional_annotation(str | None) is str
    assert mapping_module.unwrap_optional_annotation(t.Optional[int]) is int
    assert mapping_module.unwrap_optional_annotation(str | int) == (str | int)
    assert mapping_module.unwrap_optional_annotation(str) is str


def test_load_widget_map_and_available_types():
    widget_map = mapping_module.load_pydantic_widget_map()
    available_types = mapping_module.available_map_types()

    assert isinstance(widget_map, dict)
    assert "str" in available_types
    assert "datetime" in available_types


def test_resolve_map_type_covers_model_enum_literal_origin_and_fallback(monkeypatch):
    monkeypatch.setattr(mapping_module, "available_map_types", lambda: {"str", "list", "dict", "Enum", "Literal", "int"})

    assert mapping_module.resolve_map_type(t.Literal["a", "b"]) == "Literal"
    assert mapping_module.resolve_map_type(list[str]) == "list"
    assert mapping_module.resolve_map_type(DemoModel) == "dict"
    assert mapping_module.resolve_map_type(DemoEnum) == "Enum"
    assert mapping_module.resolve_map_type(int) == "int"

    class UnknownType:
        pass

    assert mapping_module.resolve_map_type(UnknownType) == "UnknownType"
    assert mapping_module.resolve_map_type(object()).startswith("<object object at ")


def test_get_defaults_from_map_covers_normal_and_error_paths(monkeypatch):
    fake_map = {
        "str|std": {"component": "input"},
        "str|textarea": {"component": "textarea"},
        "int|std": {"component": "number"},
    }
    monkeypatch.setattr(mapping_module, "load_pydantic_widget_map", lambda: fake_map)

    assert mapping_module.get_defaults_from_map("str", "textarea") == {"component": "textarea"}
    assert mapping_module.get_defaults_from_map("str", "missing") == {"component": "input"}
    assert mapping_module.get_defaults_from_map("int", "") == {"component": "number"}

    with pytest.raises(ValueError, match="can't resolve a key"):
        mapping_module.get_defaults_from_map("", "std")

    with pytest.raises(KeyError) as exc_info:
        mapping_module.get_defaults_from_map("float", "std")

    assert "float" in str(exc_info.value)


def test_build_layout_node_merges_widget_and_override_values():
    widget = mapping_module.WidgetSpec(
        component="input",
        params={"label": "Default", "value": "Ada"},
        props="clearable",
        classes="col-span-6",
    )
    field_ctx = {"fieldname": "name", "attributes_title": "Name", "fieldvalue": "Ada"}

    node = mapping_module.build_layout_node(
        field_ctx,
        widget,
        {
            "params": {"label": "Display name"},
            "props": "outlined",
            "classes": "w-full",
            "ref": "field:name",
        },
    )

    assert node.methods == "input"
    assert node.params == {"label": "Display name", "value": "Ada"}
    assert node.props == "clearable outlined"
    assert node.classes == "col-span-6 w-full"
    assert node.ref == "field:name"
