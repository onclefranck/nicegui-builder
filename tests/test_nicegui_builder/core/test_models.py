from nicegui_builder import ActionSpec, FormSpec, TableSpec
from nicegui_builder.core.models import CollectionSpec, FieldSpec, LayoutNode, WidgetSpec


def test_field_spec_defaults_are_isolated():
    left = FieldSpec(name="name", python_type=str)
    right = FieldSpec(name="age", python_type=int)

    left.constraints["min_length"] = 2

    assert right.constraints == {}
    assert left.examples == []
    assert right.examples == []


def test_layout_node_can_reference_nested_children():
    child = LayoutNode(methods="label", params={"text": "Hello"})
    parent = LayoutNode(methods="column", children=[child])

    assert parent.children[0].methods == "label"
    assert parent.children[0].params["text"] == "Hello"


def test_form_and_table_specs_hold_expected_shapes():
    field = FieldSpec(name="name", python_type=str)
    collection = CollectionSpec(name="rows", columns=[field])
    widget = WidgetSpec(component="table")

    form_spec = FormSpec(source_class=dict, field_specs=[field], flavor="compact", plugin_name="demo")
    table_spec = TableSpec(
        source_class=list,
        collection_spec=collection,
        widget_spec=widget,
        variant="filters",
        plugin_name="pandas",
    )

    assert isinstance(ActionSpec(name="create", label="Create"), ActionSpec)
    assert form_spec.field_specs[0].name == "name"
    assert table_spec.collection_spec.columns[0].name == "name"
    assert table_spec.widget_spec.component == "table"
