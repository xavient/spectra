# Copyright 2026 TELUS Digital
# SPDX-License-Identifier: Apache-2.0

"""Which installed integrations have Spectra's commands, and how to give them to the ones that do not.

**The problem.** Spec Kit registers an extension's commands for the *active* integration only. A project
with `claude` and `kiro-cli` installed therefore gets Spectra's commands in whichever one happens to be the
default, and the developer using the other one has nothing and no explanation. Worse, updating the
extension unregisters it for *every* agent and re-registers it for the default alone, so coverage
established by hand is deleted by the next maintenance run (BRD-007 findings F1 and F5).

**The mechanism, and why it is the only one.** No command registers an extension for a *named* agent.
Activation — making an integration the project's default — is the sole supported trigger, and it
*accumulates*: activating a second agent leaves the first one's commands in place (F2, F6). So coverage is
a rotation: activate each uncovered integration in turn, then activate the original default again. That
last activation is both the restoration and, because activation registers, the default's own coverage
(research R3).

**The obligation.** The default integration is committed configuration shared by everyone who clones the
repository. It may move during a run, disclosed in advance, but the run must put it back — including after
a failed activation, an unexpected exception, and an interrupt. That is why the restore lives in a
``finally`` and why :class:`CoverageResult` reports it as a verdict of its own rather than as a boolean
(FR-015, FR-016, research R4).

**Why not in `health.py`.** That module answers *is each component current?* and every function in it is
shaped by version comparison. This one answers *is Spectra present for each agent?* — different inputs, a
different failure mode, and no version anywhere in it. It reuses `health.py`'s readers rather than
duplicating them, so the installed-integration list and the default are still read in exactly one place
(research R1).

Two rules hold everywhere below, both testable from outside:

* **Planning is pure.** :func:`plan` performs no writes, spawns no subprocess, and reads no terminal. Every
  interesting property — what will be activated, in what order, and what will be restored — is a property
  of a data structure.
* **Nothing here prompts, and nothing here forces.** The question belongs to the caller, and
  :func:`extension.delegate_integration_use` cannot express an overwrite (FR-009, FR-049).
"""

from __future__ import annotations

from spectra_cli import extension, health

# --------------------------------------------------------------------------- #
# Vocabulary
# --------------------------------------------------------------------------- #

# Per-integration coverage, as read before any work. UNKNOWN is a property of the whole project rather
# than of one integration: the registry either answers the question for every agent or for none.
COVERED = "covered"
UNCOVERED = "uncovered"
UNKNOWN = "unknown"

# What became of an integration during a rotation.
NEWLY_COVERED = "newly_covered"
ALREADY_COVERED = "already_covered"
FAILED = "failed"
SKIPPED = "skipped"

# What became of the project's default integration.
NOT_NEEDED = "not_needed"    # no activation ever moved it
RESTORED = "restored"        # it moved and was put back
NOT_RESTORED = "not_restored"  # it moved and could not be put back

# Skip reasons. Fixed wording: the tests assert on these, and a user reads them (data-model.md).
REASON_ALL_COVERED = "every integration already has Spectra's commands"
REASON_UNKNOWN = "the registration state could not be read"
REASON_NO_DEFAULT = "no default integration is recorded, so there would be nothing to restore"
REASON_NO_INTEGRATIONS = "no installed integrations are recorded for this project"
REASON_NOT_INSTALLED = "Spectra is not installed in this project"

# Verification wording for the one case a delegated success does not prove anything.
DETAIL_NO_REGISTRATION = "the activation reported success but no commands were registered"
DETAIL_NOT_REACHED = "not reached"

INTERRUPTED_CODE = 130


class Interrupted(Exception):
    """The user stopped the rotation. Raised only after the default has been restored."""


# --------------------------------------------------------------------------- #
# Structures
# --------------------------------------------------------------------------- #

class CoverageState:
    """One integration's coverage, as read before any work."""

    __slots__ = ("key", "covered", "is_default")

    def __init__(self, key, covered, *, is_default=False):
        self.key = key
        self.covered = bool(covered)
        self.is_default = bool(is_default)

    def __repr__(self):  # pragma: no cover - diagnostics only
        return (f"CoverageState({self.key!r}, covered={self.covered!r}, "
                f"is_default={self.is_default!r})")


class CoveragePlan:
    """What a run intends to do, as pure data.

    `targets` holds the uncovered integrations **excluding** the default, in the order the project records
    them. The default is not a target because the restoring activation covers it (research R3) — which is
    why `activations` appends it rather than the loop visiting it.
    """

    __slots__ = ("targets", "default_key", "default_uncovered", "states", "skip_reason",
                 "project_root")

    def __init__(self, targets=(), default_key=None, *, default_uncovered=False, states=(),
                 skip_reason=None, project_root=None):
        self.targets = tuple(targets)
        self.default_key = default_key
        self.default_uncovered = bool(default_uncovered)
        self.states = tuple(states)
        self.skip_reason = skip_reason
        # Carried so `apply` can re-read state for verification without the caller passing the root a
        # second time. It is where the plan was *read from*, and nothing here ever writes to it.
        self.project_root = project_root

    @property
    def needed(self) -> bool:
        """Whether there is any coverage work to do at all."""
        return bool(self.targets) or self.default_uncovered

    @property
    def moves_default(self) -> bool:
        """Whether this plan will change the project's default, even transiently.

        False when the only uncovered integration *is* the default: activating the key that is already
        active changes no configuration, so FR-013 forbids disclosing a transient default change for it.
        """
        return bool(self.targets)

    @property
    def activations(self) -> tuple:
        """Every integration this plan will activate, in order, ending with the default (FR-015)."""
        if not self.needed:
            return ()
        return self.targets + (self.default_key,)

    @property
    def uncovered_keys(self) -> tuple:
        """Every uncovered integration, default included — what the disclosure names."""
        return tuple(state.key for state in self.states if not state.covered)

    def __repr__(self):  # pragma: no cover - diagnostics only
        return (f"CoveragePlan(targets={self.targets!r}, default={self.default_key!r}, "
                f"default_uncovered={self.default_uncovered!r}, skip_reason={self.skip_reason!r})")


class CoverageOutcome:
    """What became of one integration during a rotation."""

    __slots__ = ("key", "outcome", "detail")

    def __init__(self, key, outcome, *, detail=None):
        self.key = key
        self.outcome = outcome
        self.detail = detail

    @property
    def failed(self) -> bool:
        return self.outcome == FAILED

    def __repr__(self):  # pragma: no cover - diagnostics only
        return f"CoverageOutcome({self.key!r}, {self.outcome!r}, detail={self.detail!r})"


class CoverageResult:
    """What happened. Shaped like `health.UpdateResult` so the outcome table can render it unchanged."""

    __slots__ = ("outcome", "detail", "parts", "restoration", "original_default", "current_default")

    def __init__(self, outcome, *, detail=None, parts=(), restoration=NOT_NEEDED,
                 original_default=None, current_default=None):
        self.outcome = outcome
        self.detail = detail
        self.parts = tuple(parts)
        self.restoration = restoration
        self.original_default = original_default
        self.current_default = current_default

    @property
    def failed(self) -> bool:
        return self.outcome == FAILED

    @property
    def newly_covered(self) -> tuple:
        return tuple(child.key for child in self.parts if child.outcome == NEWLY_COVERED)

    @property
    def left_uncovered(self) -> tuple:
        """Integrations this run did not manage to cover — what the closing advice names (FR-030)."""
        return tuple(child.key for child in self.parts
                     if child.outcome in (FAILED, SKIPPED))

    def __repr__(self):  # pragma: no cover - diagnostics only
        return (f"CoverageResult({self.outcome!r}, restoration={self.restoration!r}, "
                f"parts={len(self.parts)})")


# --------------------------------------------------------------------------- #
# Detection and planning
# --------------------------------------------------------------------------- #

def read_states(project_root):
    """`(states, skip_reason)` for this project — the raw reading, before any planning.

    Three reads, each already the single reader for its file: the recorded installed list, the recorded
    default, and the per-agent command registration. Nothing is inferred from a directory listing, because
    `.specify/integrations/` also holds shared infrastructure that is not an integration (FR-002).

    Returns `([], reason)` for every state in which there is nothing to plan against, and the reason is
    the user-facing wording. In particular `registered_agents()` returning None means *unknown* — absent,
    unreadable, no `spectra` entry, or an empty command map — and unknown must never be read as "nothing is
    covered", which would tell a healthy project it had a problem (FR-003, FR-004).
    """
    keys = health.read_installed_integrations(project_root)
    if not keys:
        return [], REASON_NO_INTEGRATIONS

    covered = extension.registered_agents(project_root)
    if covered is None:
        return [], REASON_UNKNOWN

    default = health.read_default_integration(project_root)
    states = [CoverageState(key, key in covered, is_default=(key == default)) for key in keys]
    return states, None


def plan(project_root, *, extension_present=True) -> CoveragePlan:
    """What this project needs, as pure data. Never writes, never spawns, never prompts.

    `extension_present` lets the install flow say "there is nothing installed to register", which is a
    different situation from "everything is covered" and gets its own reason (FR-022).

    Support for coverage is decided by the **presence of the state above**, never by the dependency's
    version number — so an older Spec Kit degrades to a stated skip rather than to a rotation that
    registers nothing, and there is no minimum-version constant to keep current (FR-051, research R2).
    """
    if not extension_present:
        return CoveragePlan(skip_reason=REASON_NOT_INSTALLED, project_root=project_root)

    states, reason = read_states(project_root)
    if reason is not None:
        return CoveragePlan(skip_reason=reason, project_root=project_root)

    uncovered = [state for state in states if not state.covered]
    if not uncovered:
        return CoveragePlan(states=states, skip_reason=REASON_ALL_COVERED,
                            project_root=project_root)

    default_key = next((state.key for state in states if state.is_default), None)
    if default_key is None:
        # Nothing to restore, so nothing may be activated. Reported rather than guessed at: inventing a
        # default would put words in the project's mouth about which agent it targets (FR-012).
        return CoveragePlan(states=states, skip_reason=REASON_NO_DEFAULT,
                            project_root=project_root)

    targets = [state.key for state in uncovered if state.key != default_key]
    default_uncovered = any(state.key == default_key for state in uncovered)
    return CoveragePlan(targets, default_key, default_uncovered=default_uncovered,
                        states=states, project_root=project_root)


# --------------------------------------------------------------------------- #
# The rotation
# --------------------------------------------------------------------------- #

def apply(plan_, *, announce=None) -> CoverageResult:
    """Cover every integration in `plan_`, then put the project's default back.

    **Every `return` and every `raise` below passes through the `finally`**, which is the only reason the
    restoration promise (FR-015, FR-016) holds. Two rules protect it, and both are easy to break by
    accident:

    * `moved` is set *immediately after* each activation returns — not only when it succeeded. A failed
      activation may still have changed the default, and skipping the restore in that case would leave the
      project pointing at an agent nobody chose.
    * The restoring activation is attempted **once**. A retry loop would turn one bad state into a longer
      one, and the recovery command printed by the caller is a better answer than trying again blindly.

    `announce` receives each integration key as its activation begins, so a caller can narrate progress
    without this module knowing anything about presentation. It is the only output path here.

    Raises :class:`Interrupted` — after restoring — when the user stops the run.
    """
    if not plan_.needed:  # pragma: no cover - callers gate on `needed`; guard against a future one
        raise ValueError("coverage.apply called with nothing to do")

    original_default = plan_.default_key
    attempted = {}
    moved = False
    interrupted = False

    try:
        for key in plan_.targets:
            if announce is not None:
                announce(key)
            try:
                code = extension.delegate_integration_use(key)
            except KeyboardInterrupt:
                moved = True
                interrupted = True
                break
            # Set before inspecting the code: see the docstring. A non-zero activation can still have
            # re-pointed the default before failing.
            moved = True
            if code == INTERRUPTED_CODE:
                interrupted = True
                break
            attempted[key] = code
    finally:
        restoration, current_default = _restore(plan_, moved, original_default)

    result = _build_result(plan_, attempted, restoration, original_default, current_default)
    if interrupted:
        raise Interrupted(result)
    return result


def _restore(plan_, moved, original_default):
    """Put the default back, and report which of the three things happened (research R4).

    `NOT_NEEDED` covers two distinct-looking cases that are the same thing: no activation at all, and the
    FR-013 case where the only activation was of the key that was *already* the default. Neither moved the
    project's configuration, so neither has anything to restore — and the caller must therefore print no
    restoration line for them.
    """
    if not moved:
        # The FR-013 case still needs its one activation: covering the default *is* activating it.
        if plan_.default_uncovered:
            code = _activate_quietly(original_default)
            if code != 0:
                return NOT_NEEDED, original_default
        return NOT_NEEDED, original_default

    code = _activate_quietly(original_default)
    if code == 0:
        return RESTORED, original_default
    return NOT_RESTORED, health.read_default_integration(plan_.project_root)


def _activate_quietly(key):
    """Activate `key`, converting a delegation failure into a code rather than an exception.

    The restore runs inside a `finally`. An exception raised there would replace whatever the run was
    already reporting — including an interrupt the user asked for — so every failure mode becomes a
    non-zero code and the caller decides what to say.
    """
    try:
        return extension.delegate_integration_use(key)
    except (extension.DelegationError, KeyboardInterrupt, OSError):
        return 1


def _build_result(plan_, attempted, restoration, original_default, current_default):
    """Verify against re-read state, then reduce everything to one result.

    **A delegated exit code never produces `NEWLY_COVERED` on its own.** Coverage is re-read from the
    registry, and a target still absent from it is reported `FAILED` whatever the command said — the same
    discipline feature 010 applies to a version that did not move (FR-006). The two failures are reported
    differently because they need different remedies: a non-zero code is the dependency's own failure, while
    a zero code with nothing registered means the two of us disagree about what happened.

    An unreadable registry after the rotation is not evidence of failure either: coverage becomes unknown
    again, so every attempted key that exited 0 is reported as newly covered rather than accused. Reporting
    a working project as broken because we lost the ability to look is the worse error.
    """
    covered_now = extension.registered_agents(plan_.project_root)
    children = []
    for state in plan_.states:
        key = state.key
        if state.covered:
            children.append(CoverageOutcome(key, ALREADY_COVERED))
            continue
        if key == plan_.default_key and key not in attempted:
            # Covered by the restoring activation rather than by the loop (research R3).
            children.append(_verify(key, 0 if restoration != NOT_RESTORED else 1, covered_now))
            continue
        if key not in attempted:
            children.append(CoverageOutcome(key, SKIPPED, detail=DETAIL_NOT_REACHED))
            continue
        children.append(_verify(key, attempted[key], covered_now))

    outcome, detail = _aggregate(children, restoration, plan_)
    return CoverageResult(outcome, detail=detail, parts=children, restoration=restoration,
                          original_default=original_default, current_default=current_default)


def _verify(key, code, covered_now):
    """One integration's outcome, decided by re-read state first and the exit code second."""
    if covered_now is not None and key in covered_now:
        return CoverageOutcome(key, NEWLY_COVERED)
    if code != 0:
        return CoverageOutcome(key, FAILED, detail=f"exited with code {code}")
    if covered_now is None:
        # Coverage became unknown; an exit 0 is the only evidence available and it is not contradicted.
        return CoverageOutcome(key, NEWLY_COVERED)
    return CoverageOutcome(key, FAILED, detail=DETAIL_NO_REGISTRATION)


def _aggregate(children, restoration, plan_):
    """`(outcome, detail)` for the whole run, by the precedence in contracts/coverage.md § 4."""
    if any(child.failed for child in children) or restoration == NOT_RESTORED:
        return FAILED, None
    if any(child.outcome == NEWLY_COVERED for child in children):
        return COVERED, None
    return SKIPPED, plan_.skip_reason or "nothing needed covering"
