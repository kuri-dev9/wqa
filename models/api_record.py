"""Captured API response model."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class ApiRecord:
    timestamp: datetime
    method: str
    url: str
    status: int
    elapsed_ms: float
    response_headers: dict[str, str]
    response_body: Any | None
    response_size: int

    @classmethod
    def create(cls, **values: Any) -> "ApiRecord":
        return cls(timestamp=datetime.now().astimezone(), **values)
