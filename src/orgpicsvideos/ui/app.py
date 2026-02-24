"""Qt GUI application."""

from __future__ import annotations

from pathlib import Path

import time

from PySide6 import QtCore, QtGui, QtWidgets

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
        resume_enabled: bool = False,
        debug_path: Path | None = None,
    ) -> None:
        super().__init__()
        self.source = source
        self.destination = destination
        self.skip_destinations = skip_destinations or set()
        self.resume_enabled = resume_enabled
        self.debug_path = debug_path
        self._scan_start = 0.0
        self._scan_end = 0.0

    @QtCore.Slot()
    def run(self) -> None:
        try:
            media_files = []
            pics = 0
            videos = 0
            self._mark_scan_start()
            if self.debug_path:
                debug_path = self.debug_path
                debug_path.parent.mkdir(parents=True, exist_ok=True)
                with debug_path.open("a", encoding="utf-8") as debug_log:
                    debug_log.write(f"source={self.source}\n")
                    debug_log.write(f"destination={self.destination}\n")

                    def log_cb(message: str) -> None:
                        debug_log.write(message + "\n")
                        debug_log.flush()

                    log_cb("phase=scan_start")
                    for media in scan_media(self.source, self.current_dir.emit, log_cb):
                        media_files.append(media)
                        if media.media_type.value == "image":
                            pics += 1
                        else:
                            videos += 1
                        self.progress.emit(pics, videos)
                    log_cb(f"phase=scan_end pics={pics} videos={videos}")
                    log_cb("phase=plan_start")
                plan = build_plan(
                    media_files,
                    self.destination,
                    skip_destinations=self.skip_destinations,
                )
                with debug_path.open("a", encoding="utf-8") as debug_log:
                    debug_log.write(
                        "phase=plan_end "
                        f"found={plan.total_found} "
                        f"to_copy={plan.total_files} "
                        f"skipped={plan.total_skipped} "
                        f"dirs={plan.total_dirs}\n"
                    )
            else:
                # Fast path when debug logging is disabled.
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
            self._mark_scan_end()
            plan.scan_duration_seconds = self._scan_duration_seconds
            plan.resume_enabled = self.resume_enabled
            self.finished.emit(plan)
        except Exception as exc:  # noqa: BLE001
            self.error.emit(str(exc))

    @property
    def _scan_duration_seconds(self) -> float:
        return max(0.0, self._scan_end - self._scan_start)

    def _mark_scan_start(self) -> None:
        self._scan_start = time.monotonic()

    def _mark_scan_end(self) -> None:
        self._scan_end = time.monotonic()

    def _scan_debug_path(self) -> Path:
        stamp = QtCore.QDateTime.currentDateTime().toString("yyyyMMdd_HHmmss")
        return self.destination / f"debug_{stamp}.log"


class CopyWorker(QtCore.QObject):
    progress = QtCore.Signal(int, int)
    log = QtCore.Signal(str)
    finished = QtCore.Signal()
    error = QtCore.Signal(str)
    counts = QtCore.Signal(int, int)
    op_status = QtCore.Signal(str, str, bool)

    def __init__(
        self,
        plan: Plan,
        source: Path,
        destination: Path,
        debug_path: Path | None = None,
    ) -> None:
        super().__init__()
        self.plan = plan
        self.source = source
        self.destination = destination
        self.debug_path = debug_path

    @QtCore.Slot()
    def run(self) -> None:
        try:
            log_path = make_log_path(self.destination)
            with LogWriter(log_path, self.source, self.destination) as writer:
                writer.write(_format_scan_summary(self.plan))
                writer.write(_format_resume_summary(self.plan))
                writer.write(_format_duration_line("Scan duration", self.plan.scan_duration_seconds))

                debug_handle = None
                if self.debug_path:
                    self.debug_path.parent.mkdir(parents=True, exist_ok=True)
                    debug_handle = self.debug_path.open("a", encoding="utf-8")
                    debug_handle.write("copy_phase_start\n")
                    debug_handle.flush()

                copy_start = time.monotonic()
                pics_copied = 0
                videos_copied = 0

                def log_cb(line: str) -> None:
                    writer.write(line)
                    self.log.emit(line)
                    if debug_handle:
                        debug_handle.write(f"log {line}\n")
                        debug_handle.flush()

                def progress_cb(done: int, total: int) -> None:
                    self.progress.emit(done, total)

                def op_cb(op, success: bool) -> None:  # type: ignore[no-untyped-def]
                    nonlocal pics_copied, videos_copied
                    if debug_handle:
                        debug_handle.write(
                            f"op {op.op_type.value} success={success} dest={op.destination}\n"
                        )
                        debug_handle.flush()
                    self.op_status.emit(op.op_type.value, str(op.destination), success)
                    if op.op_type.value == "copy" and success:
                        if op.media_type and op.media_type.value == "image":
                            pics_copied += 1
                        elif op.media_type and op.media_type.value == "video":
                            videos_copied += 1
                        self.counts.emit(pics_copied, videos_copied)

                execute_plan(self.plan.operations, log_cb, progress_cb, op_cb)
                copy_duration = time.monotonic() - copy_start
                writer.write(_format_duration_line("Copy duration", copy_duration))
                if debug_handle:
                    debug_handle.write("copy_phase_end\n")
                    debug_handle.flush()
                    debug_handle.close()
            self.finished.emit()
        except Exception as exc:  # noqa: BLE001
            self.error.emit(str(exc))


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("OrgPicsVideos")
        self.resize(900, 600)
        self.plan: Plan | None = None
        self._scan_thread: QtCore.QThread | None = None
        self._scan_worker: ScanWorker | None = None
        self._copy_thread: QtCore.QThread | None = None
        self._copy_worker: CopyWorker | None = None
        self._current_debug_path: Path | None = None
        self._last_destination: Path | None = None

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
        self.debug_check = QtWidgets.QCheckBox("Enable debug log")
        self.debug_check.setChecked(False)

        self.stats_label = QtWidgets.QLabel(
            "Ready. Source must exist; destination can be selected or created."
        )
        self.scan_dir_label = QtWidgets.QLabel("Current Dir - (idle)")
        self.debug_label = QtWidgets.QLabel("Debug Log - (disabled)")
        self.found_label = QtWidgets.QLabel("Files Found - Pics: 0, Videos: 0")
        self.copied_label = QtWidgets.QLabel("Files Copied - Pics: 0, Videos: 0")
        self.legend_label = QtWidgets.QLabel(
            "Legend: Black = existing, Blue = new, Gray = skipped. Labels show status."
        )
        self.structure_view = QtWidgets.QTreeWidget()
        self.structure_view.setHeaderLabels(["Planned Structure"])
        self.structure_view.setColumnCount(1)
        self.structure_view.itemExpanded.connect(self._on_tree_expanded)
        self.exec_legend_label = QtWidgets.QLabel(
            "Execution Legend: Purple = pending, Green = success, Red = failed, Black = existing"
        )
        self.execution_view = QtWidgets.QTreeWidget()
        self.execution_view.setHeaderLabels(["Execution Status"])
        self.execution_view.setColumnCount(1)
        self._execution_node_map: dict[Path, QtWidgets.QTreeWidgetItem] = {}
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
        controls.addWidget(self.debug_check)
        controls.addStretch(1)

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(form)
        layout.addLayout(controls)
        layout.addWidget(self.stats_label)
        layout.addWidget(self.scan_dir_label)
        layout.addWidget(self.debug_label)
        layout.addWidget(self.found_label)
        layout.addWidget(self.copied_label)
        layout.addWidget(self.legend_label)
        layout.addWidget(self.structure_view)
        layout.addWidget(self.exec_legend_label)
        layout.addWidget(self.execution_view)
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
        self._last_destination = destination

        debug_path = None
        if self.debug_check.isChecked():
            debug_path = self._make_scan_debug_path(destination)
            debug_path.parent.mkdir(parents=True, exist_ok=True)
            debug_path.touch(exist_ok=True)
            self._set_debug_path(debug_path)
            self._current_debug_path = debug_path
            self._append_debug(f"phase=validation_passed source={source} destination={destination}")
        else:
            self._set_debug_path(None)
            self._current_debug_path = None

        skip_destinations = self._load_resume_destinations(source, destination)
        if self.debug_check.isChecked():
            self._append_debug(f"phase=resume_loaded skipped={len(skip_destinations)}")
        worker = ScanWorker(
            source,
            destination,
            skip_destinations=skip_destinations,
            resume_enabled=self.resume_check.isChecked(),
            debug_path=debug_path,
        )
        thread = QtCore.QThread(self)
        self._scan_thread = thread
        self._scan_worker = worker
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
        thread.finished.connect(self._clear_scan_refs)
        thread.start()

    def _scan_finished(self, plan: object) -> None:
        self.plan = plan  # type: ignore[assignment]
        assert isinstance(self.plan, Plan)
        self.copy_btn.setEnabled(self.plan.total_files > 0)
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        self._set_found_counts(self.plan.total_images, self.plan.total_videos)
        self._set_scan_dir("Current Dir - (idle)")
        self._populate_structure_tree(self.plan, self._last_destination)
        self._populate_execution_tree(self.plan, self._last_destination)
        summary = (
            f"Found {self.plan.total_found} files: "
            f"{self.plan.total_images} images, {self.plan.total_videos} videos. "
            f"Will create {self.plan.total_dirs} directories."
        )
        if self.plan.total_skipped > 0:
            summary += (
                " Skipped "
                f"{self.plan.total_skipped} files "
                f"(resume {self.plan.skipped_resume}, "
                f"duplicates {self.plan.skipped_duplicates})."
            )
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

        if self.debug_check.isChecked():
            self._append_debug("phase=copy_requested")
        debug_path = self._current_debug_path if self.debug_check.isChecked() else None
        worker = CopyWorker(self.plan, source, destination, debug_path=debug_path)
        thread = QtCore.QThread(self)
        self._copy_thread = thread
        self._copy_worker = worker
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.progress.connect(self._copy_progress)
        worker.counts.connect(self._copy_counts)
        worker.op_status.connect(self._on_op_status)
        worker.log.connect(self._append_log)
        worker.finished.connect(self._copy_finished)
        worker.error.connect(self._worker_error)
        worker.finished.connect(thread.quit)
        worker.error.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        worker.error.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._clear_copy_refs)
        thread.start()

    def _copy_progress(self, done: int, total: int) -> None:
        self.progress.setRange(0, total)
        self.progress.setValue(done)

    def _copy_counts(self, pics: int, videos: int) -> None:
        self._set_copied_counts(pics, videos)

    def _copy_finished(self) -> None:
        self._set_busy(False, "Copy complete.")
        self._set_scan_dir("Current Dir - (idle)")
        if not self.debug_check.isChecked():
            self._current_debug_path = None

    def _worker_error(self, message: str) -> None:
        self._set_busy(False, "Error")
        self._set_scan_dir("Current Dir - (idle)")
        if not self.debug_check.isChecked():
            self._current_debug_path = None
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
        self.debug_check.setEnabled(not busy)
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

    def _set_debug_path(self, path: Path | None) -> None:
        self._current_debug_path = path
        if path is None:
            self.debug_label.setText("Debug Log - (disabled)")
        else:
            self.debug_label.setText(f"Debug Log - {path}")

    def _make_scan_debug_path(self, destination: Path) -> Path:
        stamp = QtCore.QDateTime.currentDateTime().toString("yyyyMMdd_HHmmss")
        return destination / f"debug_{stamp}.log"

    def _append_debug(self, message: str) -> None:
        if not self._current_debug_path:
            return
        try:
            with self._current_debug_path.open("a", encoding="utf-8") as handle:
                handle.write(message + "\n")
        except OSError:
            # Debug log failures should not affect normal operation.
            return

    def _on_op_status(self, op_type: str, dest: str, success: bool) -> None:
        path = Path(dest)
        item = self._execution_node_map.get(path)
        if not item:
            return
        if item.data(0, QtCore.Qt.UserRole + 1) is True:
            return
        # Only update items that are actually planned for execution.
        status = "success" if success else "failed"
        base_name = item.text(0).split(" (", 1)[0]
        item.setText(0, f"{base_name} ({status})")
        color = QtGui.QColor("#1f9d4c") if success else QtGui.QColor("#d33")
        item.setForeground(0, QtGui.QBrush(color))
        item.setToolTip(0, str(path))

    def _populate_structure_tree(self, plan: Plan, destination_root: Path | None) -> None:
        # Planned structure tree is a static preview: existing/new/skip status.
        self.structure_view.clear()
        if not destination_root:
            return
        root_item = QtWidgets.QTreeWidgetItem([str(destination_root)])
        root_item.setData(0, QtCore.Qt.UserRole, "dir")
        root_item.setToolTip(0, str(destination_root))
        root_item.setIcon(0, self._folder_icon())
        self.structure_view.addTopLevelItem(root_item)

        node_map: dict[tuple[str, ...], QtWidgets.QTreeWidgetItem] = {(): root_item}
        for planned_dir in plan.directories:
            try:
                relative = planned_dir.path.relative_to(destination_root)
            except ValueError:
                relative = planned_dir.path
            parts = tuple(relative.parts)
            for idx in range(1, len(parts) + 1):
                key = parts[:idx]
                if key in node_map:
                    continue
                parent_key = parts[: idx - 1]
                parent = node_map[parent_key]
                base_name = parts[idx - 1]
                node = QtWidgets.QTreeWidgetItem([base_name])
                parent.addChild(node)
                node_map[key] = node
                full_path = destination_root.joinpath(*key)
                node.setData(0, QtCore.Qt.UserRole, "dir")
                node.setToolTip(0, str(full_path))
                self._apply_dir_style(node, full_path)
            leaf = node_map[parts]
            leaf.setToolTip(0, str(planned_dir.path))

        for op in plan.operations:
            if op.op_type.value != "copy" or not op.source:
                continue
            try:
                relative_dir = op.destination.parent.relative_to(destination_root)
            except ValueError:
                relative_dir = op.destination.parent
            key = tuple(relative_dir.parts)
            parent = node_map.get(key)
            if not parent:
                continue
            file_item = QtWidgets.QTreeWidgetItem([f"{op.destination.name} (copy)"])
            file_item.setToolTip(0, str(op.destination))
            file_item.setData(0, QtCore.Qt.UserRole, "file")
            file_item.setForeground(0, QtGui.QBrush(QtGui.QColor("#2b6cff")))
            file_item.setIcon(0, self._file_icon())
            parent.addChild(file_item)

        for skipped in plan.skipped_files:
            try:
                relative_dir = skipped.destination.parent.relative_to(destination_root)
            except ValueError:
                relative_dir = skipped.destination.parent
            key = tuple(relative_dir.parts)
            parent = node_map.get(key)
            if not parent:
                continue
            label = f"{skipped.destination.name} (skipped: {skipped.reason.value})"
            file_item = QtWidgets.QTreeWidgetItem([label])
            file_item.setToolTip(0, str(skipped.destination))
            file_item.setData(0, QtCore.Qt.UserRole, "skipped")
            file_item.setForeground(0, QtGui.QBrush(QtGui.QColor("#777")))
            file_item.setIcon(0, self._file_icon())
            parent.addChild(file_item)

        root_item.setExpanded(True)

    def _apply_dir_style(self, item: QtWidgets.QTreeWidgetItem, path: Path) -> None:
        exists = path.exists()
        base_name = item.text(0).split(" (", 1)[0]
        status = "existing" if exists else "new"
        item.setText(0, f"{base_name} ({status})")
        color = QtGui.QColor("#000") if exists else QtGui.QColor("#2b6cff")
        item.setForeground(0, QtGui.QBrush(color))
        item.setIcon(0, self._folder_icon())

    def _on_tree_expanded(self, item: QtWidgets.QTreeWidgetItem) -> None:
        if item.data(0, QtCore.Qt.UserRole) != "dir":
            return
        if item.parent() is None:
            return
        tooltip = item.toolTip(0)
        if tooltip:
            self._apply_dir_style(item, Path(tooltip))
        for idx in range(item.childCount()):
            child = item.child(idx)
            if child.data(0, QtCore.Qt.UserRole) == "dir":
                tooltip = child.toolTip(0)
                if tooltip:
                    self._apply_dir_style(child, Path(tooltip))

    def _folder_icon(self) -> QtGui.QIcon:
        return QtWidgets.QApplication.style().standardIcon(QtWidgets.QStyle.SP_DirIcon)

    def _file_icon(self) -> QtGui.QIcon:
        return QtWidgets.QApplication.style().standardIcon(QtWidgets.QStyle.SP_FileIcon)

    def _populate_execution_tree(self, plan: Plan, destination_root: Path | None) -> None:
        # Execution tree mirrors planned work and updates live as operations finish.
        self.execution_view.clear()
        self._execution_node_map.clear()
        if not destination_root:
            return

        root_item = QtWidgets.QTreeWidgetItem([str(destination_root)])
        root_item.setToolTip(0, str(destination_root))
        root_item.setIcon(0, self._folder_icon())
        self.execution_view.addTopLevelItem(root_item)

        node_map: dict[tuple[str, ...], QtWidgets.QTreeWidgetItem] = {(): root_item}
        for planned_dir in plan.directories:
            try:
                relative = planned_dir.path.relative_to(destination_root)
            except ValueError:
                relative = planned_dir.path
            parts = tuple(relative.parts)
            for idx in range(1, len(parts) + 1):
                key = parts[:idx]
                if key in node_map:
                    continue
                parent_key = parts[: idx - 1]
                parent = node_map[parent_key]
                node = QtWidgets.QTreeWidgetItem([parts[idx - 1]])
                parent.addChild(node)
                node_map[key] = node
                full_path = destination_root.joinpath(*key)
                node.setData(0, QtCore.Qt.UserRole, "dir")
                node.setToolTip(0, str(full_path))
                status = "existing" if full_path.exists() else "pending"
                self._set_execution_status(node, full_path, status, is_dir=True)

        for op in plan.operations:
            if op.op_type.value == "mkdir":
                continue

            if op.op_type.value != "copy" or not op.source:
                continue
            try:
                relative_dir = op.destination.parent.relative_to(destination_root)
            except ValueError:
                relative_dir = op.destination.parent
            key = tuple(relative_dir.parts)
            parent = node_map.get(key)
            if not parent:
                continue
            file_item = QtWidgets.QTreeWidgetItem([op.destination.name])
            parent.addChild(file_item)
            self._set_execution_status(file_item, op.destination, "pending", is_dir=False)

        root_item.setExpanded(True)

    def _set_execution_status(
        self,
        item: QtWidgets.QTreeWidgetItem,
        path: Path,
        status: str,
        is_dir: bool,
    ) -> None:
        # Execution tree status mapping:
        # pending (purple), success (green), failed (red), existing (black).
        base_name = item.text(0).split(" (", 1)[0]
        item.setText(0, f"{base_name} ({status})")
        item.setToolTip(0, str(path))
        if status == "pending":
            color = QtGui.QColor("#7a3df0")
        elif status == "success":
            color = QtGui.QColor("#1f9d4c")
        elif status == "existing":
            color = QtGui.QColor("#000")
            item.setData(0, QtCore.Qt.UserRole + 1, True)
        else:
            color = QtGui.QColor("#d33")
        item.setForeground(0, QtGui.QBrush(color))
        item.setIcon(0, self._folder_icon() if is_dir else self._file_icon())
        self._execution_node_map[path] = item

    def _load_resume_destinations(self, source: Path, destination: Path) -> set[Path]:
        if not self.resume_check.isChecked():
            return set()
        latest = find_latest_log(destination)
        if not latest:
            return set()
        return load_successful_destinations(latest, expected_source=source, expected_destination=destination)

    def _clear_scan_refs(self) -> None:
        self._scan_thread = None
        self._scan_worker = None

    def _clear_copy_refs(self) -> None:
        self._copy_thread = None
        self._copy_worker = None


def run() -> None:
    """Run the Qt application."""

    app = QtWidgets.QApplication([])
    window = MainWindow()
    window.show()
    app.exec()


def _format_scan_summary(plan: Plan) -> str:
    return (
        "SCAN SUMMARY: "
        f"found={plan.total_found} "
        f"images={plan.total_images} "
        f"videos={plan.total_videos} "
        f"to_copy={plan.total_files} "
        f"skipped={plan.total_skipped} "
        f"dirs={plan.total_dirs}"
    )


def _format_resume_summary(plan: Plan) -> str:
    enabled = "yes" if plan.resume_enabled else "no"
    return (
        "RESUME: "
        f"enabled={enabled} "
        f"skipped_resume={plan.skipped_resume} "
        f"skipped_duplicates={plan.skipped_duplicates}"
    )


def _format_duration_line(label: str, seconds: float) -> str:
    total_seconds = int(round(seconds))
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    return f"{label}: {hours:02d}:{minutes:02d}:{secs:02d}"
