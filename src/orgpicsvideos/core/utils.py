"""Utility helpers for filesystem and date handling."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import sys
from typing import Iterable

from PIL import Image
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser

from .types import IMAGE_EXTENSIONS, VIDEO_EXTENSIONS, MediaType

MONTH_NAMES = [
    "jan",
    "feb",
    "mar",
    "apr",
    "may",
    "jun",
    "jul",
    "aug",
    "sep",
    "oct",
    "nov",
    "dec",
]


def get_creation_time(path: Path, media_type: MediaType | None = None) -> datetime:
    """Return a best-effort creation timestamp for a file.

    Preference order:
    1) Media capture time (EXIF for images; container metadata for videos).
    2) For videos without reliable metadata, use mtime (often closer to capture date).
    3) File system birthtime where available; otherwise fall back to mtime (Unix) or ctime (Windows).
    """

    media_type = media_type or detect_media_type(path)
    if media_type == MediaType.IMAGE:
        exif_dt = _image_exif_datetime(path)
        if exif_dt:
            return exif_dt
    if media_type == MediaType.VIDEO:
        video_dt = _video_creation_datetime(path)
        if video_dt and _is_reasonable_media_datetime(video_dt, path):
            return video_dt
        # Video metadata often missing or unreliable; prefer mtime over birthtime.
        try:
            mtime = datetime.fromtimestamp(path.stat().st_mtime)
            return mtime
        except OSError:
            pass

    stat = path.stat()
    if hasattr(stat, "st_birthtime"):
        return datetime.fromtimestamp(stat.st_birthtime)
    if sys.platform == "win32":
        return datetime.fromtimestamp(stat.st_ctime)
    # On Unix-like systems without birthtime, prefer mtime over ctime.
    if stat.st_mtime:
        return datetime.fromtimestamp(stat.st_mtime)
    return datetime.fromtimestamp(stat.st_ctime)


def detect_media_type(path: Path) -> MediaType | None:
    """Return media type based on file extension, or None if unknown."""

    ext = path.suffix.lower()
    if ext in IMAGE_EXTENSIONS:
        return MediaType.IMAGE
    if ext in VIDEO_EXTENSIONS:
        return MediaType.VIDEO
    return None


def month_name(dt: datetime) -> str:
    """Return three-letter month name."""

    return MONTH_NAMES[dt.month - 1]


def is_under(path: Path, candidate_parent: Path) -> bool:
    """Return True if path is under candidate_parent."""

    try:
        path.relative_to(candidate_parent)
        return True
    except ValueError:
        return False


def unique_path(destination: Path, taken: set[Path]) -> Path:
    """Return a non-colliding destination path."""

    # Check both in-memory collisions and existing paths on disk.
    if destination not in taken and not destination.exists():
        taken.add(destination)
        return destination

    stem = destination.stem
    suffix = destination.suffix
    parent = destination.parent
    counter = 1
    while True:
        candidate = parent / f"{stem}_{counter}{suffix}"
        if candidate not in taken and not candidate.exists():
            taken.add(candidate)
            return candidate
        counter += 1


def is_probable_duplicate(source: Path, destination: Path) -> bool:
    """Heuristic duplicate check based on size and mtime."""

    try:
        src_stat = source.stat()
        dst_stat = destination.stat()
    except OSError:
        return False
    return (
        src_stat.st_size == dst_stat.st_size
        and src_stat.st_mtime_ns == dst_stat.st_mtime_ns
    )


def split_media_dirs(destination_root: Path, dt: datetime, media_type: MediaType) -> Path:
    """Return destination directory for a media item."""

    year = str(dt.year)
    month = month_name(dt)
    leaf = "pics" if media_type == MediaType.IMAGE else "videos"
    return destination_root / year / month / leaf


def _image_exif_datetime(path: Path) -> datetime | None:
    try:
        with Image.open(path) as img:
            exif = img.getexif()
            if not exif:
                return None
            raw = exif.get(36867) or exif.get(36868) or exif.get(306)
            if not raw:
                return None
            return _parse_exif_datetime(str(raw))
    except Exception:  # noqa: BLE001
        return None


def _parse_exif_datetime(value: str) -> datetime | None:
    try:
        return datetime.strptime(value.strip(), "%Y:%m:%d %H:%M:%S")
    except Exception:  # noqa: BLE001
        return None


def _video_creation_datetime(path: Path) -> datetime | None:
    # Video container metadata can be sparse or unreliable; parse conservatively.
    try:
        parser = createParser(str(path))
        if not parser:
            return None
        with parser:
            metadata = extractMetadata(parser)
        if not metadata:
            return None
        for key in ("creation_date", "date"):
            value = metadata.get(key)
            if value:
                if isinstance(value, datetime):
                    return value
                try:
                    return datetime.fromisoformat(str(value))
                except Exception:  # noqa: BLE001
                    continue
    except Exception:  # noqa: BLE001
        return None
    return None


def _is_reasonable_media_datetime(candidate: datetime, path: Path) -> bool:
    """Reject metadata dates that appear invalid for the file.

    This avoids camera defaults or container timestamps that are newer than the file itself.
    """

    try:
        mtime = datetime.fromtimestamp(path.stat().st_mtime)
    except OSError:
        return True
    now = datetime.now()
    if candidate > now + timedelta(days=1):
        return False
    # If metadata is newer than file mtime by a full day, treat as suspicious.
    if candidate > mtime + timedelta(days=1):
        return False
    return True
