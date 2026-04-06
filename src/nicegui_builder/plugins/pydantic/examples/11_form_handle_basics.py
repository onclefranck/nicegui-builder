"""Basic runtime interactions with a festival form.

The registration desk has discovered three powers:
change values, reset values, and pretend this was always the plan.
"""

from nicegui import ui

import nicegui_builder

from .models import Participant, SockColor


def build_ui():
    ui.label("FormHandle basics").classes("text-h5")
    ui.label(
        "A few runtime helpers are enough to make the registration desk feel improbably organized."
    ).classes("text-body2 text-grey-7")

    handle = ui.form_builder(
        Participant(
            display_name="Bernice Freeheel",
            email="bernice@example.com",
            sock_color=SockColor.MOONLIGHT_BLUE,
            mismatch_level=6,
            returning_legend=True,
            emergency_note="Known for elegant panic and surprisingly good ribbon work.",
        )
    )

    with ui.row().classes("gap-2"):
        ui.button(
            "Show values",
            on_click=lambda: ui.notify(str(handle.get_values())),
        )
        ui.button(
            "Prefill with drama",
            on_click=lambda: handle.set_values(
                {
                    "display_name": "Captain Velvet Ankle",
                    "email": "captain.velvet@example.com",
                    "sock_color": SockColor.PANIC_PINK,
                    "mismatch_level": 10,
                    "emergency_note": "Requires polite applause before any administrative discussion.",
                }
            ),
        )
        ui.button(
            "Reset to source",
            on_click=handle.reset_to_source,
        )
        ui.button(
            "Reset to defaults",
            on_click=handle.reset_to_defaults,
        )
        ui.button(
            "Reset to empty",
            on_click=handle.reset_to_empty,
        )


def main(*, port: int = 8080, host: str | None = None, reload: bool = False):
    ui.run(root=build_ui, port=port, host=host, reload=reload)


if __name__ in {"__main__", "__mp_main__"}:
    main()

