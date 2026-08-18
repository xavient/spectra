# Contract: Output Format

**Feature**: `008-review-pr`

Three surfaces: what the reviewer reads, what the reviewer types, and what gets published. The third is
the strictest — parts of it are machine-read by a later run of this same command.

---

## Surface 1 — The chat summary

Required elements, per FR-021. Order is fixed so a reviewer learns one shape and can skim it thereafter.

| # | Element | Requirement |
|---|---|---|
| 1 | PR identity — number, title, author | FR-021 |
| 2 | Source → target branch, head revision, change size | FR-005, FR-021 |
| 3 | Spec status — path, or an explicit statement of absence, plus which discovery tier resolved | FR-006a, FR-012 |
| 4 | CI status | FR-021 |
| 5 | Draft / fork / self-review notices, when they apply | edge cases |
| 6 | **Recommended verdict** with its one-line derivation | FR-022 |
| 7 | "What this PR does (my reading)" | FR-021 |
| 8 | Severity tally, by class × severity | FR-018, FR-021 |
| 9 | Findings — numbered, grouped by severity, minors and nits collapsible | FR-016, FR-019 |
| 10 | Coverage & limits | FR-011, FR-021, SC-003 |
| 11 | Selection prompt | FR-023 |

### Finding presentation

Each finding presents in this order — anchor and source are not optional garnish, they are the
existence condition from FR-015:

```text
[<n>] <SEVERITY> · <Class> · confidence: <high|medium|low>
    <statement>
    <file>:<line>
    <source — quoted constitution/ADR clause, requirement id, or named principle>
    Impact: <why it matters>
    Fix: <what to do>
```

Grouped repeats (FR-020) add a count and locations rather than repeating the entry:

```text
[<n>] NIT · Craft · confidence: high · 4 occurrences
    Missing return type annotation
    src/limiter/index.ts:12, :34, :51, :77
```

### Severity display labels

| Level | Label |
|---|---|
| Blocker | `S1` |
| Major | `S2` |
| Minor | `S3` |
| Nit | `Nit` |
| Question | `Q` |

These labels are the display form of the FR-016 rubric and match the illustrative output in BRD-005 §6,
so the spec, the BRD, and the running command all speak the same vocabulary.

---

## Surface 2 — Selection grammar

The reviewer's input. Every form in FR-024 must parse.

| Input | Meaning |
|---|---|
| *(empty)* | Publish nothing — terminal success |
| `none` | Publish nothing — explicit form |
| `all` | Publish every finding |
| `3` | Finding 3 |
| `1,2,4` | Findings 1, 2, and 4 |
| `1-4` | Findings 1 through 4 |
| `blockers` | All blockers |
| `blockers+major` | All blockers and majors |
| `all except 10-15` | Everything but 10 through 15 |
| `1,2,5-7 except 6` | Combined forms |
| `3:major` | Accept 3, overriding its severity to major (FR-030) |

**Parsing rules**

- Nothing is pre-selected. Empty input means publish nothing — never "publish everything" (FR-023).
- An unparseable selection re-prompts and does **not** advance the flow.
- An out-of-range number is reported rather than silently ignored.
- Severity overrides apply to the published body, not retroactively to the tally the reviewer already saw.

### Mandatory confirmation after selection

Both lists, always, before any outward action (FR-025):

```text
Publishing 3 findings:  [1] S1 Security · [2] S2 Intent · [4] S2 Data
Dropping 13 findings:   [3] · [5]-[9] · [10]-[15] · [16]
Nothing is persisted — this transcript is the only record.
```

The dropped list exists so the session transcript holds the complete record, since FR-026 forbids
storing it anywhere.

---

## Surface 3 — The published review body

### Required structural lines

Two lines are **load-bearing** — a later run of this command locates and parses its own prior reviews by
them (FR-039, research R-008). Their format is fixed and MUST NOT drift.

```text
<!-- spectra:review-pr revision=<full-40-char-sha> -->
```

```text
Reviewed at revision `<short-sha>` by Spectra `review-pr` — AI-assisted, human-curated:
every finding below was individually selected by the reviewer.
```

The HTML comment is the machine anchor: invisible in rendered Markdown, unambiguous to parse, and it
carries the full SHA. The prose line satisfies FR-034's disclosure requirement for human readers. Both
are mandatory — the first makes re-review possible, the second makes the review honest.

### Body layout

```markdown
<!-- spectra:review-pr revision=4a9f2c1e8b3d5f7a9c1e3b5d7f9a1c3e5b7d9f1a -->

Reviewed at revision `4a9f2c1` by Spectra `review-pr` — AI-assisted, human-curated:
every finding below was individually selected by the reviewer.

## Blockers
[findings…]

## Major
[findings…]

## Minor / Nits
[findings…]

## Questions
[findings…]

## Coverage and limits
[which lenses ran, which did not and why, what was excluded, evidence unavailable]
```

### Acknowledged blocker override

When an approval is published over an accepted blocker, this block is **mandatory** in the body
(FR-028). It is the mechanism behind SC-009's "zero silent overrides":

```markdown
## Acknowledged blocker — approved over

The reviewer approved this pull request with the following blocker outstanding, and
explicitly acknowledged it:

- [1] S1 · Security · src/limiter/redis.ts:34 — Redis connection used without TLS
```

### What never appears in the published body

| Excluded | Requirement |
|---|---|
| Findings the reviewer dropped | FR-023 |
| The severity tally of unselected findings | FR-023 |
| Any content not shown in the preview | FR-031 |
| Any claim that a lens passed when it did not run | FR-012, SC-003 |

The coverage statement **is** published, and deliberately so: it is what stops the review from implying
assurance it did not earn.

---

## Surface 4 — The optional saved file (FR-038)

Off by default. When the reviewer opts in, the file contains the **complete** review including dropped
findings — that is its entire reason to exist, since the transcript is otherwise the only record.

- Format: Markdown, same layout as the published body plus a `## Dropped findings` section.
- Location: a reviewer-chosen path. Not the spec directory — the reviewer is typically not on the PR's
  branch (spec Assumptions).
- The agent MUST NOT write it without an explicit request.
