from importlib import import_module
import pathlib as p

import yaml

from .builder import builder, register, builder_ctx
from .core.component_refs import DateTimeComponentRef
from .core.context import component_refs, ensure_builder_runtime
from .core.form import FormHandle
from .core.models import FormSpec
from .plugins import plugin_registry
from .plugins.registry import build_form_layout, maybe_render_form, resolve_field_plugin


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
    logical_ref = value.get("ref") or resolved["node"].get("ref") or f"field:{fieldname}"
    resolved["node"]["ref"] = logical_ref
    ctx.setdefault("_field_refs", {})[fieldname] = logical_ref
    return resolved["node"]


register("field", _resolve_plugin_field)


def form(source, flavor: str = ""):
    plugin = resolve_field_plugin(source)

    source_class = source if isinstance(source, type) else source.__class__
    source_instance = None if isinstance(source, type) else source
    rendered = maybe_render_form(plugin, source, flavor=flavor)
    if rendered is not None:
        return rendered

    field_specs = plugin.inspect_fields(source)
    try:
        layout = _resolve_layout_from_source(source, flavor)
    except FileNotFoundError:
        layout = build_form_layout(plugin, source, flavor=flavor)

    ctx = dict(builder_ctx.get())
    ctx_token = builder_ctx.set(ctx)
    ensure_builder_runtime(ctx)
    ctx.update(
        plugin=plugin,
        source=source,
        source_class=source_class,
        source_instance=source_instance,
        field_specs=field_specs,
        layout=layout,
        _field_refs={},
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
    refs = dict(component_refs(ctx))
    field_refs = dict(ctx.get("_field_refs", {}))
    for field in field_specs:
        logical_ref = field_refs.get(field.name, f"field:{field.name}")
        date_ref = f"{logical_ref}:date"
        time_ref = f"{logical_ref}:time"
        if date_ref in refs or time_ref in refs:
            refs[logical_ref] = DateTimeComponentRef(
                container=refs.get(logical_ref),
                date=refs.get(date_ref),
                time=refs.get(time_ref),
            )
    if root_component is not None and hasattr(root_component, "__dict__"):
        root_component.component_refs = refs
    handle = FormHandle(
        root_component=root_component,
        plugin=plugin,
        source_class=source_class,
        field_specs=field_specs,
        component_refs=refs,
        field_refs=field_refs,
        source_instance=source_instance,
        form_spec=form_spec,
    )
    builder_ctx.reset(ctx_token)
    return handle
