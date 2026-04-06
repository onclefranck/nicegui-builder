"""Direct use of the shared datetime_input component.

Sometimes the festival desk does not want a whole form.
It just wants one civilized datetime control and a few buttons to poke at it.
"""

from datetime import datetime

from nicegui import ui

import nicegui_builder


def build_ui():
    ui.label("Direct datetime_input usage").classes("text-h5")
    ui.label(
        "This example uses ui.datetime_input(...) directly, without form_builder or pandas."
    ).classes("text-body2 text-grey-7")

    with ui.card().classes("w-full max-w-3xl mx-auto gap-3"):
        control = ui.datetime_input(
            value=datetime(2026, 6, 14, 18, 45),
            container={
                "methods": "grid",
                "params": {"columns": 2},
                "classes": "w-full gap-2",
                "props": "",
            },
            date_options={
                "label": "Festival date",
                "classes": "col",
                "props": "clearable",
            },
            time_options={
                "label": "Festival time",
                "classes": "col",
                "props": "clearable",
            },
        )

        ui.label(
            "The component keeps one logical datetime value while exposing .container, .date, and .time."
        ).classes("text-caption text-grey-7")

        with ui.row().classes("gap-2"):
            ui.button(
                "Show value",
                on_click=lambda: ui.notify(str(control.value)),
            )
            ui.button(
                "Set 21:30",
                on_click=lambda: control.set_value(datetime(2026, 6, 14, 21, 30)),
            )
            ui.button(
                "Clear",
                on_click=lambda: control.set_value(None),
            )
            ui.button(
                "Show child refs",
                on_click=lambda: ui.notify(
                    f"date={control.date.value!r} time={control.time.value!r}"
                ),
            )


def main(*, port: int = 8080, host: str | None = None, reload: bool = False):
    ui.run(root=build_ui, port=port, host=host, reload=reload)


if __name__ in {"__main__", "__mp_main__"}:
    main()
