from importlib import import_module
import pathlib as p

import yaml

from .builder import builder, register, builder_ctx
from .core.form import FormHandle
from .core.models import FormSpec
from .plugins import plugin_registry


def _resolve_layout_from_source(source, flavor: str):
    source_class = source if isinstance(source, type) else source.__class__
    source_name = source_class.__name__
    layout_name = f"{source_name}-{flavor}" if flavor else source_name
    mod_folder = p.Path(import_module(source_class.__module__).__file__).parent
    layout_path = mod_folder / f"{layout_name}.yaml"
    with layout_path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _resolve_plugin_field(key: str, value: dict):
    value = value or {}
    ctx = builder_ctx.get()

    plugin = ctx["plugin"]
    fieldname = key.removeprefix("field__")
    ctx["fieldname"] = fieldname

    resolved = plugin.resolve_field_node(
        ctx["source_class"],
        ctx["source_instance"],
        fieldname,
        value,
    )
    ctx.update(resolved["field_ctx"])
    ctx["default_info"] = resolved.get("default_info")
    resolved["node"]["ref"] = f"field:{fieldname}"
    return resolved["node"]


register("field", _resolve_plugin_field)


def form(source, flavor: str = ""):
    plugin = plugin_registry.resolve(source)
    if not hasattr(plugin, "inspect_fields") or not hasattr(plugin, "resolve_field_node"):
        raise TypeError(f"plugin '{plugin.name}' does not support form(...)")

    source_class = source if isinstance(source, type) else source.__class__
    source_instance = None if isinstance(source, type) else source
    if hasattr(plugin, "render_form"):
        rendered = plugin.render_form(source, flavor=flavor)
        if rendered is not None:
            return rendered

    field_specs = plugin.inspect_fields(source)
    try:
        layout = _resolve_layout_from_source(source, flavor)
    except FileNotFoundError:
        if hasattr(plugin, "build_layout"):
            layout = plugin.build_layout(source, flavor=flavor)
        else:
            raise

    ctx = dict(builder_ctx.get())
    ctx_token = builder_ctx.set(ctx)
    ctx.update(
        _component_refs={},
        plugin=plugin,
        source=source,
        source_class=source_class,
        source_instance=source_instance,
        field_specs=field_specs,
        layout=layout,
    )

    form_spec = FormSpec(
        source_class=source_class,
        field_specs=field_specs,
        source_instance=source_instance,
        layout=layout,
        flavor=flavor,
        plugin_name=plugin.name,
    )

    root_component = builder(layout)
    handle = FormHandle(
        root_component=root_component,
        plugin=plugin,
        source_class=source_class,
        field_specs=field_specs,
        component_refs=dict(ctx.get("_component_refs", {})),
        source_instance=source_instance,
        form_spec=form_spec,
    )
    builder_ctx.reset(ctx_token)
    return handle
