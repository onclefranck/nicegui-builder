from datetime import datetime

from nicegui_builder.plugins.pydantic import pydantic_plugin

from .support import DemoDateTimeModel


def test_pydantic_plugin_builds_split_datetime_field_node():
    instance = DemoDateTimeModel(starts_at=datetime(2026, 3, 21, 14, 30))

    resolved = pydantic_plugin.resolve_field_node(DemoDateTimeModel, instance, "starts_at", {})
    node = resolved["node"]

    assert node["methods"] == "row"
    assert len(node["children"]) == 2
    assert node["children"][0]["date_input"]["ref"] == "field:starts_at:date"
    assert node["children"][1]["time_input"]["ref"] == "field:starts_at:time"
    assert node["children"][0]["date_input"]["params"]["value"] == "2026-03-21"
    assert node["children"][1]["time_input"]["params"]["value"] == "14:30"


def test_pydantic_plugin_allows_custom_container_for_split_datetime_field_node():
    instance = DemoDateTimeModel(starts_at=datetime(2026, 3, 21, 14, 30))

    resolved = pydantic_plugin.resolve_field_node(
        DemoDateTimeModel,
        instance,
        "starts_at",
        {
            "container": "grid",
            "params": {"columns": 2},
            "classes": "col-span-12 gap-2",
        },
    )
    node = resolved["node"]

    assert node["methods"] == "grid"
    assert node["params"] == {"columns": 2}
    assert "col-span-12" in node["classes"]
    assert node["children"][0]["date_input"]["ref"] == "field:starts_at:date"
    assert node["children"][1]["time_input"]["ref"] == "field:starts_at:time"
