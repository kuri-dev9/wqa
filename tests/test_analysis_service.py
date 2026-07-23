from datetime import datetime

from detector.registry import DetectorRegistry
from models.api_record import ApiRecord
from parser.json_parser import JsonLeafParser
from services.analysis_service import AnalysisService


def test_analysis_returns_field_path() -> None:
    record = ApiRecord(
        timestamp=datetime.now(),
        method="GET",
        url="https://example.test/api/users",
        status=200,
        elapsed_ms=12.5,
        response_headers={"content-type": "application/json"},
        response_body={"data": [{"contact": "qa@example.com"}]},
        response_size=42,
    )

    findings = AnalysisService(JsonLeafParser(), DetectorRegistry.default()).analyze(record)

    email = next(item for item in findings if item.detected_type == "EMAIL")
    assert email.field_path == "data[0].contact"
    assert email.value == "qa@example.com"
