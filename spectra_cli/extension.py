"""The installed extension, the published one, and delegating changes to Spec Kit.

Three jobs:

* read the version out of an extension manifest, installed or published;
* compare the two into a verdict;
* hand updates and removals to Spec Kit's own `specify extension` commands rather than editing the
  project's extension files ourselves.

**Why a line scanner and not a YAML parser.** The CLI ships with zero third-party dependencies, so
there is no `yaml` module available, and vendoring one to read a single field would be far more code
and far more failure modes than the field justifies. The manifest's shape is fixed by Spec Kit's own
schema — `  version: "X.Y.Z"`, two spaces deep, inside the `extension:` block — and
`.github/workflows/ci.yml` already depends on exactly that shape with `sed`. Scanning for it here is
the established approach in this repository, not a shortcut.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

from spectra_cli import net, version as cli_version

EXTENSION_ID = "spectra"

# The manifest path published on the default branch, relative to the repository root.
PUBLISHED_MANIFEST = "spectra/extension.yml"

# `  version: "1.3.1"` — the `extension:` block's own version, at two-space indentation. Anchored to
# the line so a nested `version:` deeper in the file (for example under `requires:`) cannot match.
_VERSION_LINE = re.compile(r'^  version:\s*"?([^"\s]+)"?\s*$')

# Verdicts from `compare()`.
UP_TO_DATE = "up_to_date"
OUT_OF_DATE = "out_of_date"
AHEAD = "ahead"


class DelegationError(Exception):
    """A Spec Kit command could not be run, or ran and failed. Message is user-facing."""


# --------------------------------------------------------------------------- #
# Reading versions
# --------------------------------------------------------------------------- #

def parse_manifest_version(text: str):
    """The `extension.version` value from manifest text, or None.

    Stops at the first match, which is the `extension:` block's own version because that block is
    first in every manifest Spec Kit writes.
    """
    for line in text.splitlines():
        match = _VERSION_LINE.match(line)
        if match:
            return match.group(1).strip() or None
    return None


def read_manifest_version(path):
    """The version recorded in the manifest at `path`, or None if it cannot be read.

    Missing, unreadable, and version-less manifests all return None on purpose: to the caller they
    are the same situation — the install cannot be trusted to report what it is.
    """
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    return parse_manifest_version(text)


def published_version(timeout: int = net.TIMEOUT):
    """The version published on the default branch. Raises :class:`net.FetchError` if unreachable.

    Read from the manifest rather than from `catalog.json` because the manifest is the authoritative
    field for the catalog channel (constitution Principle VI). CI enforces that the two agree, so
    either would give the same answer; this one is the source.
    """
    text = net.fetch_text(PUBLISHED_MANIFEST, timeout=timeout)
    parsed = parse_manifest_version(text)
    if not parsed:
        raise net.FetchError(
            f"{net.url_for(PUBLISHED_MANIFEST)} did not contain an extension version.")
    return parsed


def compare(installed: str, published: str) -> str:
    """One of UP_TO_DATE / OUT_OF_DATE / AHEAD.

    Reuses the CLI channel's comparison, which is already component-wise, already tolerant of a
    leading `v`, and already sorts an unparseable version below any real one.
    """
    result = cli_version.compare_versions(installed, published)
    if result < 0:
        return OUT_OF_DATE
    if result > 0:
        return AHEAD
    return UP_TO_DATE


def registered_agents(project_root):
    """The agents Spectra's commands are registered for, or None when that cannot be established.

    Read from `extensions.spectra.registered_commands` in `.specify/extensions/.registry` — a map keyed by
    agent, which Spec Kit maintains. Recorded state, not an inference about the dependency's policy, so
    the answer holds regardless of *why* an agent is missing from it.

    **None means "say nothing".** A missing registry, unreadable JSON, no `spectra` entry, or an entry with
    no command map are all states in which coverage is unknown — and an unknown must not be reported as
    "no agents covered", which would tell a healthy project it had a problem. This repository is itself an
    example: it is the extension's source rather than a consumer of it, so it has no `spectra` entry and
    must stay silent.
    """
    if project_root is None:
        return None
    path = Path(project_root) / ".specify" / "extensions" / ".registry"
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    extensions = data.get("extensions")
    if not isinstance(extensions, dict):
        return None
    entry = extensions.get(EXTENSION_ID)
    if not isinstance(entry, dict):
        return None
    commands = entry.get("registered_commands")
    if not isinstance(commands, dict) or not commands:
        return None
    return {agent for agent in commands if isinstance(agent, str) and agent}


# --------------------------------------------------------------------------- #
# Delegating to Spec Kit
# --------------------------------------------------------------------------- #

def specify_available() -> bool:
    """Whether Spec Kit's CLI is on PATH."""
    return shutil.which("specify") is not None


def _delegate(argv, *, feed: str | None = None) -> int:
    """Run a `specify` command attached to the terminal so its prompts and output reach the user.

    `feed` writes a canned answer to the child's stdin, for the one case where Spec Kit prompts and
    offers no flag to skip it. Only stdin is piped — stdout and stderr still inherit, so the user sees
    everything the command says.
    """
    if not specify_available():
        raise DelegationError(
            "Spec Kit's `specify` CLI was not found on PATH, and Spectra delegates this to it.\n"
            "  Install Spec Kit, then try again: https://github.com/github/spec-kit")
    try:
        if feed is None:
            return subprocess.call(argv)
        return subprocess.run(argv, input=feed, text=True).returncode
    except OSError as exc:
        raise DelegationError(f"could not run `{' '.join(argv)}` ({exc}).") from exc
    except KeyboardInterrupt:
        return 130


def delegate_update(assume_yes: bool = False) -> int:
    """`specify extension update spectra`. Returns its exit code.

    `specify extension update` prompts "Update these extensions? [y/N]" and, unlike
    `specify extension remove`, offers **no** flag to skip it — so a non-interactive run aborts with
    exit 1. When the caller already has the user's consent (`spectra update --yes`, which lists exactly
    what will change before asking), that answer is fed through rather than letting a prompt nobody can
    see fail the run.
    """
    return _delegate(["specify", "extension", "update", EXTENSION_ID],
                     feed="y\n" if assume_yes else None)


def delegate_self_upgrade() -> int:
    """`specify self upgrade`. Returns its exit code.

    Spec Kit's own CLI upgrading itself. Runs first in the update order because the integration upgrade
    that follows is performed *by* this CLI, so it should be the new one doing it.
    """
    return _delegate(["specify", "self", "upgrade"])


def delegate_integration_upgrade(key: str | None = None, force: bool = False) -> int:
    """`specify integration upgrade [key] [--force]`. Returns its exit code.

    **`key` names the integration to upgrade, and that is the whole mechanism.** Invoked bare, the
    upgrade resolves to the project's *default* integration and silently leaves every other installed one
    stale — which is the bug this feature exists to fix. Naming the key upgrades a non-default integration
    without re-pointing the project, so Spectra never has to change which agent a project targets.

    **`--force` is reachable, and gated.** An earlier contract
    (`specs/007-unified-version-update/contracts/health-check.md`) recorded that it was deliberately never
    passed: Spec Kit blocks this upgrade when it detects locally modified managed files, and *silently*
    overriding that would discard the user's edits. That reasoning is unchanged and still binding — what
    changed is that the blanket refusal also produced a dead end, a project that could not be updated at
    all with no explanation of why.

    So the override is now reachable through exactly one path: `cmd_update` discloses the precise files
    that would be overwritten — per integration, and shared Spec Kit infrastructure separately, because
    the overwrite is not scoped to the files that caused the block — and obtains an authorization act in
    the same run, either an interactive answer defaulting to *no* or an explicit `--force`. **No other
    caller may pass `force=True`**; if a second one appears, the guarantee that nothing is overwritten
    without an informed yes is gone. See
    `specs/010-multi-integration-updates/contracts/cli-surface.md` § 8.
    """
    argv = ["specify", "integration", "upgrade"]
    if key:
        argv.append(key)
    if force:
        argv.append("--force")
    return _delegate(argv)


def delegate_remove(force: bool = False) -> int:
    """`specify extension remove spectra`, adding `--force` only when asked.

    Spec Kit already prompts for confirmation and already offers `--force` to skip it, so the
    confirmation stays there rather than being duplicated here. Asking twice for one action is worse
    than asking once, and putting our own gate in front of an unguarded inner command would leave
    anyone calling `specify` directly no safer.
    """
    argv = ["specify", "extension", "remove", EXTENSION_ID]
    if force:
        argv.append("--force")
    return _delegate(argv)
