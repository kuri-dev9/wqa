from io import StringIO

from models.finding import Finding
from services.csv_service import CsvService
from services.rule_engine import RuleEngine


def test_csv_export_uses_displayed_value_only() -> None:
    finding = Finding(
        field_path="data.email",
        detected_type="EMAIL",
        value="qa@example.com",
        masked=False,
        displayed_value="qa***@example.com",
        api="https://example.test",
    )
    stream = StringIO()
    CsvService(RuleEngine()).write([finding], stream)
    output = stream.getvalue()
    assert "qa***@example.com" in output
    assert "qa@example.com" not in output
