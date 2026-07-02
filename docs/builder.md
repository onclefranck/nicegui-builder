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

`builder(...)` also accepts runtime data and named callbacks:

```python
root = builder(
    layout,
    context={"items": items},
    handlers={"select": select_item},
    filters={"title": str.title},
)
```

Layouts can interpolate context with `{{ ... }}`, bind events with `on`, and render repeated children with `repeat`.

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

Refs declared inside `repeat` nodes are exposed as dictionaries keyed by the repeat key.

If a referenced component has children, the returned root component also exposes `rebuild(ref_name, context=None)`.
It clears that component and renders its original child template again with updated context.

## Related Documents

For the declarative layout language itself, see:

- [`docs/layout-schema.md`](layout-schema.md)
- [`schemas/layout.schema.json`](../schemas/layout.schema.json)

For concrete runnable examples, see:

- [`docs/examples.md`](examples.md)
