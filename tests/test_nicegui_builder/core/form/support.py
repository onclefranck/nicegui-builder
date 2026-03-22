from datetime import datetime

from pydantic import BaseModel


class ValueComponent:
    def __init__(self, value):
        self.value = value
        self.error = None
        self.error_message = None
        self._value_change_callbacks = []
        self._event_callbacks = {}

    def set_value(self, value):
        self.value = value
        return value

    def set_error(self, message):
        self.error = message
        self.error_message = message
        return message

    def on_value_change(self, callback):
        self._value_change_callbacks.append(callback)
        return callback

    def on(self, event, callback):
        self._event_callbacks.setdefault(event, []).append(callback)
        return callback

    def emit_value_change(self):
        for callback in list(self._value_change_callbacks):
            callback()

    def emit(self, event):
        for callback in list(self._event_callbacks.get(event, [])):
            callback()


class TextComponent:
    def __init__(self, text):
        self.text = text


class FakeButton:
    def __init__(self, label, on_click=None, **kwargs):
        self.label = label
        self.on_click = on_click
        self.kwargs = kwargs
        self.enabled = True

    def set_enabled(self, enabled):
        self.enabled = enabled
        return enabled


class FakeBadge:
    def __init__(self, text, color=None, **kwargs):
        self.text = text
        self.color = color
        self.visible = True
        self.kwargs = kwargs

    def set_text(self, text):
        self.text = text
        return text

    def set_visibility(self, visible):
        self.visible = visible
        return visible


class FakeContext:
    def __init__(self, kind, bucket):
        self.kind = kind
        self.bucket = bucket
        self.visible = True

    def classes(self, classes):
        self.bucket.append(("classes", classes))
        return self

    def set_visibility(self, visible):
        self.visible = visible
        self.bucket.append(("visible", visible))
        return visible

    def __enter__(self):
        self.bucket.append(("enter", self.kind))
        return self

    def __exit__(self, exc_type, exc, tb):
        self.bucket.append(("exit", self.kind))
        return False


class FakeLabel:
    def __init__(self, text):
        self.text = text
        self.color = None
        self.visible = True

    def classes(self, classes):
        return self

    def set_text(self, text):
        self.text = text
        return text

    def set_visibility(self, visible):
        self.visible = visible
        return visible


class DemoModel(BaseModel):
    name: str
    age: int


class DemoDateTimeModel(BaseModel):
    starts_at: datetime


class DemoNestedModel(BaseModel):
    label: str
    count: int


class DemoStructuredModel(BaseModel):
    tags: list[str]
    metadata: dict[str, str]
    nested: DemoNestedModel
