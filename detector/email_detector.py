"""Email address detector."""

import re

from detector.base import RegexDetector


class EmailDetector(RegexDetector):
    detected_type = "EMAIL"
    pattern = re.compile(
        r"(?<![\w.+-])[A-Z0-9.!#$%&'*+/=?^_`{|}~-]+"
        r"@[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?"
        r"(?:\.[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?)+(?![\w.-])",
        re.IGNORECASE,
    )
