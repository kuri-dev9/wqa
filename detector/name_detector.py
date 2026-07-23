"""Conservative Korean name candidate detector."""

import re
from typing import Any

from detector.base import Detection, Detector


class NameDetector(Detector):
    detected_type = "NAME_CANDIDATE"
    _pattern = re.compile(r"^[가-힣](?:[가-힣*]{0,2})[가-힣]$|^[가-힣]{2}$")

    def detect(self, value: Any) -> list[Detection]:
        if not isinstance(value, str):
            return []
        candidate = value.strip()
        if not self._pattern.fullmatch(candidate) or not 2 <= len(candidate) <= 4:
            return []
        return [Detection(self.detected_type, candidate, self.is_masked(candidate))]
