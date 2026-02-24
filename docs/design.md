# Design

## Goals

- Cross-platform GUI for organizing photos and videos by year and month.
- Simple workflow: pick directories, scan, copy.
- Safe file operations with detailed logs.
- Efficient scanning and responsive UI.

## UX Flow

1. Pick source directory.
2. Pick destination directory.
3. Click `Scan` to build a plan.
4. Review summary and click `Copy`.
5. Watch progress and live log output.

## UI Layout

- Source picker (read-only path + browse button)
- Destination picker (read-only path + browse button)
- Scan / Copy controls
- Status line with summary
- Progress bar
- Live counts: `Files Found (Pics/Videos)` and `Files Copied (Pics/Videos)`
- Planned structure tree with color-coded new vs existing folders and expandable file lists (skipped files in gray), plus status labels and folder/file icons
- Execution status tree with per-item state: pending (purple), success (green), failed (red), existing (black)
- Log output view

## Key Decisions

- **PySide6 (Qt)** for portability and native file dialogs.
- **Background worker threads** to keep the UI responsive.
- **Plan-based execution** so the user can review counts before copying.
- **Timestamped logs** to make each run auditable.
- **Duplicate heuristic** (size+mtime) to skip obvious repeats.
- **On-demand directory creation** to avoid empty folders.

## File Organization

```
src/orgpicsvideos/
  core/          # Core logic (scan, plan, copy)
  ui/            # Qt GUI
```

## Constraints

- Source and destination must not be nested or identical.
- Only files with configured extensions are considered media.
- Creation time is best-effort; fallback to mtime.
