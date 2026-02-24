from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from PySide6 import QtWidgets

from orgpicsvideos.core.planner import build_plan
from orgpicsvideos.core.types import MediaFile, MediaType
from orgpicsvideos.ui.app import MainWindow


def _get_or_create_app() -> QtWidgets.QApplication:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    return app


def test_planned_tree_and_execution_tree(tmp_path: Path) -> None:
    _get_or_create_app()

    dest = tmp_path / "dest"
    dest.mkdir()
    src = tmp_path / "src"
    src.mkdir()

    img = src / "photo.jpg"
    img.write_bytes(b"abc")
    vid = src / "video.mp4"
    vid.write_bytes(b"def")

    media = [
        MediaFile(path=img, created_at=datetime(2002, 9, 27), media_type=MediaType.IMAGE),
        MediaFile(path=vid, created_at=datetime(2002, 9, 27), media_type=MediaType.VIDEO),
    ]

    plan = build_plan(media, dest)

    window = MainWindow()
    window._populate_structure_tree(plan, dest)
    window._populate_execution_tree(plan, dest)

    # Planned tree should contain file nodes with (copy) label.
    planned_items = []
    root = window.structure_view.topLevelItem(0)
    stack = [root]
    while stack:
        item = stack.pop()
        planned_items.append(item.text(0))
        for i in range(item.childCount()):
            stack.append(item.child(i))
    assert any("(copy)" in text for text in planned_items)

    # Execution tree should contain pending statuses for planned operations.
    exec_items = []
    root_exec = window.execution_view.topLevelItem(0)
    stack = [root_exec]
    while stack:
        item = stack.pop()
        exec_items.append(item.text(0))
        for i in range(item.childCount()):
            stack.append(item.child(i))
    assert any("(pending)" in text for text in exec_items)
