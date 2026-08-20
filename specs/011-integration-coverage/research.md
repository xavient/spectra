# Phase 0 — Research: Full Integration Coverage on Install and Update

Twelve decisions. Each is stated as decision / rationale / alternatives, and each is traceable to a
requirement in [spec.md](spec.md). Five are load-bearing — R1, R3, R4, R6, R9 — in that a different
answer would change the module layout, the observable behaviour, or the test strategy.

The dependency behaviours these decisions rest on were verified against **Spec Kit CLI 0.16.5** and are
recorded as F1–F9 in BRD-007 § 2.1. They are cited here, not restated.

---

## R1 — Coverage lives in a new module, not in `health.py`

**Decision**: add `spectra_cli/coverage.py`. It owns coverage detection, the plan, the rotation, the
restoration obligation, and the verification pass. It reads the installed-integration list and the
default through `health.py`'s existing readers, and the per-agent registration through
`extension.registered_agents`.

**Rationale**: `health.py` answers one question — *is each component of the stack current?* — and every
function in it is shaped by version comparison. Coverage is a different question with different inputs
(registration, not versions) and a different failure mode (a missing command file, not a stale one). It
is also the largest module in the package already. Putting a second question inside it would make the
one module that decides "current" also decide "present", and the two would start sharing helpers that
mean subtly different things.

**Alternatives considered**:
- *Extend `health.py`* — rejected for the reasons above. The one thing genuinely shared is the readers,
  and importing them is cheaper than merging the concerns.
- *Put it in `install.py`* — rejected: `spectra update` needs it too (FR-024), and `install.py` is the
  install flow rather than a library.
- *Duplicate the readers in `coverage.py`* — rejected outright. Two readers of
  `.specify/integration.json` is exactly the drift this repository has already paid for once.

---

## R2 — Plan and execute are separate, and the plan is pure

**Decision**: `coverage.plan(project_root)` returns a `CoveragePlan` and performs no side effects, reads
no terminal, and invokes no subprocess. `coverage.apply(plan, announce=…)` performs the rotation and
returns a `CoverageResult`. Prompting lives in `cli.py`; `apply` never asks anything.

**Rationale**: it makes the two claims that matter *inspectable*. "Nothing is activated unless it was in
the plan" and "the default in the plan is the one restored" are assertions against a data structure,
testable without a TTY, a stub, or a filesystem. It is also the shape feature 010 already established
with `OverwritePlan` / `apply_updates`, so a reader who knows one knows the other.

**Alternatives considered**:
- *One function that decides and acts* — rejected: the interesting properties then only exist at
  runtime, and every test needs a working `specify` stub.
- *Return a callable closure* — rejected as cleverness with no benefit over data plus a function.

---

## R3 — The rotation covers non-default integrations first, and the restore covers the default

**Decision**: targets are the uncovered integrations **excluding the default**, in the order the project
records them. After the last one, the run activates the **original default** once. That activation is
simultaneously the restoration (FR-015) and, per F2, the registration pass that covers the default if it
was uncovered.

Consequences, all of which the contract states explicitly:
- A project whose default is the *only* uncovered integration performs **one** activation — of the
  default, which is already active — so nothing about the configuration changes and no
  transient-default disclosure is made (FR-013).
- A single-integration project that is uncovered is the same case, which is why FR-013 and FR-038 do not
  conflict.
- The default is never reported as covered on the strength of the restore alone: verification re-reads
  the registry afterwards (FR-006), so a restore that failed to register cannot report coverage.

**Rationale**: the restore has to happen anyway, and it is an activation, and activation registers. Any
design that covered the default with its own separate activation would do the same work twice and
introduce an ordering where the last write to shared infrastructure is not the default's — the very
problem feature 010 solved by ending its walk on the default.

**Alternatives considered**:
- *Cover the default first, then the others, then restore* — rejected: three or more activations where
  two suffice, and the final restore would overwrite shared infrastructure aligned to a non-default
  integration.
- *Skip the restore when the default was already covered* — rejected: the restore is not an optimization,
  it is the promise (FR-015). Skipping it in a subset of cases would create a path where the default is
  left changed.
- *Order targets by anything other than the recorded order* — rejected as unmotivated; F2 makes the
  order irrelevant to the outcome, so the recorded order is chosen for reproducible output.

---

## R4 — Restoration is a `finally`-block obligation with three distinguishable outcomes

**Decision**: the rotation body runs inside `try` / `finally`. The `finally` attempts the restore
whenever the run has activated anything, including after an activation failure, after an unexpected
exception, and after `KeyboardInterrupt`. The result records one of:

| Restoration verdict | Meaning |
| --- | --- |
| `NOT_NEEDED` | no activation ever moved the default (single-integration or default-only case) |
| `RESTORED` | the default was moved and the restoring activation succeeded |
| `NOT_RESTORED` | the default was moved and the restoring activation failed or was interrupted |

`NOT_RESTORED` is what FR-034 reports on, and it is the only state that prints the verbatim recovery
command.

**Rationale**: FR-016 is unconditional, so the restore cannot live on the success path. Three verdicts
rather than a boolean because "we never moved it" and "we moved it and put it back" must not read the
same in the output — the second deserves the confirmation FR-033 requires, the first must print nothing
at all (FR-038).

**Alternatives considered**:
- *Register an interpreter-exit handler* — rejected: it would fire after the command has already printed
  its summary, so the user would be told the default was restored before it was.
- *Restore before each next activation instead of once at the end* — rejected: N extra activations, and a
  crash still leaves the default moved.
- *Treat `KeyboardInterrupt` as "stop immediately, restore nothing"* — rejected: it leaves committed
  configuration pointing at an agent nobody chose, which is the exact harm Story 4 exists to prevent.

---

## R5 — One new delegation, and it may never carry an overwrite flag

**Decision**: add `extension.delegate_integration_use(key)` → `specify integration use <key>`. It takes
no `force` parameter — not one defaulting to `False`, none at all — so there is no signature by which a
future caller could pass one.

**Rationale**: F4 established that activation preserves locally modified managed files and succeeds with
a warning, so coverage never needs the overwrite. FR-009 and FR-049 make that a rule rather than a
happy accident, and the cheapest enforcement is a function that cannot express the request. Feature 010
had to document at length that exactly one call site may pass `force=True`; this feature keeps that
guarantee by construction.

**Alternatives considered**:
- *Reuse `delegate_integration_upgrade`* — rejected: different subcommand, different semantics, and it
  *does* accept `force`.
- *Add `force=False` for symmetry* — rejected. Symmetry is not a reason to open the one door the spec
  says must stay shut.

---

## R6 — "Already installed" is detected by project state, before the attempt

**Decision**: before invoking `specify extension add <id>`, check whether that extension is already
present in the project (`.specify/extensions/<id>/` exists). If it is, skip the add, report the extension
as already present, and continue to the coverage step. If it is not, attempt the add as today; a non-zero
exit is then a genuine failure.

**Rationale**: FR-021 forbids matching the dependency's message text, and a post-hoc classification
cannot distinguish "refused because already installed" from "download failed while an older copy is
present" — both leave the project classified as installed. Deciding *before* the attempt removes the
ambiguity entirely: the only way to reach a non-zero add is to have attempted an install of something
that was absent.

It also satisfies FR-023 for free — nothing is removed, re-downloaded, or overwritten — and keeps
updating an installed extension where it belongs, in `spectra update`.

**Consequences**:
- An `INCOMPLETE` extension folder (present but no readable version) is treated as **absent** for this
  decision, so the add is attempted. If the dependency then refuses, the run reports the failure and
  points at `spectra update`, which is the documented repair for that state.
- The check is per extension id, because the catalog may advertise more than one (`catalog_extension_ids`).
  `project.classify()` stays Spectra-specific and is not overloaded for this.

**Alternatives considered**:
- *Parse the dependency's "already installed" message* — rejected by FR-021, and it is a localized
  human-facing string.
- *Pass the dependency's overwrite flag to make the add idempotent* — rejected: it would re-extract the
  extension and could discard a user's extension config, and FR-023 forbids it.
- *Classify after a failed add* — rejected as shown above: it cannot tell the two failures apart.

---

## R7 — Where the coverage step sits in each command

**Decision**:

- **`spectra install`** — a new step **4 of 4**, after the catalog and extension work. It discloses and
  proceeds (FR-018); it does not ask.
- **`spectra update`** — after the component walk and after the post-walk re-read, before the outcome
  table is rendered. The question is asked there; the outcomes then appear as a **fifth row group** in
  the same outcome table, one child line per integration (FR-032, Story 2 scenario 7).

**Rationale**: coverage must be evaluated after the extension work in both commands, because in the
update it is the extension update that destroys coverage (F5) — evaluating first would plan against a
state the run is about to invalidate. Asking before the table keeps every question in the run ahead of
every result, which is the order the update already uses for its plan confirmation and its overwrite
gate.

**Explicitly not done**: no fifth row is added to the **health table** that `spectra version` and the
head of `spectra update` render. That table reports currency verdicts for four components, and feature
010 deliberately kept coverage out of it as an advisory below the rows. The outcome table is a different
table with a different job — it reports work performed — and coverage work belongs in it.

**Alternatives considered**:
- *Fold coverage into the update plan the user confirms up front* — rejected in clarification: the plan
  is about versions, and one answer must not cover two different kinds of change.
- *Print coverage outcomes in their own block below the table* — rejected as weaker than the table for
  scanning, and Story 2 scenario 7 asks for them alongside the component results.
- *Run coverage before the walk in the update* — rejected: F5 means the walk would then undo it.

---

## R8 — Exit codes reuse the existing vocabulary

**Decision**: no new exit code. Mapping:

| Situation | Code | Constant |
| --- | --- | --- |
| coverage completed, or skipped with a stated reason | 0 | `EXIT_OK` |
| coverage attempted and an activation failed | 4 | `EXIT_DELEGATION` |
| the restoring activation failed (`NOT_RESTORED`) | 4 | `EXIT_DELEGATION` |
| interrupted during the rotation | 130 | `EXIT_INTERRUPTED` |
| the update's coverage question declined | unchanged | — |

**Rationale**: the clarified contract (spec § Clarifications) distinguishes attempt from abstention, and
`EXIT_DELEGATION` already means "a delegated `specify` command failed", which is precisely what a failed
activation is. Inventing a coverage-specific code would add a number to the CLI's vocabulary for a case
the vocabulary already covers.

**Alternatives considered**:
- *A dedicated code* — rejected as above.
- *`EXIT_PROJECT_STATE` for `NOT_RESTORED`* — rejected: the project state is a *consequence* of the
  failed delegation, not the cause, and the remedy printed is a command to run, not a state to fix.

---

## R9 — The byte-for-byte restoration claim is enforced by an end-to-end test

**Decision**: no run-time comparison of configuration files. Instead, the containerized harness gains a
scenario that snapshots `.specify/integration.json` and `.specify/init-options.json` byte-for-byte
before a coverage run against a **real** Spec Kit, and fails if either differs afterwards. If that test
cannot be made to pass, FR-044's fallback applies: name the affected files in the disclosure and make
the step declinable, including in the install.

**Rationale**: FR-044 requires a textual difference to be *eliminated*, which is a release-time
obligation, not a runtime behaviour. A run-time comparison could only report the problem after the fact
— the bytes are written by the dependency, and rewriting them ourselves is forbidden (FR-007). The
observed behaviour in the BRD probe was a clean return to the original values (F3), so the expected
outcome is a passing test that then guards the claim.

**Alternatives considered**:
- *Snapshot and restore the files ourselves* — rejected by FR-007: Spectra does not write the
  dependency's records.
- *Compare at run time and abort on difference* — rejected: it aborts after the damage, and it converts a
  cosmetic difference into a failed command.
- *Accept semantic equivalence and move on* — rejected in clarification: committed-configuration noise is
  the objection the disclosure exists to prevent.

---

## R10 — The `specify` stub gains an argv log and a side effect

**Decision**: extend `tests/helpers.py::fake_specify` with

1. an **argv log** — every invocation appended to a file the test can read, so the rotation's order and
   the presence of the restoring call are assertable exactly; and
2. an optional **`integration use` side effect** — when enabled, the stub rewrites
   `.specify/extensions/.registry` to add the activated key and rewrites `default_integration` in
   `.specify/integration.json`, so post-rotation verification (FR-006) and the restore are exercised
   against changing state rather than a frozen fixture.

**Rationale**: the existing stub answers `self check` and `integration status --json` and exits 0 for
everything else. Against that stub a rotation "succeeds" without any state changing, so verification
would pass vacuously and a bug in the restore would be invisible. The log makes order assertable without
parsing human output; the side effect makes verification meaningful.

**Alternatives considered**:
- *Monkey-patch `extension.delegate_integration_use`* — kept for the pure-planning tests, but not
  sufficient on its own: it skips the subprocess path where an argument mistake would live.
- *A second stub script* — rejected: one argument-aware stub is already the established pattern.

---

## R11 — Silence is implemented in the plan, not in the printer

**Decision**: `coverage.plan()` returns an empty plan when there is nothing to do — one integration and
covered, all covered, coverage unknown, no default recorded, or no extension present. Callers print the
step header, the disclosure, and any question **only** when the plan is non-empty.

**Rationale**: FR-037 and FR-038 are absolute, and SC-006 is measured against the previous release's
output. Making emptiness a property of the plan means every caller is silent by construction rather than
by remembering to check, and one test on the plan covers both commands.

**Alternatives considered**:
- *Let each caller decide when to print* — rejected: two callers, two chances to regress the majority
  case.
- *Always print a "coverage: nothing to do" line* — rejected: it is exactly the tax on the majority the
  spec forbids.

---

## R12 — Documentation and version obligations are tasks, not afterthoughts

**Decision**: the implementation includes, as first-class tasks: `VERSION` → `6.2.0`; README updates to
*Projects with more than one agent installed* and *Keeping everything up to date*, including removing
`specify integration use` as the advertised remedy; a "Changed in 6.2.0" note in `docs/index.html`; and
the cross-note in feature 010's `contracts/cli-surface.md` recording the supersession.

**Rationale**: Principle VI and FR-050 both require it, and the landing page already carries "Changed
in" notes for 5.0.0, 6.0.0, and 6.1.0 — an omission would be visible drift. The 010 cross-note is what
keeps two contracts from disagreeing about whether the default may move.

**Alternatives considered**:
- *Document at release time* — rejected: the repository's own constitution treats the docs as part of the
  change, not a follow-up.
