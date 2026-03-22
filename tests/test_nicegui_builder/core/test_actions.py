import pytest

from nicegui_builder.core.actions import (
    FORM_ACTION_SPECS,
    TABLE_ACTION_SPECS,
    apply_action_intent,
    get_action_spec,
)


def test_get_action_spec_returns_registered_spec():
    spec = get_action_spec(FORM_ACTION_SPECS, "create")

    assert spec.name == "create"
    assert spec.label == "Create"


def test_get_action_spec_raises_for_unknown_name():
    with pytest.raises(KeyError):
        get_action_spec(TABLE_ACTION_SPECS, "missing")


def test_apply_action_intent_sets_default_color_only_when_missing():
    button_kwargs = {}
    apply_action_intent(FORM_ACTION_SPECS["delete"], button_kwargs)

    assert button_kwargs["color"] == "negative"

    preserved = {"color": "custom"}
    apply_action_intent(FORM_ACTION_SPECS["delete"], preserved)

    assert preserved["color"] == "custom"
