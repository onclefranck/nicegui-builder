from nicegui import ui
from importlib import import_module
from typing import Callable
from .core.models import LayoutNode
from .core.context import builder_ctx, component_refs, ensure_builder_runtime, get_root_component, set_root_component

builder_expansion_registry: dict[str, Callable[[str, dict], LayoutNode]] = {}


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


def _normalize_layout_entry(component: dict, ctx: dict) -> LayoutNode:
    if isinstance(component, LayoutNode):
        if "__" not in component.methods:
            return component
        key = component.methods
        value = dict(component.context.get("builder_value") or {})
        value.setdefault("params", dict(component.params))
        value.setdefault("classes", component.classes)
        value.setdefault("props", component.props)
        value.setdefault("ref", component.ref)
        value.setdefault("children", list(component.children))
    else:
        key, value = next(iter(component.items()))
        if value is None:
            value = {}

    if "__" in key:
        register_key, builder_key = key.split("__", 1)
        return builder_expansion_registry[register_key](builder_key, value)

    return LayoutNode.from_layout_entry(component)


def _prepare_node(component, ctx: dict) -> LayoutNode:
    normalized = _normalize_layout_entry(component, ctx)
    params = {
        key: resolve_context_value(value, ctx)
        for key, value in normalized.params.items()
    }
    classes = resolve_context_value(normalized.classes, ctx)
    props = resolve_context_value(normalized.props, ctx)

    return LayoutNode(
        methods=normalized.methods,
        params=params,
        props=props,
        classes=classes,
        ref=normalized.ref,
        children=normalized.children,
        context=normalized.context,
    )


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
        prepared = _prepare_node(component, ctx)
        ui_component = _render_method_chain(prepared.methods, prepared.params)

        if prepared.classes:
            ui_component.classes(prepared.classes)

        if prepared.props:
            ui_component.props(prepared.props)

        if prepared.ref:
            refs = component_refs(ctx)
            if prepared.ref in refs:
                raise ValueError(f"duplicate component ref: {prepared.ref}")
            refs[prepared.ref] = ui_component

        if prepared.children:
            with ui_component:
                visit(prepared.children)

        set_root_component(ctx, ui_component)

        builder_ctx.reset(ctx_token)


def register(key: str, callback: Callable[[str, dict], LayoutNode]) -> None:
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
    def the_callback(resolver_key: str, node_value: dict) -> LayoutNode:
        ...
        return LayoutNode(methods="label")
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
