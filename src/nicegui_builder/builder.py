from nicegui import ui
from importlib import import_module
from .core.context import builder_ctx

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

def visit(components: list):

    for component in components:

        key, value = next(iter(component.items()))

        if value is None:
            value = {}

        ctx = dict(builder_ctx.get())
        ctx_token = builder_ctx.set(ctx)

        if "__" in key:
            register_key, builder_key = key.split("__", 1)
            resolved = builder_expansion_registry[register_key](builder_key, value)
            methods = resolved.get("methods")
            params = resolved.get("params") or {}
            classes = resolved.get("classes", "")
            props = resolved.get("props", "")
            ref = resolved.get("ref")
            children = resolved.get("children", value.get("children", []))

        else:
            methods = key
            params = value.get("params") or {}
            classes = value.get("classes", "")
            props = value.get("props", "")
            ref = value.get("ref")
            children = value.get("children", [])

        methods = methods.split('.')

        for k, v in params.items():
            params[k] = resolve_context_value(v, ctx)

        classes = resolve_context_value(classes, ctx)
        props = resolve_context_value(props, ctx)
                    
        ui_component = None
        effective_params = {}
        for i, method in enumerate(methods):
            # params are applied on the last method
            if i == len(methods) - 1:
                effective_params = params
            ui_component = \
                getattr(ui_component, method)(**effective_params) \
                if ui_component else \
                getattr(ui, method)(**effective_params)
        
        # apply classes if any
        if classes:
            ui_component.classes(classes)
        
        # apply props if any
        if props:
            ui_component.props(props)

        if ref:
            ctx.setdefault("_component_refs", {})[ref] = ui_component

        # process children if any
        if children:
            with ui_component:
                visit(children)

        ctx.setdefault("_builder_state", {}).setdefault("root_component", ui_component)

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
    ctx.setdefault("_builder_state", {})
    ctx_token = builder_ctx.set(ctx)
    visit(layout)
    root_component = ctx["_builder_state"].get("root_component")
    builder_ctx.reset(ctx_token)
    return root_component
