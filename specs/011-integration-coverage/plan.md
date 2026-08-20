# Implementation Plan: Full Integration Coverage on Install and Update

**Branch**: `011-integration-coverage` | **Date**: 2026-08-20 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/011-integration-coverage/spec.md`

## Summary

`spectra install` registers Spectra's commands for the project's **default** integration only, because
that is all the dependency does when an extension is installed. Every other installed agent gets
nothing, and `spectra update` is worse than silent: updating the extension unregisters it for *every*
agent and re-registers it for the default alone, so coverage a developer established by hand is deleted
on the next maintenance run.

The fix is a **rotation**: activate each uncovered integration in turn — activation is the only
supported trigger for registering an installed extension's commands for an agent — and make the last act
of the run a re-activation of the original default, which both restores it and covers it. The project
therefore ends every run configured exactly as it started (research R3, R4).

The change adds one module and touches four. `coverage.py` (new) answers *which integrations lack
Spectra's commands* from recorded state and turns that into a plan; the plan is pure data, so the
rotation's order and its restoration obligation are testable without a terminal or a subprocess (R1,
R2). `extension.py` gains one delegation — activate an integration, never with an overwrite flag (R5).
`install.py` gains the coverage step and stops treating an already-installed extension as a failure, by
classifying project state instead of parsing the dependency's message (R6). `cli.py` wires the step into
`spectra update` after the component walk, with a disclosure and a single question, and repoints the
existing advisory at `spectra install` (R7, R8).

Three properties hold the design together, each one a requirement rather than an intention: the
restoration is a `finally`-block obligation, so it survives a failed activation and an interrupt
(FR-015, FR-016); coverage is verified by **re-reading recorded state**, never by trusting an exit code
(FR-006); and a project with one covered integration executes no activation and prints not one extra
line (FR-038, SC-006).

## Technical Context

**Language/Version**: Python 3.9+ (CI matrix: 3.9 and 3.12)

**Primary Dependencies**: None. Standard library only — `argparse`, `subprocess`, `json`, `pathlib`.
Spec Kit's `specify` CLI is a runtime dependency invoked as a child process, never imported.

**Storage**: N/A — nothing is persisted, and no authorization is remembered across runs. Three project
files are *read*: `.specify/integration.json` (installed list, default), `.specify/extensions/.registry`
(per-agent command registration), and the installed extension manifest. Two are *written by the
dependency* during a rotation and must come back unchanged: `.specify/integration.json` and
`.specify/init-options.json`.

**Testing**: `unittest` via `python -m unittest discover -s tests`, extending `tests/helpers.py` — the
`specify` stub gains an argv log and an optional side effect for `integration use`, so the rotation's
order, the restore, and post-rotation verification are all assertable (R10). The byte-for-byte
restoration claim is additionally guarded end-to-end in the containerized harness against a real Spec
Kit (R9).

**Target Platform**: macOS, Linux, Windows — all three are supported `spectra` install targets.

**Project Type**: Single-package CLI tool.

**Performance Goals**: `spectra version` gains nothing — no subprocess, no network call, no new file
read beyond the registry it already reads. `spectra install` and `spectra update` add **one subprocess
per uncovered integration plus one for the restore**, and zero when nothing is uncovered.

**Constraints**: Every external read degrades to `unknown` and an unknown is never acted on (FR-003,
FR-004). No integration key is hard-coded (FR-046). The overwrite authorization built for version
upgrades stays unreachable from this path — no call in this feature may pass a force flag (FR-009,
FR-049). The dependency's version is never consulted as a capability gate (FR-051).

**Scale/Scope**: N installed integrations (1 in the large majority, 2–3 observed). Roughly 180 new lines
in one new module, ~120 modified across `install.py`, `cli.py`, and `extension.py`, plus fixtures and
tests.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Applies? | Verdict |
| --- | --- | --- |
| **I. Spec-Driven Development** | Yes | ✅ Pass — flowing through `specify` → `clarify` → `plan`; artifacts under `specs/011-integration-coverage/`, BRD-007 recorded upstream, 5 clarifications resolved before planning. |
| **II. A Single Self-Contained Extension** | No | N/A — CLI-channel work. No file under `spectra/commands/` changes; `spectra/extension.yml` is untouched. |
| **III. Agent-Agnostic Commands** | No | N/A — no extension command files involved. The feature is *about* agent-agnosticism but adds no command. |
| **IV. Context-Aware by Default** | Yes | ✅ Pass, and deepened — the CLI already reads the installed-integration list and the extension registry; this feature acts on what they say instead of reporting it and stopping. |
| **V. Catalog and Package in Sync** | No | N/A — governs the catalog channel. No agent is added or changed, so `agents-list.json`, `catalog.json`, `docs/packages/spectra.zip`, and every generated region are unaffected; `tools/generate_agent_docs.py --check` stays green. |
| **VI. Two Independently-Versioned Release Channels** | Yes | ⚠️ Pass with obligations — see below. |

### Principle VI obligations

This is a **CLI-channel** change and an **additive** one: install and update do more, no command or flag
is added or removed, and no existing contract is narrowed. Therefore:

- Bump the root `VERSION` from `6.1.0` to **`6.2.0`** — minor. `spectra install` keeps its arguments and
  its success path; the new behaviour is additional work inside it. Not major: nothing a user types
  changes, and nothing they relied on stops working. Not patch: the observable behaviour of two commands
  changes materially.
- The extension version in `spectra/extension.yml` and the `spectra` entry in `catalog.json` **must not
  move**. The channels are deliberately uncoupled and no agent changed.
- No git tag is created by this work; tagging is the release step for the CLI channel.
- `README.md` documents the multi-agent story verbatim in *Projects with more than one agent installed*
  and *Keeping everything up to date*; both need the new install behaviour, and the advisory's wording
  there must stop naming `specify integration use` as the remedy.
- `docs/index.html` carries a per-version "Changed in" note for CLI behaviour changes (5.0.0, 6.0.0,
  6.1.0); 6.2.0 needs the same treatment (FR-050).

### Gate result

**PASS.** No violations, so Complexity Tracking is omitted.

One consequence is recorded rather than excused: this feature **supersedes a published boundary**.
`specs/010-multi-integration-updates/spec.md` and BRD-006 § 5.2 state that the project's default
integration is changed "not as an end state and not transiently", and that registering commands for
non-default integrations is out of scope. FR-008 and FR-014–FR-016 replace the second half outright and
narrow the first to a transient, disclosed, self-reversing change. The reasoning is preserved — the
default remains the team's, and the project ends configured as it started — while the outcome changes.
The supersession is written into [`contracts/cli-surface.md`](contracts/cli-surface.md) § Supersession
and must be cross-noted in `specs/010-multi-integration-updates/contracts/cli-surface.md` during
implementation, so the two contracts do not silently disagree. This is the same treatment features 009
and 010 gave their own reversals.

## Project Structure

### Documentation (this feature)

```text
specs/011-integration-coverage/
├── plan.md                        # This file
├── spec.md                        # Feature specification (5 clarifications recorded)
├── research.md                    # Phase 0 — 12 decisions, 5 of them load-bearing
├── data-model.md                  # Phase 1 — CoverageState, CoveragePlan, CoverageResult
├── quickstart.md                  # Phase 1 — runnable validation scenarios
├── contracts/
│   ├── coverage.md                # Detection, the rotation, restoration, verification
│   └── cli-surface.md             # Command surface, output shapes, exit codes, supersession
├── checklists/
│   └── requirements.md            # Spec quality checklist (16/16)
└── tasks.md                       # Phase 2 — created by /speckit.tasks, NOT by this command
```

### Source Code (repository root)

```text
spectra_cli/
├── coverage.py          # NEW — coverage detection, the plan, the rotation, the restoration
│                        #       obligation, and post-rotation verification
├── exits.py             # NEW — the EXIT_* constants, moved out of cli.py so install.py can return
│                        #       them without a circular import (research R13)
├── extension.py         # MODIFIED — delegate_integration_use(key); registered_agents() reused as-is
├── install.py           # MODIFIED — step 4 (coverage), already-present detection by project state
├── cli.py               # MODIFIED — re-exports EXIT_* from exits.py, cmd_install exit contract,
│                        #            cmd_update coverage step and outcome row, advisory repointed
├── health.py            # UNCHANGED as a decision — currency lives here, coverage does not (R1)
├── project.py           # MODIFIED — a small "is this extension present?" helper for any id
└── ui.py                # UNCHANGED — existing helpers and glyphs cover the new output

tests/
├── test_coverage.py     # NEW — detection, plan shape, rotation order, restoration, verification
├── test_install.py      # NEW — install's coverage step, already-present path, exit codes.
│                        #       Today's install-flow assertions live in test_check.py, which reaches
│                        #       cmd_install through `spectra check --yes`; those stay put, and this
│                        #       file owns the coverage step and the exit contract.
├── test_version_update.py  # MODIFIED — the update's coverage step (ask, decline, --yes, no-TTY) and
│                        #              the advisory wording, which lives here — not in test_health.py
├── test_cli_surface.py  # MODIFIED — no new flag, help text unchanged, exit codes
├── test_no_hardcoded_agents.py  # MODIFIED — coverage.py added to the source scan
├── test_health.py       # UNCHANGED — the advisory is rendered by cli.py, so its tests are not here
└── helpers.py           # MODIFIED — argv log + `integration use` side effect in the specify stub

test/
└── scenarios.sh         # MODIFIED — end-to-end: two real integrations, coverage after install and
                         #            after update, and the byte-identical restoration check

README.md                # MODIFIED — install covers every integration; advisory remedy reworded
docs/index.html          # MODIFIED — "Changed in 6.2.0" note
VERSION                  # MODIFIED — 6.1.0 → 6.2.0
```

**Structure Decision**: The single-package CLI layout is unchanged. One new module is added rather than
extending `health.py`, because `health.py` answers *is the stack current?* and coverage answers *is the
stack present for each agent?* — different questions, different inputs, and `health.py` is already the
largest module in the package (R1). `coverage.py` depends on `health.py`'s existing readers rather than
duplicating them, so the installed-integration list and the default are read in exactly one place.

## Phase 0 — Research

See [research.md](research.md). Thirteen decisions; the five that shape the design:

- **R1** — coverage lives in a new module, not in `health.py`.
- **R3** — the rotation covers non-default integrations first and ends by re-activating the original
  default, so the restore *is* the default's own coverage. This answers the question `/speckit.clarify`
  deferred to planning.
- **R4** — restoration is a `finally`-block obligation with three distinguishable outcomes: never moved,
  moved and restored, moved and restore failed.
- **R6** — "already installed" is detected by classifying the project before attempting the install, not
  by matching the dependency's message text (FR-021).
- **R9** — the byte-for-byte restoration claim (FR-044) is enforced by an end-to-end test against a real
  Spec Kit, with the disclose-and-decline fallback specified but not built unless that test fails.
- **R13** — the `EXIT_*` constants move to a new `spectra_cli/exits.py`, because `install.py` must return
  them and `cli.py` already imports `install.py`.

## Phase 1 — Design & Contracts

- [data-model.md](data-model.md) — `CoverageState` per integration, the `CoveragePlan` (ordered targets
  plus the default to restore), `CoverageResult` with per-integration children and a restoration verdict,
  and the state transitions a rotation can produce.
- [contracts/coverage.md](contracts/coverage.md) — the detection rules, the rotation algorithm, the
  restoration obligation, the verification pass, and every skip reason with its exact wording.
- [contracts/cli-surface.md](contracts/cli-surface.md) — what `spectra install`, `spectra update`, and
  `spectra version` print and return in each case, the exit-code table, the no-new-flag guarantee, and
  the supersession note.
- [quickstart.md](quickstart.md) — runnable validation scenarios, including the two-integration
  end-to-end and the interrupt path.

### Post-design Constitution re-check

**PASS, unchanged.** The design adds no extension command, no agent, no flag, no network call, and no
credential. It reads three project files and invokes one dependency subcommand per uncovered
integration plus one restore. Principle VI's obligations (VERSION 6.2.0, README, landing page) are
carried as tasks rather than assumed, and the supersession of the 010 boundary is documented in the
contract instead of being left implicit.
