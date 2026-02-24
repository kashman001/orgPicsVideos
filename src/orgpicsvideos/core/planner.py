"""Build a copy plan from scanned media files."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .types import MediaFile, MediaType, OperationType, Plan, PlannedOperation
from .utils import split_media_dirs, unique_path


def build_plan(
    media_files: Iterable[MediaFile],
    destination_root: Path,
    skip_destinations: set[Path] | None = None,
) -> Plan:
    """Create a copy plan for the provided media files."""

    skip_destinations = skip_destinations or set()
    copy_ops: list[PlannedOperation] = []
    mkdirs: set[Path] = set()
    taken_paths: set[Path] = set()
    total_images = 0
    total_videos = 0
    total_files = 0
    total_found = 0
    total_skipped = 0

    for media in media_files:
        total_found += 1
        target_dir = split_media_dirs(destination_root, media.created_at, media.media_type)
        if media.media_type == MediaType.IMAGE:
            total_images += 1
        else:
            total_videos += 1
        if target_dir not in mkdirs:
            mkdirs.add(target_dir)

        destination = unique_path(target_dir / media.path.name, taken_paths)
        if destination in skip_destinations:
            total_skipped += 1
            continue
        copy_ops.append(
            PlannedOperation(
                op_type=OperationType.COPY,
                source=media.path,
                destination=destination,
                media_type=media.media_type,
            )
        )
        total_files += 1

    mkdir_ops = [
        PlannedOperation(
            op_type=OperationType.MKDIR,
            source=None,
            destination=directory,
        )
        for directory in sorted(mkdirs)
    ]

    return Plan(
        operations=mkdir_ops + copy_ops,
        total_files=total_files,
        total_dirs=len(mkdirs),
        total_images=total_images,
        total_videos=total_videos,
        total_found=total_found,
        total_skipped=total_skipped,
    )
