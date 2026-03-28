"""A builder example without any YAML file at all.

Sometimes the committee wants a declarative layout,
but also wants it immediately and with suspicious confidence.
"""

from nicegui import ui

import nicegui_builder
from nicegui_builder.utils import load_layout


def build_ui():
    ui.builder(load_layout("02_inline_builder"))


def main(*, port: int = 8080, host: str | None = None, reload: bool = False):
    ui.run(root=build_ui, port=port, host=host, reload=reload)


if __name__ in {"__main__", "__mp_main__"}:
    main()
