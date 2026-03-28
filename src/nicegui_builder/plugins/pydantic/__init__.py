from .plugin import PydanticPlugin
from ..registry import plugin_registry

pydantic_plugin = PydanticPlugin()
plugin_registry.register(pydantic_plugin)

__all__ = [
    "pydantic_plugin",
    "PydanticPlugin",
]
