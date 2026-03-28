# Form

[Home](../README.md)

[Previous: Builder](builder.md) | [Next: Table](table.md)

This document focuses on `form(...)`, the plugin-driven form entry point.

## Goal

Use `form(...)` when you want a plugin to inspect a supported source and render a form.

## Minimal Example

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

## Flavors

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

The original intent of `flavor` is to let a developer choose among multiple layouts for the same model source.

## Datetime Fields

For `datetime` fields, the built-in `pydantic` plugin uses a dedicated `datetime_input` component.
That component internally renders a coordinated `date_input + time_input` pair as one logical field, and the layout can choose its wrapper container.

Example:

```yaml
- field__starts_at:
    params:
      container:
        methods: grid
        params:
          columns: 2
        classes: gap-2
    classes: col-span-12 gap-2
```

That lets you keep the internal date/time pair together while placing it inside a `row`, `column`, `grid`, or another declarative container.

## Component Refs

All `pydantic` fields are also exposed through `handle.component_refs`.
By default, field refs use the logical name `field:<fieldname>`.

For split `datetime` fields, the logical ref resolves to a composite object with `.date` and `.time`.

Example:

```python
starts_at = handle.component_refs["field:starts_at"]
starts_at.container
starts_at.date
starts_at.time
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

Component refs:

```python
handle.component_refs["field:email"]
handle.get_component("field:email")

starts_at = handle.component_refs["field:starts_at"]
starts_at.date
starts_at.time
```

## Related Documents

- [`docs/plugin.md`](plugin.md)
- [`docs/examples.md`](examples.md)
- [`docs/public-api.md`](public-api.md)
