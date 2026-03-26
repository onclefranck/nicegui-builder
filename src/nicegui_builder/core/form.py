from dataclasses import dataclass, field
from collections.abc import Callable
from contextlib import nullcontext
from decimal import Decimal
from datetime import datetime
import enum
import json

from nicegui import ui

from .actions import FORM_ACTION_SPECS, apply_action_intent, get_action_spec
from .datetime_inputs import _time_to_string, combine_datetime_value, split_datetime_value
from .models import ActionSpec, FieldSpec, FormSpec
from .view import ViewHandle


def get_component_value(component):
    if hasattr(component, "value"):
        return component.value

    if hasattr(component, "text"):
        return component.text

    return None


def set_component_value(component, value):
    if component is None:
        return None

    if hasattr(component, "set_value"):
        return component.set_value(value)

    if hasattr(component, "value"):
        component.value = value
        return value

    if hasattr(component, "text"):
        component.text = "" if value is None else str(value)
        return component.text

    return None


def set_component_error(component, message: str | None):
    if component is None:
        return None

    if hasattr(component, "set_error"):
        return component.set_error(message)

    if hasattr(component, "error"):
        component.error = message

    if hasattr(component, "error_message"):
        component.error_message = message

    return message


def clear_component_error(component):
    return set_component_error(component, None)


def set_component_text(component, text: str):
    if component is None:
        return None

    if hasattr(component, "set_text"):
        return component.set_text(text)

    if hasattr(component, "text"):
        component.text = text
        return text

    return None


def set_component_visibility(component, visible: bool):
    if component is None:
        return None

    if hasattr(component, "set_visibility"):
        return component.set_visibility(visible)

    if hasattr(component, "visible"):
        component.visible = visible
        return visible

    return None


def set_component_color(component, color: str):
    if component is None:
        return None

    if hasattr(component, "color"):
        component.color = color
        return color

    return None


def set_component_enabled(component, enabled: bool):
    if component is None:
        return None

    if hasattr(component, "set_enabled"):
        return component.set_enabled(enabled)

    if hasattr(component, "enabled"):
        component.enabled = enabled
        return enabled

    return None


def bind_component_event(component, callback: Callable, event: str = "change") -> bool:
    if component is None:
        return False

    if event == "change":
        if hasattr(component, "on_value_change"):
            component.on_value_change(lambda *_args, **_kwargs: callback())
            return True

        if hasattr(component, "on_change"):
            component.on_change(lambda *_args, **_kwargs: callback())
            return True

        if hasattr(component, "on"):
            component.on("change", lambda *_args, **_kwargs: callback())
            return True

        return False

    if event == "blur":
        if hasattr(component, "on_blur"):
            component.on_blur(lambda *_args, **_kwargs: callback())
            return True

        if hasattr(component, "on"):
            component.on("blur", lambda *_args, **_kwargs: callback())
            return True

        return False

    raise ValueError("event must be one of: 'change', 'blur'")


def resolve_live_strategy(
    strategy,
    handle,
    *,
    as_model: bool = False,
    fallback: bool = True,
):
    if strategy is None:
        return fallback

    if callable(strategy):
        return bool(strategy(handle))

    if strategy == "always":
        return True

    if strategy == "never":
        return False

    if strategy == "dirty":
        return handle.is_dirty()

    if strategy == "clean":
        return not handle.is_dirty()

    if strategy == "valid":
        return handle.validate(as_model=as_model).valid

    if strategy == "invalid":
        return not handle.validate(as_model=as_model).valid

    if strategy == "dirty_and_valid":
        return handle.is_dirty() and handle.validate(as_model=as_model).valid

    if strategy == "dirty_or_valid":
        return handle.is_dirty() or handle.validate(as_model=as_model).valid

    raise ValueError(
        "strategy must be a callable or one of: "
        "'always', 'never', 'dirty', 'clean', 'valid', 'invalid', "
        "'dirty_and_valid', 'dirty_or_valid'"
    )


@dataclass(slots=True)
class LiveBinding:
    refresh: Callable
    bound_fields: int


@dataclass(slots=True)
class LiveButtonBinding(LiveBinding):
    button: object


@dataclass(slots=True)
class LiveBadgeBinding(LiveBinding):
    badge: object


@dataclass(slots=True)
class LivePanelBinding(LiveBinding):
    card: object
    title: object
    body: object


@dataclass(slots=True)
class FormState:
    source_class: type
    field_specs: list[FieldSpec]
    source_instance: object | None = None

    def _source_values(self) -> dict[str, object]:
        if self.source_instance is None:
            return {}

        if hasattr(self.source_instance, "model_dump"):
            return dict(self.source_instance.model_dump())

        return {
            field.name: getattr(self.source_instance, field.name, None)
            for field in self.field_specs
        }

    def _default_values(self) -> dict[str, object]:
        return {field.name: field.default for field in self.field_specs}

    def _baseline_values(self) -> dict[str, object]:
        source_values = self._source_values()
        if source_values:
            return source_values
        return self._default_values()

    def _empty_value_for_field(self, field: FieldSpec):
        if field.python_type is bool:
            return False

        if field.python_type in {str, bytes}:
            return ""

        if field.python_type in {list, tuple, set, dict}:
            return None

        if field.python_type in {int, float, Decimal}:
            return None

        return None

    def empty_values(self) -> dict[str, object]:
        return {field.name: self._empty_value_for_field(field) for field in self.field_specs}

    def _coerce_field_value(self, field: FieldSpec, value):
        if value is None:
            return None

        python_type = field.python_type

        if isinstance(python_type, type) and issubclass(python_type, enum.Enum):
            if isinstance(value, python_type):
                return value.value
            for member in python_type:
                if value in {member, member.value, member.name}:
                    return member.value
            return value

        if field.source_meta.get("is_structured") and isinstance(value, str):
            text = value.strip()
            if text:
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    pass

        if python_type is bool and isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"true", "1", "yes", "on"}:
                return True
            if normalized in {"false", "0", "no", "off"}:
                return False

        if python_type is int and isinstance(value, str):
            text = value.strip()
            if text:
                try:
                    return int(text)
                except ValueError:
                    return value

        if python_type is float and isinstance(value, str):
            text = value.strip()
            if text:
                try:
                    return float(text)
                except ValueError:
                    return value

        if python_type is Decimal and isinstance(value, str):
            text = value.strip()
            if text:
                try:
                    return Decimal(text)
                except Exception:
                    return value

        return value

    def changed_fields(self, values: dict[str, object]) -> dict[str, dict[str, object]]:
        baseline = self._baseline_values()
        changes: dict[str, dict[str, object]] = {}

        for field in self.field_specs:
            previous = self._coerce_field_value(field, baseline.get(field.name))
            value = self._coerce_field_value(field, values.get(field.name))
            if value != previous:
                changes[field.name] = {
                    "from": previous,
                    "to": value,
                }

        return changes

    def is_dirty(self, values: dict[str, object]) -> bool:
        return bool(self.changed_fields(values))

    def reset_values(self, mode: str = "source") -> dict[str, object]:
        if mode == "source":
            values = self._source_values()
            if not values:
                values = self._default_values()
        elif mode == "defaults":
            values = self._default_values()
        elif mode == "empty":
            values = self.empty_values()
        else:
            raise ValueError("reset mode must be one of: 'source', 'defaults', 'empty'")

        return values

    def to_model(self, values: dict[str, object]):
        try:
            from pydantic import BaseModel
        except ImportError:
            BaseModel = object

        if not isinstance(self.source_class, type) or not issubclass(self.source_class, BaseModel):
            raise TypeError("to_model() is currently only supported for pydantic models")

        payload = {
            field.name: self._coerce_field_value(field, values.get(field.name))
            for field in self.field_specs
            if field.name in values
        }
        if self.source_instance is not None:
            base_values = self.source_instance.model_dump()
            base_values.update(payload)
            payload = base_values

        return self.source_class(**payload)

    def validate(self, values: dict[str, object], *, as_model: bool = False):
        try:
            payload = self.to_model(values) if as_model else dict(values)
        except Exception as error:
            return FormValidationResult(valid=False, payload=None, error=error)

        return FormValidationResult(valid=True, payload=payload, error=None)


@dataclass(slots=True)
class FormHandle(ViewHandle):
    source_class: type
    field_specs: list[FieldSpec]
    component_refs: dict[str, object]
    field_refs: dict[str, str] = field(default_factory=dict)
    source_instance: object | None = None
    form_spec: FormSpec | None = None
    _state: FormState = field(init=False, repr=False)
    _spec: FormSpec = field(init=False, repr=False)

    def __post_init__(self):
        if self.form_spec is None:
            self._spec = FormSpec(
                source_class=self.source_class,
                field_specs=self.field_specs,
                source_instance=self.source_instance,
            )
        else:
            self._spec = self.form_spec
            self.source_class = self._spec.source_class
            self.field_specs = self._spec.field_specs
            self.source_instance = self._spec.source_instance

        self.form_spec = self._spec
        self._state = FormState(
            source_class=self._spec.source_class,
            field_specs=self._spec.field_specs,
            source_instance=self._spec.source_instance,
        )

    def _sync_spec(self) -> FormSpec:
        self._spec.source_class = self.source_class
        self._spec.field_specs = self.field_specs
        self._spec.source_instance = self.source_instance
        self.form_spec = self._spec
        return self._spec

    def _sync_state(self) -> FormState:
        spec = self._sync_spec()
        self._state.source_class = spec.source_class
        self._state.field_specs = spec.field_specs
        self._state.source_instance = spec.source_instance
        return self._state

    @property
    def spec(self) -> FormSpec:
        return self._sync_spec()

    @property
    def state(self) -> FormState:
        return self._sync_state()

    def component(self, ref: str):
        return self.component_refs.get(ref)

    def _live_refreshers(self) -> list[Callable]:
        return self.component_refs.setdefault("_live_refreshers", [])

    def _register_live_refresh(self, refresh: Callable):
        refreshers = self._live_refreshers()
        refreshers.append(refresh)
        return refresh

    def refresh_live(self):
        for refresh in list(self._live_refreshers()):
            refresh()
        return self

    def _bind_field_events(self, callback: Callable, event: str = "change") -> int:
        bound = 0
        for field in self.spec.field_specs:
            if self._has_split_datetime_parts(field.name):
                for part in ("date", "time"):
                    component = self._field_part_component(field.name, part)
                    if bind_component_event(component, callback, event=event):
                        bound += 1
                continue

            component = self._field_component(field)
            if bind_component_event(component, callback, event=event):
                bound += 1
        return bound

    def _setup_live_view(self, binding_type, refresh: Callable, *, event: str = "change", **parts):
        self._register_live_refresh(refresh)
        bound = self._bind_field_events(refresh, event=event)
        refresh()
        return binding_type(refresh=refresh, bound_fields=bound, **parts)

    def _field_ref(self, field: FieldSpec) -> str:
        return self.field_refs.get(field.name, f"field:{field.name}")

    def _field_component(self, field: FieldSpec):
        return self.component(self._field_ref(field))

    def _field_part_component(self, field_name: str, part: str):
        return self.component(f"{self.field_refs.get(field_name, f'field:{field_name}')}:{part}")

    def _has_split_datetime_parts(self, field_name: str) -> bool:
        return (
            self._field_part_component(field_name, "date") is not None
            or self._field_part_component(field_name, "time") is not None
        )

    def _field_value(self, field: FieldSpec):
        if self._has_split_datetime_parts(field.name):
            date_value = get_component_value(self._field_part_component(field.name, "date"))
            time_value = get_component_value(self._field_part_component(field.name, "time"))
            return combine_datetime_value(date_value, time_value)

        component = self._field_component(field)
        return get_component_value(component) if component else None

    def _set_field_value(self, field: FieldSpec, value):
        if self._has_split_datetime_parts(field.name):
            date_value, time_value = split_datetime_value(value)
            set_component_value(self._field_part_component(field.name, "date"), date_value)
            set_component_value(self._field_part_component(field.name, "time"), time_value)
            return value

        return set_component_value(self._field_component(field), value)

    def _binding_part(self, binding, attribute: str):
        if binding is None:
            return None

        if hasattr(binding, attribute):
            return getattr(binding, attribute)

        if isinstance(binding, dict):
            return binding.get(attribute)

        return None

    def get_values(self) -> dict[str, object]:
        values = {}
        for field in self.spec.field_specs:
            values[field.name] = self._field_value(field)
        return values

    def set_values(self, values: dict[str, object]):
        for field in self.spec.field_specs:
            if field.name not in values:
                continue
            self._set_field_value(field, values[field.name])
        self.refresh_live()
        return self

    def changed_fields(self) -> dict[str, dict[str, object]]:
        return self.state.changed_fields(self.get_values())

    def is_dirty(self) -> bool:
        return self.state.is_dirty(self.get_values())

    def reset(self, mode: str = "source"):
        return self.set_values(self.state.reset_values(mode))

    def reset_to_source(self):
        return self.reset("source")

    def reset_to_defaults(self):
        return self.reset("defaults")

    def reset_to_empty(self):
        return self.reset("empty")

    def to_model(self):
        return self.state.to_model(self.get_values())

    def validate(self, *, as_model: bool = False):
        return self.state.validate(self.get_values(), as_model=as_model)

    def _field_validation_messages(
        self,
        field_name: str,
        *,
        validation: "FormValidationResult | None" = None,
        as_model: bool = False,
    ) -> list[str]:
        validation = validation or self.validate(as_model=as_model)
        return validation.errors_by_field().get(field_name, [])

    def _set_field_error_message(self, field_name: str, message: str | None):
        set_component_error(self.component(f"field:{field_name}"), message)
        if self._has_split_datetime_parts(field_name):
            set_component_error(self._field_part_component(field_name, "date"), message)
            set_component_error(self._field_part_component(field_name, "time"), message)
        return message

    def errors(self, *, as_model: bool = False) -> dict[str, list[str]]:
        return self.validate(as_model=as_model).errors_by_field()

    def error_messages(self, *, as_model: bool = False) -> list[str]:
        return self.validate(as_model=as_model).error_messages()

    def clear_errors(self):
        return self._clear_field_errors()

    def _clear_field_errors(self, *, refresh_live: bool = True):
        for field in self.spec.field_specs:
            self._set_field_error_message(field.name, None)
        if refresh_live:
            self.refresh_live()
        return self

    def _apply_validation_errors(self, validation: "FormValidationResult"):
        for field_name, messages in validation.errors_by_field().items():
            self._set_field_error_message(field_name, "\n".join(messages))
        return validation

    def apply_errors(self, *, as_model: bool = False):
        validation = self.validate(as_model=as_model)
        self._clear_field_errors(refresh_live=False)
        self._apply_validation_errors(validation)
        self.refresh_live()
        return validation

    def validate_field(self, field_name: str, *, as_model: bool = False) -> list[str]:
        return self._field_validation_messages(field_name, as_model=as_model)

    def field_error_message(self, field_name: str, *, as_model: bool = False) -> str | None:
        messages = self._field_validation_messages(field_name, as_model=as_model)
        if not messages:
            return None
        return "\n".join(messages)

    def apply_field_errors(self, field_name: str, *, as_model: bool = False):
        message = self.field_error_message(field_name, as_model=as_model)
        self._set_field_error_message(field_name, message)
        self.refresh_live()
        return message

    def live_validation(
        self,
        *,
        as_model: bool = False,
        mode: str = "change",
        clear_when_valid: bool = True,
    ) -> LiveBinding:
        if mode not in {"change", "blur"}:
            raise ValueError("validation mode must be one of: 'change', 'blur'")

        def refresh():
            validation = self.validate(as_model=as_model)
            self._clear_field_errors(refresh_live=False)
            if not validation.valid:
                self._apply_validation_errors(validation)
            elif clear_when_valid:
                self._clear_field_errors(refresh_live=False)
            return validation

        return self._setup_live_view(LiveBinding, refresh, event=mode)

    def submit(
        self,
        callback: Callable,
        *,
        as_model: bool = False,
        on_error: Callable | None = None,
        apply_errors: bool = False,
    ):
        validation = self.validate(as_model=as_model)
        if not validation.valid:
            if apply_errors:
                self.clear_errors()
                self._apply_validation_errors(validation)
            if on_error is not None:
                return on_error(validation.error)
            raise validation.error

        if apply_errors:
            self.clear_errors()

        payload = validation.payload
        result = callback(payload)
        self.refresh_live()
        return result

    def submit_button(
        self,
        label: str,
        callback: Callable,
        *,
        as_model: bool = False,
        on_error: Callable | None = None,
        apply_errors: bool = False,
        **button_kwargs,
    ):
        def _on_click():
            return self.submit(
                callback,
                as_model=as_model,
                on_error=on_error,
                apply_errors=apply_errors,
            )

        target = self.component("form:actions")
        with target if target is not None else nullcontext():
            return ui.button(label, on_click=_on_click, **button_kwargs)

    def action_spec(self, name: str) -> ActionSpec:
        return get_action_spec(FORM_ACTION_SPECS, name)

    def create_button(
        self,
        callback: Callable,
        *,
        as_model: bool = True,
        on_error: Callable | None = None,
        apply_errors: bool = True,
        live: bool = True,
        strategy: str | Callable | None = None,
        **button_kwargs,
    ):
        spec = self.action_spec("create")
        apply_action_intent(spec, button_kwargs)
        if live:
            return self.live_submit_button(
                spec.label,
                callback,
                as_model=as_model,
                on_error=on_error,
                apply_errors=apply_errors,
                strategy=strategy or spec.strategy,
                **button_kwargs,
            )
        return self.submit_button(
            spec.label,
            callback,
            as_model=as_model,
            on_error=on_error,
            apply_errors=apply_errors,
            **button_kwargs,
        )

    def update_button(
        self,
        callback: Callable,
        *,
        as_model: bool = True,
        on_error: Callable | None = None,
        apply_errors: bool = True,
        live: bool = True,
        strategy: str | Callable | None = None,
        **button_kwargs,
    ):
        spec = self.action_spec("update")
        apply_action_intent(spec, button_kwargs)
        if live:
            return self.live_submit_button(
                spec.label,
                callback,
                as_model=as_model,
                on_error=on_error,
                apply_errors=apply_errors,
                strategy=strategy or spec.strategy,
                **button_kwargs,
            )
        return self.submit_button(
            spec.label,
            callback,
            as_model=as_model,
            on_error=on_error,
            apply_errors=apply_errors,
            **button_kwargs,
        )

    def delete_button(
        self,
        callback: Callable,
        *,
        pass_source: bool = True,
        live: bool = False,
        strategy: str | Callable | None = None,
        **button_kwargs,
    ):
        spec = self.action_spec("delete")
        apply_action_intent(spec, button_kwargs)

        def _delete(_payload=None):
            target = self.source_instance if pass_source else self.get_values()
            return callback(target)

        if live:
            return self.live_submit_button(
                spec.label,
                _delete,
                as_model=False,
                apply_errors=False,
                strategy=strategy or spec.strategy,
                **button_kwargs,
            )

        return self.submit_button(
            spec.label,
            _delete,
            as_model=False,
            apply_errors=False,
            **button_kwargs,
        )

    def crud_bar(
        self,
        *,
        on_create: Callable | None = None,
        on_update: Callable | None = None,
        on_delete: Callable | None = None,
        on_reset: Callable | None = None,
        as_model: bool = True,
        apply_errors: bool = True,
    ) -> dict[str, object | None]:
        parts: dict[str, object | None] = {
            "create": None,
            "update": None,
            "delete": None,
            "reset": None,
        }

        if on_create is not None:
            parts["create"] = self.create_button(
                on_create,
                as_model=as_model,
                apply_errors=apply_errors,
            )

        if on_update is not None:
            parts["update"] = self.update_button(
                on_update,
                as_model=as_model,
                apply_errors=apply_errors,
            )

        if on_delete is not None:
            parts["delete"] = self.delete_button(on_delete)

        if on_reset is not None:
            parts["reset"] = self.reset_button(on_reset=on_reset)

        return parts

    def live_submit_button(
        self,
        label: str,
        callback: Callable,
        *,
        as_model: bool = False,
        on_error: Callable | None = None,
        apply_errors: bool = False,
        strategy: str | Callable | None = None,
        **button_kwargs,
    ) -> LiveButtonBinding:
        button = self.submit_button(
            label,
            callback,
            as_model=as_model,
            on_error=on_error,
            apply_errors=apply_errors,
            **button_kwargs,
        )

        def refresh():
            enabled = resolve_live_strategy(
                strategy,
                self,
                as_model=as_model,
                fallback=self.validate(as_model=as_model).valid,
            )
            set_component_enabled(button, enabled)
            return button

        return self._setup_live_view(LiveButtonBinding, refresh, button=button)

    def reset_button(
        self,
        label: str = "Reset",
        *,
        mode: str = "source",
        on_reset: Callable | None = None,
        clear_errors: bool = True,
        **button_kwargs,
    ):
        def _on_click():
            self.reset(mode)
            if clear_errors:
                self.clear_errors()
            if on_reset is not None:
                return on_reset(self)
            return self

        target = self.component("form:actions")
        with target if target is not None else nullcontext():
            return ui.button(label, on_click=_on_click, **button_kwargs)

    def live_reset_button(
        self,
        label: str = "Reset",
        *,
        mode: str = "source",
        on_reset: Callable | None = None,
        clear_errors: bool = True,
        strategy: str | Callable | None = None,
        **button_kwargs,
    ) -> LiveButtonBinding:
        button = self.reset_button(
            label,
            mode=mode,
            on_reset=on_reset,
            clear_errors=clear_errors,
            **button_kwargs,
        )

        def refresh():
            enabled = resolve_live_strategy(strategy, self, fallback=self.is_dirty())
            set_component_enabled(button, enabled)
            return button

        return self._setup_live_view(LiveButtonBinding, refresh, button=button)

    def changed_badge(
        self,
        *,
        dirty_text: str | None = None,
        clean_text: str | None = None,
        show_when_clean: bool = False,
        dirty_color: str = "warning",
        clean_color: str = "positive",
        **badge_kwargs,
    ):
        changes = self.changed_fields()
        dirty = bool(changes)

        if dirty:
            text = dirty_text or (
                "1 modified field" if len(changes) == 1 else f"{len(changes)} modified fields"
            )
            color = dirty_color
        else:
            if not show_when_clean:
                return None
            text = clean_text or "No unsaved changes"
            color = clean_color

        target = self.component("form:status")
        with target if target is not None else nullcontext():
            return ui.badge(text, color=color, **badge_kwargs)

    def live_dirty_badge(
        self,
        *,
        dirty_text: str | None = None,
        clean_text: str | None = None,
        show_when_clean: bool = False,
        strategy: str | Callable | None = None,
        dirty_color: str = "warning",
        clean_color: str = "positive",
        **badge_kwargs,
    ) -> LiveBadgeBinding:
        badge = self.changed_badge(
            dirty_text=dirty_text,
            clean_text=clean_text,
            show_when_clean=show_when_clean,
            dirty_color=dirty_color,
            clean_color=clean_color,
            **badge_kwargs,
        )

        if badge is None:
            target = self.component("form:status")
            with target if target is not None else nullcontext():
                badge = ui.badge("", color=clean_color, **badge_kwargs)
            set_component_visibility(badge, False)

        def refresh():
            changes = self.changed_fields()
            dirty = bool(changes)
            visible = resolve_live_strategy(
                strategy,
                self,
                fallback=dirty or show_when_clean,
            )

            if dirty:
                text = dirty_text or (
                    "1 modified field" if len(changes) == 1 else f"{len(changes)} modified fields"
                )
                color = dirty_color
            else:
                text = clean_text or "No unsaved changes"
                color = clean_color

            set_component_text(badge, text)
            set_component_color(badge, color)
            set_component_visibility(badge, visible)
            return badge

        return self._setup_live_view(LiveBadgeBinding, refresh, badge=badge)

    def action_bar(
        self,
        submit_label: str,
        callback: Callable,
        *,
        as_model: bool = False,
        on_error: Callable | None = None,
        apply_errors: bool = True,
        show_changed_badge: bool = True,
        live_changed_badge: bool = False,
        live_submit_button: bool = False,
        live_reset_button: bool = False,
        submit_strategy: str | Callable | None = None,
        reset_strategy: str | Callable | None = None,
        show_when_clean: bool = True,
        reset_label: str = "Reset",
        reset_mode: str = "source",
        show_reset: bool = True,
        on_reset: Callable | None = None,
        submit_button_kwargs: dict | None = None,
        reset_button_kwargs: dict | None = None,
        badge_kwargs: dict | None = None,
    ) -> dict[str, object | None]:
        parts: dict[str, object | None] = {
            "badge": None,
            "live_badge": None,
            "reset_button": None,
            "live_reset_button": None,
            "submit_button": None,
            "live_submit_button": None,
        }

        if show_changed_badge:
            if live_changed_badge:
                parts["live_badge"] = self.live_dirty_badge(
                    show_when_clean=show_when_clean,
                    **(badge_kwargs or {}),
                )
                parts["badge"] = self._binding_part(parts["live_badge"], "badge")
            else:
                parts["badge"] = self.changed_badge(
                    show_when_clean=show_when_clean,
                    **(badge_kwargs or {}),
                )

        if show_reset:
            if live_reset_button:
                parts["live_reset_button"] = self.live_reset_button(
                    reset_label,
                    mode=reset_mode,
                    on_reset=on_reset,
                    strategy=reset_strategy,
                    **(reset_button_kwargs or {}),
                )
                parts["reset_button"] = self._binding_part(parts["live_reset_button"], "button")
            else:
                parts["reset_button"] = self.reset_button(
                    reset_label,
                    mode=reset_mode,
                    on_reset=on_reset,
                    **(reset_button_kwargs or {}),
                )

        if live_submit_button:
            parts["live_submit_button"] = self.live_submit_button(
                submit_label,
                callback,
                as_model=as_model,
                on_error=on_error,
                apply_errors=apply_errors,
                strategy=submit_strategy,
                **(submit_button_kwargs or {}),
            )
            parts["submit_button"] = self._binding_part(parts["live_submit_button"], "button")
        else:
            parts["submit_button"] = self.submit_button(
                submit_label,
                callback,
                as_model=as_model,
                on_error=on_error,
                apply_errors=apply_errors,
                **(submit_button_kwargs or {}),
            )

        return parts

    def live_error_panel(
        self,
        *,
        as_model: bool = False,
        title: str = "Validation errors",
        empty_message: str = "No validation errors",
        strategy: str | Callable | None = None,
    ) -> LivePanelBinding:
        target = self.component("form:errors")

        with target if target is not None else nullcontext():
            with ui.card().classes("w-full") as card:
                title_label = ui.label(title).classes("text-negative text-subtitle2")
                body_label = ui.label("").classes("text-positive")

        def refresh():
            messages = self.error_messages(as_model=as_model)
            visible = resolve_live_strategy(
                strategy,
                self,
                as_model=as_model,
                fallback=True,
            )
            if messages:
                set_component_text(body_label, "\n".join(messages))
                set_component_color(body_label, "negative")
            else:
                set_component_text(body_label, empty_message)
                set_component_color(body_label, "positive")
            set_component_visibility(card, visible)
            return body_label

        return self._setup_live_view(
            LivePanelBinding,
            refresh,
            card=card,
            title=title_label,
            body=body_label,
        )

    def error_panel(
        self,
        *,
        as_model: bool = False,
        title: str = "Validation errors",
        empty_message: str = "No validation errors",
    ):
        messages = self.error_messages(as_model=as_model)

        target = self.component("form:errors")
        with target if target is not None else nullcontext():
            with ui.card().classes("w-full"):
                ui.label(title).classes("text-negative text-subtitle2")
                if messages:
                    with ui.column().classes("gap-1"):
                        for message in messages:
                            ui.label(message).classes("text-negative")
                else:
                    ui.label(empty_message).classes("text-positive")


@dataclass(slots=True)
class FormValidationResult:
    valid: bool
    payload: object | None
    error: Exception | None

    def errors_by_field(self) -> dict[str, list[str]]:
        if self.error is None:
            return {}

        if hasattr(self.error, "errors"):
            grouped: dict[str, list[str]] = {}
            for item in self.error.errors():
                loc = item.get("loc") or ("__root__",)
                if isinstance(loc, tuple):
                    key = ".".join(str(part) for part in loc)
                else:
                    key = str(loc)
                grouped.setdefault(key, []).append(item.get("msg", "Invalid value"))
            return grouped

        return {"__root__": [str(self.error)]}

    def error_messages(self) -> list[str]:
        messages: list[str] = []
        for field, field_messages in self.errors_by_field().items():
            for message in field_messages:
                if field == "__root__":
                    messages.append(message)
                else:
                    messages.append(f"{field}: {message}")
        return messages
