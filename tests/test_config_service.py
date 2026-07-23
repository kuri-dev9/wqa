import json
from pathlib import Path

from models.settings import AppSettings
from services.config_service import ConfigService


def test_config_loads_browser_and_capture_settings() -> None:
    path = Path("tests/.config-load-test.json")
    path.write_text(
        json.dumps(
            {
                "browser": {
                    "headless": True,
                    "ignore_https_errors": False,
                    "viewport_width": 1280,
                    "viewport_height": 720,
                },
                "capture": {
                    "response_max_size_mb": 2.5,
                    "max_api_records": 250,
                },
                "modes": {"privacy_enabled": True, "security_enabled": False},
                "last_url": "https://internal.example",
            }
        ),
        encoding="utf-8",
    )
    try:
        settings = ConfigService(path=path).load()
        assert settings.ignore_https_errors is False
        assert settings.headless is True
        assert settings.max_response_body_bytes == int(2.5 * 1024 * 1024)
        assert settings.max_api_records == 250
        assert settings.last_url == "https://internal.example"
    finally:
        path.unlink(missing_ok=True)


def test_settings_save_round_trip() -> None:
    path = Path("tests/.config-save-test.json")
    settings = AppSettings(
        ignore_https_errors=True,
        headless=True,
        max_api_records=321,
        max_response_body_bytes=3 * 1024 * 1024,
        last_url="https://saved.example",
    )
    try:
        service = ConfigService(path=path)
        service.save(settings)
        loaded = service.load()
        assert loaded.ignore_https_errors is True
        assert loaded.headless is True
        assert loaded.max_api_records == 321
        assert loaded.response_max_size_mb == 3
        assert loaded.last_url == "https://saved.example"
    finally:
        path.unlink(missing_ok=True)
