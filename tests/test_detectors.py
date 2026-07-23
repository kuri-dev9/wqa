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
        ("qauser123", "USER_ID_CANDIDATE"),
        ("Strong!Pass1", "PASSWORD_CANDIDATE"),
    ],
)
def test_default_detectors(value: str, expected_type: str) -> None:
    detected = DetectorRegistry.default().detect(value)

    assert expected_type in {item.detected_type for item in detected}


def test_field_name_is_not_needed() -> None:
    detected = DetectorRegistry.default().detect("qa@example.com")

    assert any(item.detected_type == "EMAIL" for item in detected)


def test_server_like_values_are_candidates_not_confirmed_user_ids() -> None:
    registry = DetectorRegistry.default()
    for value in ("server01", "router001", "version2026"):
        types = {item.detected_type for item in registry.detect(value)}
        assert "USER_ID" not in types
        assert "USER_ID_CANDIDATE" in types


def test_false_positive_password_is_rejected() -> None:
    types = {
        item.detected_type for item in DetectorRegistry.default().detect("Error-Code_100!")
    }
    assert "PASSWORD_CANDIDATE" not in types


def test_masked_email_and_phone_are_not_detected_as_complete_values() -> None:
    registry = DetectorRegistry.default()
    assert "EMAIL" not in {item.detected_type for item in registry.detect("ab***@gmail.com")}
    assert "MOBILE_PHONE" not in {
        item.detected_type for item in registry.detect("010****1234")
    }


def test_korean_name_is_candidate_and_mask_state_is_reported() -> None:
    registry = DetectorRegistry.default()
    plain = next(item for item in registry.detect("홍길동") if item.detected_type == "NAME_CANDIDATE")
    masked = next(item for item in registry.detect("홍*동") if item.detected_type == "NAME_CANDIDATE")
    assert plain.masked is False
    assert masked.masked is True
