# Builder

[Home](../README.md)

[Previous: Public API](public-api.md) | [Next: Form](form.md)

This document focuses on `builder(...)`, the declarative entry point of `nicegui-builder`.

## Goal

Use `builder(...)` when you already have a declarative layout and want it rendered as NiceGUI components.

## Minimal Example

```python
from nicegui import ui
from nicegui_builder import builder
from nicegui_builder.utils import load_layout

layout = load_layout("demo_basic_builder")

builder(layout)
ui.run()
```

`load_layout(...)` is a small convenience helper for YAML layouts.
If you pass only a layout name and a matching `.yml` or `.yaml` file lives next to the calling Python module, that adjacent file is loaded automatically.
Otherwise, the provided path is used as-is.

## Return Value

`builder(...)` returns the root NiceGUI component.

If layout nodes declare `ref`, that root component also exposes a `component_refs` dictionary for later lookup.

Example:

```yaml
- card:
    ref: profile_card
    children:
      - label:
          ref: title_label
          params:
            text: Profile
```

```python
root = builder(layout)
root.component_refs["profile_card"]
root.component_refs["title_label"]
```

## Related Documents

For the declarative layout language itself, see:

- [`docs/layout-schema.md`](layout-schema.md)
- [`schemas/layout.schema.json`](../schemas/layout.schema.json)

For concrete runnable examples, see:

- [`docs/examples.md`](examples.md)
