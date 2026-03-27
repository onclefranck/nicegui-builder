# Public API

[Home](../README.md)

[Previous: Architecture](architecture.md) | [Next: Layout Schema](layout-schema.md)

This document defines the supported public API surface for `nicegui-builder`.

## Stable

Imports from the top-level package are considered the stable API:

```python
from nicegui_builder import (
    builder,
    form,
    table,
    ActionSpec,
    FormHandle,
    FormSpec,
    FormState,
    FormValidationResult,
    LiveBinding,
    LiveButtonBinding,
    LiveBadgeBinding,
    LivePanelBinding,
    TableHandle,
    TableSpec,
    ViewHandle,
)
```

These names are expected to remain importable across normal library evolution.

In addition, the observable behavior of the top-level entry points is part of the stable contract.
Examples:

- `builder(...)` returns the root component and may attach `component_refs` when layout nodes declare `ref`
- `form(...)` returns a `FormHandle` with `component_refs` and `get_component(ref)`
- `table(...)` returns a `TableHandle` with the documented handle helpers

The package also re-exports `ui` and patches the imported NiceGUI `ui` object at runtime with:

- `ui.builder(...)`
- `ui.datetime_input(...)`
- `ui.form_builder(...)`
- `ui.table_builder(...)`

That behavior is supported by `nicegui-builder`, but it is still a patch-style integration layered on top of NiceGUI's own `ui` module.
It should be treated as a convenience contract of this package, not as an upstream NiceGUI guarantee.

For editor completion in this repository, the package also ships local partial stubs under [`typings/nicegui`](../typings/nicegui).
Those stubs are intentionally marked `partial` so they extend NiceGUI's own type information rather than replacing the native signatures.
The main workspace stub [`typings/nicegui/ui.pyi`](../typings/nicegui/ui.pyi) is generated from NiceGUI's own `ui` module by [`scripts/generate_nicegui_ui_stub.py`](../scripts/generate_nicegui_ui_stub.py) and is checked by CI to avoid drift.

## Advanced / Experimental

The following namespaces remain available for advanced use, but are not yet treated as stable contracts:

- `nicegui_builder.core`
- `nicegui_builder.plugins`

They may evolve more aggressively as the library continues to grow.

## Internal

Everything else should be treated as internal implementation detail unless explicitly promoted later.

Examples:

- `nicegui_builder.plugins.pydantic.inspect`
- `nicegui_builder.plugins.pydantic.mapping`
- `nicegui_builder.plugins.pydantic.resolve`
- workspace editor stub wiring such as [`typings/nicegui/ui.pyi`](../typings/nicegui/ui.pyi)
