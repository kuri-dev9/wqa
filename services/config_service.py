"""Load and persist user-editable WQA settings."""

from __future__ import annotations

import json
from pathlib import Path

from models.settings import AppSettings


class ConfigService:
    def __init__(self, path: Path | None = None, default_path: Path | None = None) -> None:
        root = Path(__file__).resolve().parents[1]
        self.path = path or root / "config.user.json"
        self.default_path = default_path or root / "config.json"

    def load(self) -> AppSettings:
        source = self.path if self.path.exists() else self.default_path
        if not source.exists():
            return AppSettings()
        try:
            data = json.loads(source.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError, TypeError):
            return AppSettings()
        browser = data.get("browser", {})
        capture = data.get("capture", {})
        modes = data.get("modes", {})
        max_mb = self._positive_number(capture.get("response_max_size_mb"), 1)
        return AppSettings(
            headless=bool(browser.get("headless", False)),
            ignore_https_errors=bool(browser.get("ignore_https_errors", True)),
            viewport_width=self._positive_int(browser.get("viewport_width"), 1600),
            viewport_height=self._positive_int(browser.get("viewport_height"), 900),
            max_api_records=self._positive_int(capture.get("max_api_records"), 1000),
            max_response_body_bytes=int(max_mb * 1024 * 1024),
            privacy_mode_enabled=bool(modes.get("privacy_enabled", True)),
            security_mode_enabled=bool(modes.get("security_enabled", True)),
            last_url=str(data.get("last_url") or "about:blank"),
        )

    def save(self, settings: AppSettings) -> None:
        data = {
            "browser": {
                "headless": settings.headless,
                "ignore_https_errors": settings.ignore_https_errors,
                "viewport_width": settings.viewport_width,
                "viewport_height": settings.viewport_height,
            },
            "capture": {
                "response_max_size_mb": settings.response_max_size_mb,
                "max_api_records": settings.max_api_records,
            },
            "modes": {
                "privacy_enabled": settings.privacy_mode_enabled,
                "security_enabled": settings.security_mode_enabled,
            },
            "last_url": settings.last_url,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    def save_last_url(self, url: str) -> None:
        settings = self.load()
        settings.last_url = url
        self.save(settings)

    @staticmethod
    def _positive_int(value: object, default: int) -> int:
        try:
            parsed = int(value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return default
        return parsed if parsed > 0 else default

    @staticmethod
    def _positive_number(value: object, default: float) -> float:
        try:
            parsed = float(value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return default
        return parsed if parsed > 0 else default
