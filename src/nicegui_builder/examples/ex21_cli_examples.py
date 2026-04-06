"""A tiny guide to launching bundled examples from the CLI.

Sometimes the fastest documentation is a command you can copy,
paste, and run before the kettle boils.
"""

from nicegui import ui


def build_ui():
    ui.label("CLI: bundled examples").classes("text-h5")
    ui.markdown(
        """
Run these commands from the project root:

```bash
nicegui-builder examples list
nicegui-builder examples run ex03_pydantic_form_basic
nicegui-builder examples run ex10_pandas_table_filters --port 8081
```

The first command lists every bundled example.
The second and third launch one quickly, which is ideal when the festival committee
demands a demonstration before lunch.
"""
    ).classes("w-full max-w-3xl")


def main(*, port: int = 8080, host: str | None = None, reload: bool = False):
    ui.run(root=build_ui, port=port, host=host, reload=reload)


if __name__ in {"__main__", "__mp_main__"}:
    main()
