# Examples Roadmap

[Home](../README.md)

[Previous: Public API](public-api.md) | [Next: Product Roadmap](product-roadmap.md)

This document proposes a progressive set of examples to document `nicegui-builder`.

The goal is to cover the public API in increasing order of complexity, while keeping each example focused and easy to understand.

## Principles

Each example should ideally:

- demonstrate one main idea
- stay small and readable
- introduce only a small amount of new surface area
- be runnable directly
- build naturally toward more advanced usage

## VS Code Debug Template

A ready-to-copy VS Code debug template lives at:

- [`src/nicegui_builder/examples/vscode/launch.json`](../src/nicegui_builder/examples/vscode/launch.json)

Usage:

1. Copy that file to `.vscode/launch.json` at the root of your working copy.
2. Open the "Run and Debug" panel in VS Code.
3. Pick the example you want to start.

Notes:

- the template launches example modules directly, e.g. `python -m nicegui_builder.examples.01_basic_builder`
- `console` is set to `integratedTerminal` so terminal-based stop helpers keep working during debugging
- the template assumes the project has already been installed in editable mode, e.g. `pip install -e .`
- if that step has not been done yet, VS Code will not be able to import `nicegui_builder`
- `Ctrl+C` is the portable way to stop a running example on Linux and Windows

## Phase 1: First Contact

These examples should help a user understand the project in a few minutes.

### 1. Basic declarative builder

Goal:

- show how `builder(...)` renders a YAML layout

Covers:

- YAML layout loading
- simple components
- `builder(...)`

Suggested file:

- `examples/01_basic_builder.py`

### 2. Builder from inline Python dictionary

Goal:

- show that layouts can also be provided as Python data structures

Covers:

- inline layout
- no external YAML file

Suggested file:

- `examples/02_inline_builder.py`

### 3. First automatic Pydantic form

Goal:

- show the simplest possible `form(MyModel)`

Covers:

- automatic plugin resolution
- default auto-layout
- default widget mapping

Suggested file:

- `examples/03_pydantic_form_basic.py`

### 4. First automatic Pandas table

Goal:

- show the simplest possible `table(df)`

Covers:

- automatic plugin resolution
- default table rendering

Suggested file:

- `examples/04_pandas_table_basic.py`

## Phase 2: Core Usage Patterns

These examples should explain the main public entry points more fully.

### 5. Pydantic form with YAML layout

Goal:

- show how a YAML file overrides the automatic layout

Covers:

- class-named YAML layout
- `field__...` nodes
- basic layout customization

Suggested file:

- `examples/05_pydantic_form_yaml.py`

### 6. Pydantic automatic flavors

Goal:

- show `std`, `compact`, `detail`, `filters`, and `actionable`

Covers:

- flavor selection
- plugin-provided layouts

Suggested file:

- `examples/06_pydantic_form_flavors.py`

### 7. Pydantic field mapping variants

Goal:

- show how to force variants like `password`, `textarea`, `radio`, and `search`

Covers:

- `methods` override
- plugin map usage

Suggested file:

- `examples/07_pydantic_field_variants.py`

### 8. Pydantic structured fields

Goal:

- show nested models, collections, and structured sections

Covers:

- nested `BaseModel`
- lists and dict-like values
- generated sections

Suggested file:

- `examples/08_pydantic_structured_fields.py`

### 9. Datetime split input

Goal:

- show the aggregated `date + time` behavior for `datetime`

Covers:

- default `datetime` resolution
- split widgets
- collected combined value
- choosing a wrapper container from the layout when desired

Suggested file:

- `examples/09_pydantic_datetime_split.py`

### 10. Filtered Pandas table

Goal:

- show `table(df, variant="filters")`

Covers:

- rich plugin rendering
- a filter builder with an active filter list
- automatic filter metadata
- operator symbols, comma-separated `in` / `notIn`, and `between`

Suggested file:

- `examples/10_pandas_table_filters.py`

## Phase 3: Handles And Runtime Interaction

These examples should explain what users can do after rendering.

### 11. FormHandle basics

Goal:

- show `get_values()`, `set_values()`, `reset_*()`

Covers:

- `FormHandle`
- runtime value manipulation

Suggested file:

- `examples/11_form_handle_basics.py`

### 12. Form validation and error handling

Goal:

- show `validate()`, `apply_errors()`, `error_panel()`

Covers:

- `FormValidationResult`
- field errors
- validation display

Suggested file:

- `examples/12_form_validation.py`

### 13. Form submit and model reconstruction

Goal:

- show `submit(...)`, `to_model()`, `as_model=True`

Covers:

- callback submission
- Pydantic model reconstruction

Suggested file:

- `examples/13_form_submit.py`

### 14. Dirty tracking

Goal:

- show `changed_fields()`, `is_dirty()`, `changed_badge()`

Covers:

- dirty state
- status helpers

Suggested file:

- `examples/14_form_dirty_state.py`

### 15. Live form helpers

Goal:

- show `live_dirty_badge()`, `live_submit_button()`, `live_reset_button()`, `live_error_panel()`

Covers:

- event-driven live bindings
- live strategies

Suggested file:

- `examples/15_form_live_helpers.py`

### 16. Action bar and actionable flavor

Goal:

- show `action_bar(...)` combined with `flavor="actionable"`

Covers:

- built-in action/status/error areas
- strategy-based live buttons

Suggested file:

- `examples/16_form_actionable.py`

### 17. CRUD-ready form actions

Goal:

- show `create_button`, `update_button`, `delete_button`, `crud_bar`

Covers:

- ready-made actions
- callback-driven CRUD wiring

Suggested file:

- `examples/17_form_crud.py`

### 18. TableHandle basics

Goal:

- show `get_rows()`, `set_rows()`, `sort_rows()`

Covers:

- `TableHandle`
- runtime table manipulation

Suggested file:

- `examples/18_table_handle_basics.py`

### 19. Table pagination, selection, and export

Goal:

- show table runtime helpers beyond filtering

Covers:

- pagination
- selected rows
- CSV export

Suggested file:

- `examples/19_table_pagination_selection_export.py`

### 20. CRUD-ready table actions

Goal:

- show `crud_bar(...)` on tables

Covers:

- create action
- delete selected
- export action

Suggested file:

- `examples/20_table_crud.py`

## Phase 4: CLI Examples

These examples should connect the documentation to the CLI.

### 21. Running bundled examples from the CLI

Goal:

- show `nicegui-builder examples list` and `examples run`

Covers:

- example discovery
- quick launch workflow

Suggested file:

- `examples/21_cli_examples.py`

### 22. Running a layout file from the CLI

Goal:

- show `nicegui-builder layout run ...`

Covers:

- quick layout iteration

Suggested file:

- `examples/22_cli_layout_run.py`

Recommended standalone layout file:

- `src/nicegui_builder/examples/layouts/festival_notice.yml`

### 23. Running a form source from the CLI

Goal:

- show `nicegui-builder form run module:Class`

Covers:

- quick form testing
- flavor experimentation

Suggested file:

- `examples/23_cli_form_run.py`

## Phase 5: Advanced Plugin-Oriented Examples

These examples should help advanced users and future contributors.

### 24. How field context is resolved

Goal:

- explain the `field__...` expansion model

Covers:

- builder context
- plugin field resolution

Suggested file:

- `examples/24_field_context_resolution.py`

### 25. Plugin-local map customization

Goal:

- show how widget choices come from plugin-local mapping

Covers:

- `pydantic-nicegui.yml`
- variant defaults

Suggested file:

- `examples/25_plugin_mapping_customization.py`

### 26. Writing a minimal custom plugin

Goal:

- show the smallest useful plugin possible

Covers:

- `supports(...)`
- registration
- `inspect_fields(...)` or `inspect_collection(...)`

Suggested file:

- `examples/26_custom_plugin_minimal.py`

## Recommended Initial Implementation Order

If these examples are implemented in a later pass, the most useful first wave would be:

1. `01_basic_builder`
2. `03_pydantic_form_basic`
3. `04_pandas_table_basic`
4. `05_pydantic_form_yaml`
5. `06_pydantic_form_flavors`
6. `09_pydantic_datetime_split`
7. `11_form_handle_basics`
8. `12_form_validation`
9. `15_form_live_helpers`
10. `10_pandas_table_filters`
11. `19_table_pagination_selection_export`
12. `21_cli_examples`

## Coverage Summary

This proposed set covers:

- `builder(...)`
- `form(...)`
- `table(...)`
- automatic layouts and YAML layouts
- `pydantic` flavors and widget variants
- `datetime` split rendering
- `FormHandle`, `FormState`, `FormValidationResult`
- `TableHandle`
- live bindings
- CRUD helpers
- CLI usage
- plugin-oriented extension concepts
