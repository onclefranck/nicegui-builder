"""First contact with the festival registration desk.

One volunteer has opened a brand new form.
Another volunteer has already spilled tea on the paper backup.
The digital future has rarely felt so necessary.
"""

from nicegui import ui

import nicegui_builder
from nicegui_builder.examples.models import Participant


def build_ui():
    ui.label("New participant intake").classes("text-h6")
    ui.form_builder(Participant)


def main(*, port: int = 8080, host: str | None = None, reload: bool = False):
    ui.run(root=build_ui, port=port, host=host, reload=reload)


if __name__ in {"__main__", "__mp_main__"}:
    main()
