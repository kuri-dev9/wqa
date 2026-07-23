from models.finding import Finding
from services.excel_service import ExcelService
from services.rule_engine import RuleEngine


def finding(masked: bool) -> Finding:
    return Finding(
        field_path="user.email",
        detected_type="EMAIL",
        value="qa@example.com",
        masked=masked,
        displayed_value="qa***@example.com",
    )


def test_excel_defaults_to_unmasked_findings_and_never_writes_raw_value() -> None:
    workbook = ExcelService(RuleEngine()).build_workbook(
        [finding(False), finding(True)]
    )
    rows = list(workbook["Detail"].values)
    assert len(rows) == 2
    assert "qa***@example.com" in rows[1]
    assert all("qa@example.com" not in row for row in rows)


def test_excel_contains_summary_sheet() -> None:
    workbook = ExcelService(RuleEngine()).build_workbook([finding(False)])
    summary = dict(
        row for row in workbook["Summary"].iter_rows(min_row=2, max_row=6, values_only=True)
    )
    assert summary["Privacy Findings"] == 1
    assert summary["Security Findings"] == 0
