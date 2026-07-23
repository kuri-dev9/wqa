"""Detection result model."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Finding:
    field_path: str
    detected_type: str
    value: str
    masked: bool
    displayed_value: str
    timestamp: str = ""
    method: str = ""
    api: str = ""
    status: int = 0
    elapsed_ms: float = 0.0
    response_size: int = 0
    screenshot_path: str = ""
