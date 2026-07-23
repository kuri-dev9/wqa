import pytest

from detector.registry import DetectorRegistry


@pytest.mark.parametrize(
    ("value", "expected_type"),
    [
        ("contact: qa@example.com", "EMAIL"),
        ("010-1234-5678", "MOBILE_PHONE"),
        ("02-1234-5678", "PHONE"),
        ("900101-1234567", "RESIDENT_NUMBER"),
        ("123-45-67890", "BUSINESS_NUMBER"),
        ("client=192.168.0.10", "IP_ADDRESS"),
        ("eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjMifQ.signature", "JWT"),
        ("AKIAIOSFODNN7EXAMPLE", "API_KEY"),
        ("0123456789abcdef0123456789abcdef", "SESSION_ID"),
        ("qauser123", "USER_ID"),
        ("Strong!Pass1", "PASSWORD"),
    ],
)
def test_default_detectors(value: str, expected_type: str) -> None:
    detected = DetectorRegistry.default().detect(value)

    assert expected_type in {item.detected_type for item in detected}


def test_field_name_is_not_needed() -> None:
    detected = DetectorRegistry.default().detect("qa@example.com")

    assert any(item.detected_type == "EMAIL" for item in detected)
