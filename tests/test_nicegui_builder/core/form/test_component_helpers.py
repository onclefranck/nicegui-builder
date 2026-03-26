from datetime import date, datetime, time

from nicegui_builder.core.datetime_inputs import DateTimeInput
from nicegui_builder.core.form import (
    bind_component_event,
    clear_component_error,
    get_component_value,
    resolve_live_strategy,
    set_component_color,
    set_component_enabled,
    set_component_error,
    set_component_text,
    set_component_value,
    set_component_visibility,
)
from nicegui_builder.core.form import FormHandle
from nicegui_builder.core.models import FieldSpec

from .support import FakeBadge, FakeButton, ValueComponent, TextComponent


def test_get_component_value_uses_value_first():
    assert get_component_value(ValueComponent("hello")) == "hello"


def test_get_component_value_falls_back_to_text():
    assert get_component_value(TextComponent("readonly")) == "readonly"


def test_get_component_value_returns_none_for_unknown_component():
    assert get_component_value(object()) is None


def test_set_component_value_updates_value_components():
    component = ValueComponent("before")

    result = set_component_value(component, "after")

    assert result == "after"
    assert component.value == "after"


def test_set_component_value_handles_none_text_and_unknown_components():
    text_component = TextComponent("before")
    plain_value_component = type("PlainValueComponent", (), {"value": "before"})()

    assert set_component_value(None, "after") is None
    assert set_component_value(text_component, None) == ""
    assert text_component.text == ""
    assert set_component_value(plain_value_component, "after") == "after"
    assert plain_value_component.value == "after"
    assert set_component_value(object(), "after") is None


def test_set_and_clear_component_error_updates_component_state():
    component = ValueComponent("Ada")

    set_component_error(component, "Invalid value")
    assert component.error == "Invalid value"
    assert component.error_message == "Invalid value"

    clear_component_error(component)
    assert component.error is None
    assert component.error_message is None


def test_component_error_helpers_handle_none_and_plain_objects():
    component = type("ErrorComponent", (), {"error": "old", "error_message": "old"})()

    assert set_component_error(None, "Invalid") is None
    assert set_component_error(component, "Invalid") == "Invalid"
    assert component.error == "Invalid"
    assert component.error_message == "Invalid"
    assert clear_component_error(component) is None
    assert component.error is None
    assert component.error_message is None


def test_component_helpers_update_badge_like_components():
    badge = FakeBadge("before", color="positive")

    set_component_text(badge, "after")
    set_component_color(badge, "warning")
    set_component_visibility(badge, False)

    assert badge.text == "after"
    assert badge.color == "warning"
    assert badge.visible is False


def test_component_helpers_handle_plain_attribute_and_unknown_objects():
    plain = type("PlainComponent", (), {"text": "before", "visible": True, "color": "positive", "enabled": True})()

    assert set_component_text(None, "after") is None
    assert set_component_visibility(None, False) is None
    assert set_component_color(None, "warning") is None
    assert set_component_enabled(None, False) is None

    assert set_component_text(plain, "after") == "after"
    assert set_component_visibility(plain, False) is False
    assert set_component_color(plain, "warning") == "warning"
    assert set_component_enabled(plain, False) == False

    assert plain.text == "after"
    assert plain.visible is False
    assert plain.color == "warning"
    assert plain.enabled is False

    assert set_component_text(object(), "x") is None
    assert set_component_visibility(object(), True) is None
    assert set_component_color(object(), "x") is None
    assert set_component_enabled(object(), True) is None


def test_component_helper_updates_button_enabled_state():
    button = FakeButton("Save")

    set_component_enabled(button, False)

    assert button.enabled is False


def test_value_component_can_register_change_callbacks():
    component = ValueComponent("Ada")
    calls = []

    component.on_value_change(lambda: calls.append("changed"))
    component.emit_value_change()

    assert calls == ["changed"]


def test_bind_component_event_supports_blur():
    component = ValueComponent("Ada")
    calls = []

    assert bind_component_event(component, lambda: calls.append("blurred"), event="blur") is True

    component.emit("blur")

    assert calls == ["blurred"]


def test_bind_component_event_supports_on_change_and_on_blur_helpers():
    calls = []

    class EventComponent:
        def __init__(self):
            self.change_callback = None
            self.blur_callback = None

        def on_change(self, callback):
            self.change_callback = callback
            return callback

        def on_blur(self, callback):
            self.blur_callback = callback
            return callback

    component = EventComponent()

    assert bind_component_event(component, lambda: calls.append("changed"), event="change") is True
    assert bind_component_event(component, lambda: calls.append("blurred"), event="blur") is True

    component.change_callback()
    component.blur_callback()

    assert calls == ["changed", "blurred"]


def test_bind_component_event_supports_generic_on_for_change():
    calls = []

    class OnOnlyComponent:
        def __init__(self):
            self.callbacks = {}

        def on(self, event, callback):
            self.callbacks[event] = callback
            return callback

        def emit(self, event):
            self.callbacks[event]()

    component = OnOnlyComponent()

    assert bind_component_event(component, lambda: calls.append("changed"), event="change") is True

    component.emit("change")

    assert calls == ["changed"]


def test_bind_component_event_returns_false_or_raises_for_unsupported_cases():
    assert bind_component_event(None, lambda: None, event="change") is False
    assert bind_component_event(object(), lambda: None, event="change") is False
    assert bind_component_event(object(), lambda: None, event="blur") is False

    try:
        bind_component_event(object(), lambda: None, event="submit")
    except ValueError as exc:
        assert "change" in str(exc)
    else:
        raise AssertionError("bind_component_event should reject unsupported event names")


def test_resolve_live_strategy_supports_named_modes_and_callables():
    handle = FormHandle(
        source_class=dict,
        field_specs=[FieldSpec(name="name", python_type=str, default="Ada")],
        component_refs={"field:name": ValueComponent("Grace")},
    )

    assert resolve_live_strategy("always", handle) is True
    assert resolve_live_strategy("dirty", handle) is True
    assert resolve_live_strategy("clean", handle) is False
    assert resolve_live_strategy(lambda form_handle: form_handle.is_dirty(), handle) is True


def test_resolve_live_strategy_supports_validation_modes_and_errors():
    class FakeHandle:
        def __init__(self, *, dirty, valid):
            self._dirty = dirty
            self._valid = valid

        def is_dirty(self):
            return self._dirty

        def validate(self, as_model=False):
            return type("Result", (), {"valid": self._valid})()

    valid_handle = FakeHandle(dirty=True, valid=True)
    invalid_handle = FakeHandle(dirty=False, valid=False)

    assert resolve_live_strategy(None, valid_handle, fallback=False) is False
    assert resolve_live_strategy("never", valid_handle) is False
    assert resolve_live_strategy("valid", valid_handle) is True
    assert resolve_live_strategy("invalid", invalid_handle) is True
    assert resolve_live_strategy("dirty_and_valid", valid_handle) is True
    assert resolve_live_strategy("dirty_or_valid", invalid_handle) is False

    try:
        resolve_live_strategy("mystery", valid_handle)
    except ValueError as exc:
        assert "strategy must be" in str(exc)
    else:
        raise AssertionError("resolve_live_strategy should reject unsupported names")


def test_datetime_helpers_cover_string_parsing_and_formatting():
    assert DateTimeInput.time_to_string("14:30") == "14:30"
    assert DateTimeInput.time_to_string(time(14, 30)) == "14:30"
    assert DateTimeInput.time_to_string(time(14, 30, 45)) == "14:30:45"
    assert DateTimeInput.time_to_string(time(14, 30, 45, 123456)) == "14:30:45.123456"

    assert DateTimeInput.split_value(None) == (None, None)
    assert DateTimeInput.split_value("") == (None, None)
    assert DateTimeInput.split_value(datetime(2026, 3, 21, 14, 30)) == ("2026-03-21", "14:30")
    assert DateTimeInput.split_value(date(2026, 3, 21)) == ("2026-03-21", None)
    assert DateTimeInput.split_value("2026-03-21T14:30") == ("2026-03-21", "14:30")
    assert DateTimeInput.split_value("2026-03-21 14:30") == ("2026-03-21", "14:30")
    assert DateTimeInput.split_value("   ") == (None, None)
    assert DateTimeInput.split_value("2026-03-21Tparty-time") == ("2026-03-21", "party-time")
    assert DateTimeInput.split_value("2026-03-21T14:30Z") == ("2026-03-21", "14:30")
    assert DateTimeInput.split_value("2026-03-21 only-date") == ("2026-03-21", "only-date")
    assert DateTimeInput.split_value("nonsense") == ("nonsense", None)
    assert DateTimeInput.split_value(123) == ("123", None)

    assert DateTimeInput.combine_value(None, None) is None
    assert DateTimeInput.combine_value(None, "14:30") == "14:30"
    assert DateTimeInput.combine_value("2026-03-21", None) == "2026-03-21"
    assert DateTimeInput.combine_value("2026-03-21", "14:30") == "2026-03-21T14:30"
