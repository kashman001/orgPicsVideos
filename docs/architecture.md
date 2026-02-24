# Architecture

## Overview

The system is a desktop GUI application with a small core library that handles validation, scanning, planning, copying, and logging. The GUI is intentionally thin: it gathers user input, triggers background workers, and displays progress and logs.

## Modules

- `orgpicsvideos.core.validator`
  - Validates source/destination directories and enforces non-nesting constraints.
- `orgpicsvideos.core.scanner`
  - Recursively scans the source tree for media files based on file extensions.
- `orgpicsvideos.core.planner`
  - Converts scanned media into a `Plan` consisting of directory creation and file copy operations.
- `orgpicsvideos.core.copier`
  - Executes the plan and reports progress; produces log lines for each operation.
- `orgpicsvideos.core.logger`
  - Writes a timestamped log file with a header and per-operation results.
- `orgpicsvideos.ui.app`
  - Qt GUI that runs the scan and copy operations in background threads.

## Data Flow

1. User selects `source` and `destination` directories.
2. UI validates paths via `validate_paths`.
3. UI starts `ScanWorker` to run `scan_media` and `build_plan`.
   The scan emits live counts of images and videos found.
4. UI presents scan summary and enables copy if applicable.
5. UI starts `CopyWorker` to run `execute_plan` and emit progress/log updates plus live copy counts.
6. `LogWriter` writes the header and each operation line to `<timestamp>.log`.

## Concurrency

All scanning and copying occurs in `QThread` workers to keep the UI responsive. The main thread updates UI widgets in response to signals from the workers.

## Error Handling

- Validation errors are shown to the user before any scan.
- Scan or copy exceptions are caught in workers and displayed as message dialogs.
- File system errors during operations are logged as `[FAIL]` with a reason.

## Extensibility

- Extension sets in `core.types` can be expanded.
- Conflict strategy is centralized in `core.utils.unique_path`.
- Alternative metadata sources (e.g., EXIF) can be integrated in `core.utils.get_creation_time`.
