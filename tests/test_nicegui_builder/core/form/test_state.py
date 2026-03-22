import enum
import builtins
from decimal import Decimal

from nicegui_builder import FormState
from nicegui_builder.core.models import FieldSpec

from .support import DemoModel, DemoNestedModel, DemoStructuredModel


class Mood(enum.Enum):
    CALM = "calm"
    LOUD = "loud"


class PlainSource:
    def __init__(self, name="Ada", age=20):
        self.name = name
        self.age = age


def test_form_state_changed_fields_uses_defaults_as_baseline():
    state = FormState(
        source_class=dict,
        field_specs=[
            FieldSpec(name="name", python_type=str, default="Ada"),
            FieldSpec(name="age", python_type=int, default=20),
        ],
    )

    assert state.changed_fields({"name": "Grace", "age": 20}) == {
        "name": {"from": "Ada", "to": "Grace"},
    }
    assert state.is_dirty({"name": "Grace", "age": 20}) is True


def test_form_state_changed_fields_coerces_scalar_strings_before_comparison():
    state = FormState(
        source_class=dict,
        field_specs=[
            FieldSpec(name="mismatch_level", python_type=int, default=8),
            FieldSpec(name="returning_legend", python_type=bool, default=False),
        ],
    )

    assert state.changed_fields({"mismatch_level": "8", "returning_legend": "False"}) == {}
    assert state.is_dirty({"mismatch_level": "8", "returning_legend": "False"}) is False


def test_form_state_reset_values_can_use_source_defaults_and_empty():
    state = FormState(
        source_class=DemoModel,
        field_specs=[
            FieldSpec(name="name", python_type=str, default="Default"),
            FieldSpec(name="age", python_type=int, default=0),
            FieldSpec(name="enabled", python_type=bool, default=True),
        ],
        source_instance=DemoModel(name="Ada", age=20),
    )

    assert state.reset_values("source") == {"name": "Ada", "age": 20}
    assert state.reset_values("defaults") == {"name": "Default", "age": 0, "enabled": True}
    assert state.reset_values("empty") == {"name": "", "age": None, "enabled": False}


def test_form_state_can_build_and_validate_pydantic_models():
    state = FormState(
        source_class=DemoModel,
        field_specs=[
            FieldSpec(name="name", python_type=str),
            FieldSpec(name="age", python_type=int),
        ],
    )

    model = state.to_model({"name": "Ada", "age": 37})
    valid = state.validate({"name": "Ada", "age": 37}, as_model=True)
    invalid = state.validate({"name": "Ada", "age": "not-an-int"}, as_model=True)

    assert isinstance(model, DemoModel)
    assert valid.valid is True
    assert isinstance(valid.payload, DemoModel)
    assert invalid.valid is False
    assert invalid.error is not None


def test_form_state_to_model_parses_json_for_structured_fields():
    state = FormState(
        source_class=DemoStructuredModel,
        field_specs=[
            FieldSpec(name="tags", python_type=list[str], source_meta={"is_structured": True}),
            FieldSpec(name="metadata", python_type=dict[str, str], source_meta={"is_structured": True}),
            FieldSpec(name="nested", python_type=DemoNestedModel, source_meta={"is_structured": True}),
        ],
    )

    model = state.to_model(
        {
            "tags": '["alpha", "beta"]',
            "metadata": '{"host":"main-stage"}',
            "nested": '{"label":"Backstage crate","count":24}',
        }
    )

    assert isinstance(model, DemoStructuredModel)
    assert model.tags == ["alpha", "beta"]
    assert model.metadata == {"host": "main-stage"}
    assert model.nested.label == "Backstage crate"
    assert model.nested.count == 24


def test_form_state_supports_plain_source_objects_and_default_baseline_fallback():
    state = FormState(
        source_class=PlainSource,
        field_specs=[
            FieldSpec(name="name", python_type=str, default="Default"),
            FieldSpec(name="age", python_type=int, default=0),
        ],
        source_instance=PlainSource(name="Ada", age=20),
    )

    assert state._source_values() == {"name": "Ada", "age": 20}
    assert state._baseline_values() == {"name": "Ada", "age": 20}

    state.source_instance = None

    assert state._source_values() == {}
    assert state._baseline_values() == {"name": "Default", "age": 0}


def test_form_state_empty_values_and_coercion_cover_more_scalar_types():
    state = FormState(
        source_class=dict,
        field_specs=[
            FieldSpec(name="payload", python_type=bytes),
            FieldSpec(name="price", python_type=Decimal),
            FieldSpec(name="mood", python_type=Mood),
            FieldSpec(name="structured", python_type=dict, source_meta={"is_structured": True}),
        ],
    )

    assert state.empty_values() == {
        "payload": "",
        "price": None,
        "mood": None,
        "structured": None,
    }

    mood_field = state.field_specs[2]
    structured_field = state.field_specs[3]
    price_field = state.field_specs[1]

    assert state._coerce_field_value(mood_field, None) is None
    assert state._coerce_field_value(mood_field, Mood.CALM) == "calm"
    assert state._coerce_field_value(mood_field, "CALM") == "calm"
    assert state._coerce_field_value(mood_field, "calm") == "calm"
    assert state._coerce_field_value(mood_field, "mystery") == "mystery"
    assert state._coerce_field_value(structured_field, '{"host":"main-stage"}') == {"host": "main-stage"}
    assert state._coerce_field_value(structured_field, "{not-json}") == "{not-json}"
    assert state._coerce_field_value(FieldSpec(name="enabled", python_type=bool), "yes") is True
    assert state._coerce_field_value(price_field, "12.50") == Decimal("12.50")
    assert state._coerce_field_value(FieldSpec(name="ratio", python_type=float), "4.5") == 4.5
    assert state._coerce_field_value(FieldSpec(name="ratio", python_type=float), "nope") == "nope"
    assert state._coerce_field_value(price_field, "nope") == "nope"


def test_form_state_reset_values_and_to_model_reject_invalid_modes_and_non_pydantic_sources():
    state = FormState(
        source_class=dict,
        field_specs=[FieldSpec(name="name", python_type=str, default="Ada")],
    )

    try:
        state.reset_values("mystery")
    except ValueError as exc:
        assert "reset mode" in str(exc)
    else:
        raise AssertionError("reset_values should reject unsupported modes")

    try:
        state.to_model({"name": "Ada"})
    except TypeError as exc:
        assert "pydantic models" in str(exc)
    else:
        raise AssertionError("to_model should reject non-pydantic source classes")


def test_form_state_to_model_falls_back_when_pydantic_is_unavailable(monkeypatch):
    state = FormState(
        source_class=dict,
        field_specs=[FieldSpec(name="name", python_type=str)],
    )

    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "pydantic":
            raise ImportError()
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    assert state.to_model({"name": "Ada"}) == {"name": "Ada"}
