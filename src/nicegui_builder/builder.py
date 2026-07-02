from nicegui import ui
import re
from typing import Callable

from .core.models import LayoutNode
from .core.context import builder_ctx, component_refs, ensure_builder_runtime, get_root_component, set_root_component

builder_expansion_registry: dict[str, Callable[[str, dict], LayoutNode]] = {}

TOKEN_RE = re.compile(r"(?<!\\)\{\{\s*(.*?)\s*\}\}")
TOKEN_ONLY_RE = re.compile(r"\{\{\s*(.*?)\s*\}\}")
PATH_PART_RE = re.compile(r"\.([A-Za-z_][A-Za-z0-9_]*)|\[['\"]([^'\"]+)['\"]\]")


def resolve_context_value(value, ctx):
    if isinstance(value, dict):
        return {key: resolve_context_value(item, ctx) for key, item in value.items()}

    if isinstance(value, list):
        return [resolve_context_value(item, ctx) for item in value]

    if not isinstance(value, str):
        return value

    single_token = TOKEN_ONLY_RE.fullmatch(value)
    if single_token:
        return _resolve_token(single_token.group(1), ctx)

    return TOKEN_RE.sub(lambda match: str(_resolve_token(match.group(1), ctx)), value).replace(r"\{{", "{{")


def _resolve_token(expression: str, ctx: dict):
    parts = [part.strip() for part in expression.split("|")]
    value = _resolve_path(parts[0], ctx)
    filters = ensure_builder_runtime(ctx)["filters"]
    for name in parts[1:]:
        try:
            value = filters[name](value)
        except KeyError as exc:
            raise ValueError(f"unknown filter {name!r}; available: {sorted(filters)}") from exc
    return value


def _resolve_path(path: str, ctx: dict):
    root_match = re.match(r"^[A-Za-z_][A-Za-z0-9_]*|\$[A-Za-z_][A-Za-z0-9_]*", path)
    if root_match is None:
        raise ValueError(f"invalid dynamic expression: {path!r}")

    root = root_match.group(0)
    try:
        value = ctx[root]
    except KeyError as exc:
        raise ValueError(f"unknown context name {root!r}") from exc

    position = root_match.end()
    while position < len(path):
        match = PATH_PART_RE.match(path, position)
        if match is None:
            raise ValueError(f"invalid dynamic path: {path!r}")

        attr_name, item_key = match.groups()
        key = attr_name or item_key
        if attr_name is not None:
            try:
                value = getattr(value, key)
            except AttributeError:
                value = value[key]
        else:
            value = value[key]
        position = match.end()

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
        value.setdefault("on", dict(component.on))
        value.setdefault("children", list(component.children))
    else:
        key, value = next(iter(component.items()))
        if value is None:
            value = {}

    if "__" in key:
        register_key, builder_key = key.split("__", 1)
        return builder_expansion_registry[register_key](builder_key, value)

    return LayoutNode.from_layout_entry(component)


def _is_repeat_entry(component) -> bool:
    return isinstance(component, dict) and next(iter(component.keys())) == "repeat"


def _render_method_chain(method_chain: str, params: dict):
    ui_component = None
    methods = method_chain.split(".")
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


def _bind_event(component, event: str, handler_name: str, ctx: dict) -> None:
    handlers = ensure_builder_runtime(ctx)["handlers"]
    try:
        handler = handlers[handler_name]
    except KeyError as exc:
        raise ValueError(
            f"unknown handler {handler_name!r} for event {event!r}; available: {sorted(handlers)}"
        ) from exc

    repeat_item = ctx.get("_repeat_item")
    if ctx.get("_repeat_active"):

        def bound_handler(event_arg=None, *, _handler=handler, _item=repeat_item):
            return _handler(_item, event_arg)

        callback = bound_handler
    else:
        callback = handler

    method = getattr(component, f"on_{event}", None)
    if callable(method):
        method(callback)
    else:
        component.on(event, callback)


def _register_ref(ctx: dict, ref: str, component) -> None:
    runtime = ensure_builder_runtime(ctx)
    refs = runtime["component_refs"]
    owner_stack = ctx.get("_template_stack") or []
    owner = owner_stack[-1] if owner_stack else None
    repeat_key = ctx.get("$key")

    if ctx.get("_repeat_active"):
        if "$key" not in ctx:
            raise ValueError(f"component ref {ref!r} inside repeat requires a key")
        ref_bucket = refs.setdefault(ref, {})
        if not isinstance(ref_bucket, dict):
            raise ValueError(f"duplicate component ref: {ref}")
        if repeat_key in ref_bucket:
            raise ValueError(f"duplicate component ref: {ref}[{repeat_key!r}]")
        ref_bucket[repeat_key] = component
    else:
        if ref in refs:
            raise ValueError(f"duplicate component ref: {ref}")
        refs[ref] = component

    if owner is not None:
        runtime["ref_owners"][ref] = owner


def _remember_template(ctx: dict, ref: str, children: list) -> None:
    ensure_builder_runtime(ctx)["templates"][ref] = list(children)


def _render_repeat(component: dict, ctx: dict) -> None:
    config = component["repeat"] or {}
    items = resolve_context_value(config["in"], ctx)
    as_name = config["as"]
    children = list(config.get("children") or [])

    for index, item in enumerate(items):
        scope = dict(ctx)
        scope[as_name] = item
        scope["$index"] = index
        scope["_repeat_item"] = item
        scope["_repeat_active"] = True
        if "key" in config:
            scope["$key"] = resolve_context_value(config["key"], scope)
        token = builder_ctx.set(scope)
        try:
            visit(children)
        finally:
            builder_ctx.reset(token)


def _attach_rebuild(root_component, runtime: dict) -> None:
    def rebuild(ref_name: str, *, context: dict | None = None) -> None:
        refs = runtime["component_refs"]
        component = refs[ref_name]
        template = runtime["templates"][ref_name]
        stale_refs = [ref for ref, owner in runtime["ref_owners"].items() if owner == ref_name]
        for ref in stale_refs:
            refs.pop(ref, None)
            runtime["ref_owners"].pop(ref, None)

        component.clear()
        ctx = dict(runtime["base_context"])
        ctx.update(context or {})
        ctx["_runtime"] = runtime
        ctx["_template_stack"] = [ref_name]
        token = builder_ctx.set(ctx)
        try:
            with component:
                visit(template)
        finally:
            builder_ctx.reset(token)

    root_component.rebuild = rebuild


def visit(components: list):

    for component in components:
        ctx = dict(builder_ctx.get())
        ctx_token = builder_ctx.set(ctx)
        try:
            if _is_repeat_entry(component):
                _render_repeat(component, ctx)
                continue

            normalized = _normalize_layout_entry(component, ctx)
            params = {key: resolve_context_value(value, ctx) for key, value in normalized.params.items()}
            classes = resolve_context_value(normalized.classes, ctx)
            props = resolve_context_value(normalized.props, ctx)
            ui_component = _render_method_chain(normalized.methods, params)

            if classes:
                ui_component.classes(classes)

            if props:
                ui_component.props(props)

            for event, handler_name in normalized.on.items():
                _bind_event(ui_component, event, handler_name, ctx)

            if normalized.ref:
                _register_ref(ctx, normalized.ref, ui_component)
                if normalized.children:
                    _remember_template(ctx, normalized.ref, normalized.children)

            if normalized.children:
                child_ctx = dict(builder_ctx.get())
                if normalized.ref:
                    child_ctx["_template_stack"] = [
                        *(child_ctx.get("_template_stack") or []),
                        normalized.ref,
                    ]
                child_token = builder_ctx.set(child_ctx)
                with ui_component:
                    try:
                        visit(normalized.children)
                    finally:
                        builder_ctx.reset(child_token)

            set_root_component(ctx, ui_component)
        finally:
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


def builder(
    layout,
    *,
    context: dict | None = None,
    handlers: dict[str, Callable] | None = None,
    filters: dict[str, Callable] | None = None,
):
    ctx = dict(builder_ctx.get())
    ctx.update(context or {})
    runtime = ensure_builder_runtime(ctx, handlers=handlers, filters=filters)
    runtime["base_context"] = {
        key: value
        for key, value in ctx.items()
        if key != "_runtime" and not key.startswith("_") and not key.startswith("$")
    }
    ctx_token = builder_ctx.set(ctx)
    try:
        visit(layout)
        root_component = get_root_component(ctx)
        if root_component is not None and hasattr(root_component, "__dict__"):
            root_component.component_refs = component_refs(ctx)
            _attach_rebuild(root_component, runtime)
        return root_component
    finally:
        builder_ctx.reset(ctx_token)
