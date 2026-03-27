from pydantic import BaseModel
from nicegui import ui

import nicegui_builder


class DemoPydanticBuilder(BaseModel):
    firstname: str
    lastname: str
    email: str


def build_ui():
    ui.form_builder(DemoPydanticBuilder)


def main(*, port: int = 8080, host: str | None = None, reload: bool = False):
    ui.run(root=build_ui, port=port, host=host, reload=reload)


if __name__ in {"__main__", "__mp_main__"}:
    main()
