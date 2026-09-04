# Phase 1 — Data Model: `speckit.spectra.impact`

**Feature**: [spec.md](./spec.md) · **Plan**: [plan.md](./plan.md) · **Date**: 2026-09-03

There is no database and no persisted state beyond the documents themselves. "Data model" here means the
entities the command reasons about during a run, the schema of the one document it writes, and the one
lifecycle it deliberately does not own.

---

## 1. Entities

### FeatureIntent

The paragraph the user supplied. The only required input.

| Field | Value | Source |
|---|---|---|
| `text` | Verbatim, as typed | The invocation |
| `entities` | Domain nouns, endpoints, roles, states extracted from it | FR-020 |
| `variants` | Per entity: camelCase, snake_case, kebab-case, SCREAMING_SNAKE, singular, plural, table-naming forms, observed synonyms | FR-020 |
| `slug` | Kebab-case name derived from the text and any attachments; the filename's `<name>` and the front-matter `feature_slug` are this one value | FR-050 |

**Invariants.** `text` is recorded verbatim in the document (FR-052a) and is authoritative for what is being
asked (FR-008a). `slug` is derived per run and is **not** stable across runs (FR-053).

### Attachment

| Field | Value |
|---|---|
| `path` | As given in the invocation |
| `kind` | Feature request / brief / epic · external-system description · prior analysis |
| `format` | `.md` · `.txt` · `.pdf` · `.docx` |
| `state` | `read` · `unreadable` · `missing` · `unsupported-type` |
| `reason` | Present when `state` is not `read` |

**Invariants.** No attachment is required (FR-006). A non-`read` state never fails the run (FR-008). Every
attachment appears in the document by name with its state (FR-052a).

### DeclaredSystem

One per system the run records. The repository the command was invoked in is one of them, with `form: project`;
the rest are the other systems the user names when this repository is not the whole system.

| Field | Value |
|---|---|
| `name` | As given |
| `owner` | Owning team, optional |
| `form` | `project` (the repository the command was invoked in) · `free-text` · `document` · `local-path` |
| `path` | Present only when `form` is `local-path` |
| `scan_state` | `scanned` · `declared-not-scanned` · `not-declared` |
| `failure_reason` | `path-not-found` · `not-readable` · `contains-no-source`, when applicable |
| `coverage` | Files read / files present, when `scanned` |

**Invariants.** A `local-path` system is read in place and never written, copied, or modified (FR-015). No URL
is accepted (FR-014). A path that cannot be read degrades to `declared-not-scanned` with a distinguishing
reason and does not fail the run (FR-018). A `declared-not-scanned` system produces at least one handoff item
naming the owner and the contract to confirm (FR-013, FR-055).

**Where no other system is declared**, the document records that the user asserted single-repository scope —
the assertion a reviewer is most likely to want to challenge.

### ScanMode

| Value | Condition | Recorded as |
|---|---|---|
| `spec-informed` | The project carries specifications and/or a constitution | What was read to orient |
| `source-only` | Neither is present | Stated as the heavier path |

**Invariant.** The mode appears in the output on every run (FR-010b, SC-003).

### ContractIdentifier

Extracted from the seed set, swept as a raw string across the whole project and against each scanned local
path.

| Field | Value |
|---|---|
| `literal` | The string as it appears in source |
| `class` | `table` · `column` · `endpoint` · `event` · `topic` · `config-key` · `flag` · `env-var` |
| `tier` | `contract-bearing` (table, column, endpoint, event, topic) · `config-bearing` (config-key, flag, env-var) |
| `swept` | Whether it was reached before the identifier cap |

**Invariant.** Sweep order is `contract-bearing` before `config-bearing`; the cap is 50 by default and both the
cap and the unswept count are disclosed when reached (FR-024, research §4).

### Finding

| Field | Value |
|---|---|
| `lens` | `blast-radius` · `data` · `behavioural` · `risk-reversibility` · `effort-sequencing` · `security-privacy` · `compliance` |
| `statement` | One observation |
| `citation` | `path:line`, or — for evidenced absence — what was searched and where |
| `confidence` | `confirmed` · `probable` · `possible` |
| `verification` | Required when `possible` |

**Invariants.** Every finding carries a citation; uncited inference belongs in Assumptions (FR-042). Evidenced
absence is the one citation exception and is cited as a search (FR-042). Confidence follows the fixed mapping
in research §9, never a judgement. No finding reproduces a secret value (FR-042a).

### Clarification

| Field | Value |
|---|---|
| `n` | 1 to 5 |
| `question` | Generated from scan ambiguity, not a fixed list |
| `category` | `scope-boundary` · `data-lifecycle` · `existing-user-behaviour` · `contract-compatibility` · `reversibility` · `non-functional-threshold` |
| `options` | 3 or 4 substantive, plus `Other` accepting free text |
| `recommendation` | With its reasoning, grounded in a scan finding where one exists |
| `answer` | The user's choice, free text, or the recommendation |
| `source` | `user` · `defaulted` |

**Invariants.** At most five, fewer when fewer are ambiguous, never padded (FR-029). Nothing discoverable in
the repository is asked (FR-010). A `defaulted` answer in `scope-boundary`, `data-lifecycle`, or
`contract-compatibility` is additionally promoted into risks (FR-034).

### ImpactRating

Derived from triggers, never judged (FR-047).

| Rating | Any one of |
|---|---|
| `high` | Irreversible data change · external contract change · security-privacy lens fired · compliance lens fired · no viable rollback path identified |
| `medium` | Internal contract change · reversible migration or backfill · behaviour change visible to existing users or callers |
| `low` | All of: additive only · trivially revertible · no data change · no external contract change |

**Invariant.** The output names the trigger that produced the rating.

---

## 2. The document

One file per run at `<artifact-root>/impact-analysis/NNN-<name>.md`.

### Front matter

| Key | Type | Notes |
|---|---|---|
| `id` | `NNN` | Highest present in the folder, plus one (FR-050) |
| `feature_slug` | kebab-case | Derived per run; not stable (FR-053) |
| `title` | string | Human-readable feature name |
| `status` | enum | **Always `draft` when written** (FR-053a) |
| `impact` | `high` · `medium` · `low` | With the trigger named in the body (FR-047) |
| `generated` | timestamp | Date, time of day, and time zone (FR-052) |
| `author` | string | Local committing identity where discoverable, else empty — never invented |
| `supersedes` | `NNN` or null | Set on confirmed detection (FR-011) |
| `superseded_by` | `NNN` or null | Written into the prior document, on confirmation only |
| `scan_mode` | `spec-informed` · `source-only` | FR-010b |
| `systems_scanned[]` | name, form, path, coverage | FR-017, FR-052 |
| `systems_declared_not_scanned[]` | name, owner, form, reason | FR-017, FR-052 |
| `questions_asked` | integer ≤ 5 | FR-052 |
| `questions_defaulted` | integer | Drives the FR-066 banner at ≥ 3 |
| `caps_overridden[]` | name and value | Present only when a default was changed (FR-028) |

**No `spec_refs` field, in any form** (FR-052, FR-054).

### Section order

Comes from the resolved template, which an override may reshape (FR-057, FR-060). The shipped template's order:

1. Change statement — one line, restated (FR-061)
2. Inputs — the intent verbatim, every attachment with its state (FR-052a)
3. Impact rating — with the trigger that fired
4. Findings — the five core lenses, then the conditional ones if their triggers fired (FR-036 to FR-039)
5. External contract changes — human verification table (FR-043)
6. Human follow-up required — the excluded lenses that look relevant (FR-040)
7. Open risks and rollback — rollback path, and where the change becomes irreversible (FR-061)
8. Clarifications — question, answer, source (FR-035)
9. Assumptions and unknowns — including every defaulted answer, tagged (FR-033)
10. Sources consulted — coverage per system, scan mode, caps reached, terms searched and not found (FR-044, FR-048)

**Where an override omits a section**, the command notes the omission and does not reinstate it. Where an
override omits *Sources consulted*, the coverage statement still appears in the session — the trustworthiness
rules live in the command, not the template (plan, VIII).

---

## 3. The index

`<artifact-root>/impact-analysis/README.md`. Not an artifact: no sequence number, describes the folder.

| Column | Source |
|---|---|
| id | Document front matter |
| title | Document front matter |
| status | **Re-read from front matter on every run** (FR-056) |
| impact | Document front matter |
| date | Document front matter |
| supersedes / superseded by | Document front matter |

**Invariant.** Existing rows are refreshed from the documents before the new row is appended, and no document
is modified in order to do it (FR-056).

---

## 4. Status lifecycle — owned by a human, not the command

```text
                 ┌──────────────── the command's entire involvement ────────────────┐
                 │                                                                 │
   run  ────────▶│  draft                                                          │
                 │    │                                                            │
                 └────┼────────────────────────────────────────────────────────────-┘
                      │
      ┌───────────────┼────────────────┐
      ▼               ▼                ▼
  in-review        approved         rejected          ← all three set by a human, by hand
      │
      └──▶ superseded   ← the one later transition the command may write,
                          on explicit confirmation, two fields only
```

| Transition | Who | Requirement |
|---|---|---|
| → `draft` | The command, every run | FR-053a |
| `draft` → `in-review` / `approved` / `rejected` | A human editing the file | Deliberately outside the command |
| any → `superseded` | The command, on confirmation | FR-011, FR-005 — `status` and `superseded_by` only |
| any → `superseded`, non-interactively | **Nobody.** The new document records `supersedes`; the prior file is untouched and the run says so | FR-065 |

The command reads a human-set status — to surface it during supersede detection (FR-011) and to refresh the
index (FR-056) — and interprets it no further (FR-053a).

---

## 5. Write set

Exactly three things, all at the end of the run (FR-051a):

1. `<artifact-root>/impact-analysis/NNN-<name>.md` — new
2. `<artifact-root>/impact-analysis/README.md` — created on demand, rows refreshed, one row appended
3. `status` and `superseded_by` in one prior analysis — on explicit confirmation only

Nothing else. No constitution edit, no spec, no branch, no commit (FR-005). No write outside the project, and
no modification of any declared local path (FR-015). An interrupted run writes none of the three and consumes
no number (FR-051a).
