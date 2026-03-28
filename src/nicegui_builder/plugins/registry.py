from nicegui_builder.plugins.base import CollectionPlugin, FieldPlugin, PluginRegistration, SourcePlugin


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


def _require_plugin_methods(plugin: SourcePlugin, *method_names: str) -> None:
    missing = [
        method_name
        for method_name in method_names
        if not callable(getattr(plugin, method_name, None))
    ]
    if missing:
        joined = ", ".join(missing)
        raise TypeError(f"plugin '{plugin.name}' is missing required method(s): {joined}")


def resolve_field_plugin(source) -> FieldPlugin:
    plugin = plugin_registry.resolve(source)
    _require_plugin_methods(plugin, "inspect_fields", "resolve_field_node")
    return plugin


def resolve_collection_plugin(source) -> CollectionPlugin:
    plugin = plugin_registry.resolve(source)
    _require_plugin_methods(plugin, "inspect_collection", "resolve_collection_widget")
    return plugin


def maybe_render_form(plugin: FieldPlugin, source, *, flavor: str = ""):
    render_form = getattr(plugin, "render_form", None)
    if callable(render_form):
        return render_form(source, flavor=flavor)
    return None


def build_form_layout(plugin: FieldPlugin, source, *, flavor: str = ""):
    build_layout = getattr(plugin, "build_layout", None)
    if not callable(build_layout):
        raise FileNotFoundError("plugin does not provide build_layout(...)")
    return build_layout(source, flavor=flavor)


def maybe_render_collection(
    plugin: CollectionPlugin,
    source,
    spec,
    *,
    flavor: str = "std",
    table_spec=None,
):
    render_collection = getattr(plugin, "render_collection", None)
    if callable(render_collection):
        return render_collection(source, spec, flavor=flavor, table_spec=table_spec)
    return None


def prepare_collection_rows(plugin: CollectionPlugin, source) -> list[dict]:
    prepare_rows = getattr(plugin, "prepare_rows", None)
    if callable(prepare_rows):
        return prepare_rows(source)
    return source.to_dict(orient="records")


def filter_collection_rows(plugin: CollectionPlugin, source, filter_values: dict[str, object]) -> list[dict]:
    filter_rows = getattr(plugin, "filter_rows", None)
    if not callable(filter_rows):
        raise TypeError("filter_rows() is not supported for this collection plugin")
    return filter_rows(source, filter_values)
