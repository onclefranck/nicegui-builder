import importlib
import pytest

builder_module = importlib.import_module("nicegui_builder.builder")
from nicegui_builder.builder import builder, register, resolve_context_value
from nicegui_builder.core.context import builder_ctx


def _format_greeting(**ctx):
    return f"Hello {ctx['name']}"


class FakeComponent:
    def __init__(self, method_name, **params):
        self.method_name = method_name
        self.params = params
        self.children = []
        self.class_calls = []
        self.props_calls = []

    def classes(self, value):
        self.class_calls.append(value)
        return self

    def props(self, value):
        self.props_calls.append(value)
        return self

    def tight(self, **params):
        child = FakeComponent("tight", **params)
        self.children.append(child)
        return child

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeUI:
    def label(self, **params):
        return FakeComponent("label", **params)

    def card(self, **params):
        return FakeComponent("card", **params)


def test_resolve_context_value_supports_literal_formatting():
    assert resolve_context_value("_Hello {name}", {"name": "Ada"}) == "Hello Ada"


def test_resolve_context_value_supports_import_callbacks():
    value = resolve_context_value(f"${__name__}:_format_greeting", {"name": "Ada"})

    assert value == "Hello Ada"


def test_builder_returns_root_component_and_applies_registered_expansion(monkeypatch):
    fake_ui = FakeUI()
    monkeypatch.setattr(builder_module, "ui", fake_ui)
    builder_module.builder_expansion_registry.clear()

    def resolve_field(field_name, value):
        return {
            "methods": "label",
            "params": {"text": f"Resolved {field_name}"},
            "classes": "resolved-field",
            "props": "outlined",
            "ref": "field:name",
        }

    register("field", resolve_field)

    token = builder_ctx.set({"name": "Ada"})
    try:
        root = builder(
            [
                {
                    "card.tight": {
                        "children": [
                            {"field__name": {}},
                        ]
                    }
                }
            ]
        )
    finally:
        builder_ctx.reset(token)
        builder_module.builder_expansion_registry.clear()

    assert root.method_name == "label"
    assert root.params["text"] == "Resolved name"
    assert root.class_calls == ["resolved-field"]
    assert root.props_calls == ["outlined"]
    assert root.component_refs["field:name"] is root


def test_builder_collects_explicit_component_refs_and_rejects_duplicates(monkeypatch):
    fake_ui = FakeUI()
    monkeypatch.setattr(builder_module, "ui", fake_ui)

    root = builder(
        [
            {"card": {"ref": "panel"}},
        ]
    )

    assert root.component_refs["panel"] is root

    with pytest.raises(ValueError, match="duplicate component ref"):
        builder(
            [
                {"card": {"ref": "dup"}},
                {"label": {"ref": "dup", "params": {"text": "Hello"}}},
            ]
        )
