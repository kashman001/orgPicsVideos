# OrgPicsVideos

Cross-platform GUI tool that scans a source directory for photos and videos and copies them into an organized destination structure:

```
<dest>/<year>/<month>/pics/<file>
<dest>/<year>/<month>/videos/<file>
```

The tool validates that the source and destination directories are distinct and not nested. It creates directories only when there is content and writes a timestamped log of all operations.

## Requirements

- Python 3.10+
- PySide6

## Install

```
pip install -e .
```

## Run

```
orgpicsvideos
```

## User Guide

See `docs/user_guide.md` for the full user guide.

## Overview

See `docs/overview.md` for a concise system overview and flow.

## Tests

Install test dependencies:

```
pip install -e .[test]
```

Run tests:

```
pytest
```

Make targets:

```
make test-unit
make test-ui
```

See `docs/test_coverage.md` for coverage notes and gaps.
## Log format

A log file named `<timestamp>.log` is written under the destination directory. The first line states the source and destination, followed by one line per directory creation or copy operation:

```
SOURCE -> DEST: /path/source -> /path/dest
mkdir /path/dest/2024/jan/pics [SUCCESS]
copy /path/source/img.jpg -> /path/dest/2024/jan/pics/img.jpg [SUCCESS]
```

## Notes

- File timestamps prefer media capture time (EXIF for images, container metadata for videos). If video metadata looks suspicious (newer than file mtime or in the future), it is ignored. For videos without reliable metadata, modification time is preferred over birthtime. If unavailable, best-effort creation time is used; on Unix-like systems this falls back to modification time.
- Filename collisions are resolved by appending a numeric suffix (`_1`, `_2`, ...).
