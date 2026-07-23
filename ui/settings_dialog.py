"""Persistent application settings dialog."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QSpinBox,
)

from models.settings import AppSettings


class SettingsDialog(QDialog):
    def __init__(self, settings: AppSettings, parent: object | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("WQA Settings")
        self.ignore_https = QCheckBox()
        self.ignore_https.setChecked(settings.ignore_https_errors)
        self.headless = QCheckBox()
        self.headless.setChecked(settings.headless)
        self.response_size = QDoubleSpinBox()
        self.response_size.setRange(0.1, 100)
        self.response_size.setDecimals(1)
        self.response_size.setSuffix(" MB")
        self.response_size.setValue(settings.response_max_size_mb)
        self.max_records = QSpinBox()
        self.max_records.setRange(10, 100_000)
        self.max_records.setValue(settings.max_api_records)
        self.privacy_mode = QCheckBox()
        self.privacy_mode.setChecked(settings.privacy_mode_enabled)
        self.security_mode = QCheckBox()
        self.security_mode.setChecked(settings.security_mode_enabled)

        layout = QFormLayout(self)
        layout.addRow("Ignore HTTPS Errors", self.ignore_https)
        layout.addRow("Headless Browser", self.headless)
        layout.addRow("Response Size Limit", self.response_size)
        layout.addRow("Max API Records", self.max_records)
        layout.addRow("Privacy Mode", self.privacy_mode)
        layout.addRow("Security Mode", self.security_mode)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def apply_to(self, settings: AppSettings) -> None:
        settings.ignore_https_errors = self.ignore_https.isChecked()
        settings.headless = self.headless.isChecked()
        settings.max_response_body_bytes = int(self.response_size.value() * 1024 * 1024)
        settings.max_api_records = self.max_records.value()
        settings.privacy_mode_enabled = self.privacy_mode.isChecked()
        settings.security_mode_enabled = self.security_mode.isChecked()
