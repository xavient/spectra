# Contract: The Analysis File

**Feature**: `018-flaky-test-detector` | **Plan**: [../plan.md](../plan.md)

`.specify/memory/flaky-test-analysis.md` is the command's only durable output and its entire memory. It
is read by the same command that wrote it, possibly weeks later, so its shape is a **parse contract**
rather than a presentation choice — which is the argument that settles Principle VIII for this feature
(R-002, R-007).

## Skeleton

```markdown
# Flaky Test Analysis

- **Generated:** 2026-08-26 14:32 -07:00
- **Scope:** whole tree
- **Suites analyzed:** web/ (Jest, 148 test files), api/ (pytest, 63 test files)
- **Tests examined:** 1,204
- **Flaky candidates:** 7 — 3 high, 3 medium, 1 low
- **Progress:** 0 of 7 fixed

Delete any row you do not want fixed. `[ ]` is outstanding; `[x]` means the agent applied the fix.

## Tasks

| Done | ID     | Test                                | File                              | Confidence | Suggested fix                                                        |
| ---- | ------ | ----------------------------------- | --------------------------------- | ---------- | -------------------------------------------------------------------- |
| [ ]  | FT-001 | applies the promo code to the total | web/src/checkout/promo.test.ts:88 | High       | Replace the 500 ms sleep with an explicit wait on the updated total. |
| [ ]  | FT-002 | returns sessions created today      | api/tests/test_sessions.py:142    | High       | Freeze the clock instead of comparing against the real current time. |
| [ ]  | FT-003 | syncs the profile avatar            | web/src/profile/avatar.test.ts:31 | Medium     | Stub the upload client; the test performs a live upload.             |

## Evidence

- **FT-001** — unconditional 500 ms wait at `web/src/checkout/promo.test.ts:84`, followed by an
  assertion on the total at line 88. The wait is unrelated to the element it guards.
- **FT-002** — `api/tests/test_sessions.py:142` compares a stored creation time against the current
  time with a same-day equality check.
- **FT-003** — `web/src/profile/avatar.test.ts:31` calls the real upload client; no stub is installed
  in this file or its fixtures.

## Outcomes

- **FT-002** — left open: the evidence at line 142 is gone; the assertion was rewritten since this plan
  was generated. Re-run the analysis to pick it up again.

## Not analyzed

- `web/src/legacy/__tests__/bundle.spec.ts` and 3 other files — could not be parsed.
- `e2e/` — no test files found under it.
```

## Required structure

| Element | Requirement |
|---|---|
| `# Flaky Test Analysis` | Title, first line |
| Header block | Labelled bullets, all six fields, immediately after the title (FR-023) |
| Instruction line | States that deleting a row excludes it, and what the markers mean (FR-027) |
| `## Tasks` | Mandatory. Holds the task table and nothing else |
| `## Evidence` | Mandatory when there is at least one row (FR-025) |
| `## Outcomes` | Present once there is anything to record; may be absent in a freshly written plan (FR-026a) |
| `## Not analyzed` | Mandatory. Carries the coverage limits the chat report stated (FR-026) |

Headings are exact and ordered as above. No other `##` heading is written.

## Header fields

| Field | Shape | Why it exists |
|---|---|---|
| `Generated` | Local time with a UTC offset | Tells a returning reader how stale the plan is |
| `Scope` | `whole tree`, a project-relative path, or a suite name | The FR-029a comparison reads this |
| `Suites analyzed` | Each with framework and test-file count | Reproduces what was reported in chat |
| `Tests examined` | Integer | |
| `Flaky candidates` | Total, then the High/Medium/Low split | |
| `Progress` | `N of M fixed` | Rewritten after every applied fix (FR-034) |

## Task table

Columns, in this order, and no others: `Done`, `ID`, `Test`, `File`, `Confidence`, `Suggested fix`.

| Column | Rules |
|---|---|
| `Done` | Literal `[ ]` or `[x]`. Not a rendered control — plain text both parties edit |
| `ID` | `FT-` plus three digits from `001`, unique in the file, never reused or renumbered (FR-014) |
| `Test` | The test name as written in the source |
| `File` | Project-relative, with `:line` where determinable |
| `Confidence` | Exactly `High`, `Medium`, or `Low` |
| `Suggested fix` | One or two sentences. The developer may reword it, and their wording wins (FR-042) |

Rows are ordered by confidence — High, Medium, Low — then by file path (FR-016).

**Outcome text never appears in a table row** (FR-026a). The table stays the width it is in chat.

## Evidence and outcome entries

Both are ID-keyed bullets: `- **FT-NNN** — <text>`.

- **Evidence** records the construct and its location. It must resolve in the working tree when written,
  and it is what the pre-edit re-check compares against (FR-031a).
- **Outcomes** records either why an attempted row is still open, or what an applied fix touched beyond
  its own test (FR-032a). Entries persist across sessions.

An outcome entry for an ID with no matching row is stale but harmless; the command leaves it and does not
tidy the developer's file.

## Parse rules

**Parseable** requires all of:

1. the title line;
2. a header block from which `Generated`, `Scope`, and `Progress` can be read;
3. a `## Tasks` heading;
4. a table under it whose every row yields a state marker and an `FT-NNN` identifier.

**Unparseable** — triggering FR-040, never a silent overwrite — is any of: a missing title or header
block; a missing `## Tasks`; a table whose rows cannot be resolved to a marker and an identifier;
duplicate identifiers; or a file that cannot be read at all.

**Not unparseable**, because these are the edits developers actually make and FR-042 requires honouring
them:

| Developer edit | Treatment |
|---|---|
| Deleted a row | That test is excluded. It is never opened |
| Reworded a suggested fix | Their wording is what the agent acts on |
| Ticked `[x]` by hand | Honoured; the row is skipped |
| Un-ticked an `[x]` | Treated as pending, and worked like any other pending row |
| Reordered rows | Honoured; rows are worked in file order |
| Added a comment or a note of their own | Preserved. Left alone |
| Edited a header count so it disagrees with the rows | The rows win. The count is corrected on the next write |

## Lifecycle rules

- **At most one file exists**, at this path, at all times (FR-008, SC-010).
- **Created only at Gate 1**, on explicit consent (FR-021).
- **Replaced only wholesale**, by a newly accepted plan (FR-029). Never appended to.
- **Never deleted** by any other route. A run that finds nothing leaves an existing file untouched and
  says so (FR-041).
- **Rewritten during a fix run** only to update a row's marker, the progress count, and the outcomes
  section — never to renumber, reorder, or restore anything the developer changed.
