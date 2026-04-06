"""Watching a form become dramatically impure.

A pristine festival form is a rare and temporary phenomenon.
This example celebrates the exact moment it stops being one.
"""

from nicegui import ui

import nicegui_builder
from nicegui_builder.plugins.pydantic.examples.models import Participant


def _show_changes(handle):
    changes = handle.changed_fields()
    if not changes:
        ui.notify("No unsaved changes. The desk is calm for once.")
        return
    ui.notify(str(changes))


def build_ui():
    ui.label("Dirty state helpers").classes("text-h5")
    ui.label(
        "Change a field, and the form will cheerfully admit that it is no longer in its original state."
    ).classes("text-body2 text-grey-7")

    handle = ui.form_builder(
        Participant(
            display_name="Marshall Greatdisagreement",
            email="marshall@example.com",
            mismatch_level=8,
            emergency_note="Will defend asymmetry as an art form if encouraged.",
        ),
        flavor="actionable",
    )

    with ui.row().classes("gap-2 items-center"):
        handle.live_dirty_badge(show_when_clean=True, strategy="always")
        ui.button(
            "Is dirty?",
            on_click=lambda: ui.notify(str(handle.is_dirty())),
        )
        ui.button(
            "Show changed fields",
            on_click=lambda: _show_changes(handle),
        )
        ui.button(
            "Reset to source",
            on_click=handle.reset_to_source,
        )


def main(*, port: int = 8080, host: str | None = None, reload: bool = False):
    ui.run(root=build_ui, port=port, host=host, reload=reload)


if __name__ in {"__main__", "__mp_main__"}:
    main()

