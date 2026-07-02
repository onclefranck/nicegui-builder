from contextvars import ContextVar
from typing import Callable


builder_ctx: ContextVar[dict] = ContextVar("model_info", default={})


def ensure_builder_runtime(
    ctx: dict,
    *,
    handlers: dict[str, Callable] | None = None,
    filters: dict[str, Callable] | None = None,
) -> dict:
    runtime = ctx.get("_runtime")
    if runtime is None:
        runtime = {
            "component_refs": {},
            "root_component": None,
            "handlers": {},
            "filters": {},
            "templates": {},
            "ref_owners": {},
        }
        ctx["_runtime"] = runtime
    runtime.setdefault("handlers", {})
    runtime.setdefault("filters", {})
    runtime.setdefault("templates", {})
    runtime.setdefault("ref_owners", {})
    if handlers is not None:
        runtime["handlers"] = dict(handlers)
    if filters is not None:
        runtime["filters"] = dict(filters)
    return runtime


def component_refs(ctx: dict) -> dict:
    return ensure_builder_runtime(ctx)["component_refs"]


def set_root_component(ctx: dict, component) -> None:
    runtime = ensure_builder_runtime(ctx)
    if runtime["root_component"] is None:
        runtime["root_component"] = component


def get_root_component(ctx: dict):
    return ensure_builder_runtime(ctx)["root_component"]
