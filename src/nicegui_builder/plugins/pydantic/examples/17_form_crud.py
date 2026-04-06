"""Ready-made CRUD actions for a form with ambitions.

The festival office now has buttons for create, update, and delete.
This is how bureaucracy starts to feel dangerously confident.
"""

from nicegui import ui

import nicegui_builder

from .models import Registration


def _create_registration(model: Registration):
    ui.notify(f"Created registration for {model.participant_name}")


def _update_registration(model: Registration):
    ui.notify(f"Updated registration status to {model.status}")


def _delete_registration(target):
    participant_name = getattr(target, "participant_name", None) or target.get("participant_name", "Unknown")
    ui.notify(f"Deleted registration for {participant_name}")


def build_ui():
    ui.label("CRUD-ready form actions").classes("text-h5")
    ui.label(
        "The registration desk has discovered buttons that sound official and therefore improve morale."
    ).classes("text-body2 text-grey-7")

    handle = ui.form_builder(
        Registration(
            participant_name="Alice Two-Left-Socks",
            contest_title="Interpretive Heel Rotation",
            notes="Insists the socks were mismatched on purpose, which seems plausible.",
        ),
        flavor="actionable",
    )

    handle.crud_bar(
        on_create=_create_registration,
        on_update=_update_registration,
        on_delete=_delete_registration,
        as_model=True,
        apply_errors=True,
    )
    handle.live_error_panel(
        as_model=True,
        title="Administrative objections",
        empty_message="No objections. The forms are behaving.",
        strategy="invalid",
    )

    ui.label(
        "The persistence layer is still your callback, but the buttons are already dressed for the occasion."
    ).classes("text-caption text-grey-7")


def main(*, port: int = 8080, host: str | None = None, reload: bool = False):
    ui.run(root=build_ui, port=port, host=host, reload=reload)


if __name__ in {"__main__", "__mp_main__"}:
    main()

