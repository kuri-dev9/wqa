"""Korean resident registration and business number detectors."""

import re

from detector.base import RegexDetector


class ResidentNumberDetector(RegexDetector):
    detected_type = "RESIDENT_NUMBER"
    pattern = re.compile(r"(?<!\d)\d{6}[ -]?[1-8]\d{6}(?!\d)")


class BusinessNumberDetector(RegexDetector):
    detected_type = "BUSINESS_NUMBER"
    pattern = re.compile(r"(?<!\d)\d{3}[ -]?\d{2}[ -]?\d{5}(?!\d)")
