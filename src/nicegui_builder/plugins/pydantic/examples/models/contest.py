from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ContestCategory(str, Enum):
    SPEED_MISMATCH = "Speed mismatch"
    DRAMATIC_PAIRING = "Dramatic pairing"
    FORMAL_CHAOS = "Formal chaos"
    CROWD_FAVORITE = "Crowd favorite"


class Contest(BaseModel):
    title: str = Field(
        title="Contest title",
        description="The official name of a very serious sock-based competition.",
        min_length=4,
        max_length=120,
    )
    category: ContestCategory = Field(
        default=ContestCategory.SPEED_MISMATCH,
        title="Category",
        description="The branch of nonsense this contest belongs to.",
    )
    starts_at: datetime = Field(
        title="Starts at",
        description="When the judges gather their courage and begin.",
    )
    duration_minutes: int = Field(
        default=30,
        title="Duration in minutes",
        description="Long enough for suspense, short enough for public dignity.",
        ge=5,
        le=240,
    )
    team_event: bool = Field(
        default=False,
        title="Team event",
        description="Enable this when one mismatched pair is simply not enough.",
    )
    master_of_ceremonies: str = Field(
        default="",
        title="Master of ceremonies",
        description="The person bravely reading the rules nobody obeys.",
        max_length=80,
    )
