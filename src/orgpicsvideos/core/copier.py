"""Execute copy plans and report progress."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Callable, Iterable

from .types import OperationType, PlannedOperation


LogCallback = Callable[[str], None]
ProgressCallback = Callable[[int, int], None]
OpCallback = Callable[[PlannedOperation, bool], None]


def execute_plan(
    operations: Iterable[PlannedOperation],
    log_cb: LogCallback,
    progress_cb: ProgressCallback | None = None,
    op_cb: OpCallback | None = None,
) -> None:
    """Execute a plan, logging results for each operation."""

    ops = list(operations)
    total = len(ops)
    for index, op in enumerate(ops, start=1):
        success = True
        reason = ""
        try:
            if op.op_type == OperationType.MKDIR:
                op.destination.mkdir(parents=True, exist_ok=True)
            elif op.op_type == OperationType.COPY:
                if op.source is None:
                    raise RuntimeError("Missing source for copy operation")
                op.destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(op.source, op.destination)
            elif op.op_type == OperationType.MOVE:
                if op.source is None:
                    raise RuntimeError("Missing source for move operation")
                op.destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(op.source, op.destination)
            elif op.op_type == OperationType.DELETE:
                if op.destination.exists():
                    op.destination.unlink()
            else:
                raise RuntimeError(f"Unsupported operation: {op.op_type}")
        except Exception as exc:  # noqa: BLE001
            success = False
            reason = str(exc)

        log_line = _format_log_line(op, success, reason)
        log_cb(log_line)
        if op_cb:
            op_cb(op, success)
        if progress_cb:
            progress_cb(index, total)


def _format_log_line(op: PlannedOperation, success: bool, reason: str) -> str:
    status = "SUCCESS" if success else "FAIL"
    if op.op_type == OperationType.MKDIR:
        detail = f"mkdir {op.destination}"
    elif op.op_type == OperationType.MOVE:
        detail = f"move {op.source} -> {op.destination}"
    elif op.op_type == OperationType.DELETE:
        detail = f"delete {op.destination}"
    else:
        detail = f"copy {op.source} -> {op.destination}"
    if success:
        return f"{detail} [{status}]"
    return f"{detail} [{status}] reason={reason}"
