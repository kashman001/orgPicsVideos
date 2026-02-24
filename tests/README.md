# Testing Notes

## Current Coverage
- Validation, planning, resume parsing, and duplicate heuristics.
- Image EXIF timestamp parsing.
- Video metadata heuristics (reasonable vs suspicious fallback).
- Copy execution behavior (mkdir/copy log).
- Planned/execution tree population (headless UI).
- Optional GUI smoke test via pytest-qt.

## Current Gaps
- Full end-to-end GUI interaction coverage (only a basic smoke test).
- Large-scale performance on external drives.
- OS-specific filesystem timestamp differences.

## Running Tests
```
pip install -e .[test]
pytest
```

## Optional UI Smoke Tests
```
pip install pytest-qt
pytest -k ui_smoke
```
