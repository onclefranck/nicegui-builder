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
