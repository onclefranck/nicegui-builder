import pathlib as p
import yaml

from nicegui import ui
import nicegui_builder


def build_ui():
    with p.Path("src/nicegui_builder/examples/demo_basic_builder.yml").open(encoding="utf-8") as file:
        layout = yaml.safe_load(file)

    ui.builder(layout)


def main(*, port: int = 8080, host: str | None = None, reload: bool = False):
    ui.run(root=build_ui, port=port, host=host, reload=reload)


if __name__ in {"__main__", "__mp_main__"}:
    main()
