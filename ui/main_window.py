"""PySide6 main window for WQA."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt, QThread
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from detector.registry import DetectorRegistry
from models.api_record import ApiRecord
from models.finding import Finding
from models.settings import AppSettings
from services.excel_service import ExcelService
from services.rule_engine import RuleEngine
from ui.browser_worker import BrowserWorker
from utils.masking import protect_text


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("WQA - Web QA")
        self.resize(1450, 850)
        self.settings = AppSettings()
        self.rules = RuleEngine()
        self.display_detectors = DetectorRegistry.default()
        self.records: list[ApiRecord] = []
        self.findings: list[Finding] = []
        self.findings_by_record: dict[int, list[Finding]] = {}
        self.thread: QThread | None = None
        self.worker: BrowserWorker | None = None
        self._build_ui()
        self._update_status()

    def _build_ui(self) -> None:
        root = QWidget()
        layout = QVBoxLayout(root)
        controls = QHBoxLayout()
        self.url_input = QLineEdit("about:blank")
        self.url_input.setPlaceholderText("Start URL")
        self.start_button = QPushButton("Start")
        self.stop_button = QPushButton("Stop")
        self.export_button = QPushButton("Export Excel")
        self.clear_button = QPushButton("Clear")
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Privacy", "Security"])
        self.include_masked = QCheckBox("Include masked")
        self.password_candidate = QCheckBox("Password candidate")
        controls.addWidget(self.start_button)
        controls.addWidget(self.stop_button)
        controls.addWidget(self.export_button)
        controls.addWidget(self.clear_button)
        controls.addWidget(QLabel("Mode"))
        controls.addWidget(self.mode_combo)
        controls.addWidget(self.include_masked)
        controls.addWidget(self.password_candidate)
        controls.addWidget(self.url_input, 1)
        layout.addLayout(controls)

        horizontal = QSplitter(Qt.Orientation.Horizontal)
        lists = QSplitter(Qt.Orientation.Vertical)
        self.api_table = self._table(["Method", "Status", "URL", "Elapsed", "Detected Count"])
        self.finding_table = self._table(["Timestamp", "Type", "Masked", "API", "Field Path"])
        lists.addWidget(self.api_table)
        lists.addWidget(self.finding_table)
        horizontal.addWidget(lists)

        self.tabs = QTabWidget()
        self.request_tree = QTreeWidget()
        self.request_tree.setHeaderLabels(["Request", "Value"])
        self.response_tree = QTreeWidget()
        self.response_tree.setHeaderLabels(["Response JSON", "Value"])
        self.detected_table = self._table(["Type", "Masked", "Displayed Value", "Field Path"])
        self.tabs.addTab(self.request_tree, "Request")
        self.tabs.addTab(self.response_tree, "Response (JSON)")
        self.tabs.addTab(self.detected_table, "Detected")
        horizontal.addWidget(self.tabs)
        horizontal.setStretchFactor(0, 3)
        horizontal.setStretchFactor(1, 2)
        layout.addWidget(horizontal)
        self.setCentralWidget(root)

        self.status_label = QLabel()
        self.statusBar().addPermanentWidget(self.status_label)
        self.start_button.clicked.connect(self.start_capture)
        self.stop_button.clicked.connect(self.stop_capture)
        self.export_button.clicked.connect(self.export_excel)
        self.clear_button.clicked.connect(self.clear_results)
        self.api_table.itemSelectionChanged.connect(self.show_api_detail)
        self.stop_button.setEnabled(False)

    @staticmethod
    def _table(headers: list[str]) -> QTableWidget:
        table = QTableWidget(0, len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.horizontalHeader().setStretchLastSection(True)
        return table

    def start_capture(self) -> None:
        if self.thread and self.thread.isRunning():
            return
        self.settings.qa_mode = self.mode_combo.currentText().upper()
        self.settings.include_masked = self.include_masked.isChecked()
        password_enabled = self.password_candidate.isChecked()
        self.rules.set_enabled("PASSWORD_CANDIDATE", password_enabled)
        self.rules.set_show_in_report("PASSWORD_CANDIDATE", password_enabled)
        self.thread = QThread(self)
        self.worker = BrowserWorker(self.url_input.text().strip() or "about:blank", self.settings, self.rules)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.record_ready.connect(self.add_record)
        self.worker.failed.connect(self._show_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self._capture_stopped)
        self.thread.start()
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.statusBar().showMessage("Capturing Fetch/XHR responses")

    def stop_capture(self) -> None:
        if self.worker:
            self.worker.stop()
        self.stop_button.setEnabled(False)

    def _capture_stopped(self) -> None:
        if self.thread:
            self.thread.deleteLater()
        self.thread = None
        self.worker = None
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.statusBar().showMessage("Stopped", 3000)

    def add_record(self, record: ApiRecord, findings: list[Finding]) -> None:
        if len(self.records) >= self.settings.max_api_records:
            removed = self.records.pop(0)
            removed_findings = self.findings_by_record.pop(id(removed), [])
            removed_ids = {id(item) for item in removed_findings}
            self.findings = [item for item in self.findings if id(item) not in removed_ids]
            self.api_table.removeRow(0)
            self._rebuild_finding_table()
        self.records.append(record)
        self.findings.extend(findings)
        self.findings_by_record[id(record)] = findings
        row = self.api_table.rowCount()
        self.api_table.insertRow(row)
        values = (
            record.method,
            str(record.status),
            self._safe_text(record.url),
            f"{record.elapsed_ms:.0f} ms",
            str(record.detected_count),
        )
        for column, value in enumerate(values):
            self.api_table.setItem(row, column, QTableWidgetItem(value))
        self.api_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, record)
        for finding in findings:
            self._append_finding(finding)
        self._update_status()

    def _append_finding(self, finding: Finding) -> None:
        row = self.finding_table.rowCount()
        self.finding_table.insertRow(row)
        values = (
            finding.timestamp,
            finding.detected_type,
            str(finding.masked),
            finding.api,
            finding.field_path,
        )
        for column, value in enumerate(values):
            self.finding_table.setItem(row, column, QTableWidgetItem(value))

    def _rebuild_finding_table(self) -> None:
        self.finding_table.setRowCount(0)
        for finding in self.findings:
            self._append_finding(finding)

    def show_api_detail(self) -> None:
        row = self.api_table.currentRow()
        if row < 0:
            return
        item = self.api_table.item(row, 0)
        record = item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(record, ApiRecord):
            return
        self.request_tree.clear()
        self._add_mapping(self.request_tree.invisibleRootItem(), record.request_headers or {})
        self.response_tree.clear()
        if record.body_skipped:
            QTreeWidgetItem(self.response_tree, ["Skipped", "Response exceeds 1 MB limit"])
        elif record.response_body is None:
            QTreeWidgetItem(self.response_tree, ["Body", "Non-JSON"])
        else:
            self._add_json(self.response_tree.invisibleRootItem(), record.response_body)
        self.detected_table.setRowCount(0)
        for finding in self.findings_by_record.get(id(record), []):
            row_index = self.detected_table.rowCount()
            self.detected_table.insertRow(row_index)
            for column, value in enumerate(
                (finding.detected_type, str(finding.masked), finding.displayed_value, finding.field_path)
            ):
                self.detected_table.setItem(row_index, column, QTableWidgetItem(value))

    def _add_mapping(self, parent: QTreeWidgetItem, values: dict[str, str]) -> None:
        for key, value in sorted(values.items()):
            QTreeWidgetItem(parent, [key, self._safe_text(value)])

    def _add_json(self, parent: QTreeWidgetItem, value: Any, label: str = "$") -> None:
        if isinstance(value, dict):
            node = QTreeWidgetItem(parent, [label, "{}"])
            for key, child in value.items():
                self._add_json(node, child, str(key))
        elif isinstance(value, list):
            node = QTreeWidgetItem(parent, [label, "[]"])
            for index, child in enumerate(value):
                self._add_json(node, child, f"[{index}]")
        else:
            QTreeWidgetItem(parent, [label, self._safe_text(str(value))])

    def _safe_text(self, value: str) -> str:
        return protect_text(value, self.display_detectors.detect(value))

    def export_excel(self) -> None:
        default = Path("output") / "excel" / f"wqa_{datetime.now():%Y%m%d_%H%M%S}.xlsx"
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Excel", str(default.resolve()), "Excel Workbook (*.xlsx)"
        )
        if not path:
            return
        ExcelService(self.rules).export(
            self.findings, path, include_masked=self.include_masked.isChecked()
        )
        self.statusBar().showMessage(f"Exported: {path}", 5000)

    def clear_results(self) -> None:
        self.records.clear()
        self.findings.clear()
        self.findings_by_record.clear()
        self.api_table.setRowCount(0)
        self.finding_table.setRowCount(0)
        self.detected_table.setRowCount(0)
        self.request_tree.clear()
        self.response_tree.clear()
        self._update_status()

    def _show_error(self, message: str) -> None:
        QMessageBox.critical(self, "WQA Error", message)

    def _update_status(self) -> None:
        self.status_label.setText(
            f"Total APIs: {len(self.records)}   Findings: {len(self.findings)}"
        )

    def closeEvent(self, event: Any) -> None:
        self.stop_capture()
        if self.thread:
            self.thread.quit()
            self.thread.wait(3000)
        super().closeEvent(event)
