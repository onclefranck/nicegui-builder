# nicegui-builder

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue.svg)](pyproject.toml)
[![CI](https://github.com/onclefranck/nicegui-builder/actions/workflows/ci.yml/badge.svg)](https://github.com/onclefranck/nicegui-builder/actions/workflows/ci.yml)
[![Publish TestPyPI](https://github.com/onclefranck/nicegui-builder/actions/workflows/publish-testpypi.yml/badge.svg)](https://github.com/onclefranck/nicegui-builder/actions/workflows/publish-testpypi.yml)
[![Publish PyPI](https://github.com/onclefranck/nicegui-builder/actions/workflows/publish-pypi.yml/badge.svg)](https://github.com/onclefranck/nicegui-builder/actions/workflows/publish-pypi.yml)

`nicegui-builder` is a Python library for building NiceGUI interfaces from declarative layouts and schema-aware plugins.

It currently provides three main entry points:

- `builder(layout)` for declarative NiceGUI rendering
- `form(source, flavor="")` for plugin-driven forms
- `table(source, variant="std")` for plugin-driven tabular views

## Install

Base install:

```bash
pip install nicegui-builder
```

Optional `pandas` support:

```bash
pip install "nicegui-builder[pandas]"
```

CLI entry point:

```bash
nicegui-builder --help
```

## Stable API

Top-level imports from `nicegui_builder` are the supported stable public API.
See `docs/public-api.md` for the current stable surface.

## Quick Start

### `builder(layout)`

Use `builder(...)` when you already have a declarative layout.

```python
import yaml
from pathlib import Path

from nicegui import ui
from nicegui_builder import builder

layout = yaml.safe_load(
    Path("src/nicegui_builder/examples/demo_basic_builder.yml").read_text(encoding="utf-8")
)

builder(layout)
ui.run()
```

### `form(source, flavor="")`

Use `form(...)` when you want a plugin to inspect a supported source and render a form.

```python
from pydantic import BaseModel
from nicegui import ui

from nicegui_builder import form


class Contact(BaseModel):
    firstname: str
    lastname: str
    email: str


handle = form(Contact)
ui.run()
```

If a matching YAML layout is not found, the plugin can fall back to an automatic layout.

Built-in automatic `pydantic` flavors:

- `std`: responsive editable grid
- `compact`: simple stacked editable layout
- `detail`: read-only detail view
- `filters`: search-oriented filter form
- `actionable`: editable layout with status, error, and action areas

Examples:

```python
form(Contact, flavor="compact")
form(Contact, flavor="detail")
form(Contact, flavor="filters")
handle = form(Contact, flavor="actionable")
```

For `datetime` fields, the built-in `pydantic` plugin uses a split `date_input + time_input` widget by default.
That split stays grouped as one logical field, but the layout can choose its wrapper container.

Example:

```yaml
- field__starts_at:
    container: grid
    params:
      columns: 2
    classes: col-span-12 gap-2
```

That lets you keep the date/time pair together while placing it inside a `row`, `column`, `grid`, or another declarative container.

### `table(source, variant="std")`

Use `table(...)` when you want a plugin to inspect a collection-like source and render a table.

```python
import pandas as pd
from nicegui import ui

from nicegui_builder import table


df = pd.DataFrame(
    [
        {"name": "Ada", "country": "UK"},
        {"name": "Grace", "country": "US"},
    ]
)

handle = table(df)
ui.run()
```

For the `pandas` plugin, a richer filtered table variant is also available:

```python
handle = table(df, variant="filters")
```

## Working With Form Handles

`form(...)` returns a `FormHandle`.

Read values:

```python
handle.get_values()
```

Rebuild a model:

```python
handle.to_model()
handle.submit(lambda model: print(model), as_model=True)
```

Validate:

```python
result = handle.validate(as_model=True)
print(result.valid)
print(result.errors_by_field())
print(result.error_messages())
```

Reset:

```python
handle.reset_to_source()
handle.reset_to_defaults()
handle.reset_to_empty()
```

Track changes:

```python
handle.changed_fields()
handle.is_dirty()
```

Live helpers:

```python
handle.live_dirty_badge()
handle.live_reset_button()
handle.live_submit_button(
    "Save",
    lambda model: print(model),
    as_model=True,
    strategy="dirty_and_valid",
)
handle.live_error_panel(as_model=True, strategy="invalid")
```

Validation helpers:

```python
handle.apply_errors(as_model=True)
handle.clear_errors()
handle.validate_field("email", as_model=True)
handle.field_error_message("email", as_model=True)
handle.apply_field_errors("email", as_model=True)
handle.live_validation(as_model=True, mode="change")
```

Action helpers:

```python
handle.submit_button("Save", lambda model: print(model), as_model=True)
handle.reset_button()

handle.create_button(lambda model: save_new(model))
handle.update_button(lambda model: save_existing(model))
handle.delete_button(lambda instance: delete_instance(instance))

handle.crud_bar(
    on_create=lambda model: save_new(model),
    on_update=lambda model: save_existing(model),
    on_delete=lambda instance: delete_instance(instance),
)

handle.action_bar(
    "Save",
    lambda model: print(model),
    as_model=True,
    live_changed_badge=True,
    live_reset_button=True,
    live_submit_button=True,
    submit_strategy="dirty_and_valid",
)
```

## Working With Table Handles

`table(...)` returns a `TableHandle`.

Inspect the table:

```python
handle.spec
handle.component
handle.get_rows()
```

Sort, paginate, select, and export:

```python
handle.sort_rows("name")
handle.set_pagination(rows_per_page=25, sort_by="score", descending=True)
handle.set_selected_rows([{"name": "Ada"}])
csv_text = handle.export_csv()
```

Filter:

```python
handle.set_filter("name", "ada", op="contains")
handle.set_filter("score", [10, 20], op="between")
handle.apply_filters()
handle.clear_filters().apply_filters()
```

CRUD-style actions:

```python
handle.crud_bar(
    on_create=lambda table_handle: open_create_dialog(),
    on_delete_selected=lambda rows: delete_rows(rows),
    on_export=lambda csv_text: print(csv_text),
)
```

## CLI

The project also exposes a small CLI for quick experimentation.

List bundled examples:

```bash
nicegui-builder examples list
```

Run a bundled example:

```bash
nicegui-builder examples run 01_basic_builder --port 8080
nicegui-builder examples run 03_pydantic_form_basic --port 8080
```

Render a YAML layout directly:

```bash
nicegui-builder layout run path/to/layout.yml --port 8080
```

Render a form from a Python object path:

```bash
nicegui-builder form run my_module:MyModel --flavor actionable --port 8080
```

This is especially useful to:

- launch bundled examples quickly
- test a declarative layout without writing a dedicated script
- try a form source interactively while tuning layouts and flavors

Use `Ctrl+C` as the normal cross-platform way to stop a running CLI session.

## Pydantic Field Mapping

The `pydantic` plugin resolves `field__...` nodes using:

- field type
- field constraints and metadata
- plugin-local widget mapping in `src/nicegui_builder/plugins/pydantic/pydantic-nicegui.yml`

Example:

```yaml
- card.tight:
    classes: p-3 gap-3
    children:
    - label:
        params:
          text: Contact info form
    - grid:
        params:
          columns: 12
        classes: w-full
        children:
        - field__firstname:
            classes: col-span-6
        - field__lastname:
            classes: col-span-6
        - field__email:
            methods: email
            classes: w-full
        - field__starts_at:
            container: grid
            params:
              columns: 2
            classes: col-span-12 gap-2
```

## More Docs

- `docs/public-api.md`: stable public API
- `docs/plugin.md`: how to build a new plugin
- `docs/architecture.md`: architecture and class diagram
- `docs/publishing.md`: TestPyPI and PyPI publishing guide
- `docs/product-roadmap.md`: roadmap history
