from datetime import datetime

from nicegui_builder.plugins.pydantic import pydantic_plugin

from .support import DemoDateTimeModel


def test_pydantic_plugin_builds_split_datetime_field_node():
    instance = DemoDateTimeModel(starts_at=datetime(2026, 3, 21, 14, 30))

    resolved = pydantic_plugin.resolve_field_node(DemoDateTimeModel, instance, "starts_at", {})
    node = resolved.node

    assert node.methods == "datetime_input"
    assert node.ref == "field:starts_at"
    assert node.params["date_ref"] == "field:starts_at:date"
    assert node.params["time_ref"] == "field:starts_at:time"
    assert node.params["value"] == datetime(2026, 3, 21, 14, 30)
    assert node.params["container"]["methods"] == "row"


def test_pydantic_plugin_allows_structured_container_config_for_split_datetime_field_node():
    instance = DemoDateTimeModel(starts_at=datetime(2026, 3, 21, 14, 30))

    resolved = pydantic_plugin.resolve_field_node(
        DemoDateTimeModel,
        instance,
        "starts_at",
        {
            "params": {
                "container": {
                    "methods": "grid",
                    "params": {"columns": 2},
                    "classes": "gap-2",
                    "props": "bordered",
                }
            },
            "classes": "col-span-12 gap-2",
        },
    )
    node = resolved.node

    assert node.methods == "datetime_input"
    assert node.params["container"]["methods"] == "grid"
    assert node.params["container"]["params"] == {"columns": 2}
    assert node.params["container"]["classes"] == "gap-2"
    assert node.params["container"]["props"] == "bordered"
    assert "col-span-12" in node.classes
    assert node.params["date_ref"] == "field:starts_at:date"
    assert node.params["time_ref"] == "field:starts_at:time"
