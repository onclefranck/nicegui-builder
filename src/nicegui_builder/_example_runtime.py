"""Shared runtime setup for bundled examples."""

from __future__ import annotations

import logging

from nicegui import run as nicegui_run


def patch_nicegui_process_pool_setup() -> None:
    original_setup = nicegui_run.setup

    if getattr(original_setup, "_nicegui_builder_examples_patched", False):
        return

    def safe_setup() -> None:
        try:
            original_setup()
        except PermissionError as exc:
            logging.warning(
                "NiceGUI process pool is unavailable for bundled examples; "
                "continuing without CPU-bound worker support: %s",
                exc,
            )

    safe_setup._nicegui_builder_examples_patched = True  # type: ignore[attr-defined]
    nicegui_run.setup = safe_setup
