"""Log file writer for copy operations."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TextIO


class LogWriter:
    """Write structured logs for operations."""

    def __init__(self, log_file: Path, source: Path, destination: Path) -> None:
        self.log_file = log_file
        self.source = source
        self.destination = destination
        self._handle: TextIO | None = None

    def __enter__(self) -> "LogWriter":
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self._handle = self.log_file.open("w", encoding="utf-8")
        self._handle.write(f"SOURCE -> DEST: {self.source} -> {self.destination}\n")
        self._handle.flush()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        if self._handle:
            self._handle.flush()
            self._handle.close()
            self._handle = None

    def write(self, line: str) -> None:
        if not self._handle:
            raise RuntimeError("LogWriter not opened")
        self._handle.write(line + "\n")
        self._handle.flush()


def make_log_path(destination_root: Path) -> Path:
    """Return a log file path using timestamp format."""

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return destination_root / f"{stamp}.log"


def find_latest_log(destination_root: Path) -> Path | None:
    """Return the newest log file in the destination root."""

    if not destination_root.exists():
        return None
    logs = sorted(destination_root.glob("*.log"))
    if not logs:
        return None
    return logs[-1]


def load_successful_destinations(
    log_path: Path,
    expected_source: Path | None = None,
    expected_destination: Path | None = None,
) -> set[Path]:
    """Parse a log file and return destination paths with SUCCESS status."""

    # Resume is based on the most recent log; only trust logs that match the
    # current source and destination header to avoid cross-run confusion.
    destinations: set[Path] = set()
    try:
        with log_path.open("r", encoding="utf-8") as handle:
            header = handle.readline().strip()
            if header.startswith("SOURCE -> DEST: "):
                payload = header[len("SOURCE -> DEST: ") :]
                if " -> " in payload:
                    src_text, dest_text = payload.rsplit(" -> ", 1)
                    if expected_source and Path(src_text).resolve(strict=False) != expected_source.resolve(strict=False):
                        return set()
                    if expected_destination and Path(dest_text).resolve(strict=False) != expected_destination.resolve(
                        strict=False
                    ):
                        return set()
            for line in handle:
                line = line.strip()
                if not line.startswith("copy "):
                    continue
                if not line.endswith(" [SUCCESS]"):
                    continue
                payload = line[len("copy ") : -len(" [SUCCESS]")]
                if " -> " not in payload:
                    continue
                _src, dest = payload.split(" -> ", 1)
                destinations.add(Path(dest))
    except OSError:
        return set()

    return destinations
