"""QObject worker that owns Playwright and its asyncio loop."""

from __future__ import annotations

import asyncio

from PySide6.QtCore import QObject, Signal, Slot

from browser.playwright_browser import PlaywrightBrowser
from detector.registry import DetectorRegistry
from models.settings import AppSettings
from parser.json_parser import JsonLeafParser
from services.analysis_service import AnalysisService
from services.api_logger import ApiLogger
from services.rule_engine import RuleEngine


class BrowserWorker(QObject):
    record_ready = Signal(object, object)
    failed = Signal(str)
    finished = Signal()

    def __init__(self, start_url: str, settings: AppSettings, rules: RuleEngine) -> None:
        super().__init__()
        self.start_url = start_url
        self.settings = settings
        self.rules = rules
        self.browser: PlaywrightBrowser | None = None

    @Slot()
    def run(self) -> None:
        try:
            logger = ApiLogger(self.settings.max_api_records)
            analyzer = AnalysisService(
                JsonLeafParser(), DetectorRegistry.default(), self.rules, self.settings
            )
            self.browser = PlaywrightBrowser(
                logger,
                analyzer,
                settings=self.settings,
                on_record=self.record_ready.emit,
            )
            asyncio.run(self.browser.run(self.start_url))
        except Exception as exc:
            self.failed.emit(str(exc))
        finally:
            self.finished.emit()

    def stop(self) -> None:
        if self.browser:
            self.browser.request_stop()
