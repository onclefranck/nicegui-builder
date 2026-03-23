# Product Roadmap

[Home](../README.md)

[Previous: Examples Roadmap](examples.md)

This roadmap tracks the next user-facing capabilities for `nicegui-builder`.

## 1. Rich Form Validation

Status: in progress

Goals:

- Support validation flows beyond submit-time only.
- Provide reusable helpers for field-specific validation messages.
- Support live validation on `change` and `blur`.
- Keep submit-time validation compatible with existing `apply_errors=True`.

## 2. Richer Pydantic Forms

Status: in progress

Goals:

- Improve support for nested models and collection-like fields.
- Add clearer automatic grouping and section heuristics.
- Make generated forms more useful without custom YAML.

Delivered so far:

- Structured values are serialized more cleanly for generated fields.
- Nested models are treated as structured fields by default.
- Collection-like fields are grouped separately.
- Automatic layouts now create simple sections such as `General`, `Nested models`, and `Collections`.

## 3. Stronger Tables

Status: completed

Goals:

- Add first-class sorting and pagination options.
- Add row selection helpers.
- Add basic export helpers.

Delivered:

- `TableHandle.sort_rows(...)`
- `TableHandle.set_pagination(...)` and `get_pagination()`
- `TableHandle.set_selected_rows(...)` and `get_selected_rows()`
- `TableHandle.export_csv(...)`
- stronger default table widget metadata for sorting, pagination, and selection

## 4. Smarter Filters

Status: completed

Goals:

- Support operators such as `contains`, `equals`, `between`, and `in`.
- Improve date and numeric filtering.
- Expose filter helpers through the collection handle layer.

Delivered:

- richer filter operators in the `pandas` plugin
- `TableHandle.set_filter(...)`
- `TableHandle.clear_filters()`
- stateful `TableHandle.apply_filters(...)`

## 5. Ready-Made Actions

Status: completed

Goals:

- Provide higher-level CRUD and toolbar helpers.
- Make common form and table actions easier to wire.
- Reuse the existing handle and spec architecture.

Delivered:

- `ActionSpec`
- form helpers: `create_button(...)`, `update_button(...)`, `delete_button(...)`, `crud_bar(...)`
- table helpers: `create_button(...)`, `delete_selected_button(...)`, `export_button(...)`, `crud_bar(...)`
