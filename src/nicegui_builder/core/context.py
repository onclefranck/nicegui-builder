from contextvars import ContextVar


builder_ctx: ContextVar[dict] = ContextVar("model_info", default={})
