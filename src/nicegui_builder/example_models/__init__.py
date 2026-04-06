"""Backward-compatible alias for pydantic example models."""

from nicegui_builder.plugins.pydantic.examples.models import (
    Contest,
    ContestCategory,
    Participant,
    Registration,
    RegistrationStatus,
    SockColor,
)

__all__ = [
    "Contest",
    "ContestCategory",
    "Participant",
    "Registration",
    "RegistrationStatus",
    "SockColor",
]
