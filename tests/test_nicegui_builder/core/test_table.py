from pathlib import Path

import importlib
import pytest

from nicegui_builder import TableHandle, TableSpec, ViewHandle
from nicegui_builder.core.models import CollectionSpec, FieldSpec, WidgetSpec
from nicegui_builder.plugins.pandas import pandas_plugin

pandas = pytest.importorskip("pandas")
table_module = importlib.import_module("nicegui_builder.table")


def _make_table_handle(*, source=None, widget_spec=None, component=None, plugin=None, filter_values=None):
    collection_spec = CollectionSpec(
        name="rows",
        columns=[
            FieldSpec(name="name", python_type=str),
            FieldSpec(name="score", python_type=int),
        ],
    )
    table_spec = TableSpec(
        source_class=dict if source is None else source.__class__,
        collection_spec=collection_spec,
        source=[] if source is None else source,
        widget_spec=widget_spec,
        plugin_name="demo",
    )
    return TableHandle(
        table_spec=table_spec,
        root_component=component,
        plugin=plugin,
        filter_values={} if filter_values is None else filter_values,
    )


def test_table_spec_is_public_and_can_wrap_pandas_collection_spec():
    df = pandas.DataFrame([{"name": "Ada", "score": 10}])
    collection_spec = pandas_plugin.inspect_collection(df)
    widget_spec = pandas_plugin.resolve_collection_widget(collection_spec)
    table_spec = TableSpec(
        source_class=df.__class__,
        collection_spec=collection_spec,
        source=df,
        widget_spec=widget_spec,
        variant="std",
        plugin_name=pandas_plugin.name,
    )

    assert table_spec.plugin_name == "pandas"
    assert table_spec.collection_spec.columns[0].name == "name"
    assert table_spec.widget_spec.component == "table"
    assert table_spec.widget_spec.params["selection"] == "multiple"
    assert table_spec.widget_spec.params["pagination"]["rowsPerPage"] == 10


def test_table_attaches_table_spec_to_rendered_component(monkeypatch):
    df = pandas.DataFrame([{"name": "Ada", "score": 10}])

    class FakeTableComponent:
        def __init__(self):
            self.rows = []
            self.updated = False
            self.pagination = {}
            self.selected = []

        def update(self):
            self.updated = True

    fake_component = FakeTableComponent()

    monkeypatch.setattr(table_module, "builder", lambda layout: fake_component)

    rendered = table_module.table(df)

    assert isinstance(rendered, TableHandle)
    assert isinstance(rendered, ViewHandle)
    assert rendered.component is fake_component
    assert isinstance(rendered.table_spec, TableSpec)
    assert rendered.table_spec.plugin_name == "pandas"
    assert rendered.table_spec.collection_spec.columns[0].name == "name"
    assert rendered.component.table_handle is rendered
    assert rendered.component.table_spec is rendered.table_spec


def test_table_handle_can_proxy_component_and_apply_filters(monkeypatch):
    df = pandas.DataFrame(
        [
            {"name": "Ada", "score": 10},
            {"name": "Grace", "score": 20},
        ]
    )

    class FakeTableComponent:
        def __init__(self):
            self.rows = []
            self.updated = False
            self.marker = "ok"
            self.pagination = {}
            self.selected = []

        def update(self):
            self.updated = True

    fake_component = FakeTableComponent()
    monkeypatch.setattr(table_module, "builder", lambda layout: fake_component)

    handle = table_module.table(df)

    assert handle.marker == "ok"
    assert handle.get_rows() == []

    handle.apply_filters({"name": "ada"})

    assert handle.get_rows() == [{"name": "Ada", "score": 10}]
    assert fake_component.updated is True
    assert handle.describe()["handle_type"] == "TableHandle"
    assert handle.describe()["spec_type"] == "TableSpec"


def test_table_handle_can_store_and_clear_filter_state(monkeypatch):
    df = pandas.DataFrame(
        [
            {"name": "Ada", "score": 10},
            {"name": "Grace", "score": 20},
            {"name": "Alan", "score": 30},
        ]
    )

    class FakeTableComponent:
        def __init__(self):
            self.rows = []
            self.updated = False
            self.pagination = {}
            self.selected = []

        def update(self):
            self.updated = True

    fake_component = FakeTableComponent()
    monkeypatch.setattr(table_module, "builder", lambda layout: fake_component)

    handle = table_module.table(df)
    handle.set_filter("name", "a", op="contains").set_filter("score", [10, 20], op="between")
    handle.apply_filters()

    assert handle.filter_values["name"]["op"] == "contains"
    assert [row["name"] for row in handle.get_rows()] == ["Ada", "Grace"]

    handle.clear_filters().apply_filters()

    assert handle.filter_values == {}
    assert len(handle.get_rows()) == 3


def test_table_handle_can_share_filter_state_with_rendered_component(monkeypatch):
    df = pandas.DataFrame(
        [
            {"name": "Ada", "score": 10},
            {"name": "Grace", "score": 20},
        ]
    )

    class FakeTableComponent:
        def __init__(self):
            self.rows = []
            self.updated = False
            self.pagination = {}
            self.selected = []
            self.filter_values = {"name": {"op": "contains", "value": "ad"}}

        def update(self):
            self.updated = True

    fake_component = FakeTableComponent()
    monkeypatch.setattr(table_module, "builder", lambda layout: fake_component)

    handle = table_module.table(df)

    assert handle.filter_values is fake_component.filter_values
    assert handle.normalized_filter_values() == {"name": {"op": "contains", "value": "ad"}}


def test_table_handle_supports_sort_pagination_selection_and_csv_export(monkeypatch):
    df = pandas.DataFrame(
        [
            {"name": "Grace", "score": 20},
            {"name": "Ada", "score": 10},
        ]
    )

    class FakeTableComponent:
        def __init__(self):
            self.rows = []
            self.updated = False
            self.pagination = {"rowsPerPage": 10, "sortBy": "name", "descending": False}
            self.selected = []

        def update(self):
            self.updated = True

    fake_component = FakeTableComponent()
    monkeypatch.setattr(table_module, "builder", lambda layout: fake_component)

    handle = table_module.table(df)
    handle.set_rows(df.to_dict(orient="records"))
    handle.sort_rows("name")

    assert [row["name"] for row in handle.get_rows()] == ["Ada", "Grace"]

    handle.set_pagination(rows_per_page=25, sort_by="score", descending=True)
    assert handle.get_pagination()["rowsPerPage"] == 25
    assert handle.get_pagination()["sortBy"] == "score"
    assert handle.get_pagination()["descending"] is True

    handle.set_selected_rows([handle.get_rows()[0]])
    assert handle.get_selected_rows()[0]["name"] == "Ada"

    export_path = Path("tests") / "_table_export.csv"
    try:
        csv_text = handle.export_csv(str(export_path))
        assert "name,score" in csv_text
        assert "Ada,10" in csv_text
        assert export_path.read_text(encoding="utf-8").startswith("name,score")
    finally:
        if export_path.exists():
            export_path.unlink()


def test_table_handle_crud_bar_builds_standard_actions(monkeypatch):
    df = pandas.DataFrame(
        [
            {"name": "Ada", "score": 10},
            {"name": "Grace", "score": 20},
        ]
    )

    class FakeTableComponent:
        def __init__(self):
            self.rows = df.to_dict(orient="records")
            self.updated = False
            self.pagination = {}
            self.selected = [{"name": "Ada", "score": 10}]

        def update(self):
            self.updated = True

    fake_component = FakeTableComponent()
    monkeypatch.setattr(table_module, "builder", lambda layout: fake_component)
    monkeypatch.setattr(
        "nicegui_builder.core.table.ui.button",
        lambda label, on_click=None, **kwargs: type(
            "FakeActionButton",
            (),
            {"label": label, "on_click": on_click, "kwargs": kwargs},
        )(),
    )

    handle = table_module.table(df)
    created = []
    deleted = []
    exported = []

    parts = handle.crud_bar(
        on_create=lambda table_handle: created.append(table_handle),
        on_delete_selected=lambda rows: deleted.append(rows),
        on_export=lambda csv_text: exported.append(csv_text),
    )

    parts["create"].on_click()
    parts["delete_selected"].on_click()
    parts["export"].on_click()

    assert created == [handle]
    assert deleted == [[{"name": "Ada", "score": 10}]]
    assert exported and "name,score" in exported[0]


def test_table_handle_internal_row_ids_prevent_duplicate_selection(monkeypatch):
    df = pandas.DataFrame(
        [
            {"title": "Repeated Finale", "duration": 30},
            {"title": "Repeated Finale", "duration": 30},
            {"title": "Different Entry", "duration": 10},
        ]
    )

    class FakeTableComponent:
        def __init__(self):
            self.rows = []
            self.updated = False
            self.pagination = {"sortBy": "title", "descending": False}
            self.selected = []

        def update(self):
            self.updated = True

    fake_component = FakeTableComponent()
    monkeypatch.setattr(table_module, "builder", lambda layout: fake_component)

    handle = table_module.table(df)
    handle.set_rows(df.to_dict(orient="records"))
    rows = handle.get_rows()

    assert "nicegui_builder_row_id" not in rows[0]

    handle.set_selected_rows(rows[:1])

    assert len(fake_component.selected) == 1
    assert handle.get_selected_rows() == [rows[0]]


def test_table_handle_internal_row_ids_can_select_distinct_duplicate_rows(monkeypatch):
    df = pandas.DataFrame(
        [
            {"title": "Repeated Finale", "duration": 30},
            {"title": "Repeated Finale", "duration": 30},
        ]
    )

    class FakeTableComponent:
        def __init__(self):
            self.rows = []
            self.updated = False
            self.pagination = {"sortBy": "title", "descending": False}
            self.selected = []

        def update(self):
            self.updated = True

    fake_component = FakeTableComponent()
    monkeypatch.setattr(table_module, "builder", lambda layout: fake_component)

    handle = table_module.table(df)
    handle.set_rows(df.to_dict(orient="records"))
    rows = handle.get_rows()

    handle.set_selected_rows(rows)

    assert len(fake_component.selected) == 2
    assert handle.get_selected_rows() == rows


def test_table_handle_normalized_filter_values_skips_empty_entries():
    handle = _make_table_handle(
        filter_values={
            "blank": "",
            "none": None,
            "empty_list": [],
            "name": "Ada",
            "score": {"op": "between", "value": [10, 20]},
            "ignored_dict": {"op": "contains", "value": ""},
            "defaulted_dict": {"value": "Grace"},
        }
    )

    assert handle.normalized_filter_values() == {
        "name": "Ada",
        "score": {"op": "between", "value": [10, 20]},
        "defaulted_dict": {"op": "equals", "value": "Grace"},
    }


def test_table_handle_handles_missing_widget_spec_and_plain_rows():
    handle = _make_table_handle(source=[{"name": "Ada", "score": 10}], widget_spec=None)

    assert handle._row_key_name() is None
    assert handle.get_rows() == []
    assert handle.get_pagination() == {}
    assert handle.get_selected_rows() == []
    assert handle._strip_internal_row_id({"name": "Ada", "nicegui_builder_row_id": 1}) == {
        "name": "Ada",
        "nicegui_builder_row_id": 1,
    }
    assert handle._ensure_internal_row_ids([{"name": "Ada"}]) == [{"name": "Ada"}]


def test_table_handle_can_read_rows_from_dataframe_source_without_component():
    df = pandas.DataFrame([{"name": "Ada", "score": 10}])
    widget_spec = WidgetSpec(component="table", params={"pagination": {"rowsPerPage": 5}})
    handle = _make_table_handle(source=df, widget_spec=widget_spec)

    assert handle.get_rows() == [{"name": "Ada", "score": 10}]
    assert handle.get_pagination() == {"rowsPerPage": 5}


def test_table_handle_get_pagination_returns_empty_when_component_pagination_is_none():
    component = type("Component", (), {"pagination": None})()
    handle = _make_table_handle(component=component, widget_spec=WidgetSpec(component="table"))

    assert handle.get_pagination() == {}


def test_table_handle_set_pagination_updates_widget_spec_without_component():
    widget_spec = WidgetSpec(component="table", params={})
    handle = _make_table_handle(widget_spec=widget_spec)

    result = handle.set_pagination(rows_per_page=50, sort_by="score", descending=True)

    assert result is handle
    assert widget_spec.params["pagination"] == {
        "rowsPerPage": 50,
        "sortBy": "score",
        "descending": True,
    }


def test_table_handle_set_selected_rows_without_internal_ids_uses_plain_rows():
    class FakeComponent:
        def __init__(self):
            self.selected = []
            self.updated = False

        def update(self):
            self.updated = True

    component = FakeComponent()
    widget_spec = WidgetSpec(component="table", params={"row_key": "id"})
    handle = _make_table_handle(component=component, widget_spec=widget_spec)

    result = handle.set_selected_rows([{"name": "Ada", "score": 10}])

    assert result is handle
    assert component.selected == [{"name": "Ada", "score": 10}]
    assert component.updated is True


def test_table_handle_export_button_returns_csv_when_no_callback(monkeypatch):
    handle = _make_table_handle()
    monkeypatch.setattr(TableHandle, "export_csv", lambda self, path=None: "name,score\r\nAda,10\r\n")
    monkeypatch.setattr(
        "nicegui_builder.core.table.ui.button",
        lambda label, on_click=None, **kwargs: type("FakeButton", (), {"label": label, "on_click": on_click, "kwargs": kwargs})(),
    )

    button = handle.export_button(path="ignored.csv")

    assert button.label == "Export CSV"
    assert button.on_click() == "name,score\r\nAda,10\r\n"


def test_table_handle_crud_bar_keeps_missing_actions_as_none():
    handle = _make_table_handle()

    parts = handle.crud_bar()

    assert parts == {"create": None, "delete_selected": None, "export": None}


def test_table_handle_filter_rows_requires_plugin_support():
    handle = _make_table_handle(plugin=None)

    with pytest.raises(TypeError, match="not supported"):
        handle.filter_rows({"name": "Ada"})
