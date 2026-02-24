from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest
from PIL import Image
from PySide6 import QtWidgets

from orgpicsvideos.core.planner import build_plan
from orgpicsvideos.core.types import MediaFile, MediaType
from orgpicsvideos.ui.app import MainWindow

pytest.importorskip("pytestqt")

pytestmark = pytest.mark.ui


def test_sidecar_delete_in_copy(qtbot, tmp_path: Path) -> None:
    dest = tmp_path / "dest"
    dest.mkdir()
    src = tmp_path / "src"
    src.mkdir()

    # Create a small EXIF image for deterministic timestamp.
    photo = src / "photo.jpg"
    img = Image.new("RGB", (16, 16), color=(255, 0, 0))
    exif = img.getexif()
    exif[36867] = "2002:09:27 10:00:00"
    img.save(photo, exif=exif)

    # Sidecar in destination should be deleted by default.
    sidecar = dest / "._junk.MOV"
    sidecar.write_text("x", encoding="utf-8")

    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    window.source_edit.setText(str(src))
    window.dest_edit.setText(str(dest))
    window.keep_sidecars_check.setChecked(False)

    window.scan_btn.click()
    qtbot.waitUntil(lambda: "Scan complete" in window.stats_label.text(), timeout=5000)

    window.copy_btn.click()
    qtbot.waitUntil(lambda: "Copy complete" in window.stats_label.text(), timeout=5000)

    assert not sidecar.exists()
