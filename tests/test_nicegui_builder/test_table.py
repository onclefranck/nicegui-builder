import types
import importlib

import pytest

table_module = importlib.import_module("nicegui_builder.table")
from nicegui_builder.core.models import CollectionSpec, FieldSpec, WidgetSpec


class FakePlugin:
    name = "fake"

    def inspect_collection(self, source):
        return CollectionSpec(name="DemoRows", columns=[FieldSpec(name="name", python_type=str)])

    def resolve_collection_widget(self, spec, flavor="std"):
        return WidgetSpec(component="table", params={"columns": [], "row_key": "id"}, classes="w-full")


def test_build_table_handle_attaches_handle_and_spec_to_component():
    component = types.SimpleNamespace(filter_values={"name": "ada"})
    collection_spec = CollectionSpec(name="DemoRows")
    table_spec = table_module.TableSpec(source_class=list, collection_spec=collection_spec, plugin_name="fake")

    handle = table_module._build_table_handle(component, table_spec, plugin="plugin")

    assert handle.component is component
    assert handle.table_spec is table_spec
    assert handle.filter_values is component.filter_values
    assert component.table_handle is handle
    assert component.table_spec is table_spec


def test_build_table_handle_returns_none_for_missing_component():
    collection_spec = CollectionSpec(name="DemoRows")
    table_spec = table_module.TableSpec(source_class=list, collection_spec=collection_spec, plugin_name="fake")

    assert table_module._build_table_handle(None, table_spec) is None


def test_build_table_handle_requires_component_metadata_attachment():
    class FragileComponent:
        def __init__(self) -> None:
            object.__setattr__(self, "filter_values", {"name": "ada"})

        def __setattr__(self, name, value):
            if name in {"table_spec", "table_handle"}:
                raise RuntimeError("read-only test component")
            object.__setattr__(self, name, value)

    component = FragileComponent()
    collection_spec = CollectionSpec(name="DemoRows")
    table_spec = table_module.TableSpec(source_class=list, collection_spec=collection_spec, plugin_name="fake")

    with pytest.raises(RuntimeError, match="read-only test component"):
        table_module._build_table_handle(component, table_spec, plugin="plugin")


def test_table_returns_plugin_rendered_collection_when_available(monkeypatch):
    rendered_component = types.SimpleNamespace(filter_values={})

    class RenderPlugin(FakePlugin):
        def render_collection(self, source, spec, flavor="std", table_spec=None):
            return rendered_component

    monkeypatch.setattr(table_module.plugin_registry, "resolve", lambda source: RenderPlugin())

    handle = table_module.table([{"name": "Ada"}], flavor="filters")

    assert handle.component is rendered_component
    assert handle.spec.plugin_name == "fake"
    assert handle.spec.flavor == "filters"


def test_table_uses_prepare_rows_for_generic_builder_path(monkeypatch):
    calls = {}

    class PreparePlugin(FakePlugin):
        def prepare_rows(self, source):
            return [{"name": "Prepared"}]

    component = types.SimpleNamespace()
    monkeypatch.setattr(table_module.plugin_registry, "resolve", lambda source: PreparePlugin())
    monkeypatch.setattr(
        table_module,
        "builder",
        lambda layout: calls.setdefault("layout", layout) and component,
    )

    handle = table_module.table([{"name": "Ada"}])

    assert handle.spec.layout[0]["table"]["params"]["rows"] == [{"name": "Prepared"}]
    assert calls["layout"][0]["table"]["params"]["rows"] == [{"name": "Prepared"}]


def test_table_falls_back_to_source_to_dict_when_plugin_has_no_prepare_rows(monkeypatch):
    calls = {}

    class ToDictSource:
        def to_dict(self, orient="records"):
            calls["orient"] = orient
            return [{"name": "From source"}]

    component = types.SimpleNamespace()
    monkeypatch.setattr(table_module.plugin_registry, "resolve", lambda source: FakePlugin())
    monkeypatch.setattr(
        table_module,
        "builder",
        lambda layout: calls.setdefault("layout", layout) and component,
    )

    handle = table_module.table(ToDictSource())

    assert calls["orient"] == "records"
    assert handle.spec.layout[0]["table"]["params"]["rows"] == [{"name": "From source"}]


def test_table_rejects_plugins_without_table_capabilities(monkeypatch):
    plugin = types.SimpleNamespace(name="broken")
    monkeypatch.setattr(table_module.plugin_registry, "resolve", lambda source: plugin)

    with pytest.raises(TypeError):
        table_module.table([{"name": "Ada"}])
