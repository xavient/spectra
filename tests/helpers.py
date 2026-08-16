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
                 incomplete: bool = False, subdir: str | None = None,
                 integration_version=None):
    """Yield the path a project-scoped command should be run from.

    The four states the CLI must distinguish map onto the arguments:

    * ``is_project=False``            -> NOT_A_PROJECT
    * ``installed_version=None``      -> NOT_INSTALLED
    * ``incomplete=True``            -> INCOMPLETE (folder present, no readable version)
    * ``installed_version="1.3.1"``  -> INSTALLED

    Pass ``subdir="a/b/c"`` to be handed a nested directory instead of the project root, which is how
    the "works from a subdirectory" requirement is exercised.

    ``integration_version`` writes ``.specify/integration.json``, which the stack health check reads for
    the Core agents component. Four cases, because all four are states the check has to survive:

    * ``None``          -> no file at all (the default, so existing tests are unaffected)
    * a version string  -> a well-formed file recording it
    * :data:`BAD_JSON`  -> a file that is not valid JSON
    * :data:`NO_VERSION`-> valid JSON with the ``version`` key missing
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
        if is_project and integration_version is not None:
            write_integration(root, integration_version)
        target = root
        if subdir:
            target = root / subdir
            target.mkdir(parents=True)
        yield target


# --------------------------------------------------------------------------- #
# The Spec Kit integration file
# --------------------------------------------------------------------------- #

# Sentinels for `temp_project(integration_version=...)`. Distinct objects rather than magic strings so a
# real version string can never be mistaken for a directive.
BAD_JSON = object()     # write something that is not JSON
NO_VERSION = object()   # write valid JSON with no `version` key


def integration_json(version: str = "0.16.4") -> str:
    """An `.specify/integration.json` with the shape the health check reads.

    Mirrors the real file Spec Kit writes, including the keys we ignore, so a fixture that happened to
    contain only `version` could not let a too-eager reader pass.
    """
    return json.dumps({
        "version": version,
        "integration_state_schema": 1,
        "installed_integrations": ["claude"],
        "integration_settings": {"claude": {"script": "sh", "invoke_separator": "-"}},
        "integration": "claude",
        "default_integration": "claude",
    }, indent=2) + "\n"


def write_integration(project_root, version) -> None:
    """Write (or deliberately corrupt) `.specify/integration.json` under `project_root`."""
    path = Path(project_root) / ".specify" / "integration.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    if version is BAD_JSON:
        path.write_text("{ this is not json", encoding="utf-8")
    elif version is NO_VERSION:
        path.write_text(json.dumps({"integration": "claude"}, indent=2) + "\n", encoding="utf-8")
    else:
        path.write_text(integration_json(version), encoding="utf-8")


# --------------------------------------------------------------------------- #
# A stand-in `specify` on PATH
# --------------------------------------------------------------------------- #

# The five branches `specify self check` can print, copied from specify_cli/_version.py::self_check.
# Held as literals rather than generated, because the parser's whole job is to survive this exact text —
# a fixture derived from the parser would prove nothing.
SELF_CHECK_UP_TO_DATE = "Up to date: 0.16.4\n"
SELF_CHECK_UPDATE_AVAILABLE = (
    "Update available: 0.16.4 \u2192 v0.16.5\n"
    "\nTo upgrade:\n  specify self upgrade\n"
)
SELF_CHECK_FETCH_FAILED = (
    "Installed: 0.16.4\n"
    "Could not check latest release: network unreachable\n"
)
SELF_CHECK_TAG_INVALID = (
    "Installed: 0.16.4\n"
    "Latest release: (unknown)\n"
    "Could not validate latest release tag from GitHub.\n"
)
SELF_CHECK_NO_LOCAL_VERSION = (
    "Current version could not be determined.\n"
    "Latest release: v0.16.5\n"
)
SELF_CHECK_GIBBERISH = "something entirely unexpected\n"


@contextlib.contextmanager
def fake_specify(output: str = SELF_CHECK_UP_TO_DATE, *, exit_code: int = 0):
    """Put a stub `specify` on PATH that prints `output` for `self check`.

    Exercises the real subprocess path rather than only `parse_self_check`, so a mistake in how the
    child is invoked or decoded is caught too. `exit_code` defaults to 0 deliberately: the real command
    exits 0 on every branch, and a test that let us succeed only because of a non-zero code would be
    testing something Spec Kit does not actually do.
    """
    with tempfile.TemporaryDirectory() as tmp:
        script = Path(tmp) / "specify"
        script.write_text(
            "#!/bin/sh\n"
            f"cat <<'SPECTRA_EOF'\n{output}SPECTRA_EOF\n"
            f"exit {exit_code}\n",
            encoding="utf-8",
        )
        script.chmod(0o755)
        previous = os.environ.get("PATH", "")
        os.environ["PATH"] = f"{tmp}{os.pathsep}{previous}"
        try:
            yield script
        finally:
            os.environ["PATH"] = previous


@contextlib.contextmanager
def without_specify():
    """Remove `specify` from PATH for the duration of the block.

    Points PATH at an empty directory rather than editing it, so nothing that merely *looks* like
    `specify` can be found by accident.
    """
    with tempfile.TemporaryDirectory() as empty:
        previous = os.environ.get("PATH", "")
        os.environ["PATH"] = empty
        try:
            yield
        finally:
            os.environ["PATH"] = previous


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
