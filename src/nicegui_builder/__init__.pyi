from typing import Any, Protocol

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
from .core.datetime_inputs import DateTimeInput


class _ExtendedUI(Protocol):
    def builder(self, layout: Any) -> Any: ...
    datetime_input: type[DateTimeInput]
    def form_builder(self, source: Any, flavor: str = "") -> Any: ...
    def table_builder(self, source: Any, variant: str = "std") -> Any: ...
    def __getattr__(self, name: str) -> Any: ...


ui: _ExtendedUI

def builder(layout: Any) -> Any: ...
def form(source: Any, flavor: str = "") -> Any: ...
def table(source: Any, variant: str = "std") -> Any: ...

STABLE_API: tuple[str, ...]
EXPERIMENTAL_NAMESPACES: tuple[str, ...]

__all__: list[str]
