#!/usr/bin/env python3
# Copyright 2026 TELUS Digital
# SPDX-License-Identifier: Apache-2.0
"""Rebuild `docs/packages/spectra.zip` from the `spectra/` folder.

**Maintainer tooling. Not shipped** — `pyproject.toml` lists its packages explicitly, so nothing under
`tools/` reaches a user's machine.

Constitution Principle V requires the published package never to drift from the `spectra/` folder, and
`.github/workflows/ci.yml` enforces it by unzipping and running `diff -r`. Doing the rebuild here
rather than by hand makes it reproducible: entries are written in sorted order with a fixed timestamp,
so rebuilding an unchanged folder produces a byte-identical archive and a no-op diff.

    python tools/build_package.py
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE = REPO_ROOT / "spectra"
TARGET = REPO_ROOT / "docs" / "packages" / "spectra.zip"

# A fixed timestamp keeps the archive byte-identical across rebuilds. Without it every rebuild would
# show as a change even when no file did, which is exactly the noise that makes a drift check useless.
FIXED_TIME = (2026, 1, 1, 0, 0, 0)

# Editor and OS droppings must never reach the published package.
EXCLUDE_NAMES = {".DS_Store", "Thumbs.db"}
EXCLUDE_SUFFIXES = {".pyc", ".swp"}


def sources():
    """Every file to publish, relative to the repository root, in sorted order."""
    found = []
    for path in sorted(SOURCE.rglob("*")):
        if path.is_dir():
            continue
        if path.name in EXCLUDE_NAMES or path.suffix in EXCLUDE_SUFFIXES:
            continue
        found.append(path)
    return found


def build() -> int:
    if not SOURCE.is_dir():
        print(f"error: {SOURCE} does not exist.", file=sys.stderr)
        return 1
    files = sources()
    if not files:
        print(f"error: {SOURCE} contains no files to publish.", file=sys.stderr)
        return 1

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(TARGET, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            relative = path.relative_to(REPO_ROOT).as_posix()
            info = zipfile.ZipInfo(relative, date_time=FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())

    print(f"wrote {TARGET.relative_to(REPO_ROOT)} ({len(files)} files, {TARGET.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(build())
