"""A tiny welcome panel for the Festival of Mismatched Socks.

The organizing committee wanted something elegant.
What they got is a banner, a slogan, and alarming confidence.
"""

from nicegui import ui

import nicegui_builder
from nicegui_builder import load_layout


def build_ui():
    ui.builder(load_layout("ex01_basic_builder"))


def main(*, port: int = 8080, host: str | None = None, reload: bool = False):
    ui.run(root=build_ui, port=port, host=host, reload=reload)


if __name__ in {"__main__", "__mp_main__"}:
    main()
