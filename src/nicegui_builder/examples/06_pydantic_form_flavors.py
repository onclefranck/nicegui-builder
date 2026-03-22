"""A tasting flight of form flavors for the festival committee.

The committee asked for "one small preview".
It then requested five personalities for the same administrative chaos.
"""

from datetime import datetime

from nicegui import ui

from nicegui_builder import form
from nicegui_builder.examples.models import Contest, Participant, Registration


def _sample_participant() -> Participant:
    return Participant(
        display_name="Mira the Unmatched",
        email="mira@example.com",
        mismatch_level=9,
        returning_legend=True,
        emergency_note="Prefers applause before any sock-related questioning.",
    )


def _sample_contest() -> Contest:
    return Contest(
        title="Midnight Parade of Respectable Nonsense",
        starts_at=datetime(2026, 6, 12, 21, 15),
        duration_minutes=45,
        master_of_ceremonies="Gordon Bellringer",
    )


def _sample_registration() -> Registration:
    return Registration(
        participant_name="Mira the Unmatched",
        contest_title="Midnight Parade of Respectable Nonsense",
        notes="Arrives with excellent posture and deeply questionable hosiery.",
    )


def _section(title: str, description: str):
    with ui.card().classes("w-full gap-2"):
        ui.label(title).classes("text-h6")
        ui.label(description).classes("text-body2 text-grey-7")
        return ui.column().classes("w-full gap-3")


def build_ui():
    ui.label("Automatic Pydantic form flavors").classes("text-h5")
    ui.label(
        "Because the Festival of Mismatched Socks deserves both dignity and options."
    ).classes("text-body2 text-grey-7")

    with ui.column().classes("w-full max-w-5xl mx-auto gap-4"):
        with _section(
            "Standard flavor",
            "The default layout is calm, practical, and only mildly suspicious.",
        ):
            form(Participant)

        with _section(
            "Compact flavor",
            "Useful when the registration desk is small and the gossip is large.",
        ):
            form(Participant, flavor="compact")

        with _section(
            "Detail flavor",
            "A read-only view for moments when the committee wants facts, not improvisation.",
        ):
            form(_sample_contest(), flavor="detail")

        with _section(
            "Filters flavor",
            "For when the desk staff wants search boxes instead of philosophical commitment.",
        ):
            form(Registration, flavor="filters")

        with _section(
            "Actionable flavor",
            "Built-in status, actions, and a pleasant sense of administrative authority.",
        ):
            handle = form(_sample_participant(), flavor="actionable")
            handle.action_bar(
                "Save participant",
                lambda model: ui.notify(f"Saved {model.display_name}"),
                as_model=True,
                live_changed_badge=True,
                live_submit_button=True,
                live_reset_button=True,
                show_when_clean=True,
            )
            handle.live_error_panel(as_model=True, strategy="invalid")


def main(*, port: int = 8080, host: str | None = None, reload: bool = False):
    ui.run(root=build_ui, port=port, host=host, reload=reload)


if __name__ in {"__main__", "__mp_main__"}:
    main()
