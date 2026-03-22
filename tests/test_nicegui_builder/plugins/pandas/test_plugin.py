import builtins

from nicegui_builder.core.models import CollectionSpec, FieldSpec, TableSpec, WidgetSpec
from nicegui_builder.plugins.pandas import pandas_plugin
from nicegui_builder.plugins.pandas import plugin as pandas_module

from .support import pandas


def test_import_pandas_and_dtype_helpers_cover_basic_paths(monkeypatch):
    assert pandas_module._import_pandas() is not None
    assert pandas_module._is_numeric_dtype(pandas.Series([1, 2]).dtype) is True
    assert pandas_module._is_bool_dtype(pandas.Series([True, False]).dtype) is True
    assert pandas_module._is_datetime_dtype(pandas.to_datetime(["2026-03-21"]).dtype) is True
    assert pandas_module._python_type_from_dtype(pandas.Series([1, 2]).dtype) is int
    assert pandas_module._python_type_from_dtype(pandas.Series([1.5, 2.5]).dtype) is float
    assert pandas_module._python_type_from_dtype(pandas.Series([True, False]).dtype) is bool
    assert pandas_module._python_type_from_dtype(pandas.to_datetime(["2026-03-21"]).dtype) == "datetime"
    assert pandas_module._python_type_from_dtype(pandas.Series(["Ada"]).dtype) is str

    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "pandas":
            raise ImportError()
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    assert pandas_module._import_pandas() is None
    assert pandas_module._is_numeric_dtype("int64") is False
    assert pandas_module._is_bool_dtype("bool") is False
    assert pandas_module._is_datetime_dtype("datetime64[ns]") is False


def test_build_column_and_filter_specs_cover_more_types():
    bool_series = pandas.Series([True, False], name="active")
    float_series = pandas.Series([1.5, 2.5], name="ratio")
    text_series = pandas.Series([f"name-{i}" for i in range(13)], name="name")
    choice_column = FieldSpec(name="status", python_type=int, choices=[1, 2], title="Status")

    bool_column = pandas_module._build_column_spec("active", bool_series)
    float_column = pandas_module._build_column_spec("ratio", float_series)
    text_column = pandas_module._build_column_spec("name", text_series)
    numeric_filter = pandas_module._build_filter_spec(choice_column)
    select_column = FieldSpec(name="state", python_type=object, choices=["queued", "ready"], title="State")
    select_filter = pandas_module._build_filter_spec(select_column)

    assert bool_column.python_type is bool
    assert float_column.python_type is float
    assert float_column.constraints == {"min": 1.5, "max": 2.5}
    assert text_column.choices == []
    assert numeric_filter.source_meta["filter_kind"] == "number"
    assert select_filter.source_meta["filter_kind"] == "select"
    assert select_filter.source_meta["filter_operators"] == ["equals", "in"]


def test_normalize_and_apply_text_filters_cover_all_operators():
    df = pandas.DataFrame(
        [
            {"name": "Ada"},
            {"name": "Grace"},
            {"name": "Alan"},
        ]
    )
    text_column = FieldSpec(name="name", python_type=str, source_meta={"filter_kind": "text"})

    assert pandas_module._normalize_filter_clause("Ada", text_column) == {"op": "contains", "value": "Ada"}
    assert pandas_module._normalize_filter_clause({"value": "Ada"}, text_column) == {
        "op": "equals",
        "value": "Ada",
    }

    assert [row["name"] for row in pandas_module._apply_text_filter(df, "name", "contains", "a").to_dict("records")] == [
        "Ada",
        "Grace",
        "Alan",
    ]
    assert [row["name"] for row in pandas_module._apply_text_filter(df, "name", "equals", "ada").to_dict("records")] == [
        "Ada"
    ]
    assert [row["name"] for row in pandas_module._apply_text_filter(df, "name", "in", ["Ada", "Alan"]).to_dict("records")] == [
        "Ada",
        "Alan",
    ]

    try:
        pandas_module._apply_text_filter(df, "name", "mystery", "Ada")
    except ValueError as exc:
        assert "unsupported text filter operator" in str(exc)
    else:
        raise AssertionError("_apply_text_filter should reject unsupported operators")


def test_apply_scalar_filter_covers_all_operators_and_errors():
    df = pandas.DataFrame(
        [
            {"score": 10},
            {"score": 20},
            {"score": 30},
        ]
    )

    assert [row["score"] for row in pandas_module._apply_scalar_filter(df, "score", "equals", 20).to_dict("records")] == [20]
    assert [row["score"] for row in pandas_module._apply_scalar_filter(df, "score", "gt", 10).to_dict("records")] == [20, 30]
    assert [row["score"] for row in pandas_module._apply_scalar_filter(df, "score", "ge", 20).to_dict("records")] == [20, 30]
    assert [row["score"] for row in pandas_module._apply_scalar_filter(df, "score", "lt", 30).to_dict("records")] == [10, 20]
    assert [row["score"] for row in pandas_module._apply_scalar_filter(df, "score", "le", 20).to_dict("records")] == [10, 20]
    assert [row["score"] for row in pandas_module._apply_scalar_filter(df, "score", "between", [15, 30]).to_dict("records")] == [
        20,
        30,
    ]
    assert [row["score"] for row in pandas_module._apply_scalar_filter(df, "score", "in", [10, 30]).to_dict("records")] == [10, 30]

    try:
        pandas_module._apply_scalar_filter(df, "score", "between", [10])
    except ValueError as exc:
        assert "two-item" in str(exc)
    else:
        raise AssertionError("_apply_scalar_filter should validate between operands")

    try:
        pandas_module._apply_scalar_filter(df, "score", "mystery", 10)
    except ValueError as exc:
        assert "unsupported scalar filter operator" in str(exc)
    else:
        raise AssertionError("_apply_scalar_filter should reject unsupported operators")


def test_rows_from_dataframe_adds_internal_row_ids():
    df = pandas.DataFrame([{"name": "Ada"}, {"name": "Grace"}])

    rows = pandas_module._rows_from_dataframe(df)

    assert rows[0]["nicegui_builder_row_id"] == 0
    assert rows[1]["nicegui_builder_row_id"] == 1


def test_pandas_plugin_supports_dataframe():
    df = pandas.DataFrame([{"name": "Ada", "score": 10, "active": True}])

    assert pandas_plugin.supports(df) is True
    assert pandas_plugin.supports([{"name": "Ada"}]) is False


def test_pandas_plugin_supports_returns_false_when_pandas_is_unavailable(monkeypatch):
    monkeypatch.setattr(pandas_module, "_import_pandas", lambda: None)

    assert pandas_plugin.supports(object()) is False


def test_pandas_plugin_inspects_collection_and_filters():
    df = pandas.DataFrame(
        [
            {"name": "Ada", "score": 10, "active": True},
            {"name": "Grace", "score": 20, "active": False},
        ]
    )

    spec = pandas_plugin.inspect_collection(df)
    by_name = {field.name: field for field in spec.columns}
    filters = {field.name: field for field in spec.filters}

    assert by_name["score"].python_type is int
    assert by_name["score"].constraints["min"] == 10
    assert filters["name"].source_meta["filter_kind"] in {"text", "select"}
    assert "contains" in filters["name"].source_meta["filter_operators"]
    assert filters["active"].source_meta["filter_kind"] == "boolean"
    assert "equals" in filters["active"].source_meta["filter_operators"]


def test_pandas_plugin_resolve_collection_widget_and_prepare_rows():
    spec = CollectionSpec(
        name="ContestTable",
        columns=[
            FieldSpec(name="name", python_type=str, title="Name"),
            FieldSpec(name="score", python_type=int, title="Score"),
        ],
    )
    widget = pandas_plugin.resolve_collection_widget(spec, variant="filters")
    rows = pandas_plugin.prepare_rows(pandas.DataFrame([{"name": "Ada", "score": 10}]))

    assert widget.component == "table"
    assert widget.variant == "filters"
    assert widget.params["row_key"] == "nicegui_builder_row_id"
    assert widget.params["columns"][1]["align"] == "left"
    assert widget.params["columns"][2]["align"] == "right"
    assert rows[0]["nicegui_builder_row_id"] == 0


def test_pandas_plugin_filters_rows():
    df = pandas.DataFrame(
        [
            {"name": "Ada", "score": 10},
            {"name": "Grace", "score": 20},
        ]
    )

    rows = pandas_plugin.filter_rows(df, {"name": "ada"})

    assert len(rows) == 1
    assert rows[0]["name"] == "Ada"


def test_pandas_plugin_supports_richer_filter_operators():
    df = pandas.DataFrame(
        [
            {"name": "Ada", "score": 10, "active": True},
            {"name": "Grace", "score": 20, "active": False},
            {"name": "Alan", "score": 30, "active": True},
        ]
    )

    contains_rows = pandas_plugin.filter_rows(df, {"name": {"op": "contains", "value": "a"}})
    between_rows = pandas_plugin.filter_rows(df, {"score": {"op": "between", "value": [15, 30]}})
    in_rows = pandas_plugin.filter_rows(df, {"name": {"op": "in", "value": ["Ada", "Alan"]}})
    bool_rows = pandas_plugin.filter_rows(df, {"active": {"op": "equals", "value": True}})
    skipped_rows = pandas_plugin.filter_rows(df, {"name": {"op": "contains", "value": ""}})

    assert [row["name"] for row in contains_rows] == ["Ada", "Grace", "Alan"]
    assert [row["name"] for row in between_rows] == ["Grace", "Alan"]
    assert [row["name"] for row in in_rows] == ["Ada", "Alan"]
    assert [row["name"] for row in bool_rows] == ["Ada", "Alan"]
    assert len(skipped_rows) == 3


def test_pandas_plugin_render_collection_returns_none_for_non_filter_variant():
    df = pandas.DataFrame([{"name": "Ada", "score": 10}])
    spec = pandas_plugin.inspect_collection(df)

    assert pandas_plugin.render_collection(df, spec, variant="std") is None


def test_pandas_plugin_render_collection_builds_filter_ui_and_binds_state(monkeypatch):
    df = pandas.DataFrame(
        [
            {"name": "Ada", "score": 10, "active": True},
            {"name": "Grace", "score": 20, "active": False},
        ]
    )
    spec = pandas_plugin.inspect_collection(df)
    widget_spec = pandas_plugin.resolve_collection_widget(spec, variant="filters")
    table_spec = TableSpec(
        source_class=df.__class__,
        collection_spec=spec,
        source=df,
        widget_spec=widget_spec,
        variant="filters",
        plugin_name="pandas",
    )

    bucket = []
    controls = []

    class FakeContext:
        def __init__(self, kind):
            self.kind = kind

        def classes(self, classes):
            bucket.append(("classes", self.kind, classes))
            return self

        def __enter__(self):
            bucket.append(("enter", self.kind))
            return self

        def __exit__(self, exc_type, exc, tb):
            bucket.append(("exit", self.kind))
            return False

    class FakeControl:
        def __init__(self, kind, **kwargs):
            self.kind = kind
            self.kwargs = kwargs
            self.callbacks = []
            self.props_value = None
            controls.append(self)

        def props(self, value):
            self.props_value = value
            return self

        def on_value_change(self, callback):
            self.callbacks.append(callback)
            return callback

    class FakeTable:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            self.rows = kwargs["rows"]
            self.updated = False
            self.classes_value = None
            self.props_value = None

        def classes(self, value):
            self.classes_value = value
            return self

        def props(self, value):
            self.props_value = value
            return self

        def update(self):
            self.updated = True

    monkeypatch.setattr(pandas_module.ui, "card", lambda: FakeContext("card"))
    monkeypatch.setattr(pandas_module.ui, "row", lambda: FakeContext("row"))
    monkeypatch.setattr(pandas_module.ui, "element", lambda tag: FakeContext(f"element:{tag}"))
    monkeypatch.setattr(pandas_module.ui, "input", lambda **kwargs: FakeControl("input", **kwargs))
    monkeypatch.setattr(pandas_module.ui, "number", lambda **kwargs: FakeControl("number", **kwargs))
    monkeypatch.setattr(pandas_module.ui, "select", lambda **kwargs: FakeControl("select", **kwargs))
    monkeypatch.setattr(pandas_module.ui, "table", lambda **kwargs: FakeTable(**kwargs))

    rendered = pandas_plugin.render_collection(df, spec, variant="filters", table_spec=table_spec)

    assert rendered is not None
    assert rendered.table_spec is table_spec
    assert rendered.filter_values == {}
    assert rendered.classes_value == "w-full"
    assert rendered.props_value == "flat bordered wrap-cells"
    assert rendered.kwargs["row_key"] == "nicegui_builder_row_id"
    assert len(controls) == len(spec.filters)

    text_control = next(control for control in controls if control.kind == "input")
    text_control.callbacks[0](type("Event", (), {"value": "ada"})())

    assert rendered.updated is True
    assert rendered.filter_values["name"] == "ada"
    assert [row["name"] for row in rendered.rows] == ["Ada"]


def test_pandas_plugin_render_collection_uses_select_controls_and_tolerates_attachment_failures(monkeypatch):
    df = pandas.DataFrame(
        [
            {"state": "queued", "active": True},
            {"state": "ready", "active": False},
        ]
    )
    spec = CollectionSpec(
        name="DemoTable",
        columns=[
            FieldSpec(name="state", python_type=object, title="State", choices=["queued", "ready"]),
            FieldSpec(name="active", python_type=bool, title="Active"),
        ],
        filters=[
            FieldSpec(
                name="state",
                python_type=object,
                title="State",
                choices=["queued", "ready"],
                source_meta={"filter_kind": "select"},
            ),
            FieldSpec(
                name="active",
                python_type=bool,
                title="Active",
                source_meta={"filter_kind": "boolean"},
            ),
        ],
    )
    widget_spec = WidgetSpec(
        component="table",
        variant="filters",
        params={
            "columns": [],
            "rows": [],
            "row_key": "id",
            "selection": "multiple",
            "pagination": {"rowsPerPage": 10},
        },
        props="flat",
        classes="w-full",
    )
    table_spec = TableSpec(
        source_class=df.__class__,
        collection_spec=spec,
        source=df,
        widget_spec=widget_spec,
        variant="filters",
        plugin_name="pandas",
    )

    controls = []

    class FakeContext:
        def __init__(self, kind):
            self.kind = kind

        def classes(self, classes):
            return self

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class FakeControl:
        def __init__(self, kind, **kwargs):
            self.kind = kind
            self.kwargs = kwargs
            self.callbacks = []
            controls.append(self)

        def props(self, value):
            return self

        def on_value_change(self, callback):
            self.callbacks.append(callback)
            return callback

    class FragileTable:
        def __init__(self, **kwargs):
            object.__setattr__(self, "kwargs", kwargs)
            object.__setattr__(self, "rows", kwargs["rows"])
            object.__setattr__(self, "updated", False)

        def __setattr__(self, name, value):
            if name in {"table_spec", "filter_values"}:
                raise RuntimeError("read-only attachment")
            object.__setattr__(self, name, value)

        def classes(self, value):
            return self

        def props(self, value):
            return self

        def update(self):
            self.updated = True

    monkeypatch.setattr(pandas_module.ui, "card", lambda: FakeContext("card"))
    monkeypatch.setattr(pandas_module.ui, "row", lambda: FakeContext("row"))
    monkeypatch.setattr(pandas_module.ui, "element", lambda tag: FakeContext(f"element:{tag}"))
    monkeypatch.setattr(pandas_module.ui, "input", lambda **kwargs: FakeControl("input", **kwargs))
    monkeypatch.setattr(pandas_module.ui, "number", lambda **kwargs: FakeControl("number", **kwargs))
    monkeypatch.setattr(pandas_module.ui, "select", lambda **kwargs: FakeControl("select", **kwargs))
    monkeypatch.setattr(pandas_module.ui, "table", lambda **kwargs: FragileTable(**kwargs))

    rendered = pandas_plugin.render_collection(df, spec, variant="filters", table_spec=table_spec)

    assert rendered is not None
    assert [control.kind for control in controls] == ["select", "select"]
    assert controls[0].kwargs == {"options": ["queued", "ready"], "label": "State", "clearable": True}
    assert controls[1].kwargs == {"options": [True, False], "label": "Active", "clearable": True}
