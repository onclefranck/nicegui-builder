from .builder import builder
from .core.table import TableHandle
from .core.models import TableSpec
from .plugins import plugin_registry
from .plugins.registry import (
    maybe_render_collection,
    prepare_collection_rows,
    resolve_collection_plugin,
)
from .plugins import pandas as _pandas_plugin  # ensure builtin plugin registration


def _build_table_handle(component, table_spec: TableSpec, plugin=None):
    if component is None:
        return None

    setattr(component, "table_spec", table_spec)

    handle = TableHandle(table_spec=table_spec, root_component=component, plugin=plugin)

    component_filters = getattr(component, "filter_values", None)
    if isinstance(component_filters, dict):
        handle.filter_values = component_filters

    setattr(component, "table_handle", handle)

    return handle


def table(source, flavor: str = "std"):
    plugin = resolve_collection_plugin(source)

    collection_spec = plugin.inspect_collection(source)
    source_class = source if isinstance(source, type) else source.__class__
    widget = plugin.resolve_collection_widget(collection_spec, flavor=flavor)
    table_spec = TableSpec(
        source_class=source_class,
        collection_spec=collection_spec,
        source=source,
        widget_spec=widget,
        flavor=flavor,
        plugin_name=plugin.name,
    )

    rendered = maybe_render_collection(plugin, source, collection_spec, flavor=flavor, table_spec=table_spec)
    if rendered is not None:
        return _build_table_handle(rendered, table_spec, plugin=plugin)

    rows = prepare_collection_rows(plugin, source)

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
