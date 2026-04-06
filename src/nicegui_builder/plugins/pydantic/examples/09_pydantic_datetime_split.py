"""A close inspection of the festival schedule form.

The committee did not trust a single datetime field.
To be fair, it also does not trust ladders, geese, or matching footwear.
"""

from datetime import datetime

from nicegui import ui

import nicegui_builder
from nicegui_builder.plugins.pydantic.examples.models import Contest


def _sample_contest() -> Contest:
    return Contest(
        title="Ceremonial March of the Alarmingly Bright Socks",
        starts_at=datetime(2026, 6, 13, 10, 45),
        duration_minutes=35,
        master_of_ceremonies="Lucy Whistleworth",
    )


def build_ui():
    ui.label("Datetime split input").classes("text-h5")
    ui.label(
        "The schedule field is rendered as a date input plus a time input, then recombined by the handle."
    ).classes("text-body2 text-grey-7")

    with ui.card().classes("w-full max-w-3xl mx-auto gap-3"):
        handle = ui.form_builder(_sample_contest())

        with ui.row().classes("gap-2"):
            ui.button(
                "Show current values",
                on_click=lambda: ui.notify(str(handle.get_values()["starts_at"])),
            )
            ui.button(
                "Rebuild contest model",
                on_click=lambda: ui.notify(str(handle.to_model().starts_at)),
            )

        ui.label(
            "Try changing only the date or only the time: the collected value stays aggregated."
        ).classes("text-caption text-grey-7")


def main(*, port: int = 8080, host: str | None = None, reload: bool = False):
    ui.run(root=build_ui, port=port, host=host, reload=reload)


if __name__ in {"__main__", "__mp_main__"}:
    main()

