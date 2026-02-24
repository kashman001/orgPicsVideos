"""Shared types for scanning and organizing media."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Iterable


class MediaType(str, Enum):
    """Media category used for organizing files."""

    IMAGE = "image"
    VIDEO = "video"


IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".tif",
    ".tiff",
    ".heic",
    ".heif",
    ".webp",
    ".raw",
}

VIDEO_EXTENSIONS = {
    ".mp4",
    ".mov",
    ".avi",
    ".mkv",
    ".m4v",
    ".wmv",
    ".flv",
    ".webm",
    ".mpeg",
    ".mpg",
    ".3gp",
}


@dataclass(frozen=True)
class MediaFile:
    """Represents a discovered media file."""

    path: Path
    created_at: datetime
    media_type: MediaType


class OperationType(str, Enum):
    """Operation types written to the log."""

    MKDIR = "mkdir"
    COPY = "copy"


@dataclass(frozen=True)
class PlannedOperation:
    """An operation to run during copy."""

    op_type: OperationType
    source: Path | None
    destination: Path
    media_type: MediaType | None = None


@dataclass(frozen=True)
class PlannedDirectory:
    """A directory that may be created during copy."""

    path: Path
    exists: bool


class SkipReason(str, Enum):
    """Reason a file was skipped during planning."""

    RESUME = "resume"
    DUPLICATE = "duplicate"


@dataclass(frozen=True)
class SkippedFile:
    """A file skipped during planning with a reason."""

    source: Path
    destination: Path
    reason: SkipReason


@dataclass
class Plan:
    """Planned operations and summary counts."""

    operations: list[PlannedOperation]
    directories: list[PlannedDirectory]
    skipped_files: list[SkippedFile]
    total_files: int
    total_dirs: int
    total_images: int
    total_videos: int
    total_found: int
    total_skipped: int
    skipped_resume: int
    skipped_duplicates: int
    scan_duration_seconds: float = 0.0
    resume_enabled: bool = False

    def iter_ops(self) -> Iterable[PlannedOperation]:
        return iter(self.operations)
