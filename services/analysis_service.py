"""JSON response analysis independent from browser and UI."""

from __future__ import annotations

from detector.registry import DetectorRegistry
from models.api_record import ApiRecord
from models.finding import Finding
from parser.json_parser import JsonLeafParser


class AnalysisService:
    def __init__(self, parser: JsonLeafParser, detectors: DetectorRegistry) -> None:
        self.parser = parser
        self.detectors = detectors

    def analyze(self, record: ApiRecord) -> list[Finding]:
        if record.response_body is None:
            return []

        findings: list[Finding] = []
        for leaf in self.parser.parse(record.response_body):
            # Field names are deliberately not passed to detectors.
            for match in self.detectors.detect(leaf.value):
                findings.append(
                    Finding(
                        field_path=leaf.path,
                        detected_type=match.detected_type,
                        value=match.value,
                    )
                )
        return findings
