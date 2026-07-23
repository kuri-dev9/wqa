"""Excel export with masked display values only."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from openpyxl import Workbook

from detector.registry import DetectorRegistry
from models.api_record import ApiRecord
from models.finding import Finding
from services.rule_engine import RuleEngine
from utils.masking import protect_text


class ExcelService:
    HEADERS = (
        "Timestamp", "Method", "Status", "API", "Field Path", "Detected Type",
        "Masked", "Displayed Value", "Elapsed Time", "Response Size", "Screenshot",
    )

    def __init__(self, rules: RuleEngine) -> None:
        self.rules = rules
        self.detectors = DetectorRegistry.default()

    def export(
        self,
        findings: Iterable[Finding],
        path: str | Path,
        *,
        include_masked: bool = False,
        records: Iterable[ApiRecord] = (),
    ) -> Path:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        workbook = self.build_workbook(
            findings, include_masked=include_masked, records=records
        )
        workbook.save(destination)
        return destination

    def build_workbook(
        self,
        findings: Iterable[Finding],
        *,
        include_masked: bool = False,
        records: Iterable[ApiRecord] = (),
    ) -> Workbook:
        findings_list = [
            finding
            for finding in findings
            if (include_masked or not finding.masked)
            and self.rules.show_in_report(finding.detected_type)
        ]
        records_list = list(records)
        workbook = Workbook()
        summary = workbook.active
        summary.title = "Summary"
        privacy_types = self.rules.types_for_mode("PRIVACY")
        security_types = self.rules.types_for_mode("SECURITY")
        summary.append(("Metric", "Value"))
        summary.append(("Total APIs", len(records_list)))
        summary.append(
            ("Privacy Findings", sum(item.detected_type in privacy_types for item in findings_list))
        )
        summary.append(
            ("Security Findings", sum(item.detected_type in security_types for item in findings_list))
        )
        summary.append(("Response Size", sum(item.response_size for item in records_list)))
        average = (
            sum(item.elapsed_ms for item in records_list) / len(records_list)
            if records_list
            else 0
        )
        summary.append(("Average Elapsed", average))
        summary.append(())
        summary.append(("API", "Detected Count"))
        count_by_api: dict[str, int] = {}
        for item in findings_list:
            count_by_api[item.api] = count_by_api.get(item.api, 0) + 1
        api_urls = {
            protect_text(record.url, self.detectors.detect(record.url))
            for record in records_list
        }
        for safe_url in sorted(api_urls):
            summary.append((safe_url, count_by_api.get(safe_url, 0)))
        summary.freeze_panes = "A2"

        detail = workbook.create_sheet("Detail")
        detail.append(self.HEADERS)
        for finding in findings_list:
            detail.append(
                (
                    finding.timestamp, finding.method, finding.status, finding.api,
                    finding.field_path, finding.detected_type, finding.masked,
                    finding.displayed_value, finding.elapsed_ms, finding.response_size,
                    finding.screenshot_path,
                )
            )
        detail.freeze_panes = "A2"
        detail.auto_filter.ref = detail.dimensions
        return workbook
