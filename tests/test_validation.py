from pathlib import Path

import pytest

from orgpicsvideos.core.validator import ValidationError, validate_paths


def test_validate_paths_ok(tmp_path: Path) -> None:
    source = tmp_path / "source"
    dest = tmp_path / "dest"
    source.mkdir()
    dest.mkdir()
    validate_paths(source, dest)


def test_validate_paths_same_dir(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    with pytest.raises(ValidationError):
        validate_paths(source, source)


def test_validate_paths_nested(tmp_path: Path) -> None:
    source = tmp_path / "source"
    dest = source / "dest"
    source.mkdir()
    dest.mkdir()
    with pytest.raises(ValidationError):
        validate_paths(source, dest)

    with pytest.raises(ValidationError):
        validate_paths(dest, source)
