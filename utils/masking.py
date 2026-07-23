"""Safe display masking. Raw values must never leave the analysis layer."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol


class DetectionLike(Protocol):
    detected_type: str
    value: str


def protect_value(value: str, detected_type: str) -> str:
    """Return an irreversible, readable representation for logs/reports."""
    if not value:
        return ""
    if detected_type == "EMAIL" and "@" in value:
        local, domain = value.split("@", 1)
        visible = local[:2] if len(local) > 1 else local[:1]
        return f"{visible}***@{domain}"
    if detected_type in {"PHONE", "MOBILE_PHONE"}:
        digits = "".join(char for char in value if char.isdigit())
        return f"{digits[:3]}-****-{digits[-4:]}" if len(digits) >= 7 else "***"
    if detected_type == "RESIDENT_NUMBER":
        digits = "".join(char for char in value if char.isdigit())
        return f"{digits[:6]}-*******"
    if detected_type == "BUSINESS_NUMBER":
        digits = "".join(char for char in value if char.isdigit())
        return f"{digits[:3]}-**-*****"
    if detected_type == "IP_ADDRESS":
        if "." in value:
            parts = value.split(".")
            return ".".join(parts[:2] + ["***", "***"])
        return value.split(":")[0] + ":***"
    if detected_type == "NAME_CANDIDATE":
        return value[0] + "*" * max(1, len(value) - 2) + (value[-1] if len(value) > 1 else "")
    if detected_type in {"USER_ID_CANDIDATE", "PASSWORD_CANDIDATE"}:
        return value[:2] + "*" * max(4, len(value) - 2)
    if detected_type in {"JWT", "ACCESS_TOKEN", "API_KEY", "SESSION_ID"}:
        return value[:4] + "…" + value[-4:] if len(value) > 8 else "********"
    return value[:2] + "*" * max(3, len(value) - 2)


def protect_text(value: str, detections: Iterable[DetectionLike]) -> str:
    """Replace detected fragments within larger strings such as URLs and headers."""
    protected = value
    for detection in sorted(detections, key=lambda item: len(item.value), reverse=True):
        protected = protected.replace(
            detection.value, protect_value(detection.value, detection.detected_type)
        )
    return protected
