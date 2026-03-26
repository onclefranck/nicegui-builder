from contextvars import ContextVar


builder_ctx: ContextVar[dict] = ContextVar("model_info", default={})


def ensure_builder_runtime(ctx: dict) -> dict:
    runtime = ctx.get("_runtime")
    if runtime is None:
        runtime = {
            "component_refs": {},
            "root_component": None,
        }
        ctx["_runtime"] = runtime
    return runtime


def component_refs(ctx: dict) -> dict:
    return ensure_builder_runtime(ctx)["component_refs"]


def set_root_component(ctx: dict, component) -> None:
    runtime = ensure_builder_runtime(ctx)
    if runtime["root_component"] is None:
        runtime["root_component"] = component


def get_root_component(ctx: dict):
    return ensure_builder_runtime(ctx)["root_component"]
