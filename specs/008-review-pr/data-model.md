# Phase 1 Data Model: Review PR

**Feature**: `008-review-pr` | **Date**: 2026-08-17 | **Plan**: [plan.md](./plan.md)

These are **in-session working structures**, not persisted records. FR-026 forbids storing findings,
rejections, or review history between runs, so every entity below lives only for the duration of one
review session. The one exception is the **Published review**, which is persisted — by GitHub, on the
pull request, under the reviewer's own identity.

---

## Entity relationship overview

```text
Review session (1)
├── Review target (1) ─── pinned to ─── Head revision (1)
├── Authorizing context (0..1)          # absent → Story 3 / FR-012
│   ├── Spec, plan, tasks   @ headRefOid
│   └── Constitution, ADRs  @ baseRefOid
├── Review budget (1) ─── produces ─── Coverage statement (1)
├── Lens (1..n) ─── each produces ──── Finding (0..n)
├── Finding (0..n) ─── carries ─────── Severity (1) + Confidence (1)
├── Selection (1) ─── subsets ──────── Finding
└── Verdict (1) ─── with Selection ─── Published review (0..1)
```

---

## Review target

The pull request under review. Populated by one `gh pr view --json` call (research R-002).

| Field | Source field | Purpose |
|---|---|---|
| `number` | `number` | Identity in the summary |
| `title` | `title` | Identity in the summary |
| `url` | `url` | Returned on publication (FR-033) |
| `author` | `author.login` | Self-review detection (FR-029) |
| `sourceBranch` | `headRefName` | Summary header (FR-021) |
| `targetBranch` | `baseRefName` | Summary header; base for guardrails (FR-009) |
| `isDraft` | `isDraft` | Draft disclosure (edge case) |
| `isFork` | `headRepositoryOwner` ≠ repo owner | Fork expectation-setting (edge case) |
| `changedFiles` | `changedFiles` | Budget evaluation (FR-013) |
| `additions`, `deletions` | `additions`, `deletions` | Budget evaluation and change size |
| `ciStatus` | `statusCheckRollup` | Summary and verdict recommendation (FR-021) |
| `commits` | `commits` | Commit series in the summary |
| `existingReviews` | `reviews`, `latestReviews` | Duplicate detection (FR-036); prior findings (FR-039) |

**Validation rules**

- The target MUST resolve before any analysis begins. An unresolvable reference stops the run.
- With no argument, the target MUST be chosen explicitly by the reviewer; the agent MUST NOT
  auto-select from a list of several (FR-004).
- If `author` equals the authenticated user, approve MUST be withheld from the offered verdicts
  (FR-029).

---

## Head revision

The single commit the review is pinned to. Its own entity because a review's validity is scoped to it.

| Field | Source | Purpose |
|---|---|---|
| `headRefOid` | `gh pr view --json headRefOid` | The pinned revision (FR-005) |
| `baseRefOid` | `gh pr view --json baseRefOid` | Revision for constitution and ADRs (FR-009) |
| `priorRevision` | reviewer-supplied, or parsed from a prior review body | Delta re-review (FR-039) |

**Validation rules**

- Captured once at the start and reported in both the summary and the published body (FR-005).
- Re-read immediately before publication. If `headRefOid` changed, the agent MUST warn and offer
  re-analysis instead of publishing (FR-032).
- Every artifact read for the authorizing context MUST be read at an explicit revision — never from the
  working tree (FR-006).

---

## Authorizing context

What the change was permitted to do, and the standards it must meet. Optional: absence is a legitimate
state that triggers Story 3, never an error.

| Field | Read at | Discovery |
|---|---|---|
| `spec`, `plan`, `tasks` | `headRefOid` | Three-tier chain (FR-006a) |
| `adrs` | `headRefOid` for the PR's own; `baseRefOid` for those in force | Path convention |
| `constitution` | `baseRefOid` | `.specify/memory/constitution.md` |
| `discoverySource` | — | Which tier resolved: `diff`, `feature-record`, or `none` |

**State: how the context was resolved**

| State | Meaning | Consequence |
|---|---|---|
| `diff` | A spec appears in the PR's own diff | Full traceability; normal spec-driven case |
| `feature-record` | Spec located via the Spec Kit feature record at the head revision | Full traceability; addendum case |
| `none` | Neither resolved | FR-012: traceability listed as **not run**, intent findings capped at Question, guardrails still at full strength |

**Validation rules**

- `discoverySource` MUST be stated in the output so coverage reflects what was actually read (FR-006a).
- Branch-name inference MUST NOT be used as a discovery tier (FR-006a).
- When `discoverySource` is `none`, the traceability lens MUST NOT be reported as passed (FR-012).
- The constitution MUST come from `baseRefOid`. A PR that modifies the constitution or an ADR MUST be
  surfaced as a governance change regardless of severity (FR-009).

---

## Review budget

The declared limit that makes coverage honest and testable.

| Field | Value | Source |
|---|---|---|
| `maxFiles` | 40 | research R-003 |
| `maxChangedLines` | 1,500 | research R-003 |
| `exceeded` | derived | `changedFiles` or `additions + deletions` over limit |
| `reviewedFiles` | derived | Files inside the budget, or the highest-risk selection |
| `excludedFiles` | derived | Generated-file exclusions plus over-budget remainder |

**Risk ranking order** (highest first), applied only when `exceeded` is true:

1. Security-relevant paths — auth, crypto, secrets, permissions
2. Data and migrations
3. Public API and contract surfaces
4. Application logic
5. Configuration and infrastructure
6. Tests
7. Documentation

**Validation rules**

- Size MUST NOT cause a refusal (FR-013).
- The budget MUST NOT be surfaced to the reviewer as a choice (FR-013, per clarification).
- When `exceeded`, the excluded remainder MUST be named with a reason (SC-013).

---

## Lens

One focused review pass, selected by what the diff touches.

| Field | Values |
|---|---|
| `name` | correctness · security · tests · data & migrations · API contract & compatibility · performance · operability · maintainability · docs · dependencies · accessibility · internationalization · traceability · guardrails |
| `state` | `run` · `not-run` |
| `reason` | Required when `not-run` |

**Validation rules**

- Selection MUST be driven by what the diff actually touches, not by running everything (FR-011).
- Every lens MUST be reported as `run` or `not-run`, and `not-run` MUST carry a reason (FR-011).
- A lens that did not run MUST NEVER be reported as passed (FR-012, SC-003).

---

## Finding

The atomic unit of review output.

| Field | Required | Purpose |
|---|---|---|
| `number` | yes | Flat sequence in presentation order, for selection by number (FR-019) |
| `class` | yes | `intent` · `guardrail` · `craft` — groups by who owns the fix (FR-018) |
| `severity` | yes | One of five levels (FR-016) |
| `confidence` | yes | `high` · `medium` · `low` (FR-017) |
| `file`, `line` | yes | The anchor (FR-015) |
| `source` | yes | Constitution/ADR clause, requirement id, or named principle (FR-015) |
| `statement` | yes | What is wrong |
| `impact` | yes | Why it matters |
| `fix` | recommended | What to do about it |
| `occurrences` | when grouped | Count plus locations for repeated instances (FR-020) |

**Validation rules — these are hard gates on existence, not formatting**

- A finding without both `file`/`line` **and** `source` MUST NOT be reported at all (FR-015). This is the
  single most important invariant in the feature: it is what separates a citation from an opinion.
- `confidence: low` MUST NOT carry `severity: blocker`; it becomes a Question instead (FR-017).
- When `class` is `intent` and the authorizing context is `none`, severity is capped at Question (FR-012).
- Repeated instances of one finding SHOULD collapse into a single entry with a count (FR-020).

### Severity (rubric per FR-016)

| Level | Label | Floor rules |
|---|---|---|
| Blocker | S1 | Explicit compliance or regulatory MUST violation is never below this |
| Major | S2 | Explicit constitution MUST violation is never below this |
| Minor | S3 | — |
| Nit | S4 | — |
| Question | Q | Destination for low-confidence findings and for intent findings with no spec |

The rubric is fixed, not project-configurable — a constitution-overridable ladder was considered and
deferred (spec Assumptions).

---

## Coverage statement

The honesty mechanism. Derived entirely from other entities; holds no independent data.

| Field | Derived from |
|---|---|
| `revisionReviewed` | Head revision `headRefOid` |
| `lensesRun`, `lensesNotRun` | Lens states and reasons |
| `filesReviewed`, `filesExcluded` | Review budget |
| `specStatus` | Authorizing context `discoverySource` |
| `evidenceUnavailable` | Free-form (e.g. no load-test evidence) |
| `overallConfidence` | Aggregate judgement |

**Validation rule**: MUST be present in every review, with no exceptions (FR-011, FR-021, SC-003).

---

## Selection

The reviewer's explicit choice of what to publish. The human filter.

| Field | Purpose |
|---|---|
| `accepted` | Finding numbers to publish |
| `dropped` | Findings deliberately withheld |
| `severityOverrides` | Optional reviewer-set severity (FR-030) |

**Accepted grammar** (FR-024): individual numbers (`3`), comma-separated lists (`1,2,4`), ranges
(`1-4`), severity groups (`blockers`, `blockers+major`), `all`, `none`, and exclusions
(`all except 10-15`).

**State transitions**

```text
presented ──(empty / none / absent)──> nothing published        [terminal, FR-023]
presented ──(valid selection)────────> confirmed  ──> verdict chosen ──> preview ──> published
presented ──(unparseable)────────────> re-prompt (does not advance)
```

**Validation rules**

- Nothing is pre-selected. An empty or absent selection publishes nothing (FR-023).
- Both `accepted` and `dropped` MUST be stated before publishing, so the transcript holds the full
  record (FR-025).
- Neither list may be persisted anywhere (FR-026).

---

## Verdict

What the reviewer submits. Recommended by the agent, always chosen by the human.

| Value | `gh` invocation |
|---|---|
| `approve` | `gh pr review <ref> --approve --body-file -` |
| `request-changes` | `gh pr review <ref> --request-changes --body-file -` |
| `comment` | `gh pr review <ref> --comment --body-file -` |

**Validation rules**

- Derived mechanically as a *recommendation* from the findings, drawn from this closed set (FR-022).
- The agent MUST NOT select it on the reviewer's behalf (FR-027).
- `approve` alongside an accepted blocker MUST state the contradiction, require a **typed** confirmation
  rather than a bare yes, and record the acknowledged blocker in the published body — and MUST NOT be
  refused outright (FR-028).
- `approve` MUST NOT be offered when the reviewer is the author (FR-029).
- The recommendation MUST NOT be `approve` while required checks are failing (spec Assumptions).

---

## Published review

The only durable artifact. Persisted by GitHub, not by the agent.

| Field | Requirement |
|---|---|
| `revisionLine` | The pinned `headRefOid`, as a stable greppable line (FR-005) |
| `disclosureLine` | AI-assisted and human-curated statement (FR-034) |
| `findings` | Accepted findings only, never the dropped ones (FR-023) |
| `acknowledgedBlockers` | Present when an approval overrode a blocker (FR-028) |
| `coverage` | Coverage and limits statement (FR-021) |
| `url` | Returned to the reviewer on success (FR-033) |

**Validation rules**

- Published as exactly one review event carrying both verdict and body (FR-033).
- The exact body MUST be previewed and a final go-ahead obtained before publication (FR-031).
- `revisionLine` and `disclosureLine` are **load-bearing**, not decorative: FR-039's prior-findings
  readback locates the agent's own earlier review by exactly these two lines (research R-008). Their
  format is fixed in [contracts/output-format.md](./contracts/output-format.md) and MUST NOT drift.
- On failure after the pre-flight gate passed, no partial review may be left behind; the rendered body
  is handed over for manual posting (FR-035).

---

## Session state machine

```text
     ┌─────────────┐  gh missing / unauthenticated
     │  pre-flight │ ─────────────────────────────> HARD STOP (FR-001)
     └──────┬──────┘
            │ gh ok
     ┌──────▼──────┐  unresolvable
     │   resolve   │ ──────────────> stop with explanation
     └──────┬──────┘
            │ target pinned at headRefOid
     ┌──────▼──────┐
     │   gather    │  metadata · name-only diff · budget · artifacts at ref
     └──────┬──────┘
     ┌──────▼──────┐
     │   analyze   │  lens selection · traceability · guardrails · craft
     └──────┬──────┘
     ┌──────▼──────┐
     │   present   │  ranked findings · tally · coverage · recommendation
     └──────┬──────┘
            │
     ┌──────▼──────┐  empty selection
     │   select    │ ──────────────> nothing published  [terminal]
     └──────┬──────┘
     ┌──────▼──────┐  blocker + approve ──> typed confirmation required
     │   verdict   │
     └──────┬──────┘
     ┌──────▼──────┐  no go-ahead
     │   preview   │ ──────────────> nothing published  [terminal]
     └──────┬──────┘
            │ go-ahead
     ┌──────▼──────┐  revision moved ──> warn, offer re-analysis  [no publish]
     │   publish   │  permission/fork failure ──> hand over rendered body (FR-035)
     └──────┬──────┘
            │ success
        return URL
```

Every terminal state that publishes nothing is a **success path**, not an error: the reviewer choosing
to post nothing is the design working as intended.
