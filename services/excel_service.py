"""Excel export with masked display values only."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from openpyxl import Workbook

from models.finding import Finding
from services.rule_engine import RuleEngine


class ExcelService:
    HEADERS = (
        "Timestamp", "Method", "Status", "API", "Field Path", "Detected Type",
        "Masked", "Displayed Value", "Elapsed Time", "Response Size", "Screenshot",
    )

    def __init__(self, rules: RuleEngine) -> None:
        self.rules = rules

    def export(
        self,
        findings: Iterable[Finding],
        path: str | Path,
        *,
        include_masked: bool = False,
    ) -> Path:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        workbook = self.build_workbook(findings, include_masked=include_masked)
        workbook.save(destination)
        return destination

    def build_workbook(
        self,
        findings: Iterable[Finding],
        *,
        include_masked: bool = False,
    ) -> Workbook:
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "WQA Findings"
        sheet.append(self.HEADERS)
        for finding in findings:
            if finding.masked and not include_masked:
                continue
            if not self.rules.show_in_report(finding.detected_type):
                continue
            sheet.append(
                (
                    finding.timestamp, finding.method, finding.status, finding.api,
                    finding.field_path, finding.detected_type, finding.masked,
                    finding.displayed_value, finding.elapsed_ms, finding.response_size,
                    finding.screenshot_path,
                )
            )
        sheet.freeze_panes = "A2"
        sheet.auto_filter.ref = sheet.dimensions
        return workbook
