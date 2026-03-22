"""The committee insisted on a more polished registration form.

Apparently a serious festival of mismatched socks deserves at least one layout
that looks intentional.
"""

from nicegui import ui

from nicegui_builder import form
from nicegui_builder.examples.models import Participant


def build_ui():
    ui.label("Participant registration with custom YAML layout").classes("text-h6")
    form(Participant)


def main(*, port: int = 8080, host: str | None = None, reload: bool = False):
    ui.run(root=build_ui, port=port, host=host, reload=reload)


if __name__ in {"__main__", "__mp_main__"}:
    main()
