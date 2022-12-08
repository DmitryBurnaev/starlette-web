from dataclasses import dataclass


@dataclass
class WSRequest:
    headers: dict[str, str]
    data: dict | None = None
