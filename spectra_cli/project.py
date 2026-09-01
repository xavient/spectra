# Copyright 2026 TELUS Digital
# SPDX-License-Identifier: Apache-2.0

"""Where the project is, and whether Spectra is installed in it.

Every project-scoped command starts here. It answers one question — what state is this folder in? —
and the answer is one of exactly four values, because a user needs a different sentence and a
different remedy for each:

``NOT_A_PROJECT``
    No ancestor directory contains `.specify/`. The remedy is `specify init`.
``NOT_INSTALLED``
    A Spec Kit project, but Spectra's extension folder is absent. The remedy is `spectra install`.
``INCOMPLETE``
    The extension folder exists but carries no readable version — an interrupted or partially
    written install. The remedy is `spectra update`. Reporting this as either "installed" or "absent"
    would be a lie in one direction or the other.
``INSTALLED``
    The extension folder exists and its manifest yields a version.

Discovery walks *up* from the working directory, so every command behaves the same run from a project
root or from a directory nested inside it. That walk reuses the pattern
:func:`spectra_cli.install.check_in_specify_project` already established.
"""

from __future__ import annotations

from pathlib import Path

from spectra_cli import extension

NOT_A_PROJECT = "not_a_project"
NOT_INSTALLED = "not_installed"
INCOMPLETE = "incomplete"
INSTALLED = "installed"

# The directory Spec Kit copies an installed extension into, relative to the project root.
EXTENSION_DIR = Path(".specify") / "extensions" / "spectra"


class ProjectState:
    """The state of one folder, resolved once per command invocation."""

    __slots__ = ("state", "project_root", "installed_version")

    def __init__(self, state: str, project_root=None, installed_version=None):
        self.state = state
        self.project_root = project_root
        self.installed_version = installed_version

    @property
    def is_project(self) -> bool:
        return self.state != NOT_A_PROJECT

    @property
    def is_installed(self) -> bool:
        """True only for a usable install. An `INCOMPLETE` folder is deliberately not installed."""
        return self.state == INSTALLED

    @property
    def extension_dir(self):
        """Where the extension lives, or None outside a project."""
        return None if self.project_root is None else self.project_root / EXTENSION_DIR

    def __repr__(self):  # pragma: no cover - diagnostics only
        return (f"ProjectState({self.state!r}, root={self.project_root!r}, "
                f"version={self.installed_version!r})")


def find_project_root(start=None):
    """The nearest ancestor of `start` containing `.specify/`, or None.

    Checks `start` itself first, then each parent, so running from the root and from a nested
    subdirectory resolve to the same project.
    """
    here = Path(start) if start is not None else Path.cwd()
    here = here.resolve()
    for candidate in [here, *here.parents]:
        if (candidate / ".specify").is_dir():
            return candidate
    return None


def extension_present(project_root, extension_id) -> bool:
    """Whether `extension_id` is installed in this project, by the presence of its folder.

    Answers a narrower question than :func:`classify`, for any extension id rather than Spectra's alone:
    the catalog may advertise several, and the install flow has to decide *per id* whether there is
    anything to install.

    **Asked before the install is attempted, never after it fails.** Spec Kit refuses to install an
    extension that is already present, and a classification taken afterwards cannot tell that refusal
    apart from a download that failed while an older copy sat on disk — both leave the folder there.
    Deciding first removes the ambiguity, and removes any need to match the dependency's message text
    (spec 011 FR-021, research R6).

    A folder with no readable manifest counts as **present** here on purpose. This function reports what is
    on disk; whether it is *usable* is :func:`classify`'s question, and the install flow deliberately treats
    an unusable folder as absent so the add is attempted — see `install.add_catalog`.
    """
    if project_root is None or not extension_id:
        return False
    return (Path(project_root) / ".specify" / "extensions" / extension_id).is_dir()


def classify(start=None) -> ProjectState:
    """Resolve the folder's state. Never raises; an unreadable manifest is a state, not an error."""
    root = find_project_root(start)
    if root is None:
        return ProjectState(NOT_A_PROJECT)

    folder = root / EXTENSION_DIR
    if not folder.is_dir():
        return ProjectState(NOT_INSTALLED, project_root=root)

    version = extension.read_manifest_version(folder / "extension.yml")
    if not version:
        # The folder is here but tells us nothing: a half-written install, not a working one.
        return ProjectState(INCOMPLETE, project_root=root)
    return ProjectState(INSTALLED, project_root=root, installed_version=version)
