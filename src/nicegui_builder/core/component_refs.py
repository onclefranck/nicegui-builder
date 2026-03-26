from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class DateTimeComponentRef:
    container: object | None
    date: object | None
    time: object | None
