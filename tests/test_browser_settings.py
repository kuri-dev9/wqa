from browser.errors import classify_browser_error
from browser.playwright_browser import PlaywrightBrowser
from detector.registry import DetectorRegistry
from models.settings import AppSettings
from parser.json_parser import JsonLeafParser
from services.analysis_service import AnalysisService
from services.api_logger import ApiLogger


def make_browser(settings: AppSettings) -> PlaywrightBrowser:
    analyzer = AnalysisService(
        JsonLeafParser(), DetectorRegistry.default(), settings=settings
    )
    return PlaywrightBrowser(ApiLogger(), analyzer, settings=settings)


def test_https_ignore_is_applied_to_browser_context() -> None:
    browser = make_browser(AppSettings(ignore_https_errors=True))
    assert browser.context_options()["ignore_https_errors"] is True


def test_url_without_scheme_is_normalized_to_https() -> None:
    assert PlaywrightBrowser.normalize_url("internal.example") == "https://internal.example"


def test_browser_errors_are_classified() -> None:
    assert "DNS" in classify_browser_error(RuntimeError("net::ERR_NAME_NOT_RESOLVED"))
    assert "certificate" in classify_browser_error(RuntimeError("net::ERR_CERT_AUTHORITY_INVALID"))
    assert "refused" in classify_browser_error(RuntimeError("ERR_CONNECTION_REFUSED"))
    assert "timed out" in classify_browser_error(RuntimeError("Timeout 30000ms"))
    assert "404" in classify_browser_error(RuntimeError("HTTP 404"))
    assert "500" in classify_browser_error(RuntimeError("HTTP 500"))
