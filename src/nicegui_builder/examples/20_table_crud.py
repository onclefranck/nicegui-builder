"""CRUD-style actions for the festival program board.

The board now has create, delete, and export buttons.
Nobody is ready for this much administrative momentum.
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


def _create_contest(handle):
    rows = handle.get_rows()
    rows.append(
        {
            "title": "Closing Waltz of Administrative Triumph",
            "category": "Crowd favorite",
            "starts_at": datetime(2026, 6, 13, 18, 30).isoformat(timespec="minutes"),
            "duration_minutes": 30,
        }
    )
    handle.set_rows(rows)
    ui.notify("Created one more contest. The schedule is now even less negotiable.")


def _delete_selected(rows):
    ui.notify(f"Would delete {len(rows)} selected row(s). The committee appreciates the decisive tone.")


def _preview_export(csv_text: str):
    with ui.dialog() as dialog, ui.card().classes("w-full max-w-3xl gap-3"):
        ui.label("Full table CSV export").classes("text-h6")
        ui.label(
            "This export includes the entire current table, not only the selected rows."
        ).classes("text-body2 text-grey-7")
        ui.code(csv_text).classes("w-full max-h-96 overflow-auto")
        ui.button("Close", on_click=dialog.close)
    dialog.open()


def _show_selected_rows(handle):
    selected = handle.get_selected_rows()
    if not selected:
        ui.notify("No selected rows yet. Even the committee needs a target before acting.")
        return
    ui.notify(f"Selected rows: {selected}")


def _visible_rows(handle):
    rows = handle.get_rows()
    pagination = handle.get_pagination()
    sort_by = pagination.get("sortBy")
    descending = bool(pagination.get("descending"))

    if sort_by:
        rows = sorted(
            rows,
            key=lambda row: (row.get(sort_by) is None, row.get(sort_by)),
            reverse=descending,
        )

    return rows


def _select_first_visible_row(handle):
    rows = _visible_rows(handle)
    if not rows:
        ui.notify("No rows available. The board is suspiciously empty.")
        return

    handle.set_selected_rows(rows[:1])
    ui.notify(f"Selected: {rows[0]['title']}")


def build_ui():
    ui.label("CRUD-ready table actions").classes("text-h5")
    ui.label(
        "Selection is used by 'Delete selected'. 'Export CSV' previews the full current table."
    ).classes("text-body2 text-grey-7")

    handle = table(_contest_rows())

    with ui.row().classes("gap-2"):
        ui.button(
            "Select first row",
            on_click=lambda: _select_first_visible_row(handle),
        )
        ui.button(
            "Show selected rows",
            on_click=lambda: _show_selected_rows(handle),
        )

    handle.crud_bar(
        on_create=_create_contest,
        on_delete_selected=_delete_selected,
        on_export=_preview_export,
    )


def main(*, port: int = 8080, host: str | None = None, reload: bool = False):
    ui.run(root=build_ui, port=port, host=host, reload=reload)


if __name__ in {"__main__", "__mp_main__"}:
    main()
