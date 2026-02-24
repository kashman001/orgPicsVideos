# Overview

## Purpose
OrgPicsVideos is a cross-platform GUI tool that scans a source directory for photos and videos and copies them into a normalized destination structure organized by year/month and media type.

## Core Flow
1. **Validate** source/destination (distinct, non-nested).
2. **Scan** source tree for media files by extension.
3. **Plan** destination paths, resolve name collisions, identify skips.
4. **Preview** planned structure (new/existing/skipped) and execution plan.
5. **Copy** files and create directories, logging every operation.

## Destination Layout
```
<dest>/<year>/<month>/pics/<file>
<dest>/<year>/<month>/videos/<file>
```

## Timestamps
- Prefer media capture time (EXIF for images, container metadata for videos).
- Video metadata is ignored if it appears unreliable (newer than file mtime or in the future).
- If metadata is missing/unreliable, fallback to filesystem timestamps (mtime preferred for videos).

## Duplicate Handling
- If destination name exists, add `_1`, `_2`, ...
- If destination file exists and matches size+mtime, skip as duplicate.

## Resume
Resume is log-based: the latest log is parsed and previously successful copies are skipped when resume is enabled.

## UI Panels
- **Planned Structure** tree: preview directories and files (existing/new/skipped).
- **Execution Status** tree: live copy status (pending/success/failed/existing).

## Logs
- User log: `<timestamp>.log` in destination root.
- Debug log: `debug_<timestamp>.log` in destination root (optional).

## Rebuild Tool
Use `orgpicsvideos-rebuild <destination>` to normalize an existing destination in-place using current timestamp rules. Optional `--delete-empty-dirs` removes empty directories after rebuild.

## Cleanup Tool
Use `orgpicsvideos-cleanup <root> --threshold-kb N` to delete files smaller than a size threshold (default 1KB), useful for removing tiny web assets such as buttons/icons.
