"""Web QA Tool entry point."""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze Fetch/XHR JSON responses in real time.")
    parser.add_argument("--url", default="about:blank", help="Initial browser URL")
    parser.add_argument("--headless", action="store_true", help="Run CLI browser without UI")
    parser.add_argument("--cli", action="store_true", help="Use console mode instead of the GUI")
    return parser


async def run_cli(url: str, headless: bool) -> None:
    from browser.playwright_browser import PlaywrightBrowser
    from detector.registry import DetectorRegistry
    from models.settings import AppSettings
    from parser.json_parser import JsonLeafParser
    from services.analysis_service import AnalysisService
    from services.api_logger import ApiLogger
    from services.config_service import ConfigService

    settings = ConfigService().load()
    if headless:
        settings.headless = True
    logger = ApiLogger(settings.max_api_records)
    analyzer = AnalysisService(JsonLeafParser(), DetectorRegistry.default(), settings=settings)
    await PlaywrightBrowser(logger, analyzer, settings=settings).run(url)


def run_gui() -> int:
    from PySide6.QtWidgets import QApplication

    from ui.main_window import MainWindow

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


def main() -> None:
    args = build_parser().parse_args()
    from services.logging_service import configure_logging

    configure_logging()
    if args.cli or args.headless:
        try:
            asyncio.run(run_cli(args.url, args.headless))
        except KeyboardInterrupt:
            logging.info("WQA stopped.")
    else:
        raise SystemExit(run_gui())


if __name__ == "__main__":
    main()
