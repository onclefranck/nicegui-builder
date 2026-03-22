"""How to run a form source directly from the CLI.

It is the fastest route from "I have a model"
to "look, the festival form is already on screen".
"""

from nicegui import ui


def build_ui():
    ui.label("CLI: run a form source").classes("text-h5")
    ui.markdown(
        """
You can ask the CLI to render a plugin-supported source directly:

```bash
nicegui-builder form run nicegui_builder.examples.models:Participant
nicegui-builder form run nicegui_builder.examples.models:Contest --flavor actionable
```

This is ideal for trying a model quickly,
or for checking whether the committee's latest field additions were truly wise.
"""
    ).classes("w-full max-w-3xl")


def main(*, port: int = 8080, host: str | None = None, reload: bool = False):
    ui.run(root=build_ui, port=port, host=host, reload=reload)


if __name__ in {"__main__", "__mp_main__"}:
    main()
