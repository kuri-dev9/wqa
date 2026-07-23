"""Screenshot capture for the first visible finding."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from playwright.async_api import Page


class CaptureService:
    def __init__(self, capture_dir: Path | None = None) -> None:
        self.capture_dir = capture_dir or Path(__file__).resolve().parents[1] / "capture"
        self._captured = False

    async def capture_first(self, page: Page) -> str:
        if self._captured:
            return ""
        self.capture_dir.mkdir(parents=True, exist_ok=True)
        path = self.capture_dir / f"{datetime.now():%Y%m%d_%H%M%S}.png"
        await page.screenshot(path=str(path), full_page=False)
        self._captured = True
        return str(path)

    def reset(self) -> None:
        self._captured = False
