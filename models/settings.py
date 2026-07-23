"""Application settings shared by CLI and GUI."""

from dataclasses import dataclass


@dataclass(slots=True)
class AppSettings:
    max_api_records: int = 1000
    max_response_body_bytes: int = 1024 * 1024
    include_masked: bool = False
    qa_mode: str = "PRIVACY"
