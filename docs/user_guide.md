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
6. If files were found, click `Copy`.
7. Watch `Files Copied - Pics` / `Videos` update live during copy, along with the progress bar and log output.

## Resume after a failure

If a copy run stops unexpectedly, check `Resume from last run` before scanning. The tool will read the most recent log in the destination directory and skip files that were already copied successfully.

## Logs

A log file is created in the destination directory and named `<timestamp>.log`. Example:

```
SOURCE -> DEST: /path/source -> /path/dest
mkdir /path/dest/2024/jan/pics [SUCCESS]
copy /path/source/img.jpg -> /path/dest/2024/jan/pics/img.jpg [SUCCESS]
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

## Tips

- Large folders can take time to scan; the UI remains responsive while scanning.
- If a filename already exists in the destination, the tool appends a numeric suffix (`_1`, `_2`, ...) to avoid overwriting.
