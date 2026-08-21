# Phase 1 — Data Model: Full Integration Coverage on Install and Update

Four structures and one enumeration. None of them is persisted: every value is derived from recorded
project state at the start of a run and discarded when it ends, which is what makes "no authorization is
remembered" and "nothing is cached" true by construction rather than by policy.

Field names below are the contract for the tests; they are not a licence to add fields the requirements
do not ask for.

---

## Enumeration: coverage state

Per integration, one of three values. **Unknown is first-class** and never collapses into "uncovered"
(FR-003).

| Value | Meaning | Source |
| --- | --- | --- |
| `COVERED` | the registry records Spectra commands registered for this integration | `.specify/extensions/.registry` names the key |
| `UNCOVERED` | the registry is readable and does **not** name this integration | same |
| `UNKNOWN` | the registry is absent, unreadable, has no `spectra` entry, or an empty command map | same, degraded |

`UNKNOWN` is a property of the **whole project**, not of one integration: the registry either answers the
question for every agent or for none. So a run either has a per-integration `COVERED` / `UNCOVERED` map,
or it has nothing at all.

---

## `CoverageState`

One integration's coverage, as read before any work.

| Field | Type | Notes |
| --- | --- | --- |
| `key` | `str` | the integration key, from the project's recorded installed list (FR-002) |
| `covered` | `bool` | `True` when the registry names it |
| `is_default` | `bool` | `True` for the project's recorded default |

Rules:

- Keys come from `installed_integrations` in `.specify/integration.json`, with the shared-infrastructure
  record excluded (FR-002). Never from a directory listing.
- Agents named in the registry but **absent** from the installed list produce no state and are ignored
  (FR-005). They are neither a problem to report nor coverage to claim.

---

## `CoveragePlan`

What a run intends to do, as pure data. Produced by `coverage.plan(project_root)`; consumed by
`coverage.apply(plan)` and by the disclosure.

| Field | Type | Notes |
| --- | --- | --- |
| `targets` | `tuple[str, ...]` | uncovered integrations **excluding** the default, in recorded order (R3) |
| `default_key` | `str \| None` | the original default — the value to restore, and the last activation |
| `default_uncovered` | `bool` | whether the default itself lacks coverage; it is covered by the restore |
| `states` | `tuple[CoverageState, ...]` | every installed integration, for the outcome report |
| `skip_reason` | `str \| None` | why there is nothing to do, when that is the case |

Derived properties:

| Property | Definition |
| --- | --- |
| `needed` | `bool(targets) or default_uncovered` |
| `moves_default` | `bool(targets)` — activating a non-default key is the only thing that moves it |
| `activations` | `targets + (default_key,)` when `needed`, else `()` |

**Empty-plan rules (R11).** `needed` is `False`, `activations` is empty, and `skip_reason` is set, in
each of these cases:

| Situation | `skip_reason` | Requirement |
| --- | --- | --- |
| every installed integration is covered | `"every integration already has Spectra's commands"` | FR-011, FR-037 |
| coverage state is `UNKNOWN` | `"the registration state could not be read"` | FR-003, FR-004 |
| no default integration recorded | `"no default integration is recorded, so there would be nothing to restore"` | FR-012, FR-009 |
| no installed integrations recorded | `"no installed integrations are recorded for this project"` | FR-002 |
| the extension is not present in the project | `"Spectra is not installed in this project"` | FR-022 |

A plan carrying a `skip_reason` is never silently discarded: the *install* and *update* print it only
when it is the reason a user would otherwise be confused (see `contracts/cli-surface.md`); an
all-covered project prints nothing at all.

**`moves_default` is what gates the disclosure.** A plan with an empty `targets` and
`default_uncovered = True` performs exactly one activation — of the key that is already default — so
FR-013 forbids a transient-default disclosure for it.

---

## `CoverageResult`

What happened. Mirrors the shape `health.UpdateResult` already uses so `cli.py` can render it with the
existing outcome-table helpers.

| Field | Type | Notes |
| --- | --- | --- |
| `outcome` | one of `COVERED` / `FAILED` / `SKIPPED` | the aggregate, by the precedence below |
| `detail` | `str \| None` | the skip reason, or the failure summary |
| `parts` | `tuple[CoverageOutcome, ...]` | one per installed integration |
| `restoration` | `NOT_NEEDED` / `RESTORED` / `NOT_RESTORED` | R4 |
| `original_default` | `str \| None` | echoed for the recovery message (FR-034) |
| `current_default` | `str \| None` | re-read after the rotation; only differs when `NOT_RESTORED` |

Aggregate precedence, first match wins:

1. any child `FAILED`, or `restoration == NOT_RESTORED` → `FAILED`
2. any child `NEWLY_COVERED` → `COVERED`
3. otherwise → `SKIPPED` with `detail` set

### `CoverageOutcome` (child)

| Field | Type | Notes |
| --- | --- | --- |
| `key` | `str` | the integration |
| `outcome` | `NEWLY_COVERED` / `ALREADY_COVERED` / `FAILED` / `SKIPPED` | FR-032 |
| `detail` | `str \| None` | for `FAILED`, the delegated exit code; for `SKIPPED`, the reason |

**`NEWLY_COVERED` is only ever set from re-read state.** A delegated activation exiting 0 is not
evidence: after the rotation, `coverage.plan`'s detection runs again and a target still absent from the
registry is reported `FAILED`, with a detail saying the activation reported success but the registration
did not appear (FR-006). This is the same discipline feature 010 applied to versions that did not move.

---

## State transitions

The only transitions a rotation can produce, per integration:

```text
UNCOVERED --activation succeeds, registry now names it--> COVERED        (NEWLY_COVERED)
UNCOVERED --activation fails----------------------------> UNCOVERED      (FAILED)
UNCOVERED --activation exits 0, registry unchanged------> UNCOVERED      (FAILED, verification)
UNCOVERED --not reached (earlier interrupt)-------------> UNCOVERED      (SKIPPED)
COVERED   --never activated----------------------------> COVERED        (ALREADY_COVERED)
```

And for the project as a whole:

```text
default = D
  no activation of a non-default key        -> restoration NOT_NEEDED, default still D
  activation(s), then activate(D) succeeds  -> restoration RESTORED,   default still D
  activation(s), then activate(D) fails     -> restoration NOT_RESTORED, default = last activated key
```

`NOT_RESTORED` is the only state in which the project ends differently from how it started, and it is the
only state that prints a recovery command (FR-034). Every other path satisfies FR-043.

---

## Validation rules

Drawn directly from the requirements; each is a test.

| Rule | Requirement |
| --- | --- |
| `targets` never contains the default key | R3, FR-015 |
| `targets` never contains a covered integration | FR-011 |
| `targets` never contains a key absent from the installed list | FR-002 |
| `activations` is empty whenever `needed` is `False` | FR-004, FR-011, FR-012 |
| `activations` always ends with `default_key` when non-empty | FR-015 |
| no field of any structure carries a force/overwrite flag | FR-009, FR-049 |
| no integration key appears as a literal in the module | FR-046 |
| `restoration` is `NOT_NEEDED` exactly when `moves_default` is `False` | FR-013, FR-038 |
| a child is `NEWLY_COVERED` only if post-rotation detection says `COVERED` | FR-006 |

---

## What is deliberately **not** modelled

- **Versions.** Coverage says nothing about whether an integration is current; that is `health.py`'s
  `IntegrationState` and stays there (research R1).
- **The overwrite authorization.** No structure here has a field for it, so no code path here can carry
  one (FR-009, FR-049).
- **Presets.** The dependency registers presets on the same activation; Spectra neither models nor
  reports them (spec § Out of scope, inherited from BRD-006).
- **A cache of coverage between runs.** Every run re-reads. A stale cache would be a way to report
  coverage that no longer exists.
