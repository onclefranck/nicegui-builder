from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class RegistrationStatus(str, Enum):
    DRAFT = "Draft"
    CONFIRMED = "Confirmed"
    WAITLIST = "Waitlist"
    DRAMATICALLY_LATE = "Dramatically late"


class Registration(BaseModel):
    participant_name: str = Field(
        title="Participant",
        description="The courageous soul attempting competitive sock asymmetry.",
        min_length=2,
        max_length=80,
    )
    contest_title: str = Field(
        title="Contest",
        description="The event this participant is bravely entering.",
        min_length=4,
        max_length=120,
    )
    status: RegistrationStatus = Field(
        default=RegistrationStatus.DRAFT,
        title="Status",
        description="Current administrative mood of the registration desk.",
    )
    checked_in_at: datetime | None = Field(
        default=None,
        title="Checked in at",
        description="When the participant officially appeared with their suspiciously creative socks.",
    )
    notes: str = Field(
        default="",
        title="Notes",
        description="Useful remarks, dramatic warnings, or soft sock-related gossip.",
        max_length=240,
    )
