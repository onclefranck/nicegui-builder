from nicegui import ui

from .builder import builder
from .core import (
    ActionSpec,
    FormHandle,
    FormSpec,
    FormState,
    FormValidationResult,
    LiveBadgeBinding,
    LiveBinding,
    LiveButtonBinding,
    LivePanelBinding,
    TableHandle,
    TableSpec,
    ViewHandle,
)
from .form import form
from .table import table


def _attach_to_ui() -> None:
    ui.builder = builder
    ui.form_builder = form
    ui.table_builder = table


_attach_to_ui()

STABLE_API = (
    "ui",
    "builder",
    "form",
    "table",
    "ActionSpec",
    "FormHandle",
    "FormSpec",
    "FormState",
    "FormValidationResult",
    "LiveBinding",
    "LiveButtonBinding",
    "LiveBadgeBinding",
    "LivePanelBinding",
    "TableHandle",
    "TableSpec",
    "ViewHandle",
)

EXPERIMENTAL_NAMESPACES = (
    "nicegui_builder.core",
    "nicegui_builder.plugins",
)

__all__ = [
    "ui",
    "builder",
    "ActionSpec",
    "form",
    "table",
    "FormHandle",
    "FormSpec",
    "FormState",
    "FormValidationResult",
    "LiveBadgeBinding",
    "LiveBinding",
    "LiveButtonBinding",
    "LivePanelBinding",
    "TableHandle",
    "TableSpec",
    "ViewHandle",
    "STABLE_API",
    "EXPERIMENTAL_NAMESPACES",
]
