from __future__ import annotations

from datetime import datetime
from pathlib import Path

from orgpicsvideos.core.planner import build_plan
from orgpicsvideos.core.types import MediaFile, MediaType


def test_build_plan_basic(tmp_path: Path) -> None:
    dest = tmp_path / "dest"
    dest.mkdir()
    files = [
        MediaFile(path=tmp_path / "a.jpg", created_at=datetime(2002, 9, 27), media_type=MediaType.IMAGE),
        MediaFile(path=tmp_path / "b.mp4", created_at=datetime(2002, 9, 27), media_type=MediaType.VIDEO),
    ]

    plan = build_plan(files, dest)
    assert plan.total_found == 2
    assert plan.total_files == 2
    assert plan.total_images == 1
    assert plan.total_videos == 1
    assert plan.total_dirs == 2  # pics and videos


def test_build_plan_skips_resume(tmp_path: Path) -> None:
    dest = tmp_path / "dest"
    dest.mkdir()
    media = MediaFile(path=tmp_path / "a.jpg", created_at=datetime(2002, 9, 27), media_type=MediaType.IMAGE)
    skip_dest = {dest / "2002" / "sep" / "pics" / "a.jpg"}

    plan = build_plan([media], dest, skip_destinations=skip_dest)
    assert plan.total_files == 0
    assert plan.skipped_resume == 1
    assert len(plan.skipped_files) == 1


def test_build_plan_skips_duplicate(tmp_path: Path) -> None:
    dest = tmp_path / "dest"
    dest.mkdir()
    media = MediaFile(path=tmp_path / "a.jpg", created_at=datetime(2002, 9, 27), media_type=MediaType.IMAGE)

    target = dest / "2002" / "sep" / "pics" / "a.jpg"
    target.parent.mkdir(parents=True, exist_ok=True)
    media.path.write_bytes(b"abc")
    target.write_bytes(b"abc")
    mtime = media.path.stat().st_mtime
    target.utime((mtime, mtime))

    plan = build_plan([media], dest)
    assert plan.total_files == 0
    assert plan.skipped_duplicates == 1
