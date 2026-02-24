# User Guide

## Overview

OrgPicsVideos is a desktop GUI tool that scans a source directory for photos and videos, then copies them into a clean, organized structure under a destination directory:

```
<dest>/<year>/<month>/pics/<file>
<dest>/<year>/<month>/videos/<file>
```

It validates that source and destination are separate and not nested, creates folders only when needed, and logs each operation.

## Install

Requirements:
- Python 3.10+
- PySide6

Install in editable mode:

```
pip install -e .
```

## Run

```
orgpicsvideos
```

## Step-by-step

1. Click `Browse Source` and select the folder containing your photos/videos. The source must already exist.
2. Click `Browse Destination` and select a separate folder where organized files should be copied. You can create a new folder from the dialog if needed.
3. Click `Scan`. The status line shows `Scanning...` and the next line shows `Current Dir - <path> (entries: N)` as it walks.
4. Review the summary line (total files, images, videos, directories).
5. Watch `Files Found - Pics` / `Videos` update live during scan.
6. Review the planned destination structure tree; new folders are blue, existing folders are black, and skipped files are gray. Labels also show status (existing/new/skipped), and folder/file icons help distinguish types. Expand a leaf folder to see the files that will be copied there. Double-click a file to open it.
7. Review the execution status tree; items that already exist show as black (existing). Items pending execution start as purple, turn orange when partially complete, then green on success or red on failure as the copy runs. Double-click a file to open it (source if not copied yet).
8. If files were found, click `Copy`.
9. Watch `Files Copied - Pics` / `Videos` update live during copy, along with the progress bar, execution status tree, and log output.

By default the tool deletes macOS `._` sidecar files in the destination during copy. Check `Keep macOS ._ sidecar files` to disable this.

## Resume after a failure

If a copy run stops unexpectedly, check `Resume from last run` before scanning. The tool will read the most recent log in the destination directory and skip files that were already copied successfully.

## Rebuild Tool

If you need to re-normalize an existing destination structure (e.g., after changing timestamp logic), you can run:

```
orgpicsvideos-rebuild /path/to/destination
```

This rebuilds the structure in-place by moving files into their correct year/month folders based on current timestamp rules. By default it deletes macOS `._` sidecar files; use `--keep-sidecars` to keep them. Use `--delete-empty-dirs` to remove empty folders after rebuild (folders containing only `.DS_Store`/`._*` are treated as empty).

## Cleanup Tool

To delete files smaller than a size threshold (default 1KB):

```
orgpicsvideos-cleanup /path/to/root --threshold-kb 1
```

Use `--dry-run` to preview deletions.

## Logs

A log file is created in the destination directory and named `<timestamp>.log`. Example:

```
SOURCE -> DEST: /path/source -> /path/dest
SCAN SUMMARY: found=12 images=8 videos=4 to_copy=11 skipped=1 dirs=6
RESUME: enabled=yes skipped_resume=1 skipped_duplicates=0
Scan duration: 00:00:12
mkdir /path/dest/2024/jan/pics [SUCCESS]
copy /path/source/img.jpg -> /path/dest/2024/jan/pics/img.jpg [SUCCESS]
Copy duration: 00:00:05
```

Each line is either a directory creation or a copy operation with a success/fail result and an error reason when applicable.

## File Types

Images:
- jpg, jpeg, png, gif, bmp, tif, tiff, heic, heif, webp, raw

Videos:
- mp4, mov, avi, mkv, m4v, wmv, flv, webm, mpeg, mpg, 3gp

## Common issues

- **Source equals destination**: choose two different directories.
- **Nested folders**: destination cannot be inside source, and source cannot be inside destination.
- **No files found**: check file types and ensure you selected the correct source directory.
- **Slow external drive scan**: enable `Enable debug log` to write `debug_<timestamp>.log` in the destination and identify where scans slow down.
- **macOS sidecar files**: files starting with `._` are ignored by the scanner and won’t create folders on their own.

## Tips

- Large folders can take time to scan; the UI remains responsive while scanning.
- If a filename already exists in the destination, the tool appends a numeric suffix (`_1`, `_2`, ...) to avoid overwriting.
- If a destination file with the same name matches size+mtime, the tool skips it as a duplicate.
- File organization prefers capture time (EXIF for images, container metadata for videos). If video metadata looks suspicious (newer than file mtime or in the future), it is ignored. For images without EXIF and videos without reliable metadata, modification time is preferred over birthtime on Unix-like systems.
 
## Timestamp Notes

The tool uses the media's capture time when available. For images, it reads EXIF capture timestamps. For videos, it reads container metadata but ignores it if it appears unreliable (e.g., newer than the file). When capture metadata is missing or unreliable, it falls back to file system timestamps, preferring modification time for videos on Unix-like systems.
