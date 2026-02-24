# OrgPicsVideos Requirements

Create a cross-platform GUI tool that scans a source directory for photos/videos
and copies them into an organized destination structure.

## 1) Validation
- Source must exist and be a directory.
- Destination may not exist; if missing it will be created.
- Source and destination must be different and not nested inside each other.

## 2) Destination Layout
```
<dest>/<year>/<month>/pics/<file>
<dest>/<year>/<month>/videos/<file>
```
- Create directories only when needed (no empty year/month folders).

## 3) File Detection
- Image extensions: jpg, jpeg, png, gif, bmp, tif, tiff, heic, heif, webp, raw
- Video extensions: mp4, mov, avi, mkv, m4v, wmv, flv, webm, mpeg, mpg, 3gp

## 4) Timestamp Rules
- Prefer media capture time (EXIF for images, container metadata for videos).
- If video metadata is suspicious (newer than file mtime or in the future), ignore it.
- If video metadata is missing or ignored, prefer file modification time over birthtime.
- Fallback order for other cases: birthtime -> mtime (Unix) or birthtime -> ctime (Windows).

## 5) Copy Behavior
- Copy files, do not move/delete.
- Preserve metadata (copy2).
- If destination filename exists, append _1, _2, ... to avoid overwriting.
- If a destination file with the same name exists and matches size+mtime, skip as a duplicate.

## 6) Logging
- Log file name: <timestamp>.log in the destination root.
- First line: SOURCE -> DEST: <source> -> <destination>
- Include scan summary (found/images/videos/to_copy/skipped/dirs), resume status, and durations.
- Each operation line: mkdir or copy operation with SUCCESS/FAIL and failure reason.

## 7) Resume After Failure (Log-Only)
- UI option: "Resume from last run".
- When enabled, read the most recent log in destination and skip files already copied successfully.
- Skip only if log header matches source/destination; verify destination exists.

## 8) UI/Progress
- Folder picker for source (must exist) and destination (allow creation).
- Status line shows "Scanning..." and a separate line shows current directory with entry count.
- Live counts during scan: "Files Found - Pics: X, Videos: Y".
- Live counts during copy: "Files Copied - Pics: X, Videos: Y".
- Planned destination structure tree rooted at destination.
  - Color coding: Black = existing, Blue = new, Gray = skipped files.
  - Labels show status; folder/file icons distinguish types.
  - Expanding a leaf folder shows the files that would be copied there.
- Execution status tree rooted at destination.
  - Existing directories shown as Black = existing.
  - Pending items shown as Purple = pending.
  - Updates to Green = success, Red = failed.
  - Labels show status; folder/file icons distinguish types.
- Progress bar for scan and copy phases.
- Optional Debug Log toggle.

## 9) Debug Log (Optional)
- When enabled, write `debug_<timestamp>.log` in destination.
- Capture major phases: validation, resume, scan, plan, copy.
- Include scan directory progress, copy operation summaries, and phase durations.

## 10) Performance
- Scanning runs in a background thread and should not block the UI.

## 11) macOS Permissions
- External drives may require granting Terminal (or the launcher) access in Privacy & Security
  under Removable Volumes or Full Disk Access.
