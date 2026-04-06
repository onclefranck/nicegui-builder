"""How to test a layout file quickly from the CLI.

This is for the moment when someone says
"I only changed a tiny YAML thing" with dangerous confidence.
"""

from nicegui import ui


def build_ui() -> None:
    ui.label("CLI: run a layout file").classes("text-h5")
    ui.markdown(
        """
If you want to render a layout file directly:

```bash
nicegui-builder layout run src/nicegui_builder/examples/layouts/festival_notice.yml
```

This is useful for quick experimentation with declarative layouts,
especially when the registration desk has opinions about spacing.
"""
    ).classes("w-full max-w-3xl")


def main(*, port: int = 8080, host: str | None = None, reload: bool = False) -> None:
    ui.run(root=build_ui, port=port, host=host, reload=reload)


if __name__ in {"__main__", "__mp_main__"}:
    main()
