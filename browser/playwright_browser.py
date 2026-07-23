"""Playwright browser runner and Fetch/XHR response collector."""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable, Coroutine
from dataclasses import replace
from typing import Any

import orjson
from playwright.async_api import Browser, Page, Playwright, Request, Response, async_playwright

from browser.errors import NavigationError
from models.api_record import ApiRecord
from models.finding import Finding
from models.settings import AppSettings
from services.analysis_service import AnalysisService
from services.api_logger import ApiLogger
from services.capture_service import CaptureService
from utils.formatters import format_bytes, format_elapsed
from utils.masking import protect_text

LOG = logging.getLogger(__name__)


class PlaywrightBrowser:
    """Run Chromium and forward JSON Fetch/XHR responses to the analysis layer."""

    def __init__(
        self,
        api_logger: ApiLogger,
        analyzer: AnalysisService,
        *,
        headless: bool | None = None,
        settings: AppSettings | None = None,
        on_record: Callable[[ApiRecord, list[Finding]], None] | None = None,
    ) -> None:
        self.api_logger = api_logger
        self.analyzer = analyzer
        self.settings = settings or AppSettings()
        self.headless = self.settings.headless if headless is None else headless
        self.on_record = on_record
        self.capture_service = CaptureService()
        self._started_at: dict[Request, float] = {}
        self._tasks: set[asyncio.Task[None]] = set()
        self._stop_event: asyncio.Event | None = None
        self._loop: asyncio.AbstractEventLoop | None = None

    async def run(self, start_url: str = "about:blank") -> None:
        async with async_playwright() as playwright:
            self._loop = asyncio.get_running_loop()
            self._stop_event = asyncio.Event()
            browser = await self._launch(playwright)
            context = await browser.new_context(**self.context_options())
            context.on("page", self._attach_page)
            page = await context.new_page()
            self._attach_page(page)
            navigation = await page.goto(
                self.normalize_url(start_url),
                wait_until="domcontentloaded",
                timeout=30_000,
            )
            if navigation and navigation.status == 404:
                raise NavigationError("HTTP 404")
            if navigation and navigation.status >= 500:
                raise NavigationError("HTTP 500")
            LOG.info("Chromium started. Log in and use the site normally.")
            await self._wait_until_closed(browser)
            if browser.is_connected():
                await browser.close()
            await self._drain_tasks()

    async def _launch(self, playwright: Playwright) -> Browser:
        return await playwright.chromium.launch(headless=self.headless)

    def context_options(self) -> dict[str, object]:
        return {
            "ignore_https_errors": self.settings.ignore_https_errors,
            "viewport": {
                "width": self.settings.viewport_width,
                "height": self.settings.viewport_height,
            },
        }

    def _attach_page(self, page: Page) -> None:
        page.on("request", self._on_request)
        page.on("requestfailed", self._forget_request)
        page.on("response", lambda response: self._schedule(self._handle_response(response)))

    def _on_request(self, request: Request) -> None:
        if request.resource_type in {"xhr", "fetch"}:
            self._started_at[request] = time.perf_counter()

    def _forget_request(self, request: Request) -> None:
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
        headers = await response.all_headers()
        request_headers = await request.all_headers()
        declared_size = self._content_length(headers)
        body_bytes = b""
        body_skipped = declared_size > self.settings.max_response_body_bytes
        if not body_skipped:
            try:
                body_bytes = await response.body()
            except Exception as exc:
                safe_url = protect_text(
                    response.url, self.analyzer.detectors.detect(response.url)
                )
                error_text = str(exc)
                safe_error = protect_text(
                    error_text, self.analyzer.detectors.detect(error_text)
                )
                LOG.warning(
                    "%s %s - response body read failed: %s",
                    request.method,
                    safe_url,
                    safe_error,
                )
                return
            body_skipped = len(body_bytes) > self.settings.max_response_body_bytes

        parsed_body: object | None = None
        if not body_skipped and self._is_json(headers, body_bytes):
            try:
                parsed_body = orjson.loads(body_bytes)
            except orjson.JSONDecodeError:
                pass

        record = ApiRecord.create(
            method=request.method,
            url=response.url,
            status=response.status,
            elapsed_ms=(time.perf_counter() - started_at) * 1000,
            response_headers=headers,
            response_body=parsed_body,
            response_size=declared_size or len(body_bytes),
            request_headers=request_headers,
            body_skipped=body_skipped,
            page_url=self._page_url(request),
        )
        await self.api_logger.add(record)
        findings = self._visible_findings(self.analyzer.analyze(record))
        record.detected_count = len(findings)
        if findings:
            try:
                screenshot = await self.capture_service.capture_first(request.frame.page)
            except Exception:
                screenshot = ""
            if screenshot:
                record.screenshot_path = screenshot
                findings = [replace(item, screenshot_path=screenshot) for item in findings]

        self._log_record(record, findings)
        if self.on_record:
            self.on_record(record, findings)

    def _visible_findings(self, findings: list[Finding]) -> list[Finding]:
        return [
            finding
            for finding in findings
            if (self.settings.include_masked or not finding.masked)
            and self.analyzer.rules.show_in_report(finding.detected_type)
        ]

    @staticmethod
    def _content_length(headers: dict[str, str]) -> int:
        try:
            return max(0, int(headers.get("content-length", "0")))
        except ValueError:
            return 0

    @staticmethod
    def _page_url(request: Request) -> str:
        try:
            return request.frame.page.url
        except Exception:
            return ""

    @staticmethod
    def normalize_url(url: str) -> str:
        target = url.strip()
        if not target:
            return "about:blank"
        if target == "about:blank" or "://" in target:
            return target
        return f"https://{target}"

    def _log_record(self, record: ApiRecord, findings: list[Finding]) -> None:
        LOG.info(
            "%s %s\nStatus %d\nSize %s\nTime %s",
            record.method,
            protect_text(record.url, self.analyzer.detectors.detect(record.url)),
            record.status,
            format_bytes(record.response_size),
            format_elapsed(record.elapsed_ms),
        )
        if record.body_skipped:
            LOG.info("Body: Skipped (size limit exceeded)\n")
        elif record.response_body is None:
            LOG.info("Body: non-JSON (analysis skipped)\n")
        else:
            LOG.info(
                "JSON leaves %d / findings %d",
                len(self.analyzer.parser.parse(record.response_body)),
                len(findings),
            )
            for finding in findings:
                LOG.warning(
                    "  [%s] %s = %s",
                    finding.detected_type,
                    finding.field_path,
                    finding.displayed_value,
                )
            LOG.info("")

    @staticmethod
    def _is_json(headers: dict[str, str], body: bytes) -> bool:
        if "json" in headers.get("content-type", "").lower():
            return True
        return body.lstrip().startswith((b"{", b"["))

    async def _wait_until_closed(self, browser: Browser) -> None:
        while browser.is_connected() and browser.contexts:
            if self._stop_event and self._stop_event.is_set():
                break
            if not any(context.pages for context in browser.contexts):
                break
            await asyncio.sleep(0.25)

    async def _drain_tasks(self) -> None:
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)

    def request_stop(self) -> None:
        if self._loop and self._stop_event:
            self._loop.call_soon_threadsafe(self._stop_event.set)
