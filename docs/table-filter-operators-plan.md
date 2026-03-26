# Table Filter Operators Plan

[Home](../README.md)

This document captures the implementation plan for out-of-the-box filter operator selection in table layouts, primarily for the `pandas` table plugin.

## Decisions

- Include the following built-in filter operators:
  - `contains` `∋`
  - `equals` `=`
  - `notEquals` `≠`
  - `gt` `>`
  - `gte` `≥`
  - `lt` `<`
  - `lte` `≤`
  - `startsWith` `⋖`
  - `endsWith` `⋗`
  - `in` `∈`
  - `notIn` `∉`
  - `regex` `≈`
  - `between` `⋯`
- Support `between` in v1 for numeric and datetime filters.
- Do not expose `between` for text or boolean filters in v1.
- Start `in` and `notIn` with comma-separated input.
- Use operator symbols only in the UI.
- Let developers control which filter operators are offered later through metadata/configuration.

## Plan

### 1. Create a centralized operator definition

- Add a canonical registry for:
  - `contains`, `equals`, `notEquals`, `gt`, `gte`, `lt`, `lte`, `startsWith`, `endsWith`, `in`, `notIn`, `regex`, `between`
- Store at minimum:
  - identifier
  - Unicode symbol
- Reuse this registry for:
  - `pandas` filtering logic
  - filter UI rendering
  - tests

### 2. Update operator availability by pandas column type

- Text:
  - `contains`, `equals`, `notEquals`, `startsWith`, `endsWith`, `in`, `notIn`, `regex`
- Numeric:
  - `equals`, `notEquals`, `gt`, `gte`, `lt`, `lte`, `in`, `notIn`, `between`
- Boolean:
  - `equals`, `notEquals`
- Datetime:
  - `equals`, `notEquals`, `gt`, `gte`, `lt`, `lte`, `between`
- Select/choices:
  - `equals`, `notEquals`, `in`, `notIn`

### 3. Extend the pandas filtering engine

- Implement missing text operators:
  - `notEquals`, `startsWith`, `endsWith`, `notIn`, `regex`
- Implement missing scalar/datetime operators:
  - `notEquals`, `gte`, `lte`, `notIn`
- Keep `between` for numeric and datetime values.
- Support:
  - `in` / `notIn` via comma-separated parsing
  - `between` via two-value input

### 4. Enrich filter metadata for UI rendering

- Extend filter `FieldSpec.source_meta` with:
  - available operators
  - filter kind
  - value mode:
    - `single`
    - `list`
    - `range`

### 5. Evolve the `filters` table UI

- Add an operator selector for each filter field.
- Display the operator symbol only.
- Render the correct value input shape:
  - single-value operators: one field
  - `in` / `notIn`: one comma-separated text field
  - `between`: two fields
- Store filter values in normalized form:
  - `{"op": ..., "value": ...}`

### 6. Keep `TableHandle` integration stable

- Keep `set_filter(field_name, value, op=...)` as the primary API.
- Ensure `normalized_filter_values()` and `apply_filters()` support the new operator/value formats without breaking current usage.

### 7. Add tests

- Text operator coverage
- Numeric and datetime operator coverage
- Comma-separated `in` / `notIn`
- Numeric and datetime `between`
- Filter UI operator selection
- `TableHandle` API integration

### 8. Update docs and examples

- Document the available operators.
- Add at least one `between` example.
- Update the filtered pandas table example to show operator selection.

## Recommended Implementation Order

1. Central operator registry and pandas filtering engine
2. Filter UI updates
3. Tests
4. Documentation and examples
