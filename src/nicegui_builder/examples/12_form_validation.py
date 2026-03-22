"""Validation at the festival registration desk.

The form is patient.
The rules are clear.
The participants remain gloriously unpredictable.
"""

from nicegui import ui

from nicegui_builder import form
from nicegui_builder.examples.models import Participant


def _apply_errors(handle):
    handle.apply_errors(as_model=True)
    ui.notify("Field errors applied. The desk has entered its corrective era.")


def build_ui():
    ui.label("Form validation and error handling").classes("text-h5")
    ui.label(
        "Try clearing the required fields, then use the controls below to inspect and display validation errors."
    ).classes("text-body2 text-grey-7")

    handle = form(Participant, flavor="actionable")
    handle.action_bar(
        "Validate gently",
        lambda values: ui.notify(f"Looks valid enough for a sock festival: {values['display_name']}"),
        apply_errors=True,
        live_submit_button=True,
        live_reset_button=True,
        show_when_clean=True,
    )

    with ui.row().classes("gap-2"):
        ui.button(
            "Validate as values",
            on_click=lambda: ui.notify(str(handle.validate().valid)),
        )
        ui.button(
            "Validate as model",
            on_click=lambda: ui.notify(str(handle.validate(as_model=True).valid)),
        )
        ui.button(
            "Apply field errors",
            on_click=lambda: _apply_errors(handle),
        )
        ui.button(
            "Show messages",
            on_click=lambda: ui.notify(" | ".join(handle.error_messages(as_model=True)) or "No errors"),
        )

    handle.live_error_panel(
        as_model=True,
        title="Committee concerns",
        empty_message="Everything appears administratively survivable.",
        strategy="invalid",
    )


def main(*, port: int = 8080, host: str | None = None, reload: bool = False):
    ui.run(root=build_ui, port=port, host=host, reload=reload)


if __name__ in {"__main__", "__mp_main__"}:
    main()
