"""Utility helpers for filesystem and date handling."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable

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


def get_creation_time(path: Path) -> datetime:
    """Return a best-effort creation timestamp for a file."""

    stat = path.stat()
    if hasattr(stat, "st_birthtime"):
        return datetime.fromtimestamp(stat.st_birthtime)
    # On Windows st_ctime is creation time; on Unix it's metadata change time.
    if stat.st_ctime:
        return datetime.fromtimestamp(stat.st_ctime)
    return datetime.fromtimestamp(stat.st_mtime)


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


def split_media_dirs(destination_root: Path, dt: datetime, media_type: MediaType) -> Path:
    """Return destination directory for a media item."""

    year = str(dt.year)
    month = month_name(dt)
    leaf = "pics" if media_type == MediaType.IMAGE else "videos"
    return destination_root / year / month / leaf
