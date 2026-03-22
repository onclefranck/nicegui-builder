"""A filtered view of the festival registration board.

The registration desk claims this is "operational clarity".
Observers describe it as "surprisingly competent, given the sock trumpet solo".
"""

from datetime import datetime

from nicegui import ui
import pandas as pd

from nicegui_builder import table


def _registrations_dataframe() -> pd.DataFrame:
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


def build_ui():
    ui.label("Filtered Pandas table").classes("text-h5")
    ui.label(
        "Small filters appear automatically so the desk can find people before the ceremonial confusion begins."
    ).classes("text-body2 text-grey-7")

    handle = table(_registrations_dataframe(), variant="filters")

    with ui.row().classes("gap-2"):
        ui.button(
            "Prefill filters",
            on_click=lambda: handle.apply_filters(
                {
                    "contest_title": {"op": "contains", "value": "Midnight"},
                    "status": {"op": "equals", "value": "Confirmed"},
                }
            ),
        )
        ui.button(
            "Clear filters",
            on_click=lambda: handle.clear_filters().apply_filters({}),
        )
        ui.button(
            "Show active filters",
            on_click=lambda: ui.notify(str(handle.normalized_filter_values())),
        )


def main(*, port: int = 8080, host: str | None = None, reload: bool = False):
    ui.run(root=build_ui, port=port, host=host, reload=reload)


if __name__ in {"__main__", "__mp_main__"}:
    main()
