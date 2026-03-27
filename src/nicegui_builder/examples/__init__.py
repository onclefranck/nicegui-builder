"""Shared setup for bundled core examples."""

from ._runtime import patch_nicegui_process_pool_setup


patch_nicegui_process_pool_setup()
