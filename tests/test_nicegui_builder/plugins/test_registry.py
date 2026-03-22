import pytest

from nicegui_builder.plugins import plugin_registry
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
