from __future__ import annotations

from datetime import datetime
from pathlib import Path

from orgpicsvideos.core import utils
from orgpicsvideos.core.types import MediaType


def test_video_metadata_reasonable(monkeypatch, tmp_path: Path) -> None:
    path = tmp_path / "video.mpg"
    path.write_bytes(b"data")
    mtime = datetime(2002, 9, 27, 19, 7, 18).timestamp()
    path.utime((mtime, mtime))

    meta_dt = datetime(2002, 9, 27, 10, 0, 0)
    monkeypatch.setattr(utils, "_video_creation_datetime", lambda _: meta_dt)
    monkeypatch.setattr(utils, "_is_reasonable_media_datetime", lambda dt, p: True)

    created = utils.get_creation_time(path, MediaType.VIDEO)
    assert created == meta_dt


def test_video_metadata_suspicious_falls_back_to_mtime(monkeypatch, tmp_path: Path) -> None:
    path = tmp_path / "video.mpg"
    path.write_bytes(b"data")
    mtime_dt = datetime(2002, 9, 27, 19, 7, 18)
    mtime = mtime_dt.timestamp()
    path.utime((mtime, mtime))

    meta_dt = datetime(2026, 2, 22, 14, 28, 47)
    monkeypatch.setattr(utils, "_video_creation_datetime", lambda _: meta_dt)
    monkeypatch.setattr(utils, "_is_reasonable_media_datetime", lambda dt, p: False)

    created = utils.get_creation_time(path, MediaType.VIDEO)
    assert created == mtime_dt
