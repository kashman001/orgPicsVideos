"""CLI entrypoint for rebuild."""

from __future__ import annotations

import argparse
from pathlib import Path

from orgpicsvideos.core.logger import make_log_path
from orgpicsvideos.core.rebuild import rebuild_destination


def main() -> None:
    parser = argparse.ArgumentParser(description="Rebuild destination structure in-place.")
    parser.add_argument("destination", type=Path, help="Destination root to rebuild")
    parser.add_argument(
        "--keep-sidecars",
        action="store_true",
        help="Do not delete macOS ._ sidecar files (default is to delete)",
    )
    parser.add_argument(
        "--delete-empty-dirs",
        action="store_true",
        help="Delete empty directories after rebuild",
    )
    args = parser.parse_args()

    destination = args.destination
    if not destination.exists() or not destination.is_dir():
        raise SystemExit(f"Destination is not a directory: {destination}")

    log_path = make_log_path(destination)
    summary = rebuild_destination(
        destination,
        log_path,
        delete_sidecars=not args.keep_sidecars,
        delete_empty_dirs=args.delete_empty_dirs,
    )
    print(
        "Rebuild complete: "
        f"total={summary.total_files} "
        f"moved={summary.moved} "
        f"skipped_same={summary.skipped_same_path} "
        f"skipped_duplicates={summary.skipped_duplicates} "
        f"deleted_empty_dirs={summary.deleted_empty_dirs} "
        f"log={log_path}"
    )


if __name__ == "__main__":
    main()
