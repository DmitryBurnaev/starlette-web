from typing import Any


class Event:
    def __init__(self, group: str, message: Any) -> None:
        self.group = group
        self.message = message

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Event) and self.group == other.group and self.message == other.message
        )

    def __repr__(self) -> str:
        return f"Event(group={self.group!r}, message={self.message!r})"
