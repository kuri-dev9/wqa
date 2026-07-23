"""Korean mobile and landline phone detectors."""

import re

from detector.base import RegexDetector


class MobilePhoneDetector(RegexDetector):
    detected_type = "MOBILE_PHONE"
    pattern = re.compile(r"(?<!\d)01[016789][ -]?\d{3,4}[ -]?\d{4}(?!\d)")


class PhoneDetector(RegexDetector):
    detected_type = "PHONE"
    pattern = re.compile(
        r"(?<!\d)(?:0(?:2|3[1-3]|4[1-4]|5[1-5]|6[1-4]))[ -]?"
        r"\d{3,4}[ -]?\d{4}(?!\d)"
    )
