"""Streaming-friendly CSV export with protected values only."""

from __future__ import annotations

import csv
from io import TextIOBase
from pathlib import Path
from typing import Iterable

from models.finding import Finding
from services.excel_service import ExcelService
from services.rule_engine import RuleEngine


class CsvService:
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
        with destination.open("w", encoding="utf-8-sig", newline="") as stream:
            self.write(findings, stream, include_masked=include_masked)
        return destination

    def write(
        self,
        findings: Iterable[Finding],
        stream: TextIOBase,
        *,
        include_masked: bool = False,
    ) -> None:
        writer = csv.writer(stream)
        writer.writerow(ExcelService.HEADERS)
        for finding in findings:
            if finding.masked and not include_masked:
                continue
            if not self.rules.show_in_report(finding.detected_type):
                continue
            writer.writerow(
                (
                    finding.timestamp, finding.method, finding.status, finding.api,
                    finding.field_path, finding.detected_type, finding.masked,
                    finding.displayed_value, finding.elapsed_ms, finding.response_size,
                    finding.screenshot_path,
                )
            )
