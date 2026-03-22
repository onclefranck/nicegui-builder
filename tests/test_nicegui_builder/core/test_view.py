import types

from nicegui_builder import FormState, LiveBadgeBinding, LiveBinding, LiveButtonBinding, LivePanelBinding, ViewHandle

from .form.support import FakeContext


def test_live_binding_types_are_publicly_exported():
    assert isinstance(ViewHandle(), ViewHandle)
    assert issubclass(LiveButtonBinding, LiveBinding)
    assert issubclass(LiveBadgeBinding, LiveBinding)
    assert issubclass(LivePanelBinding, LiveBinding)
    assert isinstance(FormState(source_class=dict, field_specs=[]), FormState)


def test_view_handle_can_proxy_visibility_and_refresh():
    component = FakeContext("root", [])
    calls = {"updated": 0}

    def update():
        calls["updated"] += 1

    component.update = update
    handle = ViewHandle(root_component=component)

    handle.hide().show().refresh()

    assert component.visible is True
    assert calls["updated"] == 1


def test_view_handle_spec_property_requires_subclass_override():
    handle = ViewHandle()

    try:
        _ = handle.spec
    except NotImplementedError as exc:
        assert "spec property" in str(exc)
    else:
        raise AssertionError("expected NotImplementedError")


def test_view_handle_plugin_name_can_fall_back_to_spec_and_describe_without_root():
    class DemoHandle(ViewHandle):
        @property
        def spec(self):
            return type("DemoSpec", (), {"plugin_name": "from-spec"})()

    handle = DemoHandle()

    assert handle.plugin_name == "from-spec"
    assert handle.spec_type == "DemoSpec"
    assert handle.describe() == {
        "handle_type": "DemoHandle",
        "plugin_name": "from-spec",
        "spec_type": "DemoSpec",
        "root_component_type": None,
    }


def test_view_handle_show_hide_can_use_visible_attribute_when_set_visibility_is_absent():
    component = type("VisibleOnly", (), {"visible": False})()
    handle = ViewHandle(root_component=component)

    handle.show()
    assert component.visible is True

    handle.hide()
    assert component.visible is False


def test_view_handle_missing_root_component_raises_attribute_error():
    handle = ViewHandle()

    try:
        _ = handle.anything
    except AttributeError as exc:
        assert str(exc) == "anything"
    else:
        raise AssertionError("expected AttributeError")


def test_view_handle_plugin_name_prefers_plugin_and_can_fall_back_to_empty_string():
    class SpecWithoutPluginName:
        pass

    class DemoHandle(ViewHandle):
        @property
        def spec(self):
            return SpecWithoutPluginName()

    plugin_handle = DemoHandle(plugin=type("Plugin", (), {"name": "from-plugin"})())
    empty_handle = DemoHandle()

    assert plugin_handle.plugin_name == "from-plugin"
    assert plugin_handle.spec_type == "SpecWithoutPluginName"
    assert empty_handle.plugin_name == ""


def test_view_handle_can_proxy_attributes_to_root_component():
    component = types.SimpleNamespace(title="Mismatch Parade")
    handle = ViewHandle(root_component=component)

    assert handle.title == "Mismatch Parade"
