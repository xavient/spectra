"""Shared fixtures for the Spectra CLI test suite.

Standard library only, like everything else in this repository — `unittest` rather than pytest, and
nothing here imports `spectra_cli`, so these helpers stay usable while the modules they support are
still being written.

Three kinds of fixture:

* **Projects** — `temp_project()` builds a throwaway Spec Kit project in each of the four states the
  CLI classifies, so tests never touch the developer's real tree.
* **Rosters** — `roster()` returns a valid roster dict that a test mutates to express the one thing it
  cares about, instead of restating all 44 published entries.
* **Servers** — `serve()` publishes files over loopback HTTP so the network paths can be exercised
  through `SPECTRA_RAW_BASE` without publishing anything, and `UNREACHABLE_BASE` covers the failure
  side.
"""

from __future__ import annotations

import contextlib
import copy
import http.server
import json
import os
import tempfile
import threading
from pathlib import Path

# Port 9 is the discard service and is closed on a normal machine, so a connection here fails fast
# and deterministically on macOS, Linux, and Windows alike. Used for the "published data
# unreachable" paths rather than a real timeout, which would make the suite slow.
UNREACHABLE_BASE = "http://127.0.0.1:9"

# The line every published copy of the extension description must carry (FR-051).
DESCRIPTION = "TELUS Digital - Agentic software engineering across the entire SDLC."


# --------------------------------------------------------------------------- #
# Manifests
# --------------------------------------------------------------------------- #

def manifest_yaml(version: str = "1.3.1", *, commands=("adr", "domain-analyzer", "create-pr", "brd")) -> str:
    """An extension manifest with the shape the version scanner relies on.

    Deliberately reproduces the real indentation — `  version: "X.Y.Z"` two spaces deep inside the
    `extension:` block — because that exact shape is what `spectra_cli/extension.py` and
    `.github/workflows/ci.yml` both scan for. A fixture that "looked close enough" would let a
    broken scanner pass.
    """
    lines = [
        'schema_version: "1.0"',
        "",
        "extension:",
        '  id: "spectra"',
        '  name: "Spectra"',
        f'  version: "{version}"',
        f'  description: "{DESCRIPTION}"',
        '  category: "workflow"',
        '  effect: "read-write"',
        '  author: "TELUS Digital"',
        "",
        "provides:",
        "  commands:",
    ]
    for name in commands:
        lines += [
            f'    - name: "speckit.spectra.{name}"',
            f'      file: "commands/{name}.md"',
            f'      description: "Does the {name} thing."',
        ]
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- #
# Projects
# --------------------------------------------------------------------------- #

@contextlib.contextmanager
def temp_project(installed_version: str | None = "1.3.1", *, is_project: bool = True,
                 incomplete: bool = False, subdir: str | None = None):
    """Yield the path a project-scoped command should be run from.

    The four states the CLI must distinguish map onto the arguments:

    * ``is_project=False``            -> NOT_A_PROJECT
    * ``installed_version=None``      -> NOT_INSTALLED
    * ``incomplete=True``             -> INCOMPLETE (folder present, no readable version)
    * ``installed_version="1.3.1"``   -> INSTALLED

    Pass ``subdir="a/b/c"`` to be handed a nested directory instead of the project root, which is how
    the "works from a subdirectory" requirement is exercised.
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        if is_project:
            (root / ".specify" / "memory").mkdir(parents=True)
        if incomplete:
            # An interrupted install: the folder exists but carries nothing readable.
            (root / ".specify" / "extensions" / "spectra").mkdir(parents=True)
        elif installed_version is not None and is_project:
            ext = root / ".specify" / "extensions" / "spectra"
            ext.mkdir(parents=True)
            (ext / "extension.yml").write_text(manifest_yaml(installed_version), encoding="utf-8")
        target = root
        if subdir:
            target = root / subdir
            target.mkdir(parents=True)
        yield target


@contextlib.contextmanager
def cwd(path):
    """Run a block with the process working directory moved, then restore it.

    Project discovery walks up from the working directory, so tests have to move; leaking a changed
    directory into the next test would make failures depend on execution order.
    """
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield Path(path)
    finally:
        os.chdir(previous)


# --------------------------------------------------------------------------- #
# Rosters
# --------------------------------------------------------------------------- #

_ROSTER = {
    "schema_version": "1.0",
    "phases": [
        {"id": "foundation", "title": "Foundation", "aidlc": "Inception"},
        {"id": "requirements-discovery", "title": "Requirements & Discovery", "aidlc": "Inception"},
        {"id": "deployment-operations", "title": "Deployment & Operations", "aidlc": "Operation"},
    ],
    "agents": [
        {
            "id": "constitution",
            "title": "Guardrails",
            "description": "Encode coding, security, and architecture standards once.",
            "status": "available",
            "phase": "foundation",
            "type": "core",
            "provider": "speckit",
            "command": "speckit.constitution",
        },
        {
            "id": "domain-analyzer",
            "title": "Domain Analyzer",
            "description": "Infer the project's domain and propose candidate guardrails.",
            "status": "available",
            "phase": "foundation",
            "type": "add-on",
            "provider": "spectra",
            "command": "speckit.spectra.domain-analyzer",
        },
        {
            "id": "brd",
            "title": "BRD Generator",
            "description": "Turn a raw business requirement into a specify-ready BRD.",
            "status": "available",
            "phase": "requirements-discovery",
            "type": "add-on",
            "provider": "spectra",
            "command": "speckit.spectra.brd",
        },
        {
            "id": "gdpr",
            "title": "GDPR Compliance",
            "description": "Verify data-subject rights, lawful basis, retention, and transfers.",
            "status": "planned",
            "phase": "requirements-discovery",
            "type": "add-on",
            "provider": "spectra",
        },
        {
            "id": "create-pr",
            "title": "GitHub (PR)",
            "description": "Open a correctly-targeted GitHub PR for the current spec branch.",
            "status": "available",
            "phase": "deployment-operations",
            "type": "core",
            "provider": "spectra",
            "command": "speckit.spectra.create-pr",
        },
    ],
}


def roster(**overrides) -> dict:
    """A small but structurally complete roster: both statuses, both providers, three phases.

    Deep-copied on every call so a test that mutates the result cannot affect the next one. Keyword
    arguments replace top-level keys, which is how the schema-version tests express themselves.
    """
    data = copy.deepcopy(_ROSTER)
    data.update(overrides)
    return data


def agent(data: dict, agent_id: str) -> dict:
    """The entry with `agent_id`, for tests that want to mutate exactly one agent."""
    for entry in data["agents"]:
        if entry["id"] == agent_id:
            return entry
    raise KeyError(f"no agent {agent_id!r} in this roster fixture")


# --------------------------------------------------------------------------- #
# Serving published data
# --------------------------------------------------------------------------- #

class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):  # noqa: D102 - silence per-request logging in test output
        pass


@contextlib.contextmanager
def serve(files: dict):
    """Serve `files` (relative path -> text) over loopback HTTP and yield the base URL.

    Binds port 0 so concurrent runs never collide, and serves from a temporary directory so the
    layout can mirror the published one — `agents-list.json` at the root, `spectra/extension.yml`
    one level down — which is what makes this a drop-in value for `SPECTRA_RAW_BASE`.
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for relative, text in files.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")

        def handler(*args, **kwargs):
            return _QuietHandler(*args, directory=str(root), **kwargs)

        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield f"http://127.0.0.1:{server.server_port}"
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)


def serve_roster(data: dict | None = None, *, manifest_version: str | None = None):
    """`serve()` preloaded with a roster, and optionally a published manifest beside it."""
    files = {"agents-list.json": json.dumps(data if data is not None else roster(), indent=2)}
    if manifest_version is not None:
        files["spectra/extension.yml"] = manifest_yaml(manifest_version)
    return serve(files)


@contextlib.contextmanager
def raw_base(base: str):
    """Point the CLI's published-data reads at `base` for the duration of the block."""
    previous = os.environ.get("SPECTRA_RAW_BASE")
    os.environ["SPECTRA_RAW_BASE"] = base
    try:
        yield base
    finally:
        if previous is None:
            os.environ.pop("SPECTRA_RAW_BASE", None)
        else:
            os.environ["SPECTRA_RAW_BASE"] = previous


# --------------------------------------------------------------------------- #
# Repository paths
# --------------------------------------------------------------------------- #

REPO_ROOT = Path(__file__).resolve().parent.parent


def repo_file(*parts) -> Path:
    """A path inside this repository, for the tests that assert on committed artifacts."""
    return REPO_ROOT.joinpath(*parts)
