# Layout Schema

[Home](../README.md)

[Previous: Public API](public-api.md) | [Next: Examples Roadmap](examples.md)

This document explains the declarative layout language accepted by `builder(...)`, `form(...)`, and other entry points that eventually delegate to the builder.

It also documents the JSON Schema shipped with the project:

- [`schemas/layout.schema.json`](../schemas/layout.schema.json)

## Goal

The schema helps you catch structural mistakes early while writing YAML layouts:

- wrong root shape
- invalid node shape
- misplaced `children`
- unsupported keys like typos in `params` / `classes` / `props`
- plugin expansion nodes missing the expected object shape

It is intentionally strongest on structure.
It does not try to prove that every method name is a valid NiceGUI API call or that every `field__...` key matches a real model field.

## The Layout Shape

At the top level, a layout is a list of entries.
Each entry is an object with exactly one key.

Example:

```yaml
- card.tight:
    classes: w-full p-4 gap-3
    children:
      - label:
          params:
            text: Hello world
```

This corresponds to:

- one root list
- one node entry: `card.tight`
- one child node entry: `label`

## Standard Nodes

A standard node uses its key as the NiceGUI method chain.

Examples:

- `label`
- `card`
- `card.tight`
- `grid`

Supported configuration keys:

- `params`: keyword arguments passed to the resolved method
- `props`: props string passed to `.props(...)`
- `classes`: classes string passed to `.classes(...)`
- `ref`: optional string reference name stored in `component_refs`
- `on`: event-to-handler-name bindings
- `children`: nested layout entries
- `context`: reserved for future layout-time metadata

Example:

```yaml
- grid:
    ref: contact_grid
    params:
      columns: 12
    classes: w-full gap-3
    children:
      - label:
          params:
            text: Contact form
          classes: text-h6
```

If `ref` is present, the rendered component is added to the runtime `component_refs` dictionary under that name.
Duplicate ref names are rejected.

## Events

Use `on` to bind a NiceGUI or DOM event to a handler supplied from Python:

```yaml
- button:
    params:
      text: Save
    on:
      click: save
```

```python
root = builder(layout, handlers={"save": save})
```

Handler names must exist in the `handlers` mapping. Missing handlers fail during build.
The builder calls component methods such as `on_click(...)` or `on_value_change(...)` when present, and falls back to `component.on(event, handler)` for DOM-style event names.

## Expansion Nodes

An expansion node delegates resolution to a registered callback.
Today the most important built-in family is `field__...`.

Examples:

- `field__firstname`
- `field__email`
- `field__starts_at`

Expansion nodes support the same common keys as standard nodes, plus plugin-specific overrides such as:

- `methods`

Example:

```yaml
- field__email:
    methods: email
    classes: col-span-6
```

Another example with the split `datetime` widget:

```yaml
- field__starts_at:
    ref: starts_at
    params:
      container:
        methods: grid
        params:
          columns: 2
        classes: gap-2
    classes: col-span-12 gap-2
```

In that case:

- `field__starts_at` selects the field expansion callback
- `ref` names the logical component ref exposed at runtime
- `params.container` configures the internal wrapper component used by `datetime_input`
- node-level `classes` still apply to the `datetime_input` component itself

For `pydantic` field expansions:

- every field gets a logical ref even if you do not provide one explicitly
- the default logical name is `field:<fieldname>`
- split `datetime` fields also expose child refs with `:date` and `:time` suffixes

So the example above produces a logical ref named `starts_at`, plus child refs `starts_at:date` and `starts_at:time`.
The form handle then exposes the logical ref as a composite object with `.date` and `.time`.

## Null Values

You can omit the node body entirely by using `null`.

Example:

```yaml
- field__owner_name:
```

That is equivalent to:

```yaml
- field__owner_name: {}
```

This can be useful when the plugin default is already good enough.

## Dynamic Values

`params` accepts arbitrary JSON-like YAML values:

- strings
- numbers
- booleans
- `null`
- arrays
- nested objects

The builder resolves `{{ ... }}` tokens in `params`, `classes`, and `props` as Jinja expressions.

Examples:

```yaml
- label:
    params:
      text: "Hello {{ user.name }}"
- switch:
    params:
      value: "{{ enabled }}"
    classes: "w-full {{ extra_classes }}"
```

If the entire value is one token, the resolved object keeps its type.
That is why `value: "{{ enabled }}"` passes a boolean instead of the string `"True"`.

Dynamic expressions support:

- root names from `builder(..., context={...})` or the current repeat scope
- attribute paths such as `{{ user.name }}`
- item paths such as `{{ row['score'] }}`
- standard Jinja filters
- filters supplied from Python through `builder(..., filters={...})`, `form(..., filters={...})`, or `register_filter(...)`
- expression operators such as `{{ count > 0 }}` or `{{ price * quantity }}`
- regular Jinja attribute and call semantics, including dunder attributes such as `{{ source_class.__name__ }}`

```python
root = builder(
    layout,
    context={"user": user, "enabled": True},
    filters={"mmss": format_mmss},
)
```

Registered filters are available without passing them to each render call:

```python
from nicegui_builder import register_filter

register_filter("mmss", format_mmss)
```

`register_filter(...)` is a gateway to Jinja's native filter registration model.
The builder installs those registered callbacks on the Jinja environment used to render YAML values, so the YAML syntax remains ordinary Jinja filter syntax:

```yaml
text: "{{ duration | mmss }}"
```

Use `\{{` when a literal opening token is needed.
The Jinja literal form also works: `{{ '{{' }}`.

Only expression output is supported in layout values.
Jinja statement blocks and comments such as `{% if ... %}`, `{% for ... %}`, `{% set ... %}`, and `{# ... #}` are rejected.

The schema intentionally allows dynamic values as ordinary strings.
Their runtime meaning is documented here because JSON Schema cannot validate the context path or filter name itself.

The runtime context is intentionally small and operational.
In practice, layouts should treat it as helper data for formatting and callbacks, not as a place to depend on large amounts of implicit mutable state.

## Repeat Nodes

Use `repeat` to render one child template per item in a context iterable:

```yaml
- repeat:
    in: "{{ segments }}"
    as: seg
    key: "{{ seg.segment_id }}"
    children:
      - label:
          ref: segment_label
          params:
            text: "#{{ loop.index0 }} {{ seg.name }}"
```

For each item, the child scope includes:

- the item under the configured `as` name
- `loop.index0`, the zero-based index
- `loop.index`, the one-based index
- `loop.key`, when `key` is configured

Refs inside a repeat are collected as dictionaries keyed by `$key`, so `segment_label` becomes `root.component_refs["segment_label"][segment_id]`.

Handlers bound inside a repeat receive the current item first:

```python
def choose(segment, event=None):
    ...
```

## Rebuild

When a referenced container has children, the builder stores its original child template.
The returned root component exposes `rebuild(ref_name, context=None)`:

```python
root.rebuild("segments_panel", context={"segments": new_segments})
```

`rebuild` clears the referenced component and renders that stored child template again with the original context plus the provided context override.

## What The Schema Validates Well

The shipped schema is strong at validating:

- the top-level list shape
- one-entry-per-node objects
- standard vs expansion vs repeat node shapes
- the presence and type of `params`, `props`, `classes`, `ref`, `on`, `children`, and `context`
- plugin override keys currently used in layouts such as `methods`

## What The Schema Does Not Fully Validate

Some things are outside the reach of a practical static schema:

- whether `card.tight` or another method chain exists in NiceGUI
- whether a specific `field__name` actually exists on your model
- whether a plugin accepts a given `methods` override such as `email` or `textarea`
- whether a `params.container` override is meaningful for a given field/plugin
- whether a specialized component such as `datetime_input` imposes additional runtime invariants on that container config
- semantic correctness of Jinja context expressions and filter names in `{{ ... }}` strings

So the schema should be treated as a strong structural guardrail, not as a complete semantic type system.

## VS Code Setup

The most practical workflow in VS Code is:

1. install the `YAML` extension by Red Hat
2. associate your layout files with the shipped schema
3. optionally add a per-file schema directive for standalone layouts

### Recommended Extension

- `YAML` by Red Hat

This extension gives you:

- YAML validation
- hover help from the schema
- completion from the schema
- error reporting inside the editor

VS Code's built-in JSON support is usually enough for editing the schema file itself.

### Workspace Mapping

In `.vscode/settings.json`, you can associate patterns with the schema:

```json
{
  "yaml.schemas": {
    "./schemas/layout.schema.json": [
      "src/nicegui_builder/examples/**/*.yml",
      "src/nicegui_builder/examples/**/*.yaml",
      "**/*Builder.yml",
      "**/*Builder.yaml",
      "**/models/*.yml",
      "**/models/*.yaml"
    ]
  }
}
```

Adjust the file globs to match how your project stores layouts.

### Per-File Directive

If you want an individual layout file to opt into the schema explicitly, add this as the first line:

```yaml
# yaml-language-server: $schema=../../schemas/layout.schema.json
```

Use a relative path that makes sense from the file location.

## Practical Writing Advice

The schema is most useful when you lean into a few habits:

- keep each node to one key only
- use `children` only for nested nodes
- prefer `params` for widget arguments and `props` / `classes` for view tuning
- use expansion nodes like `field__...` only when a plugin owns that part of the tree
- keep plugin overrides explicit when you need them, for example `methods: email`

For ordinary layouts, start with standard nodes.
Reach for expansion nodes when a plugin should resolve the final widget for you.

## Related Files

- [`README.md`](../README.md)
- [`src/nicegui_builder/builder.py`](../src/nicegui_builder/builder.py)
- [`src/nicegui_builder/core/models.py`](../src/nicegui_builder/core/models.py)
- [`src/nicegui_builder/examples/demo_basic_builder.yml`](../src/nicegui_builder/examples/demo_basic_builder.yml)
- [`src/nicegui_builder/plugins/pydantic/examples/24_field_context_resolution.py`](../src/nicegui_builder/plugins/pydantic/examples/24_field_context_resolution.py)
