"""Qt GUI application."""

from __future__ import annotations

from pathlib import Path

from PySide6 import QtCore, QtWidgets

from orgpicsvideos.core.copier import execute_plan
from orgpicsvideos.core.logger import (
    LogWriter,
    find_latest_log,
    load_successful_destinations,
    make_log_path,
)
from orgpicsvideos.core.planner import build_plan
from orgpicsvideos.core.scanner import scan_media
from orgpicsvideos.core.types import Plan
from orgpicsvideos.core.validator import ValidationError, validate_paths


class ScanWorker(QtCore.QObject):
    finished = QtCore.Signal(object)
    error = QtCore.Signal(str)
    progress = QtCore.Signal(int, int)
    current_dir = QtCore.Signal(str)

    def __init__(
        self,
        source: Path,
        destination: Path,
        skip_destinations: set[Path] | None = None,
    ) -> None:
        super().__init__()
        self.source = source
        self.destination = destination
        self.skip_destinations = skip_destinations or set()

    @QtCore.Slot()
    def run(self) -> None:
        try:
            media_files = []
            pics = 0
            videos = 0
            for media in scan_media(self.source, self.current_dir.emit):
                media_files.append(media)
                if media.media_type.value == "image":
                    pics += 1
                else:
                    videos += 1
                self.progress.emit(pics, videos)
            plan = build_plan(
                media_files,
                self.destination,
                skip_destinations=self.skip_destinations,
            )
            self.finished.emit(plan)
        except Exception as exc:  # noqa: BLE001
            self.error.emit(str(exc))


class CopyWorker(QtCore.QObject):
    progress = QtCore.Signal(int, int)
    log = QtCore.Signal(str)
    finished = QtCore.Signal()
    error = QtCore.Signal(str)
    counts = QtCore.Signal(int, int)

    def __init__(self, plan: Plan, source: Path, destination: Path) -> None:
        super().__init__()
        self.plan = plan
        self.source = source
        self.destination = destination

    @QtCore.Slot()
    def run(self) -> None:
        try:
            log_path = make_log_path(self.destination)
            with LogWriter(log_path, self.source, self.destination) as writer:
                pics_copied = 0
                videos_copied = 0

                def log_cb(line: str) -> None:
                    writer.write(line)
                    self.log.emit(line)

                def progress_cb(done: int, total: int) -> None:
                    self.progress.emit(done, total)

                def op_cb(op, success: bool) -> None:  # type: ignore[no-untyped-def]
                    nonlocal pics_copied, videos_copied
                    if op.op_type.value == "copy" and success:
                        if op.media_type and op.media_type.value == "image":
                            pics_copied += 1
                        elif op.media_type and op.media_type.value == "video":
                            videos_copied += 1
                        self.counts.emit(pics_copied, videos_copied)

                execute_plan(self.plan.operations, log_cb, progress_cb, op_cb)
            self.finished.emit()
        except Exception as exc:  # noqa: BLE001
            self.error.emit(str(exc))


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("OrgPicsVideos")
        self.resize(900, 600)
        self.plan: Plan | None = None

        self.source_edit = QtWidgets.QLineEdit()
        self.source_edit.setReadOnly(True)
        self.dest_edit = QtWidgets.QLineEdit()
        self.dest_edit.setReadOnly(False)

        self.source_btn = QtWidgets.QPushButton("Browse Source")
        self.dest_btn = QtWidgets.QPushButton("Browse Destination")
        self.scan_btn = QtWidgets.QPushButton("Scan")
        self.copy_btn = QtWidgets.QPushButton("Copy")
        self.copy_btn.setEnabled(False)
        self.resume_check = QtWidgets.QCheckBox("Resume from last run")
        self.resume_check.setChecked(False)

        self.stats_label = QtWidgets.QLabel(
            "Ready. Source must exist; destination can be selected or created."
        )
        self.scan_dir_label = QtWidgets.QLabel("Current Dir - (idle)")
        self.found_label = QtWidgets.QLabel("Files Found - Pics: 0, Videos: 0")
        self.copied_label = QtWidgets.QLabel("Files Copied - Pics: 0, Videos: 0")
        self.progress = QtWidgets.QProgressBar()
        self.progress.setValue(0)

        self.log_view = QtWidgets.QTextEdit()
        self.log_view.setReadOnly(True)

        form = QtWidgets.QFormLayout()
        form.addRow("Source", self._row(self.source_edit, self.source_btn))
        form.addRow("Destination", self._row(self.dest_edit, self.dest_btn))

        controls = QtWidgets.QHBoxLayout()
        controls.addWidget(self.scan_btn)
        controls.addWidget(self.copy_btn)
        controls.addWidget(self.resume_check)
        controls.addStretch(1)

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(form)
        layout.addLayout(controls)
        layout.addWidget(self.stats_label)
        layout.addWidget(self.scan_dir_label)
        layout.addWidget(self.found_label)
        layout.addWidget(self.copied_label)
        layout.addWidget(self.progress)
        layout.addWidget(self.log_view)

        container = QtWidgets.QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.source_btn.clicked.connect(self.select_source)
        self.dest_btn.clicked.connect(self.select_destination)
        self.scan_btn.clicked.connect(self.scan)
        self.copy_btn.clicked.connect(self.copy)

    def _row(self, field: QtWidgets.QLineEdit, button: QtWidgets.QPushButton) -> QtWidgets.QWidget:
        row = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(field)
        layout.addWidget(button)
        row.setLayout(layout)
        return row

    def select_source(self) -> None:
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Source Directory")
        if path:
            self.source_edit.setText(path)

    def select_destination(self) -> None:
        dialog = QtWidgets.QFileDialog(self, "Select Destination Directory")
        dialog.setFileMode(QtWidgets.QFileDialog.Directory)
        dialog.setOption(QtWidgets.QFileDialog.ShowDirsOnly, True)
        dialog.setOption(QtWidgets.QFileDialog.DontResolveSymlinks, True)
        dialog.setOption(QtWidgets.QFileDialog.DontUseNativeDialog, True)
        if self.dest_edit.text().strip():
            dialog.setDirectory(self.dest_edit.text().strip())
        if dialog.exec():
            selected = dialog.selectedFiles()
            if selected:
                self.dest_edit.setText(selected[0])

    def scan(self) -> None:
        source, destination = self._paths()
        if not source or not destination:
            self._error("Select source and destination directories.")
            return
        try:
            validate_paths(source, destination)
        except ValidationError as exc:
            self._error(str(exc))
            return

        self._set_busy(True, "Scanning...")
        self.log_view.clear()
        self._set_found_counts(0, 0)
        self._set_copied_counts(0, 0)
        self._set_scan_dir("Current Dir - (starting)")

        skip_destinations = self._load_resume_destinations(source, destination)
        worker = ScanWorker(source, destination, skip_destinations=skip_destinations)
        thread = QtCore.QThread(self)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(self._scan_finished)
        worker.error.connect(self._worker_error)
        worker.progress.connect(self._scan_progress)
        worker.current_dir.connect(self._scan_current_dir)
        worker.finished.connect(thread.quit)
        worker.error.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        worker.error.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.start()

    def _scan_finished(self, plan: object) -> None:
        self.plan = plan  # type: ignore[assignment]
        assert isinstance(self.plan, Plan)
        self.copy_btn.setEnabled(self.plan.total_files > 0)
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        self._set_found_counts(self.plan.total_images, self.plan.total_videos)
        self._set_scan_dir("Current Dir - (idle)")
        summary = (
            f"Found {self.plan.total_found} files: "
            f"{self.plan.total_images} images, {self.plan.total_videos} videos. "
            f"Will create {self.plan.total_dirs} directories."
        )
        if self.plan.total_skipped > 0:
            summary += f" Skipped {self.plan.total_skipped} already-copied files."
        if self.plan.total_files > 0:
            summary += f" Remaining to copy: {self.plan.total_files}."
        self.stats_label.setText(summary)
        if self.plan.total_found == 0:
            self._set_busy(False, "No media files found.")
        elif self.plan.total_files == 0:
            self._set_busy(False, "All files already copied.")
        else:
            self._set_busy(False, "Scan complete.")

    def copy(self) -> None:
        if not self.plan:
            self._error("Run a scan first.")
            return
        source, destination = self._paths()
        if not source or not destination:
            self._error("Select source and destination directories.")
            return

        self._set_busy(True, "Copying...")
        self.progress.setRange(0, len(self.plan.operations))
        self.progress.setValue(0)
        self._set_copied_counts(0, 0)

        worker = CopyWorker(self.plan, source, destination)
        thread = QtCore.QThread(self)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.progress.connect(self._copy_progress)
        worker.counts.connect(self._copy_counts)
        worker.log.connect(self._append_log)
        worker.finished.connect(self._copy_finished)
        worker.error.connect(self._worker_error)
        worker.finished.connect(thread.quit)
        worker.error.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        worker.error.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.start()

    def _copy_progress(self, done: int, total: int) -> None:
        self.progress.setRange(0, total)
        self.progress.setValue(done)

    def _copy_counts(self, pics: int, videos: int) -> None:
        self._set_copied_counts(pics, videos)

    def _copy_finished(self) -> None:
        self._set_busy(False, "Copy complete.")
        self._set_scan_dir("Current Dir - (idle)")

    def _worker_error(self, message: str) -> None:
        self._set_busy(False, "Error")
        self._set_scan_dir("Current Dir - (idle)")
        self._error(message)

    def _append_log(self, line: str) -> None:
        self.log_view.append(line)

    def _scan_progress(self, pics: int, videos: int) -> None:
        self._set_found_counts(pics, videos)

    def _scan_current_dir(self, message: str) -> None:
        self._set_scan_dir(message)

    def _set_busy(self, busy: bool, status: str) -> None:
        self.scan_btn.setEnabled(not busy)
        self.copy_btn.setEnabled(not busy and self.plan is not None and self.plan.total_files > 0)
        self.source_btn.setEnabled(not busy)
        self.dest_btn.setEnabled(not busy)
        self.resume_check.setEnabled(not busy)
        if busy:
            self.progress.setRange(0, 0)
        self.stats_label.setText(status)

    def _paths(self) -> tuple[Path | None, Path | None]:
        source_text = self.source_edit.text().strip()
        dest_text = self.dest_edit.text().strip()
        if not source_text or not dest_text:
            return None, None
        return Path(source_text), Path(dest_text)

    def _error(self, message: str) -> None:
        QtWidgets.QMessageBox.critical(self, "Error", message)

    def _set_found_counts(self, pics: int, videos: int) -> None:
        self.found_label.setText(f"Files Found - Pics: {pics}, Videos: {videos}")

    def _set_copied_counts(self, pics: int, videos: int) -> None:
        self.copied_label.setText(f"Files Copied - Pics: {pics}, Videos: {videos}")

    def _set_scan_dir(self, message: str) -> None:
        self.scan_dir_label.setText(message)

    def _load_resume_destinations(self, source: Path, destination: Path) -> set[Path]:
        if not self.resume_check.isChecked():
            return set()
        latest = find_latest_log(destination)
        if not latest:
            return set()
        return load_successful_destinations(latest, expected_source=source, expected_destination=destination)


def run() -> None:
    """Run the Qt application."""

    app = QtWidgets.QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
