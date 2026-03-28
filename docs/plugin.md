# Plugin Development

[Home](../README.md)

[Previous: Table](table.md) | [Next: Architecture](architecture.md)

This document explains how to add a new source plugin to `nicegui-builder`.

## Goal

A plugin lets the library understand a new source type and translate it into:

- form-oriented specs
- collection-oriented specs
- default widgets
- optional rich rendering behaviors

Examples already present in the project:

- `pydantic` for schema-driven forms
- `pandas` for table-oriented collections

Both built-in source plugins are optional dependencies.
The base package stays importable without them, and each plugin registers itself only when its dependency is available.

## Mental Model

The core library should stay source-agnostic.
A plugin is responsible for understanding a specific source and producing core-friendly specs.

Typical pipeline:

`source -> plugin inspection -> specs -> widget resolution -> layout/rendering`

## Plugin Types

There are currently two practical plugin families.

### Field Plugins

Field plugins power `form(...)`.

Required entry-point methods:

- `supports(source)`
- `inspect_fields(source)`
- `resolve_field_node(model_class, model_instance, fieldname, value)`

Common but optional extension points:

- `build_layout(source, flavor="")`
- `build_field_context(model_class, model_instance, fieldname)`
- `resolve_widget(spec, variant="std")`
- `render_form(source, flavor="")`

See [`src/nicegui_builder/plugins/base.py`](../src/nicegui_builder/plugins/base.py).

### Collection Plugins

Collection plugins power `table(...)`.

Required entry-point methods:

- `supports(source)`
- `inspect_collection(source)`
- `resolve_collection_widget(spec, flavor="std")`

Common but optional extension points:

- `prepare_rows(source)`
- `filter_rows(source, filter_values)`
- `render_collection(source, spec, flavor="std")`

## Registration

Plugins are registered in the global plugin registry.

Minimal pattern:

```python
from nicegui_builder.plugins.registry import plugin_registry


class MyPlugin:
    name = "my_plugin"

    def supports(self, source) -> bool:
        ...


my_plugin = MyPlugin()
plugin_registry.register(my_plugin)
```

Built-in plugins are typically registered from their package `__init__.py`.

## What A Good Plugin Should Produce

### For forms

Your plugin should produce `FieldSpec` values rich enough to support:

- automatic widget choice
- labels and descriptions
- defaults
- validation constraints
- choices
- plugin-specific metadata in `source_meta`

### For collections

Your plugin should produce a `CollectionSpec` that describes:

- columns
- optional filter metadata
- source-level metadata

## Recommended Implementation Pattern

### 1. Start with `supports(...)`

Keep it strict and predictable.
If the plugin cannot fully support the source, return `False`.

### 2. Build clean specs first

Prefer putting source understanding into `FieldSpec` and `CollectionSpec` instead of mixing it directly into rendering code.

### 3. Keep widget resolution separate

A plugin should usually have a dedicated resolution step from spec to widget intent.

For example:

- YAML map for defaults
- Python heuristics for richer cases

### 4. Use rich rendering only when it adds real value

Most plugins should let the generic builder do the rendering.
Use `render_form(...)` or `render_collection(...)` only for behaviors that are meaningfully richer than generic rendering.

Current example:

- the `pandas` plugin uses `render_collection(..., flavor="filters")` for a richer filter UI

### 5. Normalize early

If a plugin accepts multiple convenient input shapes at its public boundary, prefer normalizing them early into one internal form.

Current examples:

- table filter clauses are normalized into a canonical internal shape before filtering
- builder nodes are normalized before method-chain rendering

## Pydantic Plugin Notes

The `pydantic` plugin is a good reference for form-oriented plugins.

Its code is organized under:

- [`src/nicegui_builder/plugins/pydantic/inspect.py`](../src/nicegui_builder/plugins/pydantic/inspect.py)
- [`src/nicegui_builder/plugins/pydantic/mapping.py`](../src/nicegui_builder/plugins/pydantic/mapping.py)
- [`src/nicegui_builder/plugins/pydantic/resolve.py`](../src/nicegui_builder/plugins/pydantic/resolve.py)
- [`src/nicegui_builder/plugins/pydantic/plugin.py`](../src/nicegui_builder/plugins/pydantic/plugin.py)
- [`src/nicegui_builder/plugins/pydantic/pydantic-nicegui.yml`](../src/nicegui_builder/plugins/pydantic/pydantic-nicegui.yml)

The YAML file is plugin-local on purpose, so the plugin stays self-contained.

One useful pattern in the `pydantic` plugin is the `datetime` split field.
That behavior is now centralized in the core as a dedicated `datetime_input` component so multiple plugins can reuse the same widget while still treating it as one logical value.
The `pydantic` resolver keeps the internal date/time inputs grouped as one logical field while still allowing the layout node to override the wrapper container.

Example:

```yaml
- field__starts_at:
    params:
      container:
        methods: column
        classes: gap-2
```

This means the plugin can provide a rich field expansion without forcing a single visual wrapper such as `row`.

The `pydantic` form flow also auto-registers field components in `component_refs`.
Default logical names use the form `field:<fieldname>`.
For split `datetime` fields, the logical ref resolves to a composite object with:

- `.container`
- `.date`
- `.time`

If the layout supplies `ref`, that explicit logical name is used instead.

## Pandas Plugin Notes

The `pandas` plugin is a good reference for collection-oriented plugins.

It shows how to:

- inspect a `DataFrame`
- infer column/filter metadata
- provide default table widgets
- optionally render a richer filtered table flavor with a filter builder and active filter list

It is also a good reference for:

- canonical filter clause handling
- validating/coercing filter values before applying them to the dataframe

See:

- [`src/nicegui_builder/plugins/pandas/plugin.py`](../src/nicegui_builder/plugins/pandas/plugin.py)

## Testing Guidance

A plugin should usually be tested at three levels:

1. `supports(...)`
2. spec generation
3. public entry point integration through `form(...)` or `table(...)`

Good tests are usually small and structural.
You do not need a full NiceGUI runtime for most plugin tests.

## Design Guidelines

- Keep the core source-agnostic.
- Prefer specs over ad hoc dictionaries.
- Use `source_meta` for plugin-specific metadata.
- Keep plugin-local maps and heuristics inside the plugin package.
- Favor small rich render flavors over plugin-wide custom rendering.
- Preserve compatibility with the stable top-level API.

## Future Plugin Candidates

Likely good additions:

- `dataclasses`
- `json_schema`
- `sqlmodel`
- `sqlalchemy`
- `polars`

`sqlmodel` is especially interesting if the project later grows stronger persistence-aware CRUD workflows.
