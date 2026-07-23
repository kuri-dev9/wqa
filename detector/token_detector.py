"""JWT, access token, session ID and API key detectors."""

import re

from detector.base import RegexDetector


class JwtDetector(RegexDetector):
    detected_type = "JWT"
    pattern = re.compile(
        r"(?<![A-Za-z0-9_-])eyJ[A-Za-z0-9_-]{2,}\."
        r"[A-Za-z0-9_-]{2,}\.[A-Za-z0-9_-]{2,}(?![A-Za-z0-9_-])"
    )


class AccessTokenDetector(RegexDetector):
    detected_type = "ACCESS_TOKEN"
    pattern = re.compile(
        r"(?<![A-Za-z0-9_-])(?:Bearer\s+)?"
        r"(?:ya29\.[A-Za-z0-9_-]{20,}|gh[opsu]_[A-Za-z0-9]{20,}|"
        r"xox[baprs]-[A-Za-z0-9-]{20,})(?![A-Za-z0-9_-])",
        re.IGNORECASE,
    )


class ApiKeyDetector(RegexDetector):
    detected_type = "API_KEY"
    pattern = re.compile(
        r"(?<![A-Za-z0-9])(?:AIza[0-9A-Za-z_-]{35}|AKIA[0-9A-Z]{16}|"
        r"sk-[A-Za-z0-9_-]{20,})(?![A-Za-z0-9])"
    )


class SessionIdDetector(RegexDetector):
    detected_type = "SESSION_ID"
    pattern = re.compile(r"(?<![A-Fa-f0-9])[A-Fa-f0-9]{32,64}(?![A-Fa-f0-9])")
