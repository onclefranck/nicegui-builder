# Table

[Home](../README.md)

[Previous: Form](form.md) | [Next: Plugin Development](plugin.md)

This document focuses on `table(...)`, the plugin-driven collection/table entry point.

## Goal

Use `table(...)` when you want a plugin to inspect a collection-like source and render a table.

## Minimal Example

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

## Flavors

For the `pandas` plugin, a richer filtered table flavor is also available:

```python
handle = table(df, flavor="filters")
```

Here too, `flavor` is used at the global view/layout level rather than as a local widget tweak.

## Filtered Table UI

The built-in filtered table UI exposes operator symbols out of the box:

- `∋` contains
- `=` equals
- `≠` not equals
- `>` greater than
- `≥` greater than or equal
- `<` less than
- `≤` less than or equal
- `⋖` starts with
- `⋗` ends with
- `∈` in
- `∉` not in
- `≈` regex
- `⋯` between

The UI lets you choose a field, an operator, and one or more values, then add that filter to an active filter list.
Active filters can be enabled or disabled with a checkbox and removed from the list without losing the builder state.
For `in` and `notIn`, the current UI accepts comma-separated values.
For numeric and datetime columns, `between` renders two inputs.
For `datetime` columns, the built-in filter UI reuses the same `datetime_input` component as the `pydantic` forms.

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
handle.set_filter("status", "confirmed, waitlist", op="in")
handle.apply_filters()
handle.normalized_filter_values()
handle.clear_filters()
```

`normalized_filter_values()` returns the active filter clauses in normalized form:

```python
{
    "name": {"op": "contains", "value": "ada"},
    "score": {"op": "between", "value": [10, 20]},
}
```

CRUD-style actions:

```python
handle.crud_bar(
    on_create=lambda table_handle: open_create_dialog(),
    on_delete_selected=lambda rows: delete_rows(rows),
    on_export=lambda csv_text: print(csv_text),
)
```

## Related Documents

- [`docs/plugin.md`](plugin.md)
- [`docs/examples.md`](examples.md)
- [`docs/public-api.md`](public-api.md)
