from datetime import datetime
import typing as t

from pydantic import BaseModel, Field


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
    children = layout[0]["card.tight"]["children"]
    for child in children[1:]:
        if next(iter(child.keys())) != "column":
            continue
        column = child["column"]
        if column["children"][0]["label"]["params"]["text"] == title:
            return column
    raise KeyError(title)


def extract_section_fields(section_column):
    children = section_column["children"]
    grid = next(
        child["grid"]
        for child in children
        if next(iter(child.keys())) == "grid"
    )
    return {
        next(iter(child.keys())): next(iter(child.values()))
        for child in grid["children"]
    }
