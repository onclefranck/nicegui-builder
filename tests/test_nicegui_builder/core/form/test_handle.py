from datetime import datetime
import types

from nicegui_builder import ViewHandle
from nicegui_builder.core.form import FormHandle, FormValidationResult
from nicegui_builder.core.models import FieldSpec

from .support import (
    DemoDateTimeModel,
    DemoModel,
    FakeBadge,
    FakeButton,
    FakeContext,
    FakeLabel,
    ValueComponent,
)


def test_form_handle_inherits_common_view_description():
    handle = FormHandle(
        source_class=DemoModel,
        field_specs=[FieldSpec(name="name", python_type=str, default="Ada")],
        component_refs={"field:name": ValueComponent("Ada")},
        source_instance=DemoModel(name="Ada", age=20),
    )

    description = handle.describe()

    assert description["handle_type"] == "FormHandle"
    assert description["spec_type"] == "FormSpec"


def test_form_handle_reuses_and_syncs_internal_form_state():
    handle = FormHandle(
        source_class=DemoModel,
        field_specs=[FieldSpec(name="name", python_type=str, default="Ada")],
        component_refs={"field:name": ValueComponent("Ada")},
        source_instance=DemoModel(name="Ada", age=20),
    )

    assert isinstance(handle, ViewHandle)
    first_state = handle.state
    handle.source_instance = DemoModel(name="Grace", age=30)
    second_state = handle.state

    assert first_state is second_state
    assert second_state.source_instance.name == "Grace"


def test_form_handle_exposes_and_syncs_form_spec():
    handle = FormHandle(
        source_class=DemoModel,
        field_specs=[FieldSpec(name="name", python_type=str, default="Ada")],
        component_refs={"field:name": ValueComponent("Ada")},
        source_instance=DemoModel(name="Ada", age=20),
    )

    first_spec = handle.spec
    handle.source_instance = DemoModel(name="Grace", age=30)
    second_spec = handle.spec

    assert first_spec is second_spec
    assert handle.form_spec is second_spec
    assert second_spec.source_class is DemoModel
    assert second_spec.field_specs == handle.field_specs
    assert second_spec.source_instance.name == "Grace"


def test_form_handle_collects_values_from_component_refs():
    handle = FormHandle(
        source_class=dict,
        field_specs=[
            FieldSpec(name="name", python_type=str),
            FieldSpec(name="age", python_type=int),
        ],
        component_refs={
            "field:name": ValueComponent("Ada"),
            "field:age": ValueComponent(37),
        },
    )

    assert handle.get_values() == {"name": "Ada", "age": 37}


def test_form_handle_can_collect_split_datetime_field_values():
    handle = FormHandle(
        source_class=DemoDateTimeModel,
        field_specs=[FieldSpec(name="starts_at", python_type=datetime)],
        component_refs={
            "field:starts_at:date": ValueComponent("2026-03-21"),
            "field:starts_at:time": ValueComponent("14:30"),
        },
    )

    assert handle.get_values() == {"starts_at": "2026-03-21T14:30"}


def test_form_handle_can_set_split_datetime_field_values():
    date_component = ValueComponent(None)
    time_component = ValueComponent(None)
    handle = FormHandle(
        source_class=DemoDateTimeModel,
        field_specs=[FieldSpec(name="starts_at", python_type=datetime)],
        component_refs={
            "field:starts_at:date": date_component,
            "field:starts_at:time": time_component,
        },
    )

    handle.set_values({"starts_at": datetime(2026, 3, 21, 14, 30)})

    assert date_component.value == "2026-03-21"
    assert time_component.value == "14:30"


def test_form_handle_to_model_builds_pydantic_instance():
    handle = FormHandle(
        source_class=DemoModel,
        field_specs=[
            FieldSpec(name="name", python_type=str, default="Ada"),
            FieldSpec(name="age", python_type=int, default=37),
        ],
        component_refs={
            "field:name": ValueComponent("Ada"),
            "field:age": ValueComponent(37),
        },
    )

    model = handle.to_model()

    assert isinstance(model, DemoModel)
    assert model.name == "Ada"
    assert model.age == 37


def test_form_handle_to_model_merges_with_source_instance():
    handle = FormHandle(
        source_class=DemoModel,
        field_specs=[
            FieldSpec(name="name", python_type=str),
            FieldSpec(name="age", python_type=int),
        ],
        component_refs={
            "field:name": ValueComponent("Grace"),
            "field:age": ValueComponent(37),
        },
        source_instance=DemoModel(name="Ada", age=20),
    )

    model = handle.to_model()

    assert model.name == "Grace"
    assert model.age == 37


def test_form_handle_submit_passes_values_to_callback():
    handle = FormHandle(
        source_class=dict,
        field_specs=[
            FieldSpec(name="name", python_type=str),
            FieldSpec(name="age", python_type=int),
        ],
        component_refs={
            "field:name": ValueComponent("Ada"),
            "field:age": ValueComponent(37),
        },
    )

    received = []

    result = handle.submit(lambda payload: received.append(payload) or "done")

    assert result == "done"
    assert received == [{"name": "Ada", "age": 37}]


def test_form_handle_submit_can_pass_model():
    handle = FormHandle(
        source_class=DemoModel,
        field_specs=[
            FieldSpec(name="name", python_type=str, default="Ada"),
            FieldSpec(name="age", python_type=int, default=37),
        ],
        component_refs={
            "field:name": ValueComponent("Ada"),
            "field:age": ValueComponent(37),
        },
    )

    received = []

    handle.submit(lambda payload: received.append(payload), as_model=True)

    assert isinstance(received[0], DemoModel)
    assert received[0].name == "Ada"
    assert received[0].age == 37


def test_form_handle_validate_returns_success_for_model():
    handle = FormHandle(
        source_class=DemoModel,
        field_specs=[
            FieldSpec(name="name", python_type=str),
            FieldSpec(name="age", python_type=int),
        ],
        component_refs={
            "field:name": ValueComponent("Ada"),
            "field:age": ValueComponent(37),
        },
    )

    validation = handle.validate(as_model=True)

    assert isinstance(validation, FormValidationResult)
    assert validation.valid is True
    assert isinstance(validation.payload, DemoModel)
    assert validation.error is None


def test_form_handle_validate_returns_error_for_invalid_model():
    handle = FormHandle(
        source_class=DemoModel,
        field_specs=[
            FieldSpec(name="name", python_type=str),
            FieldSpec(name="age", python_type=int),
        ],
        component_refs={
            "field:name": ValueComponent("Ada"),
            "field:age": ValueComponent("not-an-int"),
        },
    )

    validation = handle.validate(as_model=True)

    assert validation.valid is False
    assert validation.payload is None
    assert validation.error is not None


def test_form_handle_submit_uses_on_error_for_invalid_model():
    handle = FormHandle(
        source_class=DemoModel,
        field_specs=[
            FieldSpec(name="name", python_type=str),
            FieldSpec(name="age", python_type=int),
        ],
        component_refs={
            "field:name": ValueComponent("Ada"),
            "field:age": ValueComponent("not-an-int"),
        },
    )

    result = handle.submit(
        lambda payload: payload,
        as_model=True,
        on_error=lambda error: str(type(error).__name__),
    )

    assert result == "ValidationError"


def test_form_handle_submit_raises_when_invalid_and_no_on_error():
    handle = FormHandle(
        source_class=DemoModel,
        field_specs=[
            FieldSpec(name="name", python_type=str),
            FieldSpec(name="age", python_type=int),
        ],
        component_refs={
            "field:name": ValueComponent("Ada"),
            "field:age": ValueComponent("not-an-int"),
        },
    )

    try:
        handle.submit(lambda payload: payload, as_model=True)
    except Exception as exc:
        assert type(exc).__name__ == "ValidationError"
    else:
        raise AssertionError("submit should raise when invalid and no on_error is provided")


def test_form_handle_submit_can_apply_field_errors_on_invalid_model():
    age_component = ValueComponent("not-an-int")
    handle = FormHandle(
        source_class=DemoModel,
        field_specs=[
            FieldSpec(name="name", python_type=str),
            FieldSpec(name="age", python_type=int),
        ],
        component_refs={
            "field:name": ValueComponent("Ada"),
            "field:age": age_component,
        },
    )

    result = handle.submit(
        lambda payload: payload,
        as_model=True,
        apply_errors=True,
        on_error=lambda error: type(error).__name__,
    )

    assert result == "ValidationError"
    assert age_component.error is not None


def test_form_validation_result_exposes_field_errors():
    handle = FormHandle(
        source_class=DemoModel,
        field_specs=[
            FieldSpec(name="name", python_type=str),
            FieldSpec(name="age", python_type=int),
        ],
        component_refs={
            "field:name": ValueComponent("Ada"),
            "field:age": ValueComponent("not-an-int"),
        },
    )

    validation = handle.validate(as_model=True)

    errors = validation.errors_by_field()
    assert "age" in errors
    assert errors["age"]


def test_form_validation_result_handles_non_validation_exceptions():
    validation = FormValidationResult(valid=False, payload=None, error=RuntimeError("boom"))

    assert validation.errors_by_field() == {"__root__": ["boom"]}
    assert validation.error_messages() == ["boom"]


def test_form_validation_result_handles_non_tuple_locations():
    class FakeError:
        def errors(self):
            return [{"loc": "age", "msg": "Invalid value"}]

    validation = FormValidationResult(valid=False, payload=None, error=FakeError())

    assert validation.errors_by_field() == {"age": ["Invalid value"]}
    assert validation.error_messages() == ["age: Invalid value"]


def test_form_handle_error_helpers_proxy_validation_errors():
    handle = FormHandle(
        source_class=DemoModel,
        field_specs=[
            FieldSpec(name="name", python_type=str),
            FieldSpec(name="age", python_type=int),
        ],
        component_refs={
            "field:name": ValueComponent("Ada"),
            "field:age": ValueComponent("not-an-int"),
        },
    )

    errors = handle.errors(as_model=True)
    messages = handle.error_messages(as_model=True)

    assert "age" in errors
    assert any(message.startswith("age:") for message in messages)


def test_form_handle_can_return_field_specific_validation_messages():
    handle = FormHandle(
        source_class=DemoModel,
        field_specs=[
            FieldSpec(name="name", python_type=str),
            FieldSpec(name="age", python_type=int),
        ],
        component_refs={
            "field:name": ValueComponent("Ada"),
            "field:age": ValueComponent("not-an-int"),
        },
    )

    assert handle.validate_field("age", as_model=True)
    assert handle.field_error_message("age", as_model=True) is not None


def test_form_handle_apply_errors_sets_field_level_component_errors():
    name_component = ValueComponent("Ada")
    age_component = ValueComponent("not-an-int")
    handle = FormHandle(
        source_class=DemoModel,
        field_specs=[
            FieldSpec(name="name", python_type=str),
            FieldSpec(name="age", python_type=int),
        ],
        component_refs={
            "field:name": name_component,
            "field:age": age_component,
        },
    )

    validation = handle.apply_errors(as_model=True)

    assert validation.valid is False
    assert name_component.error is None
    assert age_component.error is not None


def test_form_handle_apply_field_errors_returns_none_for_valid_or_unknown_field():
    handle = FormHandle(
        source_class=DemoModel,
        field_specs=[
            FieldSpec(name="name", python_type=str),
            FieldSpec(name="age", python_type=int),
        ],
        component_refs={
            "field:name": ValueComponent("Ada"),
            "field:age": ValueComponent(37),
        },
    )

    assert handle.field_error_message("name", as_model=True) is None
    assert handle.apply_field_errors("name", as_model=True) is None
    assert handle.apply_field_errors("missing", as_model=True) is None


def test_form_handle_clear_errors_clears_existing_field_errors():
    name_component = ValueComponent("Ada")
    age_component = ValueComponent("not-an-int")
    name_component.error = "old"
    age_component.error = "old"
    handle = FormHandle(
        source_class=DemoModel,
        field_specs=[
            FieldSpec(name="name", python_type=str),
            FieldSpec(name="age", python_type=int),
        ],
        component_refs={
            "field:name": name_component,
            "field:age": age_component,
        },
    )

    handle.clear_errors()

    assert name_component.error is None
    assert age_component.error is None


def test_form_handle_set_values_updates_existing_components():
    handle = FormHandle(
        source_class=dict,
        field_specs=[
            FieldSpec(name="name", python_type=str),
            FieldSpec(name="age", python_type=int),
        ],
        component_refs={
            "field:name": ValueComponent("Ada"),
            "field:age": ValueComponent(37),
        },
    )

    handle.set_values({"name": "Grace", "age": 42})

    assert handle.get_values() == {"name": "Grace", "age": 42}


def test_form_handle_set_values_ignores_missing_fields():
    age_component = ValueComponent(37)
    handle = FormHandle(
        source_class=dict,
        field_specs=[
            FieldSpec(name="name", python_type=str),
            FieldSpec(name="age", python_type=int),
        ],
        component_refs={
            "field:name": ValueComponent("Ada"),
            "field:age": age_component,
        },
    )

    handle.set_values({"name": "Grace"})

    assert handle.get_values() == {"name": "Grace", "age": 37}


def test_form_handle_changed_fields_uses_defaults_as_baseline():
    handle = FormHandle(
        source_class=dict,
        field_specs=[
            FieldSpec(name="name", python_type=str, default="Ada"),
            FieldSpec(name="age", python_type=int, default=20),
        ],
        component_refs={
            "field:name": ValueComponent("Grace"),
            "field:age": ValueComponent(20),
        },
    )

    assert handle.changed_fields() == {
        "name": {"from": "Ada", "to": "Grace"},
    }
    assert handle.is_dirty() is True


def test_form_handle_changed_fields_uses_source_instance_as_baseline():
    handle = FormHandle(
        source_class=DemoModel,
        field_specs=[
            FieldSpec(name="name", python_type=str, default="Default"),
            FieldSpec(name="age", python_type=int, default=0),
        ],
        component_refs={
            "field:name": ValueComponent("Ada"),
            "field:age": ValueComponent(42),
        },
        source_instance=DemoModel(name="Ada", age=20),
    )

    assert handle.changed_fields() == {
        "age": {"from": 20, "to": 42},
    }
    assert handle.is_dirty() is True


def test_form_handle_reset_to_defaults_uses_field_defaults():
    handle = FormHandle(
        source_class=dict,
        field_specs=[
            FieldSpec(name="name", python_type=str, default="Ada"),
            FieldSpec(name="age", python_type=int, default=20),
        ],
        component_refs={
            "field:name": ValueComponent("Grace"),
            "field:age": ValueComponent(42),
        },
    )

    handle.reset_to_defaults()

    assert handle.get_values() == {"name": "Ada", "age": 20}


def test_form_handle_reset_to_source_uses_source_instance_values():
    handle = FormHandle(
        source_class=DemoModel,
        field_specs=[
            FieldSpec(name="name", python_type=str, default="Default"),
            FieldSpec(name="age", python_type=int, default=0),
        ],
        component_refs={
            "field:name": ValueComponent("Changed"),
            "field:age": ValueComponent(42),
        },
        source_instance=DemoModel(name="Ada", age=20),
    )

    handle.reset_to_source()

    assert handle.get_values() == {"name": "Ada", "age": 20}


def test_form_handle_reset_to_empty_clears_values_with_simple_empty_state():
    handle = FormHandle(
        source_class=dict,
        field_specs=[
            FieldSpec(name="name", python_type=str),
            FieldSpec(name="enabled", python_type=bool),
            FieldSpec(name="age", python_type=int),
        ],
        component_refs={
            "field:name": ValueComponent("Ada"),
            "field:enabled": ValueComponent(True),
            "field:age": ValueComponent(37),
        },
    )

    handle.reset_to_empty()

    assert handle.get_values() == {"name": "", "enabled": False, "age": None}


def test_form_handle_submit_button_wires_callback(monkeypatch):
    handle = FormHandle(
        source_class=dict,
        field_specs=[FieldSpec(name="name", python_type=str)],
        component_refs={"field:name": ValueComponent("Ada")},
    )

    created = {}

    def fake_button(label, on_click=None, **kwargs):
        button = FakeButton(label, on_click=on_click, **kwargs)
        created["button"] = button
        return button

    monkeypatch.setattr("nicegui_builder.core.form.ui.button", fake_button)

    received = []
    button = handle.submit_button("Save", lambda payload: received.append(payload), color="primary")
    button.on_click()

    assert button.label == "Save"
    assert button.kwargs["color"] == "primary"
    assert received == [{"name": "Ada"}]


def test_form_handle_crud_bar_builds_standard_actions(monkeypatch):
    handle = FormHandle(
        source_class=DemoModel,
        field_specs=[
            FieldSpec(name="name", python_type=str),
            FieldSpec(name="age", python_type=int),
        ],
        component_refs={
            "field:name": ValueComponent("Ada"),
            "field:age": ValueComponent(37),
        },
        source_instance=DemoModel(name="Ada", age=20),
    )

    monkeypatch.setattr(
        "nicegui_builder.core.form.ui.button",
        lambda label, on_click=None, **kwargs: FakeButton(label, on_click=on_click, **kwargs),
    )

    created = []
    updated = []
    deleted = []
    reset_called = []

    parts = handle.crud_bar(
        on_create=lambda model: created.append(model),
        on_update=lambda model: updated.append(model),
        on_delete=lambda instance: deleted.append(instance),
        on_reset=lambda form: reset_called.append(form),
    )

    assert parts["create"] is not None
    assert parts["update"] is not None
    assert parts["delete"] is not None
    assert parts["reset"] is not None

    parts["create"].button.on_click()
    parts["update"].button.on_click()
    parts["delete"].on_click()
    parts["reset"].on_click()

    assert created and isinstance(created[0], DemoModel)
    assert updated and isinstance(updated[0], DemoModel)
    assert deleted and isinstance(deleted[0], DemoModel)
    assert reset_called == [handle]


def test_form_handle_non_live_crud_buttons_use_submit_button_paths(monkeypatch):
    handle = FormHandle(
        source_class=DemoModel,
        field_specs=[
            FieldSpec(name="name", python_type=str),
            FieldSpec(name="age", python_type=int),
        ],
        component_refs={
            "field:name": ValueComponent("Ada"),
            "field:age": ValueComponent(37),
        },
        source_instance=DemoModel(name="Ada", age=20),
    )

    monkeypatch.setattr(
        "nicegui_builder.core.form.ui.button",
        lambda label, on_click=None, **kwargs: FakeButton(label, on_click=on_click, **kwargs),
    )

    created = []
    updated = []
    deleted = []

    create_button = handle.create_button(lambda model: created.append(model), live=False)
    update_button = handle.update_button(lambda model: updated.append(model), live=False)
    delete_button = handle.delete_button(lambda payload: deleted.append(payload), live=False, pass_source=False)

    create_button.on_click()
    update_button.on_click()
    delete_button.on_click()

    assert created and isinstance(created[0], DemoModel)
    assert updated and isinstance(updated[0], DemoModel)
    assert deleted == [{"name": "Ada", "age": 37}]


def test_form_handle_delete_button_can_use_live_submit_button(monkeypatch):
    handle = FormHandle(
        source_class=DemoModel,
        field_specs=[FieldSpec(name="name", python_type=str)],
        component_refs={"field:name": ValueComponent("Ada")},
        source_instance=DemoModel(name="Ada", age=20),
    )

    called = {}

    monkeypatch.setattr(
        FormHandle,
        "live_submit_button",
        lambda self, label, callback, **kwargs: called.setdefault(
            "binding",
            {"label": label, "callback": callback, "kwargs": kwargs},
        ),
    )

    binding = handle.delete_button(lambda payload: payload, live=True)

    assert binding is called["binding"]
    assert called["binding"]["label"] == "Delete"
    assert called["binding"]["kwargs"]["as_model"] is False


def test_form_handle_submit_button_can_apply_errors(monkeypatch):
    age_component = ValueComponent("not-an-int")
    handle = FormHandle(
        source_class=DemoModel,
        field_specs=[
            FieldSpec(name="name", python_type=str),
            FieldSpec(name="age", python_type=int),
        ],
        component_refs={
            "field:name": ValueComponent("Ada"),
            "field:age": age_component,
        },
    )

    def fake_button(label, on_click=None, **kwargs):
        return FakeButton(label, on_click=on_click, **kwargs)

    monkeypatch.setattr("nicegui_builder.core.form.ui.button", fake_button)

    button = handle.submit_button(
        "Save",
        lambda payload: payload,
        as_model=True,
        apply_errors=True,
        on_error=lambda error: type(error).__name__,
    )
    result = button.on_click()

    assert result == "ValidationError"
    assert age_component.error is not None


def test_form_handle_reset_button_resets_values(monkeypatch):
    handle = FormHandle(
        source_class=dict,
        field_specs=[
            FieldSpec(name="name", python_type=str, default="Ada"),
            FieldSpec(name="age", python_type=int, default=20),
        ],
        component_refs={
            "field:name": ValueComponent("Grace"),
            "field:age": ValueComponent(42),
        },
    )

    def fake_button(label, on_click=None, **kwargs):
        return FakeButton(label, on_click=on_click, **kwargs)

    monkeypatch.setattr("nicegui_builder.core.form.ui.button", fake_button)

    button = handle.reset_button("Reset", mode="defaults", color="secondary")
    result = button.on_click()

    assert button.label == "Reset"
    assert button.kwargs["color"] == "secondary"
    assert result is handle
    assert handle.get_values() == {"name": "Ada", "age": 20}


def test_form_handle_reset_button_can_invoke_callback(monkeypatch):
    handle = FormHandle(
        source_class=dict,
        field_specs=[FieldSpec(name="name", python_type=str, default="Ada")],
        component_refs={"field:name": ValueComponent("Grace")},
    )

    def fake_button(label, on_click=None, **kwargs):
        return FakeButton(label, on_click=on_click, **kwargs)

    monkeypatch.setattr("nicegui_builder.core.form.ui.button", fake_button)

    received = []
    button = handle.reset_button(
        on_reset=lambda form_handle: received.append(form_handle.get_values()) or "reset-done",
    )
    result = button.on_click()

    assert result == "reset-done"
    assert received == [{"name": "Ada"}]


def test_form_handle_reset_button_uses_actions_container(monkeypatch):
    bucket = []
    handle = FormHandle(
        source_class=dict,
        field_specs=[FieldSpec(name="name", python_type=str, default="Ada")],
        component_refs={
            "field:name": ValueComponent("Grace"),
            "form:actions": FakeContext("actions", bucket),
        },
    )

    def fake_button(label, on_click=None, **kwargs):
        bucket.append(("button", label))
        return FakeButton(label, on_click=on_click, **kwargs)

    monkeypatch.setattr("nicegui_builder.core.form.ui.button", fake_button)

    handle.reset_button()

    assert ("enter", "actions") in bucket
    assert ("button", "Reset") in bucket
    assert ("exit", "actions") in bucket


def test_form_handle_live_reset_button_tracks_dirty_state(monkeypatch):
    handle = FormHandle(
        source_class=dict,
        field_specs=[FieldSpec(name="name", python_type=str, default="Ada")],
        component_refs={"field:name": ValueComponent("Ada")},
    )

    monkeypatch.setattr(
        "nicegui_builder.core.form.ui.button",
        lambda label, on_click=None, **kwargs: FakeButton(label, on_click=on_click, **kwargs),
    )

    live = handle.live_reset_button()

    assert live.button.enabled is False
    assert live.bound_fields == 1

    handle.component("field:name").value = "Grace"
    handle.component("field:name").emit_value_change()

    assert live.button.enabled is True


def test_form_handle_live_reset_button_accepts_named_strategy(monkeypatch):
    handle = FormHandle(
        source_class=dict,
        field_specs=[FieldSpec(name="name", python_type=str, default="Ada")],
        component_refs={"field:name": ValueComponent("Ada")},
    )

    monkeypatch.setattr(
        "nicegui_builder.core.form.ui.button",
        lambda label, on_click=None, **kwargs: FakeButton(label, on_click=on_click, **kwargs),
    )

    live = handle.live_reset_button(strategy="always")

    assert live.button.enabled is True


def test_form_handle_live_submit_button_tracks_validity(monkeypatch):
    handle = FormHandle(
        source_class=DemoModel,
        field_specs=[
            FieldSpec(name="name", python_type=str),
            FieldSpec(name="age", python_type=int),
        ],
        component_refs={
            "field:name": ValueComponent("Ada"),
            "field:age": ValueComponent("not-an-int"),
        },
    )

    monkeypatch.setattr(
        "nicegui_builder.core.form.ui.button",
        lambda label, on_click=None, **kwargs: FakeButton(label, on_click=on_click, **kwargs),
    )

    live = handle.live_submit_button("Save", lambda payload: payload, as_model=True)

    assert live.button.enabled is False
    assert live.bound_fields == 2

    handle.component("field:age").value = 37
    handle.component("field:age").emit_value_change()

    assert live.button.enabled is True


def test_form_handle_live_submit_button_accepts_named_strategy(monkeypatch):
    handle = FormHandle(
        source_class=DemoModel,
        field_specs=[
            FieldSpec(name="name", python_type=str, default="Ada"),
            FieldSpec(name="age", python_type=int, default=37),
        ],
        component_refs={
            "field:name": ValueComponent("Ada"),
            "field:age": ValueComponent(37),
        },
    )

    monkeypatch.setattr(
        "nicegui_builder.core.form.ui.button",
        lambda label, on_click=None, **kwargs: FakeButton(label, on_click=on_click, **kwargs),
    )

    live = handle.live_submit_button(
        "Save",
        lambda payload: payload,
        as_model=True,
        strategy="dirty_and_valid",
    )

    assert live.button.enabled is False

    handle.component("field:name").value = "Grace"
    handle.component("field:name").emit_value_change()

    assert live.button.enabled is True


def test_form_handle_live_submit_button_accepts_callable_strategy(monkeypatch):
    handle = FormHandle(
        source_class=DemoModel,
        field_specs=[
            FieldSpec(name="name", python_type=str, default="Ada"),
            FieldSpec(name="age", python_type=int, default=37),
        ],
        component_refs={
            "field:name": ValueComponent("Ada"),
            "field:age": ValueComponent(37),
        },
    )

    monkeypatch.setattr(
        "nicegui_builder.core.form.ui.button",
        lambda label, on_click=None, **kwargs: FakeButton(label, on_click=on_click, **kwargs),
    )

    live = handle.live_submit_button(
        "Save",
        lambda payload: payload,
        as_model=True,
        strategy=lambda form_handle: len(form_handle.changed_fields()) >= 2,
    )

    assert live.button.enabled is False

    handle.component("field:name").value = "Grace"
    handle.component("field:name").emit_value_change()
    assert live.button.enabled is False

    handle.component("field:age").value = 38
    handle.component("field:age").emit_value_change()
    assert live.button.enabled is True


def test_form_handle_changed_badge_renders_dirty_state(monkeypatch):
    handle = FormHandle(
        source_class=dict,
        field_specs=[
            FieldSpec(name="name", python_type=str, default="Ada"),
            FieldSpec(name="age", python_type=int, default=20),
        ],
        component_refs={
            "field:name": ValueComponent("Grace"),
            "field:age": ValueComponent(20),
        },
    )

    monkeypatch.setattr(
        "nicegui_builder.core.form.ui.badge",
        lambda text, color=None, **kwargs: FakeBadge(text, color=color, **kwargs),
    )

    badge = handle.changed_badge()

    assert badge.text == "1 modified field"
    assert badge.color == "warning"


def test_form_handle_changed_badge_can_render_clean_state(monkeypatch):
    handle = FormHandle(
        source_class=dict,
        field_specs=[FieldSpec(name="name", python_type=str, default="Ada")],
        component_refs={"field:name": ValueComponent("Ada")},
    )

    monkeypatch.setattr(
        "nicegui_builder.core.form.ui.badge",
        lambda text, color=None, **kwargs: FakeBadge(text, color=color, **kwargs),
    )

    badge = handle.changed_badge(show_when_clean=True)

    assert badge.text == "No unsaved changes"
    assert badge.color == "positive"


def test_form_handle_changed_badge_uses_status_container(monkeypatch):
    bucket = []
    handle = FormHandle(
        source_class=dict,
        field_specs=[FieldSpec(name="name", python_type=str, default="Ada")],
        component_refs={
            "field:name": ValueComponent("Grace"),
            "form:status": FakeContext("status", bucket),
        },
    )

    def fake_badge(text, color=None, **kwargs):
        bucket.append(("badge", text, color))
        return FakeBadge(text, color=color, **kwargs)

    monkeypatch.setattr("nicegui_builder.core.form.ui.badge", fake_badge)

    handle.changed_badge()

    assert ("enter", "status") in bucket
    assert any(item[0] == "badge" for item in bucket)
    assert ("exit", "status") in bucket


def test_form_handle_live_dirty_badge_refreshes_state(monkeypatch):
    handle = FormHandle(
        source_class=dict,
        field_specs=[FieldSpec(name="name", python_type=str, default="Ada")],
        component_refs={"field:name": ValueComponent("Ada")},
    )

    def fake_badge(text, color=None, **kwargs):
        return FakeBadge(text, color=color, **kwargs)

    monkeypatch.setattr("nicegui_builder.core.form.ui.badge", fake_badge)

    live = handle.live_dirty_badge(show_when_clean=False)

    assert live.badge.visible is False
    assert live.bound_fields == 1

    handle.component("field:name").value = "Grace"
    handle.component("field:name").emit_value_change()

    assert live.badge.visible is True
    assert live.badge.text == "1 modified field"
    assert live.badge.color == "warning"


def test_form_handle_live_dirty_badge_can_show_clean_state(monkeypatch):
    handle = FormHandle(
        source_class=dict,
        field_specs=[FieldSpec(name="name", python_type=str, default="Ada")],
        component_refs={"field:name": ValueComponent("Ada")},
    )

    def fake_badge(text, color=None, **kwargs):
        return FakeBadge(text, color=color, **kwargs)

    monkeypatch.setattr("nicegui_builder.core.form.ui.badge", fake_badge)

    live = handle.live_dirty_badge(show_when_clean=True, clean_text="Clean")

    assert live.badge.visible is True
    assert live.badge.text == "Clean"
    assert live.badge.color == "positive"


def test_form_handle_live_dirty_badge_accepts_visibility_strategy(monkeypatch):
    handle = FormHandle(
        source_class=dict,
        field_specs=[FieldSpec(name="name", python_type=str, default="Ada")],
        component_refs={"field:name": ValueComponent("Grace")},
    )

    monkeypatch.setattr(
        "nicegui_builder.core.form.ui.badge",
        lambda text, color=None, **kwargs: FakeBadge(text, color=color, **kwargs),
    )

    live = handle.live_dirty_badge(strategy="never")

    assert live.badge.visible is False


def test_form_handle_action_bar_builds_badge_reset_and_submit(monkeypatch):
    bucket = []
    handle = FormHandle(
        source_class=dict,
        field_specs=[FieldSpec(name="name", python_type=str, default="Ada")],
        component_refs={
            "field:name": ValueComponent("Grace"),
            "form:status": FakeContext("status", bucket),
            "form:actions": FakeContext("actions", bucket),
        },
    )

    def fake_badge(text, color=None, **kwargs):
        bucket.append(("badge", text, color))
        return FakeBadge(text, color=color, **kwargs)

    def fake_button(label, on_click=None, **kwargs):
        bucket.append(("button", label))
        return FakeButton(label, on_click=on_click, **kwargs)

    monkeypatch.setattr("nicegui_builder.core.form.ui.badge", fake_badge)
    monkeypatch.setattr("nicegui_builder.core.form.ui.button", fake_button)

    received = []
    parts = handle.action_bar(
        "Save",
        lambda payload: received.append(payload) or "done",
    )

    assert parts["badge"] is not None
    assert parts["reset_button"] is not None
    assert parts["submit_button"] is not None
    assert ("button", "Reset") in bucket
    assert ("button", "Save") in bucket
    assert any(item[0] == "badge" for item in bucket)

    result = parts["submit_button"].on_click()
    assert result == "done"
    assert received == [{"name": "Grace"}]


def test_form_handle_action_bar_can_use_live_badge(monkeypatch):
    handle = FormHandle(
        source_class=dict,
        field_specs=[FieldSpec(name="name", python_type=str, default="Ada")],
        component_refs={"field:name": ValueComponent("Grace")},
    )

    monkeypatch.setattr(
        FormHandle,
        "live_dirty_badge",
        lambda self, **kwargs: {"badge": FakeBadge("live", color="warning"), "refresh": lambda: None, "bound_fields": 1},
    )

    def fake_button(label, on_click=None, **kwargs):
        return FakeButton(label, on_click=on_click, **kwargs)

    monkeypatch.setattr("nicegui_builder.core.form.ui.button", fake_button)

    parts = handle.action_bar(
        "Save",
        lambda payload: payload,
        live_changed_badge=True,
    )

    assert parts["badge"] is not None
    assert parts["live_badge"] is not None


def test_form_handle_binding_part_handles_none_dict_and_missing_values():
    handle = FormHandle(
        source_class=dict,
        field_specs=[FieldSpec(name="name", python_type=str)],
        component_refs={"field:name": ValueComponent("Ada")},
    )

    assert handle._binding_part(None, "button") is None
    assert handle._binding_part({"button": FakeButton("Save")}, "button").label == "Save"
    assert handle._binding_part({"other": 1}, "button") is None
    assert handle._binding_part(object(), "button") is None


def test_form_handle_binding_part_can_read_object_attributes():
    handle = FormHandle(
        source_class=dict,
        field_specs=[FieldSpec(name="name", python_type=str)],
        component_refs={"field:name": ValueComponent("Ada")},
    )

    binding = types.SimpleNamespace(button=FakeButton("Save"))

    assert handle._binding_part(binding, "button").label == "Save"


def test_form_handle_action_bar_can_use_live_buttons(monkeypatch):
    handle = FormHandle(
        source_class=dict,
        field_specs=[FieldSpec(name="name", python_type=str, default="Ada")],
        component_refs={"field:name": ValueComponent("Grace")},
    )

    monkeypatch.setattr(
        FormHandle,
        "live_reset_button",
        lambda self, *args, **kwargs: {"button": FakeButton("Reset"), "refresh": lambda: None, "bound_fields": 1},
    )
    monkeypatch.setattr(
        FormHandle,
        "live_submit_button",
        lambda self, *args, **kwargs: {"button": FakeButton("Save"), "refresh": lambda: None, "bound_fields": 1},
    )
    monkeypatch.setattr(
        "nicegui_builder.core.form.ui.badge",
        lambda text, color=None, **kwargs: FakeBadge(text, color=color, **kwargs),
    )

    parts = handle.action_bar(
        "Save",
        lambda payload: payload,
        live_reset_button=True,
        live_submit_button=True,
    )

    assert parts["reset_button"] is not None
    assert parts["live_reset_button"] is not None
    assert parts["submit_button"] is not None
    assert parts["live_submit_button"] is not None


def test_form_handle_action_bar_can_hide_optional_parts(monkeypatch):
    handle = FormHandle(
        source_class=dict,
        field_specs=[FieldSpec(name="name", python_type=str, default="Ada")],
        component_refs={"field:name": ValueComponent("Ada")},
    )

    def fake_button(label, on_click=None, **kwargs):
        return FakeButton(label, on_click=on_click, **kwargs)

    monkeypatch.setattr("nicegui_builder.core.form.ui.button", fake_button)
    monkeypatch.setattr(
        "nicegui_builder.core.form.ui.badge",
        lambda text, color=None, **kwargs: FakeBadge(text, color=color, **kwargs),
    )

    parts = handle.action_bar(
        "Save",
        lambda payload: payload,
        show_changed_badge=False,
        show_reset=False,
    )

    assert parts["badge"] is None
    assert parts["live_badge"] is None
    assert parts["reset_button"] is None
    assert parts["submit_button"] is not None


def test_form_handle_submit_button_uses_actions_container(monkeypatch):
    bucket = []
    handle = FormHandle(
        source_class=dict,
        field_specs=[FieldSpec(name="name", python_type=str)],
        component_refs={
            "field:name": ValueComponent("Ada"),
            "form:actions": FakeContext("actions", bucket),
        },
    )

    def fake_button(label, on_click=None, **kwargs):
        bucket.append(("button", label))
        return FakeButton(label, on_click=on_click, **kwargs)

    monkeypatch.setattr("nicegui_builder.core.form.ui.button", fake_button)

    handle.submit_button("Save", lambda payload: payload)

    assert ("enter", "actions") in bucket
    assert ("button", "Save") in bucket
    assert ("exit", "actions") in bucket


def test_form_handle_error_panel_renders_messages(monkeypatch):
    handle = FormHandle(
        source_class=DemoModel,
        field_specs=[
            FieldSpec(name="name", python_type=str),
            FieldSpec(name="age", python_type=int),
        ],
        component_refs={
            "field:name": ValueComponent("Ada"),
            "field:age": ValueComponent("not-an-int"),
        },
    )

    rendered = []

    def fake_card():
        return FakeContext("card", rendered)

    def fake_column():
        return FakeContext("column", rendered)

    class FakeLabel:
        def __init__(self, text):
            rendered.append(("label", text))

        def classes(self, classes):
            rendered.append(("classes", classes))
            return self

    monkeypatch.setattr("nicegui_builder.core.form.ui.card", fake_card)
    monkeypatch.setattr("nicegui_builder.core.form.ui.column", fake_column)
    monkeypatch.setattr("nicegui_builder.core.form.ui.label", lambda text: FakeLabel(text))

    handle.error_panel(as_model=True)

    assert ("label", "Validation errors") in rendered
    assert any(item[0] == "label" and "age:" in item[1] for item in rendered)


def test_form_handle_error_panel_renders_empty_message(monkeypatch):
    handle = FormHandle(
        source_class=DemoModel,
        field_specs=[
            FieldSpec(name="name", python_type=str),
            FieldSpec(name="age", python_type=int),
        ],
        component_refs={
            "field:name": ValueComponent("Ada"),
            "field:age": ValueComponent(37),
        },
    )

    rendered = []

    def fake_card():
        return FakeContext("card", rendered)

    class EmptyLabel:
        def __init__(self, text):
            rendered.append(("label", text))

        def classes(self, classes):
            rendered.append(("classes", classes))
            return self

    monkeypatch.setattr("nicegui_builder.core.form.ui.card", fake_card)
    monkeypatch.setattr("nicegui_builder.core.form.ui.column", lambda: FakeContext("column", rendered))
    monkeypatch.setattr("nicegui_builder.core.form.ui.label", lambda text: EmptyLabel(text))

    handle.error_panel(as_model=True, empty_message="All clear")

    assert ("label", "All clear") in rendered


def test_form_handle_error_panel_uses_error_container(monkeypatch):
    bucket = []
    handle = FormHandle(
        source_class=DemoModel,
        field_specs=[
            FieldSpec(name="name", python_type=str),
            FieldSpec(name="age", python_type=int),
        ],
        component_refs={
            "field:name": ValueComponent("Ada"),
            "field:age": ValueComponent("not-an-int"),
            "form:errors": FakeContext("errors", bucket),
        },
    )

    def fake_card():
        return FakeContext("card", bucket)

    class FakeLabel:
        def __init__(self, text):
            bucket.append(("label", text))

        def classes(self, classes):
            bucket.append(("classes", classes))
            return self

    monkeypatch.setattr("nicegui_builder.core.form.ui.card", fake_card)
    monkeypatch.setattr("nicegui_builder.core.form.ui.column", lambda: FakeContext("column", bucket))
    monkeypatch.setattr("nicegui_builder.core.form.ui.label", lambda text: FakeLabel(text))

    handle.error_panel(as_model=True)

    assert ("enter", "errors") in bucket
    assert ("exit", "errors") in bucket


def test_form_handle_live_error_panel_refreshes_messages(monkeypatch):
    handle = FormHandle(
        source_class=DemoModel,
        field_specs=[
            FieldSpec(name="name", python_type=str),
            FieldSpec(name="age", python_type=int),
        ],
        component_refs={
            "field:name": ValueComponent("Ada"),
            "field:age": ValueComponent("not-an-int"),
        },
    )

    def fake_card():
        return FakeContext("card", [])

    labels = []

    def fake_label(text):
        label = FakeLabel(text)
        labels.append(label)
        return label

    monkeypatch.setattr("nicegui_builder.core.form.ui.card", fake_card)
    monkeypatch.setattr("nicegui_builder.core.form.ui.label", fake_label)

    panel = handle.live_error_panel(as_model=True)

    assert panel.body.text.startswith("age:")
    assert panel.body.color == "negative"
    assert panel.bound_fields == 2

    handle.component("field:age").value = 37
    handle.component("field:age").emit_value_change()

    assert panel.body.text == "No validation errors"
    assert panel.body.color == "positive"


def test_form_handle_live_error_panel_can_show_clean_state(monkeypatch):
    handle = FormHandle(
        source_class=DemoModel,
        field_specs=[
            FieldSpec(name="name", python_type=str),
            FieldSpec(name="age", python_type=int),
        ],
        component_refs={
            "field:name": ValueComponent("Ada"),
            "field:age": ValueComponent(37),
        },
    )

    def fake_card():
        return FakeContext("card", [])

    def fake_label(text):
        return FakeLabel(text)

    monkeypatch.setattr("nicegui_builder.core.form.ui.card", fake_card)
    monkeypatch.setattr("nicegui_builder.core.form.ui.label", fake_label)

    panel = handle.live_error_panel(as_model=True, empty_message="All good")

    assert panel.body.text == "All good"
    assert panel.body.color == "positive"


def test_form_handle_live_error_panel_accepts_visibility_strategy(monkeypatch):
    handle = FormHandle(
        source_class=DemoModel,
        field_specs=[
            FieldSpec(name="name", python_type=str),
            FieldSpec(name="age", python_type=int),
        ],
        component_refs={
            "field:name": ValueComponent("Ada"),
            "field:age": ValueComponent(37),
        },
    )

    def fake_card():
        return FakeContext("card", [])

    def fake_label(text):
        return FakeLabel(text)

    monkeypatch.setattr("nicegui_builder.core.form.ui.card", fake_card)
    monkeypatch.setattr("nicegui_builder.core.form.ui.label", fake_label)

    panel = handle.live_error_panel(as_model=True, strategy="invalid")

    assert panel.card.visible is False


def test_form_handle_live_validation_tracks_change_events():
    age_component = ValueComponent("not-an-int")
    handle = FormHandle(
        source_class=DemoModel,
        field_specs=[
            FieldSpec(name="name", python_type=str),
            FieldSpec(name="age", python_type=int),
        ],
        component_refs={
            "field:name": ValueComponent("Ada"),
            "field:age": age_component,
        },
    )

    binding = handle.live_validation(as_model=True, mode="change")

    assert binding.bound_fields == 2
    assert age_component.error is not None

    age_component.value = 37
    age_component.emit_value_change()

    assert age_component.error is None


def test_form_handle_live_validation_can_bind_blur_events():
    age_component = ValueComponent("not-an-int")
    handle = FormHandle(
        source_class=DemoModel,
        field_specs=[
            FieldSpec(name="name", python_type=str),
            FieldSpec(name="age", python_type=int),
        ],
        component_refs={
            "field:name": ValueComponent("Ada"),
            "field:age": age_component,
        },
    )

    binding = handle.live_validation(as_model=True, mode="blur")

    assert binding.bound_fields == 2
    age_component.value = 37
    age_component.emit("blur")

    assert age_component.error is None


def test_form_handle_live_validation_rejects_unknown_mode():
    handle = FormHandle(
        source_class=dict,
        field_specs=[FieldSpec(name="name", python_type=str)],
        component_refs={"field:name": ValueComponent("Ada")},
    )

    try:
        handle.live_validation(mode="submit")
    except ValueError as exc:
        assert "validation mode" in str(exc)
    else:
        raise AssertionError("live_validation should reject unsupported modes")


def test_form_handle_live_validation_binds_split_datetime_parts():
    date_component = ValueComponent("2026-03-21")
    time_component = ValueComponent("14:30")
    handle = FormHandle(
        source_class=DemoDateTimeModel,
        field_specs=[FieldSpec(name="starts_at", python_type=datetime)],
        component_refs={
            "field:starts_at:date": date_component,
            "field:starts_at:time": time_component,
        },
    )

    binding = handle.live_validation(mode="change")

    assert binding.bound_fields == 2
