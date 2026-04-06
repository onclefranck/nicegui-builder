"""Pagination, selection, and export for a table that means business.

The festival board has become efficient enough to frighten the accordion player.
"""

from datetime import datetime

from nicegui import ui
import pandas as pd

import nicegui_builder


def _registration_rows() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "participant_name": "Mira the Unmatched",
                "contest_title": "Midnight Parade of Respectable Nonsense",
                "status": "Confirmed",
                "checked_in_at": datetime(2026, 6, 12, 20, 50).isoformat(timespec="minutes"),
            },
            {
                "participant_name": "Bernard Two-Left-Socks",
                "contest_title": "Speed Folding Under Emotional Pressure",
                "status": "Waitlist",
                "checked_in_at": None,
            },
            {
                "participant_name": "Clara of the Fierce Ankles",
                "contest_title": "Midnight Parade of Respectable Nonsense",
                "status": "Confirmed",
                "checked_in_at": datetime(2026, 6, 12, 20, 58).isoformat(timespec="minutes"),
            },
            {
                "participant_name": "Lucian the Mildly Dramatic",
                "contest_title": "Interpretive Heel Rotation",
                "status": "Dramatically late",
                "checked_in_at": datetime(2026, 6, 12, 21, 17).isoformat(timespec="minutes"),
            },
        ]
    )


def _select_first_two(handle):
    rows = handle.get_rows()[:2]
    handle.set_selected_rows(rows)
    ui.notify("Selected the first two rows. The desk feels decisive.")


def build_ui() -> None:
    ui.label("Table pagination, selection, and export").classes("text-h5")
    ui.label(
        "A few runtime helpers turn the registration board into a surprisingly capable little control panel."
    ).classes("text-body2 text-grey-7")

    handle = ui.table_builder(_registration_rows())

    with ui.row().classes("gap-2"):
        ui.button(
            "Set pagination",
            on_click=lambda: (
                handle.set_pagination(rows_per_page=2, sort_by="participant_name"),
                ui.notify(str(handle.get_pagination())),
            ),
        )
        ui.button(
            "Select first two",
            on_click=lambda: _select_first_two(handle),
        )
        ui.button(
            "Show selected rows",
            on_click=lambda: ui.notify(str(handle.get_selected_rows())),
        )
        ui.button(
            "Preview CSV export",
            on_click=lambda: ui.notify(handle.export_csv()[:160]),
        )


def main(*, port: int = 8080, host: str | None = None, reload: bool = False) -> None:
    ui.run(root=build_ui, port=port, host=host, reload=reload)


if __name__ in {"__main__", "__mp_main__"}:
    main()
