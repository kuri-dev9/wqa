"""Detection result model."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Finding:
    field_path: str
    detected_type: str
    value: str
