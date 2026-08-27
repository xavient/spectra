# Feature Specification: Flaky Test Detector

**Feature Branch**: `018-flaky-test-detector`

**Created**: 2026-08-26

**Status**: Draft

**Input**: `brds/flaky-test-detector.md` (BRD-008, v0.1.0) — the Flaky Test Detector agent
(`speckit.spectra.flaky-test-detector`): a source-only agent that identifies the project's test
suite(s) from the working tree, statically detects likely-flaky tests, reports them with a confidence
rating and a concrete suggested fix, and — behind two explicit consent gates — writes a resumable task
list to `.specify/memory/flaky-test-analysis.md` and applies the approved fixes. The BRD deliberately
scopes down the TELUS Digital QE Practice reference document, which specifies the execution-telemetry
version of this capability (run-history ingestion, flakiness scoring, dashboards, quarantine policy).

## Clarifications

### Session 2026-08-26

The BRD closed with eight open questions (§13). Each is settled below as a decision with its
rationale, rather than carried into the spec as an unknown. Any of them can be reopened with
`/speckit-clarify`.

- Q: Should the analysis file ship as a registered, overridable template (Principle VIII)? → A: **No.**
  Principle VIII governs durable Markdown *deliverables*. The analysis file is a working artifact under
  `.specify/memory/` — context the command writes for its own next run — which is the same category as
  `domain-analysis.md`, which has no template. Its structure is defined by this spec and carried in the
  command. The plan's Constitution Check must confirm this reading rather than assume it.
- Q: What command does the agent expose? → A: `speckit.spectra.flaky-test-detector`, matching the
  roster id `flaky-test-detector` already registered under development.
- Q: Do low-confidence candidates reach the plan file? → A: **Yes, all candidates do.** Filtering is
  the developer's job and they do it by deleting rows. Ordering by confidence (FR-016) puts the weakest
  rows at the bottom, where pruning is cheapest.
- Q: May the agent offer to run the affected tests after fixing? → A: **No.** FR-003 forbids execution
  outright, including for verification. A single exception would make "this agent never runs your
  tests" untrue, and running a suite after editing it is exactly where an agent would be tempted to
  iterate until green — which is how tests get weakened. Verification stays with the developer and CI.
- Q: When the real remedy lives in production code, does the agent propose the change? → A: **It
  records what would need to change and where, and leaves the item open.** It does not edit production
  source (FR-032) and does not stage a speculative production diff.
- Q: Does the optional scope argument ship in the first release? → A: **Yes.** The command must accept
  a generic arguments placeholder regardless (Principle III), so honouring an optional path or suite
  name costs little and is what makes the agent usable on a large monorepo.
- Q: Is there a cap on how many candidates one run may report? → A: **No fixed numeric cap.** A cap
  would silently decide for the developer which flakiness matters. Instead, candidates are ordered by
  confidence and the coverage statement (FR-015) must disclose anything the run could not reach.
- Q: Should the file retain a summary of previous runs? → A: **No.** Cross-run history is excluded by
  the BRD (§5.2) and is the telemetry system's job. The single-file invariant means each accepted plan
  replaces the last.
- Q: Before editing a test from the task list, must the agent re-check that the recorded evidence is
  still present? → A: **Yes.** A plan can sit for days, and a teammate may have already removed the
  sleep or rewritten the test around it. The agent re-reads the test and confirms the recorded evidence
  before editing; where the evidence is gone or materially changed it leaves the row `[ ]` with a note
  that the code moved on, and continues (FR-031a).
- Q: What happens to pending rows outside the scope of a narrowed re-run, given that a new plan
  replaces the file wholesale? → A: **Replacement stays whole-file, but it must be disclosed by name.**
  Before writing a plan whose scope is narrower than the file it would replace, the agent names the
  pending rows that fall outside the new scope and waits for an explicit answer. One file, one
  timestamp, one scope — and no unfinished work discarded without the developer seeing the list
  (FR-029a).
- Q: Where in the file is the reason recorded when the agent leaves a row unfixed? → A: **In a
  dedicated outcomes section keyed by candidate identifier**, alongside the evidence section and shaped
  the same way. The task table keeps exactly the columns shown in chat, and a returning reader has one
  place to learn why a row is still open (FR-026a).
- Q: May a fix create new test-support files, or change shared test configuration? → A: **Both are
  allowed, and anything reaching past the row's own test must be declared.** A mock with nowhere to
  live is a fix that never lands, so creating a helper, fixture, or mock is in scope — but a change to
  suite-wide setup affects tests the developer did not approve, so the agent names it in the run report
  and in the file (FR-032a). Creating a file never extends to production source, and never to adding a
  dependency (FR-003).
- Q: Does the project constitution constrain which fix the agent applies, and whose constitution is
  it? → A: **The consumer project's, when it exists, and it is binding.** The agent reads
  `.specify/memory/constitution.md` in the project the command is run from — not Spectra's own — and
  every suggested and applied fix must conform to it. Where a guardrail rules out the only remedy, the
  row is left `[ ]` with that rule named as the reason. Where the project declares no constitution, the
  agent proceeds on technical merit and says so (FR-033a).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Find the flaky tests in this repository (Priority: P1)

A developer runs the command in a project that has tests and no prior analysis. The agent works out
what the test suite(s) are by reading the working tree, analyzes the test code, and reports a ranked
table of likely-flaky tests — each with a file, a confidence rating, and a specific suggested fix —
followed by a statement of what it did and did not cover.

**Why this priority**: this is the MVP and it stands alone. A developer who declines everything that
follows still leaves the run with a list they did not have before, produced with no CI wiring, no
results store, and no waiting for run history to accumulate. Every later story depends on this one;
none of them is worth building if this list is not credible.

**Independent Test**: run the command in a repository with known flaky patterns and confirm the table
names real tests at real paths, rates each one, suggests a fix, discloses coverage — and that nothing
on disk changed.

**Acceptance Scenarios**:

1. **Given** a project containing at least one recognizable test suite, **When** the agent runs,
   **Then** it names each suite it found, its framework, and how many test files it examined, before
   reporting any candidate.
2. **Given** the analysis produces at least one candidate, **When** the table is presented, **Then**
   every row carries a stable ID, a test name, a project-relative file path, a confidence of exactly
   High, Medium, or Low, and a suggested fix stated concretely in one or two sentences.
3. **Given** any reported row, **When** its test name, file path, and cited evidence are checked
   against the working tree, **Then** all three are present as reported.
4. **Given** the analysis completes, **When** the agent reports, **Then** it states what it did not
   cover — suites skipped, files it could not parse, anything it did not reach.
5. **Given** the agent has finished reporting, **When** the working tree is inspected, **Then** no file
   has been created and no file has been modified.

---

### User Story 2 - Turn the findings into a reviewable plan (Priority: P1)

The developer accepts the agent's offer, and the candidates become a durable task list at
`.specify/memory/flaky-test-analysis.md`: a run summary, one unchecked row per candidate, and the
evidence behind each. The agent then stops and waits, telling the developer they may delete any rows
they do not want fixed.

**Why this priority**: without the file the whole capability lives and dies inside one chat session.
The file is what makes the work reviewable by someone other than the person who ran the command, and
it is the only thing that makes User Story 4 possible.

**Independent Test**: accept at the gate, then confirm the file exists at the canonical path with a
complete header, one `[ ]` row per candidate, and evidence per row — and that declining instead leaves
the tree untouched.

**Acceptance Scenarios**:

1. **Given** consent at the gate, **When** the file is written, **Then** its header states the
   generation timestamp with time zone, the scope analyzed, the suites, the number of tests examined,
   the candidate count broken down by confidence, and the fixed-vs-total progress.
2. **Given** the file is written, **When** its task table is read, **Then** it holds exactly one row
   per candidate reported in chat, each beginning with a literal `[ ]` and carrying the same ID, test
   name, file, confidence, and suggested fix.
3. **Given** the file is written, **When** its evidence section is read, **Then** every task row's ID
   resolves to the specific signal and location that triggered it.
4. **Given** the file is written, **When** the agent reports back, **Then** it names the path, states
   that it is waiting on the developer's review, and states that rows may be deleted to exclude those
   tests from the fix run.
5. **Given** an analysis file already existed, **When** a new plan is written, **Then** it replaces the
   previous file at the same path — no second file, no dated variant, no appended section.
6. **Given** the developer declines at this gate, **When** the agent stops, **Then** no file is
   created, any existing file is byte-for-byte unchanged, the working tree is untouched, and the agent
   says so.

---

### User Story 3 - Fix the approved items (Priority: P1)

The developer has read the file, deleted the rows they disagree with, and tells the agent to proceed.
The agent works the surviving unchecked rows one at a time, applying the fix that removes the cause of
the flakiness, ticking each row off on disk as it lands, and leaving open — with a recorded reason —
anything it cannot fix confidently.

**Why this priority**: this is what separates the agent from a report. It is also where the safety
rules earn their place: an agent that may edit tests in order to make them pass has an easy degenerate
solution available to it, and this story is only valuable if that solution is closed off.

**Independent Test**: approve a pruned file, then inspect the resulting diff — every `[x]` row has a
corresponding edit, every edit is in a test or test-support file, no assertion was weakened, and no
deleted row's test was touched.

**Acceptance Scenarios**:

1. **Given** the developer deleted rows before approving, **When** the agent proceeds, **Then** it acts
   only on the rows present in the file at that moment, and the deleted tests are never opened or
   modified.
2. **Given** a row has been fixed, **When** the agent begins the next row, **Then** the completed row
   is already `[x]` on disk and the progress count is updated — progress is checkpointed per item, not
   batched to the end of the run.
3. **Given** the session is interrupted midway, **When** the file is inspected, **Then** every fix
   already applied is marked `[x]` and every remaining item is still `[ ]`.
4. **Given** any applied fix, **When** the resulting diff is reviewed, **Then** it touches only test
   and test-support files, and no assertion has been deleted, loosened so that it always passes, and no
   test has been skipped, marked expected-to-fail, wrapped in a retry, or given a longer sleep.
5. **Given** a fix that adds a test-support file or changes shared test setup, **When** the agent
   reports, **Then** the created file is named and any change reaching tests beyond that row is stated
   as such, in both the run report and the file, rather than presented as an ordinary single-row fix.
6. **Given** an item whose genuine remedy is in production source, **When** the agent reaches it,
   **Then** it leaves the row `[ ]`, records what would need to change and where, and continues to the
   next item.
7. **Given** a project guardrail that rules out the only available remedy, **When** the agent reaches
   that item, **Then** it leaves the row `[ ]`, names the rule that blocked it as the reason, and
   applies nothing.
8. **Given** the run completes, **When** the agent reports, **Then** it states how many items were
   fixed, how many were left open and why, which files it changed, and that nothing was committed or
   pushed.

---

### User Story 4 - Resume unfinished work in a later session (Priority: P1)

A developer returns days later and runs the command again. Before anything else, the agent finds the
existing file, reports when it was generated and how many items are done versus pending, and offers to
carry on with the pending ones.

**Why this priority**: flaky-test remediation is not one sitting's work, and a list that has to be
regenerated from scratch every session is a list nobody finishes. It is also the story that protects
the developer's pruning decisions, which would otherwise be silently discarded by a re-analysis.

**Independent Test**: leave a file with a mix of `[x]` and `[ ]` rows, run the command in a fresh
session, and confirm the agent reports the counts, performs no new analysis, and fixes only the
pending rows.

**Acceptance Scenarios**:

1. **Given** an analysis file with at least one unchecked item, **When** the command is run, **Then**
   the agent reports the file's generation date and its done/pending counts before offering any action,
   and performs no new analysis unless the developer asks for one.
2. **Given** the developer approves continuing, **When** the agent proceeds, **Then** it fixes only the
   unchecked items and never re-opens an item already marked `[x]`.
3. **Given** the developer chooses a fresh analysis instead, **When** the agent proceeds, **Then** it
   states plainly that the pending items in the current file will be replaced — naming individually any
   that fall outside the new run's scope — and replaces the file only after producing a new plan the
   developer accepts.
4. **Given** the developer declines both, **When** the agent stops, **Then** the file and the working
   tree are unchanged.

---

### User Story 5 - Re-run after everything is done (Priority: P2)

The previous run's items are all ticked. Running the command again does not silently start over: the
agent reports that the earlier analysis is complete and asks whether to analyze afresh, stating that a
new plan will replace the existing file.

**Why this priority**: it keeps the single-file invariant honest without making the developer hunt down
and delete a file by hand. Lower than P1 because a project only reaches this state after the P1 loop
has already paid off.

**Independent Test**: leave a file with every row `[x]`, run the command, and confirm the agent asks
before analyzing and replaces the file only after a new plan is accepted.

**Acceptance Scenarios**:

1. **Given** an analysis file with no unchecked items, **When** the command is run, **Then** the agent
   reports the previous run's date and completion state and asks whether to re-analyze, rather than
   analyzing immediately or overwriting silently.
2. **Given** the developer agrees and the new analysis produces candidates they accept, **When** the
   file is written, **Then** it replaces the previous file at the same path, so exactly one analysis
   file still exists.
3. **Given** the developer agrees and the new analysis finds no candidates, **When** the agent reports,
   **Then** it says so, leaves the existing completed file in place unchanged, and tells the developer
   they may delete it if they no longer need the record.
4. **Given** the developer declines, **When** the agent stops, **Then** nothing further is read,
   written, or changed.

---

### User Story 6 - Nothing to act on (Priority: P3)

The project has no tests, or has tests with nothing worth flagging. The agent says so quickly and
exits — no empty file, no invented findings, no prompt to act on nothing.

**Why this priority**: it is the smallest story, but it is the one that decides whether the agent is
trusted. An agent that manufactures a finding rather than return empty-handed cannot be believed when
it does report something.

**Independent Test**: run in a repository with no tests, and in one with a deliberately clean suite;
confirm both exit with a plain statement and no file.

**Acceptance Scenarios**:

1. **Given** a project with no recognizable test suite, **When** the command is run, **Then** the agent
   reports that none was found, names the locations and conventions it checked, writes no file, and
   stops without asking a further question.
2. **Given** suites are found but no candidate meets the bar, **When** the agent reports, **Then** it
   states the suites and coverage, reports zero candidates, writes no file, and does not offer to
   create a plan.
3. **Given** either outcome, **When** the run ends, **Then** no file has been created and no file in
   the working tree has been modified.

---

### Edge Cases

- **The analysis file exists but cannot be parsed** (hand-edited into an unrecognizable state,
  truncated, or unreadable). The agent reports what it could not read, never overwrites silently, and
  offers a fresh analysis — which would replace the file — or stopping.
- **The file mixes `[x]` and `[ ]` rows.** Treated as pending (User Story 4). Completed rows are never
  re-opened.
- **The developer deleted every row before approving.** The agent reports there is nothing to fix,
  leaves the file as the record, and edits nothing.
- **A pending row's test has been renamed, moved, or deleted since the analysis.** The agent does not
  guess and does not edit a similarly-named test. It leaves the row `[ ]` with a note that the test
  could not be located, and continues.
- **A pending row's test still exists, but the flakiness is already gone** — a teammate removed the
  sleep, or rewrote the test. Caught by the pre-edit re-check (FR-031a): the row is left `[ ]` with a
  note that the code moved on, and nothing is edited on the strength of a stale description.
- **The developer reworded a row's suggested fix.** The developer's wording is what the agent acts on;
  it does not restore its own text.
- **The developer ticked a row `[x]` themselves** after fixing it by hand. The agent honours the mark
  and skips the item.
- **A monorepo with several suites in different languages.** All discovered suites are analyzed and
  reported in one table; the file column disambiguates identically-named tests.
- **A narrowed run against a broader plan.** Someone scopes a re-run to one suite while the existing
  file still holds pending rows from elsewhere. The agent names those rows before replacing anything
  (FR-029a); it does not merge the two analyses, and it does not drop the rows silently.
- **A suite too large to analyze exhaustively in one run.** The agent analyzes what it can and states
  plainly what it did not reach. A silent partial pass presented as complete is a defect.
- **A test already annotated known-flaky, or configured with retries.** Strong corroborating evidence,
  not a reason to skip the test: the annotation is the symptom, and removing the underlying cause is
  the fix.
- **`.specify/memory/` does not exist** (the project is not a Spec Kit project, or is partially
  initialized). The agent reports what is missing and where the file would go, rather than creating the
  directory tree unannounced.
- **The same test name appears in more than one file.** The file path, not the test name, identifies a
  candidate; two rows may legitimately carry the same test name.
- **The working tree already has uncommitted changes when the fix run starts.** The agent does not
  stash, revert, or manage the developer's changes; it reports at the end which files *it* changed.

## Requirements *(mandatory)*

### Functional Requirements

**Command surface and hard limits**

- **FR-001**: The capability MUST be a single agent-agnostic command, `speckit.spectra.flaky-test-detector`,
  written in the generic command format with the generic arguments placeholder, so it runs on whatever
  coding agent the team uses.
- **FR-002**: The agent MUST accept an optional scope argument naming a path or a suite. With no
  argument it MUST consider the whole working tree. It MUST state the scope it actually analyzed.
- **FR-003**: The agent MUST NOT execute tests, run build or package commands, install dependencies, or
  access the network — at any point, for any reason, including verifying a fix it has just applied.
  This is a hard limit, not a default.
- **FR-004**: The agent MUST NOT commit, stage, push, create branches, or open pull requests. Changes
  it makes remain uncommitted in the working tree.
- **FR-005**: The agent MUST NOT modify production source code, project governance, or any file outside
  the project.

**State check — always first**

- **FR-006**: As its first action on every run, before any discovery or analysis, the agent MUST check
  for an analysis file at `.specify/memory/flaky-test-analysis.md` and branch on one of four states:
  absent, holding unchecked rows, holding no unchecked rows, or present but unparseable.
- **FR-007**: Where `.specify/memory/` does not exist, the agent MUST report what is missing and where
  the file would go, and MUST NOT create the directory tree unannounced.
- **FR-008**: The agent MUST maintain at most **one** analysis file, at that single canonical path. It
  MUST NOT create a second file, a dated variant, or append a second analysis to an existing one.

**Test-suite discovery**

- **FR-009**: The agent MUST identify the project's test suite(s) by reading the working tree only —
  configuration files, directory conventions, and test file naming — and MUST handle multiple suites
  and multiple frameworks in one project.
- **FR-010**: Before reporting any candidate, the agent MUST report each suite it found: its root, the
  framework it uses, and how many test files were examined.
- **FR-011**: Where no test suite is found, the agent MUST report that plainly, name the locations and
  conventions it checked, write nothing, and exit without a further prompt.

**Detection and rating**

- **FR-012**: The agent MUST analyze discovered test code for flakiness signals across at least these
  categories: timing and async (hardcoded sleeps, missing or implicit waits, un-awaited asynchronous
  calls); test isolation and shared mutable state (order dependence, unreset globals or module state,
  unclean fixtures); unmocked external dependencies (live network, filesystem, database, or third-party
  calls); non-determinism (unseeded randomness, real clock or timezone dependence, generated
  identifiers, unordered collection iteration, floating-point equality without tolerance); brittle
  assertions (exact-match snapshots, whole-rendered-output comparison, over-specified expectations);
  parallel-execution conflicts (fixed ports, fixed temporary paths, shared records between tests);
  environment coupling (environment variables, absolute paths, working-directory assumptions); and
  pre-existing retry or known-flaky annotations.
- **FR-013**: Every candidate MUST carry a stable identifier, the test name, a project-relative file
  path with a line reference where determinable, a confidence rating, a suggested fix stated concretely
  in one or two sentences, and the evidence that triggered it.
- **FR-014**: Candidate identifiers MUST be assigned as `FT-` followed by a zero-padded three-digit
  sequence starting at `001`, unique within the analysis file, and MUST NOT be reused or renumbered
  once the file is written.
- **FR-015**: Confidence MUST be exactly one of High, Medium, or Low, assigned by this rubric:
  - **High** — a recognized flakiness pattern is present in the test's own body or its direct fixtures,
    the triggering construct can be cited by file and line, and intermittent failure follows from it
    without further assumption.
  - **Medium** — the pattern is present, but whether it actually produces intermittent failure depends
    on context the agent cannot confirm without running the suite (for example, whether a shared
    resource is genuinely contended, or whether a stubbed boundary is reached in this test).
  - **Low** — the signal is indirect or inferred from surrounding convention rather than from the test
    itself, and a reasonable reviewer could conclude the test is stable.

  The agent MUST NOT rate a candidate High without direct supporting evidence in the test source.
- **FR-016**: Candidates MUST be ordered by confidence — High, then Medium, then Low — and by file path
  within each band, in both the chat table and the analysis file, so the weakest rows sit at the bottom
  where they are cheapest to prune.
- **FR-017**: Every reported test name, file path, and cited evidence location MUST exist in the
  working tree as reported. The agent MUST NOT report a candidate in a file it did not read.
- **FR-018**: Where no candidate meets the bar, the agent MUST report zero findings plainly, and MUST
  NOT lower its bar to produce a non-empty list.

**Reporting and the first gate**

- **FR-019**: The agent MUST present the candidates as a table in chat — identifier, test name, file,
  confidence, suggested fix — **before** writing any file.
- **FR-020**: Every run MUST state its coverage and limits: which suites and how many files it
  examined, and anything it skipped, could not parse, or did not reach. A partial analysis presented as
  complete is a defect, not a degradation.
- **FR-021**: After the table and the coverage statement, the agent MUST ask for explicit consent
  before creating or replacing the analysis file, and MUST state that this step produces a plan, not a
  code change.
- **FR-022**: Declining at this gate MUST leave any existing analysis file byte-for-byte unchanged and
  the working tree untouched, and the agent MUST say that nothing was written.

**The analysis file**

- **FR-023**: On consent, the file MUST open with a summary carrying at minimum: the generation
  timestamp including time zone, the scope analyzed, the suites analyzed with their frameworks, the
  number of tests examined, the candidate count broken down by confidence, and the fixed-vs-total
  progress count.
- **FR-024**: The file MUST render each candidate as a task row whose first column is a literal `[ ]`,
  carrying the same identifier, test name, file, confidence, and suggested fix presented in chat.
- **FR-025**: The file MUST record, per candidate, the specific signal and location that triggered it,
  so a later session can act on a row without re-running the analysis.
- **FR-026**: The file MUST list what the run did not analyze — files skipped, unparseable, or not
  reached — so the record carries the same limits the chat report stated.
- **FR-026a**: The file MUST carry an outcomes section keyed by candidate identifier. Every row the
  agent attempted and left `[ ]` MUST have an entry there stating why, and every row whose fix reached
  beyond its own test MUST have one stating what else it touched (FR-032a). Entries MUST persist across
  sessions so a returning reader can tell a row that was deliberately skipped from one that was never
  reached. The task table's columns MUST remain exactly those presented in chat; outcome text MUST NOT
  be added to a table row.
- **FR-027**: The file MUST carry a line telling the developer that deleting a row excludes that test
  from the fix run, and that `[ ]` means outstanding while `[x]` means the agent applied the fix.
- **FR-028**: After writing, the agent MUST report the file path, state that it is waiting on the
  developer's review, and state explicitly that rows may be deleted.
- **FR-029**: Writing a newly accepted plan MUST replace any previous file wholesale at the same path.
  The agent MUST NOT delete the analysis file by any other means.
- **FR-029a**: Where the plan about to be written covers a narrower scope than the file it would
  replace, the agent MUST, before writing, name the pending rows that fall outside the new scope and
  obtain an explicit answer. It MUST NOT merge rows from two analyses into one file: a file carries one
  timestamp, one scope, and one set of candidates.

**The second gate and remediation**

- **FR-030**: The agent MUST obtain a second explicit approval, after the developer's review, before
  editing any file in the project.
- **FR-031**: At that approval the agent MUST re-read the analysis file from disk and act only on the
  unchecked rows present at that moment. Rows the developer deleted MUST NOT be opened or modified.
- **FR-031a**: Before editing the test named by a row, the agent MUST re-read that test and confirm
  the evidence recorded for the row is still present. Where the evidence is absent or materially
  changed — because the test was rewritten, or the cause was already fixed — the agent MUST leave the
  row `[ ]` with a note in the outcomes section (FR-026a) that the code has moved on since the
  analysis, MUST NOT apply the recorded fix,
  and MUST continue to the next row. Re-confirmation is a read, not a re-analysis: the agent MUST NOT
  derive a new fix for that row inside a fix run.
- **FR-032**: The agent MUST work the unchecked rows in file order, and MUST confine every edit to test
  code and test-support files — fixtures, helpers, factories, mocks, and test configuration. Creating a
  new test-support file is permitted where the fix requires one; creating or editing production source
  is not, and adding a dependency is forbidden by FR-003 regardless.
- **FR-032a**: Where a fix changes anything whose effect reaches tests beyond the row being fixed —
  shared test configuration, a global setup or teardown, a fixture other tests consume — the agent MUST
  say so explicitly in the run report and record it against that row in the outcomes section, naming
  what it changed and what else depends on it. A change with suite-wide reach MUST NOT be reported as
  an ordinary single-row fix.
- **FR-033**: A fix MUST remove the cause of the flakiness. The agent MUST NOT deliver as a fix:
  deleting an assertion; loosening an assertion so that it passes regardless of behaviour; skipping a
  test or marking it expected-to-fail; adding a retry wrapper or retry configuration; or lengthening a
  sleep.
- **FR-033a**: Where the project the command is run from carries a constitution at
  `.specify/memory/constitution.md`, the agent MUST read it and every fix — both the one it suggests at
  analysis time and the one it applies — MUST conform to its guardrails. Where a guardrail rules out
  the only available remedy, the agent MUST leave the row `[ ]`, name the rule as the reason in the
  outcomes section, and continue. Where the project declares no constitution, the agent MUST proceed on
  technical merit and state that no project guardrails were found. The constitution read is always the
  consumer project's, never Spectra's own.
- **FR-034**: Immediately after applying a row's fix — before starting the next row — the agent MUST
  mark that row `[x]` and update the progress count on disk. Progress MUST NOT be batched to the end of
  the run.
- **FR-035**: Any item the agent cannot fix confidently MUST be left `[ ]`, with a short reason written
  to the outcomes section (FR-026a), and the run MUST continue to the next item. This includes an item
  whose genuine remedy lies in production source — for which the agent MUST record what would need to
  change and where — and an item whose test can no longer be located, for which the agent MUST NOT edit
  a similarly-named test.
- **FR-036**: Where no unchecked row survives the developer's review, the agent MUST report that there
  is nothing to fix, leave the file as the record, and edit nothing.
- **FR-037**: On completing a fix run the agent MUST report how many items were fixed, how many were
  left open and why, which files it changed — naming any file it created and any change with reach
  beyond a single row (FR-032a) — and that the changes are uncommitted and awaiting review.

**Resumption and lifecycle**

- **FR-038**: Where the analysis file holds unchecked rows, the agent MUST report its generation date,
  its scope, and its done/pending counts, then offer three choices: continue with the pending items,
  discard and re-analyze, or stop. It MUST NOT analyze unless the developer asks for it. Where the
  developer chooses to re-analyze under a narrower scope, FR-029a governs what must be disclosed before
  the file is replaced.
- **FR-039**: Where the analysis file holds no unchecked rows, the agent MUST report that the previous
  analysis is complete, and MUST ask whether to re-analyze rather than analyzing immediately or
  overwriting silently.
- **FR-040**: Where the analysis file exists but cannot be parsed, the agent MUST report what it could
  not read, MUST NOT overwrite it silently, and MUST offer a fresh analysis or stopping.
- **FR-041**: A re-analysis that produces no candidates MUST leave any existing file unchanged, say so,
  and tell the developer they may delete it if they no longer need the record.
- **FR-042**: The agent MUST honour developer edits to the file — deleted rows, reworded suggested
  fixes, and manually ticked items — over its own previously generated content, and MUST NOT restore or
  renumber what the developer changed.

**Shipping**

- **FR-043**: Shipping the agent MUST include registering the command in the extension manifest,
  moving its roster entry to available with its command recorded, regenerating the structured agent
  listings, and updating the catalog, changelog, and distributed package in the same change, so no
  published surface disagrees about what Spectra offers.

### Key Entities

- **Test suite**: One discovered body of tests — its root path, its framework, and the test files
  within it. A project may have several, in different languages.
- **Candidate**: One test the agent believes is likely flaky. Carries an identifier, test name, file
  path with line where determinable, confidence, suggested fix, and evidence. A candidate without
  evidence at a verifiable location cannot exist.
- **Confidence rating**: High, Medium, or Low — the strength of the evidence in the source, assigned by
  the FR-015 rubric. Not a measured failure rate; without run history there is no frequency
  denominator.
- **Evidence entry**: The specific construct and location that triggered a candidate — the sleep, the
  shared fixture, the live call, the unseeded generator. What lets a later session, or a human, judge
  the row without re-running the analysis.
- **Analysis file**: `.specify/memory/flaky-test-analysis.md` — the single durable record: run summary,
  task table, evidence, and what was not analyzed. The agent's only durable output and its entire
  cross-session memory.
- **Task row**: One line of the task table, beginning `[ ]` (outstanding) or `[x]` (fixed). The unit the
  developer prunes and the agent works.
- **Progress count**: Fixed-versus-total, updated on disk after every applied fix, so an interrupted run
  is readable from the file alone.
- **Coverage-and-limits statement**: What the run examined and what it did not — suites, file counts,
  skipped and unparseable files, anything unreached. Prevents a partial pass from implying completeness.
- **Project guardrails**: The constitution of the project the command is run from, when it has one.
  Binding on fix selection: a remedy a guardrail forbids is not applied, and the rule is named instead.
- **Outcome entry**: One line in the outcomes section, keyed by candidate identifier, saying either why
  a row the agent attempted is still open, or what a fix touched beyond its own test. Distinguishes a
  deliberate skip from work not yet reached, and survives the session that wrote it.
- **Fix outcome**: What happened to a row — applied and ticked, or left outstanding with a recorded
  reason. There is no third state; an unfixed row stays `[ ]`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer obtains a ranked list of likely-flaky tests from **one command run**, in a
  project with zero prior configuration, zero pipeline integration, and no historical run data.
- **SC-002**: 100% of reported candidates are traceable — test name, file path, and cited evidence all
  present in the working tree as reported. Zero fabricated rows.
- **SC-003**: 100% of file writes and code edits are preceded by the corresponding explicit approval.
  Zero analysis files created or replaced, and zero source files edited, without one.
- **SC-004**: Across all applied fixes, zero assertions are deleted or loosened so that they always
  pass, zero tests are skipped or marked expected-to-fail, zero retry wrappers are added, and zero
  sleeps are lengthened as a remedy — verifiable from the diff alone.
- **SC-005**: 100% of files changed during a fix run are test or test-support files. Zero production
  source edits.
- **SC-006**: After a session ends mid-run, a later run resumes with 100% of completed items still
  marked done and 100% of pending items still pending, with no re-analysis.
- **SC-007**: 100% of rows deleted by the developer before approval result in no modification to those
  tests.
- **SC-008**: At least 80% of High-confidence candidates are judged genuinely flaky, or genuinely at
  risk of intermittent failure, by the reviewing engineer in pilot review.
- **SC-009**: At least 75% of applied fixes are accepted by the reviewing engineer without rework in
  pilot sampling.
- **SC-010**: Exactly one analysis file exists at every point in the lifecycle — create, resume,
  complete, re-run. Never two, and never zero while work is pending.
- **SC-011**: 100% of runs state their coverage and limits, including anything skipped, unparseable, or
  unreached.
- **SC-012**: A developer can review and prune a generated task list of typical size in under 10
  minutes, because every row is atomic, evidenced, and carries a stated fix.

## Assumptions

- The project uses Spec Kit, so `.specify/memory/` exists — the directory that already holds the
  constitution and `domain-analysis.md`. Where it does not, FR-007 governs. A constitution inside it is
  treated as optional: many projects install Spec Kit before ratifying one, and FR-033a covers its
  absence.
- The analysis file is a working artifact rather than a published deliverable, which is what places it
  under `.specify/memory/` instead of the artifact root. This is the same reading that puts
  `domain-analysis.md` there, and the plan's Constitution Check must confirm it against Principle VII.
- Static analysis of test source is sufficient to identify the dominant classes of flakiness. The
  established causes — sleeps, un-awaited async, shared state, live dependencies, unseeded randomness,
  real clocks, exact-match assertions — are visible in the code without a single test run.
- A stable per-row identifier is worth carrying even though the BRD's requested columns did not include
  one: it is what makes pruning, resumption, and reporting unambiguous across sessions.
- Recording per-candidate evidence is elevated here to a MUST (FR-025) from the BRD's SHOULD (BR-31),
  because User Story 4 requires a later session to act on a row without re-running the analysis, and
  without recorded evidence that session would have nothing to act on but a one-line summary.
- Markdown `[ ]` / `[x]` is an acceptable state marker: literal text in a table cell, editable by both
  the agent and the developer, not an interactive control.
- Common frameworks are recognizable from configuration and naming conventions. The agent is not
  restricted to a fixed supported list, and an unrecognized suite is reported as unexamined rather than
  silently ignored.
- The developer, or their continuous-integration system, verifies the fixes by running the suite. The
  agent never does.
- Fixes are reviewed as an ordinary change, left uncommitted so the working-tree diff is the review
  surface.

## Constraints

- **Agent-agnostic command (Principle III).** One command file in the generic format with the generic
  arguments placeholder, namespaced `speckit.spectra.flaky-test-detector`, carrying front matter with a
  description and registered in the manifest. No coding-agent-specific invocation syntax.
- **Context-aware by default (Principle IV).** The agent reads real project state — the working tree,
  the consumer project's constitution where it has one, and any existing analysis file — before acting.
  Here that is the product, not a nicety.
- **Document artifacts (Principle VII).** The analysis file is context for a later run of the same
  command, not a human-facing deliverable, so it lives inside the Spec Kit locations the principle
  places outside the artifact-root rule.
- **Overridable templates (Principle VIII).** Per the Clarifications, the analysis file is not a
  deliverable and therefore ships no registered template; its structure is defined by this spec. The
  plan MUST confirm this reading rather than assume it.
- **Catalog and package in sync (Principle V).** FR-043 states the shipping obligation. It is a
  build-time constraint, not runtime behaviour.
- **Human-in-the-loop is non-negotiable.** Two explicit gates — plan, then fix — with pruning in
  between. There is no auto-apply mode and no flag that removes a gate.
- **Read-write, narrowly.** The agent's only writes are its own analysis file and test code the
  developer approved row by row.

## Dependencies

- **Input**: the working tree of the project the command is run from — test files, test configuration,
  fixtures, and helpers — and that project's constitution under `.specify/memory/`, where it has one.
- **Input and output**: `.specify/memory/flaky-test-analysis.md`, written in one run and read by the
  next. It is the entire cross-session contract.
- **Downstream, optional**: `speckit.spectra.create-pr` can open a pull request for the resulting
  changes. This agent deliberately stops at an uncommitted working tree.
- **Roster and listings**: the agent roster and the generated listings, per FR-043.

## Out of Scope

- **Running the test suite** — for detection, for reproduction, or for verifying a fix.
- **Pipeline integration, execution-history ingestion, and flakiness scoring.** No results store, no
  run-frequency score, no temporal or concurrency correlation, no reliability index. That is the
  reference QE document's telemetry system and remains a separate, later product.
- **Dashboards, trend views, and cross-run history.** The file records the latest accepted plan only.
- **Quarantine, smart retry, and skip policy.** Excluded as remedies by FR-033 and as features here.
- **Changing production source code**, even where the genuine remedy lives there.
- **Committing, branching, pushing, or opening a pull request.**
- **Installing dependencies, adding test libraries, or reaching the network.**
- **Writing new tests or improving coverage.** That belongs to the Test Coverage Analyst and Test
  Automation Analyst on the roster.
- **Guaranteeing zero false positives.** Static analysis infers risk from patterns; the confidence
  rubric and human pruning bound the cost of being wrong.
