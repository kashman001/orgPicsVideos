from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest
from PIL import Image
from PySide6 import QtWidgets

from orgpicsvideos.ui.app import MainWindow

pytest.importorskip("pytestqt")


def test_ui_smoke_scan_and_copy(qtbot, tmp_path: Path) -> None:
    source = tmp_path / "source"
    dest = tmp_path / "dest"
    source.mkdir()
    dest.mkdir()

    photo = source / "photo.jpg"
    img = Image.new("RGB", (16, 16), color=(255, 0, 0))
    exif = img.getexif()
    exif[36867] = "2002:09:27 10:00:00"
    img.save(photo, exif=exif)

    window = MainWindow()
    qtbot.addWidget(window)
    window.show()

    window.source_edit.setText(str(source))
    window.dest_edit.setText(str(dest))

    window.scan_btn.click()
    qtbot.waitUntil(lambda: "Scan complete" in window.stats_label.text(), timeout=5000)

    assert window.copy_btn.isEnabled()

    window.copy_btn.click()
    qtbot.waitUntil(lambda: "Copy complete" in window.stats_label.text(), timeout=5000)

    assert (dest / "2002" / "sep" / "pics" / "photo.jpg").exists()
