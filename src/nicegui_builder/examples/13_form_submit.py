"""Submitting festival forms with a straight face.

The registration desk now accepts that a form may become a model,
which is a surprisingly philosophical sentence for a sock festival.
"""

from nicegui import ui

from nicegui_builder import form
from nicegui_builder.examples.models import Registration


def _notify_values(values: dict[str, object]):
    ui.notify(f"Submitted raw values for {values['participant_name']}")


def _notify_model(model: Registration):
    ui.notify(f"Rebuilt model with status {model.status}")


def build_ui():
    ui.label("Form submit and model reconstruction").classes("text-h5")
    ui.label(
        "The same form can submit plain values or a reconstructed Pydantic model, depending on the desk's mood."
    ).classes("text-body2 text-grey-7")

    handle = form(
        Registration(
            participant_name="Odette of the Triumphant Heel",
            contest_title="Midnight Parade of Respectable Nonsense",
            notes="Has already thanked the judges in advance, which feels strategic.",
        ),
        flavor="actionable",
    )

    with ui.row().classes("gap-2"):
        ui.button(
            "Show to_model()",
            on_click=lambda: ui.notify(str(handle.to_model())),
        )
        ui.button(
            "Submit values",
            on_click=lambda: handle.submit(_notify_values, apply_errors=True),
        )
        ui.button(
            "Submit model",
            on_click=lambda: handle.submit(_notify_model, as_model=True, apply_errors=True),
        )

    handle.action_bar(
        "Approve registration",
        _notify_model,
        as_model=True,
        apply_errors=True,
        live_changed_badge=True,
        live_submit_button=True,
        live_reset_button=True,
        show_when_clean=True,
    )


def main(*, port: int = 8080, host: str | None = None, reload: bool = False):
    ui.run(root=build_ui, port=port, host=host, reload=reload)


if __name__ in {"__main__", "__mp_main__"}:
    main()
