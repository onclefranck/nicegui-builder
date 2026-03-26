import csv
from collections.abc import Callable
from dataclasses import dataclass, field
import io

from nicegui import ui

from .actions import TABLE_ACTION_SPECS, apply_action_intent, get_action_spec
from .filter_operators import normalize_filter_operator
from .models import ActionSpec, TableSpec
from .view import ViewHandle


@dataclass(slots=True)
class TableHandle(ViewHandle):
    table_spec: TableSpec
    filter_values: dict[str, object] = field(default_factory=dict)

    @property
    def spec(self) -> TableSpec:
        return self.table_spec

    @property
    def component(self):
        return self.root_component

    def _filter_store(self) -> dict[str, object]:
        component_filters = getattr(self.component, "filter_values", None)
        if isinstance(component_filters, dict):
            self.filter_values = component_filters
        return self.filter_values

    def _refresh_filter_ui(self) -> None:
        callback = getattr(self.component, "refresh_filters_ui", None)
        if callable(callback):
            callback()

    def normalized_filter_values(self) -> dict[str, object]:
        normalized: dict[str, object] = {}
        for field_name, raw_value in self._filter_store().items():
            if raw_value in (None, "", []):
                continue

            if isinstance(raw_value, dict):
                if raw_value.get("enabled") is False:
                    continue
                operator = normalize_filter_operator(raw_value.get("op", "equals"))
                value = raw_value.get("value")
                if value in (None, "", []):
                    continue
                normalized[field_name] = {"op": operator, "value": value}
                continue

            normalized[field_name] = raw_value

        return normalized

    def _row_key_name(self) -> str | None:
        widget_spec = self.table_spec.widget_spec
        if widget_spec is None:
            return None
        return widget_spec.params.get("row_key")

    def _uses_internal_row_ids(self) -> bool:
        return self._row_key_name() == "nicegui_builder_row_id"

    def _strip_internal_row_id(self, row: dict) -> dict:
        if not self._uses_internal_row_ids():
            return dict(row)
        stripped = dict(row)
        stripped.pop("nicegui_builder_row_id", None)
        return stripped

    def _ensure_internal_row_ids(self, rows: list[dict]) -> list[dict]:
        if not self._uses_internal_row_ids():
            return [dict(row) for row in rows]

        prepared: list[dict] = []
        used_ids = set()

        for row in rows:
            prepared_row = dict(row)
            row_id = prepared_row.get("nicegui_builder_row_id")
            if row_id is None or row_id in used_ids:
                row_id = 0
                while row_id in used_ids:
                    row_id += 1
            prepared_row["nicegui_builder_row_id"] = row_id
            used_ids.add(row_id)
            prepared.append(prepared_row)

        return prepared

    def action_spec(self, name: str) -> ActionSpec:
        return get_action_spec(TABLE_ACTION_SPECS, name)

    def get_rows(self) -> list[dict]:
        if self.component is not None and hasattr(self.component, "rows"):
            rows = list(getattr(self.component, "rows"))
            return [self._strip_internal_row_id(row) for row in rows]

        source = self.table_spec.source
        if hasattr(source, "to_dict"):
            return source.to_dict(orient="records")

        return []

    def set_rows(self, rows: list[dict]):
        if self.component is not None and hasattr(self.component, "rows"):
            self.component.rows = self._ensure_internal_row_ids(rows)
            if hasattr(self.component, "update"):
                self.component.update()
        return self

    def sort_rows(self, column_name: str, *, descending: bool = False):
        rows = self.get_rows()
        sorted_rows = sorted(
            rows,
            key=lambda row: (row.get(column_name) is None, row.get(column_name)),
            reverse=descending,
        )
        self.set_pagination(sort_by=column_name, descending=descending)
        return self.set_rows(sorted_rows)

    def get_pagination(self) -> dict:
        if self.component is not None and hasattr(self.component, "pagination"):
            pagination = getattr(self.component, "pagination")
            if pagination is None:
                return {}
            return dict(pagination)

        widget_spec = self.table_spec.widget_spec
        if widget_spec is None:
            return {}
        return dict(widget_spec.params.get("pagination") or {})

    def set_pagination(
        self,
        *,
        rows_per_page: int | None = None,
        sort_by: str | None = None,
        descending: bool | None = None,
    ):
        pagination = self.get_pagination()

        if rows_per_page is not None:
            pagination["rowsPerPage"] = rows_per_page
        if sort_by is not None:
            pagination["sortBy"] = sort_by
        if descending is not None:
            pagination["descending"] = descending

        if self.component is not None and hasattr(self.component, "pagination"):
            self.component.pagination = pagination
            if hasattr(self.component, "update"):
                self.component.update()

        if self.table_spec.widget_spec is not None:
            self.table_spec.widget_spec.params["pagination"] = pagination

        return self

    def get_selected_rows(self) -> list[dict]:
        if self.component is not None and hasattr(self.component, "selected"):
            selected = list(getattr(self.component, "selected") or [])
            return [self._strip_internal_row_id(row) for row in selected]
        return []

    def set_selected_rows(self, rows: list[dict]):
        if self.component is not None and hasattr(self.component, "selected"):
            if self._uses_internal_row_ids() and hasattr(self.component, "rows"):
                selected = []
                used_indexes = set()
                component_rows = list(getattr(self.component, "rows") or [])
                for target in rows:
                    for index, row in enumerate(component_rows):
                        if index in used_indexes:
                            continue
                        if self._strip_internal_row_id(row) == dict(target):
                            selected.append(row)
                            used_indexes.add(index)
                            break
                self.component.selected = selected
            else:
                self.component.selected = list(rows)
            if hasattr(self.component, "update"):
                self.component.update()
        return self

    def export_csv(self, path: str | None = None) -> str:
        rows = self.get_rows()
        columns = [column.name for column in self.table_spec.collection_spec.columns]

        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column) for column in columns})

        csv_text = buffer.getvalue()
        if path is not None:
            with open(path, "w", encoding="utf-8", newline="") as file:
                file.write(csv_text)

        return csv_text

    def action_button(self, label: str, callback, **button_kwargs):
        return ui.button(label, on_click=callback, **button_kwargs)

    def create_button(self, callback, **button_kwargs):
        spec = self.action_spec("create")
        apply_action_intent(spec, button_kwargs)
        return self.action_button(spec.label, lambda *_args, **_kwargs: callback(self), **button_kwargs)

    def delete_selected_button(self, callback, **button_kwargs):
        spec = self.action_spec("delete_selected")
        apply_action_intent(spec, button_kwargs)
        return self.action_button(
            spec.label,
            lambda *_args, **_kwargs: callback(self.get_selected_rows()),
            **button_kwargs,
        )

    def export_button(self, callback=None, *, path: str | None = None, **button_kwargs):
        spec = self.action_spec("export")
        apply_action_intent(spec, button_kwargs)

        def _on_click(*_args, **_kwargs):
            csv_text = self.export_csv(path=path)
            if callback is not None:
                return callback(csv_text)
            return csv_text

        return self.action_button(spec.label, _on_click, **button_kwargs)

    def crud_bar(
        self,
        *,
        on_create: Callable | None = None,
        on_delete_selected: Callable | None = None,
        on_export: Callable | None = None,
        export_path: str | None = None,
    ) -> dict[str, object | None]:
        parts: dict[str, object | None] = {
            "create": None,
            "delete_selected": None,
            "export": None,
        }

        if on_create is not None:
            parts["create"] = self.create_button(on_create)

        if on_delete_selected is not None:
            parts["delete_selected"] = self.delete_selected_button(on_delete_selected)

        if on_export is not None or export_path is not None:
            parts["export"] = self.export_button(on_export, path=export_path)

        return parts

    def filter_rows(self, filter_values: dict[str, object]) -> list[dict]:
        if self.plugin is None or not hasattr(self.plugin, "filter_rows"):
            raise TypeError("filter_rows() is not supported for this table handle")

        return self.plugin.filter_rows(self.table_spec.source, filter_values)

    def set_filter(self, field_name: str, value, *, op: str | None = None):
        store = self._filter_store()
        store[field_name] = {"op": op, "value": value} if op else value
        self._refresh_filter_ui()
        return self

    def clear_filters(self):
        self._filter_store().clear()
        self._refresh_filter_ui()
        if self.plugin is not None and hasattr(self.plugin, "filter_rows"):
            return self.set_rows(self.filter_rows(self.normalized_filter_values()))
        return self

    def apply_filters(self, filter_values: dict[str, object] | None = None):
        if filter_values is not None:
            store = self._filter_store()
            store.clear()
            store.update(filter_values)
            self._refresh_filter_ui()
        return self.set_rows(self.filter_rows(self.normalized_filter_values()))
