from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6 import QtWidgets

from orgpicsvideos.core.planner import build_plan
from orgpicsvideos.core.types import MediaFile, MediaType
from orgpicsvideos.ui.app import MainWindow


def _get_or_create_app() -> QtWidgets.QApplication:
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    return app


def test_execution_partial_status(tmp_path: Path) -> None:
    _get_or_create_app()
    dest = tmp_path / "dest"
    dest.mkdir()
    src = tmp_path / "src"
    src.mkdir()

    img1 = src / "a.jpg"
    img2 = src / "b.jpg"
    img1.write_bytes(b"a")
    img2.write_bytes(b"b")

    media = [
        MediaFile(path=img1, created_at=datetime(2002, 9, 27), media_type=MediaType.IMAGE),
        MediaFile(path=img2, created_at=datetime(2002, 9, 27), media_type=MediaType.IMAGE),
    ]
    plan = build_plan(media, dest)

    window = MainWindow()
    window._last_destination = dest
    window._populate_execution_tree(plan, dest)

    # Simulate one copy success.
    dest_file = dest / "2002" / "sep" / "pics" / "a.jpg"
    window._on_op_status("copy", str(dest_file), True)

    # Parent directory should be marked partial.
    dir_item = window._execution_node_map[dest / "2002" / "sep" / "pics"]
    assert "(partial)" in dir_item.text(0)
