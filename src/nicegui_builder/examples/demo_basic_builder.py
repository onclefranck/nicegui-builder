from nicegui import ui
import nicegui_builder  # noqa: F401
from nicegui_builder import load_layout


def build_ui() -> None:
    ui.builder(load_layout("demo_basic_builder"))


def main(*, port: int = 8080, host: str | None = None, reload: bool = False) -> None:
    ui.run(root=build_ui, port=port, host=host, reload=reload)


if __name__ in {"__main__", "__mp_main__"}:
    main()
