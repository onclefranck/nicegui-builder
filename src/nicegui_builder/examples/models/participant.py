from enum import Enum

from pydantic import BaseModel, Field


class SockColor(str, Enum):
    SUNSET_ORANGE = "Sunset orange"
    MOONLIGHT_BLUE = "Moonlight blue"
    MYSTERY_GREEN = "Mystery green"
    PANIC_PINK = "Panic pink"


class Participant(BaseModel):
    display_name: str = Field(
        title="Display name",
        description="The heroic name printed on the contestant badge.",
        min_length=2,
        max_length=80,
    )
    email: str = Field(
        title="Email",
        description="Where urgent sock-related announcements should be sent.",
    )
    sock_color: SockColor = Field(
        default=SockColor.SUNSET_ORANGE,
        title="Signature sock color",
        description="The dominant color of the contestant's least-matching pair.",
    )
    mismatch_level: int = Field(
        default=7,
        title="Mismatch level",
        description="A rigorously unscientific score from 1 to 10.",
        ge=1,
        le=10,
    )
    returning_legend: bool = Field(
        default=False,
        title="Returning legend",
        description="Enable this if the participant has survived a previous edition.",
    )
    emergency_note: str = Field(
        default="",
        title="Emergency note",
        description="Optional note in case the left sock attempts an artistic escape.",
        max_length=240,
    )
