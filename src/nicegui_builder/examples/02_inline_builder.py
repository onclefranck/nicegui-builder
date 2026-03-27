"""A builder example without any YAML file at all.

Sometimes the committee wants a declarative layout,
but also wants it immediately and with suspicious confidence.
"""

from nicegui import ui

import nicegui_builder


LAYOUT = [
    {
        "card.tight": {
            "classes": "w-full max-w-xl mx-auto p-4 gap-3",
            "children": [
                {
                    "label": {
                        "params": {"text": "Inline builder example"},
                        "classes": "text-h5",
                    }
                },
                {
                    "label": {
                        "params": {
                            "text": "This layout lives directly in Python, which pleased the committee far more than it should have."
                        },
                        "classes": "text-body2 text-grey-7",
                    }
                },
                {
                    "row": {
                        "classes": "items-center gap-2",
                        "children": [
                            {
                                "badge": {
                                    "params": {"text": "Inline"},
                                    "props": "color=primary",
                                }
                            },
                            {
                                "badge": {
                                    "params": {"text": "No YAML harmed"},
                                    "props": "color=positive",
                                }
                            },
                        ],
                    }
                },
            ],
        }
    }
]


def build_ui():
    ui.builder(LAYOUT)


def main(*, port: int = 8080, host: str | None = None, reload: bool = False):
    ui.run(root=build_ui, port=port, host=host, reload=reload)


if __name__ in {"__main__", "__mp_main__"}:
    main()
