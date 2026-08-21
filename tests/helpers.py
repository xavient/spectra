"""Shared fixtures for the Spectra CLI test suite.

Standard library only, like everything else in this repository — `unittest` rather than pytest, and
nothing here imports `spectra_cli`, so these helpers stay usable while the modules they support are
still being written.

Three kinds of fixture:

* **Projects** — `temp_project()` builds a throwaway Spec Kit project in each of the four states the
  CLI classifies, so tests never touch the developer's real tree.
* **Rosters** — `roster()` returns a valid roster dict that a test mutates to express the one thing it
  cares about, instead of restating all 45 published entries.
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
import sys
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
                 integration_version=None, integrations=None, default_integration=None,
                 registered_agents=None):
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

    ``integrations`` makes the project **multi-integration**: a mapping of integration key to the
    version its own manifest records, e.g. ``{"kiro-cli": "0.16.5", "claude": "0.15.1"}``. It writes
    ``installed_integrations`` and ``default_integration`` into ``.specify/integration.json`` and one
    ``.specify/integrations/<key>.manifest.json`` per key. Pass :data:`MISSING_MANIFEST` as a value to
    record a key as installed while leaving it no readable manifest.

    Omitting ``integrations`` leaves the single-record fixture exactly as it was, which is what keeps the
    existing tests — and the fallback path they cover — untouched.

    ``registered_agents`` writes ``.specify/extensions/.registry`` recording which agents Spectra's
    commands are registered for, so the coverage advisory has something to read. ``None`` writes no
    registry at all, which is the "cannot determine, say nothing" case.
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
            write_integration(root, integration_version, integrations=integrations,
                              default_integration=default_integration)
        if is_project and integrations is not None:
            write_integration_manifests(root, integrations)
        if is_project and registered_agents is not None:
            write_registry(root, registered_agents)
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
NO_DEFAULT = object()   # write valid JSON that records no default integration

# Sentinel for `temp_project(integrations={...})`: record the key as installed but write no manifest for
# it. That is "recorded but unverifiable" — a state the enumeration must report as unknown rather than
# drop, so it needs to be expressible in a fixture.
MISSING_MANIFEST = object()


def integration_json(version: str = "0.16.4", *, integrations=None, default_integration=None) -> str:
    """An `.specify/integration.json` with the shape the health check reads.

    Mirrors the real file Spec Kit writes, including the keys we ignore, so a fixture that happened to
    contain only `version` could not let a too-eager reader pass.

    With `integrations` given, `installed_integrations` lists those keys and `default_integration` names
    the first (or the one passed explicitly) — the multi-install shape. The top-level `version` is left
    as given on purpose: the real file records the CLI that last ran *any* upgrade, which is exactly the
    field that can disagree with a stale per-integration manifest.
    """
    keys = list(integrations) if integrations else ["claude"]
    payload = {
        "version": version,
        "integration_state_schema": 1,
        "installed_integrations": keys,
        "integration_settings": {k: {"script": "sh", "invoke_separator": "-"} for k in keys},
    }
    # NO_DEFAULT writes a file that records installed integrations but names no default — a real state
    # (Spec Kit can leave it after a partial migration) in which nothing may be activated, because there
    # would be nothing to restore.
    if default_integration is not NO_DEFAULT:
        default = default_integration or keys[0]
        payload["integration"] = default
        payload["default_integration"] = default
    return json.dumps(payload, indent=2) + "\n"


def write_integration(project_root, version, *, integrations=None, default_integration=None) -> None:
    """Write (or deliberately corrupt) `.specify/integration.json` under `project_root`."""
    path = Path(project_root) / ".specify" / "integration.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    if version is BAD_JSON:
        path.write_text("{ this is not json", encoding="utf-8")
    elif version is NO_VERSION:
        path.write_text(json.dumps({"integration": "claude"}, indent=2) + "\n", encoding="utf-8")
    else:
        path.write_text(integration_json(version, integrations=integrations,
                                         default_integration=default_integration), encoding="utf-8")


def integration_manifest(key: str, version: str) -> str:
    """A `.specify/integrations/<key>.manifest.json` with the shape the per-integration read expects.

    Carries `integration`, `installed_at`, and `files` alongside `version` because the real manifest does;
    a fixture holding only the field we read could let a reader that grabs the wrong key pass.
    """
    return json.dumps({
        "integration": key,
        "version": version,
        "installed_at": "2026-08-19T00:00:00.000000+00:00",
        "files": {f".{key}/commands/speckit.plan.md": "0" * 64},
    }, indent=2) + "\n"


def write_integration_manifests(project_root, integrations: dict) -> None:
    """Write one manifest per entry in `integrations`, honouring :data:`MISSING_MANIFEST`.

    Also writes `speckit.manifest.json` — the shared-infrastructure record — because it sits in the same
    directory and is *not* an integration. Every fixture carries it so a reader that enumerates by
    globbing the directory fails here rather than in production.
    """
    directory = Path(project_root) / ".specify" / "integrations"
    directory.mkdir(parents=True, exist_ok=True)
    for key, version in integrations.items():
        if version is MISSING_MANIFEST:
            continue
        (directory / f"{key}.manifest.json").write_text(integration_manifest(key, version),
                                                        encoding="utf-8")
    (directory / "speckit.manifest.json").write_text(integration_manifest("speckit", "0.16.4"),
                                                     encoding="utf-8")


def write_registry(project_root, registered_agents) -> None:
    """Write `.specify/extensions/.registry` recording Spectra's per-agent command registration.

    `registered_agents` is a list of agent keys, or :data:`BAD_JSON` for an unreadable registry, or an
    empty list for a `spectra` entry that records no command map at all. All three of the latter mean
    "coverage could not be determined", which must produce no advisory rather than a guess.
    """
    path = Path(project_root) / ".specify" / "extensions" / ".registry"
    path.parent.mkdir(parents=True, exist_ok=True)
    if registered_agents is BAD_JSON:
        path.write_text("{ not json at all", encoding="utf-8")
        return
    commands = {agent: ["speckit.spectra.adr"] for agent in registered_agents}
    path.write_text(json.dumps({
        "schema_version": "1.0",
        "extensions": {
            "spectra": {
                "version": "1.3.1",
                "enabled": True,
                "registered_commands": commands,
            },
        },
    }, indent=2) + "\n", encoding="utf-8")


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


def integration_status_json(installed=("claude",), *, default=None, modified=None,
                            status=None) -> str:
    """The payload `specify integration status --json` prints, reduced to what we read.

    Reproduces the real shape: per-manifest `modified_files` lists under `manifests`, the `speckit`
    record sitting among them without being an integration, and `findings` carrying the
    `managed-files-modified` code. `status` derives from the findings unless overridden, mirroring the
    real command — which reports `warning` while still exiting 0.
    """
    modified = dict(modified or {})
    keys = list(installed)
    manifests = {}
    for key in keys + ["speckit"]:
        manifests[key] = {
            "manifest": f".specify/integrations/{key}.manifest.json",
            "readable": True,
            "tracked_files": 10,
            "missing_files": [],
            "modified_files": list(modified.get(key, [])),
            "invalid_files": [],
        }
    findings = [
        {"severity": "warning", "code": "managed-files-modified",
         "message": f"{len(files)} managed file(s) were modified for integration '{key}'.",
         "integration": key,
         "suggestion": "Review the changes before running `specify integration upgrade --force`."}
        for key, files in modified.items() if files
    ]
    total = sum(len(files) for files in modified.values())
    return json.dumps({
        "status": status or ("warning" if findings else "ok"),
        "default_integration": default or (keys[0] if keys else None),
        "installed_integrations": keys,
        "recorded_installed_integrations": keys,
        "manifest_checked_integrations": keys + ["speckit"],
        "multi_install_safe": True,
        "shared_templates_target_alignment": default or (keys[0] if keys else None),
        "missing_managed_files": 0,
        "modified_managed_files": total,
        "invalid_manifest_paths": 0,
        "unchecked_manifests": 0,
        "manifests": manifests,
        "findings": findings,
    }, indent=2) + "\n"


@contextlib.contextmanager
def fake_specify(output: str = SELF_CHECK_UP_TO_DATE, *, exit_code: int = 0,
                 installed=("claude",), default=None, modified=None,
                 status_output=None, status_exit_code=0,
                 argv_log=None, use_effect=None, use_fails=()):
    """Put a stub `specify` on PATH that answers each subcommand it is actually asked.

    Exercises the real subprocess path rather than only `parse_self_check`, so a mistake in how the
    child is invoked or decoded is caught too. `exit_code` defaults to 0 deliberately: the real command
    exits 0 on every branch, and a test that let us succeed only because of a non-zero code would be
    testing something Spec Kit does not actually do.

    **Argument-aware on purpose.** A stub that printed self-check text for every invocation would answer
    `integration status --json` with the wrong payload entirely, and the reader would still "pass". The
    dispatch below is therefore part of the fixture's correctness:

    * ``self check``               -> `output` (one of the SELF_CHECK_* branches)
    * ``integration status --json``-> a JSON payload built from `installed` / `default` / `modified`
    * ``integration use <key>``    -> applies `use_effect`, fails for keys in `use_fails`
    * anything else                -> exit 0 silently, which is what a delegated upgrade looks like

    `modified` maps an integration key (or ``"speckit"`` for shared infrastructure) to the managed files
    that diverge, which is what makes the disclosure and consent paths testable end to end.
    `status_output` replaces the JSON wholesale — pass unparseable text to exercise degradation — and
    `status_exit_code` makes the status call fail outright.

    Three parameters exist for the coverage rotation, and each closes a hole the older stub left:

    ``argv_log``
        A path. Every invocation appends its arguments as one line, so a test can assert the exact
        rotation order — and the presence of the restoring call — without parsing human-facing output.
        Read it with :func:`read_argv_log`.
    ``use_effect``
        A project root. When given, ``integration use <key>`` *acts*: it adds `<key>` to
        `.specify/extensions/.registry` and writes `<key>` as `default_integration` in
        `.specify/integration.json`, the way the real command does. Without this the stub exits 0 while
        nothing changes, so post-rotation verification would pass vacuously and a broken restore would be
        invisible.
    ``use_fails``
        Integration keys whose activation exits non-zero. This is how the failed-activation and
        failed-restore paths are reached — including leaving the default pointing at the wrong agent.
    """
    payload = (status_output if status_output is not None
               else integration_status_json(installed, default=default, modified=modified))
    # Built by concatenation rather than f-strings on purpose: the shell fragments below contain both
    # quote characters, and an f-string expression cannot carry a quote of its own delimiter — or any
    # escape — before Python 3.12 (PEP 701). The CI matrix includes 3.9, where that is a SyntaxError at
    # import time, which takes the whole suite down rather than one test.
    fail_list = " ".join('"' + key + '"' for key in use_fails) or '""'
    log_line = 'printf "%s\\n" "$*" >> ' + str(argv_log) + "\n" if argv_log else ""
    with tempfile.TemporaryDirectory() as tmp:
        script = Path(tmp) / "specify"
        helper = Path(tmp) / "use_effect.py"
        use_line = ("  " + sys.executable + " " + str(helper) + " " + str(use_effect)
                    + ' "$3" || exit 1\n')
        # A tiny Python helper rather than shell JSON surgery: the registry and integration.json are
        # JSON, and sed-ing them would be the kind of fixture that passes while the product is wrong.
        helper.write_text(
            "import json, sys, pathlib\n"
            "root, key = pathlib.Path(sys.argv[1]), sys.argv[2]\n"
            "reg = root / '.specify' / 'extensions' / '.registry'\n"
            "try:\n"
            "    data = json.loads(reg.read_text())\n"
            "except (OSError, ValueError):\n"
            "    data = None\n"
            "if isinstance(data, dict):\n"
            "    entry = data.setdefault('extensions', {}).setdefault('spectra', {})\n"
            "    commands = entry.setdefault('registered_commands', {})\n"
            "    if isinstance(commands, dict):\n"
            "        commands[key] = ['speckit.spectra.adr']\n"
            "        reg.write_text(json.dumps(data, indent=2) + '\\n')\n"
            "cfg = root / '.specify' / 'integration.json'\n"
            "try:\n"
            "    state = json.loads(cfg.read_text())\n"
            "except (OSError, ValueError):\n"
            "    state = None\n"
            "if isinstance(state, dict):\n"
            "    state['default_integration'] = key\n"
            "    state['integration'] = key\n"
            "    cfg.write_text(json.dumps(state, indent=2) + '\\n')\n",
            encoding="utf-8",
        )
        script.write_text(
            "#!/bin/sh\n"
            + log_line
            + 'if [ "$1" = "self" ] && [ "$2" = "check" ]; then\n'
            + "  cat <<'SPECTRA_SELF_EOF'\n" + output + "SPECTRA_SELF_EOF\n"
            + "  exit " + str(exit_code) + "\n"
            + "fi\n"
            + 'if [ "$1" = "integration" ] && [ "$2" = "status" ]; then\n'
            + "  cat <<'SPECTRA_STATUS_EOF'\n" + payload + "SPECTRA_STATUS_EOF\n"
            + "  exit " + str(status_exit_code) + "\n"
            + "fi\n"
            + 'if [ "$1" = "integration" ] && [ "$2" = "use" ]; then\n'
            + "  for failing in " + fail_list + "; do\n"
            + '    if [ "$3" = "$failing" ]; then exit 1; fi\n'
            + "  done\n"
            + (use_line if use_effect else "")
            + "  exit 0\n"
            + "fi\n"
            + "exit 0\n",
            encoding="utf-8",
        )
        script.chmod(0o755)
        previous = os.environ.get("PATH", "")
        os.environ["PATH"] = f"{tmp}{os.pathsep}{previous}"
        try:
            yield script
        finally:
            os.environ["PATH"] = previous


def read_argv_log(path):
    """The `specify` invocations recorded by `fake_specify(argv_log=…)`, oldest first.

    Returns a list of argument lists. Absent log -> empty list, so a test asserting "nothing was invoked"
    reads the same whether the stub was never called or never asked to log.
    """
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError:
        return []
    return [line.split() for line in text.splitlines() if line.strip()]


def integration_use_calls(path):
    """Just the integration keys passed to `specify integration use`, in order.

    The rotation's contract is about that sequence — targets first, the original default last — so tests
    assert on this rather than on the whole log.
    """
    return [argv[2] for argv in read_argv_log(path)
            if len(argv) >= 3 and argv[0] == "integration" and argv[1] == "use"]


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
            "title": "Create PR",
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
