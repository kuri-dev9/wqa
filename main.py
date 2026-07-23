"""Web QA Tool command-line entry point."""

from __future__ import annotations

import argparse
import asyncio
import logging

from browser.playwright_browser import PlaywrightBrowser
from detector.registry import DetectorRegistry
from parser.json_parser import JsonLeafParser
from services.analysis_service import AnalysisService
from services.api_logger import ApiLogger


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="사용 중인 Chromium의 Fetch/XHR JSON 응답을 실시간 분석합니다."
    )
    parser.add_argument(
        "--url", default="about:blank", help="브라우저에서 처음 열 URL (기본: about:blank)"
    )
    parser.add_argument(
        "--headless", action="store_true", help="브라우저 UI 없이 실행 (점검/자동화용)"
    )
    return parser


async def run(url: str, headless: bool) -> None:
    logger = ApiLogger()
    analyzer = AnalysisService(JsonLeafParser(), DetectorRegistry.default())
    browser = PlaywrightBrowser(logger, analyzer, headless=headless)
    await browser.run(url)


def main() -> None:
    args = build_parser().parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    try:
        asyncio.run(run(args.url, args.headless))
    except KeyboardInterrupt:
        logging.info("\nWQA를 종료했습니다.")


if __name__ == "__main__":
    main()
