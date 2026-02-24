from __future__ import annotations

from pathlib import Path

from orgpicsvideos.core.logger import load_successful_destinations


def test_load_successful_destinations(tmp_path: Path) -> None:
    log = tmp_path / "run.log"
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    log.write_text(
        "SOURCE -> DEST: {src} -> {dst}\n"
        "mkdir /tmp/whatever [SUCCESS]\n"
        "copy /a/b.jpg -> {dst}/2002/sep/pics/b.jpg [SUCCESS]\n"
        "copy /a/c.jpg -> {dst}/2002/sep/pics/c.jpg [FAIL] reason=oops\n".format(
            src=src, dst=dst
        ),
        encoding="utf-8",
    )

    results = load_successful_destinations(log, expected_source=src, expected_destination=dst)
    assert (dst / "2002" / "sep" / "pics" / "b.jpg") in results
    assert (dst / "2002" / "sep" / "pics" / "c.jpg") not in results


def test_load_successful_destinations_header_mismatch(tmp_path: Path) -> None:
    log = tmp_path / "run.log"
    log.write_text(
        "SOURCE -> DEST: /other/src -> /other/dst\n"
        "copy /a/b.jpg -> /other/dst/2002/sep/pics/b.jpg [SUCCESS]\n",
        encoding="utf-8",
    )

    results = load_successful_destinations(log, expected_source=tmp_path / "src", expected_destination=tmp_path / "dst")
    assert results == set()
