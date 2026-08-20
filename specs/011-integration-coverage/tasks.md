# Tasks: Full Integration Coverage on Install and Update

**Input**: Design documents from `/specs/011-integration-coverage/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md — all present

**Tests**: **Included.** Five success criteria are direct assertions about behaviour (SC-002 "zero runs
end with a changed default", SC-003 "survives in 100% of runs", SC-005 "zero files overwritten", SC-006
"output identical to the previous release", SC-013 "zero textual changes to committed configuration"), and
the feature's central act — moving a shared, committed setting and putting it back — is only trustworthy
if a test proves the restoration on every failure path. Every story phase leads with its tests.

**Organization**: Grouped by user story. US1 delivers the coverage step and the rotation; US2 reuses it
from the update; US3 is a separate install-flow change that needs only the plan from US1; US4 hardens the
restoration paths US1 introduces; US5 is a guard on US1 and US2; US6 is fully independent of everything
after US1's detection exists.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US6)

## Path Conventions

Single package at repository root: `spectra_cli/` for source, `tests/` for tests, `test/` for the
containerized harness. No `src/` directory — paths below are literal.

---

## Phase 1: Setup

**Purpose**: Record the baseline and re-confirm the dependency behaviours the whole design rests on, so a
later regression is attributable to us or to Spec Kit rather than ambiguous.

- [ ] T001 Record the pre-change test baseline by running `python3 -m unittest discover -s tests` and noting the count (expected: 455 tests, OK)
- [ ] T002 Re-confirm findings F1, F2, F3 in a disposable project: `specify init` with one integration, `specify integration install <second> --force`, `specify extension add --dev ./spectra`, then read `.specify/extensions/.registry` (expect the default only), then `specify integration use <second>` and re-read it (expect both keys), then `specify integration use <default>` and re-read (expect both keys, default restored)
- [ ] T003 Re-confirm finding F4 in the same project by editing `.specify/scripts/bash/check-prerequisites.sh` and running `specify integration use <second>` — expect a "Preserved … customized shared infrastructure file(s)" warning and exit 0, never a failure
- [ ] T004 Capture the byte snapshots the FR-044 gate needs: copy `.specify/integration.json` and `.specify/init-options.json` aside, run a full rotation by hand, and `diff` them afterwards — record the result in the task notes, because it decides whether FR-044's fallback must be built (research R9)
- [ ] T005 Delete the disposable project from T002–T004 with `rm -rf` and confirm nothing was written outside it — in particular that `/Users/alibahaloo/Projects/spectra/.specify/` is untouched

**Checkpoint**: The three load-bearing dependency behaviours are re-verified against the installed Spec
Kit, and the FR-044 question is answered with evidence rather than assumption.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The delegation, the detection, and the plan. Every user story reads from these, and none can
begin until they exist.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T006 Add `delegate_integration_use(key)` to `spectra_cli/extension.py`: `specify integration use <key>`, no `force` parameter in the signature at all, `DelegationError` when `specify` is absent, 130 on `KeyboardInterrupt` — with a docstring stating why the overwrite flag is deliberately not expressible here, citing F4. This is the sole mechanism by which coverage is established (contracts/coverage.md § 6, FR-008, FR-009, FR-049)
- [ ] T007 [P] Add an extension-presence helper to `spectra_cli/project.py` that answers "is extension `<id>` present in this project?" for an arbitrary id, without overloading `classify()` (research R6)
- [ ] T008 Create `spectra_cli/coverage.py` with the module docstring explaining the rotation, why activation is the only mechanism (F6), and that the restoration is an obligation rather than a step
- [ ] T009 Implement `CoverageState`, `CoverageOutcome`, `CoverageResult`, and the `COVERED`/`UNCOVERED`/`UNKNOWN` and `NOT_NEEDED`/`RESTORED`/`NOT_RESTORED` constants in `spectra_cli/coverage.py` per data-model.md, with `__slots__` matching the house style
- [ ] T010 Implement `coverage.plan(project_root)` in `spectra_cli/coverage.py`: read membership via `health.read_installed_integrations`, the default via `health.read_default_integration`, and coverage via `extension.registered_agents`; exclude the default from `targets`; ignore registry keys absent from the installed list (FR-001, FR-002, FR-005, FR-011)
- [ ] T011 Implement the five empty-plan reasons in `coverage.plan` with the exact wording in data-model.md § CoveragePlan, including the unknown-coverage case that must never read as "nothing is covered" (FR-003, FR-004, FR-012, FR-022)
- [ ] T012 Implement the derived properties `needed`, `moves_default`, and `activations` in `spectra_cli/coverage.py`, with `activations` always ending in `default_key` (FR-015)
- [ ] T013 Decide and implement where the process exit codes live so `spectra_cli/install.py` can return them: `cli.py` already imports `install.py`, so the `EXIT_*` constants cannot be imported back from it. Move them to a neutral `spectra_cli/exits.py`, re-export the existing names from `spectra_cli/cli.py` so `cli.EXIT_OK` still resolves for current tests, and import them in `spectra_cli/install.py` (contracts/cli-surface.md § 1, research R13)

**Checkpoint**: Detection and planning are complete and pure — no subprocess, no terminal, no writes — so
every property in data-model.md § Validation rules is assertable without a stub.

---

## Phase 3: User Story 1 - Installing Spectra covers every agent in the project (Priority: P1) 🎯 MVP

**Goal**: `spectra install` leaves every installed integration carrying Spectra's commands, and the
project's default integration is exactly what it was when the run started.

**Independent Test**: In a two-integration project with one uncovered, run `spectra install`; both
integrations end up registered, the recorded default and active agent are unchanged, and the run stated
before acting that the default would move and be restored (quickstart Scenario 1).

### Tests for User Story 1

> Write these first and confirm they fail before implementing T024–T029.

- [ ] T014 [P] [US1] Extend `tests/helpers.py::fake_specify` with an argv log — every invocation appended to a file the test reads — so rotation order and the restoring call are assertable without parsing human output (research R10)
- [ ] T015 [P] [US1] Extend `tests/helpers.py::fake_specify` with an optional `integration use` side effect that rewrites `.specify/extensions/.registry` to add the activated key and rewrites `default_integration` in `.specify/integration.json`, so verification and restoration run against changing state (research R10)
- [ ] T016 [P] [US1] Create `tests/test_coverage.py` with plan tests: `targets` excludes the default and every covered key — which is what guarantees existing coverage is never re-registered or replaced — excludes keys absent from the installed list, and `activations` always ends with the default (FR-010, FR-011, FR-002, FR-015)
- [ ] T017 [P] [US1] Add tests to `tests/test_coverage.py` for all five empty-plan reasons, asserting `needed is False`, empty `activations`, and the exact `skip_reason` wording
- [ ] T018 [P] [US1] Add a rotation-order test to `tests/test_coverage.py` asserting the argv log equals `targets + [default]`, in order, for a two- and a three-integration project
- [ ] T019 [P] [US1] Add a verification test to `tests/test_coverage.py`: an activation that exits 0 without the registry changing is reported `FAILED` with the wording in contracts/coverage.md § 3, never `NEWLY_COVERED` (FR-006)
- [ ] T020 [P] [US1] Add the FR-013 test to `tests/test_coverage.py`: when only the default is uncovered, exactly one activation occurs, `restoration` is `NOT_NEEDED`, and `moves_default` is `False`
- [ ] T021 [P] [US1] Create `tests/test_install.py` asserting step 4 appears, the disclosure names the default to be restored before any activation, the run reports which integrations were covered, and the whole step costs at most one line per integration plus one disclosure and one restoration confirmation — five lines for a three-integration project (FR-014, FR-033, SC-011)
- [ ] T022 [P] [US1] Add a test to `tests/test_install.py` asserting `.specify/integration.json` and `.specify/init-options.json` are byte-identical before and after a stubbed rotation, and that the recorded default and active agent match their pre-run values (FR-043, SC-002, SC-013)
- [ ] T023 [P] [US1] Add a no-TTY test to `tests/test_install.py` asserting a non-interactive `spectra install` performs the coverage step on the same terms as an interactive one — the step is non-destructive and self-reversing, so it is not withheld from automated provisioning (FR-019)

### Implementation for User Story 1

- [ ] T024 [US1] Implement `coverage.apply(plan, announce=None)` in `spectra_cli/coverage.py` following contracts/coverage.md § 2 line for line, including `moved` being set immediately after each call returns rather than only on success. Every state change goes through `extension.delegate_*`; the module writes no agent command file, no skill file, and no registration record itself (FR-007, FR-008)
- [ ] T025 [US1] Implement the `try`/`finally` restoration in `coverage.apply` with the three verdicts, attempting the restoring activation exactly once and never retrying (FR-015, FR-016, research R4)
- [ ] T026 [US1] Implement `coverage.Interrupted` and raise it after the `finally` has restored, for both `KeyboardInterrupt` and a delegated exit code of 130 (FR-036)
- [ ] T027 [US1] Implement the post-rotation verification and aggregate precedence in `spectra_cli/coverage.py` per contracts/coverage.md § 3 and § 4, re-reading the registry rather than trusting exit codes (FR-006, FR-032)
- [ ] T028 [US1] Add the coverage step to `spectra_cli/install.py` as step 4, printing the header, the disclosure, one line per activation, and the restoration confirmation exactly as contracts/cli-surface.md § 1 specifies — and printing nothing when the plan is empty (FR-017, FR-018, FR-037)
- [ ] T029 [US1] Make `spectra_cli/install.py` compute the plan before printing step 1 so the step count is 3 or 4 correctly, never `[1/4]` followed by no fourth step (contracts/cli-surface.md § 1)

**Checkpoint**: `spectra install` covers every integration in a multi-agent project and returns the
default unchanged. Quickstart Scenario 1 passes end to end.

---

## Phase 4: User Story 2 - Updating Spectra keeps every agent covered (Priority: P1)

**Goal**: `spectra update` re-establishes coverage after the component walk instead of silently deleting
it for every non-default agent.

**Independent Test**: With both agents covered and the extension behind, run `spectra update`, accept the
coverage question, and confirm both agents are still covered and the default is unchanged; then decline on
a second run and confirm nothing was activated (quickstart Scenario 4).

### Tests for User Story 2

- [ ] T030 [P] [US2] Add tests to `tests/test_version_update.py` for the coverage question: asked exactly once, defaulting to no, with the disclosure naming the integrations and the default to be restored (FR-025, FR-026)
- [ ] T031 [P] [US2] Add a test to `tests/test_version_update.py` asserting `--yes` proceeds with no prompt, and that `--force` is never consulted for coverage — no overwrite prompt or flag originates from the coverage path, and no modified managed file is overwritten by it (FR-027, FR-009, SC-005)
- [ ] T032 [P] [US2] Add a declined-run test to `tests/test_version_update.py`: nothing activated, default unchanged, uncovered integrations named with `spectra install` as the remedy the user can run verbatim, and the exit code unaffected (FR-029, FR-030, SC-007)
- [ ] T033 [P] [US2] Add a no-TTY test to `tests/test_version_update.py`: nothing activated and the skip names `--yes` as what would authorize it (FR-028)
- [ ] T034 [P] [US2] Add a test to `tests/test_version_update.py` asserting coverage is evaluated even when the Spectra agents were already current and nothing was updated (FR-024)
- [ ] T035 [P] [US2] Add a test to `tests/test_version_update.py` asserting the coverage row group renders in the outcome table with one child line per integration, that **no** fifth row appears in the health table, and that the health table, its verdicts, the overwrite disclosure, and the per-integration upgrade rows are unchanged from the previous release (FR-031, FR-032, research R7)

### Implementation for User Story 2

- [ ] T036 [US2] Add the coverage step to `cmd_update` in `spectra_cli/cli.py` at position 6 of contracts/cli-surface.md § 3 — after the post-walk re-read, before the outcome table
- [ ] T037 [US2] Implement the coverage question in `spectra_cli/cli.py`: one prompt defaulting to no, `--yes` as the only authorization, no prompt and no activation without a TTY (FR-025, FR-027, FR-028)
- [ ] T038 [US2] Render the coverage outcome as a fifth row group in the outcome table using the existing `_outcome_row` / child-row helpers in `spectra_cli/cli.py` (FR-032)
- [ ] T039 [US2] Wire the coverage result into the failure and exit-code handling in `cmd_update` so a failed activation or `NOT_RESTORED` returns `EXIT_DELEGATION` while a decline changes nothing (FR-029, research R8)
- [ ] T040 [US2] Update `_say_what_happened` in `spectra_cli/cli.py` so the closing line does not claim completeness when coverage was declined, matching the rule it already applies to a declined overwrite

**Checkpoint**: Coverage survives an update. The regression where the extension update deletes the
non-default agent's commands is closed.

---

## Phase 5: User Story 3 - A partially covered project is repaired by re-running the install (Priority: P2)

**Goal**: `spectra install` in an already-installed project reports success and repairs coverage instead
of failing on the extension step.

**Independent Test**: In a project where Spectra is installed and one integration is uncovered, run
`spectra install`; it exits 0, reports the extension as already present, and covers the uncovered
integration (quickstart Scenario 2).

### Tests for User Story 3

- [ ] T041 [P] [US3] Add tests to `tests/test_install.py`: an already-present extension is reported as present, is not re-downloaded, and the run exits 0 after coverage — one command, no dependency documentation needed (FR-020, FR-023, SC-004)
- [ ] T042 [P] [US3] Add a test to `tests/test_install.py` asserting the already-present decision is made from project state, with no dependency message text anywhere in the code path (FR-021)
- [ ] T043 [P] [US3] Add a test to `tests/test_install.py`: an extension step that fails for another reason still exits non-zero, and coverage still runs when an extension is present from an earlier run, reported separately (FR-022)
- [ ] T044 [P] [US3] Add a test to `tests/test_install.py`: an extension step that fails with nothing installed skips coverage as inapplicable and reports only the extension failure (FR-022)
- [ ] T045 [P] [US3] Add a test to `tests/test_install.py` asserting an `INCOMPLETE` extension folder is treated as absent, so the add is attempted (research R6)

### Implementation for User Story 3

- [ ] T046 [US3] Add the pre-attempt presence check to `add_catalog` in `spectra_cli/install.py` using the T007 helper, per extension id from `catalog_extension_ids()`, skipping the add for ids already present (FR-020, FR-021, research R6)
- [ ] T047 [US3] Print the already-present message from contracts/cli-surface.md § 2 and continue to step 4, without claiming anything was installed or downloaded (FR-020)
- [ ] T048 [US3] Make `run_install` in `spectra_cli/install.py` return the clarified exit contract: zero for covered or stated-skip, non-zero for an attempted-and-failed coverage, and the extension failure's code preserved when it fails — so no run reports success after an attempted coverage step left an integration uncovered (FR-017, FR-022, SC-012, spec § Clarifications)

**Checkpoint**: Every project that predates this feature can be repaired by one command.

---

## Phase 6: User Story 4 - The project's default is never left changed (Priority: P2)

**Goal**: The restoration holds on every path — a failed activation, an interrupt, and a failed restore —
and where it cannot be completed the user is handed the exact command that fixes it.

**Independent Test**: Interrupt a rotation between activations and confirm the default is restored, the
already-covered integration stays covered, and the run reports an interruption; then force the restoring
activation to fail and confirm the recovery command is printed (quickstart Scenarios 6 and 7).

### Tests for User Story 4

- [ ] T049 [P] [US4] Add a test to `tests/test_coverage.py`: an activation that fails still restores the default, the remaining targets are still attempted, and the failure is attributed to its integration (FR-015, FR-016, FR-035)
- [ ] T050 [P] [US4] Add an interrupt test to `tests/test_coverage.py`: `KeyboardInterrupt` mid-rotation restores the default, raises `coverage.Interrupted`, and leaves already-covered integrations covered (FR-016, FR-036)
- [ ] T051 [P] [US4] Add a failed-restore test to `tests/test_coverage.py`: `restoration` is `NOT_RESTORED` and `current_default` differs from `original_default` (FR-034)
- [ ] T052 [P] [US4] Add a test to `tests/test_install.py` asserting the `NOT_RESTORED` output names the current default, the original, and the verbatim recovery command, and that the run exits 4 — no run ends with a changed default without printing the command that restores it (FR-034, SC-008, research R8)
- [ ] T053 [P] [US4] Add a test to `tests/test_install.py` asserting an interrupt exits 130 and is reported as an interruption, not a failure — then run `spectra install` again in the same interrupted project and assert it completes coverage, so the interrupted state is provably repairable rather than merely tidy (FR-036, SC-010)
- [ ] T054 [P] [US4] Add a test to `tests/test_coverage.py` asserting no activation is attempted when no default is recorded, with the reason reported (FR-012)

### Implementation for User Story 4

- [ ] T055 [US4] Implement the `NOT_RESTORED` reporting in `spectra_cli/install.py` and `spectra_cli/cli.py` per contracts/cli-surface.md § 1, the only place `specify integration use` is printed as advice (FR-034, FR-040)
- [ ] T056 [US4] Implement the interrupt path in both callers: report the interruption, return `EXIT_INTERRUPTED`, and never present it as a component failure (FR-036, research R8)
- [ ] T057 [US4] Verify by inspection that every `return` and `raise` in `coverage.apply` passes through the `finally`, and record that check in the module docstring so a later edit cannot quietly bypass it (FR-016)

**Checkpoint**: The restoration guarantee holds on all four failure paths and is proven by test rather
than by reading.

---

## Phase 7: User Story 5 - Single-integration projects notice nothing (Priority: P3)

**Goal**: The majority case gains no step, no question, and no line of output.

**Independent Test**: In a one-integration project, run `spectra install` and `spectra update` and diff
the output against the previous release; only version numbers may differ (quickstart Scenario 3).

### Tests for User Story 5

- [ ] T058 [P] [US5] Add a test to `tests/test_install.py` asserting a single-integration covered project prints `[1/3]`…`[3/3]`, no step 4, and performs no activation (FR-038, SC-006)
- [ ] T059 [P] [US5] Add a test to `tests/test_version_update.py` asserting a single-integration covered project's update output and prompts are unchanged — no coverage question, no coverage row (FR-037, FR-038)
- [ ] T060 [P] [US5] Add a test to `tests/test_install.py` and `tests/test_version_update.py` asserting a multi-integration project where every integration is covered produces no coverage output in either command (FR-037)
- [ ] T061 [P] [US5] Add a test to `tests/test_cli_surface.py` asserting the rendered help and `OPTIONS` are unchanged — no new flag, no new environment variable (FR-018, FR-047)

### Implementation for User Story 5

- [ ] T062 [US5] Confirm the silence is a property of the empty plan rather than of each caller, and add the assertion to `tests/test_coverage.py` that an empty plan yields no `activations` (research R11)
- [ ] T063 [US5] Extend the source scan in `tests/test_no_hardcoded_agents.py` to cover `spectra_cli/coverage.py`: no integration key as a literal (FR-046), no `integration install` / `integration remove` / `integration switch` invocation anywhere in the module (FR-045), and no network or credential import (FR-048)

**Checkpoint**: The feature is invisible to the projects it does not serve.

---

## Phase 8: User Story 6 - Where coverage cannot be completed, the report still explains it (Priority: P3)

**Goal**: The advisory survives for the declined and unknowable cases, and points at a command that is
safe to run.

**Independent Test**: In a partially covered project, run `spectra version` and confirm the advisory names
the uncovered integration and gives `spectra install` as the remedy, with nothing changed and the exit
code unaffected (quickstart Scenario 8).

### Tests for User Story 6

- [ ] T064 [P] [US6] Update the advisory tests in `tests/test_version_update.py` (where they live today, alongside the `write_registry` fixture in `tests/helpers.py` — **not** `tests/test_health.py`) to expect `Add them with: spectra install` and to assert the two lines about changing the project's default are gone (FR-039, FR-040)
- [ ] T065 [P] [US6] Add a test to `tests/test_version_update.py` asserting the advisory stays silent when coverage is unknown, when everything is covered, and when fewer than two integrations are installed (FR-041)
- [ ] T066 [P] [US6] Add a test to `tests/test_version_update.py` asserting the advisory changes nothing in the project and does not affect the exit code (FR-042)

### Implementation for User Story 6

- [ ] T067 [US6] Reword `_show_coverage_advisory` in `spectra_cli/cli.py` per contracts/cli-surface.md § 4, removing the `specify integration use` remedy and the two lines about changing the default for everyone, so one command run tells a developer which agents have Spectra and what to do about the ones that do not (FR-039, FR-040, SC-009)
- [ ] T068 [US6] Confirm in `spectra_cli/cli.py` that the advisory remains below the four rows in `_show_health`'s output and never becomes a fifth row in the health table (FR-042, research R7)

**Checkpoint**: All six stories are independently functional.

---

## Phase 9: Polish & Cross-Cutting Concerns

- [ ] T069 Add the end-to-end coverage scenario to `test/scenarios.sh`: build a second real integration, run `spectra install`, and assert both agents' command directories are populated; then run `spectra update` and assert they still are (SC-001, SC-003)
- [ ] T070 Add the FR-044 gate to `test/scenarios.sh`: snapshot `.specify/integration.json` and `.specify/init-options.json` byte-for-byte before a coverage run against a real Spec Kit and fail on any difference (FR-044, SC-013)
- [ ] T071 If T070 fails, implement FR-044's fallback — name the affected files in the disclosure and make the coverage step declinable, including in `spectra install` — and record the decision in `research.md` § R9; if it passes, record that instead
- [ ] T072 [P] Bump `VERSION` from `6.1.0` to `6.2.0` and confirm `spectra/extension.yml` and `catalog.json` are untouched (Principle VI)
- [ ] T073 [P] Update `README.md` § "Projects with more than one agent installed" and § "Keeping everything up to date": install and update now cover every installed integration, the default is changed only transiently and restored, and the advisory no longer names `specify integration use` (FR-050)
- [ ] T074 [P] Add the recovery step for an abandoned run to `README.md` — the one-line `specify integration use <original>` — so a default left changed is diagnosable without support (FR-050, BRD-007 § 12)
- [ ] T075 [P] Add a "Changed in 6.2.0" note to `docs/index.html` alongside the existing 6.1.0, 6.0.0, and 5.0.0 notes (FR-050, Principle VI)
- [ ] T076 [P] Add the supersession cross-note to `specs/010-multi-integration-updates/contracts/cli-surface.md` § Supersession pointing at this feature's contract, so the two do not disagree about whether the default may move (contracts/cli-surface.md § 7)
- [ ] T077 [P] Add `requires.speckit_version` confirmation to the task notes: record 0.16.5 as the version this behaviour was verified against, without introducing any run-time version gate (FR-051)
- [ ] T078 Run `python3 -m unittest discover -s tests` and confirm the count rose from 455 with no failures; a run that adds tests but leaves the total at 455 has exercised nothing. Zero pre-existing tests may be deleted or weakened — that is what holds FR-031 (FR-031)
- [ ] T079 Run every quickstart scenario by hand, including the interrupt and failed-restore paths, and record the observed exit codes against the table in contracts/cli-surface.md
- [ ] T080 Run `python3 tools/generate_agent_docs.py --check` and confirm it stays green — no agent changed, so no generated region may move (Principle V)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies. T004 decides whether T071 is needed, so it must complete before Phase 9.
- **Foundational (Phase 2)**: depends on Setup. **Blocks every story** — T006 is the only delegation, and T010–T012 are the plan every story reads.
- **US1 (Phase 3)**: depends on Phase 2. Delivers `coverage.apply`, which US2 and US4 consume.
- **US2 (Phase 4)**: depends on Phase 2 and on T024–T027 from US1 (`apply` must exist to be called).
- **US3 (Phase 5)**: depends on Phase 2 only. It needs the plan, not the rotation, so it can proceed in parallel with US1's implementation.
- **US4 (Phase 6)**: depends on US1's T024–T026. It hardens paths US1 creates.
- **US5 (Phase 7)**: depends on Phase 2 for T062–T063; T058–T061 can be written any time after Phase 2.
- **US6 (Phase 8)**: depends on Phase 2 only. Fully independent of US1–US5.
- **Polish (Phase 9)**: depends on every story intended for the release.

### Story Dependency Graph

```text
Phase 2 (foundational: delegation + plan)
   ├── US1 (rotation, install step 4) ──┬── US2 (update coverage step)
   │                                    └── US4 (restoration hardening)
   ├── US3 (already-installed install path)     [parallel with US1]
   ├── US5 (silence guards)                     [parallel with US1]
   └── US6 (advisory rewording)                 [parallel with everything]
```

### Within Each User Story

- Tests are written and confirmed failing before the implementation tasks in the same phase.
- The plan (data) before the rotation (behaviour); the rotation before its callers.
- A story is complete and its checkpoint validated before the next priority starts.

### Parallel Opportunities

- T007 runs alongside T006 (different files).
- Every test task marked [P] within a phase can be written in parallel — they touch different files or
  disjoint regions of one.
- US3, US5, and US6 can each be implemented in parallel with US1 by a second developer.
- Phase 9's documentation tasks (T072–T077) are all [P] and independent of one another.

---

## Parallel Example: User Story 1 tests

```bash
# Fixtures first, since the later tests consume them:
Task: "T014 argv log in tests/helpers.py"
Task: "T015 integration use side effect in tests/helpers.py"   # same file — sequence these two

# Then, genuinely parallel:
Task: "T016 plan tests in tests/test_coverage.py"
Task: "T018 rotation-order test in tests/test_coverage.py"
Task: "T021 install disclosure test in tests/test_install.py"
Task: "T022 byte-identical configuration test in tests/test_install.py"
```

## Parallel Example: two developers after Phase 2

```bash
# Developer A — the rotation and its callers:
US1 (T014–T029) → US2 (T030–T040) → US4 (T049–T057)

# Developer B — the independent surfaces:
US3 (T041–T048) → US6 (T064–T068) → US5 (T058–T063)
```

---

## Implementation Strategy

### MVP First (US1 only)

1. Complete Phase 1 (baseline and dependency re-verification).
2. Complete Phase 2 (delegation, detection, plan) — blocks everything.
3. Complete Phase 3 (US1).
4. **STOP and VALIDATE**: quickstart Scenario 1 in a real two-integration project. Confirm both agents
   covered, default unchanged, and configuration files byte-identical.
5. At this point the headline problem is fixed for new installs.

### Incremental Delivery

1. Phase 1 + Phase 2 → foundation ready.
2. US1 → install covers every agent → validate → demo.
3. US2 → update stops deleting coverage → validate → demo. **Ship no release without this**: US1 alone is
   undone by the first `spectra update`.
4. US3 → the installed base becomes repairable.
5. US4 → the restoration guarantee is proven on every failure path.
6. US5 + US6 → the majority case stays silent and the advisory tells the truth.
7. Phase 9 → docs, version bump, end-to-end gate.

### Release gate

Do not tag until: T070 passes (or T071 is done), T078 shows a risen count with no failures, T079's
observed exit codes match the contract, and T072–T076 are complete. The version bump without the README
and landing-page updates is exactly the drift Principle V and VI exist to prevent.

---

## Notes

- [P] tasks = different files, no dependencies on incomplete work.
- Two tasks touching `tests/helpers.py` (T014, T015) are marked [P] relative to other files but must be
  sequenced against each other.
- The tests are not optional here: five success criteria are "zero occurrences" assertions, and the
  restoration promise is only real if a test proves it on the interrupt and failure paths.
- Commit after each task or logical group; the branch is `011-integration-coverage` and every commit
  belongs to this spec only (constitution § Version Control).
- Never add a `force` parameter to `delegate_integration_use`, not even defaulting to `False`. The
  guarantee that exactly one call site can overwrite a team's files is enforced by that signature.
