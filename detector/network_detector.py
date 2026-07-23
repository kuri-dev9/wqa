"""Network-address detectors."""

from __future__ import annotations

import ipaddress
import re
from typing import Any

from detector.base import Detection, Detector


class IpAddressDetector(Detector):
    detected_type = "IP_ADDRESS"
    _candidate = re.compile(r"(?<![\w:])(?:[0-9A-Fa-f:.]+)(?![\w:])")

    def detect(self, value: Any) -> list[Detection]:
        if not isinstance(value, str):
            return []
        results: list[Detection] = []
        for match in self._candidate.finditer(value):
            candidate = match.group(0).strip(".:")
            if "." not in candidate and ":" not in candidate:
                continue
            try:
                ipaddress.ip_address(candidate)
            except ValueError:
                continue
            results.append(Detection(self.detected_type, candidate))
        return results
