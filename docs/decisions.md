# Decisions

## Timestamp Strategy
We prefer capture metadata (EXIF for images, container metadata for videos). Video metadata can be unreliable; if it's newer than the file mtime or in the future, it is ignored. For videos without reliable metadata, we prefer mtime over birthtime.

## Duplicate Handling
We avoid overwriting by adding numeric suffixes to destination filenames. We skip a file if the destination name exists and size+mtime match (fast heuristic).

## Resume Behavior
Resume is log-only for simplicity. The latest log is parsed, and only entries with SUCCESS are skipped. The log header must match source/destination to avoid cross-run confusion.

## UI Trees
- Planned Structure tree previews new/existing/skipped directories and files.
- Execution Status tree shows live status for actual planned operations.

## Debug Log
A separate optional debug log captures phase-level details and per-op status to diagnose long scans or failures.
