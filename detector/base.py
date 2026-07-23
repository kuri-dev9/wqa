"""Detector contracts and regex implementation helper."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, ClassVar


@dataclass(frozen=True, slots=True)
class Detection:
    detected_type: str
    value: str
    masked: bool


class Detector(ABC):
    detected_type: ClassVar[str]

    @abstractmethod
    def detect(self, value: Any) -> list[Detection]:
        """Return every sensitive fragment found in a leaf value."""

    def is_masked(self, value: str) -> bool:
        """Return whether the matched source already contains masking."""
        return "*" in value


class RegexDetector(Detector):
    pattern: ClassVar[re.Pattern[str]]

    def detect(self, value: Any) -> list[Detection]:
        if not isinstance(value, str):
            return []
        return [
            Detection(self.detected_type, match.group(0), self.is_masked(match.group(0)))
            for match in self.pattern.finditer(value)
        ]
