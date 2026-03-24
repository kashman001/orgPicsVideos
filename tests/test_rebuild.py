from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from orgpicsvideos.core.rebuild import build_rebuild_operations
from orgpicsvideos.core.types import MediaType
from orgpicsvideos.core.utils import detect_media_type, get_creation_time, month_name, split_media_dirs


def test_rebuild_moves_into_structure(tmp_path: Path) -> None:
    dest = tmp_path / "dest"
    dest.mkdir()
    # Create a file at root with known mtime.
    file_path = dest / "photo.jpg"
    file_path.write_bytes(b"abc")
    mtime = datetime(2002, 9, 27, 10, 0, 0).timestamp()
    os.utime(file_path, (mtime, mtime))

    ops, summary = build_rebuild_operations(dest)
    # Determine expected target using the same logic the scanner uses.
    created = get_creation_time(file_path, MediaType.IMAGE)
    target = split_media_dirs(dest, created, MediaType.IMAGE) / "photo.jpg"
    assert any(op.destination == target for op in ops)
    assert summary.total_files == 1


def test_rebuild_deletes_sidecars_by_default(tmp_path: Path) -> None:
    dest = tmp_path / "dest"
    dest.mkdir()
    sidecar = dest / "._junk.MOV"
    sidecar.write_text("x", encoding="utf-8")

    ops, _ = build_rebuild_operations(dest)
    assert any(op.op_type.value == "delete" and op.destination == sidecar for op in ops)


def test_rebuild_delete_empty_dirs(tmp_path: Path) -> None:
    dest = tmp_path / "dest"
    empty_dir = dest / "2001" / "jan" / "pics"
    empty_dir.mkdir(parents=True)

    from orgpicsvideos.core.rebuild import rebuild_destination
    from orgpicsvideos.core.logger import make_log_path

    log_path = make_log_path(dest)
    summary = rebuild_destination(dest, log_path, delete_empty_dirs=True)
    assert summary.deleted_empty_dirs >= 1
