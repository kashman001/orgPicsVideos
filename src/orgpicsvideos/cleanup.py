"""CLI entrypoint to delete files below a size threshold."""

from __future__ import annotations

import argparse
import os
from pathlib import Path


def iter_files(root: Path):
    stack = [root]
    while stack:
        current = stack.pop()
        try:
            with os.scandir(current) as it:
                for entry in it:
                    if entry.is_dir(follow_symlinks=False):
                        stack.append(Path(entry.path))
                    elif entry.is_file(follow_symlinks=False):
                        yield Path(entry.path)
        except PermissionError:
            continue


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Delete files smaller than a threshold (in KB) under a directory tree."
    )
    parser.add_argument("root", type=Path, help="Root directory to scan")
    parser.add_argument(
        "--threshold-kb",
        type=int,
        default=1,
        help="Delete files smaller than this size in KB (default: 1)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show files that would be deleted without deleting them",
    )
    args = parser.parse_args()

    root = args.root
    if not root.exists() or not root.is_dir():
        raise SystemExit(f"Root is not a directory: {root}")

    # Threshold is defined in KB for easy user input; convert to bytes.
    threshold_bytes = args.threshold_kb * 1024
    deleted = 0
    total = 0

    for path in iter_files(root):
        try:
            size = path.stat().st_size
        except OSError:
            continue
        if size < threshold_bytes:
            total += 1
            if args.dry_run:
                print(f"DRY-RUN delete {path} ({size} bytes)")
                continue
            try:
                path.unlink()
                deleted += 1
                print(f"deleted {path} ({size} bytes)")
            except OSError as exc:
                print(f"failed {path} ({size} bytes): {exc}")

    if args.dry_run:
        print(f"Dry-run complete. Candidates: {total}")
    else:
        print(f"Deleted {deleted} files (candidates: {total}).")


if __name__ == "__main__":
    main()
