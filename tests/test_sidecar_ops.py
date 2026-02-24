from __future__ import annotations

from pathlib import Path

from orgpicsvideos.core.rebuild import build_sidecar_delete_ops


def test_build_sidecar_delete_ops(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    sidecar = root / "._junk.MOV"
    sidecar.write_text("x", encoding="utf-8")

    ops = build_sidecar_delete_ops(root)
    assert any(op.destination == sidecar for op in ops)
