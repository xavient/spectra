"""The health of the whole Spectra stack, and bringing it current.

Four things have to be current for Spectra to work, and until now the CLI could only report on one of
them. This module answers the whole question — *is my stack current?* — by resolving each component to
the **same** :class:`ComponentStatus` shape no matter how differently it has to be detected:

``Specify CLI``
    Spec Kit's own CLI. Detected by running `specify self check` and **parsing its stdout**, because
    that command exits 0 on every path it takes, including its failure paths. See
    :func:`parse_self_check`.
``Core agents``
    The Spec Kit integration installed into `.specify/`. Its version is recorded in
    `.specify/integration.json` and nowhere else — `specify integration status` reports health but no
    version — and it *tracks* the CLI version, which is why a behind CLI implies a behind integration.
``Spectra CLI``
    This command. Delegated wholesale to :mod:`spectra_cli.version`.
``Spectra agents``
    The extension installed in this project. Delegated wholesale to :mod:`spectra_cli.extension`.

That uniformity is the point. It collapses `spectra version` into "render four rows" and
`spectra update` into "walk four rows in order", with no per-component branching in either command.

**Why the walk lives here and not in `cli.py`.** :func:`apply_updates` carries the most intricate logic
in the feature — an ordered walk that must continue past failures, skip what it could not establish, and
still stop dead on an interrupt. Keeping it beside the checks makes it testable without argparse, a
prompt, or a terminal; `cli.py` keeps only parsing, prompting, and rendering.

**Nothing here raises.** A component that cannot be checked is a *status*, not an exception — the same
rule :func:`spectra_cli.project.classify` already follows. An unreachable network, an absent `specify`,
and a corrupt integration file are all ordinary answers, and each degrades exactly one row.
"""

from __future__ import annotations

import json
import shutil
import subprocess

from spectra_cli import extension, net, project, version as cli_version

# --------------------------------------------------------------------------- #
# Vocabulary
# --------------------------------------------------------------------------- #

# Component status. Four values, deliberately: there is no separate `error`, because reporting an
# error and reporting an unknown lead the caller to do exactly the same two things — show it, and
# refuse to act on it. A fifth value would be a distinction without a consequence.
UP_TO_DATE = "up_to_date"
NEEDS_UPDATING = "needs_updating"
AHEAD = "ahead"
UNKNOWN = "unknown"

# Component keys. Stable identifiers, distinct from the display labels so the walk and the tests match
# on something that is free to stay put while copy is reworded.
SPECIFY_CLI = "specify_cli"
INTEGRATION = "integration"
SPECTRA_CLI = "spectra_cli"
SPECTRA_EXTENSION = "spectra_extension"

LABELS = {
    SPECIFY_CLI: "Specify CLI",
    INTEGRATION: "Core agents",
    SPECTRA_CLI: "Spectra CLI",
    SPECTRA_EXTENSION: "Spectra agents",
}

# Canonical order. This is *also* the update order, so `HealthReport.outdated` is directly walkable and
# the ordering constraint holds by construction rather than by a sort at the call site. Two facts pin
# it: the integration verdict is derived from the CLI verdict, so the CLI must resolve first; and
# updating the Spectra CLI replaces this running process's own code, so it must come after both
# `specify` steps and before only the extension update.
ORDER = (SPECIFY_CLI, INTEGRATION, SPECTRA_CLI, SPECTRA_EXTENSION)

# Update outcomes.
UPDATED = "updated"
FAILED = "failed"
SKIPPED = "skipped"

# How long `specify self check` gets before we give up and call it unknown. It makes a GitHub request
# of its own, so a hung network inside the child must not hang us.
SELF_CHECK_TIMEOUT = 15


# --------------------------------------------------------------------------- #
# Structures
# --------------------------------------------------------------------------- #

class ComponentStatus:
    """The health of one component, resolved once per command invocation.

    `detail` is required whenever `status` is :data:`UNKNOWN` — an unknown with no explanation tells a
    user nothing they can act on. `installed` may be set while the status is still unknown: that is the
    ordinary offline case, where the local version reads fine but there is nothing to compare it to.
    """

    __slots__ = ("key", "installed", "latest", "status", "detail")

    def __init__(self, key, status, installed=None, latest=None, detail=None):
        self.key = key
        self.status = status
        self.installed = installed
        self.latest = latest
        self.detail = detail

    @property
    def label(self) -> str:
        return LABELS.get(self.key, self.key)

    @property
    def needs_updating(self) -> bool:
        return self.status == NEEDS_UPDATING

    @property
    def is_unknown(self) -> bool:
        return self.status == UNKNOWN

    def __repr__(self):  # pragma: no cover - diagnostics only
        return (f"ComponentStatus({self.key!r}, {self.status!r}, installed={self.installed!r}, "
                f"latest={self.latest!r})")


class HealthReport:
    """The four statuses together — full-stack health at one moment.

    Never filtered and never reordered. A component that could not be checked stays in the list as
    `UNKNOWN` rather than being dropped, so the table always has four rows and a reader can tell "not
    checked" from "not there".
    """

    __slots__ = ("components",)

    def __init__(self, components):
        self.components = list(components)

    def __iter__(self):
        return iter(self.components)

    def get(self, key):
        """The status for `key`, or None."""
        for component in self.components:
            if component.key == key:
                return component
        return None

    @property
    def outdated(self):
        """Components needing an update, in canonical order — directly walkable."""
        return [c for c in self.components if c.status == NEEDS_UPDATING]

    @property
    def needs_update(self) -> bool:
        return bool(self.outdated)

    @property
    def unknown(self):
        """Components whose status could not be established."""
        return [c for c in self.components if c.status == UNKNOWN]

    @property
    def all_unknown(self) -> bool:
        """True when nothing at all could be checked.

        Distinct from `not needs_update`, and the distinction is user-visible: "everything is current"
        and "nothing could be checked" are opposite situations that would otherwise print the same
        reassuring sentence.
        """
        return bool(self.components) and len(self.unknown) == len(self.components)


class UpdateResult:
    """What happened when one component's update was attempted — or why it was not.

    `SKIPPED` is load-bearing rather than cosmetic: it is what stops a component we could not establish
    from turning a successful run into a failed one. The exit code answers "did anything I *attempted*
    go wrong?", so something never attempted cannot contribute to it.
    """

    __slots__ = ("key", "outcome", "detail")

    def __init__(self, key, outcome, detail=None):
        self.key = key
        self.outcome = outcome
        self.detail = detail

    @property
    def label(self) -> str:
        return LABELS.get(self.key, self.key)

    @property
    def failed(self) -> bool:
        return self.outcome == FAILED

    def __repr__(self):  # pragma: no cover - diagnostics only
        return f"UpdateResult({self.key!r}, {self.outcome!r}, detail={self.detail!r})"


# --------------------------------------------------------------------------- #
# 1 · Specify CLI
# --------------------------------------------------------------------------- #

# The exact strings `specify self check` prints, from specify_cli/_version.py::self_check.
_UP_TO_DATE_PREFIX = "Up to date:"
_UPDATE_AVAILABLE_PREFIX = "Update available:"
_INSTALLED_PREFIX = "Installed:"
_LATEST_PREFIX = "Latest release:"
_UNDETERMINED = "Current version could not be determined."
_FETCH_FAILED_PREFIX = "Could not check latest release:"
_TAG_INVALID = "Could not validate latest release tag"

# `Update available: 0.16.4 → v0.16.5` — the separator is U+2192, not `->`.
_ARROW = "\u2192"


def parse_self_check(text):
    """Interpret `specify self check` output. Returns `{status, installed, latest, detail}`.

    **The exit code is not consulted, because it carries no information** — `self_check` returns 0 on
    all five of its branches, including "could not reach GitHub". Folding those into "needs updating"
    (as a naive read of the command's contract would) would send `spectra update` off to run
    `specify self upgrade` against a CLI whose state was never established.

    Matching is on line *prefixes* so that Rich's 80-column wrapping of a long failure reason cannot
    turn a continuation line into a directive. Anything unrecognized is UNKNOWN rather than a guess,
    which is what keeps this honest if the upstream format changes.
    """
    lines = [line.strip() for line in (text or "").splitlines()]
    present = [line for line in lines if line]

    def find(prefix):
        for line in present:
            if line.startswith(prefix):
                return line[len(prefix):].strip()
        return None

    # 1 - current.
    current = find(_UP_TO_DATE_PREFIX)
    if current:
        return {"status": UP_TO_DATE, "installed": current, "latest": current, "detail": None}

    # 2 - a newer release exists.
    available = find(_UPDATE_AVAILABLE_PREFIX)
    if available and _ARROW in available:
        installed, _, latest = available.partition(_ARROW)
        installed, latest = installed.strip(), latest.strip()
        if installed and latest:
            return {"status": NEEDS_UPDATING, "installed": installed, "latest": latest,
                    "detail": None}

    # 3 - the local version is unreadable.
    if any(line.startswith(_UNDETERMINED) for line in present):
        return {"status": UNKNOWN, "installed": None, "latest": find(_LATEST_PREFIX),
                "detail": "Spec Kit could not determine its own installed version."}

    # 4 - the local version reads, but the latest could not be resolved or validated.
    installed = find(_INSTALLED_PREFIX)
    if installed:
        reason = find(_FETCH_FAILED_PREFIX)
        if reason:
            return {"status": UNKNOWN, "installed": installed, "latest": None,
                    "detail": f"the latest Spec Kit release could not be checked ({reason})"}
        if any(line.startswith(_TAG_INVALID) for line in present):
            return {"status": UNKNOWN, "installed": installed, "latest": None,
                    "detail": "Spec Kit could not validate the latest release tag from GitHub."}
        return {"status": UNKNOWN, "installed": installed, "latest": None,
                "detail": "`specify self check` reported no verdict."}

    # 5 - nothing recognized. Keep the first line so the user sees what we actually got.
    first = present[0] if present else ""
    detail = (f"`specify self check` printed something this version of Spectra does not "
              f"recognize: {first!r}") if first else "`specify self check` printed nothing."
    return {"status": UNKNOWN, "installed": None, "latest": None, "detail": detail}


def specify_available() -> bool:
    """Whether Spec Kit's CLI is on PATH."""
    return shutil.which("specify") is not None


def get_specify_cli_status(timeout: int = SELF_CHECK_TIMEOUT) -> ComponentStatus:
    """Resolve the Specify CLI by running `specify self check`. Never raises."""
    if not specify_available():
        return ComponentStatus(
            SPECIFY_CLI, UNKNOWN,
            detail="`specify` is not on PATH, so Spec Kit's version could not be checked.")
    try:
        proc = subprocess.run(["specify", "self", "check"], capture_output=True, text=True,
                              timeout=timeout)
    except subprocess.TimeoutExpired:
        return ComponentStatus(
            SPECIFY_CLI, UNKNOWN,
            detail=f"`specify self check` did not finish within {timeout}s.")
    except OSError as exc:
        return ComponentStatus(
            SPECIFY_CLI, UNKNOWN, detail=f"`specify self check` could not be run ({exc}).")

    parsed = parse_self_check(f"{proc.stdout or ''}\n{proc.stderr or ''}")
    return ComponentStatus(SPECIFY_CLI, parsed["status"], installed=parsed["installed"],
                           latest=parsed["latest"], detail=parsed["detail"])


# --------------------------------------------------------------------------- #
# 2 · Core agents (the Spec Kit integration)
# --------------------------------------------------------------------------- #

INTEGRATION_FILE = "integration.json"


def read_integration_version(project_root):
    """The `version` recorded in `.specify/integration.json`, or None.

    Missing file, unreadable file, invalid JSON, a non-object top level, and an absent or empty
    `version` all return None on purpose: to the caller they are one situation — the integration cannot
    be trusted to report what it is — and they share one remedy.
    """
    if project_root is None:
        return None
    path = project_root / ".specify" / INTEGRATION_FILE
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    recorded = data.get("version")
    if not isinstance(recorded, str):
        return None
    return recorded.strip() or None


def get_integration_status(project_root, specify_status: ComponentStatus) -> ComponentStatus:
    """Resolve the integration, given the already-resolved Specify CLI status.

    Cannot be evaluated independently. The recorded version means "the Spec Kit that installed this
    integration", so it is only meaningful against a known CLI version — hence an unknown CLI forces an
    unknown integration rather than a guess from the file alone.

    Two independent ways to be behind:

    * **the CLI is behind** — the file can only ever record what the *old* CLI installed, so the
      integration is behind too, whatever the file says. Its target is then the CLI's own latest, so
      the row reads the same transition the upgrade will actually produce.
    * **the CLI is current but the file disagrees with it** — the user upgraded the CLI and never re-ran
      the integration upgrade. Locally detectable, and invisible until now.
    """
    recorded = read_integration_version(project_root)

    if specify_status.status == UNKNOWN:
        return ComponentStatus(
            INTEGRATION, UNKNOWN, installed=recorded,
            detail="the Specify CLI version is unknown, so there is nothing to compare against.")

    if recorded is None:
        return ComponentStatus(
            INTEGRATION, UNKNOWN,
            detail=f"no usable version in .specify/{INTEGRATION_FILE}.")

    if specify_status.status == NEEDS_UPDATING:
        return ComponentStatus(INTEGRATION, NEEDS_UPDATING, installed=recorded,
                               latest=specify_status.latest,
                               detail="the Specify CLI is behind, and the integration tracks it.")

    # The CLI is current (or ahead): compare the file against what is actually installed.
    installed_cli = specify_status.installed
    comparison = cli_version.compare_versions(recorded, installed_cli or "")
    if comparison < 0:
        return ComponentStatus(
            INTEGRATION, NEEDS_UPDATING, installed=recorded, latest=installed_cli,
            detail="the Specify CLI was upgraded but the integration was not re-run.")
    if comparison > 0:
        return ComponentStatus(
            INTEGRATION, AHEAD, installed=recorded, latest=installed_cli,
            detail="the integration is newer than the Specify CLI installed here.")
    return ComponentStatus(INTEGRATION, UP_TO_DATE, installed=recorded, latest=installed_cli)


# --------------------------------------------------------------------------- #
# 3 · Spectra CLI (this command)
# --------------------------------------------------------------------------- #

def get_spectra_cli_status(*, skip_network: bool = False) -> ComponentStatus:
    """Resolve this command's own version, reusing the existing release check."""
    installed = cli_version.read_installed_version()

    if skip_network:
        return ComponentStatus(
            SPECTRA_CLI, UNKNOWN, installed=installed,
            detail="latest-release check skipped (--no-update-check).")

    try:
        result = cli_version.check_update()
    except Exception as exc:  # noqa: BLE001 - a probe must not take the report down with it
        return ComponentStatus(SPECTRA_CLI, UNKNOWN, installed=installed,
                               detail=f"the latest release could not be checked ({exc}).")

    installed = result.get("installed") or installed
    latest = result.get("latest")
    status = result.get("status")

    if status == "up_to_date":
        return ComponentStatus(SPECTRA_CLI, UP_TO_DATE, installed=installed, latest=latest)
    if status == "update_available":
        return ComponentStatus(SPECTRA_CLI, NEEDS_UPDATING, installed=installed, latest=latest)
    if status == "ahead":
        return ComponentStatus(SPECTRA_CLI, AHEAD, installed=installed, latest=latest)
    return ComponentStatus(SPECTRA_CLI, UNKNOWN, installed=installed,
                           detail="the latest release could not be fetched.")


# --------------------------------------------------------------------------- #
# 4 · Spectra agents (the extension in this project)
# --------------------------------------------------------------------------- #

def get_spectra_extension_status(project_state) -> ComponentStatus:
    """Resolve the installed extension against the published one.

    Takes the already-classified project state so the filesystem is read once per invocation rather
    than once per component.

    An `INCOMPLETE` install — the folder is present but carries no readable version — reports
    `NEEDS_UPDATING`, not `UNKNOWN`. What is unknown there is the *version*, not the verdict: a
    half-written install definitely needs fixing, and re-running the extension update is exactly the fix.
    Calling it unknown would make the walk skip the one component it could repair. This is the single
    documented case where `NEEDS_UPDATING` carries no `installed` version.
    """
    if project_state.state == project.INCOMPLETE:
        try:
            published = extension.published_version()
        except net.FetchError:
            published = None
        return ComponentStatus(
            SPECTRA_EXTENSION, NEEDS_UPDATING, installed=None, latest=published,
            detail="the extension folder is here but carries no readable version; "
                   "updating repairs it.")

    installed = project_state.installed_version
    if not installed:
        return ComponentStatus(SPECTRA_EXTENSION, UNKNOWN,
                               detail="no version could be read from the installed extension.")

    try:
        published = extension.published_version()
    except net.FetchError as exc:
        return ComponentStatus(SPECTRA_EXTENSION, UNKNOWN, installed=installed,
                               detail=f"the published version could not be fetched ({exc}).")

    verdict = extension.compare(installed, published)
    if verdict == extension.UP_TO_DATE:
        return ComponentStatus(SPECTRA_EXTENSION, UP_TO_DATE, installed=installed, latest=published)
    if verdict == extension.OUT_OF_DATE:
        return ComponentStatus(SPECTRA_EXTENSION, NEEDS_UPDATING, installed=installed,
                               latest=published)
    return ComponentStatus(SPECTRA_EXTENSION, AHEAD, installed=installed, latest=published)


# --------------------------------------------------------------------------- #
# The whole stack
# --------------------------------------------------------------------------- #

def check_all(project_state, *, skip_network: bool = False,
              timeout: int = SELF_CHECK_TIMEOUT) -> HealthReport:
    """Resolve all four components, in canonical order.

    Sequential rather than threaded. The integration genuinely depends on the CLI result, and the whole
    report costs one subprocess plus two bounded HTTP GETs — threading it to save a fraction of a second
    would buy interleaved output and harder tracebacks for no user-visible gain.
    """
    specify_status = get_specify_cli_status(timeout=timeout)
    return HealthReport([
        specify_status,
        get_integration_status(project_state.project_root, specify_status),
        get_spectra_cli_status(skip_network=skip_network),
        get_spectra_extension_status(project_state),
    ])


# --------------------------------------------------------------------------- #
# Bringing it current
# --------------------------------------------------------------------------- #

def _update_specify_cli() -> int:
    return extension.delegate_self_upgrade()


def _update_integration() -> int:
    return extension.delegate_integration_upgrade()


def _update_spectra_cli(component: ComponentStatus) -> int:
    # Raises UpdateError on failure rather than returning a code, so normalize to this walk's contract.
    cli_version.perform_update(component.latest)
    return 0


def _update_spectra_extension(assume_yes: bool = False) -> int:
    return extension.delegate_update(assume_yes=assume_yes)


# Keyed by component. Each takes the component plus whether the user has already consented, so the one
# delegate that faces an unskippable downstream prompt can answer it. ORDER sequences the walk.
_ACTIONS = {
    SPECIFY_CLI: lambda component, assume_yes=False: _update_specify_cli(),
    INTEGRATION: lambda component, assume_yes=False: _update_integration(),
    SPECTRA_CLI: lambda component, assume_yes=False: _update_spectra_cli(component),
    SPECTRA_EXTENSION: lambda component, assume_yes=False: _update_spectra_extension(assume_yes),
}

INTERRUPTED = 130


class Interrupted(Exception):
    """The user stopped a delegated command. Aborts the walk rather than recording a failure."""


def _skip_reason(component: ComponentStatus) -> str:
    if component.status == UP_TO_DATE:
        return "already up to date"
    if component.status == AHEAD:
        return "ahead of the published version"
    return "status could not be determined"


def apply_updates(report: HealthReport, *, announce=None, assume_yes: bool = False):
    """Update every component that needs it, in canonical order. Returns one result per component.

    Three properties, each required by the spec rather than chosen:

    * **Every component is visited.** A failure is recorded and the walk continues — "continue through
      partial failures" is the requirement, so one broken component cannot strand the rest.
    * **Skips are inert.** Anything not established as behind is never attempted and never influences
      the exit code, so an unknown component cannot turn a clean run into a failed one.
    * **Cancellation is not a failure.** Ctrl-C raises :class:`Interrupted` and stops the walk. The user
      asked us to stop touching their toolchain; pressing on to the next component would ignore that.

    `announce` is an optional callback invoked with each component about to be attempted, so the caller
    can narrate progress without this function knowing anything about presentation.

    `assume_yes` is passed to the delegates that face a prompt of their own. `specify extension update`
    asks for confirmation and offers no flag to skip it, so without this a non-interactive run would
    abort on that step alone.
    """
    results = []
    # Walk `report.components` rather than ORDER. Both are canonical order — `check_all` builds the
    # report from ORDER — but reading it from the report means the sequence updates run in *cannot*
    # drift from the sequence that was just shown to the user. One source, not two.
    for component in report.components:
        key = component.key
        if component.status != NEEDS_UPDATING:
            results.append(UpdateResult(key, SKIPPED, detail=_skip_reason(component)))
            continue

        if announce is not None:
            announce(component)

        action = _ACTIONS.get(key)
        if action is None:  # pragma: no cover - unreachable for the four known components
            results.append(UpdateResult(key, SKIPPED, detail="no update action for this component"))
            continue
        try:
            code = action(component, assume_yes)
        except extension.DelegationError as exc:
            results.append(UpdateResult(key, FAILED, detail=str(exc)))
            continue
        except cli_version.UpdateError as exc:
            results.append(UpdateResult(key, FAILED, detail=str(exc)))
            continue
        except KeyboardInterrupt:
            raise Interrupted(key)

        if code == INTERRUPTED:
            raise Interrupted(key)
        if code == 0:
            results.append(UpdateResult(key, UPDATED))
        else:
            results.append(UpdateResult(key, FAILED, detail=f"exited with code {code}"))
    return results
