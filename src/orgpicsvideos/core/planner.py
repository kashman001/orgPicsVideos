"""Build a copy plan from scanned media files."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .types import (
    MediaFile,
    MediaType,
    OperationType,
    Plan,
    PlannedDirectory,
    PlannedOperation,
    SkipReason,
    SkippedFile,
)
from .utils import is_probable_duplicate, split_media_dirs, unique_path


def build_plan(
    media_files: Iterable[MediaFile],
    destination_root: Path,
    skip_destinations: set[Path] | None = None,
) -> Plan:
    """Create a copy plan for the provided media files."""

    # Copy operations are planned after we compute the target directory and
    # resolve filename collisions. Skipped files are tracked for UI visibility.
    skip_destinations = skip_destinations or set()
    copy_ops: list[PlannedOperation] = []
    mkdirs: set[Path] = set()
    taken_paths: set[Path] = set()
    total_images = 0
    total_videos = 0
    total_files = 0
    total_found = 0
    total_skipped = 0
    skipped_resume = 0
    skipped_duplicates = 0
    # Track skipped files so the UI can render them in the planned tree.
    skipped_files: list[SkippedFile] = []

    for media in media_files:
        total_found += 1
        target_dir = split_media_dirs(destination_root, media.created_at, media.media_type)
        if media.media_type == MediaType.IMAGE:
            total_images += 1
        else:
            total_videos += 1
        if target_dir not in mkdirs:
            mkdirs.add(target_dir)

        base_destination = target_dir / media.path.name
        # Skip files already copied in a prior run (resume mode).
        if base_destination in skip_destinations:
            total_skipped += 1
            skipped_resume += 1
            skipped_files.append(
                SkippedFile(
                    source=media.path,
                    destination=base_destination,
                    reason=SkipReason.RESUME,
                )
            )
            continue
        # Fast duplicate heuristic: if destination exists and matches size+mtime, skip.
        if base_destination.exists() and is_probable_duplicate(media.path, base_destination):
            total_skipped += 1
            skipped_duplicates += 1
            skipped_files.append(
                SkippedFile(
                    source=media.path,
                    destination=base_destination,
                    reason=SkipReason.DUPLICATE,
                )
            )
            continue
        # Ensure a stable unique destination within this plan.
        destination = unique_path(base_destination, taken_paths)
        copy_ops.append(
            PlannedOperation(
                op_type=OperationType.COPY,
                source=media.path,
                destination=destination,
                media_type=media.media_type,
            )
        )
        total_files += 1

    sorted_dirs = sorted(mkdirs)
    mkdir_ops = [
        PlannedOperation(
            op_type=OperationType.MKDIR,
            source=None,
            destination=directory,
        )
        for directory in sorted_dirs
    ]
    planned_dirs = [
        PlannedDirectory(path=directory, exists=directory.exists())
        for directory in sorted_dirs
    ]

    return Plan(
        operations=mkdir_ops + copy_ops,
        directories=planned_dirs,
        skipped_files=skipped_files,
        total_files=total_files,
        total_dirs=len(mkdirs),
        total_images=total_images,
        total_videos=total_videos,
        total_found=total_found,
        total_skipped=total_skipped,
        skipped_resume=skipped_resume,
        skipped_duplicates=skipped_duplicates,
    )
