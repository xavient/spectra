# Tasks: Unified Version & Update Commands

**Input**: Design documents from `/specs/007-unified-version-update/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md — all present

**Tests**: **Included.** The spec requires them (SC-005 "all existing tests pass", SC-006 "new tests cover
the health check module, edge cases, and partial failure scenarios"), so every story phase leads with its
tests.

**Organization**: Grouped by user story. US3 is fully independent of the others and can ship first if
preferred; US2 and US4 build on US1's health module.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US4)

## Path Conventions

Single package at repository root: `spectra_cli/` for source, `tests/` for tests. No `src/` directory —
paths below are literal.

---

## Phase 1: Setup

**Purpose**: Establish the baseline so later regressions are attributable.

- [X] T001 Record the pre-change test baseline by running `python3 -m unittest discover -s tests` and noting the count (expected: 259 tests, OK)
- [X] T002 Confirm `specify` is on PATH and capture its live output with `specify self check`, verifying it matches research.md R1 branch 5 (`Up to date: <version>`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The status vocabulary, the data structures, the renderer, and the test fixtures. Every user
story needs these.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T003 Create `spectra_cli/health.py` with the module docstring and the status constants `UP_TO_DATE`, `NEEDS_UPDATING`, `AHEAD`, `UNKNOWN` and component keys `SPECIFY_CLI`, `INTEGRATION`, `SPECTRA_CLI`, `SPECTRA_EXTENSION` per contracts/health-check.md
- [X] T004 Implement the `ComponentStatus` class in `spectra_cli/health.py` with fields `key`, `label`, `installed`, `latest`, `status`, `detail` and `__slots__`, following the `ProjectState` style in `spectra_cli/project.py`
- [X] T005 Implement the `HealthReport` class in `spectra_cli/health.py` holding `components` plus the derived properties `outdated`, `needs_update`, and `unknown` per data-model.md
- [X] T006 [P] Add a single `ui.health_table(rows)` to `spectra_cli/ui.py` rendering aligned label/glyph/phrase/version columns using `visible_len` for padding, with `✓` green, `!` yellow, `✗` red, `–` dimmed per research.md R7. It takes already-formatted glyph/phrase/version cells so the **same** renderer serves both the status table and the update final report — one column layout, two callers
- [X] T007 [P] Add a fake `specify` executable fixture to `tests/helpers.py` that can emit any of the five `specify self check` output branches from research.md R1 on demand, placed on a temporary `PATH`
- [X] T008 [P] Add a `without_specify()` context manager to `tests/helpers.py` that removes `specify` from `PATH` for the duration of a block
- [X] T009 Extend `temp_project()` in `tests/helpers.py` with an `integration_version` argument that writes `.specify/integration.json`, accepting a sentinel for "write malformed JSON" and one for "omit the version key"

**Checkpoint**: Data structures, renderer, and fixtures ready — user story implementation can begin.

---

## Phase 3: User Story 1 - Four-component health report (Priority: P1) 🎯 MVP

**Goal**: `spectra version` reports Specify CLI, Core agents, Spectra CLI, and Spectra agents in one
invocation, degrading each row independently to `unknown` rather than failing.

**Independent Test**: Run `spectra version` in this repository and confirm four rows appear, with Core
agents reading `needs updating (0.12.14 → 0.16.4)` — the real state of this project.

### Tests for User Story 1

- [X] T010 [P] [US1] Create `tests/test_health.py` with a `SelfCheckParsing` class asserting `parse_self_check()` handles all five branches from research.md R1 using literal fixture strings, including the U+2192 arrow and the unrecognized-output fallback
- [X] T011 [P] [US1] Add an `IntegrationVersion` class to `tests/test_health.py` covering `read_integration_version()` for: valid file, missing file, malformed JSON, non-object top level, absent `version` key, and empty `version`
- [X] T012 [P] [US1] Add an `IntegrationStatus` class to `tests/test_health.py` asserting every row of the state table in contracts/health-check.md §2, including that an unknown Specify CLI forces an unknown integration status
- [X] T013 [P] [US1] Add a `CheckAll` class to `tests/test_health.py` asserting `check_all()` returns exactly four components in canonical order and that one component's failure never suppresses the other three
- [X] T014 [P] [US1] Add a `SpecifyAbsent` class to `tests/test_health.py` asserting that with `specify` off `PATH` the first two components are `unknown` and the last two still resolve
- [X] T015 [P] [US1] Update the `Verdicts` class in `tests/test_version_update.py` to assert all four component rows are reported and that the `spectra update` hint appears only when at least one row needs updating
- [X] T016 [US1] Replace `test_it_distinguishes_the_extension_version_from_the_tools_own` in `tests/test_version_update.py` — the `spectra cli version` hint line is removed, so assert it is absent
- [X] T017 [US1] Rewrite `test_an_unreachable_published_version_exits_three_without_implying_currency` in `tests/test_version_update.py`: unreachable published data now yields an `unknown` row and **exit 0**, not exit 3, per contracts/cli-surface.md
- [X] T018 [P] [US1] Add tests to `tests/test_version_update.py` asserting `--no-update-check` and `SPECTRA_NO_UPDATE_CHECK` suppress only the Spectra CLI release lookup while the other three checks still run (FR-016)

### Implementation for User Story 1

- [X] T019 [US1] Implement `parse_self_check(text)` in `spectra_cli/health.py` per the parse table in contracts/health-check.md §1, matching on line prefixes and never on exit code
- [X] T020 [US1] Implement `get_specify_cli_status()` in `spectra_cli/health.py`, shelling out via `subprocess.run` with `capture_output=True`, `text=True`, and an explicit timeout; map `shutil.which` miss, `OSError`, and `TimeoutExpired` to `UNKNOWN` with distinct details
- [X] T021 [US1] Implement `read_integration_version(project_root)` in `spectra_cli/health.py`, returning `None` for missing, unreadable, malformed, and version-less files alike
- [X] T022 [US1] Implement `get_integration_status(project_root, specify_status)` in `spectra_cli/health.py` per the state table, setting `latest` to the CLI's *latest* when the CLI is behind and to its *installed* version otherwise
- [X] T023 [P] [US1] Implement `get_spectra_cli_status(skip_network=False)` in `spectra_cli/health.py`, translating `version.check_update()`'s four statuses and honouring `skip_network` per FR-016
- [X] T024 [P] [US1] Implement `get_spectra_extension_status(project_state)` in `spectra_cli/health.py`, reusing `extension.published_version()` and `extension.compare()`, mapping `net.FetchError` and an `INCOMPLETE` project to `UNKNOWN` while still reporting `installed`
- [X] T025 [US1] Implement `check_all(project_state, skip_network=False, timeout=...)` in `spectra_cli/health.py`, resolving the Specify CLI first and feeding its result into the integration check (FR-025), returning a `HealthReport` of four components in canonical order
- [X] T026 [US1] Rewrite `cmd_version` in `spectra_cli/cli.py` to guard project state (exit 5 per FR-022), call `health.check_all()`, render via `ui.health_table()`, append the `spectra update` hint when `needs_update`, and return `EXIT_OK` for every delivered verdict
- [X] T027 [US1] Remove the `EXIT_UNREACHABLE` return path from `cmd_version` in `spectra_cli/cli.py` and delete the now-obsolete `spectra cli version` hint line

**Checkpoint**: `spectra version` reports all four components. US1 is independently demonstrable.

---

## Phase 4: User Story 2 - Unified update (Priority: P1)

**Goal**: `spectra update` checks all four components, prompts once listing only what will change, then
updates in order, continuing through partial failures and skipping undeterminable components.

**Independent Test**: With two components out of date, run `spectra update`, confirm one prompt lists
exactly those two, and confirm the final four-row report shows per-component outcomes.

**Depends on**: US1's `health.check_all()` (T025).

### Tests for User Story 2

- [X] T028 [P] [US2] Add an `UpdateResult` class to `tests/test_health.py` asserting the outcome vocabulary `UPDATED`/`FAILED`/`SKIPPED` and that `FAILED` always carries a non-empty detail
- [X] T029 [P] [US2] Add tests to `tests/test_version_update.py` asserting an all-current stack reports the table, prints no prompt, and exits 0 (FR-021)
- [X] T030 [P] [US2] Add a test to `tests/test_version_update.py` asserting that when **no** component's status could be determined, the output says nothing could be checked, names the unverified components, does not claim everything is up to date, and exits 0 (FR-027)
- [X] T031 [P] [US2] Add a test to `tests/test_version_update.py` asserting that when some components are current and others unknown with none outdated, the output reports both facts rather than implying the whole stack was verified (FR-027)
- [X] T032 [P] [US2] Add tests to `tests/test_version_update.py` asserting the confirmation prompt lists only `NEEDS_UPDATING` components and omits `unknown` and `ahead` ones (FR-024)
- [X] T033 [P] [US2] Add tests to `tests/test_version_update.py` asserting `--yes` skips the prompt and that declining exits `EXIT_DECLINED` (1) having invoked no update
- [X] T034 [P] [US2] Add a partial-failure test for `apply_updates()` to `tests/test_health.py` (matchable by `-k partial`) proving a failing early component does not prevent later components being attempted, and that the returned results carry actionable detail for the failure
- [X] T035 [P] [US2] Add a skip-semantics test for `apply_updates()` to `tests/test_health.py` (matchable by `-k skip`) proving an `unknown` or `ahead` component is never attempted and yields a `SKIPPED` result (FR-023)
- [X] T036 [P] [US2] Add a test for `apply_updates()` to `tests/test_health.py` asserting Ctrl-C (exit 130) during a delegated step stops the walk rather than continuing to the next component
- [X] T037 [P] [US2] Add an end-to-end test to `tests/test_version_update.py` asserting `cmd_update` exits `EXIT_DELEGATION` (4) when any result failed and `EXIT_OK` (0) when only skips accompany successes (FR-012)
- [X] T038 [US2] Update the existing `Update` class tests in `tests/test_version_update.py` that assume extension-only behavior, so they exercise the four-component walk instead

### Implementation for User Story 2

- [X] T039 [P] [US2] Add `delegate_self_upgrade()` to `spectra_cli/extension.py` calling `_delegate(["specify", "self", "upgrade"])`
- [X] T040 [P] [US2] Add `delegate_integration_upgrade()` to `spectra_cli/extension.py` calling `_delegate(["specify", "integration", "upgrade"])` bare, with a docstring recording why `--force` is deliberately not passed
- [X] T041 [US2] Implement the `UpdateResult` class and its `UPDATED`/`FAILED`/`SKIPPED` constants in `spectra_cli/health.py` per data-model.md
- [X] T042 [US2] Implement `apply_updates(report)` in `spectra_cli/health.py` as the ordered walk, guarding each step individually so `DelegationError`, `UpdateError`, and a non-zero exit each record a `FAILED` result and continue, while exit 130 aborts the walk. It lives in `health.py`, not `cli.py`, so the partial-failure semantics can be tested without argparse or a terminal — see contracts/health-check.md
- [X] T043 [US2] Rewrite `cmd_update` in `spectra_cli/cli.py` to run `health.check_all()`, prompt on `report.outdated` (respecting `--yes` and non-TTY), execute the walk, render the final four-row report, and return `EXIT_DELEGATION` if any result failed
- [X] T044 [US2] Implement the three-way no-op branch in `cmd_update` in `spectra_cli/cli.py` per FR-027 and contracts/cli-surface.md: all current → "Everything is up to date"; none outdated but some unknown → report what is current *and* name the unverified components; nothing checkable at all → warn that nothing could be checked. All three exit 0 and none may claim the stack is current when it was not verified
- [X] T045 [US2] Add an update-outcome formatter that maps each `UpdateResult` to glyph/phrase/version cells and feeds them to the existing `ui.health_table()` from T006 — **no second renderer**, so the before and after tables share one column layout by construction (F12)

**Checkpoint**: `spectra update` brings the whole stack current from one confirmation.

---

## Phase 5: User Story 3 - Retired `cli version` and `cli update` (Priority: P2)

**Goal**: The two retired subcommands name their replacements and exit 2; `cli uninstall` is untouched;
help and CI reflect the smaller surface.

**Independent Test**: Run `spectra cli version` and `spectra cli update`, confirm each prints its
retirement message and exits 2, then confirm `spectra --help` lists only `uninstall` under Tool commands.

**Independent of US1, US2, and US4** — this phase touches only dispatch, help text, and CI, so it can be
implemented and shipped in any order relative to the others.

### Tests for User Story 3

- [X] T046 [P] [US3] Add a `RetiredToolSubcommands` class to `tests/test_cli_surface.py` asserting `spectra cli version` and `spectra cli update` each exit `EXIT_USAGE` (2) and print a message naming their replacement, and that neither reaches the network nor spawns a subprocess — the substantive form of SC-004's one-second bound
- [X] T047 [P] [US3] Add a test to `tests/test_cli_surface.py` asserting neither retired subcommand performs its old action — no uv invocation, no release lookup
- [X] T048 [US3] Remove `test_cli_version_reports_the_tools_own_version_on_the_first_line` and `test_cli_update_dispatches_to_the_tools_own_update` from `TheToolGroup` in `tests/test_cli_surface.py`, superseded by T044
- [X] T049 [US3] Move `test_cli_version_matches_the_committed_version_file` in `tests/test_cli_surface.py` off the retired command, asserting instead that `version.read_installed_version()` equals the committed `VERSION` file
- [X] T050 [US3] Update `test_all_three_tool_handlers_share_one_signature` in `tests/test_cli_surface.py` — there is one live tool handler plus two retirement handlers now — and confirm `test_cli_uninstall_dispatches_to_the_tools_own_uninstall` still passes untouched, which is what verifies FR-015 (`cli uninstall` unchanged)
- [X] T051 [US3] Update `test_every_tool_command_is_listed_under_cli` and the `TheSplitIsEvident` panel tests in `tests/test_cli_surface.py` to expect a single-row Tool commands panel
- [X] T052 [P] [US3] Add a test to `tests/test_cli_surface.py` asserting the `version` and `update` descriptions in the help output describe the whole stack rather than "the agents installed here" (FR-019)

### Implementation for User Story 3

- [X] T053 [US3] Add retirement handlers to `spectra_cli/cli.py` that print `✗ \`spectra cli <verb>\` has been retired. Use \`spectra <verb>\` instead.` and return `EXIT_USAGE`
- [X] T054 [US3] Point the `version` and `update` entries of `TOOL_DISPATCH` in `spectra_cli/cli.py` at the retirement handlers, keeping both registered with the parser so they do not degrade into a bare "invalid choice" error
- [X] T055 [US3] Reduce `TOOL_COMMANDS` in `spectra_cli/cli.py` to `cli uninstall` only, and update the `version` / `update` descriptions in `PROJECT_COMMANDS` to describe the whole stack (FR-019, FR-020)
- [X] T056 [US3] Update `print_cli_group_help()` in `spectra_cli/cli.py` so the group help lists only `uninstall` and points at the top-level commands for version and update
- [X] T057 [US3] Update the module docstring of `spectra_cli/cli.py`, which currently documents `spectra cli version | update | uninstall` as the tool surface
- [X] T058 [US3] Replace the `spectra cli version` assertion in `.github/workflows/ci.yml` with the `importlib.metadata` comparison from research.md R3, keeping the `VERSION` parity intent intact
- [X] T059 [US3] Extend the "removed flags name their replacements" step in `.github/workflows/ci.yml` to also assert `spectra cli version` and `spectra cli update` exit non-zero and name their replacements

**Checkpoint**: The retirement is complete and CI no longer depends on a command that does not exist.

---

## Phase 6: User Story 4 - Update order is enforced (Priority: P2)

**Goal**: Updates always execute Specify CLI → Core agents → Spectra CLI → Spectra agents, and a subset
preserves that relative order.

**Independent Test**: With all four components out of date and every delegate mocked, assert the recorded
call order.

**Depends on**: US2's update walk (T042).

### Tests for User Story 4

- [X] T060 [P] [US4] Add an ordering test to `tests/test_version_update.py` (matchable by `-k order`) recording delegate invocation order with all four components out of date and asserting the canonical sequence
- [X] T061 [P] [US4] Add a test to `tests/test_version_update.py` asserting that when only a subset is out of date, only that subset is attempted and its relative order is preserved
- [X] T062 [P] [US4] Add a test to `tests/test_version_update.py` asserting the order holds even when an earlier component's update fails — no short-circuiting (US4 scenario 3)

### Implementation for User Story 4

- [X] T063 [US4] Assert canonical ordering structurally in `spectra_cli/health.py` by deriving the walk from `HealthReport.components` order rather than a separate list, so ordering cannot drift from the report
- [X] T064 [US4] Add a comment in `spectra_cli/health.py` recording research.md R6's finding that the Spectra CLI step must stay third because it replaces the running process's own code

**Checkpoint**: Ordering is guaranteed by construction and pinned by tests.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [X] T065 Bump the root `VERSION` file from `5.0.0` to `6.0.0` — major, because two commands are removed (constitution Principle VI)
- [X] T066 Verify `spectra/extension.yml` and `catalog.json` versions are **unchanged**, confirming the two release channels stayed decoupled
- [X] T067 [P] Update the `Working with your agents` and `Keeping the command itself up to date` sections of `README.md`, which document `spectra cli version` and `spectra cli update` as live commands, and the `Two release channels` table at line 390 which names `spectra cli update` as the tool's update path
- [X] T068 [P] Add a "Changed in 6.0.0" note to `README.md` mirroring the existing 5.0.0 note, explaining that the two `cli` subcommands were absorbed into the top-level commands
- [X] T069 Update the four `spectra cli version` / `spectra cli update` references in `CONTRIBUTING.md` (lines ~335, ~390, ~400, ~413), and rewrite the release smoke-test step at lines 398-400 to use bare `spectra` per research.md R8 — `spectra version` cannot substitute there because the step runs from an arbitrary directory
- [X] T070 [P] Update `docs/index.html`, which documents `spectra cli version` and `spectra cli update` as live commands; leave the dynamically-read version pill alone, since constitution Principle V forbids hard-coding a version there
- [X] T071 Update the clean-room test matrix in `test/README.md`, whose rows 1b, 5, 9, and 10 are built on the retired commands; row 10 ("project uninstall leaves the tool") must become `spectra uninstall` then bare `spectra` per research.md R8, because by construction no project extension remains for `spectra version` to accept
- [X] T072 Run `python3 tools/generate_agent_docs.py --check` to confirm no generated region drifted (expected: no change, since no agent data was touched)
- [X] T073 Run the full suite `python3 -m unittest discover -s tests` and confirm it is green with no fewer tests than the T001 baseline
- [X] T074 Work through every scenario in `quickstart.md` (1–15), confirming each expected outcome and exit code
- [X] T075 Confirm the `spectra version` timing budget from plan.md holds — roughly one second on a warm network
- [X] T076 Verify the suite passes on Python 3.9 as well as 3.12 to match the CI matrix in `.github/workflows/ci.yml`, e.g. `python3.9 -m unittest discover -s tests`
- [X] T077 Grep the whole repository for surviving references to the retired commands — `grep -rn "cli version\|cli update" --exclude-dir=.git --exclude-dir=specs .` should return only the retirement handlers, their tests, and the CI assertions that check them

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies
- **Foundational (Phase 2)**: Depends on Setup — **BLOCKS all user stories**
- **US1 (Phase 3)**: Depends on Foundational
- **US2 (Phase 4)**: Depends on Foundational **and US1's T025** (`check_all`)
- **US3 (Phase 5)**: Depends on Foundational only — **independent of US1, US2, US4**
- **US4 (Phase 6)**: Depends on **US2's T042** (the update walk)
- **Polish (Phase 7)**: Depends on all shipped stories

### User Story Dependencies

```text
Foundational ─┬─► US1 ──► US2 ──► US4
              └─► US3            (independent branch)
```

US2's dependency on US1 is real rather than organizational: `spectra update` runs the same health check
`spectra version` renders, and the spec requires it never act on a state it did not first report. US4 is
a property of US2's walk, so it cannot precede it.

US3 shares no code path with the others — it touches dispatch, help text, and CI only.

### Within Each User Story

- Tests first, and confirmed failing, before implementation
- Data structures before the functions that build them
- Detectors before `check_all`
- `check_all` before the command handlers
- Command handlers before the CI and docs updates that describe them

### Parallel Opportunities

- T006–T009 (renderer and three fixture tasks) are four different concerns in two files — T007, T008, T009 all touch `tests/helpers.py`, so run T006 in parallel with them but serialize the three fixture tasks against each other
- T010–T014 create separate classes in the new `tests/test_health.py` and can be written in parallel
- T023 and T024 touch independent functions in `health.py`
- T039 and T040 are two independent additions to `extension.py`
- T046, T047, T052 are independent test additions
- T060, T061, T062 are independent test additions
- **US3 (T046–T059) can run fully in parallel with US1 and US2** by a second developer

---

## Parallel Example: User Story 1 tests

```bash
# Five independent test classes in the new tests/test_health.py:
Task: "SelfCheckParsing class covering all five specify self check branches"
Task: "IntegrationVersion class covering six integration.json edge cases"
Task: "IntegrationStatus class covering the seven-row state table"
Task: "CheckAll class covering canonical order and independent degradation"
Task: "SpecifyAbsent class covering the specify-off-PATH path"
```

## Parallel Example: two developers

```bash
# Developer A — the health module and the two commands:
Phase 3 (US1) → Phase 4 (US2) → Phase 6 (US4)

# Developer B — the retirement, in parallel from the start:
Phase 5 (US3), including both .github/workflows/ci.yml edits
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Phase 1: Setup — capture the baseline
2. Phase 2: Foundational — structures, renderer, fixtures
3. Phase 3: US1 — the four-component report
4. **STOP and VALIDATE**: run `spectra version` in this repository; the Core agents row should reveal
   the real `0.12.14 → 0.16.4` gap that nothing currently surfaces
5. This is already shippable value: the report alone answers "is my stack current?", even before
   `spectra update` can fix it

### Incremental Delivery

1. Foundational → nothing user-visible yet
2. + US1 → `spectra version` reports everything (**MVP**)
3. + US2 → `spectra update` fixes everything
4. + US3 → the old commands are retired and CI is consistent
5. + US4 → ordering pinned by tests
6. + Polish → `VERSION` bumped, docs and README aligned

### Ship-order note

US3 carries the **breaking** change and the CI edit. Landing it in the same release as US1/US2 is
required — the `VERSION` bump to `6.0.0` and the retirement must travel together, or the published CLI
would advertise a major bump without the removal that justifies it.

---

## Notes

- `[P]` = different files, no dependencies on incomplete tasks
- Six files are outside the issue's original file list and easy to miss: `.github/workflows/ci.yml`
  (T058, T059), `VERSION` (T065), `README.md` (T067, T068), `CONTRIBUTING.md` (T069),
  `docs/index.html` (T070), and `test/README.md` (T071). T077 is the backstop that catches any
  reference the list missed
- Two procedures depended on the retired `spectra cli version` and had **no** substitute in
  `spectra version`, because both run without a project: the release smoke test (T069) and clean-room
  row 10 (T071). Both now use bare `spectra`, whose banner prints `cli vX.Y.Z` from any directory —
  see research.md R8
- Two existing tests encode behavior this feature deliberately changes and must be rewritten rather than
  patched: T017 (exit 3 → exit 0 on unreachable data) and T016 (the removed hint line)
- **T076 caveat.** Only Python 3.14 is installed on the development machine, so 3.9 was verified
  at the syntax level (`ast.parse(..., feature_version=(3, 9))` over every module, clean). The
  real 3.9 run happens in CI, whose matrix covers 3.9 and 3.12
- Zero third-party dependencies is a hard constraint — nothing here adds one
- Commit after each task or logical group; stop at any checkpoint to validate a story independently
