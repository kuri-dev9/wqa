"""JSON-backed detector activation and QA mode filtering."""

from __future__ import annotations

import json
from pathlib import Path


class RuleEngine:
    def __init__(self, rules_path: Path | None = None) -> None:
        path = rules_path or Path(__file__).resolve().parents[1] / "rules" / "rules.json"
        with path.open(encoding="utf-8") as stream:
            data = json.load(stream)
        self.rules = {rule["type"]: rule for rule in data["rules"]}
        self.modes = data["modes"]

    def is_enabled(self, detected_type: str, mode: str) -> bool:
        rule = self.rules.get(detected_type)
        return bool(
            rule
            and rule.get("enabled", False)
            and detected_type in self.modes.get(mode.upper(), [])
        )

    def show_in_report(self, detected_type: str) -> bool:
        return bool(self.rules.get(detected_type, {}).get("show_in_report", True))

    def set_enabled(self, detected_type: str, enabled: bool) -> None:
        if detected_type in self.rules:
            self.rules[detected_type]["enabled"] = enabled

    def set_show_in_report(self, detected_type: str, visible: bool) -> None:
        if detected_type in self.rules:
            self.rules[detected_type]["show_in_report"] = visible

    def types_for_mode(self, mode: str) -> set[str]:
        return set(self.modes.get(mode.upper(), []))
