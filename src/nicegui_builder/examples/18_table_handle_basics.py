"""Basic runtime manipulation of a festival table.

At last, the program board can be reordered without a committee meeting,
which is frankly revolutionary.
"""

from datetime import datetime

from nicegui import ui
import pandas as pd

from nicegui_builder import table


def _contest_rows() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "title": "Emergency Synchronised Sock Folding",
                "category": "Formal chaos",
                "starts_at": datetime(2026, 6, 13, 9, 30).isoformat(timespec="minutes"),
                "duration_minutes": 20,
            },
            {
                "title": "Interpretive Heel Rotation",
                "category": "Dramatic pairing",
                "starts_at": datetime(2026, 6, 13, 11, 15).isoformat(timespec="minutes"),
                "duration_minutes": 45,
            },
            {
                "title": "Parade of Alarmingly Formal Ankles",
                "category": "Crowd favorite",
                "starts_at": datetime(2026, 6, 13, 14, 0).isoformat(timespec="minutes"),
                "duration_minutes": 35,
            },
        ]
    )


def _replace_rows(handle):
    handle.set_rows(
        [
            {
                "title": "Committee Debrief and Biscuit Recovery",
                "category": "Formal chaos",
                "starts_at": datetime(2026, 6, 13, 16, 30).isoformat(timespec="minutes"),
                "duration_minutes": 25,
            },
            {
                "title": "Closing Ceremony of Glorious Footwear Ambiguity",
                "category": "Crowd favorite",
                "starts_at": datetime(2026, 6, 13, 18, 0).isoformat(timespec="minutes"),
                "duration_minutes": 50,
            },
        ]
    )
    ui.notify("Table rows replaced. The schedule has entered a new artistic phase.")


def _sort_by_duration(handle):
    handle.sort_rows("duration_minutes", descending=True)
    durations = [row["duration_minutes"] for row in handle.get_rows()]
    ui.notify(f"Sorted by duration: {durations}")


def build_ui():
    ui.label("TableHandle basics").classes("text-h5")
    ui.label(
        "Rows can be read, replaced, and sorted without rethinking the entire festival."
    ).classes("text-body2 text-grey-7")

    handle = table(_contest_rows())

    with ui.row().classes("gap-2"):
        ui.button(
            "Show rows",
            on_click=lambda: ui.notify(str(handle.get_rows())),
        )
        ui.button(
            "Sort by duration",
            on_click=lambda: _sort_by_duration(handle),
        )
        ui.button(
            "Replace rows",
            on_click=lambda: _replace_rows(handle),
        )


def main(*, port: int = 8080, host: str | None = None, reload: bool = False):
    ui.run(root=build_ui, port=port, host=host, reload=reload)


if __name__ in {"__main__", "__mp_main__"}:
    main()
