from datetime import date as date_type, datetime, time as time_type
import locale
from typing import Callable

from nicegui import ui
from nicegui.elements.mixins.value_element import ValueElement

from .context import builder_ctx, component_refs, ensure_builder_runtime


class DateTimeInput(ValueElement):
    DEFAULT_CONTAINER = {
        "methods": "row",
        "params": {},
        "classes": "items-end gap-2",
        "props": "",
    }
    DEFAULT_DATE_OPTIONS = {
        "label": "Date",
        "props": "clearable",
        "classes": "",
    }
    DEFAULT_TIME_OPTIONS = {
        "label": "Time",
        "props": "clearable",
        "classes": "",
    }

    # Value helpers
    @staticmethod
    def coerce_datetime_like(value):
        if hasattr(value, "to_pydatetime"):
            return value.to_pydatetime()
        return value

    @staticmethod
    def parse_datetime_string(value: str):
        normalized = value.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(normalized)
        except ValueError:
            return None

    @staticmethod
    def time_to_string(value) -> str:
        if not isinstance(value, time_type):
            return str(value)

        if value.microsecond:
            return value.isoformat(timespec="microseconds")
        if value.second:
            return value.isoformat(timespec="seconds")
        return value.isoformat(timespec="minutes")

    @classmethod
    def split_value(cls, value) -> tuple[str | None, str | None]:
        if value in (None, ""):
            return (None, None)

        value = cls.coerce_datetime_like(value)

        if isinstance(value, datetime):
            return (value.date().isoformat(), cls.time_to_string(value.time()))

        if isinstance(value, date_type) and not isinstance(value, datetime):
            return (value.isoformat(), None)

        if isinstance(value, str):
            text = value.strip()
            if not text:
                return (None, None)

            parsed = cls.parse_datetime_string(text)
            if parsed is None:
                if "T" in text:
                    date_value, time_value = text.split("T", 1)
                    return (date_value or None, time_value or None)
                if " " in text:
                    date_value, time_value = text.split(" ", 1)
                    return (date_value or None, time_value or None)
                return (text, None)

            return (parsed.date().isoformat(), cls.time_to_string(parsed.time()))

        return (str(value), None)

    @staticmethod
    def combine_value(date_value, time_value):
        if date_value in (None, "") and time_value in (None, ""):
            return None
        if date_value in (None, ""):
            return time_value
        if time_value in (None, ""):
            return date_value
        return f"{date_value}T{time_value}"

    @classmethod
    def normalize_value(cls, raw_value):
        if raw_value in (None, ""):
            return raw_value
        raw_value = cls.coerce_datetime_like(raw_value)
        if isinstance(raw_value, datetime):
            return raw_value
        if isinstance(raw_value, date_type):
            return datetime.combine(raw_value, datetime.min.time())
        if isinstance(raw_value, str):
            parsed = cls.parse_datetime_string(raw_value)
            if parsed is not None:
                return parsed
            return raw_value
        return raw_value

    @classmethod
    def format_for_display(cls, value) -> str:
        normalized = cls.normalize_value(value)
        if not isinstance(normalized, datetime):
            return str(value)

        try:
            current_locale = locale.setlocale(locale.LC_TIME)
            locale.setlocale(locale.LC_TIME, "")
            try:
                formatted = normalized.strftime("%x %X").strip()
            finally:
                locale.setlocale(locale.LC_TIME, current_locale)
            if formatted:
                return formatted
        except locale.Error:
            pass

        return normalized.strftime("%Y-%m-%d %H:%M")

    # Config normalization
    @staticmethod
    def normalize_container(
        container: dict | None,
    ) -> dict:
        if container and container.get("children"):
            raise ValueError("datetime_input container does not support nested children")

        normalized = dict(DateTimeInput.DEFAULT_CONTAINER)
        normalized["params"] = dict(DateTimeInput.DEFAULT_CONTAINER["params"])
        if container:
            normalized.update({k: v for k, v in container.items() if k != "params"})
            if "params" in container:
                normalized["params"] = dict(container.get("params") or {})
        return normalized

    @classmethod
    def normalize_part_options(
        cls,
        options: dict | None,
        *,
        defaults: dict[str, str],
    ) -> dict[str, str]:
        normalized = dict(defaults)
        normalized.update(dict(options or {}))
        return normalized

    # Builder layout helpers
    def _internal_ref(self, part: str) -> str:
        return f"__datetime_input:{id(self)}:{part}"

    def _part_node(self, *, methods: str, ref: str, value, options: dict[str, str]) -> dict:
        return {
            methods: {
                "ref": ref,
                "params": {
                    "value": value,
                    "label": options["label"],
                },
                "classes": options["classes"],
                "props": options["props"],
            }
        }

    def _layout(
        self,
        *,
        container_config: dict,
        date_value,
        time_value,
        date_options: dict[str, str],
        time_options: dict[str, str],
    ) -> list[dict]:
        container_ref = self._internal_ref("container")
        date_ref = self.date_ref or self._internal_ref("date")
        time_ref = self.time_ref or self._internal_ref("time")

        return [
            {
                container_config["methods"]: {
                    "ref": container_ref,
                    "params": dict(container_config["params"]),
                    "classes": container_config["classes"],
                    "props": container_config["props"],
                    "children": [
                        self._part_node(
                            methods="date_input",
                            ref=date_ref,
                            value=date_value,
                            options=date_options,
                        ),
                        self._part_node(
                            methods="time_input",
                            ref=time_ref,
                            value=time_value,
                            options=time_options,
                        ),
                    ],
                }
            }
        ]

    def _assign_built_parts(self, refs: dict) -> None:
        container_ref = self._internal_ref("container")
        date_ref = self.date_ref or self._internal_ref("date")
        time_ref = self.time_ref or self._internal_ref("time")

        self.container = refs.pop(container_ref)
        self.date = refs[date_ref]
        self.time = refs[time_ref]

        if self.date_ref is None:
            refs.pop(date_ref, None)
        if self.time_ref is None:
            refs.pop(time_ref, None)

    # Runtime lifecycle
    def _build_with_builder(
        self,
        *,
        container_config: dict,
        date_value,
        time_value,
        date_options: dict[str, str],
        time_options: dict[str, str],
    ) -> None:
        from ..builder import visit

        ctx = dict(builder_ctx.get())
        runtime = ensure_builder_runtime(ctx)
        previous_root = runtime.get("root_component")
        if previous_root is None:
            runtime["root_component"] = self

        token = builder_ctx.set(ctx)
        try:
            with self:
                visit(
                    self._layout(
                        container_config=container_config,
                        date_value=date_value,
                        time_value=time_value,
                        date_options=date_options,
                        time_options=time_options,
                    )
                )
            self._assign_built_parts(component_refs(ctx))
        finally:
            builder_ctx.reset(token)

    def _wire_events(self) -> None:
        self.date.on_value_change(lambda _event: self._emit_change())
        self.time.on_value_change(lambda _event: self._emit_change())

    def __init__(
        self,
        *,
        value=None,
        on_value_change: Callable | None = None,
        container: dict | None = None,
        date_ref: str | None = None,
        time_ref: str | None = None,
        date_options: dict | None = None,
        time_options: dict | None = None,
    ) -> None:
        normalized = self.normalize_value(value)
        self.container = None
        self.date = None
        self.time = None
        self.date_ref = date_ref
        self.time_ref = time_ref
        super().__init__(tag="div", value=normalized, on_value_change=on_value_change)

        date_value, time_value = self.split_value(normalized)
        container_config = self.normalize_container(container)
        date_config = self.normalize_part_options(
            date_options,
            defaults=self.DEFAULT_DATE_OPTIONS,
        )
        time_config = self.normalize_part_options(
            time_options,
            defaults=self.DEFAULT_TIME_OPTIONS,
        )

        self._build_with_builder(
            container_config=container_config,
            date_value=date_value,
            time_value=time_value,
            date_options=date_config,
            time_options=time_config,
        )

        self._wire_events()

    def _emit_change(self) -> None:
        combined = self.combine_value(self.date.value, self.time.value)
        self.set_value(self.normalize_value(combined))

    def set_value(self, value) -> None:
        normalized = self.normalize_value(value)
        super().set_value(normalized)

        if self.date is None or self.time is None:
            return

        date_value, time_value = self.split_value(normalized)
        self.date.value = date_value
        self.time.value = time_value

def build_split_datetime_node(
    *,
    field_name: str,
    label: str,
    raw_value=None,
    ref: str | None = None,
    container: dict | None = None,
    component_props: str = "",
    component_classes: str = "",
    date_ref: str | None = None,
    time_ref: str | None = None,
    date_options: dict | None = None,
    time_options: dict | None = None,
) -> dict:
    logical_ref = ref or f"field:{field_name}"
    normalized_container = DateTimeInput.normalize_container(container)
    normalized_date_options = DateTimeInput.normalize_part_options(
        date_options,
        defaults={
            **DateTimeInput.DEFAULT_DATE_OPTIONS,
            "label": f"{label} date",
            "classes": "col",
        },
    )
    normalized_time_options = DateTimeInput.normalize_part_options(
        time_options,
        defaults={
            **DateTimeInput.DEFAULT_TIME_OPTIONS,
            "label": f"{label} time",
            "classes": "col",
        },
    )

    return {
        "methods": "datetime_input",
        "ref": logical_ref,
        "params": {
            "value": raw_value,
            "container": normalized_container,
            "date_ref": date_ref or f"{logical_ref}:date",
            "time_ref": time_ref or f"{logical_ref}:time",
            "date_options": normalized_date_options,
            "time_options": normalized_time_options,
        },
        "props": component_props,
        "classes": component_classes,
        "children": [],
    }


if not hasattr(ui, "datetime_input"):
    ui.datetime_input = DateTimeInput
