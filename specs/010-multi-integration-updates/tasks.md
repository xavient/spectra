# Tasks: Multi-Integration Stack Updates

**Input**: Design documents from `/specs/010-multi-integration-updates/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md — all present

**Tests**: **Included.** Four success criteria are direct assertions about behaviour (SC-002 "zero
occurrences", SC-003 "zero files overwritten without authorization", SC-005 "unchanged line for line",
SC-007 "zero files unless `--force`"), and one of them guards an irreversible action. Every story phase
leads with its tests.

**Organization**: Grouped by user story. US1 is the foundation every other story reads from; US2 consumes
its children; US3 gates US2's walk; US4 is a constrained variant of US3; US5 is fully independent of
US2–US4 and can ship at any point after US1.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US5)

## Path Conventions

Single package at repository root: `spectra_cli/` for source, `tests/` for tests. No `src/` directory —
paths below are literal.

---

## Phase 1: Setup

**Purpose**: Establish the baseline and confirm the dependency still behaves as BRD-006 § 2.1 recorded, so
later regressions are attributable.

- [X] T001 Record the pre-change test baseline by running `python3 -m unittest discover -s tests` and noting the count (expected: 343 tests, OK)
- [X] T002 Confirm findings F1/F3/F7 still hold on the installed Spec Kit by running `specify integration upgrade --help` (a positional `key` and `--force` are offered) and `specify integration status --json >/dev/null; echo $?` in `~/Projects/willow` (read-only; expect exit 0 while status is `warning`)
- [X] T003 Capture the reference states both fixtures must reproduce: `specify integration status --json` in `~/Projects/willow` (two integrations, 23 modified files) and in `/Users/alibahaloo/Projects/spectra` (two integrations, 0 modified) — read-only, no writes to either project

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The fixtures and the three data-structure changes. Nothing in US1–US5 is testable without
them — the current `specify` stub answers every subcommand with self-check text, so it would reply to
`integration status --json` with the wrong payload entirely.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T004 Add an `integration_manifest(key, version)` JSON writer to `tests/helpers.py` producing the `.specify/integrations/<key>.manifest.json` shape (`integration`, `version`, `installed_at`, `files`), mirroring the real files listed in contracts/core-agents.md § 1
- [X] T005 Extend `temp_project()` in `tests/helpers.py` with an `integrations={key: version}` argument that writes `installed_integrations`, `default_integration`, and one manifest per key via T004; omitting it MUST leave today's single-record fixture untouched so existing tests are unaffected (research R10)
- [X] T006 Add a `MISSING_MANIFEST` sentinel to `tests/helpers.py` accepted as an `integrations` value, so "recorded but unreadable" (contracts/core-agents.md § 2) is expressible in a fixture
- [X] T007 Make `fake_specify()` in `tests/helpers.py` argument-aware: dispatch on the subcommand so `self check` serves the existing branch text, `integration status --json` serves a JSON payload, and anything else exits 0 — keeping the real subprocess path under test (research R10)
- [X] T008 Add a `modified={key: [paths], "speckit": [paths]}` option to `fake_specify()` in `tests/helpers.py` that seeds per-integration and shared `modified_files` in the `integration status --json` payload, including the `manifests` and `findings` keys the real command emits
- [X] T009 [P] Implement the `IntegrationState` class in `spectra_cli/health.py` with `__slots__` for `key`, `installed`, `latest`, `status`, `detail`, `is_default`, `modified`, per data-model.md § 1 and following the `ComponentStatus` style already in the module
- [X] T010 [P] Add the optional `parts` field to `ComponentStatus` in `spectra_cli/health.py` (default empty list) plus a derived `has_parts` helper, keeping every existing constructor call valid, per data-model.md § 2
- [X] T011 [P] Add the optional `parts` field and a `key` field to `UpdateResult` in `spectra_cli/health.py` (both defaulting to empty/None), per data-model.md § 5
- [X] T012 Add indented child-row rendering to `ui.health_table()` in `spectra_cli/ui.py` — accept an optional list of child `(label, glyph, phrase)` tuples per row and render them beneath it, aligned to their own width, so the status table and the outcome table keep sharing one renderer

**Checkpoint**: Fixtures can build a two-integration project with seeded modifications, and the three
structures carry per-integration data — user story implementation can begin.

---

## Phase 3: User Story 1 - The report tells the truth about every installed integration (Priority: P1) 🎯 MVP

**Goal**: `spectra version` enumerates every installed integration, reads each one's own recorded version,
and derives the `Core agents` verdict from all of them — naming the ones that are behind.

**Independent Test**: In `~/Projects/willow` (two integrations, one default, both recorded at 0.15.1
against a 0.16.5 CLI), run `spectra version` and confirm `Core agents` reports needs-updating, shows the
oldest version, and names both integrations. Before this story the same project reports up to date.

### Tests for User Story 1

- [X] T013 [P] [US1] Add an `InstalledIntegrations` test class to `tests/test_health.py` covering `read_installed_integrations`: a two-key list, a missing file, invalid JSON, a non-object top level, an empty list, and a project where `speckit.manifest.json` exists but is NOT reported as an integration (FR-001, FR-002)
- [X] T014 [P] [US1] Add a `PerIntegrationVersion` test class to `tests/test_health.py` covering `read_integration_version(root, key)` for a readable manifest, a missing manifest, invalid JSON, a non-object top level, and an absent/empty `version` — all four failures returning `None` (FR-003)
- [X] T015 [P] [US1] Add a `PerIntegrationVerdict` test class to `tests/test_health.py` asserting every row of the table in contracts/core-agents.md § 3, including that an unknown Specify CLI forces every integration unknown, that every unknown carries a reason, and that both ways of being behind are distinguished by `detail` (FR-005)
- [X] T016 [P] [US1] Add an `Aggregation` test class to `tests/test_health.py` asserting all five precedence rules in contracts/core-agents.md § 4, explicitly including behind-outranks-unknown, unknown-outranks-up-to-date, all-ahead, and the ahead+current mix resolving to `UP_TO_DATE` (FR-006, FR-009, FR-010, research R2)
- [X] T017 [P] [US1] Add tests to `tests/test_health.py` asserting the row's derived fields: `installed` is the oldest readable child version (FR-007) and `detail` names the behind children (FR-008)
- [X] T018 [P] [US1] Add a `Fallback` test class to `tests/test_health.py` asserting the single-record path (contracts/core-agents.md § 6) triggers on absent `installed_integrations` and on present-but-unreadable manifests, produces one child with `key=None`, and matches today's verdicts exactly (research R8)
- [X] T019 [P] [US1] Add a `RecordPrecedence` test class to `tests/test_health.py` asserting the per-integration manifests win over the project-level record: seed `.specify/integration.json` with `version` at `0.16.5` while one manifest reads `0.15.1`, and assert `Core agents` reports needs-updating and names that integration (FR-004, BRD-006 finding F2). This is the regression the feature exists for and the sharpest instance of SC-002 — the project-level field is rewritten on any single upgrade, so an implementation that still reads it first must fail here
- [X] T020 [P] [US1] Add tests to `tests/test_version_update.py` asserting the report still prints exactly four rows for a two-integration project (FR-011), that breakdown lines appear only when integrations are non-uniform, and that a uniform two-integration project prints no children (FR-013) — one run tells the developer which integrations are behind without opening a file (SC-009)
- [X] T021 [P] [US1] Add a regression test to `tests/test_version_update.py` asserting a single-integration project's `spectra version` output contains no child lines and no advisory — the in-suite half of SC-005

### Implementation for User Story 1

- [X] T022 [US1] Implement `read_installed_integrations(project_root)` in `spectra_cli/health.py` reading `installed_integrations` from `.specify/integration.json`, preserving order, returning `None` to mean "fall back", and never globbing `.specify/integrations/` (contracts/core-agents.md § 2)
- [X] T023 [US1] Implement `read_integration_version(project_root, key)` in `spectra_cli/health.py` reading `version` from `.specify/integrations/<key>.manifest.json`, collapsing all five failure modes to `None`, with a docstring recording why they are one situation
- [X] T024 [US1] Implement `read_default_integration(project_root)` in `spectra_cli/health.py` reading `default_integration` then falling back to `integration`, returning `None` when neither is recorded
- [X] T025 [US1] Implement `get_integration_states(project_root, specify_status)` in `spectra_cli/health.py` returning one `IntegrationState` per enumerated key, applying the § 3 verdict table via `version.compare_versions`, and marking `is_default`
- [X] T026 [US1] Implement `aggregate_integration_status(states, specify_status)` in `spectra_cli/health.py` as a pure function applying the § 4 precedence table and deriving `installed`, `latest`, and `detail` from the children (depends on T025)
- [X] T027 [US1] Rewire `get_integration_status(project_root, specify_status)` in `spectra_cli/health.py` to enumerate, judge, and aggregate — falling back to today's single-record path when enumeration yields nothing usable — keeping its existing signature so `check_all` is unchanged (depends on T022–T026)
- [X] T028 [US1] Add `_integration_child_rows(component)` to `spectra_cli/cli.py` producing one `(label, glyph, phrase)` tuple per child, reusing `_status_row`'s phrasing so parent and child wording cannot drift
- [X] T029 [US1] Wire the child rows into `_show_health()` in `spectra_cli/cli.py`, gated on the FR-013 visibility rule (more than one integration AND non-uniform), passing them to the extended `ui.health_table()` (depends on T012, T028)

**Checkpoint**: `spectra version` tells the truth about every installed integration. Nothing about
updating has changed yet, and the story is independently valuable.

---

## Phase 4: User Story 2 - One update brings every installed integration current (Priority: P1)

**Goal**: `spectra update` upgrades every behind integration in one run, naming each one, without touching
the project's default integration.

**Independent Test**: In a two-integration project with both behind, run `spectra update --yes` and
confirm both are current afterwards, each has its own outcome line, and `default_integration` is
byte-identical before and after.

### Tests for User Story 2

- [X] T030 [P] [US2] Add an `IntegrationWalk` test class to `tests/test_version_update.py` asserting every behind integration is upgraded in one run and integrations already current are skipped with a reason, not attempted (FR-014, FR-015)
- [X] T031 [P] [US2] Add tests to `tests/test_version_update.py` capturing the delegated argv and asserting it is `specify integration upgrade <key>` per behind integration — with no `--force`, and with no invocation that would re-point or rescaffold an agent (`integration use`, `integration switch`, `extension add`, `extension update`) anywhere in the captured calls (FR-017, FR-040)
- [X] T032 [P] [US2] Add a test to `tests/test_version_update.py` asserting `default_integration` in `.specify/integration.json` is unchanged after a successful run, a failed run, and an interrupted run (FR-017)
- [X] T033 [P] [US2] Add a test to `tests/test_version_update.py` asserting walk order places the default integration last when it is among the targets (research R3, FR-018)
- [X] T034 [P] [US2] Add tests to `tests/test_version_update.py` asserting a failed integration does not stop the walk, the component's outcome is the worst of its children, and the command exits `EXIT_DELEGATION` (4) (FR-019, FR-023, data-model.md § 5)
- [X] T035 [P] [US2] Add a test to `tests/test_version_update.py` asserting an unknown integration is never attempted, is reported skipped, and does not affect the exit code (FR-015, FR-023)
- [X] T036 [P] [US2] Add a test to `tests/test_version_update.py` asserting exit code 130 from any child aborts the whole walk — including the components after `Core agents` (FR-020)
- [X] T037 [P] [US2] Add a test to `tests/test_version_update.py` asserting per-integration verification: a child whose delegate returns 0 without moving its manifest version renders "reported success, but the version is unchanged" while its sibling renders as updated (FR-022)
- [X] T038 [P] [US2] Add a test to `tests/test_version_update.py` asserting the confirmation plan names each integration to be upgraded with its version transition (FR-016)
- [X] T039 [P] [US2] Add a round-trip test to `tests/test_version_update.py` asserting that after a successful `spectra update` in a project with two behind integrations, a fresh `spectra version` reports `Core agents` up to date with no breakdown — the in-suite form of SC-001

### Implementation for User Story 2

- [X] T040 [US2] Change `delegate_integration_upgrade(key=None, force=False)` in `spectra_cli/extension.py` to append the key then `--force` when given, keeping the bare invocation reachable for the fallback path, per contracts/core-agents.md § 8
- [X] T041 [US2] Replace the docstring on `delegate_integration_upgrade` in `spectra_cli/extension.py`: record that `--force` is now reachable, that it is reachable **only** from an authorized `OverwritePlan`, and that the protected property is unchanged — superseding the note it currently carries (contracts/cli-surface.md § 8)
- [X] T042 [US2] Add an `authorized_keys` parameter to `apply_updates()` in `spectra_cli/health.py` (default empty set) and document that the walk never resolves authorization itself
- [X] T043 [US2] Implement the per-integration inner loop for the `INTEGRATION` component in `apply_updates()` in `spectra_cli/health.py`: target the behind children, order non-default first and default last, delegate per key, record a child `UpdateResult` each, continue past failures, and re-raise `Interrupted` on 130 (depends on T040, T042)
- [X] T044 [US2] Implement the worst-of roll-up (`FAILED` > `UPDATED` > `SKIPPED`) for the component's own outcome in `spectra_cli/health.py`, and record skipped children with their specific reason (depends on T043)
- [X] T045 [US2] Extend `_confirm_updates()` in `spectra_cli/cli.py` so the `Core agents` line names the integrations that will be upgraded (FR-016)
- [X] T046 [US2] Extend `_outcome_row()` in `spectra_cli/cli.py` to emit child rows for the `Core agents` component, each re-reading that integration's manifest version so "success but unchanged" is decided per integration (FR-021, FR-022)

**Checkpoint**: A multi-integration project can be brought fully current by one command, with no project
configuration touched.

---

## Phase 5: User Story 3 - Nothing is overwritten without an informed yes (Priority: P2)

**Goal**: Where an upgrade would be blocked by modified managed files, the exact files are disclosed —
grouped per integration and shared infrastructure — and one question is asked, defaulting to no.

**Independent Test**: In a two-integration project with one behind integration whose managed files are
modified, run `spectra update`, press Enter, and confirm nothing was overwritten, the integration is
reported skipped, and the exit code is 0.

### Tests for User Story 3

- [X] T047 [P] [US3] Add a `ModificationReport` test class to `tests/test_health.py` asserting the `speckit` entry is routed to `shared` and never appears as an integration key (FR-002), that keys absent from the installed list are ignored, that only `--json` invocations are captured so no human-formatted status output is ever parsed (FR-041), and that a clean project yields empty lists with `established=True` (FR-024)
- [X] T048 [P] [US3] Add tests to `tests/test_health.py` asserting `established=False` when `specify` is absent, when the call times out, when it exits non-zero, and when its output is unparseable — with both lists empty in every case (research R6)
- [X] T049 [P] [US3] Add a test to `tests/test_version_update.py` asserting `spectra version` never runs `integration status` — the probe belongs to the update path only (FR-012, research R1)
- [X] T050 [P] [US3] Add tests to `tests/test_version_update.py` asserting candidate reduction: an integration with modified files that is already current produces no disclosure and no prompt (FR-034), and shared-only modifications with every integration current produce neither
- [X] T051 [P] [US3] Add a test to `tests/test_version_update.py` asserting the disclosure lists every affected file, grouped per integration and with shared infrastructure as its own group, and that it is printed **before** any prompt (FR-025)
- [X] T052 [P] [US3] Add a test to `tests/test_version_update.py` seeding a divergence that covers every managed file in the project and asserting the disclosure lists all of them, in full and untruncated (spec Edge Cases, "very large divergence")
- [X] T053 [P] [US3] Add a test to `tests/test_version_update.py` asserting the prompt defaults to no: an empty answer authorizes nothing and overwrites nothing (FR-026)
- [X] T054 [P] [US3] Add a test to `tests/test_version_update.py` asserting a declined overwrite still upgrades the integrations that need none, reports the rest as `skipped (overwrite not authorized)`, and exits 0 (FR-030) — the updated-with-declared-skips half of SC-006
- [X] T055 [P] [US3] Add a test to `tests/test_version_update.py` asserting authorization is limited to candidates — an integration upgradeable without an overwrite is never delegated with `--force` (FR-029)
- [X] T056 [P] [US3] Add a test to `tests/test_version_update.py` asserting the closing message states the two real options and contains no advice to review a difference (FR-035, finding F9), and that a second run asks again (FR-033)
- [X] T057 [P] [US3] Add a guard test to `tests/test_version_update.py` asserting no code path emits `--force` in the delegated argv unless an authorization act was recorded in the same run — the in-suite form of SC-003

### Implementation for User Story 3

- [X] T058 [US3] Implement `modification_report(timeout=...)` in `spectra_cli/health.py` running `specify integration status --json`, routing `speckit` to `shared`, ignoring non-integration keys, and never raising — returning `established=False` on every failure path (FR-024, contracts/core-agents.md § 5)
- [X] T059 [US3] Implement the `OverwritePlan` structure in `spectra_cli/cli.py` with `candidates`, `shared`, `authorized`, and `source`, per data-model.md § 4
- [X] T060 [US3] Implement candidate reduction in `spectra_cli/cli.py`: intersect the modification report with the integrations the walk is about to upgrade, so an integration that is not being upgraded can never trigger a prompt (FR-034) (depends on T058, T059)
- [X] T061 [US3] Implement the disclosure renderer in `spectra_cli/cli.py`: per-integration groups, the shared-infrastructure group, the full file list, and the closing sentence stating the two options — matching contracts/cli-surface.md § 5 (depends on T060)
- [X] T062 [US3] Implement authorization resolution in `spectra_cli/cli.py` per the contracts/cli-surface.md § 5 matrix, using `ui.confirm(..., default_yes=False)` for the interactive branch and refusing to authorize anything when `established` is `False` (depends on T061)
- [X] T063 [US3] Pass the resolved `authorized` set from `cmd_update()` into `health.apply_updates()` in `spectra_cli/cli.py`, and record unauthorized candidates as skipped with the remedy (depends on T042, T062)
- [X] T064 [US3] Add the closing remedy message to `cmd_update()` in `spectra_cli/cli.py` naming each integration left behind, its version, and both options (FR-030, FR-035)

**Checkpoint**: A project with modified managed files can be updated on the user's terms, and cannot lose
a file without an informed yes.

---

## Phase 6: User Story 4 - Automation cannot destroy local work (Priority: P2)

**Goal**: With no terminal attached, `--yes` updates what it can, skips what would require an overwrite,
and names `--force`.

**Independent Test**: With stdin closed and modified managed files present, run `spectra update --yes` and
confirm no file was overwritten, `--force` is named, nothing hung, and the exit code is 0.

### Tests for User Story 4

- [X] T065 [P] [US4] Add a `NonInteractive` test class to `tests/test_version_update.py` asserting `--yes` with no TTY overwrites nothing, skips the affected integrations, and names `--force` in the output (FR-027, FR-031, SC-007)
- [X] T066 [P] [US4] Add a test to `tests/test_version_update.py` asserting `--force` with no TTY proceeds **and** still prints the disclosure (FR-032)
- [X] T067 [P] [US4] Add a test to `tests/test_version_update.py` asserting no prompt is attempted when stdin is not a TTY — the run cannot block (FR-031)
- [X] T068 [P] [US4] Add a test to `tests/test_version_update.py` asserting `--force` with no candidates changes nothing and writes no additional files (spec US4 scenario 5)
- [X] T069 [P] [US4] Add tests to `tests/test_cli_surface.py` asserting `--force` is accepted by `spectra update`, rejected with `EXIT_USAGE` (2) at the top level and on other subcommands, and that its help line states the consequence (FR-028, contracts/cli-surface.md § 2)

### Implementation for User Story 4

- [X] T070 [US4] Register `--force` on the `update` subparser only in `build_parser()` in `spectra_cli/cli.py`, deliberately not in `_add_shared`, per research R5
- [X] T071 [US4] Add the `--force` help line to the options panel copy in `spectra_cli/cli.py`, stating that it overwrites locally modified managed files rather than that it forces something (FR-028)
- [X] T072 [US4] Read the flag as `bool(getattr(args, "force", False))` in `cmd_update()` in `spectra_cli/cli.py`, since the attribute is absent from other subcommand namespaces (depends on T062, T070)

**Checkpoint**: Unattended runs are non-destructive by default and destructive only on an explicit,
named flag.

---

## Phase 7: User Story 5 - The agent-coverage gap is visible (Priority: P3)

**Goal**: An installed integration with no Spectra commands is named, with the exact remedy and its side
effect — and nothing is changed.

**Independent Test**: In `~/Projects/willow`, where the registry records Spectra commands for `kiro-cli`
only, run `spectra version` and confirm the advisory names `claude`, the remedy, and the consequence.

### Tests for User Story 5

- [X] T073 [P] [US5] Add a `RegisteredAgents` test class to `tests/test_extension.py` covering `registered_agents`: a two-agent map, a one-agent map, a missing registry, unreadable JSON, no `spectra` entry, and an empty command map — the last four returning `None` (FR-036)
- [X] T074 [P] [US5] Add tests to `tests/test_version_update.py` asserting the advisory names every uncovered integration, the `specify integration use <key>` remedy, and the default-integration side effect (FR-037, SC-008); is absent when coverage is complete, when the registry is unreadable (FR-039), and when no default integration is recorded; and never changes the exit code (FR-038)
- [X] T075 [P] [US5] Add a test to `tests/test_version_update.py` asserting the advisory is rendered outside the four rows and that a single-integration project never shows it (FR-038, FR-012)

### Implementation for User Story 5

- [X] T076 [US5] Implement `registered_agents(project_root)` in `spectra_cli/extension.py` reading `extensions.spectra.registered_commands` from `.specify/extensions/.registry` and returning its keys, or `None` for every unreadable or absent case (FR-036, contracts/core-agents.md § 7)
- [X] T077 [US5] Implement the advisory renderer in `spectra_cli/cli.py`, called from `cmd_version()` after the table and any update hint, naming each uncovered integration and its remedy, suppressed entirely when `registered_agents` returns `None` (depends on T076)

**Checkpoint**: All five stories are independently functional.

---

## Phase 8: Polish & Cross-Cutting Concerns

- [X] T078 Bump the root `VERSION` from `6.0.0` to `6.1.0` — minor, because `--force` is additive and nothing is removed (plan.md § Principle VI obligations)
- [X] T079 Record the supersession in `specs/007-unified-version-update/contracts/health-check.md`: annotate the "Neither passes `--force`" paragraph with a pointer to `specs/010-multi-integration-updates/contracts/cli-surface.md` § 8, keeping the original reasoning visible
- [X] T080 Update `README.md` § "Keeping everything up to date": the four-component table copy, the multi-integration behaviour of `Core agents`, and the new `--force` flag on `spectra update`
- [X] T081 Update `docs/index.html` § "Keep the whole stack current" with the multi-integration behaviour of `Core agents` and a `Changed in 6.1.0` note naming `--force`, matching the existing `5.0.0` / `6.0.0` convention in that block
- [X] T082 [P] Verify `spectra/extension.yml` and `catalog.json` versions are **unchanged** and `python3 tools/generate_agent_docs.py --check` is green — no agent or roster data moved (plan.md, Principle V)
- [X] T083 [P] Confirm every new docstring records its decision rather than restating its code, matching the module's existing style: aggregation precedence in `health.py`, authorization gating in `extension.py`, disclosure grouping in `cli.py`
- [X] T084 Run the full suite on both CI interpreters (`python3.9` and `python3.12` if available locally, otherwise confirm via CI), confirm no pre-existing test was modified to accommodate the change, and assert the Specify CLI, Spectra CLI, and Spectra agents rows are byte-identical in a multi-integration project (FR-042)
- [X] T085 Execute every scenario in `specs/010-multi-integration-updates/quickstart.md`, including the byte-identical diff against the 6.0.0 release for a single-integration project (SC-005) and the read-only checks in `~/Projects/willow`. Scenario 4 is the evidence for SC-004 (four commands become one) and Scenario 5 on the F3 fixture is the evidence for SC-006, since `~/Projects/willow` itself must not be mutated
- [X] T086 Confirm the three explicit exclusions still hold: no fifth report row (FR-011), no new top-level command, and no persisted overwrite setting anywhere on disk (FR-033)
- [X] T087 Clean up the scratch directories the quickstart creates (`/tmp/spectra-multi`, `/tmp/spectra-solo`, `/tmp/spectra-legacy`, `/tmp/prev`) and confirm `git status` is clean apart from intended changes

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately.
- **Foundational (Phase 2)**: Depends on Setup. **BLOCKS every user story** — the fixtures are what make
  any of it testable, and the three structures are what the stories write into.
- **US1 (Phase 3)**: Depends on Phase 2 only.
- **US2 (Phase 4)**: Depends on US1 — the walk consumes `IntegrationState` children produced there.
- **US3 (Phase 5)**: Depends on US2 — the disclosure is reduced to the integrations the walk will upgrade.
- **US4 (Phase 6)**: Depends on US3 — it is the non-interactive resolution of the same authorization.
- **US5 (Phase 7)**: Depends on US1 only. **Independent of US2–US4** and can be built or shipped at any
  point after the report exists.
- **Polish (Phase 8)**: Depends on all shipped stories. T078–T080 can be done earlier if a release is cut
  mid-way, but T085 needs everything.

### Story Dependency Graph

```text
Phase 2 (fixtures + structures)
        │
        ▼
      US1  ── detection & reporting  ──►  US5  (advisory; independent of the rest)
        │
        ▼
      US2  ── the walk
        │
        ▼
      US3  ── disclosure & consent
        │
        ▼
      US4  ── non-interactive resolution
```

### Within Each User Story

- Tests are written first and MUST fail before the implementation tasks in that phase.
- Readers before judges: `read_*` before `get_integration_states` before `aggregate_*`.
- Detection before presentation: `health.py` before `cli.py` in every phase.
- Authorization before delegation: no task may pass `force=True` before T062 exists.

### Parallel Opportunities

- T009–T011 are three separate structures in one file section — do them in one sitting, or in parallel by
  different people if the file is split by conflict-free hunks.
- Every test task within a phase is `[P]`: they touch different test classes.
- T013–T021 (nine US1 test classes) parallelize fully.
- US5 (T073–T077) can run in parallel with all of US2–US4 once US1 lands.
- T082 and T083 are independent of each other and of T084.

---

## Parallel Example: User Story 1 tests

```bash
# Nine independent test classes, two files, no shared state:
Task: "InstalledIntegrations in tests/test_health.py"          # T013
Task: "PerIntegrationVersion in tests/test_health.py"          # T014
Task: "PerIntegrationVerdict in tests/test_health.py"          # T015
Task: "Aggregation in tests/test_health.py"                    # T016
Task: "Derived row fields in tests/test_health.py"             # T017
Task: "Fallback in tests/test_health.py"                       # T018
Task: "RecordPrecedence in tests/test_health.py"                # T019
Task: "Four rows + breakdown in tests/test_version_update.py"  # T020
Task: "Single-integration regression in tests/test_version_update.py"  # T021
```

## Parallel Example: two developers after US1

```bash
# Developer A — the update path:
Phase 4 (US2)  ->  Phase 5 (US3)  ->  Phase 6 (US4)

# Developer B — the advisory, fully independent:
Phase 7 (US5)  ->  T080 README copy  ->  T082 catalog/roster verification
```

---

## Implementation Strategy

### MVP First (US1 only)

1. Phase 1: Setup — capture the 343-test baseline.
2. Phase 2: Foundational — fixtures and structures (**blocks everything**).
3. Phase 3: US1 — detection and reporting.
4. **STOP and VALIDATE**: run `spectra version` in `~/Projects/willow`; the row that reports up to date
   today must report needs-updating and name both integrations.
5. Shippable: the silent drift is over even though updating has not changed.

### Incremental Delivery

1. Setup + Foundational → fixtures ready.
2. US1 → truthful report → **MVP**.
3. US2 → one command updates every integration.
4. US3 → the dead-end project becomes updatable, safely.
5. US4 → automation is safe by default.
6. US5 → the coverage gap stops being silent.
7. Polish → version bump, README, supersession, quickstart.

Each step leaves the CLI in a shippable state, and none of them changes behaviour for a
single-integration project.

---

## Notes

- **[P] tasks** = different files or different test classes, no dependencies.
- **The riskiest task in the list is T062** (authorization resolution). It is the only place that can
  cause irreversible loss, T057 is its guard test, and both should be reviewed together.
- **Never edit an existing test to make a new behaviour pass.** T084 exists to catch exactly that; a
  pre-existing test that fails is a signal the single-integration path changed, which FR-012 forbids.
- **`--force` has one caller.** If a second appears, the SC-003 guarantee is gone.
- Commit after each task or logical group; stop at any checkpoint to validate a story on its own.
- Avoid: a fifth report row, a new command, parsing human-formatted `specify` output, or switching the
  project's default integration for any reason.
