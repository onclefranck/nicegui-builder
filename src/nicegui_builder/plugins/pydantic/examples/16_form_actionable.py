"""A form with opinions, buttons, and a sense of purpose.

The actionable flavor gives the registration desk dedicated places
for status, actions, and administrative concern.
This is the closest the festival gets to executive polish.
"""

from nicegui import ui

import nicegui_builder

from .models import Contest


def _save_contest(model: Contest):
    ui.notify(f"Contest saved: {model.title}")


def build_ui():
    ui.label("Actionable flavor").classes("text-h5")
    ui.label(
        "This layout exposes built-in status, action, and error areas so the handle can do more of the stage work."
    ).classes("text-body2 text-grey-7")

    handle = ui.form_builder(Contest, flavor="actionable")

    handle.action_bar(
        "Save contest",
        _save_contest,
        as_model=True,
        apply_errors=True,
        live_changed_badge=True,
        live_submit_button=True,
        live_reset_button=True,
        show_when_clean=True,
        submit_strategy="dirty_and_valid",
        reset_strategy="dirty",
    )
    handle.live_error_panel(
        as_model=True,
        title="Operational concerns",
        empty_message="No operational concerns. The chaos is, for now, well curated.",
        strategy="invalid",
    )

    ui.label(
        "Fill the form, break the form, fix the form: the built-in zones should keep up."
    ).classes("text-caption text-grey-7")


def main(*, port: int = 8080, host: str | None = None, reload: bool = False):
    ui.run(root=build_ui, port=port, host=host, reload=reload)


if __name__ in {"__main__", "__mp_main__"}:
    main()

