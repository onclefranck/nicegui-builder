"""A quick look at the festival program board.

The board was once alphabetical.
Then creativity happened.
"""

from datetime import datetime

from nicegui import ui
import pandas as pd

from nicegui_builder import table


def build_ui():
    contests = pd.DataFrame(
        [
            {
                "title": "100m Sprint in Polite Panic",
                "category": "Speed mismatch",
                "starts_at": datetime(2026, 6, 12, 9, 0).isoformat(timespec="minutes"),
                "duration_minutes": 25,
            },
            {
                "title": "Interpretive Sock Pairing",
                "category": "Dramatic pairing",
                "starts_at": datetime(2026, 6, 12, 11, 30).isoformat(timespec="minutes"),
                "duration_minutes": 40,
            },
            {
                "title": "Gala of Formal Chaos",
                "category": "Formal chaos",
                "starts_at": datetime(2026, 6, 12, 14, 0).isoformat(timespec="minutes"),
                "duration_minutes": 55,
            },
        ]
    )

    ui.label("Today's contests").classes("text-h6")
    table(contests)


def main(*, port: int = 8080, host: str | None = None, reload: bool = False):
    ui.run(root=build_ui, port=port, host=host, reload=reload)


if __name__ in {"__main__", "__mp_main__"}:
    main()
