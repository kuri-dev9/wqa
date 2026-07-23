"""JSON response analysis independent from browser and UI."""

from __future__ import annotations

from detector.registry import DetectorRegistry
from models.api_record import ApiRecord
from models.finding import Finding
from models.settings import AppSettings
from parser.json_parser import JsonLeafParser
from services.rule_engine import RuleEngine
from utils.masking import protect_text, protect_value


class AnalysisService:
    def __init__(
        self,
        parser: JsonLeafParser,
        detectors: DetectorRegistry,
        rules: RuleEngine | None = None,
        settings: AppSettings | None = None,
    ) -> None:
        self.parser = parser
        self.detectors = detectors
        self.rules = rules or RuleEngine()
        self.settings = settings or AppSettings()

    def analyze(self, record: ApiRecord) -> list[Finding]:
        if record.response_body is None:
            return []

        findings: list[Finding] = []
        for leaf in self.parser.parse(record.response_body):
            # Field names are deliberately not passed to detectors.
            for match in self.detectors.detect(leaf.value):
                if not self.rules.is_enabled(match.detected_type, self.settings.qa_mode):
                    continue
                findings.append(
                    Finding(
                        field_path=leaf.path,
                        detected_type=match.detected_type,
                        value=match.value,
                        masked=match.masked,
                        displayed_value=protect_value(match.value, match.detected_type),
                        timestamp=record.timestamp.isoformat(timespec="seconds"),
                        method=record.method,
                        api=protect_text(record.url, self.detectors.detect(record.url)),
                        status=record.status,
                        elapsed_ms=record.elapsed_ms,
                        response_size=record.response_size,
                    )
                )
        return findings
