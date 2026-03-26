import pytest

from nicegui_builder.plugins import plugin_registry
import nicegui_builder.plugins as plugins_module
from nicegui_builder.plugins.registry import PluginRegistry


def test_builtin_plugins_are_registered():
    plugin_names = {plugin.name for plugin in plugin_registry.all()}
    assert "pydantic" in plugin_names
    assert "pandas" in plugin_names


def test_registry_resolves_pydantic_model():
    from pydantic import BaseModel

    class DemoModel(BaseModel):
        name: str

    plugin = plugin_registry.resolve(DemoModel)
    assert plugin.name == "pydantic"


def test_registry_can_register_get_and_list_plugins():
    class DemoPlugin:
        name = "demo"

        def supports(self, source):
            return source == "demo-source"

    registry = PluginRegistry()
    plugin = DemoPlugin()

    registry.register(plugin)

    assert registry.get("demo") is plugin
    assert registry.all() == [plugin]
    assert registry.resolve("demo-source") is plugin


def test_registry_raises_lookup_error_with_source_instance_and_type():
    class DemoPlugin:
        name = "demo"

        def supports(self, source):
            return False

    class UnknownSource:
        pass

    registry = PluginRegistry()
    registry.register(DemoPlugin())

    with pytest.raises(LookupError, match="UnknownSource"):
        registry.resolve(UnknownSource())

    with pytest.raises(LookupError, match="UnknownSource"):
        registry.resolve(UnknownSource)


def test_plugins_module_can_skip_optional_builtin_imports(monkeypatch):
    imported = []

    def fake_import(name):
        imported.append(name)
        if name.endswith(".pydantic"):
            raise ModuleNotFoundError("No module named 'pydantic'", name="pydantic")
        return object()

    monkeypatch.setattr(plugins_module, "import_module", fake_import)

    plugins_module._load_optional_builtin("pydantic", missing_dependencies={"pydantic", "pydantic_core"})
    plugins_module._load_optional_builtin("pandas", missing_dependencies={"pandas"})

    assert imported == [
        "nicegui_builder.plugins.pydantic",
        "nicegui_builder.plugins.pandas",
    ]
