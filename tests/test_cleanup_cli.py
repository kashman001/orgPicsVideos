from __future__ import annotations

from pathlib import Path

from orgpicsvideos.cleanup import main as cleanup_main


def test_cleanup_dry_run(tmp_path: Path, capsys) -> None:
    root = tmp_path / "root"
    root.mkdir()
    small = root / "small.bin"
    big = root / "big.bin"
    small.write_bytes(b"x")
    big.write_bytes(b"x" * 5000)

    # Simulate CLI args.
    import sys
    argv = sys.argv
    sys.argv = ["cleanup", str(root), "--threshold-kb", "1", "--dry-run"]
    try:
        cleanup_main()
    finally:
        sys.argv = argv

    out = capsys.readouterr().out
    assert "DRY-RUN" in out
    assert small.exists()
    assert big.exists()


def test_cleanup_delete(tmp_path: Path, capsys) -> None:
    root = tmp_path / "root"
    root.mkdir()
    small = root / "small.bin"
    big = root / "big.bin"
    small.write_bytes(b"x")
    big.write_bytes(b"x" * 5000)

    import sys
    argv = sys.argv
    sys.argv = ["cleanup", str(root), "--threshold-kb", "1"]
    try:
        cleanup_main()
    finally:
        sys.argv = argv

    out = capsys.readouterr().out
    assert "deleted" in out
    assert not small.exists()
    assert big.exists()
