"""PySide6 main window for WQA."""

from __future__ import annotations

import platform
from datetime import datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt, QThread
from PySide6.QtGui import QAction, QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
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
    QTreeWidgetItemIterator,
    QVBoxLayout,
    QWidget,
)

from detector.registry import DetectorRegistry
from models.api_record import ApiRecord
from models.finding import Finding
from services.config_service import ConfigService
from services.csv_service import CsvService
from services.excel_service import ExcelService
from services.rule_engine import RuleEngine
from ui.browser_worker import BrowserWorker
from ui.settings_dialog import SettingsDialog
from utils.masking import protect_text


class MainWindow(QMainWindow):
    VERSION = "0.3.0"

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("WQA - Web QA")
        self.resize(1500, 900)
        self.config_service = ConfigService()
        self.settings = self.config_service.load()
        self.rules = RuleEngine()
        self.display_detectors = DetectorRegistry.default()
        self.records: list[ApiRecord] = []
        self.findings: list[Finding] = []
        self.findings_by_record: dict[int, list[Finding]] = {}
        self.thread: QThread | None = None
        self.worker: BrowserWorker | None = None
        self.run_state = "Idle"
        self._build_ui()
        self._refresh_modes()
        self._update_status()

    def _build_ui(self) -> None:
        self._build_menu()
        root = QWidget()
        layout = QVBoxLayout(root)
        controls = QHBoxLayout()
        self.url_input = QLineEdit(self.settings.last_url)
        self.url_input.setPlaceholderText("Start URL")
        self.start_button = QPushButton("Start")
        self.stop_button = QPushButton("Stop")
        self.export_button = QPushButton("Export Excel")
        self.csv_button = QPushButton("Export CSV")
        self.clear_button = QPushButton("Clear")
        self.mode_combo = QComboBox()
        self.include_masked = QCheckBox("Include masked")
        self.password_candidate = QCheckBox("Password candidate")
        for widget in (
            self.start_button, self.stop_button, self.export_button,
            self.csv_button, self.clear_button,
        ):
            controls.addWidget(widget)
        controls.addWidget(QLabel("Mode"))
        controls.addWidget(self.mode_combo)
        controls.addWidget(self.include_masked)
        controls.addWidget(self.password_candidate)
        controls.addWidget(self.url_input, 1)
        layout.addLayout(controls)

        filters = QHBoxLayout()
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(
            ["All", "Privacy", "Security", "Current Page", "Only Unmasked"]
        )
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search API URL, Field Path, or Displayed Value")
        filters.addWidget(QLabel("Filter"))
        filters.addWidget(self.filter_combo)
        filters.addWidget(QLabel("Search"))
        filters.addWidget(self.search_input, 1)
        layout.addLayout(filters)

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

        self.running_label = QLabel()
        self.status_label = QLabel()
        self.statusBar().addWidget(self.running_label)
        self.statusBar().addPermanentWidget(self.status_label)
        self.start_button.clicked.connect(self.start_capture)
        self.stop_button.clicked.connect(self.stop_capture)
        self.export_button.clicked.connect(self.export_excel)
        self.csv_button.clicked.connect(self.export_csv)
        self.clear_button.clicked.connect(self.clear_results)
        self.filter_combo.currentTextChanged.connect(self.apply_filters)
        self.search_input.textChanged.connect(self.apply_filters)
        self.include_masked.toggled.connect(self.apply_filters)
        self.api_table.itemSelectionChanged.connect(self.show_api_detail)
        self.finding_table.itemSelectionChanged.connect(self.highlight_selected_finding)
        self.stop_button.setEnabled(False)

    def _build_menu(self) -> None:
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.open_settings)
        self.menuBar().addMenu("Settings").addAction(settings_action)
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        self.menuBar().addMenu("Help").addAction(about_action)

    @staticmethod
    def _table(headers: list[str]) -> QTableWidget:
        table = QTableWidget(0, len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.horizontalHeader().setStretchLastSection(True)
        return table

    def _refresh_modes(self) -> None:
        current = self.mode_combo.currentText()
        self.mode_combo.clear()
        if self.settings.privacy_mode_enabled:
            self.mode_combo.addItem("Privacy")
        if self.settings.security_mode_enabled:
            self.mode_combo.addItem("Security")
        index = self.mode_combo.findText(current)
        if index >= 0:
            self.mode_combo.setCurrentIndex(index)

    def start_capture(self) -> None:
        if self.thread and self.thread.isRunning():
            return
        if self.mode_combo.count() == 0:
            QMessageBox.warning(self, "WQA", "Enable at least one QA mode in Settings.")
            return
        target_url = self.url_input.text().strip() or "about:blank"
        self.settings.last_url = target_url
        self.config_service.save(self.settings)
        self.settings.qa_mode = self.mode_combo.currentText().upper()
        self.settings.include_masked = self.include_masked.isChecked()
        password_enabled = self.password_candidate.isChecked()
        self.rules.set_enabled("PASSWORD_CANDIDATE", password_enabled)
        self.rules.set_show_in_report("PASSWORD_CANDIDATE", password_enabled)
        self.thread = QThread(self)
        self.worker = BrowserWorker(target_url, self.settings, self.rules)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.record_ready.connect(self.add_record)
        self.worker.failed.connect(self._show_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self._capture_stopped)
        self.thread.start()
        self.run_state = "Running"
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self._update_status()

    def stop_capture(self) -> None:
        if self.worker:
            self.worker.stop()
        self.stop_button.setEnabled(False)

    def _capture_stopped(self) -> None:
        if self.thread:
            self.thread.deleteLater()
        self.thread = None
        self.worker = None
        self.run_state = "Stopped"
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self._update_status()

    def add_record(self, record: ApiRecord, findings: list[Finding]) -> None:
        if len(self.records) >= self.settings.max_api_records:
            removed = self.records.pop(0)
            removed_findings = self.findings_by_record.pop(id(removed), [])
            removed_ids = {id(item) for item in removed_findings}
            self.findings = [item for item in self.findings if id(item) not in removed_ids]
        self.records.append(record)
        self.findings.extend(findings)
        self.findings_by_record[id(record)] = findings
        self.apply_filters()
        self._update_status()

    def apply_filters(self, *_args: object) -> None:
        visible_records = self._filtered_records()
        self.api_table.setRowCount(0)
        for record in visible_records:
            row = self.api_table.rowCount()
            self.api_table.insertRow(row)
            values = (
                record.method, str(record.status), self._safe_text(record.url),
                f"{record.elapsed_ms:.0f} ms", str(record.detected_count),
            )
            for column, value in enumerate(values):
                self.api_table.setItem(row, column, QTableWidgetItem(value))
            self.api_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, record)

        visible_ids = {id(record) for record in visible_records}
        self.finding_table.setRowCount(0)
        for finding in self.findings:
            record = self._record_for_finding(finding)
            if not record or id(record) not in visible_ids or not self._finding_matches(finding):
                continue
            if finding.masked and (
                not self.include_masked.isChecked()
                or self.filter_combo.currentText() == "Only Unmasked"
            ):
                continue
            self._append_finding(finding)

    def _filtered_records(self) -> list[ApiRecord]:
        selected = self.filter_combo.currentText()
        query = self.search_input.text().strip().casefold()
        privacy = self.rules.types_for_mode("PRIVACY")
        security = self.rules.types_for_mode("SECURITY")
        current_page = next((item.page_url for item in reversed(self.records) if item.page_url), "")
        results = []
        for record in self.records:
            findings = self.findings_by_record.get(id(record), [])
            types = {item.detected_type for item in findings}
            if selected == "Privacy" and not types.intersection(privacy):
                continue
            if selected == "Security" and not types.intersection(security):
                continue
            if selected == "Current Page" and record.page_url != current_page:
                continue
            if selected == "Only Unmasked" and not any(not item.masked for item in findings):
                continue
            if query and not self._record_matches(record, findings, query):
                continue
            results.append(record)
        return results

    def _record_matches(
        self, record: ApiRecord, findings: list[Finding], query: str
    ) -> bool:
        if query in self._safe_text(record.url).casefold():
            return True
        return any(
            query in item.field_path.casefold()
            or query in item.displayed_value.casefold()
            for item in findings
        )

    def _finding_matches(self, finding: Finding) -> bool:
        query = self.search_input.text().strip().casefold()
        return not query or any(
            query in value.casefold()
            for value in (finding.api, finding.field_path, finding.displayed_value)
        )

    def _append_finding(self, finding: Finding) -> None:
        row = self.finding_table.rowCount()
        self.finding_table.insertRow(row)
        for column, value in enumerate(
            (
                finding.timestamp, finding.detected_type, str(finding.masked),
                finding.api, finding.field_path,
            )
        ):
            self.finding_table.setItem(row, column, QTableWidgetItem(value))
        self.finding_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, finding)

    def show_api_detail(self) -> None:
        row = self.api_table.currentRow()
        if row < 0 or not self.api_table.item(row, 0):
            return
        record = self.api_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if not isinstance(record, ApiRecord):
            return
        self._show_record(record)

    def _show_record(self, record: ApiRecord) -> None:
        self.request_tree.clear()
        self._add_mapping(self.request_tree.invisibleRootItem(), record.request_headers or {})
        self.response_tree.clear()
        if record.body_skipped:
            QTreeWidgetItem(
                self.response_tree,
                ["Skipped", f"Response exceeds {self.settings.response_max_size_mb:g} MB limit"],
            )
        elif record.response_body is None:
            QTreeWidgetItem(self.response_tree, ["Body", "Non-JSON"])
        else:
            self._populate_json(record.response_body)
        self.detected_table.setRowCount(0)
        for finding in self.findings_by_record.get(id(record), []):
            row = self.detected_table.rowCount()
            self.detected_table.insertRow(row)
            for column, value in enumerate(
                (
                    finding.detected_type, str(finding.masked),
                    finding.displayed_value, finding.field_path,
                )
            ):
                self.detected_table.setItem(row, column, QTableWidgetItem(value))

    def highlight_selected_finding(self) -> None:
        row = self.finding_table.currentRow()
        if row < 0 or not self.finding_table.item(row, 0):
            return
        finding = self.finding_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if not isinstance(finding, Finding):
            return
        record = self._record_for_finding(finding)
        if not record:
            return
        for api_row in range(self.api_table.rowCount()):
            item = self.api_table.item(api_row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) is record:
                self.api_table.selectRow(api_row)
                break
        self._show_record(record)
        iterator = QTreeWidgetItemIterator(self.response_tree)
        while iterator.value():
            item = iterator.value()
            for column in range(item.columnCount()):
                item.setBackground(column, QColor("transparent"))
            if item.data(0, Qt.ItemDataRole.UserRole) == finding.field_path:
                item.setBackground(0, QColor("#fff59d"))
                item.setBackground(1, QColor("#fff59d"))
                self.response_tree.setCurrentItem(item)
                self.response_tree.scrollToItem(item)
                self.tabs.setCurrentWidget(self.response_tree)
                break
            iterator += 1

    def _record_for_finding(self, finding: Finding) -> ApiRecord | None:
        for record in self.records:
            if any(item is finding for item in self.findings_by_record.get(id(record), [])):
                return record
        return None

    def _add_mapping(self, parent: QTreeWidgetItem, values: dict[str, str]) -> None:
        for key, value in sorted(values.items()):
            QTreeWidgetItem(parent, [key, self._safe_text(value)])

    def _populate_json(self, value: Any) -> None:
        root = self.response_tree.invisibleRootItem()
        if isinstance(value, dict):
            for key, child in value.items():
                self._add_json(root, child, str(key), str(key))
        elif isinstance(value, list):
            for index, child in enumerate(value):
                self._add_json(root, child, f"[{index}]", f"[{index}]")
        else:
            self._add_json(root, value, "$", "$")

    def _add_json(
        self, parent: QTreeWidgetItem, value: Any, label: str, path: str
    ) -> None:
        if isinstance(value, dict):
            node = QTreeWidgetItem(parent, [label, "{}"])
            node.setData(0, Qt.ItemDataRole.UserRole, path)
            for key, child in value.items():
                self._add_json(node, child, str(key), f"{path}.{key}")
        elif isinstance(value, list):
            node = QTreeWidgetItem(parent, [label, "[]"])
            node.setData(0, Qt.ItemDataRole.UserRole, path)
            for index, child in enumerate(value):
                self._add_json(node, child, f"[{index}]", f"{path}[{index}]")
        else:
            node = QTreeWidgetItem(parent, [label, self._safe_text(str(value))])
            node.setData(0, Qt.ItemDataRole.UserRole, path)

    def _safe_text(self, value: str) -> str:
        return protect_text(value, self.display_detectors.detect(value))

    def export_excel(self) -> None:
        default = Path("output") / "excel" / f"wqa_{datetime.now():%Y%m%d_%H%M%S}.xlsx"
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Excel", str(default.resolve()), "Excel Workbook (*.xlsx)"
        )
        if path:
            ExcelService(self.rules).export(
                self.findings,
                path,
                include_masked=self.include_masked.isChecked(),
                records=self.records,
            )
            self.statusBar().showMessage(f"Exported: {path}", 5000)

    def export_csv(self) -> None:
        default = Path("output") / "report" / f"wqa_{datetime.now():%Y%m%d_%H%M%S}.csv"
        path, _ = QFileDialog.getSaveFileName(
            self, "Export CSV", str(default.resolve()), "CSV (*.csv)"
        )
        if path:
            CsvService(self.rules).export(
                self.findings, path, include_masked=self.include_masked.isChecked()
            )
            self.statusBar().showMessage(f"Exported: {path}", 5000)

    def open_settings(self) -> None:
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            dialog.apply_to(self.settings)
            self.config_service.save(self.settings)
            self._refresh_modes()
            self.apply_filters()

    def show_about(self) -> None:
        try:
            playwright_version = version("playwright")
        except PackageNotFoundError:
            playwright_version = "Not installed"
        QMessageBox.about(
            self,
            "About WQA",
            f"WQA Version {self.VERSION}\n"
            f"Python {platform.python_version()}\n"
            f"Playwright {playwright_version}",
        )

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
        QMessageBox.critical(self, "WQA Browser Error", message)

    def _update_status(self) -> None:
        self.running_label.setText(f"Status: {self.run_state}")
        self.status_label.setText(
            f"Total APIs: {len(self.records)}   Findings: {len(self.findings)}"
        )

    def closeEvent(self, event: Any) -> None:
        self.stop_capture()
        if self.thread:
            self.thread.quit()
            self.thread.wait(5000)
        super().closeEvent(event)
