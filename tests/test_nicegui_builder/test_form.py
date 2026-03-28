import importlib
import types
from pathlib import Path

import pytest

form_module = importlib.import_module("nicegui_builder.form")
from nicegui_builder.core.models import FieldSpec, LayoutNode, ResolvedFieldNode


class FakePlugin:
    name = "fake"

    def __init__(self):
        self.field_specs = [FieldSpec(name="name", python_type=str)]

    def inspect_fields(self, source):
        return self.field_specs

    def resolve_field_node(self, model_class, model_instance, fieldname, value):
        return ResolvedFieldNode(
            node=LayoutNode(methods="input", params={"label": fieldname}),
            field_ctx={"fieldname": fieldname},
        )

    def build_layout(self, source, flavor=""):
        return [{"label": {"params": {"text": "fallback layout"}}}]


def test_resolve_layout_from_source_loads_adjacent_yaml(monkeypatch):
    tmp_path = Path("tests") / "_tmp_form_layout"
    tmp_path.mkdir(exist_ok=True)
    module_file = tmp_path / "demo_source.py"
    layout_file = tmp_path / "Demo.yaml"

    try:
        module_file.write_text("class Demo:\n    pass\n", encoding="utf-8")
        layout_file.write_text("- label:\n    params:\n      text: Loaded from yaml\n", encoding="utf-8")

        demo_class = type("Demo", (), {})
        demo_class.__module__ = "demo_source"

        fake_module = types.SimpleNamespace(__file__=str(module_file))
        monkeypatch.setattr(form_module, "import_module", lambda name: fake_module)

        layout = form_module._resolve_layout_from_source(demo_class, "")
    finally:
        if layout_file.exists():
            layout_file.unlink()
        if module_file.exists():
            module_file.unlink()
        if tmp_path.exists():
            tmp_path.rmdir()

    assert layout[0]["label"]["params"]["text"] == "Loaded from yaml"


def test_form_uses_plugin_build_layout_when_yaml_is_missing(monkeypatch):
    fake_plugin = FakePlugin()
    calls = {}

    monkeypatch.setattr(form_module.plugin_registry, "resolve", lambda source: fake_plugin)
    monkeypatch.setattr(form_module, "_resolve_layout_from_source", lambda source, flavor: (_ for _ in ()).throw(FileNotFoundError()))

    def fake_builder(layout):
        calls["layout"] = layout
        return object()

    monkeypatch.setattr(form_module, "builder", fake_builder)

    handle = form_module.form(type("Demo", (), {}))

    assert handle.spec.plugin_name == "fake"
    assert calls["layout"][0]["label"]["params"]["text"] == "fallback layout"


def test_form_returns_plugin_rendered_form_when_available(monkeypatch):
    fake_handle = object()

    class RenderPlugin(FakePlugin):
        def render_form(self, source, flavor=""):
            return fake_handle

    monkeypatch.setattr(form_module.plugin_registry, "resolve", lambda source: RenderPlugin())

    assert form_module.form(type("Demo", (), {})) is fake_handle


def test_form_rejects_plugins_without_form_capabilities(monkeypatch):
    plugin = types.SimpleNamespace(name="broken")
    monkeypatch.setattr(form_module.plugin_registry, "resolve", lambda source: plugin)

    with pytest.raises(TypeError):
        form_module.form(type("Demo", (), {}))


def test_resolve_plugin_field_updates_builder_context_and_assigns_field_ref():
    class FieldPlugin(FakePlugin):
        def resolve_field_node(self, model_class, model_instance, fieldname, value):
            assert model_class.__name__ == "Demo"
            assert model_instance == "instance"
            assert fieldname == "name"
            assert value == {"classes": "w-full"}
            return ResolvedFieldNode(
                node=LayoutNode(methods="input", params={"label": "Name"}),
                field_ctx={"title": "Name"},
            )

    ctx = {
        "plugin": FieldPlugin(),
        "source_class": type("Demo", (), {}),
        "source_instance": "instance",
    }
    token = form_module.builder_ctx.set(ctx)
    try:
        node = form_module._resolve_plugin_field("field__name", {"classes": "w-full"})
        current = form_module.builder_ctx.get()
    finally:
        form_module.builder_ctx.reset(token)

    assert node.ref == "field:name"
    assert current["fieldname"] == "name"
    assert current["title"] == "Name"


def test_form_reraises_missing_layout_when_plugin_cannot_build_one(monkeypatch):
    plugin = types.SimpleNamespace(
        name="fake",
        inspect_fields=lambda source: [FieldSpec(name="name", python_type=str)],
        resolve_field_node=lambda model_class, model_instance, fieldname, value: ResolvedFieldNode(
            node=LayoutNode(methods="input", params={"label": fieldname}),
            field_ctx={"fieldname": fieldname},
        ),
    )
    monkeypatch.setattr(form_module.plugin_registry, "resolve", lambda source: plugin)
    monkeypatch.setattr(
        form_module,
        "_resolve_layout_from_source",
        lambda source, flavor: (_ for _ in ()).throw(FileNotFoundError()),
    )

    with pytest.raises(FileNotFoundError):
        form_module.form(type("Demo", (), {}))


def test_form_uses_source_instance_when_building_handle(monkeypatch):
    fake_plugin = FakePlugin()
    calls = {}

    class Demo:
        pass

    instance = Demo()

    monkeypatch.setattr(form_module.plugin_registry, "resolve", lambda source: fake_plugin)
    monkeypatch.setattr(
        form_module,
        "_resolve_layout_from_source",
        lambda source, flavor: [{"label": {"params": {"text": "loaded"}}}],
    )
    monkeypatch.setattr(form_module, "builder", lambda layout: object())

    original_form_handle = form_module.FormHandle

    class RecordingFormHandle(original_form_handle):
        def __init__(self, *args, **kwargs):
            calls["kwargs"] = kwargs
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(form_module, "FormHandle", RecordingFormHandle)

    handle = form_module.form(instance)

    assert handle.source_instance is instance
    assert calls["kwargs"]["source_instance"] is instance


def test_form_exposes_custom_component_refs_and_split_datetime_composites(monkeypatch):
    class DateTimePlugin(FakePlugin):
        def __init__(self):
            self.field_specs = [FieldSpec(name="starts_at", python_type=object)]

    class DummyComponent:
        def __init__(self):
            self.component_refs = {}

    class FakeDateTimeInput:
        def __init__(self):
            self.date = object()
            self.time = object()
            self.date_ref = "starts_at:date"
            self.time_ref = "starts_at:time"

    monkeypatch.setattr(form_module.plugin_registry, "resolve", lambda source: DateTimePlugin())
    monkeypatch.setattr(
        form_module,
        "_resolve_layout_from_source",
        lambda source, flavor: [{"field__starts_at": {"ref": "starts_at"}}],
    )

    def fake_builder(layout):
        ctx = form_module.builder_ctx.get()
        refs = form_module.component_refs(ctx)
        ctx["_field_refs"]["starts_at"] = "starts_at"
        refs["starts_at"] = FakeDateTimeInput()
        return DummyComponent()

    monkeypatch.setattr(form_module, "builder", fake_builder)

    handle = form_module.form(type("Demo", (), {}))

    assert handle.component_refs["starts_at:date"] is handle.component_refs["starts_at"].date
    assert handle.component_refs["starts_at:time"] is handle.component_refs["starts_at"].time
