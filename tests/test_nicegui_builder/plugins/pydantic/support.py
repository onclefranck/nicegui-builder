from datetime import datetime
import typing as t

from pydantic import BaseModel, Field
from nicegui_builder.core.models import LayoutNode


class DemoModel(BaseModel):
    name: str = Field(title="Name", min_length=2, max_length=80)
    age: int = Field(default=18, ge=0, le=120)
    active: bool = True
    role: t.Literal["admin", "user"] = "user"


class Address(BaseModel):
    street: str
    city: str


class DemoStructuredModel(BaseModel):
    name: str
    address: Address
    tags: list[str] = []


class DemoDateTimeModel(BaseModel):
    starts_at: datetime


def extract_section(layout, title: str):
    children = layout[0].children
    for child in children[1:]:
        if child.methods != "column":
            continue
        if child.children[0].methods == "label" and child.children[0].params["text"] == title:
            return child
    raise KeyError(title)


def extract_section_fields(section_column: LayoutNode):
    children = section_column.children
    grid = next(
        child
        for child in children
        if child.methods == "grid"
    )
    return {
        child.methods: child
        for child in grid.children
    }
