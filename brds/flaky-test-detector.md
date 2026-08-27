# Business Requirements Document (BRD): Flaky Test Detector

## Document Control

| Field             | Value                                                                                                                                                                                                                    |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| BRD ID            | BRD-008                                                                                                                                                                                                                    |
| Title             | Flaky Test Detector — static detection and guided remediation of flaky tests                                                                                                                                              |
| Author            | Spectra / TELUS Digital                                                                                                                                                                                                    |
| Status            | Draft                                                                                                                                                                                                                      |
| Version           | 0.1.0                                                                                                                                                                                                                      |
| Created           | 2026-08-26                                                                                                                                                                                                                 |
| Last updated      | 2026-08-26                                                                                                                                                                                                                 |
| Related documents | `Flaky_Test_Detector_Analyzer_BRD.docx` (TELUS Digital QE Practice — reference input, scoped down here), `.specify/memory/constitution.md`, `agents-list.json` (roster — entry `flaky-test-detector`, under dev), `brds/domain-analyzer.md` (precedent for a `.specify/` review artifact) |

## 1. Executive Summary

**Flaky Test Detector** is a Spectra add-on agent (SDLC Phase — Testing & Quality) that finds
likely-flaky tests by reading the project's own test code, and then — only with the developer's
explicit go-ahead at each step — fixes them.

One command does the whole loop: it identifies the project's test suite(s) from the working tree,
analyzes the tests for the patterns that cause intermittent failures, and reports a ranked table of
candidates with a confidence rating and a concrete suggested fix for each. If the developer wants to
act on it, the agent writes a single durable checklist to `.specify/memory/flaky-test-analysis.md`,
waits for the developer to prune it, and then works the surviving items one at a time, ticking each
off as it lands. The checklist survives the session, so the work can be started on one day and
finished on another.

It converts flaky tests from a tolerated background cost into a short, reviewable, resumable task
list — without ever running the suite, touching production code, or fixing anything the developer
did not approve.

## 2. Business Context & Problem Statement

Flaky tests are the most expensive kind of test: they cost more than a failing test and more than no
test at all, because they consume attention without producing signal.

- **Trust decays first, then the suite.** Once a suite fails intermittently, developers re-run rather
  than investigate. Real regressions then hide inside the noise, which is exactly the failure mode
  the suite exists to prevent.
- **Nobody owns them.** A flaky test belongs to whoever's build it broke today. There is no backlog,
  no list, no assignee — so the same tests break the same builds for months.
- **Finding them is slow, and today's tooling wants history.** The conventional approach is to
  instrument CI, accumulate hundreds of runs, and compute a flakiness score. That is a program of
  work: pipeline changes, a results store, a retention policy, and weeks of waiting before the first
  answer. Teams that most need the help are the least able to start.
- **The causes are known and visible in the source.** Hardcoded sleeps, un-awaited async calls,
  shared mutable state between tests, live network calls, unseeded randomness, `now()` in an
  assertion, exact-match snapshots — these are recognizable patterns sitting in the test files right
  now. They do not require a single test run to spot.
- **Knowing is not fixing.** Even teams with a flakiness dashboard still carry the debt, because
  turning a list of offenders into merged fixes is manual work that never wins against feature work.

The reference QE Practice BRD for a Flaky Test Detector & Analyzer describes the full
execution-telemetry system: ingestion of run history, frequency scoring, temporal and concurrency
correlation, dashboards, quarantine and smart-retry policy. That system is valuable and remains the
long-term destination. **This BRD deliberately specifies a different, smaller product**: a
zero-setup, source-only agent that needs no CI integration, no results database, and no run history —
and that goes one step further than the reference by actually applying the fixes, under human
control. It is the first useful slice, and it is available to any project on the day it installs
Spectra.

## 3. Business Objectives & Goals

- **G1 — Answer on day one, with no setup.** Produce a credible list of likely-flaky tests from the
  working tree alone: no CI wiring, no historical run data, no configuration.
- **G2 — Make the list actionable, not informational.** Every candidate carries a confidence rating
  and a specific suggested fix, so the developer can triage in minutes rather than investigate.
- **G3 — Close the loop.** Take approved items all the way to applied fixes in the working tree,
  rather than handing over a report and stopping.
- **G4 — Keep the human in control at every gate.** Nothing is written without consent, nothing is
  edited without a second consent, and the developer can delete any item before work starts.
- **G5 — Survive the session.** Work started today can be finished next week, in a different session,
  without redoing the analysis or losing the developer's pruning decisions.
- **G6 — Never trade correctness for a green build.** A fix must remove the cause of the flakiness.
  Weakening a test — loosening assertions, skipping it, wrapping it in retries — is not a fix and is
  prohibited.
- **G7 — Work on any project.** Language- and framework-agnostic, monorepo-aware, and useful whether
  the suite is 40 tests or 4,000.

## 4. Stakeholders & Users

| Stakeholder / user                    | Role in this product     | What they need from it                                                                                    |
| ------------------------------------- | ------------------------ | --------------------------------------------------------------------------------------------------------- |
| Developer / QE engineer               | Primary user             | One command that finds the flaky tests in their repo and fixes the ones they approve, without babysitting. |
| Tech lead / engineering manager       | Reviewer                 | A durable, reviewable list of what is flaky and what was done about it, and confidence that nothing was silently weakened. |
| Code reviewer on the resulting change | Downstream consumer      | Uncommitted, self-explanatory edits confined to test code, with the reasoning recorded in the checklist.   |
| QE Practice / quality leadership      | Sponsor / governance     | Flakiness treated as tracked, remediable debt with named items and evidence — not an accepted cost.        |
| Other Spectra agents and CI           | Indirect beneficiaries   | A more trustworthy suite, so downstream gates (review, integration, deployment) act on real signal.        |

## 5. Scope

### 5.1 In Scope

- **Test-suite discovery from the working tree**: identify the project's test suite(s) — including
  multiple suites in a monorepo, and multiple frameworks in one project — by reading configuration
  files, directory conventions, and test file naming, with no execution of anything.
- **Static flakiness analysis** of the discovered test code across the recognized signal categories
  (timing and async, test isolation and shared state, unmocked external dependencies,
  non-determinism, brittle assertions, parallel-execution conflicts, environment and time-zone
  coupling, and pre-existing retry or known-flaky annotations).
- **A ranked chat summary**: one row per candidate with test name, file, confidence (High / Medium /
  Low), and a specific suggested fix, plus a plain statement of what was and was not covered.
- **A single durable analysis file** at `.specify/memory/flaky-test-analysis.md`, containing a run
  summary and the same rows rendered as an unchecked task list, written only on the developer's
  explicit consent.
- **Developer pruning**: the developer edits the file — deleting any items they do not want fixed —
  between the two approval gates.
- **Guided remediation**: on a second explicit approval, the agent works the surviving items in
  order, applies the fix to the test code, and ticks each item off as it completes.
- **Resumption across sessions**: on every run, the agent inspects the existing analysis file first
  and branches on its state (pending items, all complete, or unreadable) before doing anything else.
- **A single-file invariant**: exactly one analysis file exists at any time; a new analysis replaces
  it wholesale rather than accumulating dated copies.

### 5.2 Out of Scope

- **Running the test suite.** The agent never executes tests — not to detect flakiness, not to
  reproduce it, and not to verify a fix. Detection is source-only by design (G1). Verification stays
  with the developer and their CI.
- **CI/CD integration, execution-history ingestion, and flakiness scoring.** No results store, no
  run-frequency scores, no temporal or concurrency correlation, no pipeline reliability index. That
  is the reference QE BRD's telemetry system and remains a separate, later product.
- **Dashboards, trend views, and cross-run history.** The analysis file records the latest run only.
- **Quarantine, smart retry, and skip policy.** The agent will not mark tests skipped, add retry
  wrappers, or recommend quarantine as a remedy (G6).
- **Changing production source code.** Fixes are confined to test code and test-support files. Where
  the genuine remedy lives in the application, the agent reports it and leaves the item open.
- **Committing, branching, pushing, or opening a pull request.** Changes are left uncommitted in the
  working tree. Publishing is `speckit.spectra.create-pr`'s job.
- **Installing dependencies, adding test libraries, or reaching the network.**
- **Writing new tests, or improving coverage.** That is the Test Coverage Analyst / Test Automation
  Analyst territory on the roster.
- **Guaranteeing zero false positives.** Static analysis infers risk from patterns; confidence
  ratings and human pruning bound the cost of being wrong.

## 6. User Journeys *(feeds the spec's prioritized user stories)*

### Journey 1 — Find the flaky tests in this repo (Priority: P1)

- **Actor:** Developer / QE engineer
- **Trigger:** Runs the command in a project with a test suite and no prior analysis file.
- **Outcome / value:** Within a single run, a ranked table of likely-flaky tests with a confidence
  rating and a concrete fix for each. This is the MVP: even if the developer declines everything that
  follows, they now have the list they did not have before, and they got it without touching CI.
- **Flow:**
  1. The developer runs the command.
  2. The agent checks `.specify/memory/` for an existing analysis file, finds none, and proceeds.
  3. It discovers the project's test suite(s) from the working tree — frameworks, roots, and test
     files — reading source only.
  4. It analyzes the test code for flakiness signals and assigns each candidate a confidence rating
     and a suggested fix.
  5. It presents the ranked table in chat, with a count summary and a statement of coverage and
     limits.
  6. It asks whether to go ahead and fix them (Journey 2).
- **Acceptance:**
  - **Given** a project containing at least one recognizable test suite, **When** the agent runs,
    **Then** it names each suite it found, its framework, and how many test files it examined, before
    reporting any candidate.
  - **Given** the analysis completes with at least one candidate, **When** the table is presented,
    **Then** every row carries a test name, a project-relative file path, a confidence of exactly
    High, Medium, or Low, and a suggested fix stated in one or two concrete sentences.
  - **Given** any reported row, **When** the referenced test name and file path are checked against
    the working tree, **Then** both exist — no candidate is fabricated or inferred from a file the
    agent did not read.
  - **Given** the analysis completes, **When** the agent reports, **Then** it states what it did not
    cover (suites skipped, files truncated, anything it could not parse).
  - **Given** the agent has produced its table, **When** it finishes reporting, **Then** it has
    written no file and changed nothing in the working tree.

#### Illustrative output — the chat summary (Journey 1, step 5)

<!-- Product surface, not implementation: this is what the developer reads and acts on. -->

```text
Flaky Test Detector — 2 suites · 211 test files · 1,204 tests examined
7 candidates: 3 high · 3 medium · 1 low

| ID     | Test                                    | File                                    | Confidence | Suggested fix                                                                 |
| ------ | --------------------------------------- | --------------------------------------- | ---------- | ----------------------------------------------------------------------------- |
| FT-001 | applies the promo code to the total      | web/src/checkout/promo.test.ts:88       | High       | Replace the 500 ms sleep with an explicit wait on the updated total element.  |
| FT-002 | returns sessions created today           | api/tests/test_sessions.py:142          | High       | Freeze the clock instead of comparing against datetime.now(); the assertion   |
|        |                                          |                                         |            | fails when the run crosses midnight.                                          |
| FT-003 | lists users in registration order        | api/tests/test_users.py:60              | High       | Sort before asserting; the query has no ORDER BY, so row order is arbitrary.  |
| FT-004 | syncs the profile avatar                 | web/src/profile/avatar.test.ts:31       | Medium     | Mock the S3 client; the test performs a live upload and depends on network.   |
| FT-005 | caches the feature flags                 | web/src/flags/cache.test.ts:12          | Medium     | Reset the module-level cache in afterEach; state leaks into later tests.      |
| FT-006 | renders the invoice summary              | web/src/billing/invoice.test.ts:74      | Medium     | Assert on the values, not the exact rendered HTML string.                     |
| FT-007 | generates a unique order reference       | api/tests/test_orders.py:88             | Low        | Seed the random source so the generated reference is reproducible.            |

Coverage: web/ (Jest, 148 files), api/ (pytest, 63 files). Not covered: e2e/
(Playwright) — no test files found under it. 4 files could not be parsed and were
skipped; they are listed at the end of the analysis file if you create one.

Would you like me to go ahead and fix these? The first step is a plan: I write the
list above to .specify/memory/flaky-test-analysis.md as a task list you can review and prune.
Nothing is changed until you approve it.
```

### Journey 2 — Turn the findings into a reviewable plan (Priority: P1)

- **Actor:** Developer / QE engineer
- **Trigger:** Answers yes to the agent's offer at the end of Journey 1.
- **Outcome / value:** A single durable file at `.specify/memory/flaky-test-analysis.md` holding the
  run summary and the candidates as an unchecked task list — a record that outlives the chat session
  and that the developer can edit, share, or attach to a ticket.
- **Flow:**
  1. The developer accepts.
  2. The agent writes the analysis file at the canonical path, replacing any existing file wholesale.
  3. Each candidate becomes a task row whose first column is an unchecked `[ ]`.
  4. The agent reports the path, states that it is now waiting for the developer's review, and says
     explicitly that the developer may delete any rows they do not want fixed.
  5. The agent asks for approval to start fixing (Journey 3).
- **Acceptance:**
  - **Given** consent at this gate, **When** the file is written, **Then** its header states the
    generation timestamp with time zone, the suites analyzed, the number of tests examined, and the
    number of candidates found broken down by confidence.
  - **Given** the file is written, **When** its task table is read, **Then** it holds exactly one row
    per candidate from the chat summary, each row beginning with `[ ]` and carrying the same ID, test
    name, file, confidence, and suggested fix.
  - **Given** the file is written, **When** the agent reports back, **Then** the message names the
    file path, states that the agent is waiting on the developer's review, and states that rows may
    be deleted to exclude them.
  - **Given** an analysis file already existed, **When** the new one is written, **Then** it replaces
    the previous file at the same path — no second file, no dated variant, no appended section.
  - **Given** the developer declines at this gate, **When** the agent stops, **Then** no file is
    created, any existing file is byte-for-byte unchanged, and the working tree is untouched.

#### Illustrative output — the analysis file (Journey 2, step 2)

```markdown
# Flaky Test Analysis

- **Generated:** 2026-08-26 14:32 -07:00
- **Suites analyzed:** web/ (Jest, 148 test files), api/ (pytest, 63 test files)
- **Tests examined:** 1,204
- **Flaky candidates:** 7 — 3 high, 3 medium, 1 low
- **Progress:** 0 of 7 fixed

Delete any row you do not want fixed. Leave `[ ]` for work to be done; the agent
marks `[x]` when it has applied the fix.

## Tasks

| Done | ID     | Test                                | File                              | Confidence | Suggested fix                                                              |
| ---- | ------ | ----------------------------------- | --------------------------------- | ---------- | -------------------------------------------------------------------------- |
| [ ]  | FT-001 | applies the promo code to the total | web/src/checkout/promo.test.ts:88 | High       | Replace the 500 ms sleep with an explicit wait on the updated total.       |
| [ ]  | FT-002 | returns sessions created today      | api/tests/test_sessions.py:142    | High       | Freeze the clock instead of comparing against datetime.now().              |
| [ ]  | FT-003 | lists users in registration order   | api/tests/test_users.py:60        | High       | Sort before asserting; the query has no ORDER BY.                          |
| [ ]  | FT-004 | syncs the profile avatar            | web/src/profile/avatar.test.ts:31 | Medium     | Mock the S3 client; the test performs a live upload.                       |
| [ ]  | FT-005 | caches the feature flags            | web/src/flags/cache.test.ts:12    | Medium     | Reset the module-level cache in afterEach.                                 |
| [ ]  | FT-006 | renders the invoice summary         | web/src/billing/invoice.test.ts:74| Medium     | Assert on the values, not the exact rendered HTML string.                  |
| [ ]  | FT-007 | generates a unique order reference  | api/tests/test_orders.py:88       | Low        | Seed the random source so the reference is reproducible.                   |

## Evidence

- **FT-001** — `await sleep(500)` at line 84 followed by an assertion on `total`
  at line 88; the wait is unconditional and unrelated to the element it guards.
- **FT-002** — assertion compares a stored `created_at` against `datetime.now()`
  with a same-day equality check.
- …

## Not analyzed

- `web/src/legacy/__tests__/bundle.spec.ts` — file could not be parsed (4 files total).
```

### Journey 3 — Fix the approved items (Priority: P1)

- **Actor:** Developer / QE engineer
- **Trigger:** Has reviewed (and possibly pruned) the analysis file, and tells the agent to proceed.
- **Outcome / value:** The approved flaky tests are actually fixed in the working tree, each item
  ticked off as it lands, with a closing report of what was fixed, what was not, and why.
- **Flow:**
  1. The developer approves.
  2. The agent re-reads the analysis file from disk, so the developer's deletions and edits are what
     it acts on.
  3. It works the unchecked rows in file order: reads the test, applies the fix that removes the
     cause, and confirms the edit is confined to test code.
  4. After each successful fix it immediately marks that row `[x]` and updates the progress count.
  5. Where it cannot fix an item confidently — or the real remedy lies in production code — it leaves
     the row `[ ]` and records the reason.
  6. It reports the totals, the files it touched, and that the changes are uncommitted and ready for
     review.
- **Acceptance:**
  - **Given** the developer deleted rows before approving, **When** the agent proceeds, **Then** it
    acts only on the rows present in the file at that moment, and the deleted tests are never opened
    or modified.
  - **Given** a row is fixed, **When** the agent moves to the next row, **Then** the completed row is
    already `[x]` on disk — progress is checkpointed per item, not written in one batch at the end.
  - **Given** the session is interrupted midway, **When** the file is inspected, **Then** every fix
    already applied is marked `[x]` and every remaining item is still `[ ]`.
  - **Given** any applied fix, **When** the resulting diff is reviewed, **Then** it touches only test
    files and test-support files, and no assertion has been deleted, loosened to always pass, skipped,
    marked expected-to-fail, or wrapped in a retry.
  - **Given** an item whose genuine remedy is in production source, **When** the agent reaches it,
    **Then** it leaves the row `[ ]`, records what would need to change and where, and continues to
    the next item.
  - **Given** the run completes, **When** the agent reports, **Then** it states how many items were
    fixed, how many were left open with reasons, which files it changed, and that nothing was
    committed or pushed.

### Journey 4 — Resume unfinished work in a later session (Priority: P1)

- **Actor:** Developer returning after closing the previous session
- **Trigger:** Runs the command in a project whose analysis file still has unchecked items.
- **Outcome / value:** The agent picks up exactly where the work stopped, with no re-analysis and no
  loss of the developer's earlier pruning.
- **Flow:**
  1. The agent's first action is to look for the analysis file at
     `.specify/memory/flaky-test-analysis.md`.
  2. It finds one with unchecked items, reads it, and reports when it was generated, how many items
     it holds, how many are done, and how many are pending.
  3. It asks whether to proceed with the pending items — offering, as alternatives, discarding the
     file and running a fresh analysis, or stopping.
  4. On approval it proceeds as in Journey 3, working the pending rows only.
- **Acceptance:**
  - **Given** an analysis file with at least one unchecked item, **When** the command is run, **Then**
    the agent reports the file's date and its done/pending counts before offering any action, and
    performs no new analysis unless the developer asks for one.
  - **Given** the developer approves, **When** the agent proceeds, **Then** it fixes only the
    unchecked items and never re-opens an item already marked `[x]`.
  - **Given** the developer chooses a fresh analysis instead, **When** the agent proceeds, **Then**
    it states plainly that the pending items in the current file will be replaced, and replaces the
    file only after producing a new plan the developer accepts.
  - **Given** the developer declines both, **When** the agent stops, **Then** the file and the
    working tree are unchanged.

### Journey 5 — Re-run after everything is done (Priority: P2)

- **Actor:** Developer whose previous run completed every item
- **Trigger:** Runs the command with an analysis file in which every item is `[x]` (or which holds no
  items at all).
- **Outcome / value:** A fresh analysis on the current state of the code, without the developer
  having to find and delete the old file first — and without the agent silently discarding a record.
- **Flow:**
  1. The agent finds the file and determines that nothing is pending.
  2. It reports that a previous analysis exists, when it ran, and that all of its items are complete.
  3. It asks whether to run the analysis again, stating that a new plan will replace this file.
  4. On yes, it runs a fresh analysis and continues from Journey 1, step 5.
- **Acceptance:**
  - **Given** an analysis file with no unchecked items, **When** the command is run, **Then** the
    agent reports the previous run's date and completion state and asks whether to re-analyze, rather
    than analyzing immediately or silently overwriting.
  - **Given** the developer says yes and the new analysis produces candidates they accept, **When**
    the file is written, **Then** it replaces the previous file at the same path, so exactly one
    analysis file still exists.
  - **Given** the developer says yes and the new analysis finds no candidates, **When** the agent
    reports, **Then** it says so, leaves the existing completed file in place unchanged, and tells the
    developer they can delete it if they no longer need the record.
  - **Given** the developer says no, **When** the agent stops, **Then** nothing is read further,
    written, or changed.

### Journey 6 — Nothing to act on (Priority: P3)

- **Actor:** Developer on a project with no tests, or with a clean suite
- **Trigger:** Runs the command where no test suite exists, or where the analysis finds no candidates.
- **Outcome / value:** A fast, unambiguous answer and a clean exit — no empty file, no invented
  findings, no prompt to act on nothing.
- **Flow:**
  1. The agent checks for an existing analysis file (none) and discovers test suites.
  2. If no suite is found, it says so — naming where it looked — and exits.
  3. If suites are found but no candidate meets the bar, it reports the suites and file counts,
     states that no likely-flaky tests were identified, and exits.
- **Acceptance:**
  - **Given** a project with no recognizable test suite, **When** the command is run, **Then** the
    agent reports that none was found, names the locations and conventions it checked, writes no file,
    and stops without asking any further question.
  - **Given** suites are found but no candidate is identified, **When** the agent reports, **Then** it
    states the suites and coverage, reports zero candidates, writes no file, and does not offer to
    create a plan.
  - **Given** either outcome, **When** the run ends, **Then** no file has been created and no file in
    the working tree has been modified.

### Edge Cases

- **The analysis file is unreadable or has been edited into an unparseable state.** The agent reports
  what it could not read, never overwrites silently, and offers a fresh analysis (which would replace
  the file) or stopping.
- **The file has a mix of `[x]` and `[ ]` items.** Treated as pending (Journey 4); done items are
  never re-opened.
- **The developer deleted every row before approving.** The agent reports that there is nothing to
  fix, leaves the file as the record, and stops without editing anything.
- **A pending item's test has been renamed, moved, or deleted since the analysis.** The agent does not
  guess and does not edit a similarly-named test. It leaves the row `[ ]` with a note saying the test
  could not be located, and continues.
- **The developer edited a row's suggested fix.** The developer's wording is what the agent acts on;
  it does not restore its own text.
- **The developer manually ticked a row `[x]` because they fixed it themselves.** The agent honors the
  mark and skips the item.
- **A monorepo with several suites in different languages.** All discovered suites are analyzed and
  reported in one table; the file column disambiguates.
- **A suite too large to analyze exhaustively in one run.** The agent analyzes what it can, and states
  plainly what it did not reach — a silent partial pass is a defect (BR-12).
- **A test already annotated as known-flaky or configured with retries.** Treated as strong
  corroborating evidence, not as a reason to skip the test — the annotation is a symptom, and removing
  the underlying cause is the fix.
- **The project is not a Spec Kit project (`.specify/memory/` is absent).** The agent says where the file
  would go and what needs to exist first, rather than creating the directory tree unannounced.

## 7. Business Requirements

| ID    | Requirement                                                                                                                                                                                             | Priority |
| ----- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| BR-01 | The agent MUST, as its first action on every run, check for an existing analysis file at `.specify/memory/flaky-test-analysis.md` and branch on its state (pending items / all complete / unreadable / absent) before any analysis.  | P1       |
| BR-02 | The agent MUST maintain at most **one** analysis file, at a single canonical path. It MUST NOT create a second file, a dated variant, or an appended second analysis.                                     | P1       |
| BR-03 | The agent MUST identify the project's test suite(s) by reading the working tree only — configuration, directory conventions, and test file naming — including multiple suites and multiple frameworks.     | P1       |
| BR-04 | The agent MUST NOT execute tests, run build or package commands, install dependencies, or access the network at any point.                                                                                | P1       |
| BR-05 | When no test suite is found, the agent MUST report that plainly, name the locations and conventions it checked, write nothing, and exit.                                                                  | P1       |
| BR-06 | The agent MUST analyze discovered test code for flakiness signals across at least: timing and async (sleeps, missing waits, un-awaited calls), test isolation and shared state, unmocked external dependencies, non-determinism (unseeded randomness, real clock, unordered collections), brittle assertions, parallel-execution conflicts, environment and time-zone coupling, and existing retry or known-flaky annotations. | P1       |
| BR-07 | Every candidate MUST carry a stable ID, the test name, a project-relative file path (with line where determinable), a confidence of exactly High / Medium / Low, and a suggested fix stated concretely in one or two sentences. | P1       |
| BR-08 | The agent MUST apply a stated, consistent confidence rubric, and MUST NOT rate a candidate High without direct supporting evidence in the test source.                                                    | P1       |
| BR-09 | Every reported test name and file path MUST correspond to something that exists in the working tree. The agent MUST NOT report a candidate it did not read.                                               | P1       |
| BR-10 | When no candidate meets the bar, the agent MUST report zero findings plainly and MUST NOT lower its bar to produce a non-empty list.                                                                      | P1       |
| BR-11 | The agent MUST present the candidates as a table in chat — test name, file, confidence, suggested fix — **before** writing any file.                                                                       | P1       |
| BR-12 | The agent MUST state its coverage and limits: which suites and how many files it examined, and anything it skipped, could not parse, or did not reach.                                                    | P1       |
| BR-13 | The agent MUST obtain explicit consent (Gate 1) before creating or replacing the analysis file, and MUST state that this step produces a plan, not a code change.                                         | P1       |
| BR-14 | On consent, the file MUST open with a summary carrying at minimum: generation timestamp including time zone, suites analyzed, number of tests examined, candidate count broken down by confidence, and fixed-vs-total progress. | P1       |
| BR-15 | The file MUST render each candidate as a task row whose first column is a literal `[ ]`, carrying the same ID, test name, file, confidence, and suggested fix shown in chat.                               | P1       |
| BR-16 | After writing, the agent MUST report the file path, state that it is waiting on the developer's review, and state explicitly that rows may be deleted to exclude those tests from the fix run.            | P1       |
| BR-17 | Declining at Gate 1 MUST leave any existing analysis file byte-for-byte unchanged and the working tree untouched.                                                                                          | P1       |
| BR-18 | Writing a new plan MUST replace the previous file wholesale at the same path. The agent MUST NOT delete the analysis file except by replacing it with a newly accepted plan.                              | P1       |
| BR-19 | The agent MUST obtain a second explicit approval (Gate 2), after the developer's review, before editing any file in the project.                                                                          | P1       |
| BR-20 | At Gate 2 the agent MUST re-read the analysis file from disk and act only on the unchecked rows present at that moment. Rows the developer deleted MUST NOT be opened or modified.                        | P1       |
| BR-21 | The agent MUST mark a row `[x]` and update the progress count on disk immediately after applying that row's fix, before starting the next — progress MUST NOT be batched to the end of the run.           | P1       |
| BR-22 | Edits MUST be confined to test code and test-support files (fixtures, helpers, test configuration). The agent MUST NOT modify production source code.                                                     | P1       |
| BR-23 | A fix MUST remove the cause of the flakiness. The agent MUST NOT deliver as a fix: deleting or loosening an assertion so it always passes, skipping or marking a test expected-to-fail, adding retry wrappers, or lengthening a sleep. | P1       |
| BR-24 | Any item the agent cannot fix confidently — including one whose real remedy lies in production code or whose test can no longer be located — MUST be left `[ ]` with a short recorded reason, and the run MUST continue to the next item. | P1       |
| BR-25 | The agent MUST NOT commit, stage-and-commit, push, create branches, or open pull requests. Changes remain uncommitted in the working tree.                                                                | P1       |
| BR-26 | On completing a fix run, the agent MUST report how many items were fixed, how many were left open and why, which files it changed, and that the changes are uncommitted and awaiting review.              | P1       |
| BR-27 | Where an analysis file has unchecked items, the agent MUST report its generation date and its done/pending counts, then offer: continue with the pending items, discard and re-analyze, or stop.          | P1       |
| BR-28 | Where an analysis file has no unchecked items, the agent MUST report that the previous analysis is complete and ask whether to re-run, rather than analyzing immediately or overwriting silently.         | P1       |
| BR-29 | Where the analysis file exists but cannot be parsed, the agent MUST say so, MUST NOT overwrite it silently, and MUST offer a fresh analysis or stopping.                                                  | P1       |
| BR-30 | The agent MUST honor developer edits to the file — deleted rows, reworded suggested fixes, and manually ticked items — over its own previously generated content.                                          | P2       |
| BR-31 | The file SHOULD record, per candidate, the specific evidence that triggered it, so a later session (or a human) can act on the item without re-running the analysis.                                      | P2       |
| BR-32 | The agent MUST be a single agent-agnostic, namespaced Spectra command that runs on whatever coding agent the team uses, and MUST be language- and framework-agnostic in what it can analyze.               | P1       |
| BR-33 | The agent SHOULD accept an optional scope argument narrowing the analysis to a path or a named suite, and MUST state the scope it actually analyzed.                                                       | P3       |
| BR-34 | Where `.specify/memory/` does not exist, the agent MUST report what is missing and where the file would go, rather than creating the directory tree unannounced.                                          | P2       |

## 8. Success Metrics & Measurable Outcomes

- **SC-01** — A developer gets a ranked list of likely-flaky tests from **one command run**, in a
  project with zero prior configuration, CI integration, or historical run data.
- **SC-02** — 100% of reported candidates are traceable: the test name and file path exist in the
  working tree and the cited evidence is present at the cited location. Zero fabricated rows.
- **SC-03** — Zero writes without consent: across a pilot, no analysis file is created or replaced,
  and no source file is edited, without the corresponding explicit approval.
- **SC-04** — Zero weakened tests: across all applied fixes in a pilot, no assertion is deleted or
  loosened to always pass, no test is skipped or marked expected-to-fail, and no retry wrapper is
  added as a remedy (verifiable from the diff).
- **SC-05** — Zero production-code edits: 100% of the changed files in a fix run are test or
  test-support files.
- **SC-06** — Resumption is lossless: after a session ends mid-run, a later run resumes with 100% of
  completed items still marked done and 100% of pending items still pending, with no re-analysis.
- **SC-07** — Pruning is respected: 100% of rows deleted by the developer before approval result in no
  modification to those tests.
- **SC-08** — Precision at High confidence: in pilot review, at least 80% of High-confidence
  candidates are judged genuinely flaky (or genuinely at risk of intermittent failure) by the
  reviewing engineer.
- **SC-09** — Fix quality: at least 75% of applied fixes are accepted by the reviewing engineer
  without rework in pilot sampling.
- **SC-10** — Exactly one analysis file exists at every point in the lifecycle, across create,
  resume, complete, and re-run — never zero-when-work-is-pending, never two.
- **SC-11** — Triage cost: a developer can review and prune a typical generated task list in under
  10 minutes, because each row is atomic, evidenced, and carries a stated fix.

## 9. Assumptions

- The project uses Spec Kit, so a `.specify/memory/` directory exists — the same directory that holds
  the constitution and `domain-analysis.md` (or the developer is told what is missing — BR-34).
- The analysis file is a **working artifact**, not a published deliverable: it is a task list the
  agent and the developer hand back and forth, which is why it belongs under `.specify/memory/`
  rather than the artifact root of Principle VII — the same reasoning that puts
  `.specify/memory/domain-analysis.md` there, and it sits beside that file for the same reason.
- The canonical path is **`.specify/memory/flaky-test-analysis.md`** — settled, not proposed. The
  requested `flaky_test_analysis` name is rendered in the repository's kebab-case convention.
- Adding a stable per-row ID (`FT-001`) beyond the four columns requested is worth it: it makes
  resumption, pruning, and reporting unambiguous across sessions. Stated here so it can be challenged.
- Markdown `[ ]` / `[x]` is an acceptable state marker. It is literal text in a table cell, not an
  interactive control, and both the agent and the developer can edit it.
- Static analysis of test source is sufficient to identify the dominant classes of flakiness. The
  established causes — sleeps, un-awaited async, shared state, live dependencies, unseeded randomness,
  real clocks, exact-match assertions — are visible in the code without a single run.
- Confidence is a judgment, not a computed score. Without run history there is no frequency
  denominator, so High/Medium/Low expresses strength of evidence, not measured failure rate.
- The developer, or their CI, verifies the fixes by running the suite. The agent does not.
- Common frameworks (for example Jest, Vitest, Playwright, Cypress, Mocha, pytest, unittest, JUnit,
  TestNG, Go's testing package, RSpec, PHPUnit, xUnit/NUnit) are recognizable from configuration and
  naming conventions. These are examples of reach, not a fixed supported list.
- Fixes are reviewed as a normal change — left uncommitted so `git diff` is the review surface.

## 10. Constraints

- **Principle III (agent-agnostic commands).** One command file, written in Spec Kit's generic format
  using `$ARGUMENTS`, namespaced `speckit.spectra.<command>`, with YAML front matter and registered in
  `provides.commands`. No agent-specific invocation syntax.
- **Principle IV (context-aware by default).** The agent reads real project state — the working tree,
  the constitution, and any existing analysis file — before acting. This is the product, not a nicety.
- **Principle VII (artifact root).** The analysis file is context for a later run of the same command,
  not a human-facing deliverable, so it lives at `.specify/memory/flaky-test-analysis.md` — inside the
  Spec Kit locations the principle explicitly places outside the artifact-root rule, beside
  `domain-analysis.md`. If it were ever reclassified as a deliverable it would have to move to
  `<artifact-root>/flaky-test-analysis/` and take a sequence number — a different product.
- **Principle VIII (overridable templates).** Applies to durable Markdown deliverables. Whether the
  analysis file should nonetheless ship as a registered, overridable template is an open question
  below; `domain-analysis.md` sets the precedent that it need not.
- **Principle V (catalog and package in sync).** Shipping the agent requires, in the same change:
  registration in `agents-list.json`, `spectra/extension.yml`, `catalog.json`,
  `spectra/CHANGELOG.md`, the regenerated listings, `docs/packages/spectra.zip`, and
  `docs/index.html`. Build-time obligation, not runtime behavior.
- **Read-write effect, narrowly.** The agent's writes are limited to its own analysis file and to test
  code the developer has approved item by item. It never writes production source, never writes
  governance, and never writes outside the project.
- **Human-in-the-loop is non-negotiable.** Two explicit gates — plan, then fix — and the ability to
  delete any item in between. No auto-apply mode.
- **No execution.** The agent's read of the project is static. It cannot rely on running anything.

## 11. Dependencies

- **Input:** the project's working tree — test files, test configuration, fixtures and helpers — and
  the project constitution under `.specify/memory/`.
- **Input / output:** `.specify/memory/flaky-test-analysis.md`, which the agent writes in one run and reads
  in the next. It is the entire cross-session contract.
- **Downstream (optional):** `speckit.spectra.create-pr` can open a PR for the resulting changes; this
  agent deliberately stops at an uncommitted working tree.
- **Adjacent on the roster:** Test Coverage Analyst and Test Automation Analyst (both Testing &
  Quality, both planned) cover coverage gaps and automation placement; this agent does neither.
- **Long-term:** the reference QE Practice telemetry system (execution-history ingestion, flakiness
  scoring, dashboards). This agent produces no data for it and does not depend on it; the two could
  later be complementary, with history confirming what static analysis suspects.
- **Roster and packaging:** `agents-list.json` and the generated listings, per Principle V.

## 12. Risks & Mitigations

| Risk                                                                     | Impact | Likelihood | Mitigation                                                                                                                |
| ------------------------------------------------------------------------ | ------ | ---------- | ------------------------------------------------------------------------------------------------------------------------- |
| False positives — a stable test flagged as flaky                         | M      | H          | Confidence rubric with High reserved for direct evidence (BR-08); evidence recorded per row (BR-31); the developer prunes before anything is edited (BR-20). |
| A "fix" that hides a real defect by weakening the test                   | H      | M          | BR-23 prohibits assertion-loosening, skipping, and retries as remedies; SC-04 measures it from the diff; changes stay uncommitted for review. |
| A fix changes production behavior to make a test pass                    | H      | L          | BR-22 confines edits to test code; production-side remedies are reported, not applied (BR-24); SC-05 measures it.          |
| False negatives — genuinely flaky tests missed                           | M      | H          | Multiple signal categories (BR-06); explicit coverage-and-limits statement so the developer knows what was not examined (BR-12); re-run is cheap and non-destructive. |
| Silent partial analysis on a large monorepo presented as complete        | M      | M          | BR-12 makes stating what was not reached mandatory; a silent truncation is a defect, not a degradation.                    |
| The single-file rule loses a previous analysis the developer still wanted | M      | M          | Replacement only ever happens as part of writing a newly accepted plan (BR-18); the developer is told replacement is coming before it happens (BR-27, BR-28). |
| A stale plan is applied to code that has since moved on                  | M      | M          | The file records its generation timestamp (BR-14); items whose tests cannot be located are left open with a note (BR-24); re-analysis is always offered on resume (BR-27). |
| Developer hand-edits break the file's structure                          | L      | M          | Never overwrite an unparseable file silently (BR-29); honor edits that are parseable (BR-30).                              |
| Batch-at-the-end progress marking loses work on interruption             | M      | M          | Per-item checkpointing is a requirement (BR-21) with its own acceptance criterion in Journey 3.                             |
| Expectation gap — users expect the reference BRD's dashboards and scores | M      | M          | Scope section 5.2 names the exclusions explicitly; the agent's own coverage statement never implies run history.            |

## 13. Open Questions

- **Template registration.** Should the analysis file's structure ship as a registered, overridable
  template under `spectra/templates/` (Principle VIII's mechanism) even though it is a
  `.specify/memory/` working artifact rather than a deliverable? `domain-analysis.md`, its neighbour,
  has no template today.
- **Command name.** The roster registers this agent as `flaky-test-detector` / "Flaky Test Detector"
  in the Testing & Quality phase, under development. Confirm the command it exposes on shipping is
  `speckit.spectra.flaky-test-detector`.
- **Low-confidence items in the plan.** Include every candidate and let the developer prune (assumed),
  or omit Low-confidence rows from the file unless asked?
- **Optional verification.** Should the agent be allowed to offer to run the affected tests after
  fixing, as an explicitly-consented extra step? Currently out of scope — the agent never executes
  anything.
- **Production-side remedies.** When the real fix is in application code, is a recorded note enough
  (assumed), or should the agent propose the change for the developer to apply?
- **Scope argument (BR-33).** Ship the optional path/suite narrowing in the first release, or defer?
- **Volume cap.** Should there be a maximum number of candidates per run for very large suites, and if
  so, how is the remainder surfaced?
- **History.** The single-file rule means each analysis replaces the last, so nothing accumulates. Is a
  short "previous runs" summary retained in the file worth having, or is that the telemetry system's job?

## 14. Glossary

| Term                       | Definition                                                                                                                                |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| Flaky test                 | A test that can pass or fail on the same code, because its outcome depends on something other than the behavior it claims to verify.       |
| Flakiness signal           | A pattern in test source that makes intermittent failure likely — a sleep, un-awaited async, shared mutable state, a live network call, unseeded randomness, a real clock, an exact-match assertion. |
| Candidate                  | One test the agent has identified as likely flaky, with its ID, location, confidence, and suggested fix.                                    |
| Confidence (High/Med/Low)  | The strength of the evidence in the source, not a measured failure rate. High requires direct evidence in the test itself.                  |
| Analysis file              | `.specify/memory/flaky-test-analysis.md` — the single Markdown file holding the run summary and the task list. The agent's only durable output and its cross-session memory. |
| Task row                   | One line of the analysis file's table, beginning `[ ]` (to do) or `[x]` (fixed), representing one candidate.                                |
| Gate 1                     | The consent to write the plan. Produces the analysis file; changes no code.                                                                 |
| Gate 2                     | The consent to fix, given after the developer has reviewed and pruned the file. The only point at which test code is edited.                |
| Pruning                    | The developer deleting rows from the analysis file so those tests are excluded from the fix run.                                            |
| Test-support file          | A fixture, helper, factory, mock, or test configuration file that exists to serve the tests — in scope for edits, unlike production source.  |
| Weakening a test           | Making a test pass by reducing what it verifies — deleting or loosening assertions, skipping, expecting failure, or retrying. Prohibited as a fix. |
| Single-file invariant      | At most one analysis file exists at any time; a new accepted plan replaces the previous file wholesale.                                     |
| Add-on agent               | An optional Spectra agent enabled per project need, as opposed to a required core agent.                                                     |
