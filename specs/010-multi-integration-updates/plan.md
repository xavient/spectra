# Implementation Plan: Multi-Integration Stack Updates

**Branch**: `010-multi-integration-updates` | **Date**: 2026-08-20 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/010-multi-integration-updates/spec.md`

## Summary

`spectra version` and `spectra update` treat "Core agents" as one thing. It is not: a project can have
several Spec Kit integrations installed, and today only the default one is ever judged or upgraded —
while the project-level record they are judged *by* is rewritten on any single upgrade, so the row
reports current while a sibling is stale.

The change is contained to three modules and adds no new command. `health.py` learns to enumerate the
installed integrations, read each one's own recorded version, and derive the row's verdict from them by a
pure aggregation function (research R1, R2). `extension.py` learns to name an integration when
delegating the upgrade, and to carry `--force` when — and only when — the user has authorized it.
`cli.py` gains the per-integration breakdown lines, the disclose-and-consent gate in front of any
overwrite, and the agent-coverage advisory.

Three properties hold the design together: the walk **names** integrations rather than switching the
project default (R3), so no project configuration is ever touched; the consent gate **plans, discloses,
asks once, then walks** (R4), so no file is overwritten before the user has seen it; and a project with
one integration executes exactly the reads and prints exactly the lines it does today (FR-012), so a
minority-case feature costs the majority nothing.

## Technical Context

**Language/Version**: Python 3.9+ (CI matrix: 3.9 and 3.12)

**Primary Dependencies**: None. Standard library only — `argparse`, `subprocess`, `json`, `pathlib`.
Spec Kit's `specify` CLI is a runtime dependency invoked as a child process, never imported.

**Storage**: N/A — nothing is persisted, and FR-033 forbids persisting the overwrite authorization.
Four project files are *read*: `.specify/integration.json`, `.specify/integrations/<key>.manifest.json`
(one per integration), `.specify/extensions/.registry`, and the installed extension manifest. One child
process is read from on the update path only: `specify integration status --json`.

**Testing**: `unittest` via `python -m unittest discover -s tests`, extending the existing fixtures in
`tests/helpers.py` (research R10) — a project fixture that can hold several integrations, and an
argument-aware `specify` stub.

**Target Platform**: macOS, Linux, Windows — all three are supported `spectra` install targets, so no
path or shell assumption may leak in.

**Project Type**: Single-package CLI tool.

**Performance Goals**: `spectra version` gains **no** subprocess and no network call; it stays at
today's cost plus one small file read per installed integration. `spectra update` adds exactly one
subprocess (`specify integration status --json`) ahead of the walk.

**Constraints**: Every external read degrades to a reported `unknown` rather than an exception, and an
unknown is never acted on (FR-005, FR-015, FR-018). Machine decisions never parse human-formatted output
(FR-041). The overwrite is never applied without an authorization act performed in the same run
(FR-026, FR-033).

**Scale/Scope**: Four report components, N installed integrations (1 in the overwhelming majority of
projects, 2–3 observed). Roughly 250 modified lines across three modules, one new UI helper for the
breakdown lines, plus fixtures.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Applies? | Verdict |
| --- | --- | --- |
| **I. Spec-Driven Development** | Yes | ✅ Pass — flowing through `specify` → `plan`, artifacts under `specs/010-multi-integration-updates/`, BRD-006 recorded upstream of the spec. |
| **II. A Single Self-Contained Extension** | No | N/A — CLI-channel work. No file under `spectra/commands/` changes and `spectra/extension.yml` is untouched. |
| **III. Agent-Agnostic Commands** | No | N/A — no extension command files involved. |
| **IV. Context-Aware by Default** | Yes | ✅ Pass, and deepened — the feature exists because the CLI was reading too little project context. It now reads the recorded integration list, each integration's own manifest, and the extension registry instead of inferring a whole project from one field. |
| **V. Catalog and Package in Sync** | No | N/A — governs the catalog channel. No agent is added, so `agents-list.json`, `catalog.json`, `docs/packages/spectra.zip`, and the generated regions are unaffected; `tools/generate_agent_docs.py --check` stays green. |
| **VI. Two Independently-Versioned Release Channels** | Yes | ⚠️ Pass with obligations — see below. |

### Principle VI obligations

This is a **CLI-channel** change and an **additive** one — a flag is added, a row gets richer, and
nothing is removed or renamed. Therefore:

- Bump the root `VERSION` from `6.0.0` to **`6.1.0`** — minor, not major: `spectra update` keeps its
  existing contract, `--force` is optional, and no command or flag disappears.
- The extension version in `spectra/extension.yml` and `catalog.json` **must not** move. The channels are
  deliberately uncoupled and no agent changed.
- No git tag is created by this work; tagging is the release step and belongs to the CLI channel.
- README copy for `spectra version` / `spectra update` needs the multi-integration behaviour and the new
  flag, since it documents the four-component table verbatim.

### Gate result

**PASS.** No violations, so Complexity Tracking is omitted.

One consequence is recorded rather than excused: this feature **supersedes a published decision**. The
contract at `specs/007-unified-version-update/contracts/health-check.md` states that `--force` is
deliberately never passed to `specify integration upgrade`, on the grounds that overriding the
dependency's block would discard the user's edits. FR-026–FR-033 replace that blanket refusal with a
consent gate — the *reasoning* is preserved (the user's content is never discarded without their say)
while the outcome changes (they may now say so). The supersession is written into
[`contracts/cli-surface.md`](contracts/cli-surface.md) § Supersession and must also be noted in the 007
contract itself during implementation, so the two do not silently disagree.

## Project Structure

### Documentation (this feature)

```text
specs/010-multi-integration-updates/
├── plan.md                        # This file
├── spec.md                        # Feature specification (1 clarification recorded)
├── research.md                    # Phase 0 — 10 decisions, 4 of them load-bearing
├── data-model.md                  # Phase 1 — IntegrationState, aggregation, overwrite plan
├── quickstart.md                  # Phase 1 — runnable validation scenarios
├── contracts/
│   ├── core-agents.md             # Detection, aggregation, and the update walk
│   └── cli-surface.md             # Command surface, output shapes, exit codes, supersession
├── checklists/
│   └── requirements.md            # Spec quality checklist (16/16)
└── tasks.md                       # Phase 2 — created by /speckit.tasks, NOT by this command
```

### Source Code (repository root)

```text
spectra_cli/
├── health.py            # MODIFIED — integration enumeration, per-key versions, aggregation,
│                        #            modification report, per-key update walk
├── extension.py         # MODIFIED — delegate_integration_upgrade(key, force), registered_agents()
├── cli.py               # MODIFIED — breakdown rows, disclosure + consent gate, --force,
│                        #            coverage advisory, per-key outcome rows
├── ui.py                # MODIFIED — indented sub-rows for the breakdown and per-key outcomes
├── project.py           # UNCHANGED — reused as-is
├── version.py           # UNCHANGED — compare_versions reused for per-key comparison
├── net.py               # UNCHANGED
├── install.py           # UNCHANGED
└── roster.py            # UNCHANGED

tests/
├── helpers.py           # MODIFIED — multi-integration project fixture, argument-aware specify stub
├── test_health.py       # MODIFIED — enumeration, per-key reads, aggregation precedence
├── test_version_update.py # MODIFIED — report rows, walk order, consent paths, exit codes
└── test_cli_surface.py  # MODIFIED — `--force` placement and help text

VERSION                  # MODIFIED — 6.0.0 -> 6.1.0
README.md                # MODIFIED — multi-integration behaviour and the new flag
specs/007-unified-version-update/contracts/health-check.md  # MODIFIED — supersession note
```

**Structure Decision**: The flat `spectra_cli/` package is kept — no subpackage, no new module. The
feature is a deepening of one existing component's detection and update path, and every piece of it has
an established home: detection and the walk in `health.py`, delegation in `extension.py`, presentation
and prompting in `cli.py`. Adding a module for one component's plurality would split logic that the
existing tests already reach through those three seams.

## Design Overview

### Detection

`health.get_integration_status()` keeps its signature and its four-value vocabulary, and gains children:

```text
read_installed_integrations(root)      -> ["kiro-cli", "claude"] | None   # integration.json
read_integration_version(root, key)    -> "0.15.1" | None                 # per-key manifest
get_integration_states(root, specify)  -> [IntegrationState, ...]         # one per installed key
aggregate(states, specify)             -> ComponentStatus(parts=states)   # R2 precedence
```

The per-integration verdict reuses today's two-way reasoning unchanged — the CLI being behind implies
every integration is behind, and a CLI that is current but a record that disagrees means the upgrade was
never re-run — applied once per key instead of once per project. `version.compare_versions` does the
comparing, so a leading `v` and an unparseable version behave exactly as they do elsewhere.

When `installed_integrations` is absent or no per-key manifest reads, the function falls back to today's
single-record path (R8) and produces one child with no key — which is what keeps FR-012 true by
construction rather than by care.

### The update walk

`apply_updates()` keeps its three properties (every component visited, skips inert, cancellation stops
the walk) and gains an inner loop for the integration component:

```text
for component in report.components:
    if component is Core agents and has children:
        for state in behind(children), non-default first, default last:      # R3
            force = state.key in authorized_keys                             # R4
            code = delegate_integration_upgrade(state.key, force=force)
            record a child UpdateResult; continue past failure               # R9
        parent outcome = worst(children)
    else:
        ... unchanged ...
```

`authorized_keys` is decided **before** the walk starts and passed in, so `health.py` never prompts and
stays testable without a terminal — the same division the module already keeps.

### Consent

`cmd_update` builds the overwrite plan between the check and the walk:

1. `modification_report()` — one `specify integration status --json`, bounded, never raising (R1, R6).
2. Reduce to integrations that are **about to be upgraded** and have modified files (FR-034).
3. Empty set → print nothing, ask nothing, walk with no force (FR-009 path, unchanged behaviour).
4. Non-empty → disclose per-integration groups **and** the shared-infrastructure group (F6, FR-025),
   then resolve authorization: `--force` authorizes; otherwise a TTY is asked with the default at *no*;
   otherwise nothing is authorized and `--force` is named (FR-028, FR-031).
5. Unauthorized integrations become `SKIPPED` with the two real options — never `FAILED` (FR-030).

### Exit codes

Unchanged from `007-unified-version-update`: `EXIT_OK` 0, `EXIT_DECLINED` 1 when the plan itself is
declined, `EXIT_DELEGATION` 4 when any *attempted* upgrade failed, 130 on interrupt. A declined overwrite
produces skips, and skips never reach the exit code — so a project that cannot be fully updated still
exits 0 having said exactly why (FR-023, FR-030).

## Phase 1 Artifacts

| Artifact | What it fixes |
| --- | --- |
| [`data-model.md`](data-model.md) | `IntegrationState`, `ComponentStatus.parts`, `ModificationReport`, `OverwritePlan`, child `UpdateResult`, and the aggregation truth table |
| [`contracts/core-agents.md`](contracts/core-agents.md) | Detection inputs, the per-key verdict rules, aggregation precedence, walk order, and degradation paths |
| [`contracts/cli-surface.md`](contracts/cli-surface.md) | `--force` placement and help text, the disclosure and outcome output shapes, exit codes, and the 007 supersession |
| [`quickstart.md`](quickstart.md) | Runnable validation scenarios covering all five user stories, including the fixture recipes for a two-integration project |

## Post-Design Constitution Re-Check

| Principle | Post-design verdict |
| --- | --- |
| **I. Spec-Driven Development** | ✅ Pass — design is recorded in artifacts before code; no implementation has begun. |
| **II. Single Self-Contained Extension** | ✅ N/A — the design touches no file under `spectra/`. |
| **III. Agent-Agnostic Commands** | ✅ N/A — no command files. The design deliberately avoids per-agent layout knowledge (R7 reads the registry rather than guessing each agent's directory), so no agent-specific assumption enters the CLI either. |
| **IV. Context-Aware by Default** | ✅ Pass — strengthened; four recorded project facts are read where one was. |
| **V. Catalog and Package in Sync** | ✅ N/A — no roster, catalog, package, or generated region changes. |
| **VI. Two Release Channels** | ✅ Pass — `VERSION` 6.1.0, extension version frozen, no tag created here. |

**Result: PASS.** No new violations introduced by the design, so Complexity Tracking remains omitted.

## Notes for `/speckit.tasks`

- **Order the work detection → reporting → walk → consent → advisory.** Each stage is independently
  testable and the later ones consume the earlier ones; the advisory (US5) is genuinely separable and
  can land last.
- **Fixtures come first.** Nothing in US1–US4 is testable until `tests/helpers.py` can build a
  two-integration project and the `specify` stub can answer two different subcommands (R10). Treat that
  as the first task, not a step inside another.
- **Two regression guards deserve their own tasks**: that a single-integration project's output is
  byte-identical to today (FR-012, SC-005), and that no code path passes `--force` without an
  authorization recorded in the same run (FR-026, SC-003).
- **The supersession is a task, not a footnote.** Editing
  `specs/007-unified-version-update/contracts/health-check.md` is part of this change.
- **Do not add a fifth report row, a new command, or an "always force" setting.** All three are
  explicitly excluded (FR-011, FR-033, spec § 5.2).
