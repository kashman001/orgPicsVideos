# Contributing

## Setup
```
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Run
```
orgpicsvideos
```

## Debugging
- Enable **Enable debug log** in the UI to write `debug_<timestamp>.log` under the destination root.
- On macOS, external drives may require Terminal Full Disk Access or Removable Volumes permission.

## Quick Test Plan
1. Scan a small folder on internal storage.
2. Copy into an empty destination.
3. Re-run with **Resume from last run** to verify skips.
4. Place a file with the same name and size+mtime in destination and verify it’s skipped.
5. Check the planned structure and execution status trees.
