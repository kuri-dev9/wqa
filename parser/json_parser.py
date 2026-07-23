"""Recursive JSON leaf parser."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class JsonLeaf:
    path: str
    value: Any


class JsonLeafParser:
    """Flatten dict/list JSON values while preserving their field paths."""

    def parse(self, value: Any) -> list[JsonLeaf]:
        leaves: list[JsonLeaf] = []
        self._walk(value, "", leaves)
        return leaves

    def _walk(self, value: Any, path: str, leaves: list[JsonLeaf]) -> None:
        if isinstance(value, dict):
            if not value:
                leaves.append(JsonLeaf(path or "$", value))
            for key, child in value.items():
                child_path = f"{path}.{key}" if path else str(key)
                self._walk(child, child_path, leaves)
        elif isinstance(value, list):
            if not value:
                leaves.append(JsonLeaf(path or "$", value))
            for index, child in enumerate(value):
                self._walk(child, f"{path}[{index}]" if path else f"[{index}]", leaves)
        else:
            leaves.append(JsonLeaf(path or "$", value))
