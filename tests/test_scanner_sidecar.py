from __future__ import annotations

from pathlib import Path

from orgpicsvideos.core.scanner import scan_media


def test_scanner_ignores_sidecar_files(tmp_path: Path) -> None:
    (tmp_path / "._foo.jpg").write_bytes(b"abc")
    (tmp_path / "bar.jpg").write_bytes(b"abc")

    found = list(scan_media(tmp_path))
    names = {m.path.name for m in found}
    assert "bar.jpg" in names
    assert "._foo.jpg" not in names
