from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PIL import Image

from orgpicsvideos.core.utils import (
    detect_media_type,
    get_creation_time,
    is_probable_duplicate,
)


def _make_exif_image(path: Path, dt: datetime) -> None:
    image = Image.new("RGB", (16, 16), color=(255, 0, 0))
    exif = image.getexif()
    exif[36867] = dt.strftime("%Y:%m:%d %H:%M:%S")  # DateTimeOriginal
    image.save(path, exif=exif)


def test_get_creation_time_uses_exif(tmp_path: Path) -> None:
    path = tmp_path / "photo.jpg"
    dt = datetime(2002, 9, 27, 17, 23, 24)
    _make_exif_image(path, dt)

    media_type = detect_media_type(path)
    assert media_type is not None
    created = get_creation_time(path, media_type)
    assert created == dt


def test_is_probable_duplicate(tmp_path: Path) -> None:
    src = tmp_path / "src.jpg"
    dst = tmp_path / "dst.jpg"
    src.write_bytes(b"abc")
    dst.write_bytes(b"abc")
    # Align mtime for heuristic.
    mtime = src.stat().st_mtime
    dst.utime((mtime, mtime))

    assert is_probable_duplicate(src, dst) is True
