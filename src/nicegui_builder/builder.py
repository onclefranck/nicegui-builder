from nicegui import ui
from importlib import import_module
from .core.models import LayoutNode
from .core.context import builder_ctx, component_refs, ensure_builder_runtime, get_root_component, set_root_component

builder_expansion_registry = {}


def resolve_context_value(value, ctx):
    if not isinstance(value, str):
        return value

    if value.startswith("_"):
        return value.removeprefix("_").format(**ctx)

    if value.startswith("$"):
        import_string = value.removeprefix("$")
        module, func = import_string.split(':')
        return getattr(import_module(module), func)(**ctx)

    return value


def _normalize_layout_entry(component: dict, ctx: dict) -> dict:
    if isinstance(component, LayoutNode):
        return component

    key, value = next(iter(component.items()))
    if value is None:
        value = {}

    if "__" in key:
        register_key, builder_key = key.split("__", 1)
        resolved = builder_expansion_registry[register_key](builder_key, value)
        if isinstance(resolved, LayoutNode):
            return resolved
        return LayoutNode.from_dict(
            {
                "methods": resolved.get("methods"),
                "params": resolved.get("params") or {},
                "classes": resolved.get("classes", ""),
                "props": resolved.get("props", ""),
                "ref": resolved.get("ref"),
                "children": resolved.get("children", value.get("children", [])),
            }
        )

    return LayoutNode.from_layout_entry(component)


def _render_method_chain(method_chain: str, params: dict):
    ui_component = None
    methods = method_chain.split('.')
    effective_params = {}

    for i, method in enumerate(methods):
        if i == len(methods) - 1:
            effective_params = params
        ui_component = (
            getattr(ui_component, method)(**effective_params)
            if ui_component
            else getattr(ui, method)(**effective_params)
        )

    return ui_component


def visit(components: list):

    for component in components:

        ctx = dict(builder_ctx.get())
        ctx_token = builder_ctx.set(ctx)
        normalized = _normalize_layout_entry(component, ctx)
        params = dict(normalized.params)
        classes = normalized.classes
        props = normalized.props
        ref = normalized.ref
        children = normalized.children

        for k, v in params.items():
            params[k] = resolve_context_value(v, ctx)

        classes = resolve_context_value(classes, ctx)
        props = resolve_context_value(props, ctx)
        ui_component = _render_method_chain(normalized.methods, params)
        
        # apply classes if any
        if classes:
            ui_component.classes(classes)
        
        # apply props if any
        if props:
            ui_component.props(props)

        if ref:
            refs = component_refs(ctx)
            if ref in refs:
                raise ValueError(f"duplicate component ref: {ref}")
            refs[ref] = ui_component

        # process children if any
        if children:
            with ui_component:
                visit(children)

        set_root_component(ctx, ui_component)

        builder_ctx.reset(ctx_token)


def register(key, callback):
    """Register a callback so the builder can delegate node resolution

    In the layout, an element can be solved by an extended solver.
    
    As an example, pydantic model have special resolver so the following layout
    element can be resolved: `field__address: {...}`.
    
    In this example:
    - `field` before the dunder is the registry key
    - `address` after the dunder is the resolver key
    - `{...}` is the layout node value

    The callback function should have the following signature:
    `
    def the_callback(resolver_key: str, node_value: dict) -> method: str, params: dict:
        ...
        return method, params
    `

    When registering the callback function:
    `
    register("field", the_callback)
    `
    """
    builder_expansion_registry[key] = callback


def builder(layout) -> None:
    ctx = dict(builder_ctx.get())
    ensure_builder_runtime(ctx)
    ctx_token = builder_ctx.set(ctx)
    visit(layout)
    root_component = get_root_component(ctx)
    if root_component is not None and hasattr(root_component, "__dict__"):
        root_component.component_refs = dict(component_refs(ctx))
    builder_ctx.reset(ctx_token)
    return root_component
