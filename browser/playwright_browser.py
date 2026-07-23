"""Playwright browser runner and Fetch/XHR response collector."""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Coroutine
from typing import Any

import orjson
from playwright.async_api import Browser, Page, Playwright, Request, Response, async_playwright

from models.api_record import ApiRecord
from services.analysis_service import AnalysisService
from services.api_logger import ApiLogger
from utils.formatters import format_bytes, format_elapsed

LOG = logging.getLogger(__name__)


class PlaywrightBrowser:
    """Run Chromium and forward JSON Fetch/XHR responses to the analysis layer."""

    def __init__(
        self,
        api_logger: ApiLogger,
        analyzer: AnalysisService,
        *,
        headless: bool = False,
    ) -> None:
        self.api_logger = api_logger
        self.analyzer = analyzer
        self.headless = headless
        self._started_at: dict[Request, float] = {}
        self._tasks: set[asyncio.Task[None]] = set()

    async def run(self, start_url: str = "about:blank") -> None:
        async with async_playwright() as playwright:
            browser = await self._launch(playwright)
            context = await browser.new_context()
            context.on("page", self._attach_page)
            page = await context.new_page()
            self._attach_page(page)
            await page.goto(start_url)
            LOG.info("Chromium이 실행되었습니다. 직접 로그인하고 사이트를 사용하세요.")
            LOG.info("브라우저 창을 모두 닫거나 Ctrl+C를 누르면 종료됩니다.\n")
            await self._wait_until_closed(browser)
            await self._drain_tasks()

    async def _launch(self, playwright: Playwright) -> Browser:
        return await playwright.chromium.launch(headless=self.headless)

    def _attach_page(self, page: Page) -> None:
        page.on("request", self._on_request)
        page.on("requestfailed", self._forget_request)
        page.on("response", lambda response: self._schedule(self._handle_response(response)))

    def _on_request(self, request: Request) -> None:
        if request.resource_type in {"xhr", "fetch"}:
            self._started_at[request] = time.perf_counter()

    def _forget_request(self, request: Request) -> None:
        # Failed requests have no response handler to remove their start time.
        self._started_at.pop(request, None)

    def _schedule(self, coroutine: Coroutine[Any, Any, None]) -> None:
        task = asyncio.create_task(coroutine)
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    async def _handle_response(self, response: Response) -> None:
        request = response.request
        if request.resource_type not in {"xhr", "fetch"}:
            return

        started_at = self._started_at.pop(request, time.perf_counter())
        try:
            body_bytes = await response.body()
        except Exception as exc:  # browser navigation can cancel an in-flight body
            LOG.warning("%s %s\nResponse Body 읽기 실패: %s\n", request.method, response.url, exc)
            return

        elapsed_ms = (time.perf_counter() - started_at) * 1000
        headers = await response.all_headers()
        parsed_body: object | None = None
        if self._is_json(headers, body_bytes):
            try:
                parsed_body = orjson.loads(body_bytes)
            except orjson.JSONDecodeError:
                parsed_body = None

        record = ApiRecord.create(
            method=request.method,
            url=response.url,
            status=response.status,
            elapsed_ms=elapsed_ms,
            response_headers=headers,
            response_body=parsed_body,
            response_size=len(body_bytes),
        )
        await self.api_logger.add(record)
        findings = self.analyzer.analyze(record)

        LOG.info(
            "%s %s\nStatus %d\nSize %s\nTime %s",
            record.method,
            record.url,
            record.status,
            format_bytes(record.response_size),
            format_elapsed(record.elapsed_ms),
        )
        if parsed_body is None:
            LOG.info("Body: JSON 아님 (분석 생략)\n")
        else:
            LOG.info("JSON leaf %d개 / 검출 %d건\n", len(self.analyzer.parser.parse(parsed_body)), len(findings))
            for finding in findings:
                LOG.warning(
                    "  [%s] %s = %s",
                    finding.detected_type,
                    finding.field_path,
                    finding.value,
                )

    @staticmethod
    def _is_json(headers: dict[str, str], body: bytes) -> bool:
        content_type = headers.get("content-type", "").lower()
        if "json" in content_type:
            return True
        stripped = body.lstrip()
        return stripped.startswith((b"{", b"["))

    async def _wait_until_closed(self, browser: Browser) -> None:
        while browser.is_connected() and browser.contexts:
            if not any(context.pages for context in browser.contexts):
                break
            await asyncio.sleep(0.25)

    async def _drain_tasks(self) -> None:
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
