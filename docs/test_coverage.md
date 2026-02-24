# Test Coverage

## Covered
- Path validation (nested, identical, missing).
- Planning logic: counts, directory layout, resume skips, duplicate skips.
- Timestamp parsing for images via EXIF.
- Video metadata heuristics (reasonable vs suspicious fallback).
- Duplicate heuristic (size+mtime).
- Copy execution: mkdir + copy operations and logging.
- Resume log parsing.
- UI tree population for planned and execution trees (model-level, headless).

## Remaining Gaps
- True end-to-end GUI interactions (manual smoke tests recommended).
- Large-scale performance on external drives.
- Full cross-platform filesystem timestamp quirks (manual or OS-specific CI).

## Suggested Next Steps
- Add optional Qt smoke tests using pytest-qt for UI interactions.
- Add a large synthetic fixture set for performance profiling (not for CI).
- Extend CI matrix to include macOS and Windows runners.

## UI Tests
- UI tests are marked with `@pytest.mark.ui` and run separately in CI.
