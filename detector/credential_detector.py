"""Heuristic password and user-ID value detectors.

Because field names are intentionally ignored, these conservative heuristics can
produce false positives. Rule configuration and allowlists belong to STEP 10.
"""

import re
from typing import Any

from detector.base import Detection, Detector


class PasswordDetector(Detector):
    detected_type = "PASSWORD_CANDIDATE"
    _candidate = re.compile(r"(?<!\S)\S{8,64}(?!\S)")

    def detect(self, value: Any) -> list[Detection]:
        if not isinstance(value, str):
            return []
        results = []
        for match in self._candidate.finditer(value):
            candidate = match.group(0)
            classes = sum(
                bool(re.search(pattern, candidate))
                for pattern in (r"[a-z]", r"[A-Z]", r"\d", r"[^A-Za-z0-9]")
            )
            if (
                classes >= 3
                and "@" not in candidate
                and "." not in candidate
                and not candidate.lower().startswith(("error-", "http"))
            ):
                results.append(Detection(self.detected_type, candidate, self.is_masked(candidate)))
        return results


class UserIdDetector(Detector):
    detected_type = "USER_ID_CANDIDATE"
    _pattern = re.compile(r"(?<![A-Za-z0-9_])[A-Za-z][A-Za-z0-9_]{5,19}(?![A-Za-z0-9_])")

    def detect(self, value: Any) -> list[Detection]:
        if not isinstance(value, str):
            return []
        return [
            Detection(self.detected_type, item, self.is_masked(item))
            for item in self._pattern.findall(value)
            if any(char.isdigit() for char in item)
        ]
