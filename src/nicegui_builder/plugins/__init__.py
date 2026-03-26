from importlib import import_module

from .base import CollectionPlugin, FieldPlugin, SourcePlugin
from .registry import plugin_registry


def _load_optional_builtin(module_name: str, *, missing_dependencies: set[str]) -> None:
    try:
        import_module(f"{__name__}.{module_name}")
    except ModuleNotFoundError as exc:
        if exc.name in missing_dependencies:
            return
        raise


_load_optional_builtin("pydantic", missing_dependencies={"pydantic", "pydantic_core"})
_load_optional_builtin("pandas", missing_dependencies={"pandas"})

__all__ = ["CollectionPlugin", "FieldPlugin", "SourcePlugin", "plugin_registry"]
