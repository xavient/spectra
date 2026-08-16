# Implementation Plan: Unified Version & Update Commands

**Branch**: `007-unified-version-update` | **Date**: 2026-08-16 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/007-unified-version-update/spec.md`

## Summary

Replace the extension-only `spectra version` and `spectra update` with unified commands that report and
repair all four components of the Spectra stack — Specify CLI, core integration, Spectra CLI, and
Spectra agents — and hard-remove `spectra cli version` / `spectra cli update`, whose jobs those two now
absorb.

The technical approach is a new `spectra_cli/health.py` that turns each component into one uniform
`ComponentStatus`, so `cmd_version` becomes "render four statuses" and `cmd_update` becomes "act on the
four statuses in order". Three research findings shape it: `specify self check` must be parsed from
stdout because it always exits 0 (R1); the integration version has no command exposing it, so
`.specify/integration.json` is read directly (R2); and CI currently asserts on `spectra cli version`,
so retiring it requires moving that assertion in the same change (R3).

## Technical Context

**Language/Version**: Python 3.9+ (CI matrix: 3.9 and 3.12)

**Primary Dependencies**: None. Standard library only — `argparse`, `subprocess`, `json`, `urllib`,
`importlib.metadata`, `pathlib`. This is a hard constraint, not a preference (see Constitution Check).

**Storage**: N/A — no persisted state. Two files are *read*: `.specify/integration.json` and
`.specify/extensions/spectra/extension.yml`.

**Testing**: `unittest` via `python -m unittest discover -s tests`, with the existing fixtures in
`tests/helpers.py` (`temp_project`, `serve`, `raw_base`, `cwd`). No pytest.

**Target Platform**: macOS, Linux, Windows — all three are supported install targets for the `spectra`
command.

**Project Type**: Single-package CLI tool.

**Performance Goals**: `spectra version` completes in roughly one second on a warm network. Budget is
one `specify self check` subprocess (measured 0.33 s) plus two HTTP GETs already bounded by
`net.TIMEOUT`.

**Constraints**: Every external call must degrade to a reported `unknown` rather than an exception —
`spectra version` has to stay useful offline, with `specify` absent, and with a malformed project.
Subprocess calls carry an explicit timeout.

**Scale/Scope**: Four components; one new module (~200 lines), one new UI helper, two new delegation
helpers, two rewritten command handlers, one CI step edited, three test files touched or added.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Applies? | Verdict |
| --- | --- | --- |
| **I. Spec-Driven Development** | Yes | ✅ Pass — this work is flowing through `specify` → `clarify` → `plan`, with artifacts under `specs/007-unified-version-update/`. |
| **II. A Single Self-Contained Extension** | No | N/A — this is CLI-channel work. No command is added, changed, or removed under `spectra/commands/`, and `spectra/extension.yml` is untouched. |
| **III. Agent-Agnostic Commands** | No | N/A — no extension command files involved. |
| **IV. Context-Aware by Default** | Yes | ✅ Pass — and this feature deepens it. The health check reads the project's real `.specify/integration.json` and installed manifest rather than assuming a state. |
| **V. Catalog and Package in Sync** | No | N/A — governs the catalog channel. No agent is added, so `agents-list.json`, `catalog.json`, `docs/packages/spectra.zip`, and the generated regions are all unaffected. `tools/generate_agent_docs.py --check` stays green because no roster data changes. |
| **VI. Two Independently-Versioned Release Channels** | Yes | ⚠️ Pass with obligations — see below. |

### Principle VI obligations

This is a **CLI-channel** change and a **breaking** one: two commands are removed from the public
surface. Therefore:

- Bump the root `VERSION` to **`6.0.0`** — major, because `spectra cli version` and `spectra cli update`
  disappear. This mirrors 5.0.0's removal of `--version` / `--update` / `--uninstall`.
- The extension version in `spectra/extension.yml` and `catalog.json` **must not** move. The two
  channels are explicitly not coupled, and no agent changed.
- No git tag is created by this work. Tagging is the release step, and tags belong to the CLI channel
  only.
- The CLI must keep reading `catalog.json` at run time; nothing here hard-codes an extension set.

### Gate result

**PASS.** No violations to justify, so Complexity Tracking is omitted. One consequence is recorded
rather than excused: retiring a command that CI depends on obliges this change to update
`.github/workflows/ci.yml` (R3). That is a necessary part of the change, not a deviation from it.

## Project Structure

### Documentation (this feature)

```text
specs/007-unified-version-update/
├── plan.md              # This file
├── spec.md              # Feature specification (with 3 clarifications)
├── research.md          # Phase 0 output — 7 findings, 3 of them design-changing
├── data-model.md        # Phase 1 output — ComponentStatus, HealthReport, UpdateResult
├── quickstart.md        # Phase 1 output — runnable validation scenarios
├── contracts/
│   ├── cli-surface.md   # The command surface after this change
│   └── health-check.md  # Detection and update contract per component
├── checklists/
│   └── requirements.md  # Spec quality checklist (16/16)
└── tasks.md             # Phase 2 — created by /speckit.tasks, NOT by this command
```

### Source Code (repository root)

```text
spectra_cli/
├── health.py            # NEW — the four-component health check
├── cli.py               # MODIFIED — new cmd_version, new cmd_update, retirements, help text
├── extension.py         # MODIFIED — delegate_self_upgrade(), delegate_integration_upgrade()
├── ui.py                # MODIFIED — health_table() renderer
├── version.py           # UNCHANGED — reused as-is
├── project.py           # UNCHANGED — reused as-is
├── net.py               # UNCHANGED
├── install.py           # UNCHANGED
└── roster.py            # UNCHANGED

tests/
├── test_health.py       # NEW — parser, integration.json reads, check_all combinations
├── test_version_update.py  # MODIFIED — four-component reporting, partial failures
├── test_cli_surface.py  # MODIFIED — retirements, help panels
└── helpers.py           # MODIFIED — add a specify-self-check output fixture + fake `specify`

.github/workflows/ci.yml # MODIFIED — version assertion moved off the retired command (R3)
VERSION                  # MODIFIED — 5.x -> 6.0.0
```

**Structure Decision**: The existing flat `spectra_cli/` package is kept — no subpackages introduced.
`health.py` sits alongside `version.py` and `extension.py` as a third peer that *composes* them rather
than a layer above them, which is why it holds no network or subprocess logic of its own beyond the one
call Spec Kit gives us no other way to make (`specify self check`). Test files mirror the module they
cover, matching the existing one-file-per-concern convention.

## Design Overview

### The uniform status

Every component resolves to one `ComponentStatus` with the same five fields regardless of how wildly
different its detection mechanism is. That uniformity is the whole point: it collapses `cmd_version`
into a render loop and `cmd_update` into an ordered walk, with no per-component branching in either.

Statuses: `UP_TO_DATE` · `NEEDS_UPDATING` · `AHEAD` · `UNKNOWN`. Full field list and the state table
live in [data-model.md](data-model.md); per-component detection and update mechanics live in
[contracts/health-check.md](contracts/health-check.md).

### Detection, per component

| Component | Installed from | Latest from | Notes |
| --- | --- | --- | --- |
| Specify CLI | `specify self check` stdout | same output | Always exits 0 — parse stdout (R1) |
| Core agents | `.specify/integration.json` → `version` | the installed Specify CLI version | `unknown` if the CLI status is unknown (FR-025) |
| Spectra CLI | `version.read_installed_version()` | `version.resolve_latest()` | Suppressed by `--no-update-check` |
| Spectra agents | project manifest via `project.classify()` | `extension.published_version()` | Reuses the existing comparison |

### Update, per component

Ordered walk over components whose status is `NEEDS_UPDATING`; `UNKNOWN` and `AHEAD` are skipped
without being attempted (FR-023, FR-024). Each step is independently guarded so one failure cannot end
the run (FR-009), and results are collected into one final report (FR-010). Order is
Specify CLI → Core agents → Spectra CLI → Spectra agents, and R6 records why step 3 must stay third
rather than first: it replaces the running process's own code.

### Exit codes

Reusing the existing constants unchanged; the only new rule is how skips are counted.

| Situation | Code |
| --- | --- |
| Any verdict delivered by `spectra version` | `EXIT_OK` (0) |
| `spectra update` — everything attempted succeeded | `EXIT_OK` (0) |
| `spectra update` — nothing needed updating | `EXIT_OK` (0) |
| User declined the prompt | `EXIT_DECLINED` (1) |
| `spectra cli version` / `spectra cli update` | `EXIT_USAGE` (2) |
| Not a Spec Kit project, or Spectra not installed | `EXIT_PROJECT_STATE` (5) |
| `spectra update` — any attempted update failed | `EXIT_DELEGATION` (4) |
| Interrupted | `EXIT_INTERRUPTED` (130) |

`spectra version` keeps its "a verdict is a success" rule: reporting that things are out of date, or
that a status is unknown, still exits 0, so the command stays safe to drop into a shell without
`|| true`. Only a project-state failure is non-zero.

## Phase 1 Artifacts

| Artifact | Contents |
| --- | --- |
| [data-model.md](data-model.md) | `ComponentStatus`, `HealthReport`, `UpdateResult`; status values, derivation rules, and the integration-vs-CLI state table |
| [contracts/cli-surface.md](contracts/cli-surface.md) | The command surface after the change, retirement messages, help panels, exit codes |
| [contracts/health-check.md](contracts/health-check.md) | Per-component detect/update contract, the `specify self check` parse table, failure mapping |
| [quickstart.md](quickstart.md) | Runnable validation scenarios covering each user story and edge case |

## Post-Design Constitution Re-Check

Re-evaluated after the Phase 1 artifacts were written:

- **Zero dependencies** — held. `health.py` imports only `json`, `subprocess`, `shutil`, `pathlib`, and
  Spectra's own modules. No YAML parser added; the integration file is JSON, and the extension manifest
  continues to use the established line scanner.
- **Principle II / III / V** — still N/A. The design touches no file under `spectra/`, so the catalog
  channel cannot drift as a result of it.
- **Principle VI** — the `VERSION` bump to 6.0.0 and the untouched extension version are recorded in
  the plan and reflected in `contracts/cli-surface.md`. CI's parity assertion survives the retirement
  in a stronger form (asserting against distribution metadata directly).
- **Principle IV** — strengthened, as noted in the gate.
- **Complexity** — one new module, no new abstractions layered over existing ones, no new subpackage.
  The four `try/except` blocks in the update walk are required by FR-009 rather than defensive padding.

**Result: PASS.** No new violations introduced by the design.

## Notes for `/speckit.tasks`

Two items to carry forward that are easy to lose:

1. **`.github/workflows/ci.yml` and `VERSION` are in scope.** Neither appears in the issue's file
   list. Skipping the CI edit turns the build red the moment the retirement lands (R3).
2. **`tests/helpers.py` needs a fake `specify` on `PATH`.** The health check shells out, so tests need
   both a stub executable emitting each of R1's five output branches and a way to simulate `specify`
   being absent entirely.

FR-016's wording has already been corrected in the spec: it previously called `specify self check` a
"local check" when it makes its own GitHub request (R5). Behavior was unaffected — only the label was
wrong — and the requirement now states what is and is not suppressed.
