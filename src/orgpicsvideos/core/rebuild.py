"""Rebuild destination structure in-place based on media timestamps."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Iterable

from .copier import execute_plan
from .logger import LogWriter
from .scanner import scan_media
from .types import OperationType, PlannedOperation
from .utils import is_probable_duplicate, split_media_dirs, unique_path


@dataclass
class RebuildSummary:
    moved: int
    skipped_same_path: int
    skipped_duplicates: int
    total_files: int
    deleted_empty_dirs: int


def build_sidecar_delete_ops(destination_root: Path) -> list[PlannedOperation]:
    return [
        PlannedOperation(op_type=OperationType.DELETE, source=None, destination=sidecar)
        for sidecar in destination_root.rglob("._*")
    ]


def build_rebuild_operations(
    destination_root: Path,
    delete_sidecars: bool = True,
) -> tuple[list[PlannedOperation], RebuildSummary]:
    """Scan destination and build move operations to normalize structure."""

    ops: list[PlannedOperation] = []
    mkdirs: set[Path] = set()
    taken_paths: set[Path] = set()
    moved = 0
    skipped_same = 0
    skipped_dupe = 0
    total = 0

    for media in scan_media(destination_root):
        total += 1
        target_dir = split_media_dirs(destination_root, media.created_at, media.media_type)
        mkdirs.add(target_dir)

        target = target_dir / media.path.name
        if target.resolve() == media.path.resolve():
            skipped_same += 1
            continue
        if target.exists() and is_probable_duplicate(media.path, target):
            skipped_dupe += 1
            continue

        target = unique_path(target, taken_paths)
        ops.append(
            PlannedOperation(
                op_type=OperationType.MOVE,
                source=media.path,
                destination=target,
                media_type=media.media_type,
            )
        )
        moved += 1

    if delete_sidecars:
        ops.extend(build_sidecar_delete_ops(destination_root))

    mkdir_ops = [
        PlannedOperation(op_type=OperationType.MKDIR, source=None, destination=path)
        for path in sorted(mkdirs)
    ]
    return (
        mkdir_ops + ops,
        RebuildSummary(moved, skipped_same, skipped_dupe, total, deleted_empty_dirs=0),
    )


def rebuild_destination(
    destination_root: Path,
    log_path: Path,
    delete_sidecars: bool = True,
    delete_empty_dirs: bool = False,
) -> RebuildSummary:
    """Rebuild destination in-place and log operations.

    Optionally removes empty directories after moves.
    """

    ops, summary = build_rebuild_operations(destination_root, delete_sidecars=delete_sidecars)
    with LogWriter(log_path, destination_root, destination_root) as writer:
        writer.write(
            "REBUILD SUMMARY: "
            f"total={summary.total_files} "
            f"moved={summary.moved} "
            f"skipped_same={summary.skipped_same_path} "
            f"skipped_duplicates={summary.skipped_duplicates}"
        )
        execute_plan(ops, writer.write)
        if delete_empty_dirs:
            summary.deleted_empty_dirs = _delete_empty_dirs(destination_root, writer.write)
    return summary


def _delete_empty_dirs(destination_root: Path, log_cb) -> int:  # type: ignore[no-untyped-def]
    deleted = 0
    # Walk bottom-up so children are removed before parents.
    for root, dirs, files in os.walk(destination_root, topdown=False):
        if root == str(destination_root):
            continue
        # Treat macOS metadata files as ignorable for emptiness checks.
        ignorable = {".DS_Store"}
        path = Path(root)
        # Re-evaluate directory contents to avoid stale os.walk state.
        try:
            entries = list(path.iterdir())
        except Exception:  # noqa: BLE001
            continue
        real_files = [
            p for p in entries if p.is_file() and p.name not in ignorable and not p.name.startswith("._")
        ]
        real_dirs = [p for p in entries if p.is_dir()]
        if real_files or real_dirs:
            continue
        # Remove ignorable files so the directory can be deleted.
        for p in entries:
            if p.is_file() and (p.name in ignorable or p.name.startswith("._")):
                try:
                    p.unlink()
                except Exception:  # noqa: BLE001
                    pass
        try:
            path.rmdir()
            deleted += 1
            log_cb(f"rmdir {path} [SUCCESS]")
        except Exception as exc:  # noqa: BLE001
            log_cb(f"rmdir {path} [FAIL] reason={exc}")
    return deleted
