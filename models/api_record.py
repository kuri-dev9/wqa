"""Captured API response model."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class ApiRecord:
    timestamp: datetime
    method: str
    url: str
    status: int
    elapsed_ms: float
    response_headers: dict[str, str]
    response_body: Any | None
    response_size: int
    request_headers: dict[str, str] | None = None
    body_skipped: bool = False
    detected_count: int = 0
    screenshot_path: str = ""

    @classmethod
    def create(cls, **values: Any) -> "ApiRecord":
        return cls(timestamp=datetime.now().astimezone(), **values)
