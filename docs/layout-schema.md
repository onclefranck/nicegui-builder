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

## Expansion Nodes

An expansion node delegates resolution to a registered callback.
Today the most important built-in family is `field__...`.

Examples:

- `field__firstname`
- `field__email`
- `field__starts_at`

Expansion nodes support the same common keys as standard nodes, plus plugin-specific overrides such as:

- `methods`
- `container`

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
    container: grid
    params:
      columns: 2
    classes: col-span-12 gap-2
```

In that case:

- `field__starts_at` selects the field expansion callback
- `ref` names the logical component ref exposed at runtime
- `container` overrides the wrapper component used for the split `date_input + time_input`
- `params` and `classes` apply to that wrapper container

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

## `params` Values

`params` accepts arbitrary JSON-like YAML values:

- strings
- numbers
- booleans
- `null`
- arrays
- nested objects

The builder also resolves two special string conventions at runtime:

- strings starting with `_`
  - treated as Python `str.format(**context)` templates
- strings starting with `$`
  - treated as `module:function` callbacks that receive the current builder context

Examples:

```yaml
- label:
    params:
      text: _Hello {name}
```

```yaml
- label:
    params:
      text: $my_app.layout_helpers:format_title
```

The schema intentionally allows those values as ordinary strings.
Their runtime meaning is documented here because JSON Schema cannot validate the import target itself.

The runtime context is intentionally small and operational.
In practice, layouts should treat it as helper data for formatting and callbacks, not as a place to depend on large amounts of implicit mutable state.

## What The Schema Validates Well

The shipped schema is strong at validating:

- the top-level list shape
- one-entry-per-node objects
- standard vs expansion node shapes
- the presence and type of `params`, `props`, `classes`, `ref`, `children`, and `context`
- plugin override keys currently used in layouts such as `methods` and `container`

## What The Schema Does Not Fully Validate

Some things are outside the reach of a practical static schema:

- whether `card.tight` or another method chain exists in NiceGUI
- whether a specific `field__name` actually exists on your model
- whether a plugin accepts a given `methods` override such as `email` or `textarea`
- whether a `container` override is meaningful for a given field/plugin
- semantic correctness of runtime context expressions in `_...` or `$module:function` strings

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
- [`src/nicegui_builder/examples/24_field_context_resolution.py`](../src/nicegui_builder/examples/24_field_context_resolution.py)
