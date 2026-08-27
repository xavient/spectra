# Phase 1 Data Model: Flaky Test Detector

**Feature**: `018-flaky-test-detector` | **Date**: 2026-08-26 | **Plan**: [plan.md](./plan.md)

Nothing here is a database schema. The command holds no state between runs beyond one Markdown file, so
this document describes two things: the entities the command reasons about *within* a run, and the
state machine that file puts the *next* run into.

Field types are stated for precision, not to imply serialization. The only serialized entity is the
analysis file, whose byte-level shape is [contracts/analysis-file.md](./contracts/analysis-file.md).

## Entity overview

```text
Run
├── Scope ......................... what the run was allowed to look at
├── Test suite (1..n) ............. discovered, never executed
│   └── Test file (0..n)
├── Candidate (0..n) .............. one likely-flaky test
│   ├── Confidence rating ......... High | Medium | Low
│   ├── Evidence entry (1) ........ why it was flagged, and where
│   └── Suggested fix (1)
├── Coverage statement (1) ........ what was examined, what was not
└── Analysis file (0..1) .......... written only on consent
    ├── Header .................... timestamp, scope, suites, counts, progress
    ├── Task row (0..n) ........... a candidate plus its state marker
    ├── Evidence entry (0..n) ..... carried from the run that wrote it
    ├── Outcome entry (0..n) ...... why a row is still open, or what a fix touched
    └── Not-analyzed entry (0..n)
```

A **Candidate** exists only inside the run that found it. Once the developer consents, it becomes a
**Task row** plus an **Evidence entry**, and from then on the file is the only record — which is why
FR-025 makes evidence mandatory rather than nice to have.

---

## Run

One invocation of the command.

| Field | Type | Notes |
|---|---|---|
| `scope` | Scope | From `$ARGUMENTS`, or the whole working tree |
| `entry_state` | enum | `absent` \| `pending` \| `complete` \| `unparseable` — decided before any other work (FR-006) |
| `constitution` | Project guardrails \| none | The consumer project's, where present (FR-033a) |
| `suites` | Test suite[] | May be empty; empty ends the run (FR-011) |
| `candidates` | Candidate[] | May be empty; empty ends the run (FR-018) |
| `coverage` | Coverage statement | Always produced, never optional (FR-020) |

**Rule.** A run produces at most one write to the analysis file and only after Gate 1. A run that ends at
`absent` with no suites, or with no candidates, writes nothing at all.

## Scope

What the run was allowed to look at.

| Field | Type | Notes |
|---|---|---|
| `kind` | enum | `whole-tree` \| `path` \| `suite` |
| `value` | string | Project-relative path or suite name; empty for `whole-tree` |

**Rules.** The scope is reported in chat and recorded in the file header (FR-002, FR-023). Comparing a new
run's scope with the header's is what triggers the FR-029a disclosure; `whole-tree` is never narrower than
anything, and a `path` is narrower than another when it resolves inside it.

## Test suite

A discovered body of tests. Discovery is a read; nothing is executed (FR-003).

| Field | Type | Notes |
|---|---|---|
| `root` | path | Project-relative |
| `framework` | string | As identified from configuration or convention (R-003) |
| `test_file_count` | integer | Files examined, not files present, when the two differ |
| `identified_by` | enum | `configuration` \| `manifest-script` \| `directory-convention` \| `filename-pattern` |

**Rule.** Every suite is named in chat before any candidate is reported (FR-010). A directory that looks
like a suite but yields no test files is reported as such rather than omitted — silence reads as "nothing
there", which is a different claim.

## Candidate

One test the agent believes is likely to fail intermittently.

| Field | Type | Notes |
|---|---|---|
| `id` | `FT-NNN` | Zero-padded from `001`, unique in the file, never reused or renumbered (FR-014) |
| `test_name` | string | As written in the source |
| `file` | path | Project-relative, with a line reference where determinable |
| `confidence` | Confidence rating | Exactly High, Medium, or Low |
| `suggested_fix` | string | One or two sentences, concrete enough to act on |
| `evidence` | Evidence entry | Mandatory — a candidate without it cannot exist (FR-013) |
| `signal_category` | enum | One of the eight categories in FR-012 |

**Rules.** `test_name`, `file`, and the evidence location must all exist in the working tree as reported
(FR-017). Ordering is by confidence, then file path (FR-016), so the weakest rows sit where pruning is
cheapest. Two candidates may share a `test_name` when they are in different files; `file` is what
disambiguates.

## Confidence rating

| Value | Assigned when |
|---|---|
| High | The triggering construct is in the test's own body or its direct fixtures, citable by line, and intermittent failure follows without further assumption |
| Medium | The pattern is present, but whether it produces intermittent failure depends on context only a run could confirm |
| Low | The signal is indirect or inferred from surrounding convention, and a reasonable reviewer could call the test stable |

**Rule.** High is unavailable without direct evidence in the test source (FR-015). This is a rating of
evidence, not a measured failure rate — there is no run history and therefore no denominator (R-004).

## Evidence entry

Why a candidate was flagged, and where to look.

| Field | Type | Notes |
|---|---|---|
| `candidate_id` | `FT-NNN` | The key |
| `construct` | string | The sleep, the shared fixture, the live call, the unseeded generator |
| `location` | path + line | Must resolve in the working tree |

**Rule.** Written into the file and kept there, so a later session can act on a row without re-analyzing
(FR-025). It is also what the pre-edit re-check compares against (FR-031a): evidence gone or materially
changed means the code moved on, and the row is left open.

## Outcome entry

What happened to a row the agent worked on.

| Field | Type | Notes |
|---|---|---|
| `candidate_id` | `FT-NNN` | The key |
| `kind` | enum | `left-open` \| `reached-beyond-row` |
| `reason` | string | Why it is still open, or what else the fix touched and what depends on it |

**Rules.** Every row the agent attempted and left `[ ]` has one, and so does every applied fix whose
change reaches tests beyond its own row (FR-026a, FR-032a). Entries persist across sessions, which is what
lets a returning reader tell a deliberate skip from work never reached. Outcome text never goes in a table
row.

## Coverage statement

| Field | Type | Notes |
|---|---|---|
| `suites_examined` | Test suite[] | With file counts |
| `tests_examined` | integer | |
| `not_reached` | Not-analyzed entry[] | Skipped, unparseable, or beyond what the run could read |
| `scope_analyzed` | Scope | What was actually covered, which may be narrower than requested |

**Rule.** Produced on every run, including runs that find nothing (FR-020). A partial analysis presented
as complete is a defect, not a degradation — this entity exists so that claim has somewhere to live.

## Project guardrails

The consumer project's constitution, when it has one.

| Field | Type | Notes |
|---|---|---|
| `present` | boolean | Absence is reported, not assumed (FR-033a) |
| `source` | path | Always the invoking project's `.specify/memory/constitution.md`, never Spectra's own |

**Rule.** Binding on fix selection, both for the fix suggested at analysis time and the one applied. A
guardrail that rules out the only remedy leaves the row `[ ]` with the rule named as the reason.

## Analysis file

The single durable artifact. Byte-level shape in
[contracts/analysis-file.md](./contracts/analysis-file.md).

| Field | Type | Notes |
|---|---|---|
| `generated_at` | timestamp with zone | Identifies how stale the plan is |
| `scope` | Scope | Drives the FR-029a comparison |
| `suites` | Test suite[] | With frameworks and file counts |
| `tests_examined` | integer | |
| `candidate_counts` | by confidence | Total plus the High/Medium/Low split |
| `progress` | fixed / total | Rewritten after every applied fix (FR-034) |
| `rows` | Task row[] | |
| `evidence` | Evidence entry[] | |
| `outcomes` | Outcome entry[] | |
| `not_analyzed` | Not-analyzed entry[] | |

**Rules.** At most one exists at any time (FR-008). It is created only at Gate 1 and replaced only by a
newly accepted plan — never appended to, never deleted by any other route (FR-029). Its structure is a
parse contract, so structural edits break it in the sense of FR-040 while content edits do not (R-007).

## Task row

| Field | Type | Notes |
|---|---|---|
| `state` | `[ ]` \| `[x]` | Literal text in the first column, editable by either party |
| `id` | `FT-NNN` | |
| `test_name`, `file`, `confidence`, `suggested_fix` | as Candidate | Same values presented in chat (FR-024) |

**State transitions.**

```text
        (Gate 1: plan accepted)
                  │
                  ▼
               [ ]  ──── agent applies the fix ─────────────► [x]
                │
                ├──── agent attempts, cannot fix ──────────► [ ] + outcome entry
                ├──── evidence gone (FR-031a) ─────────────► [ ] + outcome entry
                ├──── guardrail blocks it (FR-033a) ───────► [ ] + outcome entry
                ├──── developer deletes the row ───────────► gone; test never opened
                └──── developer ticks it themselves ───────► [x] honoured, row skipped
```

`[x]` is terminal within the life of a file: a completed row is never re-opened (FR-038). The only route
back is a new accepted plan, which is a different file.

---

## Session state machine

The first act of every run. Four branches, decided before discovery or analysis (FR-006).

```text
run starts
    │
    ├─ .specify/memory/ missing ──────► report what is missing, where the file would go. Stop. (FR-007)
    │
    └─ read .specify/memory/flaky-test-analysis.md
         │
         ├─ absent ──────────────────► ANALYZE
         │
         ├─ has ≥1 unchecked row ────► report date, scope, done/pending counts.
         │                              Offer: continue │ discard and re-analyze │ stop.  (FR-038)
         │                                ├─ continue ─────────► GATE 2
         │                                ├─ re-analyze ───────► ANALYZE (FR-029a applies on write)
         │                                └─ stop ─────────────► nothing read further, nothing written
         │
         ├─ no unchecked rows ───────► report previous run complete. Ask before re-analyzing. (FR-039)
         │                                ├─ yes ──────────────► ANALYZE
         │                                └─ no ───────────────► stop
         │
         └─ unparseable ─────────────► report what could not be read. Never overwrite silently.
                                        Offer: fresh analysis │ stop.  (FR-040)

ANALYZE ─► discover suites ─┬─ none ────────► report where it looked. Write nothing. Stop. (FR-011)
                            └─ found ───────► analyze ─┬─ 0 candidates ─► report. Write nothing.
                                                       │                   Existing file left as is. (FR-041)
                                                       └─ ≥1 candidate ─► report table + coverage
                                                                          ─► GATE 1

GATE 1 ─┬─ declined ─► nothing written; any existing file byte-identical (FR-022)
        └─ accepted ─► write/replace the file ─► report path, waiting-for-review, rows may be deleted
                       ─► GATE 2

GATE 2 ─┬─ declined ─► file stands; no source edited
        └─ accepted ─► re-read file from disk (FR-031)
                       ─► for each unchecked row in file order:
                            re-check evidence (FR-031a) ─► apply or leave open
                            ─► write state to disk before the next row (FR-034)
                       ─► closing report (FR-037)
```

**Invariant across every path**: at most one analysis file exists, and no path deletes it except the one
that replaces it with a newly accepted plan (SC-010).

**Invariant on every declining path**: the working tree is unchanged. Declining is always safe, at every
gate, in every state.
