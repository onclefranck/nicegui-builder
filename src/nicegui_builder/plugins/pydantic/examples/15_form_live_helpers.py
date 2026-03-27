"""Live helpers for a form that refuses to stay quiet.

Every time a participant edits something, the interface reacts.
It is the closest thing this festival has to a reliable chaperone.
"""

from nicegui import ui

import nicegui_builder
from nicegui_builder.examples.models import Participant


def build_ui():
    ui.label("Live form helpers").classes("text-h5")
    ui.label(
        "Dirty tracking, live validation, and strategic buttons all reacting as the form changes."
    ).classes("text-body2 text-grey-7")

    handle = ui.form_builder(Participant, flavor="actionable")
    handle.live_validation(as_model=True, mode="change")

    with ui.row().classes("gap-2 items-center"):
        handle.live_dirty_badge(show_when_clean=True, strategy="always")
        handle.live_reset_button(
            "Reset politely",
            strategy="dirty",
            color="secondary",
        )
        handle.live_submit_button(
            "Approve participant",
            lambda model: ui.notify(f"Approved: {model.display_name}"),
            as_model=True,
            apply_errors=True,
            strategy="dirty_and_valid",
            color="positive",
        )

    handle.live_error_panel(
        as_model=True,
        title="Live objections from the registration desk",
        empty_message="No objections. The socks may proceed.",
        strategy="invalid",
    )

    ui.label(
        "Try editing the form: the badge, buttons, and error panel should all react on their own."
    ).classes("text-caption text-grey-7")


def main(*, port: int = 8080, host: str | None = None, reload: bool = False):
    ui.run(root=build_ui, port=port, host=host, reload=reload)


if __name__ in {"__main__", "__mp_main__"}:
    main()
