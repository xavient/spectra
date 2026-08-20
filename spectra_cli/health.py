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

    `parts` carries the per-integration children of the `Core agents` row and is empty for the other
    three components. When it is populated, this row's `status`, `installed`, `latest`, and `detail` are
    all *derived* from it by :func:`aggregate_integration_status` — never set independently — so the row
    cannot disagree with its own children.
    """

    __slots__ = ("key", "installed", "latest", "status", "detail", "parts")

    def __init__(self, key, status, installed=None, latest=None, detail=None, parts=None):
        self.key = key
        self.status = status
        self.installed = installed
        self.latest = latest
        self.detail = detail
        self.parts = list(parts) if parts else []

    @property
    def label(self) -> str:
        return LABELS.get(self.key, self.key)

    @property
    def has_parts(self) -> bool:
        """Whether this row represents several things rather than one."""
        return bool(self.parts)

    @property
    def needs_updating(self) -> bool:
        return self.status == NEEDS_UPDATING

    @property
    def is_unknown(self) -> bool:
        return self.status == UNKNOWN

    def __repr__(self):  # pragma: no cover - diagnostics only
        return (f"ComponentStatus({self.key!r}, {self.status!r}, installed={self.installed!r}, "
                f"latest={self.latest!r}, parts={len(self.parts)})")


class IntegrationState:
    """One installed integration, and whether it is current.

    The unit of truth this feature adds. `key` is the integration's own key (`"kiro-cli"`, `"claude"`),
    and is `None` only in the single-record fallback, where the project records no key at all.

    Reuses `ComponentStatus`'s four-value vocabulary rather than inventing its own, so aggregation has
    nothing to translate. `detail` is required when `status` is :data:`UNKNOWN`, for the same reason it
    is on a component.

    `modified` distinguishes three states, and the distinction is load-bearing: `None` means *not
    established* (nobody asked, or the probe failed), `[]` means established as clean, and a non-empty
    list means these files would be overwritten. Only `spectra update` ever populates it — the report
    never runs the probe that fills it.
    """

    __slots__ = ("key", "installed", "latest", "status", "detail", "is_default", "modified")

    def __init__(self, key, status, installed=None, latest=None, detail=None,
                 is_default=False, modified=None):
        self.key = key
        self.status = status
        self.installed = installed
        self.latest = latest
        self.detail = detail
        self.is_default = is_default
        self.modified = modified

    @property
    def label(self) -> str:
        """What to call this integration in output. The key is already the user's own word for it."""
        return self.key or LABELS[INTEGRATION]

    @property
    def needs_updating(self) -> bool:
        return self.status == NEEDS_UPDATING

    def __repr__(self):  # pragma: no cover - diagnostics only
        return (f"IntegrationState({self.key!r}, {self.status!r}, installed={self.installed!r}, "
                f"latest={self.latest!r}, is_default={self.is_default!r})")


class ModificationReport:
    """Which managed files diverge from what was installed, per integration and for shared files.

    Built once per `spectra update` run and discarded. `established` is `False` when the probe could not
    be run or parsed at all — and that is not the same as "nothing is modified": not knowing what would
    be overwritten is precisely the state in which overwriting must not be authorized.
    """

    __slots__ = ("per_integration", "shared", "established", "detail")

    def __init__(self, per_integration=None, shared=None, established=True, detail=None):
        self.per_integration = dict(per_integration or {})
        self.shared = list(shared or [])
        self.established = established
        self.detail = detail

    def files_for(self, key):
        """The modified files recorded for `key`, or an empty list."""
        return list(self.per_integration.get(key, []))

    def __repr__(self):  # pragma: no cover - diagnostics only
        return (f"ModificationReport(established={self.established!r}, "
                f"per_integration={ {k: len(v) for k, v in self.per_integration.items()} }, "
                f"shared={len(self.shared)})")


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

    `parts` carries one child result per attempted integration for the `Core agents` component, and is
    empty for the other three. A child's `key` is the integration's own key, so its `label` is that key —
    which is the word the user already uses for it. The parent's `outcome` is the **worst** of its
    children (:data:`FAILED` > :data:`UPDATED` > :data:`SKIPPED`), so one failed integration reaches the
    exit code while a component of only skips stays inert.
    """

    __slots__ = ("key", "outcome", "detail", "parts")

    def __init__(self, key, outcome, detail=None, parts=None):
        self.key = key
        self.outcome = outcome
        self.detail = detail
        self.parts = list(parts) if parts else []

    @property
    def label(self) -> str:
        return LABELS.get(self.key, self.key)

    @property
    def failed(self) -> bool:
        return self.outcome == FAILED

    def __repr__(self):  # pragma: no cover - diagnostics only
        return f"UpdateResult({self.key!r}, {self.outcome!r}, detail={self.detail!r})"


def worst_outcome(outcomes):
    """The most serious outcome in `outcomes`, ordered FAILED > UPDATED > SKIPPED.

    A pure function so the roll-up rule is stated once and testable without a walk. An empty sequence is
    :data:`SKIPPED`: a component with nothing attempted has, correctly, attempted nothing.
    """
    outcomes = list(outcomes)
    if FAILED in outcomes:
        return FAILED
    if UPDATED in outcomes:
        return UPDATED
    return SKIPPED


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
INTEGRATIONS_DIR = "integrations"

# The record that lives beside the per-integration manifests but is **not** an integration: it tracks the
# shared scripts and templates every integration uses. Named here so both the enumeration and the
# modification report exclude it deliberately rather than by accident.
SHARED_KEY = "speckit"


def _read_json_object(path):
    """The JSON object at `path`, or None if it cannot be read as one.

    Missing file, unreadable file, invalid JSON, and a non-object top level all return None on purpose:
    to every caller here they are one situation — the file cannot be trusted to report what it says — and
    they share one remedy.
    """
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _recorded_version(data):
    """The `version` string in an already-parsed record, or None when absent or empty."""
    if not isinstance(data, dict):
        return None
    recorded = data.get("version")
    if not isinstance(recorded, str):
        return None
    return recorded.strip() or None


def read_integration_version(project_root, key=None):
    """The version recorded for one integration, or for the project as a whole.

    Two sources, one question — *what version is installed here?* — and which one answers it depends on
    whether a `key` is given:

    * ``key`` given -> ``.specify/integrations/<key>.manifest.json``, the integration's **own** record.
      This is the authoritative per-integration version and the only place it exists.
    * ``key`` omitted -> ``.specify/integration.json``, the **project-level** record. Used by the
      single-record fallback only, because Spec Kit rewrites it to the current CLI version whenever
      *any* integration is upgraded — so it cannot represent a project where one integration is stale
      and another is not.

    Every failure mode returns None: missing, unreadable, invalid JSON, non-object, absent or empty
    `version`. To the caller they are one situation with one remedy.
    """
    if project_root is None:
        return None
    if key is None:
        return _recorded_version(_read_json_object(project_root / ".specify" / INTEGRATION_FILE))
    path = project_root / ".specify" / INTEGRATIONS_DIR / f"{key}.manifest.json"
    return _recorded_version(_read_json_object(path))


def read_installed_integrations(project_root):
    """The integration keys this project records as installed, or None meaning *fall back*.

    Read from `installed_integrations` in `.specify/integration.json` with order preserved.

    **Never inferred from the filesystem.** `.specify/integrations/` also holds `speckit.manifest.json`,
    which is shared infrastructure rather than an integration, so a reader that enumerated that directory
    would invent an integration that does not exist. The recorded list is the membership, full stop.

    Returns None — rather than an empty list — for every state in which membership cannot be established:
    no file, unreadable file, no such key, not a list, or a list with nothing usable in it. None is the
    signal to fall back to the single-record path, and it is deliberately distinct from "a list that
    happens to be empty", which would mean the same thing but say it less clearly.
    """
    if project_root is None:
        return None
    data = _read_json_object(project_root / ".specify" / INTEGRATION_FILE)
    if data is None:
        return None
    recorded = data.get("installed_integrations")
    if not isinstance(recorded, list):
        return None
    keys = [key.strip() for key in recorded if isinstance(key, str) and key.strip()]
    keys = [key for key in keys if key != SHARED_KEY]
    return keys or None


def read_default_integration(project_root):
    """The project's default integration key, or None when none is recorded.

    Reads `default_integration`, falling back to the legacy `integration` key that older projects carry.
    None is returned rather than guessing at the first installed key: the default decides walk position
    and whether the coverage advisory can name a remedy, and inventing one would put words in the
    project's mouth.
    """
    if project_root is None:
        return None
    data = _read_json_object(project_root / ".specify" / INTEGRATION_FILE)
    if data is None:
        return None
    for field in ("default_integration", "integration"):
        value = data.get(field)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _integration_verdict(recorded, specify_status, key=None):
    """`(status, latest, detail)` for one integration recorded at `recorded`.

    The same two-way reasoning the single-record check has always used, factored out so it is applied
    identically to one integration or to five:

    * **the CLI is behind** — a record can only ever say what the *old* CLI installed, so the integration
      is behind too, whatever it says. Its target is then the CLI's own latest, so the row reads the
      transition the upgrade will actually produce.
    * **the CLI is current but the record disagrees** — the CLI was upgraded and the integration upgrade
      was never re-run. Locally detectable, and invisible before this feature.
    """
    if specify_status.status == UNKNOWN:
        return (UNKNOWN, None,
                "the Specify CLI version is unknown, so there is nothing to compare against.")
    if recorded is None:
        where = (f"the manifest for '{key}'" if key
                 else f".specify/{INTEGRATION_FILE}")
        return UNKNOWN, None, f"no usable version in {where}."
    if specify_status.status == NEEDS_UPDATING:
        return (NEEDS_UPDATING, specify_status.latest,
                "the Specify CLI is behind, and the integration tracks it.")

    installed_cli = specify_status.installed
    comparison = cli_version.compare_versions(recorded, installed_cli or "")
    if comparison < 0:
        return (NEEDS_UPDATING, installed_cli,
                "the Specify CLI was upgraded but the integration was not re-run.")
    if comparison > 0:
        return (AHEAD, installed_cli,
                "the integration is newer than the Specify CLI installed here.")
    return UP_TO_DATE, installed_cli, None


def get_integration_states(project_root, specify_status):
    """One :class:`IntegrationState` per installed integration, or `[]` to mean *fall back*.

    A key recorded as installed but carrying no readable manifest is still returned — as `UNKNOWN` — rather
    than dropped. A recorded-but-broken integration is exactly the thing a user needs told about, and
    silently omitting it would shrink the report to the integrations that happen to be healthy.
    """
    keys = read_installed_integrations(project_root)
    if not keys:
        return []
    default = read_default_integration(project_root)
    states = []
    for key in keys:
        recorded = read_integration_version(project_root, key)
        status, latest, detail = _integration_verdict(recorded, specify_status, key=key)
        states.append(IntegrationState(key, status, installed=recorded, latest=latest,
                                       detail=detail, is_default=(key == default)))
    return states


def _oldest(versions):
    """The lowest version in `versions`, ignoring None. None when there is nothing to compare."""
    readable = [v for v in versions if v]
    if not readable:
        return None
    oldest = readable[0]
    for candidate in readable[1:]:
        if cli_version.compare_versions(candidate, oldest) < 0:
            oldest = candidate
    return oldest


def aggregate_integration_status(states, specify_status) -> ComponentStatus:
    """Derive the one `Core agents` row from its per-integration children.

    A pure function, so the precedence below is stated once and testable without a project on disk.
    Evaluated top to bottom, first match wins:

    1. **no integrations** -> `UNKNOWN`. Nothing was enumerated, so nothing is known.
    2. **any child behind** -> `NEEDS_UPDATING`. Outranks unknown deliberately: a behind integration is
       *actionable*, and an unreadable sibling must not hide work that can be done.
    3. **any child unknown** -> `UNKNOWN`. Outranks both currency verdicts, because the row must never
       claim a currency it has not established (FR-006 permits `UP_TO_DATE` only when **every**
       integration is current, and an unknown one is not current — it is unknown).
    4. **every child ahead** -> `AHEAD`.
    5. **otherwise** -> `UP_TO_DATE`, which covers all-current and a mix of current and ahead. "Ahead" is
       a flavour of not-behind, and this row answers "is anything stale here?".

    The row's version is the **oldest readable** child version: "is my stack current?" is answered by the
    weakest link, and an unreadable child contributes no version to that comparison (it is reported
    through rule 3 instead).
    """
    states = list(states)

    # The single-record fallback: one unnamed child, whose fields *are* the row's. Kept verbatim rather
    # than routed through the rules below so the older layout's wording is unchanged.
    if len(states) == 1 and states[0].key is None:
        only = states[0]
        return ComponentStatus(INTEGRATION, only.status, installed=only.installed,
                               latest=only.latest, detail=only.detail, parts=states)

    if not states:
        return ComponentStatus(
            INTEGRATION, UNKNOWN,
            detail="no installed integrations are recorded for this project.")

    oldest = _oldest(state.installed for state in states)
    behind = [state for state in states if state.status == NEEDS_UPDATING]
    if behind:
        target = _oldest(state.latest for state in behind) or specify_status.installed
        names = ", ".join(state.key for state in behind)
        return ComponentStatus(INTEGRATION, NEEDS_UPDATING, installed=oldest, latest=target,
                               detail=f"behind: {names}.", parts=states)

    unknown = [state for state in states if state.status == UNKNOWN]
    if unknown:
        names = ", ".join(state.key for state in unknown)
        return ComponentStatus(
            INTEGRATION, UNKNOWN, installed=oldest, latest=specify_status.installed,
            detail=f"the state of {names} could not be established.", parts=states)

    if all(state.status == AHEAD for state in states):
        return ComponentStatus(INTEGRATION, AHEAD, installed=oldest,
                               latest=specify_status.installed, parts=states)

    return ComponentStatus(INTEGRATION, UP_TO_DATE, installed=oldest,
                           latest=specify_status.installed, parts=states)


def get_integration_status(project_root, specify_status: ComponentStatus) -> ComponentStatus:
    """Resolve the integration component, given the already-resolved Specify CLI status.

    Cannot be evaluated independently. A recorded version means "the Spec Kit that installed this", so it
    is only meaningful against a known CLI version — hence an unknown CLI forces an unknown integration
    rather than a guess from the files alone.

    **Plural first, singular as a fallback.** Every installed integration is enumerated and judged on its
    own manifest, and the row is derived from all of them. Only when membership cannot be established —
    or when nothing it names has a readable manifest — does this fall back to the project-level `version`
    field and today's single-integration behaviour. The fallback is detected by *absence of data*, never
    by comparing `specify` version numbers, so it also covers a layout that predates per-integration
    records without a constant to keep up to date.
    """
    states = get_integration_states(project_root, specify_status)
    if states and any(state.installed for state in states):
        return aggregate_integration_status(states, specify_status)

    recorded = read_integration_version(project_root)
    status, latest, detail = _integration_verdict(recorded, specify_status)
    only = IntegrationState(None, status, installed=recorded, latest=latest, detail=detail,
                            is_default=True)
    return aggregate_integration_status([only], specify_status)


# --------------------------------------------------------------------------- #
# What has diverged (the update path only)
# --------------------------------------------------------------------------- #

# How long `specify integration status --json` gets. It only reads local files and hashes them, so this
# is generous; the bound exists so a hung child cannot hang the update.
STATUS_TIMEOUT = 20


def modification_report(project_root=None, timeout: int = STATUS_TIMEOUT) -> ModificationReport:
    """Which managed files diverge from what was installed. Never raises.

    Asks `specify integration status --json`, which is read-only and exits 0 in every state — including
    the one where it reports its own `warning` — so **the exit code is not the signal**; the parsed
    payload is. The human-formatted table is never read: a machine-readable form exists, and decisions
    that can destroy a file must not depend on prose that is free to be reworded.

    This is the one input `spectra version` never gathers. It costs a subprocess, and the report has no
    use for it — only an update that is about to overwrite something does.

    `established=False` covers every way the answer could not be obtained: no `specify`, a timeout, a
    non-zero exit, unparseable output. It is deliberately distinct from "nothing is modified", because not
    knowing what would be overwritten is precisely the state in which nothing may be overwritten.

    The shared-infrastructure record (`speckit`) is routed to `shared` rather than treated as an
    integration, and any key the project does not record as installed is ignored — the same rule the
    enumeration follows, applied to the same trap.
    """
    if not specify_available():
        return ModificationReport(established=False,
                                  detail="`specify` is not on PATH, so modification state is unknown.")
    try:
        proc = subprocess.run(["specify", "integration", "status", "--json"],
                              capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return ModificationReport(established=False,
                                  detail=f"`specify integration status` did not finish within {timeout}s.")
    except OSError as exc:
        return ModificationReport(established=False,
                                  detail=f"`specify integration status` could not be run ({exc}).")
    if proc.returncode != 0:
        return ModificationReport(
            established=False,
            detail=f"`specify integration status` exited with code {proc.returncode}.")
    try:
        data = json.loads(proc.stdout or "")
    except ValueError:
        return ModificationReport(
            established=False,
            detail="`specify integration status --json` did not print JSON this version understands.")
    if not isinstance(data, dict):
        return ModificationReport(established=False,
                                  detail="`specify integration status --json` printed no object.")

    recorded = read_installed_integrations(project_root) if project_root is not None else None
    manifests = data.get("manifests")
    manifests = manifests if isinstance(manifests, dict) else {}

    per_integration, shared = {}, []
    for key, entry in manifests.items():
        if not isinstance(entry, dict):
            continue
        files = [f for f in (entry.get("modified_files") or []) if isinstance(f, str)]
        if not files:
            continue
        if key == SHARED_KEY:
            shared = files
        elif recorded is None or key in recorded:
            per_integration[key] = files
    return ModificationReport(per_integration=per_integration, shared=shared, established=True)

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


def _update_integration(component: ComponentStatus, authorized_keys) -> UpdateResult:
    """Upgrade every behind integration in `component`, one child result each.

    Ordering is the one design decision here: **non-default integrations first, the default last**.
    Upgrading a non-default key installs shared infrastructure aligned to the *default*, while upgrading
    the default key refreshes it as its own and re-registers extension and preset commands. Ending on the
    default therefore makes the last write to shared infrastructure the correct one, rather than leaving a
    non-default upgrade to overwrite it.

    `force` is never inferred here. It is set only for keys the caller has already collected an
    authorization act for, so this function cannot become a second route to an overwrite.
    """
    # The single-record fallback: one unnamed integration, upgraded bare and reported as one row with no
    # children. Byte-identical to the behaviour before this feature existed, which is what FR-012 asks of
    # every project that has not recorded per-integration state.
    if len(component.parts) == 1 and component.parts[0].key is None:
        code = extension.delegate_integration_upgrade()
        if code == INTERRUPTED:
            raise Interrupted(INTEGRATION)
        if code == 0:
            return UpdateResult(INTEGRATION, UPDATED)
        return UpdateResult(INTEGRATION, FAILED, detail=f"exited with code {code}")

    targets = [state for state in component.parts if state.status == NEEDS_UPDATING]
    targets.sort(key=lambda state: bool(state.is_default))

    children = []
    for state in component.parts:
        if state.status != NEEDS_UPDATING:
            children.append(UpdateResult(state.key, SKIPPED, detail=_skip_reason(state)))

    for state in targets:
        if state.key is not None and state.key in _blocked_keys(component, authorized_keys):
            children.append(UpdateResult(state.key, SKIPPED, detail="overwrite not authorized"))
            continue
        force = bool(state.key and state.key in authorized_keys)
        code = extension.delegate_integration_upgrade(state.key, force=force)
        if code == INTERRUPTED:
            raise Interrupted(INTEGRATION)
        if code == 0:
            children.append(UpdateResult(state.key, UPDATED))
        else:
            children.append(UpdateResult(state.key, FAILED, detail=f"exited with code {code}"))

    # Report children in the order the report showed them, not the order they were attempted: the reader
    # is matching this table against the one above it.
    order = {state.key: index for index, state in enumerate(component.parts)}
    children.sort(key=lambda child: order.get(child.key, 0))
    outcome = worst_outcome(child.outcome for child in children)
    # A plural row needs its own reason when nothing was attempted, or it renders as `skipped (None)`.
    detail = None
    if outcome == SKIPPED:
        detail = ("no integration was upgraded" if any(child.detail for child in children)
                  else _skip_reason(component))
    return UpdateResult(INTEGRATION, outcome, detail=detail, parts=children)


def _blocked_keys(component: ComponentStatus, authorized_keys):
    """Behind integrations with modified files that were **not** authorized for overwrite.

    `modified` is only ever populated on the update path, and only for integrations the run is about to
    upgrade, so an integration nobody asked about can never land here.
    """
    return {state.key for state in component.parts
            if state.status == NEEDS_UPDATING and state.modified
            and state.key not in authorized_keys}


def _update_spectra_cli(component: ComponentStatus) -> int:
    # Raises UpdateError on failure rather than returning a code, so normalize to this walk's contract.
    cli_version.perform_update(component.latest)
    return 0


def _update_spectra_extension(assume_yes: bool = False) -> int:
    return extension.delegate_update(assume_yes=assume_yes)


# Keyed by component. Each takes the component plus whether the user has already consented, so the one
# delegate that faces an unskippable downstream prompt can answer it. ORDER sequences the walk.
# `INTEGRATION` is absent on purpose: it is plural, so it returns a whole `UpdateResult` with children
# rather than a single exit code, and is dispatched separately in `apply_updates`.
_ACTIONS = {
    SPECIFY_CLI: lambda component, assume_yes=False: _update_specify_cli(),
    SPECTRA_CLI: lambda component, assume_yes=False: _update_spectra_cli(component),
    SPECTRA_EXTENSION: lambda component, assume_yes=False: _update_spectra_extension(assume_yes),
}

INTERRUPTED = 130


class Interrupted(Exception):
    """The user stopped a delegated command. Aborts the walk rather than recording a failure."""


def _skip_reason(component) -> str:
    if component.status == UP_TO_DATE:
        return "already up to date"
    if component.status == AHEAD:
        return "ahead of the published version"
    return "status could not be determined"


def apply_updates(report: HealthReport, *, announce=None, assume_yes: bool = False,
                  authorized_keys=None):
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

    `authorized_keys` is the set of integration keys the caller has obtained an overwrite authorization
    for, in this run. **This function never resolves authorization itself** — it does not prompt, read a
    TTY, or consult a flag — so it stays testable without a terminal and there is exactly one place where
    an overwrite can be authorized.
    """
    authorized_keys = set(authorized_keys or ())
    results = []
    # Walk `report.components` rather than ORDER. Both are canonical order — `check_all` builds the
    # report from ORDER — but reading it from the report means the sequence updates run in *cannot*
    # drift from the sequence that was just shown to the user. One source, not two.
    for component in report.components:
        key = component.key

        # The integration component is plural: it may have work to do for some of its children while
        # others are current, so its own status is not the whole story.
        if key == INTEGRATION and component.has_parts:
            if any(state.status == NEEDS_UPDATING for state in component.parts):
                if announce is not None:
                    announce(component)
                try:
                    results.append(_update_integration(component, authorized_keys))
                except extension.DelegationError as exc:
                    results.append(UpdateResult(key, FAILED, detail=str(exc)))
                except KeyboardInterrupt:
                    raise Interrupted(key)
            else:
                results.append(UpdateResult(key, SKIPPED, detail=_skip_reason(component)))
            continue

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
