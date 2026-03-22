"""A gentle look at the plugin-local widget map.

The pydantic plugin keeps its widget opinions in a YAML file.
This is where a `datetime` quietly becomes two inputs and nobody panics. Much.
"""

from nicegui import ui

from nicegui_builder.examples.models import Contest, Participant, Registration
from nicegui_builder.plugins.pydantic.mapping import (
    get_defaults_from_map,
    resolve_map_type,
    select_default_variant,
)
from nicegui_builder.plugins.pydantic.plugin import PydanticPlugin


def _mapping_rows(plugin: PydanticPlugin, source) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for spec in plugin.inspect_fields(source):
        field_info = spec.source_meta["field_info"]
        map_type = resolve_map_type(spec.python_type)
        variant = select_default_variant(field_info, map_type, "std")
        defaults = get_defaults_from_map(map_type, variant)
        rows.append(
            {
                "field": spec.name,
                "map_type": map_type,
                "variant": variant,
                "component": defaults.get("methods", ""),
            }
        )
    return rows


def _markdown_table(rows: list[dict[str, str]]) -> str:
    header = "| Field | Map type | Variant | Component |\n| --- | --- | --- | --- |"
    body = "\n".join(
        f"| `{row['field']}` | `{row['map_type']}` | `{row['variant']}` | `{row['component']}` |"
        for row in rows
    )
    return f"{header}\n{body}"


def build_ui():
    plugin = PydanticPlugin()

    ui.label("Plugin-local mapping").classes("text-h5")
    ui.label(
        "These tables show how the pydantic plugin chooses widgets from its own YAML map."
    ).classes("text-body2 text-grey-7")

    sections = [
        ("Participant", _mapping_rows(plugin, Participant)),
        ("Contest", _mapping_rows(plugin, Contest)),
        ("Registration", _mapping_rows(plugin, Registration)),
    ]

    with ui.column().classes("w-full max-w-4xl mx-auto gap-4"):
        for title, rows in sections:
            with ui.card().classes("gap-2"):
                ui.label(title).classes("text-h6")
                ui.markdown(_markdown_table(rows)).classes("w-full")

    ui.label(
        "If you want a different default, the first place to look is the plugin-local `pydantic-nicegui.yml`."
    ).classes("text-caption text-grey-7")


def main(*, port: int = 8080, host: str | None = None, reload: bool = False):
    ui.run(root=build_ui, port=port, host=host, reload=reload)


if __name__ in {"__main__", "__mp_main__"}:
    main()
