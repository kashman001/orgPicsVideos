from __future__ import annotations

from pathlib import Path

from orgpicsvideos.core.copier import execute_plan
from orgpicsvideos.core.types import OperationType, PlannedOperation


def test_execute_plan_creates_and_copies(tmp_path: Path) -> None:
    src = tmp_path / "src.jpg"
    src.write_bytes(b"abc")
    dest_dir = tmp_path / "dest" / "2002" / "sep" / "pics"
    dest_file = dest_dir / "src.jpg"

    ops = [
        PlannedOperation(op_type=OperationType.MKDIR, source=None, destination=dest_dir),
        PlannedOperation(op_type=OperationType.COPY, source=src, destination=dest_file),
    ]

    logs: list[str] = []
    execute_plan(ops, logs.append)

    assert dest_dir.exists()
    assert dest_file.exists()
    assert any("mkdir" in line for line in logs)
    assert any("copy" in line for line in logs)
