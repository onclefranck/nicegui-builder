from .plugin import PandasPlugin
from ..registry import plugin_registry

pandas_plugin = PandasPlugin()
plugin_registry.register(pandas_plugin)

__all__ = ["PandasPlugin", "pandas_plugin"]
