"""Validation helpers for source/destination directories."""

from __future__ import annotations

from pathlib import Path

from .utils import is_under


class ValidationError(Exception):
    """Raised when user input fails validation."""


def validate_paths(source: Path, destination: Path) -> None:
    """Validate source and destination directories are acceptable."""

    if not source.exists() or not source.is_dir():
        raise ValidationError(f"Source is not a directory: {source}")
    if destination.exists() and not destination.is_dir():
        raise ValidationError(f"Destination is not a directory: {destination}")

    source_resolved = source.resolve()
    destination_resolved = destination.resolve(strict=False)

    if source_resolved == destination_resolved:
        raise ValidationError("Source and destination must be different directories.")

    if is_under(source_resolved, destination_resolved):
        raise ValidationError("Source cannot be inside destination directory.")

    if is_under(destination_resolved, source_resolved):
        raise ValidationError("Destination cannot be inside source directory.")
