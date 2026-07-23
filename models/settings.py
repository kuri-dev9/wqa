"""Application settings shared by CLI and GUI."""

from dataclasses import dataclass


@dataclass(slots=True)
class AppSettings:
    headless: bool = False
    ignore_https_errors: bool = True
    viewport_width: int = 1600
    viewport_height: int = 900
    max_api_records: int = 1000
    max_response_body_bytes: int = 1024 * 1024
    include_masked: bool = False
    qa_mode: str = "PRIVACY"
    privacy_mode_enabled: bool = True
    security_mode_enabled: bool = True
    last_url: str = "about:blank"

    @property
    def response_max_size_mb(self) -> float:
        return self.max_response_body_bytes / (1024 * 1024)
