"""A tiny welcome panel for the Festival of Mismatched Socks.

The organizing committee wanted something elegant.
What they got is a banner, a slogan, and alarming confidence.
"""

from nicegui import ui

from nicegui_builder import builder


LAYOUT = [
    {
        "card.tight": {
            "classes": "w-full max-w-xl mx-auto p-4 gap-2",
            "children": [
                {
                    "label": {
                        "params": {"text": "Festival of Mismatched Socks"},
                        "classes": "text-h5",
                    }
                },
                {
                    "label": {
                        "params": {
                            "text": "Three days of applause, confusion, and highly decorative laundry decisions."
                        },
                        "classes": "text-body2 text-grey-7",
                    }
                },
            ],
        }
    }
]


def build_ui():
    builder(LAYOUT)


def main(*, port: int = 8080, host: str | None = None, reload: bool = False):
    ui.run(root=build_ui, port=port, host=host, reload=reload)


if __name__ in {"__main__", "__mp_main__"}:
    main()
