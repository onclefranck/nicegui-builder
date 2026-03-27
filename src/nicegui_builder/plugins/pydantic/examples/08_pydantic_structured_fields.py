"""Structured fields, nested models, and a little controlled complexity.

The festival keeps insisting that sock logistics are simple.
This example documents the evidence to the contrary.
"""

from nicegui import ui
from pydantic import BaseModel, Field

import nicegui_builder


class SupplyCrate(BaseModel):
    label: str = Field(default="Backstage crate", title="Crate label")
    sock_count: int = Field(default=24, title="Sock count", ge=0)


class ParadePlan(BaseModel):
    lead_marshals: list[str] = Field(
        default=["Mira the Unmatched", "Gordon Bellringer"],
        title="Lead marshals",
    )
    emergency_items: list[str] = Field(
        default=["Spare ribbon", "Backup whistle", "Emotionally supportive clipboard"],
        title="Emergency items",
    )
    supply_crate: SupplyCrate = Field(
        default_factory=SupplyCrate,
        title="Supply crate",
    )
    announcement_notes: dict[str, str] = Field(
        default={
            "opening": "Welcome, brave wearers of asymmetry.",
            "closing": "Please retrieve only the socks you recognize emotionally.",
        },
        title="Announcement notes",
    )


def build_ui():
    ui.label("Structured Pydantic fields").classes("text-h5")
    ui.label(
        "Nested models, lists, and dict-like values are grouped into their own generated sections."
    ).classes("text-body2 text-grey-7")

    handle = ui.form_builder(ParadePlan())

    with ui.row().classes("gap-2"):
        ui.button(
            "Show collected values",
            on_click=lambda: ui.notify(str(handle.get_values())),
        )
        ui.button(
            "Show rebuilt model",
            on_click=lambda: ui.notify(str(handle.to_model())),
        )


def main(*, port: int = 8080, host: str | None = None, reload: bool = False):
    ui.run(root=build_ui, port=port, host=host, reload=reload)


if __name__ in {"__main__", "__mp_main__"}:
    main()
