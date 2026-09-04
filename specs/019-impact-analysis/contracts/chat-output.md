# Contract — What the User Sees

The session is half the product: the BA answers questions in it, and the honesty rules have to hold there too.
These are shapes, not scripts — the wording is the command's to choose, the structure is not.

## Pre-flight

### Supersede detection — only when a candidate exists

A candidate is a prior analysis whose slug matches, or whose entity set overlaps the current one by at least
half of the smaller set. Several candidates → propose the most recent that is not already superseded (FR-011).

```text
Found a prior analysis: 001-cart-abandonment (approved, 2026-04-11).
This run will be recorded as superseding it. Continue? [Y/n]
```

Declined → neither document records anything (FR-011). Non-interactive → not asked; the new document records
`supersedes` and the prior file is untouched, stated in the report (FR-065).

### Scope

```text
Is this repository the only one this system depends on?

  1. Yes — just this repository
  2. No — there are other systems

  Recommended: 2 if you are unsure. Under-declaring scope is the most
  common cause of a missed impact.

Answer with a number:
```

### Per declared system

```text
Tell me about the next system. Name and owning team is enough.

  1. Describe it in a sentence
  2. Point me at a document
  3. Point me at a local copy of its source (a directory on this machine)

  Recommended: 3 when a checkout exists — it is the only form I can search.
  I never fetch anything: no URLs, no credentials, no cloning.

Answer with a number:
```

A URL offered here is explained away, not fetched, and the system is recorded as described (FR-014).

**None of the above counts against the five clarifying questions** (FR-016).

## Progress

The scan is the long part. What it says while working is not fixed, but two things are required:

- **When a cap binds**, say which and what it cut, at the moment it happens (FR-045).
- **When project-wide search is unavailable**, say so before the sweeps rather than after (FR-027).

## Clarifying questions

One at a time. Each waits (FR-031).

```text
Question 2 of 4

Should this apply to accounts created before launch?

  1. New accounts only
  2. All accounts, backfilled at launch
  3. All accounts, populated lazily on next access
  4. Other (describe in a sentence)

  Recommended: 1. The scan found no backfill tooling in this repository,
  and option 2 would need a migration over the ~2.4M rows in `accounts`
  (db/migrations/0042_accounts.sql:12).

Answer with a number, or press enter to accept the recommendation:
```

Required of every question (FR-032, FR-033):

- 3 or 4 substantive options, then `Other` accepting a free-text sentence.
- A recommendation **with its reasoning**, grounded in a scan finding wherever one exists.
- Enter accepts the recommendation, and the answer is recorded as `defaulted — not confirmed`. Never blocks.

Never asked: anything the repository answers (FR-010). Never padded to five (FR-029).

## Non-interactive announcement

When the switch was passed, or when an answer cannot be obtained and it was not (FR-062a):

```text
No interactive session detected — running as if --non-interactive were passed.
Every question will take its recommendation and be recorded as unconfirmed.
Pass --non-interactive to make this explicit.
```

One line, before anything else. Never silent, and never a wait on input that cannot arrive.

## Run report

After the write. Required content:

| Item | Requirement |
|---|---|
| Document path and id | FR-049, FR-050 |
| Resolved template path | FR-059 |
| Impact rating and the trigger that fired | FR-047 |
| Coverage per system: files read of files present, selection method, scan mode | FR-044, FR-010b |
| Caps reached and what they cut | FR-045 |
| Questions asked and how many were defaulted | FR-052 |
| Whether a prior analysis was superseded, or left untouched and why | FR-011, FR-065 |
| The override path, mentioned once, for a team that wants to reshape the document | Principle VIII |

```text
✓ Wrote docs/impact-analysis/003-cart-abandonment-recovery.md (impact: high — external contract change)
  Template: .specify/extensions/spectra/templates/impact-analysis-template.md
  Scanned: checkout-api 62/1400 files (term match + 2-hop), spec-informed
           notifications-svc 14/380 files (consumer detection only)
  Declared, not scanned: billing-service (Payments team) — no local copy
  Caps: identifier sweep stopped at 50 of 63 — 13 config keys unswept
  Questions: 4 asked, 1 defaulted
  Superseded 001-cart-abandonment
  Status is draft. Take it to your stakeholders; record their answer in the front matter yourself.
```

## What the session must never contain

| Never | Requirement |
|---|---|
| A secret value, whole or fragment | FR-042a |
| A claim that there is no impact | FR-041 |
| A compliance verdict or certification claim | FR-038 |
| Prose about a lens the repository cannot evidence | FR-040 |
| A silent truncation | FR-045 |
