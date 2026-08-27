# Phase 0 Research: Flaky Test Detector

**Feature**: `018-flaky-test-detector` | **Date**: 2026-08-26 | **Plan**: [plan.md](./plan.md)

The spec left no `[NEEDS CLARIFICATION]` markers — the BRD's eight open questions and five more from
`/speckit-clarify` were all settled before planning. So Phase 0 is not a hunt for unknowns. It records
the twelve decisions that turn those settled requirements into a command someone can write, each with
the alternative it beat and why.

Numbered `R-NNN` so tasks and the command file can cite them.

---

## R-001 — The analysis file lives at `.specify/memory/flaky-test-analysis.md`

**Decision.** One file, that exact path, created only on consent and replaced only by a newly accepted
plan.

**Rationale.** Principle VII places `.specify/` outside the artifact-root rule for writes that are
*context for another command* rather than deliverables, and names `domain-analyzer`'s
`.specify/memory/domain-analysis.md` as the example. This file is the same shape of thing, with one
difference that strengthens the case rather than weakening it: the consuming command is *this same
command's next run*. `memory/` specifically, not `.specify/` root, because that is where the existing
precedent sits and because `.specify/` root holds Spec Kit's own machinery (`scripts/`, `templates/`,
`extensions/`, `init-options.json`) rather than project state.

**Alternatives considered.**

| Option | Rejected because |
|---|---|
| `<artifact-root>/flaky-test-analysis/NNN-*.md` | Principle VII's sequence-numbered deliverables are append-only by design; this file is replaced wholesale and must be unique. A `002-` beside a `001-` would break the single-file invariant the spec's whole lifecycle rests on (FR-008, SC-010). It would also default into `docs/`, which for some projects is a published web root — a list of a team's flaky tests is not something to publish by accident. |
| `.specify/flaky-test-analysis.md` (root) | Diverges from the one precedent for no gain. |
| `.flaky-tests.json` or similar at the project root | A new top-level file per agent is exactly what Principle VII exists to prevent, and a machine format would defeat the review gate — the developer prunes this file by hand. |

---

## R-002 — No registered template, and the argument written down

**Decision.** Ship no `spectra/templates/flaky-test-analysis-template.md` and add no `provides.templates`
entry. The structure lives in the command file and is pinned by
[contracts/analysis-file.md](./contracts/analysis-file.md).

**Rationale.** Principle VIII shapes **deliverables**; R-001 establishes this file is context. The 1.7.1
clarification widened "deliverable" to reach emitted documents (a PR body, a review comment) — documents
a human reads *as the product of the run* — not to reach working state a command reads back.
`domain-analysis.md` has shipped without a template since the extension's first document agent, and
nothing distinguishes this file from it.

The load-bearing half of the argument is the one that is easy to miss: **this file's structure is a
parsing contract** (R-007). Principle VIII's honour-don't-repair rule would require the command to accept
an override as authored — so an override that renamed `## Tasks`, dropped `## Outcomes`, or reordered the
table columns would not restyle the output, it would make the file unreadable to the run that has to
resume from it, and the command would be constitutionally required to comply. Templates are right for
documents whose shape is taste. They are wrong for a file two runs have to agree on.

**Alternatives considered.** Ship the template anyway "for consistency" — rejected for the hazard above.
Ship it with a note saying some sections are mandatory — rejected because a template with immovable parts
is not an override, it is a trap that looks like one. If the team later wants the shape configurable, the
change is additive and none of this design blocks it.

---

## R-003 — Suite discovery is prose, not a script

**Decision.** The command states a discovery order in prose and the agent executes it by reading files:
(1) test-runner configuration, (2) declared test scripts or targets in project manifests, (3) directory
conventions, (4) filename patterns. Whatever matched is reported with its root, framework, and file
count (FR-010).

**Rationale.** Principle III forbids depending on a shell flavour, and the published package promises
Markdown only — no scripts, no binaries, no post-install hooks. A detection script would break both, and
would also freeze the supported framework list into code, which is precisely the wrong direction for a
requirement that says "language- and framework-agnostic" (FR-001, FR-009). Prose degrades well: an agent
that meets an unfamiliar suite can still recognize it from convention, and FR-020 forces it to say what
it could not classify rather than silently skipping it.

**Alternatives considered.** A shipped detection script (breaks III and the Markdown-only guarantee); a
fixed list of supported frameworks in the command (turns every new framework into an extension release);
asking the developer to name their suite up front (adds a question to the common case where discovery is
obvious, and the optional scope argument already covers the case where they want to narrow it).

---

## R-004 — Confidence is a rubric over evidence, not a computed score

**Decision.** High / Medium / Low, assigned by the rubric now written into FR-015: High requires the
triggering construct in the test's own body or its direct fixtures, citable by line, with intermittent
failure following without further assumption; Medium is the same pattern where the outcome depends on
context only a run could confirm; Low is an indirect or convention-based signal.

**Rationale.** The reference QE document computes flakiness as inconsistent runs over total runs. With no
execution and no history there is no denominator, so any percentage would be invented. Naming the axis
honestly — strength of evidence, not measured failure rate — is what lets SC-008 be a meaningful
precision target and keeps the agent from implying data it does not have. Writing the rubric into the
spec rather than leaving it to the command matters because it is the one judgment the whole report rests
on; the BRD required a rubric to exist but never stated one.

**Alternatives considered.** A numeric score (implies precision that does not exist); two levels
(collapses "the sleep is right there" with "this fixture might be shared", which is the distinction the
developer prunes on); five levels (finer than the evidence supports).

---

## R-005 — Both gates are plain questions in chat, and neither has a bypass

**Decision.** Gate 1 (write the plan) and Gate 2 (apply the fixes) are ordinary questions the agent asks
and waits on. No flag, argument, or configuration removes either, and declining leaves the tree
byte-identical (FR-022).

**Rationale.** Principle III rules out any agent-specific prompt UI, so the mechanism is the same one
`create-pr` and `review-pr` already use — state what will happen, ask, act only on an answer. The absence
of a bypass is a product decision, not an oversight: an unattended mode for a command that edits source
without a human reading the list first is the failure mode the two gates exist to prevent, and "the
developer can prune between the gates" is only true if there is a pause to prune in.

**Alternatives considered.** A `--yes` argument (removes the review that makes the fix run safe); a single
combined gate (there would be nothing to review, since the file is what gets reviewed); auto-writing the
file and gating only the fixes (writes to the project before anyone agreed to anything, and would break
FR-022's byte-identical guarantee for a declined run).

---

## R-006 — The file is rewritten after every applied fix

**Decision.** After each row's fix lands, the agent updates that row to `[x]` and the progress count on
disk, before starting the next row (FR-034).

**Rationale.** The cost is one small file write per fixed item; the benefit is that an interrupted
session — closed terminal, exhausted context, a developer who changes their mind — leaves a file that is
exactly true. A batch write at the end has a window in which several fixes exist in the working tree and
none is recorded, and a resumed run would then re-open items already fixed, which is both wasted work and
a second edit to a test that no longer needs one. For a command whose entire memory is this file,
"the file is stale for the duration of the run" is not an acceptable default.

**Alternatives considered.** Batch at the end (the window above); write every N items (same failure, less
often, and N is arbitrary); rely on the developer to re-run analysis after an interruption (throws away
their pruning, which User Story 4 exists to protect).

---

## R-007 — The file is a parse contract, and "unparseable" is defined

**Decision.** Fixed heading names (`## Tasks`, `## Evidence`, `## Outcomes`, `## Not analyzed`), a fixed
header block of labelled fields, a fixed task-table column order, and `FT-NNN` identifiers. A file is
**unparseable** when the header block or `## Tasks` is missing or unreadable, or when the task table's
rows cannot be resolved to a state marker and an identifier. Anything else — a reworded fix, a deleted
row, a hand-ticked box, an added comment — is a legitimate developer edit and must be honoured (FR-042).
The full contract is [contracts/analysis-file.md](./contracts/analysis-file.md).

**Rationale.** FR-006 makes the first act of every run a state check with four branches, and FR-040 says
an unparseable file must never be overwritten silently. Both require a definition of parseable that a
prompt can apply consistently — otherwise "unparseable" means whatever the agent felt about the file that
day, and the difference between "I could not read this" and "I will replace this" is the difference
between a preserved afternoon of triage and a lost one. Drawing the line at *structure* rather than
*content* is what makes developer editing safe: the two things they actually do — delete rows, reword
fixes — are explicitly on the legitimate side.

**Alternatives considered.** A machine format with a Markdown view (two artifacts to keep in sync, and the
developer prunes the Markdown one); YAML front matter for the header (a second syntax to parse for no
gain over labelled bullets); tolerate any structure and infer (the failure mode above).

---

## R-008 — Scope is recorded in the file and compared before replacement

**Decision.** The header records the scope the run analyzed. Before writing a plan whose scope is
narrower than the file it would replace, the agent names the pending rows falling outside the new scope
and waits for an explicit answer (FR-029a). Rows from two analyses are never merged into one file.

**Rationale.** The optional scope argument (FR-002) and whole-file replacement (FR-029) are individually
reasonable and jointly a data-loss path: running on `api/` after triaging `web/` would discard the `web/`
backlog with no mention. Recording the scope is what makes the comparison possible at all — without it
the agent cannot tell a narrower run from a re-run. Disclosure rather than prevention keeps one simple
rule for the file and puts the choice where it belongs.

**Alternatives considered.** Merge the two analyses (one file, two timestamps, two coverage statements —
the header stops being true); refuse the narrower run (blocks a legitimate workflow to prevent a mistake
the developer can be shown instead); one file per scope (breaks the single-file invariant and reintroduces
"which file is current?").

---

## R-009 — The constitution read is the consumer project's, and it binds

**Decision.** Where the project the command runs in has `.specify/memory/constitution.md`, the agent reads
it and every suggested and applied fix must conform. A guardrail that rules out the only remedy leaves the
row open with the rule named. Where there is none, the agent proceeds on technical merit and says so
(FR-033a).

**Rationale.** Principle IV makes reading real project state the product; reading a constitution and then
letting it change nothing is not context-awareness. The practical stake is concrete: "no new test
dependencies", "no network in tests", "prefer fakes over mocks" all directly decide whether the obvious
remedy is acceptable, and a fix that violates a team's own guardrail gets reverted in review — after
which nothing this agent says is trusted. Naming the blocking rule instead of applying the fix reuses the
pattern already established for a remedy that belongs in production code (FR-035): leave it open, say
why, keep going.

The "whose constitution" half is not pedantry. Spectra's own constitution governs how Spectra is built;
grading a user's tests against it would be a genuine defect, and the command must say `.specify/memory/`
of the project it is invoked in, never its own.

**Alternatives considered.** Advisory only — apply and note the tension (produces diffs teams reject);
ignore it (contradicts IV); read it only for test conventions (arbitrary half-measure that still requires
reading the whole file).

---

## R-010 — Extension 1.10.0 → 1.11.0, and the surface that moves with it

**Decision.** MINOR bump on the catalog channel only. `spectra/extension.yml` version and
`provides.commands` gain the command; `catalog.json` version → 1.11.0 and `provides.commands` 5 → 6, with
`updated_at` refreshed; `spectra/CHANGELOG.md` gains a `[1.11.0]` entry; `agents-list.json` flips
`flaky-test-detector` from planned to available and records its command; the generated regions in
`README.md`, `AGENTS_LIST.md`, and `spectra/README.md` are regenerated; a hand-authored prose block is
added under `<!-- SPECTRA:AGENT id=flaky-test-detector -->`; `docs/index.html` gains the command; and
`docs/packages/spectra.zip` is rebuilt. The CLI channel does not move: `VERSION` is untouched, no tag,
no Release.

**Rationale.** Principle V lists the obligation and CI enforces most of it — `.github/workflows/ci.yml`
fails on a version or command-count mismatch between manifest and catalog, on a drifted zip, and on
`generate_agent_docs.py --check` finding a stale region, a shipped agent with no prose block, or a
roster/manifest disagreement about the shipped set. MINOR rather than MAJOR because nothing is renamed or
removed; Principle VI forbids mirroring the bump onto the CLI, which changes for its own reasons.

**The one item automation cannot do**: the prose block. `--check` asserts only that a shipped agent has
one, never what it says. A shipped agent with no block fails CI, so this cannot be forgotten — but it also
cannot be generated, and it is the paragraph a reader meets first.

---

## R-011 — No hook registration

**Decision.** Register no `before_*` or `after_*` hook in `spectra/extension.yml`.

**Rationale.** `create-pr` earns its optional `after_implement` hook because opening a pull request is
genuinely the next step after implementing a feature. Flaky-test remediation is not a step in any
command's flow — it is work a team chooses to do, on their own schedule, usually when a suite has become
untrustworthy. An offer appended to every `implement` run would be noise in the common case, and noise
attached to a prompt is worse than absence, because it trains people to dismiss prompts.

**Alternatives considered.** An optional `after_implement` hook (noise, above); a `before_implement` hook
(worse — it would interrupt work to propose unrelated work).

---

## R-012 — Testing strategy: assert the rules on the shipped text

**Decision.** A new `tests/test_flaky_test_detector_flow.py` asserting the command file states its
non-negotiables, following the pattern of `tests/test_review_pr_flow.py` and
`tests/test_create_pr_flow.py`: the canonical file path; the no-execution rule; both gates and the
absence of a bypass; the prohibited-remedy list; the confinement of edits to test and test-support files;
per-item checkpointing; the four state branches; and that the constitution named is the consumer
project's. Plus census updates in `tests/test_roster_data.py` (14 → 15 available, 32 → 31 planned, shipped
set 5 → 6) and the manual zip-install pass in `test/README.md`.

**Rationale.** The deliverable is a prompt, so the enforceable surface is its text — the same reasoning
that governs every existing command test in this repository. These assertions cannot prove the agent
behaves correctly at run time; they prove that the rules it is supposed to follow have not been quietly
deleted, which is the regression that actually happens. Behavioural verification is the manual pass in
`test/README.md`, which is why [quickstart.md](./quickstart.md) carries a scenario per user story
including the refusal paths.

**Alternatives considered.** Simulating an agent run in unit tests (there is no agent to run; the tests
would assert against a fake); skipping tests because "it is only a prompt" (the existing suite's whole
premise is that prompt text is the artifact and drift in it is the defect).

---

## Summary of decisions

| ID | Decision | Requirement it settles |
|---|---|---|
| R-001 | `.specify/memory/flaky-test-analysis.md`, one file, replaced wholesale | FR-006, FR-008, FR-029 |
| R-002 | No registered template; structure pinned by contract | Principle VIII gate |
| R-003 | Suite discovery stated in prose, never scripted | FR-009, FR-010, Principle III |
| R-004 | Confidence is evidence strength, by rubric | FR-015, SC-008 |
| R-005 | Two plain gates, no bypass | FR-021, FR-030 |
| R-006 | Rewrite the file after each applied fix | FR-034 |
| R-007 | Fixed structure; "unparseable" defined by structure, not content | FR-040, FR-042 |
| R-008 | Scope recorded, compared, and disclosed before replacement | FR-002, FR-029a |
| R-009 | Consumer project's constitution binds fix selection | FR-033a, Principle IV |
| R-010 | Extension 1.11.0; catalog channel only | Principles V, VI |
| R-011 | No hook | — |
| R-012 | Assert the rules on the command text; verify behaviour manually | FR-043 |
