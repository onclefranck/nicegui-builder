"""Forcing widget variants when the defaults are not theatrical enough.

The plugin has sensible defaults.
The festival committee occasionally has stronger feelings.
"""

from enum import Enum
from typing import Literal

from nicegui import ui
from pydantic import BaseModel, Field

import nicegui_builder


class SockMood(str, Enum):
    OPTIMISTIC = "Optimistic"
    CONCERNED = "Concerned"
    OPERATIC = "Operatic"


class VariantShowcase(BaseModel):
    secret_code: str = Field(
        default="left-sock-supremacy",
        title="Secret code",
        description="A password-like value the desk should probably not shout aloud.",
    )
    committee_notes: str = Field(
        default="Please applaud before opening any suspicious duffel bag of socks.",
        title="Committee notes",
        description="Long text is a fine excuse for a textarea.",
        max_length=240,
    )
    sock_mood: SockMood = Field(
        default=SockMood.CONCERNED,
        title="Sock mood",
        description="Enums can be rendered as radios when the mood is specific enough.",
    )
    attendee_lookup: str = Field(
        default="",
        title="Attendee lookup",
        description="A search-style field is useful when the line gets dramatic.",
    )
    applause_policy: Literal["Polite", "Enthusiastic", "Alarmingly sincere"] = Field(
        default="Enthusiastic",
        title="Applause policy",
    )


def build_ui():
    ui.label("Pydantic field variants").classes("text-h5")
    ui.label(
        "Here the layout explicitly requests widget variants instead of relying on the plugin defaults."
    ).classes("text-body2 text-grey-7")

    handle = ui.form_builder(VariantShowcase, flavor="actionable")
    handle.set_values(
        {
            "secret_code": "velvet-ankle-42",
            "committee_notes": "Use the gold clipboard only for emotionally significant registrations.",
            "attendee_lookup": "Mira",
        }
    )

    ui.separator()
    ui.markdown(
        """```yaml
- grid:
    params:
      columns: 12
    children:
    - field__secret_code:
        methods: password
    - field__committee_notes:
        methods: textarea
    - field__sock_mood:
        methods: radio
    - field__attendee_lookup:
        methods: search
    - field__applause_policy:
        methods: radio
```"""
    ).classes("w-full max-w-4xl")


def main(*, port: int = 8080, host: str | None = None, reload: bool = False):
    ui.run(root=build_ui, port=port, host=host, reload=reload)


if __name__ in {"__main__", "__mp_main__"}:
    main()

