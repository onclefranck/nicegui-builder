"""How a `field__...` node becomes a real widget.

This is the backstage tour.
The audience sees a neat form field.
The committee sees a tiny expansion engine working very hard behind a curtain.
"""

import json

from nicegui import ui

import nicegui_builder
from nicegui_builder.example_models import Participant
from nicegui_builder.plugins import plugin_registry


LAYOUT_SNIPPET = """- card.tight:
    classes: w-full p-4 gap-3
    children:
    - grid:
        params:
          columns: 12
        classes: w-full gap-3
        children:
        - field__display_name:
            classes: col-span-6
        - field__email:
            methods: email
            classes: col-span-6
        - field__emergency_note:
            methods: textarea
            classes: col-span-12
"""


def _pretty(data) -> str:
    return json.dumps(data, indent=2, default=str)


def build_ui():
    plugin = plugin_registry.resolve(Participant)
    sample = Participant(
        display_name="Rosalind Semicolon",
        email="rosalind@example.com",
        emergency_note="Will absolutely ask whether sock asymmetry counts as a worldview.",
    )

    field_ctx = plugin.build_field_context(Participant, sample, "emergency_note")
    resolved = plugin.resolve_field_node(
        Participant,
        sample,
        "emergency_note",
        {"methods": "textarea", "classes": "col-span-12"},
    )

    ui.label("Field context resolution").classes("text-h5")
    ui.label(
        "This example shows the same festival field from three angles: declarative layout, field context, and resolved node."
    ).classes("text-body2 text-grey-7")

    with ui.card().classes("w-full max-w-4xl mx-auto gap-2"):
        ui.label("Declarative layout snippet").classes("text-subtitle1")
        ui.markdown(f"```yaml\n{LAYOUT_SNIPPET}\n```").classes("w-full")

    ui.form_builder(sample)

    with ui.grid(columns=2).classes("w-full max-w-4xl mx-auto gap-4"):
        with ui.card().classes("gap-2"):
            ui.label("Field context").classes("text-subtitle1")
            ui.markdown(f"```json\n{_pretty(field_ctx)}\n```").classes("w-full")

        with ui.card().classes("gap-2"):
            ui.label("Resolved node").classes("text-subtitle1")
            ui.markdown(f"```json\n{_pretty(resolved.node.to_builder_dict())}\n```").classes("w-full")


def main(*, port: int = 8080, host: str | None = None, reload: bool = False):
    ui.run(root=build_ui, port=port, host=host, reload=reload)


if __name__ in {"__main__", "__mp_main__"}:
    main()

