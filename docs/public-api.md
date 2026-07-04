# Public API

[Home](../README.md)

[Previous: Architecture](architecture.md) | [Next: Builder](builder.md)

This document defines the supported public API surface for `nicegui-builder`.

## Stable

Imports from the top-level package are considered the stable API:

```python
from nicegui_builder import (
    builder,
    form,
    register_filter,
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

The following utility import is also part of the supported public surface:

```python
from nicegui_builder.utils import load_layout
```

`load_layout(...)` loads a YAML layout from an explicit path, or from a sidecar `.yml` / `.yaml` file adjacent to the calling module when only a layout name is provided.

In addition, the observable behavior of the top-level entry points is part of the stable contract.
Examples:

- `builder(...)` returns the root component and may attach `component_refs` plus `rebuild(ref_name, context=None)` when layouts declare refs
- `builder(..., context=..., handlers=..., filters=...)` supplies dynamic layout data, named event handlers, and call-specific Jinja filters
- `form(..., filters=...)` supplies call-specific Jinja filters when rendering a YAML-backed form layout
- `register_filter(name, callback)` registers a callback into the builder's package-level Jinja filter registry for later builder and form renders
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
