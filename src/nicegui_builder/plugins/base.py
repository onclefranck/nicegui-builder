from dataclasses import dataclass
from typing import Protocol

from nicegui_builder.core.models import CollectionSpec, FieldSpec, WidgetSpec


class SourcePlugin(Protocol):
    name: str

    def supports(self, source) -> bool: ...


class FieldPlugin(SourcePlugin, Protocol):
    def inspect_fields(self, source) -> list[FieldSpec]: ...

    def build_layout(self, source, flavor: str = ""): ...

    def build_field_context(self, model_class, model_instance, fieldname: str) -> dict: ...

    def resolve_field_node(
        self, model_class, model_instance, fieldname: str, value: dict | None
    ) -> dict: ...

    def resolve_widget(self, spec: FieldSpec, variant: str = "std") -> WidgetSpec: ...

    def render_form(self, source, flavor: str = ""): ...


class CollectionPlugin(SourcePlugin, Protocol):
    def inspect_collection(self, source) -> CollectionSpec: ...

    def resolve_collection_widget(
        self, spec: CollectionSpec, flavor: str = "std"
    ) -> WidgetSpec: ...

    def render_collection(
        self, source, spec: CollectionSpec, flavor: str = "std"
    ): ...


@dataclass(slots=True)
class PluginRegistration:
    name: str
    plugin: SourcePlugin
