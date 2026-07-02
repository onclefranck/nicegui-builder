from collections.abc import Callable
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
    def builder(
        self,
        layout: Any,
        *,
        context: dict[str, Any] | None = None,
        handlers: dict[str, Callable[..., Any]] | None = None,
        filters: dict[str, Callable[..., Any]] | None = None,
    ) -> Any: ...
    datetime_input: type[DateTimeInput]
    def form_builder(self, source: Any, flavor: str = "") -> Any: ...
    def table_builder(self, source: Any, flavor: str = "std") -> Any: ...
    def __getattr__(self, name: str) -> Any: ...

ui: _ExtendedUI

def builder(
    layout: Any,
    *,
    context: dict[str, Any] | None = None,
    handlers: dict[str, Callable[..., Any]] | None = None,
    filters: dict[str, Callable[..., Any]] | None = None,
) -> Any: ...
def form(source: Any, flavor: str = "") -> Any: ...
def table(source: Any, flavor: str = "std") -> Any: ...

STABLE_API: tuple[str, ...]
EXPERIMENTAL_NAMESPACES: tuple[str, ...]

__all__: list[str]
