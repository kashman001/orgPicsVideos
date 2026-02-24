"""Scan directory trees for media files."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Callable, Iterable

from .types import MediaFile
from .utils import detect_media_type, get_creation_time

SKIP_DIR_NAMES = {
    ".Spotlight-V100",
    ".fseventsd",
    ".TemporaryItems",
    "System Volume Information",
}


def scan_media(
    source: Path,
    on_dir: Callable[[str], None] | None = None,
    log_cb: Callable[[str], None] | None = None,
) -> Iterable[MediaFile]:
    """Yield media files under the source directory."""

    # Use an explicit stack to avoid recursion limits on deep trees.
    stack = [source]
    while stack:
        current = stack.pop()
        if on_dir:
            on_dir(f"Current Dir - {current} (entries: 0)")
        entries_seen = 0
        try:
            if log_cb:
                log_cb(f"scandir_start path={current}")
            with os.scandir(current) as it:
                for entry in it:
                    entries_seen += 1
                    # Throttle UI updates to keep scanning fast on large folders.
                    if on_dir and entries_seen % 200 == 0:
                        on_dir(f"Current Dir - {current} (entries: {entries_seen})")
                    if entry.is_dir(follow_symlinks=False):
                        if entry.name in SKIP_DIR_NAMES:
                            # Skip common system folders on external drives.
                            continue
                        stack.append(Path(entry.path))
                    elif entry.is_file(follow_symlinks=False):
                        path = Path(entry.path)
                        if path.name.startswith("._"):
                            continue
                        media_type = detect_media_type(path)
                        if not media_type:
                            continue
                        created_at = get_creation_time(path, media_type)
                        yield MediaFile(path=path, created_at=created_at, media_type=media_type)
            if on_dir:
                on_dir(f"Current Dir - {current} (entries: {entries_seen})")
            if log_cb:
                log_cb(f"scandir_end path={current} entries={entries_seen}")
        except PermissionError:
            if log_cb:
                log_cb(f"scandir_error path={current} error=PermissionError")
            # Skip unreadable directories.
            continue
