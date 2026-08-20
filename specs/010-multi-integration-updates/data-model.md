# Phase 1 Data Model: Multi-Integration Stack Updates

**Feature**: `010-multi-integration-updates` | **Date**: 2026-08-20

Five structures. One is new (`IntegrationState`), two are new but short-lived (`ModificationReport`,
`OverwritePlan`), and two are existing structures that gain one optional field each
(`ComponentStatus.parts`, `UpdateResult.parts`). Nothing existing changes shape, so every current caller
and test keeps working.

---

## 1 · `IntegrationState` — one installed integration

**New**, in `spectra_cli/health.py`. The unit of truth this feature adds: what a single installed
integration is, and whether it is current.

| Field | Type | Meaning |
| --- | --- | --- |
| `key` | `str \| None` | The integration's key (`"kiro-cli"`, `"claude"`). `None` only in the single-record fallback (R8), where the project records no key. |
| `installed` | `str \| None` | Version recorded in `.specify/integrations/<key>.manifest.json`. `None` when unreadable. |
| `latest` | `str \| None` | The version this integration should be at — the Specify CLI's latest when the CLI is behind, otherwise the CLI's installed version. |
| `status` | one of `UP_TO_DATE` / `NEEDS_UPDATING` / `AHEAD` / `UNKNOWN` | Same four-value vocabulary as `ComponentStatus`; reusing it means the aggregation has nothing to translate. |
| `detail` | `str \| None` | Required when `status` is `UNKNOWN`. Also carries the reason a behind integration is behind, mirroring today's two cases. |
| `is_default` | `bool` | Whether this is the project's `default_integration`. Decides walk position (last) and nothing else. |
| `modified` | `list[str] \| None` | Managed files that diverge from what was installed. `None` means *not established*, which is different from `[]` (established as clean) — the distinction drives R6's degradation. |

**Validation rules**

- `detail` MUST be present when `status` is `UNKNOWN` (FR-005) — an unknown with no reason is not
  actionable.
- `installed` MAY be `None` while `status` is `UNKNOWN`; that is the ordinary unreadable-manifest case.
- `installed` MUST be present when `status` is anything other than `UNKNOWN` — a verdict without a
  version is not derivable.
- `modified` is only ever populated on the `spectra update` path. `spectra version` leaves it `None` by
  construction, because it never runs the probe that fills it (R1).

**Per-integration verdict rules** — the same two-way reasoning the current single-record check uses,
applied per key:

| Specify CLI status | Recorded version vs installed CLI | `IntegrationState.status` |
| --- | --- | --- |
| `UNKNOWN` | — | `UNKNOWN` — "the Specify CLI version is unknown, so there is nothing to compare against" |
| any | unreadable | `UNKNOWN` — "no usable version in the manifest for `<key>`" |
| `NEEDS_UPDATING` | any | `NEEDS_UPDATING`, `latest` = the CLI's latest — "the Specify CLI is behind, and the integration tracks it" |
| `UP_TO_DATE` / `AHEAD` | recorded < installed | `NEEDS_UPDATING`, `latest` = the CLI's installed — "the Specify CLI was upgraded but this integration was not re-run" |
| `UP_TO_DATE` / `AHEAD` | recorded > installed | `AHEAD` |
| `UP_TO_DATE` / `AHEAD` | equal | `UP_TO_DATE` |

Comparison is `version.compare_versions`, so a leading `v` and an unparseable version behave as they do
everywhere else in the CLI.

---

## 2 · `ComponentStatus.parts` — the aggregate row

**Existing structure, one new optional field.** `parts` is an ordered `list[IntegrationState]`, empty for
the three components that are not plural.

The row's own `status`, `installed`, `latest`, and `detail` are **derived** from `parts` and never set
independently, so the row cannot disagree with its own children:

| Field | Derivation |
| --- | --- |
| `status` | The precedence table below |
| `installed` | The **oldest** readable version among `parts` (FR-007) |
| `latest` | The target the behind children share; the CLI's installed version otherwise |
| `detail` | Names the behind children when behind; names the unestablished children when unknown |

### Aggregation precedence (FR-006, FR-009, FR-010)

Evaluated top to bottom; first match wins.

| # | Condition | Row `status` | Row `detail` |
| - | --------- | ------------ | ------------ |
| 1 | `parts` is empty | `UNKNOWN` | "no installed integrations are recorded for this project" |
| 2 | any child is `NEEDS_UPDATING` | `NEEDS_UPDATING` | names the behind keys |
| 3 | any child is `UNKNOWN` | `UNKNOWN` | names the unestablished keys |
| 4 | every child is `AHEAD` | `AHEAD` | — |
| 5 | otherwise | `UP_TO_DATE` | — |

Rule 2 outranks rule 3 so an unreadable sibling cannot hide actionable work. Rule 3 outranks rules 4–5
so the row never claims currency it has not established. Rule 5 covers both "all current" and "a mix of
current and ahead"; see research R2 for why that mix is `UP_TO_DATE`.

### Breakdown visibility (FR-013)

The per-integration lines are rendered only when **both** hold:

- `len(parts) > 1`, and
- the children are not uniform — their versions differ **or** their statuses differ.

A single-integration project therefore never renders a breakdown, and a two-integration project that is
uniformly current renders only the row. This is the rule that makes FR-012 and SC-005 assertable.

---

## 3 · `ModificationReport` — what has diverged

**New**, short-lived, built once per `spectra update` run from `specify integration status --json`.

| Field | Type | Meaning |
| --- | --- | --- |
| `per_integration` | `dict[str, list[str]]` | Modified managed files, keyed by integration key |
| `shared` | `list[str]` | Modified shared Spec Kit infrastructure files (the `speckit` record — never an integration, F8/FR-002) |
| `established` | `bool` | `False` when the probe could not be run or parsed (R6) |

**Validation rules**

- `established` is `False` → both lists MUST be empty, and no overwrite may be authorized on the basis
  of this report. The walk proceeds unforced (R6).
- The `speckit` entry MUST be routed to `shared` and MUST NOT appear as a key in `per_integration`.
- Keys in `per_integration` that are not in the installed-integrations list are ignored rather than
  treated as integrations.

---

## 4 · `OverwritePlan` — the authorization decision

**New**, short-lived, built in `cli.py` between the check and the walk. This is the structure that makes
"no file is overwritten without an authorization act in the same run" (SC-003) inspectable rather than
implicit.

| Field | Type | Meaning |
| --- | --- | --- |
| `candidates` | `dict[str, list[str]]` | Integrations that are **about to be upgraded** and have modified files — the only ones a prompt may cover (FR-034) |
| `shared` | `list[str]` | The shared files that would be overwritten as collateral if any candidate is authorized (F6, FR-025) |
| `authorized` | `set[str]` | Integration keys the user authorized **this run**. Empty until the act happens |
| `source` | `"flag"` / `"prompt"` / `"none"` | How authorization was obtained; `"none"` when withheld or unavailable |

**State transitions** — the only paths by which `authorized` becomes non-empty:

```text
candidates empty ─────────────────────────────► authorized = {}        source = none
                                                 (nothing disclosed, nothing asked)

candidates ≠ {} ─┬─ --force passed ───────────► authorized = candidates source = flag
                 │   (disclosure still printed — FR-032)
                 ├─ TTY, user answers yes ────► authorized = candidates source = prompt
                 ├─ TTY, user answers no ─────► authorized = {}        source = none
                 └─ no TTY, no --force ───────► authorized = {}        source = none
                     (names --force; never blocks — FR-031)
```

**Validation rules**

- `authorized` MUST be a subset of `candidates` (FR-029) — an integration that can be upgraded without an
  overwrite is never forced.
- `authorized` MUST be empty when `ModificationReport.established` is `False` (R6).
- The plan is discarded at the end of the run; nothing about it is written to disk (FR-033).
- A key in `candidates` but not in `authorized` yields `SKIPPED`, never `FAILED` (FR-030).

---

## 5 · `UpdateResult.parts` — per-integration outcomes

**Existing structure, one new optional field.** `parts` is an ordered `list[UpdateResult]`, one per
attempted integration, empty for the three components that are not plural.

| Field | Meaning for a child |
| --- | --- |
| `key` | The integration key, so the row can name it |
| `outcome` | `UPDATED` / `FAILED` / `SKIPPED` — same vocabulary as the parent |
| `detail` | Failure detail, or the skip reason (already current / ahead / unknown / overwrite not authorized) |

**Roll-up rule**: the parent's `outcome` is the **worst** of its children, ordered
`FAILED` > `UPDATED` > `SKIPPED`. Consequences, both required:

- One failed integration makes the component failed, so `EXIT_DELEGATION` (4) is reached (FR-023).
- A component whose children were all skipped stays inert and cannot turn a clean run into a failed one
  (FR-023, FR-030).

**Verification rule** (FR-022): after the walk, each attempted integration's manifest version is
re-read. A child whose `outcome` is `UPDATED` but whose version did not move is rendered as "reported
success, but the version is unchanged" — decided per integration, not for the component as a whole.

---

## Relationships

```text
HealthReport
 └── ComponentStatus × 4                      (unchanged shape; four rows always)
      └── Core agents only:
           parts: [IntegrationState, ...]     (one per installed integration, ordered)

ModificationReport  ──filtered by "about to be upgraded"──►  OverwritePlan
                                                                  │
                                                        authorized: set[key]
                                                                  │
                                                                  ▼
apply_updates(report, authorized_keys) ──► [UpdateResult × 4]
                                            └── Core agents only:
                                                 parts: [UpdateResult per key]
```

`IntegrationState` is the only structure that crosses phases: detection produces it, aggregation reads
it, the walk consumes the behind ones, and verification re-reads its version. Everything else is derived
from it and discarded.
