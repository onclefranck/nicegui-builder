import importlib
from types import SimpleNamespace

import pytest

builder_module = importlib.import_module("nicegui_builder.builder")
from nicegui_builder.builder import builder, register, resolve_context_value
from nicegui_builder.core.context import builder_ctx
from nicegui_builder.core.models import LayoutNode


class FakeComponent:
    def __init__(self, method_name, **params):
        self.method_name = method_name
        self.params = params
        self.children = []
        self.class_calls = []
        self.props_calls = []
        self.event_calls = []
        self.cleared = False

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

    def on_click(self, callback):
        self.event_calls.append(("click", callback))
        return self

    def on(self, event, callback):
        self.event_calls.append((event, callback))
        return self

    def clear(self):
        self.cleared = True
        self.children = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeUI:
    def label(self, **params):
        return FakeComponent("label", **params)

    def card(self, **params):
        return FakeComponent("card", **params)

    def row(self, **params):
        return FakeComponent("row", **params)


def test_resolve_context_value_interpolates_tokens_and_preserves_single_token_type():
    ctx = {"name": "Ada", "enabled": True, "items": [1, 2]}

    assert resolve_context_value("Hello {{ name }}", ctx) == "Hello Ada"
    assert resolve_context_value("{{ enabled }}", ctx) is True
    assert resolve_context_value("{{ items }}", ctx) == [1, 2]


def test_resolve_context_value_supports_paths_filters_and_escaped_tokens():
    ctx = {
        "entry": SimpleNamespace(name="Ada"),
        "row": {"score": 7},
    }
    builder_module.ensure_builder_runtime(ctx, filters={"upper": str.upper, "bracket": lambda value: f"[{value}]"})

    assert resolve_context_value("{{ entry.name | upper | bracket }}", ctx) == "[ADA]"
    assert resolve_context_value("score={{ row['score'] }}", ctx) == "score=7"
    assert resolve_context_value(r"\{{ literal }}", ctx) == "{{ literal }}"


def test_resolve_context_value_rejects_unknown_names_and_filters():
    with pytest.raises(ValueError, match="unknown context name 'missing'"):
        resolve_context_value("{{ missing }}", {})

    ctx = {"name": "Ada"}
    builder_module.ensure_builder_runtime(ctx, filters={})
    with pytest.raises(ValueError, match="unknown filter 'upper'"):
        resolve_context_value("{{ name | upper }}", ctx)


def test_builder_returns_root_component_and_applies_registered_expansion(monkeypatch):
    fake_ui = FakeUI()
    monkeypatch.setattr(builder_module, "ui", fake_ui)
    builder_module.builder_expansion_registry.clear()

    def resolve_field(field_name, value):
        return LayoutNode(
            methods="label",
            params={"text": f"Resolved {field_name}"},
            classes="resolved-field",
            props="outlined",
            ref="field:name",
            on={"click": "save"},
        )

    register("field", resolve_field)
    handler = lambda event=None: None

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
            ],
            handlers={"save": handler},
        )
    finally:
        builder_ctx.reset(token)
        builder_module.builder_expansion_registry.clear()

    assert root.method_name == "label"
    assert root.params["text"] == "Resolved name"
    assert root.class_calls == ["resolved-field"]
    assert root.props_calls == ["outlined"]
    assert root.component_refs["field:name"] is root
    assert root.event_calls == [("click", handler)]


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


def test_builder_normalizes_layout_entries_to_layout_nodes():
    node = builder_module._normalize_layout_entry(
        {"label": {"params": {"text": "Hello"}}},
        {},
    )

    assert isinstance(node, LayoutNode)
    assert node.methods == "label"
    assert node.params == {"text": "Hello"}


def test_builder_binds_generic_events_and_rejects_unknown_handlers(monkeypatch):
    fake_ui = FakeUI()
    monkeypatch.setattr(builder_module, "ui", fake_ui)

    handler = lambda event=None: None
    root = builder(
        [
            {"label": {"on": {"keydown.enter": "submit"}}},
        ],
        handlers={"submit": handler},
    )

    assert root.event_calls == [("keydown.enter", handler)]

    with pytest.raises(ValueError, match="unknown handler 'missing'"):
        builder([{"label": {"on": {"click": "missing"}}}], handlers={})


def test_builder_repeats_children_with_scoped_values_handlers_and_keyed_refs(monkeypatch):
    fake_ui = FakeUI()
    monkeypatch.setattr(builder_module, "ui", fake_ui)
    seen = []
    segments = [
        SimpleNamespace(segment_id="a", label="Alpha"),
        SimpleNamespace(segment_id="b", label="Beta"),
    ]

    root = builder(
        [
            {
                "row": {
                    "children": [
                        {
                            "repeat": {
                                "in": "{{ segments }}",
                                "as": "seg",
                                "key": "{{ seg.segment_id }}",
                                "children": [
                                    {
                                        "label": {
                                            "ref": "segment_label",
                                            "params": {"text": "#{{ $index }} {{ seg.label }}"},
                                            "on": {"click": "choose"},
                                        }
                                    }
                                ],
                            }
                        }
                    ]
                }
            }
        ],
        context={"segments": segments},
        handlers={"choose": lambda item, event=None: seen.append((item.segment_id, event))},
    )

    labels = root.component_refs["segment_label"]
    assert labels["a"].params["text"] == "#0 Alpha"
    assert labels["b"].params["text"] == "#1 Beta"

    labels["a"].event_calls[0][1]("event-a")
    labels["b"].event_calls[0][1]("event-b")
    assert seen == [("a", "event-a"), ("b", "event-b")]


def test_builder_rejects_refs_inside_repeat_without_key(monkeypatch):
    fake_ui = FakeUI()
    monkeypatch.setattr(builder_module, "ui", fake_ui)

    with pytest.raises(ValueError, match="inside repeat requires a key"):
        builder(
            [
                {
                    "repeat": {
                        "in": "{{ values }}",
                        "as": "value",
                        "children": [
                            {"label": {"ref": "value_label"}},
                        ],
                    },
                },
            ],
            context={"values": [1]},
        )


def test_builder_rebuilds_container_template_with_new_context(monkeypatch):
    fake_ui = FakeUI()
    monkeypatch.setattr(builder_module, "ui", fake_ui)

    root = builder(
        [
            {
                "row": {
                    "ref": "rows",
                    "children": [
                        {
                            "repeat": {
                                "in": "{{ values }}",
                                "as": "value",
                                "key": "{{ value }}",
                                "children": [
                                    {"label": {"ref": "value_label", "params": {"text": "{{ value }}"}}},
                                ],
                            }
                        }
                    ],
                }
            }
        ],
        context={"values": [1, 2]},
    )

    assert sorted(root.component_refs["value_label"]) == [1, 2]

    root.rebuild("rows", context={"values": [3]})

    assert root.component_refs["rows"].cleared is True
    assert sorted(root.component_refs["value_label"]) == [3]
