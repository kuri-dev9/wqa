"""Detector collection used by the analysis service."""

from __future__ import annotations

from typing import Any, Iterable

from detector.base import Detection, Detector
from detector.credential_detector import PasswordDetector, UserIdDetector
from detector.email_detector import EmailDetector
from detector.identity_detector import BusinessNumberDetector, ResidentNumberDetector
from detector.network_detector import IpAddressDetector
from detector.name_detector import NameDetector
from detector.phone_detector import MobilePhoneDetector, PhoneDetector
from detector.token_detector import (
    AccessTokenDetector,
    ApiKeyDetector,
    JwtDetector,
    SessionIdDetector,
)


class DetectorRegistry:
    def __init__(self, detectors: Iterable[Detector]) -> None:
        self.detectors = tuple(detectors)

    @classmethod
    def default(cls) -> "DetectorRegistry":
        return cls(
            (
                EmailDetector(),
                MobilePhoneDetector(),
                PhoneDetector(),
                ResidentNumberDetector(),
                BusinessNumberDetector(),
                NameDetector(),
                IpAddressDetector(),
                JwtDetector(),
                AccessTokenDetector(),
                ApiKeyDetector(),
                SessionIdDetector(),
                PasswordDetector(),
                UserIdDetector(),
            )
        )

    def detect(self, value: Any) -> list[Detection]:
        return [
            detection
            for detector in self.detectors
            for detection in detector.detect(value)
        ]
