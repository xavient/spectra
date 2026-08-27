---

description: "Task list for Flaky Test Detector"
---

# Tasks: Flaky Test Detector

**Input**: Design documents from `/specs/018-flaky-test-detector/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md),
[data-model.md](./data-model.md), [contracts/](./contracts/), [quickstart.md](./quickstart.md)

**Tests**: One automated test module, and it is not TDD. The behavioural deliverable is a Markdown
instruction file with no unit-test surface, so `tests/test_flaky_test_detector_flow.py` asserts that the
command *states* its non-negotiable rules — the regression that actually happens is a rule quietly
deleted (R-012). Behavioural validation is the eleven scenarios in [quickstart.md](./quickstart.md),
run by hand in Phase 10.

**Organization**: Grouped by user story so each is independently deliverable and testable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel — different files, no dependency on incomplete work
- **[Story]**: `[US1]`…`[US6]`, on user-story phases only
- Every task names its exact file path

## Path Conventions

This feature ships instructions, not code. There is no `src/`. Real paths:

- **The behavioural deliverable**: `spectra/commands/flaky-test-detector.md` (one new file)
- **The publishing surface**: `spectra/extension.yml`, `spectra/CHANGELOG.md`, `spectra/README.md`,
  `agents-list.json`, `AGENTS_LIST.md`, `README.md`, `catalog.json`, `docs/index.html`,
  `docs/packages/spectra.zip`
- **Tests**: `tests/test_flaky_test_detector_flow.py`, `tests/test_roster_data.py`, `test/README.md`
- **Tooling used, never modified**: `tools/generate_agent_docs.py`, `tools/build_package.py`

> ## ⚠️ Read this before parallelizing
>
> **Phases 2 through 8 are almost entirely sequential, and that is a property of the feature.**
>
> User stories 1 through 6 are not separate modules — they are sections of a **single Markdown file**,
> `spectra/commands/flaky-test-detector.md`. Two people editing it at once conflict on every task. `[P]`
> therefore appears only in Phase 9 (publishing surface) and Phase 10 (tests), where tasks genuinely
> touch different files.
>
> The stories stay independently *testable* and *deliverable* — you can stop after US1 and ship a useful
> agent that reports flaky tests and writes nothing. They are not independently *assignable*.

---

## Phase 1: Setup

**Purpose**: Record the baseline, and create the file with its interface and its one governing rule.

- [ ] T001 Record the pre-implementation baseline from the repository root: `python3 tools/generate_agent_docs.py --check` must read **46 agents / 5 prose blocks / roster and manifest agree**; `python3 tools/build_package.py` followed by `git diff --stat docs/packages/spectra.zip` must show no drift; `spectra/extension.yml` is at **1.10.0** with **5** commands and `catalog.json` agrees; `tests/test_roster_data.py` asserts **14 available / 32 planned**. Phase 10 asserts these became 47-agent-set-unchanged / 6 prose blocks / 1.11.0 / 6 commands / 15 available / 31 planned.
- [ ] T002 Create `spectra/commands/flaky-test-detector.md` with YAML front matter carrying a single `description` key in the style of `spectra/commands/review-pr.md`, an H1 title, and a one-paragraph statement of the job: find likely-flaky tests by reading the test source, report them with confidence and a fix, then write a resumable task list and apply approved fixes behind two gates.
- [ ] T003 Add the **User Input** section to `spectra/commands/flaky-test-detector.md` documenting the `$ARGUMENTS` surface per [contracts/command-interface.md](./contracts/command-interface.md): empty means the whole working tree; a project-relative path or a suite name narrows the run; an argument resolving to nothing is reported and MUST NOT silently widen back to the whole tree (FR-002).
- [ ] T004 Add the **governing rule** section to `spectra/commands/flaky-test-detector.md`, stated once and in full: *read anything, execute nothing, and change only test code the developer approved row by row.* Name it as the sentence every later rule narrows.

**Checkpoint**: The file exists, declares its interface, and states its limit.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The machinery every story depends on — the refusals, the state check, and how the file is
read.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. Every task edits the same
file and they are strictly sequential.

- [ ] T005 Add the **refusal list** to `spectra/commands/flaky-test-detector.md`, reproducing the table in [contracts/command-interface.md](./contracts/command-interface.md): no execution of tests, builds, or package commands *including to verify a fix it just applied* (FR-003); no dependency installation; no network; no commit, stage, push, branch, or pull request (FR-004); no production-source or governance edit (FR-005); no write outside the project. State explicitly that no argument or instruction in the session enables any of them.
- [ ] T006 Add **Step 1 — the state check** to `spectra/commands/flaky-test-detector.md` as the first action of every run: read `.specify/memory/flaky-test-analysis.md` and branch on absent / pending rows / no pending rows / unparseable (FR-006). Include the `.specify/memory/` absence path — report what is missing and where the file would go, create nothing (FR-007). Reproduce the state machine from [data-model.md](./data-model.md).
- [ ] T007 Add the **parse rules** to `spectra/commands/flaky-test-detector.md` per [contracts/analysis-file.md](./contracts/analysis-file.md): parseable requires the title, a header block yielding `Generated`/`Scope`/`Progress`, a `## Tasks` heading, and rows resolving to a marker plus an `FT-NNN` id. List what is *not* unparseable — a deleted row, a reworded fix, a hand-ticked box, reordered rows, an added note, a stale header count — and state that developer edits win over the command's own prior content (FR-042).
- [ ] T008 Add the **single-file invariant** to `spectra/commands/flaky-test-detector.md`: at most one analysis file, at that exact path, ever; no second file, no dated variant, no appended second analysis (FR-008); replacement only as part of writing a newly accepted plan, and no other route deletes it (FR-029).
- [ ] T009 Add the **project guardrails** step to `spectra/commands/flaky-test-detector.md` (FR-033a): read `.specify/memory/constitution.md` **of the project the command is invoked in**, never Spectra's own; state that it binds both the suggested and the applied fix; where absent, proceed on technical merit and say no project guardrails were found.

**Checkpoint**: The command knows what it may not do, what state it is in, and what rules it inherits.

---

## Phase 3: User Story 1 — Find the flaky tests (Priority: P1) 🎯 MVP

**Goal**: One command run produces a credible, ranked, evidenced list of likely-flaky tests, and writes
nothing.

**Independent Test**: Run in a project with planted flaky patterns. Every row names a real test at a real
path with evidence at the cited line; the planted stable test is absent; `git status --porcelain` is
empty. Quickstart Scenario 1.

- [ ] T010 [US1] Add the **suite discovery** section to `spectra/commands/flaky-test-detector.md` stating the order in prose per R-003 — test-runner configuration, then declared test scripts or targets in project manifests, then directory conventions, then filename patterns — and requiring every suite found to be reported with root, framework, test-file count, and how it was identified, **before any candidate** (FR-009, FR-010). State that a directory matching a convention but yielding no test files is reported rather than omitted.
- [ ] T011 [US1] Add the **flakiness signal categories** to `spectra/commands/flaky-test-detector.md`, all eight from FR-012 with concrete examples per category: timing and async; test isolation and shared state; unmocked external dependencies; non-determinism; brittle assertions; parallel-execution conflicts; environment coupling; and pre-existing retry or known-flaky annotations. State that an existing flaky annotation is corroborating evidence, never a reason to skip the test.
- [ ] T012 [US1] Add the **candidate record** definition to `spectra/commands/flaky-test-detector.md` per [data-model.md](./data-model.md): stable id, test name, project-relative path with line where determinable, confidence, a one-to-two-sentence concrete fix, and mandatory evidence (FR-013). Specify the `FT-NNN` id format — zero-padded from `001`, unique in the file, never reused or renumbered (FR-014).
- [ ] T013 [US1] Add the **confidence rubric** to `spectra/commands/flaky-test-detector.md`, reproducing FR-015 in full: High requires the triggering construct in the test's own body or direct fixtures, citable by line, with intermittent failure following without further assumption; Medium is the same pattern where the outcome depends on context only a run could confirm; Low is indirect or convention-based. State that this rates evidence, not failure rate, and that no percentage or score is ever emitted (R-004).
- [ ] T014 [US1] Add the **ordering rule** to `spectra/commands/flaky-test-detector.md`: High, then Medium, then Low, then by file path within each band, in both the chat table and the file, so the weakest rows sit where pruning is cheapest (FR-016).
- [ ] T015 [US1] Add the **honesty rules** to `spectra/commands/flaky-test-detector.md`: every reported test name, path, and evidence location must exist as reported and no candidate may come from a file the agent did not read (FR-017); and where nothing meets the bar, report zero plainly rather than lowering the bar (FR-018).
- [ ] T016 [US1] Add the **chat table format** to `spectra/commands/flaky-test-detector.md` per [contracts/chat-output.md](./contracts/chat-output.md) — ID, Test, File, Confidence, Suggested fix — and require it to be presented before anything is written (FR-019).
- [ ] T017 [US1] Add the **coverage and limits statement** to `spectra/commands/flaky-test-detector.md` (FR-020): suites and file counts examined, tests examined, and anything skipped, unparseable, or not reached. State that a partial analysis presented as complete is a defect, not a degradation, and that this statement is mandatory on every run including empty ones.

**Checkpoint**: US1 is shippable on its own — the agent reports and stops, having written nothing.

---

## Phase 4: User Story 2 — Turn the findings into a reviewable plan (Priority: P1)

**Goal**: On consent, the candidates become a durable, prunable task list at
`.specify/memory/flaky-test-analysis.md`.

**Independent Test**: Accept at Gate 1; the file matches [contracts/analysis-file.md](./contracts/analysis-file.md)
section for section, every row is `[ ]`, every id resolves to an evidence entry, and no test file was
touched. Declining instead leaves the tree byte-identical. Quickstart Scenario 2.

- [ ] T018 [US2] Add **Gate 1** to `spectra/commands/flaky-test-detector.md`: after the table and the coverage statement, ask whether to write the plan, stating that this step produces a plan and not a code change, and wait (FR-021). State that no argument or flag bypasses it (R-005).
- [ ] T019 [US2] Add the **Gate 1 decline path** to `spectra/commands/flaky-test-detector.md`: nothing is created, any existing file is left byte-for-byte unchanged, the working tree is untouched, and the command says nothing was written (FR-022).
- [ ] T020 [US2] Add the **file header block** specification to `spectra/commands/flaky-test-detector.md` — `Generated` with a UTC offset, `Scope`, `Suites analyzed` with frameworks and counts, `Tests examined`, `Flaky candidates` with the confidence split, and `Progress: N of M fixed` (FR-023) — matching [contracts/analysis-file.md](./contracts/analysis-file.md) exactly.
- [ ] T021 [US2] Add the **task table** specification to `spectra/commands/flaky-test-detector.md`: columns `Done`, `ID`, `Test`, `File`, `Confidence`, `Suggested fix` in that order and no others; first column a literal `[ ]`; same values as the chat table (FR-024). Add the instruction line telling the developer that deleting a row excludes that test and what the markers mean (FR-027).
- [ ] T022 [US2] Add the **`## Evidence` section** specification to `spectra/commands/flaky-test-detector.md`: one id-keyed bullet per row recording the construct and its location, mandatory so a later session can act without re-analyzing (FR-025).
- [ ] T023 [US2] Add the **`## Not analyzed` section** specification to `spectra/commands/flaky-test-detector.md`, carrying into the file the same limits the chat coverage statement gave (FR-026).
- [ ] T024 [US2] Add the **`## Outcomes` section** specification to `spectra/commands/flaky-test-detector.md`: id-keyed entries recording why an attempted row is still open, or what an applied fix touched beyond its own test; entries persist across sessions; outcome text never goes in a table row (FR-026a).
- [ ] T025 [US2] Add the **post-write report** to `spectra/commands/flaky-test-detector.md`: name the path, state that the command is waiting on the developer's review, and state explicitly that rows may be deleted to exclude those tests (FR-028).
- [ ] T026 [US2] Add the **narrowed-scope disclosure** to `spectra/commands/flaky-test-detector.md`: before writing a plan whose scope is narrower than the file it would replace, name the pending rows falling outside the new scope and wait for an explicit answer; never merge two analyses into one file (FR-029a, R-008).

**Checkpoint**: The plan exists, is reviewable, and nothing has been edited.

---

## Phase 5: User Story 3 — Fix the approved items (Priority: P1)

**Goal**: The surviving rows are actually fixed, ticked off one at a time, with anything unfixable left
open and explained.

**Independent Test**: Prune two rows, approve, then inspect the diff — only test and test-support files,
no weakened assertions, pruned tests untouched, every `[x]` backed by a real edit, nothing committed.
Quickstart Scenario 3.

- [ ] T027 [US3] Add **Gate 2** to `spectra/commands/flaky-test-detector.md`: after the developer's review, ask for approval before editing any file, stating what will happen and that nothing will be committed (FR-030). No bypass.
- [ ] T028 [US3] Add the **re-read and act-only-on-survivors** rule to `spectra/commands/flaky-test-detector.md`: at Gate 2, re-read the file from disk and work only the unchecked rows present at that moment, in file order; a deleted row's test is never opened or modified (FR-031, FR-032).
- [ ] T029 [US3] Add the **pre-edit evidence re-check** to `spectra/commands/flaky-test-detector.md`: before editing a row's test, re-read it and confirm the recorded evidence is still present; where it is gone or materially changed, leave the row `[ ]` with an outcome entry saying the code moved on, apply nothing, and continue. State that re-confirmation is a read, not a re-analysis — no new fix is derived inside a fix run (FR-031a).
- [ ] T030 [US3] Add the **edit confinement** rule to `spectra/commands/flaky-test-detector.md`: edits are confined to test code and test-support files — fixtures, helpers, factories, mocks, test configuration; creating a new test-support file is permitted where the fix requires one; creating or editing production source is not, and adding a dependency is forbidden regardless (FR-032).
- [ ] T031 [US3] Add the **reach disclosure** to `spectra/commands/flaky-test-detector.md`: a fix touching shared test configuration, global setup or teardown, or a fixture other tests consume must be stated in the run report and recorded against that row in `## Outcomes`, naming what changed and what depends on it; such a change is never reported as an ordinary single-row fix (FR-032a).
- [ ] T032 [US3] Add the **prohibited remedies** to `spectra/commands/flaky-test-detector.md` as an explicit list: deleting an assertion; loosening one so it passes regardless of behaviour; skipping a test or marking it expected-to-fail; adding a retry wrapper or retry configuration; lengthening a sleep. State the rule positively too — a fix removes the cause (FR-033).
- [ ] T033 [US3] Add the **guardrail-blocked** path to `spectra/commands/flaky-test-detector.md`: where a project guardrail rules out the only available remedy, leave the row `[ ]`, name the blocking rule as the reason in `## Outcomes`, and continue (FR-033a, R-009).
- [ ] T034 [US3] Add **per-item checkpointing** to `spectra/commands/flaky-test-detector.md`: immediately after applying a row's fix and before starting the next, mark that row `[x]` and update the progress count on disk. State explicitly that progress must not be batched to the end of the run, and why — an interrupted session must leave a file that is exactly true (FR-034, R-006).
- [ ] T035 [US3] Add the **cannot-fix** path to `spectra/commands/flaky-test-detector.md`: leave `[ ]` with a short reason in `## Outcomes` and continue to the next item; covers a remedy that lives in production source (record what would change and where) and a test that can no longer be located (never edit a similarly-named test) (FR-035).
- [ ] T036 [US3] Add the **nothing-to-fix** path to `spectra/commands/flaky-test-detector.md`: where no unchecked row survived the review, report that there is nothing to fix, leave the file as the record, and edit nothing (FR-036).
- [ ] T037 [US3] Add the **closing report** to `spectra/commands/flaky-test-detector.md` per [contracts/chat-output.md](./contracts/chat-output.md): fixed count, every open item with its reason, every file changed with created files marked and suite-wide changes called out, and that the changes are uncommitted and awaiting review (FR-037).

**Checkpoint**: The full loop works — detect, plan, prune, fix — and every safety rail is stated.

---

## Phase 6: User Story 4 — Resume unfinished work (Priority: P1)

**Goal**: A later session picks up exactly where the work stopped, with no re-analysis and no lost
pruning.

**Independent Test**: Leave a mixed `[x]`/`[ ]` file, restart, run the command; it reports the counts,
analyzes nothing, and works only the pending rows. Quickstart Scenarios 5 and 6.

- [ ] T038 [US4] Add the **pending-rows branch** to `spectra/commands/flaky-test-detector.md`: report the file's generation date, its scope, and its done/pending counts, then offer exactly three choices — continue with the pending items, discard and re-analyze, or stop — and analyze nothing unless asked. Note that choosing to re-analyze under a narrower scope triggers the FR-029a disclosure before any write, and that a completed row is never re-opened (FR-038).

**Checkpoint**: Work survives the session that started it.

---

## Phase 7: User Story 5 — Re-run after everything is done (Priority: P2)

**Goal**: A completed list is replaced only on request, never silently.

**Independent Test**: Finish every item, run again; the command reports completion and asks before
analyzing. Decline, and the file is byte-identical. Quickstart Scenario 7.

- [ ] T039 [US5] Add the **all-complete branch** to `spectra/commands/flaky-test-detector.md`: report that the previous analysis is complete with its date, and ask whether to re-run, stating that a new plan would replace this file; never analyze immediately and never overwrite silently (FR-039).
- [ ] T040 [US5] Add the **unparseable branch** to `spectra/commands/flaky-test-detector.md`: report what could not be read, never overwrite silently, and offer a fresh analysis — disclosing that it would replace the file — or stopping (FR-040). Add the **empty re-analysis** rule: a consented re-analysis producing no candidates leaves any existing file unchanged, says so, and tells the developer they may delete it if they no longer need the record (FR-041).

**Checkpoint**: Every one of the four state branches is implemented.

---

## Phase 8: User Story 6 — Nothing to act on (Priority: P3)

**Goal**: An empty answer is fast, plain, and writes nothing.

**Independent Test**: Run in a project with no tests, then in one with a clean suite. Both exit with a
statement, no file, and no further question. Quickstart Scenario 9.

- [ ] T041 [US6] Add the **no-suite exit** to `spectra/commands/flaky-test-detector.md`: report that no test suite was found, name the locations and conventions checked, write nothing, and stop without asking a further question (FR-011).
- [ ] T042 [US6] Add the **zero-candidate exit** to `spectra/commands/flaky-test-detector.md`: report the suites and coverage, state that no likely-flaky tests were identified, write nothing, and **do not offer to create a plan** (FR-018 reporting path).

**Checkpoint**: The command is behaviourally complete. Everything after this is publishing and proof.

---

## Phase 9: Publishing Surface (Principle V)

**Purpose**: Make the command real to a consumer. These touch different files and are the only genuinely
parallel work in this feature.

- [ ] T043 Register the command in `spectra/extension.yml`: add `speckit.spectra.flaky-test-detector` to `provides.commands` with `file: "commands/flaky-test-detector.md"` and the description from [contracts/command-interface.md](./contracts/command-interface.md); bump `extension.version` to `1.11.0`; add the tags `testing`, `flaky-tests`, and `quality`. Do **not** add a `provides.templates` entry — R-002 is the reason, and T052 asserts its absence.
- [ ] T044 [P] Add a `## [1.11.0]` entry to `spectra/CHANGELOG.md` under an `### Added` heading, describing the agent in the changelog's established voice: what it detects, that detection is source-only and executes nothing, the two gates, the resumable file at `.specify/memory/flaky-test-analysis.md`, and the rule that a fix removes the cause rather than weakening the test.
- [ ] T045 [P] Flip the `flaky-test-detector` entry in `agents-list.json` from `"status": "planned"` to `"status": "available"` and add `"command": "speckit.spectra.flaky-test-detector"`. The roster contract requires a command exactly when an agent is available.
- [ ] T046 Regenerate the structured listings by running `python3 tools/generate_agent_docs.py` from the repository root, rewriting the generated regions in `README.md`, `AGENTS_LIST.md`, and `spectra/README.md`. Depends on T045. Do not hand-edit any generated region.
- [ ] T047 Hand-author the per-agent prose block in `AGENTS_LIST.md` under a new `<!-- SPECTRA:AGENT id=flaky-test-detector -->` anchor, in the voice of the existing blocks: what the agent is for, the two gates, what it will not do, and where the analysis file lives. Depends on T046. This is the one item automation cannot produce — `--check` asserts only that it exists.
- [ ] T048 [P] Update the `spectra` entry in `catalog.json`: `version` to `1.11.0`, `provides.commands` from `5` to `6`, both `updated_at` fields to the change's timestamp, and add the new tags so the entry matches `spectra/extension.yml`. Depends on T043.
- [ ] T049 [P] Add the command to the Spectra panel in `docs/index.html` following the existing `<li>` structure — `name`, `cdesc`, `args`, and a Claude-form example — describing the scope argument and the two gates. Depends on T043.
- [ ] T050 Rebuild the distributed package with `python3 tools/build_package.py` and confirm `docs/packages/spectra.zip` now contains `spectra/commands/flaky-test-detector.md`. Depends on T043 and T044.

**Checkpoint**: A consumer running `spectra install` would get the command.

---

## Phase 10: Validation

**Purpose**: Prove the rules survived, and that an agent actually follows them.

- [ ] T051 [P] Create `tests/test_flaky_test_detector_flow.py` in the style of `tests/test_review_pr_flow.py`, asserting against the shipped text of `spectra/commands/flaky-test-detector.md`: the canonical path `.specify/memory/flaky-test-analysis.md` appears and no other analysis-file path does; the no-execution rule is stated including the no-verification-run case; both gates are present and no bypass argument is documented; every prohibited remedy from FR-033 is named; edits are confined to test and test-support files; per-item checkpointing is required; all four state branches appear; and the constitution named is the invoking project's, not Spectra's.
- [ ] T052 [P] Extend `tests/test_flaky_test_detector_flow.py` with the two negative guards: `spectra/extension.yml` registers **no** template for this command (R-002), and the command file names no runtime binary dependency such as `gh` or `git` — this command must not gate on either.
- [ ] T053 [P] Update the roster census in `tests/test_roster_data.py`: available `14` → `15`, planned `32` → `31`, rename `test_it_splits_into_fourteen_available_and_thirty_two_planned` to match the new counts, and extend `test_spectra_ships_exactly_five_agents_today` to the six-id set including `flaky-test-detector` — renaming that method too.
- [ ] T054 [P] Add a manual pass for this agent to `test/README.md` in Section 2, covering the two gates, the four state branches, the stale-plan guard, and the guardrail block, and pointing at [quickstart.md](./quickstart.md) for the full scenario list.
- [ ] T055 Run the repository gates from the root: `python3 -m unittest discover -s tests` (all green, including `tests/test_doc_output_paths.py`, which scans every command file for absolute paths and legacy folders); `python3 tools/generate_agent_docs.py --check` (must now read **6 prose blocks** and agree with the manifest); and `python3 tools/build_package.py` followed by `git diff --stat docs/packages/spectra.zip` (no drift after T050).
- [ ] T056 Run the parity check from [quickstart.md](./quickstart.md) confirming `extension.yml` and `catalog.json` agree at `1.11.0` with `6` commands, and `git diff --exit-code VERSION` confirming the CLI channel did not move (Principle VI).
- [ ] T057 Execute quickstart Scenarios 1 through 11 in a throwaway project (`specify init` plus `specify extension add --dev`), with a scratch suite carrying the planted patterns from [quickstart.md](./quickstart.md). Scenarios 3, 4, 6, and 10 are the ones that cannot be replaced by unit tests: the diff-level safety check, checkpointing after an interruption, the stale-evidence guard, and the refusals.

**Checkpoint**: The rules are asserted, and an agent has been observed following them.

---

## Phase 11: Publish (Constitution Development Workflow step 6)

- [ ] T058 Commit the feature on `018-flaky-test-detector`: `spectra/`, `agents-list.json`, `catalog.json`, `docs/`, `README.md`, `AGENTS_LIST.md`, `tests/`, `test/README.md`, and `specs/018-flaky-test-detector/`.
- [ ] T059 Open a pull request into `main` and merge once green. Merging to `main` **is** the catalog-channel release — the raw `catalog.json` and `docs/packages/spectra.zip` links go live immediately, with no tag and no GitHub Release (Principle VI).

---

## Dependencies & Execution Order

### Phase dependencies

- **Phase 1 (Setup)** — no dependencies.
- **Phase 2 (Foundational)** — depends on Phase 1. **Blocks every user story.**
- **Phase 3 (US1)** — depends on Phase 2. The MVP.
- **Phase 4 (US2)** — depends on Phase 3: there is nothing to write a plan about until candidates exist.
- **Phase 5 (US3)** — depends on Phase 4: the file is what authorizes an edit.
- **Phase 6 (US4)** — depends on Phase 5: resuming means resuming a fix run.
- **Phase 7 (US5)** — depends on Phase 2 for the state check; sequenced here because it is P2.
- **Phase 8 (US6)** — depends on Phase 3 for discovery.
- **Phase 9 (Publishing)** — depends on Phase 8; the command must be behaviourally complete before it ships.
- **Phase 10 (Validation)** — depends on Phase 9.
- **Phase 11 (Publish)** — depends on Phase 10 being green.

### User story dependencies

Unlike a typical feature, these stories form a **chain rather than a fan**: US1 → US2 → US3, with US4
and US5 as re-entry points into that chain and US6 as its empty branch. That is inherent — each story is
a later step of one conversation, not a separate capability.

They remain independently **deliverable**: stopping after US1 ships an agent that reports and writes
nothing, which is genuinely useful. Stopping after US2 ships one that reports and plans but never edits.

### Within each phase

Sequential, because every task edits `spectra/commands/flaky-test-detector.md`.

### Parallel opportunities

- **T044, T045, T048, T049** — four different files, safe together once T043 has set the version.
- **T051, T052, T053, T054** — three test files and one doc, no overlap.
- Nothing in Phases 1 through 8 is parallelizable. See the warning at the top.

---

## Parallel Example: Phase 9

```bash
# After T043 sets extension.yml to 1.11.0, these four touch four different files:
Task: "Add the [1.11.0] entry to spectra/CHANGELOG.md"
Task: "Flip flaky-test-detector to available in agents-list.json"
Task: "Update the spectra entry in catalog.json to 1.11.0 / 6 commands"
Task: "Add the command to the Spectra panel in docs/index.html"

# Then strictly in order:
Task: "T046 — regenerate listings"        # needs T045
Task: "T047 — hand-author the prose block" # needs T046
Task: "T050 — rebuild the zip"             # needs T043 and T044
```

---

## Implementation Strategy

### MVP first (US1 only)

1. Phase 1 → Phase 2 → Phase 3.
2. **Stop and validate**: quickstart Scenario 1. The agent reports a credible list and writes nothing.
3. That is a shippable agent. Everything after it is about acting on the list.

### Incremental delivery

1. Setup + Foundational → the command knows its limits and its state.
2. US1 → reports. Validate, then ship or continue.
3. US2 → plans. Validate: the file is prunable and nothing is edited.
4. US3 → fixes. Validate at the diff level — this is the phase where a mistake reaches the user's code.
5. US4, US5, US6 → the re-entry points and the empty branch.
6. Publishing + Validation → the agent becomes installable.

### Parallel team strategy

There isn't one for Phases 1 through 8, and pretending otherwise produces merge conflicts on a single
Markdown file. With two people, the honest split is: one writes the command through Phase 8 while the
other prepares Phase 9's publishing surface and Phase 10's test module against the contracts, which are
already fixed.

---

## Notes

- `[P]` = different files, no dependency on incomplete work.
- Every user-story task edits the same file; commit after each logical group rather than each task.
- The contracts in [contracts/](./contracts/) are the specification for what each task writes — where a
  task and a contract disagree, the contract wins and the task is wrong.
- Stop at any checkpoint to validate. Phase 3 and Phase 4 are both genuine stopping points.
- The riskiest task in this list is **T034** (checkpointing) and the most important is **T032**
  (prohibited remedies). If review time is scarce, spend it there.

---

## Task Summary

| Phase | Tasks | Count |
|---|---|---|
| 1 — Setup | T001–T004 | 4 |
| 2 — Foundational | T005–T009 | 5 |
| 3 — US1 Find the flaky tests (P1, MVP) | T010–T017 | 8 |
| 4 — US2 Reviewable plan (P1) | T018–T026 | 9 |
| 5 — US3 Fix approved items (P1) | T027–T037 | 11 |
| 6 — US4 Resume (P1) | T038 | 1 |
| 7 — US5 Re-run when complete (P2) | T039–T040 | 2 |
| 8 — US6 Nothing to act on (P3) | T041–T042 | 2 |
| 9 — Publishing surface | T043–T050 | 8 |
| 10 — Validation | T051–T057 | 7 |
| 11 — Publish | T058–T059 | 2 |
| **Total** | | **59** |
