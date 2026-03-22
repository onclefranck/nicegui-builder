from .models import ActionSpec


FORM_ACTION_SPECS = {
    "create": ActionSpec(name="create", label="Create", intent="primary", strategy="valid"),
    "update": ActionSpec(
        name="update",
        label="Update",
        intent="primary",
        strategy="dirty_and_valid",
    ),
    "delete": ActionSpec(name="delete", label="Delete", intent="negative", strategy="always"),
    "reset": ActionSpec(name="reset", label="Reset", intent="secondary", strategy="dirty"),
}


TABLE_ACTION_SPECS = {
    "create": ActionSpec(name="create", label="Create", intent="primary"),
    "delete_selected": ActionSpec(
        name="delete_selected",
        label="Delete selected",
        intent="negative",
        strategy="always",
    ),
    "export": ActionSpec(name="export", label="Export CSV", intent="secondary"),
}


def get_action_spec(specs: dict[str, ActionSpec], name: str) -> ActionSpec:
    if name not in specs:
        raise KeyError(name)
    return specs[name]


def apply_action_intent(spec: ActionSpec, button_kwargs: dict) -> dict:
    button_kwargs.setdefault("color", spec.intent)
    return button_kwargs
