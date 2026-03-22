from nicegui_builder.plugins.base import PluginRegistration, SourcePlugin


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins: dict[str, PluginRegistration] = {}

    def register(self, plugin: SourcePlugin) -> None:
        self._plugins[plugin.name] = PluginRegistration(
            name=plugin.name,
            plugin=plugin,
        )

    def get(self, name: str) -> SourcePlugin:
        return self._plugins[name].plugin

    def all(self) -> list[SourcePlugin]:
        return [registration.plugin for registration in self._plugins.values()]

    def resolve(self, source) -> SourcePlugin:
        for registration in self._plugins.values():
            if registration.plugin.supports(source):
                return registration.plugin

        source_type = source if isinstance(source, type) else source.__class__
        raise LookupError(f"no plugin registered for source: {source_type}")


plugin_registry = PluginRegistry()
