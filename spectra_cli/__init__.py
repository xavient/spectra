# Copyright 2026 TELUS Digital
# SPDX-License-Identifier: Apache-2.0

"""Spectra — a curated catalog of Spec Kit extensions for agentic development across the SDLC.

Distributed as a uv tool; the on-PATH command is `spectra`
(entry point: :func:`spectra_cli.cli.main`).

This package is the **CLI channel**. The extensions it installs are the **catalog channel** —
shipped from `catalog.json` on `main` and versioned independently (constitution Principle VI).
"""

from __future__ import annotations

from spectra_cli.version import read_installed_version

__all__ = ["__version__"]

__version__ = read_installed_version() or "unknown"
