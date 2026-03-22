from .builder import builder
from .core.table import TableHandle
from .core.models import TableSpec
from .plugins import plugin_registry
from .plugins import pandas as _pandas_plugin  # ensure builtin plugin registration


def _build_table_handle(component, table_spec: TableSpec, plugin=None):
    if component is None:
        return None

    try:
        setattr(component, "table_spec", table_spec)
    except Exception:
        pass

    handle = TableHandle(table_spec=table_spec, root_component=component, plugin=plugin)

    component_filters = getattr(component, "filter_values", None)
    if isinstance(component_filters, dict):
        handle.filter_values = component_filters

    try:
        setattr(component, "table_handle", handle)
    except Exception:
        pass

    return handle


def table(source, variant: str = "std"):
    plugin = plugin_registry.resolve(source)
    if not hasattr(plugin, "inspect_collection") or not hasattr(plugin, "resolve_collection_widget"):
        raise TypeError(f"plugin '{plugin.name}' does not support table(...)")

    collection_spec = plugin.inspect_collection(source)
    source_class = source if isinstance(source, type) else source.__class__
    widget = plugin.resolve_collection_widget(collection_spec, variant=variant)
    table_spec = TableSpec(
        source_class=source_class,
        collection_spec=collection_spec,
        source=source,
        widget_spec=widget,
        variant=variant,
        plugin_name=plugin.name,
    )

    if hasattr(plugin, "render_collection"):
        rendered = plugin.render_collection(source, collection_spec, variant=variant, table_spec=table_spec)
        if rendered is not None:
            return _build_table_handle(rendered, table_spec, plugin=plugin)

    rows = plugin.prepare_rows(source) if hasattr(plugin, "prepare_rows") else source.to_dict(orient="records")

    layout = [
        {
            widget.component: {
                "params": {
                    **widget.params,
                    "rows": rows,
                },
                "props": widget.props,
                "classes": widget.classes,
            }
        }
    ]

    table_spec.layout = layout
    return _build_table_handle(builder(layout), table_spec, plugin=plugin)
