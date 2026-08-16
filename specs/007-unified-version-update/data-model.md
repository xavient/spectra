# Data Model — Unified Version & Update Commands

**Feature**: `007-unified-version-update` | **Date**: 2026-08-16

Three structures, all in-memory and all resolved once per command invocation. Nothing is persisted;
`spectra version` and `spectra update` are read-then-act commands with no state of their own.

---

## `ComponentStatus`

The health of one stack component. Every component produces this same shape no matter how its detection
works — that uniformity is what lets `cmd_version` render in a loop and `cmd_update` walk in order
without per-component branching.

| Field | Type | Meaning |
| --- | --- | --- |
| `key` | `str` | Stable identifier: `specify_cli` · `integration` · `spectra_cli` · `spectra_extension`. Used for ordering and lookup, never displayed. |
| `label` | `str` | Display name: `Specify CLI` · `Core agents` · `Spectra CLI` · `Spectra agents`. |
| `installed` | `str | None` | Version in place now. `None` when it could not be read. |
| `latest` | `str | None` | Version that ought to be in place. `None` when it could not be resolved. |
| `status` | `str` | One of the four values below. |
| `detail` | `str | None` | Why the status is what it is, when that is not self-evident. Required whenever `status == UNKNOWN`; otherwise usually `None`. |

`key` is deliberately distinct from `label`: the label is display copy and free to be reworded, while
`key` is what the update walk and the tests match on. The same split that `agents-list.json` draws
between an agent's `id` and its `title`.

### Status values

| Value | Constant | Meaning | Offered for update? |
| --- | --- | --- | --- |
| `up_to_date` | `UP_TO_DATE` | Installed matches latest. | No — nothing to do |
| `needs_updating` | `NEEDS_UPDATING` | Installed is behind latest. | **Yes** |
| `ahead` | `AHEAD` | Installed is newer than latest — a local or pre-release build. | No — FR-023 |
| `unknown` | `UNKNOWN` | Status could not be established. | No — FR-023, FR-024 |

There is no separate `error` value. An error *is* an unknown status with a `detail` explaining it: the
caller's decision is identical either way (report it, do not act on it), so a fifth value would be a
distinction without a consequence. This mirrors `extension.read_manifest_version()` returning `None` for
missing, unreadable, and version-less manifests alike.

### Invariants

- `status == UNKNOWN` ⟹ `detail` is a non-empty string.
- `status` is `UP_TO_DATE`, `NEEDS_UPDATING`, or `AHEAD` ⟹ both `installed` and `latest` are non-`None`.
  A comparison verdict without two versions to compare is not reachable.
- `installed is None and latest is None` ⟹ `status == UNKNOWN`.
- `installed` may be non-`None` while `status == UNKNOWN` — the common offline case, where the local
  version is readable but nothing can be compared against it (FR-026 requires it still be shown).

### Derivation

`UP_TO_DATE` / `NEEDS_UPDATING` / `AHEAD` come from `version.compare_versions(installed, latest)`,
reused unchanged so all four components order versions identically — component-wise, tolerant of a
leading `v`, and sorting an unparseable version below any real one.

---

## `HealthReport`

The four statuses together, representing full-stack health at one moment.

| Field | Type | Meaning |
| --- | --- | --- |
| `components` | `list[ComponentStatus]` | Exactly four, always in canonical order: Specify CLI, Core agents, Spectra CLI, Spectra agents. |

The list is never filtered and never reordered. A component that could not be checked appears as
`UNKNOWN` rather than being dropped, so the table always has four rows and a reader can tell "not
checked" from "not present".

### Derived properties

| Property | Definition | Used by |
| --- | --- | --- |
| `outdated` | components with `status == NEEDS_UPDATING`, in canonical order | the confirmation prompt (FR-024), the update walk (FR-008) |
| `needs_update` | `bool(outdated)` | the `spectra update` hint (FR-003), the no-op exit (FR-021) |
| `unknown` | components with `status == UNKNOWN` | the skipped rows in the final report (FR-023) |

Canonical order *is* the update order (FR-008), so `outdated` is directly walkable — the ordering
constraint is satisfied by construction rather than by a sort at the call site.

### Ordering rationale

Canonical order is not cosmetic. Two facts pin it:

1. The Core agents verdict is a function of the Specify CLI verdict (FR-025), so the CLI must resolve
   first.
2. Updating the Spectra CLI replaces the running process's own code, so it must come after the two
   `specify` steps and before only the extension update (R6).

---

## `UpdateResult`

The outcome of attempting one component's update. Produced only by `spectra update`.

| Field | Type | Meaning |
| --- | --- | --- |
| `key` | `str` | Matches the `ComponentStatus.key` it came from. |
| `label` | `str` | Carried through for display. |
| `outcome` | `str` | `UPDATED` · `FAILED` · `SKIPPED`. |
| `detail` | `str | None` | For `FAILED`, the actionable reason — exit code or error text (FR-012). For `SKIPPED`, why. |

### Outcomes

| Value | When | Effect on exit code |
| --- | --- | --- |
| `updated` | The delegated command reported success. | none |
| `failed` | Non-zero exit, `DelegationError`, or `UpdateError`. | **exit 4** (`EXIT_DELEGATION`) |
| `skipped` | Status was `UP_TO_DATE`, `AHEAD`, or `UNKNOWN` — never attempted. | none (FR-023) |

`skipped` is load-bearing rather than cosmetic: it is what keeps an undeterminable component from
turning a successful run into a failed one. The exit code answers "did anything I attempted go wrong?",
so a component never attempted cannot contribute to it.

### Invariants

- `outcome == FAILED` ⟹ `detail` is a non-empty string carrying an exit code or error message.
- Every component in `HealthReport.components` yields exactly one `UpdateResult` — the final report has
  four rows, like the status table, so the before and after line up.
- `outcome == UPDATED` is only reachable from `status == NEEDS_UPDATING`.

---

## The integration-vs-CLI state table

The Core agents verdict is the only one derived from two inputs, so it is enumerated in full. `I` is
`.specify/integration.json` → `version`; `C` is the installed Specify CLI version.

| Specify CLI status | `I` readable? | `I` vs `C` | Core agents status | `detail` |
| --- | --- | --- | --- | --- |
| `UNKNOWN` | either | — | `UNKNOWN` | the Specify CLI version is unknown, so there is nothing to compare against |
| `NEEDS_UPDATING` | yes | any | `NEEDS_UPDATING` | the Specify CLI is behind, and the integration tracks it |
| `NEEDS_UPDATING` | no | — | `UNKNOWN` | the integration version could not be read |
| `UP_TO_DATE` | yes | `I == C` | `UP_TO_DATE` | — |
| `UP_TO_DATE` | yes | `I < C` | `NEEDS_UPDATING` | the CLI was upgraded but the integration was not re-run |
| `UP_TO_DATE` | yes | `I > C` | `AHEAD` | a pre-release or hand-modified integration |
| `UP_TO_DATE` | no | — | `UNKNOWN` | the integration version could not be read |

Row 2 is the clarified coupling: when the CLI is behind, the integration is reported behind whatever the
file says, because the file can only ever record a version the *old* CLI installed. Its `latest` is then
the CLI's own latest, not the CLI's installed version — so the row reads `0.12.14 → 0.16.5` and matches
what the upgrade will actually produce.

### "Readable" means

`I` is unreadable when the file is missing, unreadable, not valid JSON, or has no non-empty `version`
key. All four collapse to `UNKNOWN` (FR-018) because the remedy is the same and the caller's behavior is
identical.

---

## Relationships

```text
project.ProjectState ─┐
                      ├─► health.check_all() ─► HealthReport ─┬─► ui.health_table()   (spectra version)
specify self check ───┤                          │            │
integration.json ─────┤                          │            └─► update walk ─► [UpdateResult × 4]
version.check_update()┤                          │                                      │
extension.published() ┘                          └── outdated ──► confirmation prompt ───┘
```

`HealthReport` is the single seam between detection and action. `spectra version` renders it and stops;
`spectra update` renders it, prompts on `outdated`, then walks it. Both commands see the same data,
which is what guarantees `spectra update` never acts on a state it did not first report.
