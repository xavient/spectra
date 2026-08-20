# Phase 0 Research: Multi-Integration Stack Updates

**Feature**: `010-multi-integration-updates` | **Date**: 2026-08-20

Ten decisions. The first four are load-bearing — they decide where truth comes from, how one row
represents many integrations, what order the walk runs in, and how consent is obtained. The rest close
the edges.

The dependency's observed behaviour is **not re-derived here**. It is recorded as findings F1–F9 in
[`brds/multi-integration-updates.md`](../../brds/multi-integration-updates.md) § 2.1, established
against Spec Kit CLI 0.16.5 on 2026-08-19. This document cites those findings rather than restating
them.

---

## R1 — Where per-integration truth comes from

**Decision**: A **split source**, with the split drawn on cost.

| What | Read from | Cost |
| --- | --- | --- |
| Which integrations are installed | `installed_integrations` in `.specify/integration.json` | file read |
| Each integration's version | `version` in `.specify/integrations/<key>.manifest.json` | file read per integration |
| Which managed files are modified | `specify integration status --json` | one subprocess |
| Which agents have Spectra commands | `registered_commands` in `.specify/extensions/.registry` | file read |

**Rationale**: The three cheap facts are all that `spectra version` needs, so the report stays a pure
local read and adds no subprocess (FR-001, FR-003, FR-012). Modification state is the one fact only the
dependency can supply — it is a hash comparison against what was recorded at install, and recomputing
it ourselves would duplicate the dependency's hashing and drift from it the moment its algorithm
changes. It is also only needed by `spectra update`, so it is fetched **only on that path**.

This is the shape that makes FR-012 achievable. A single-integration project runs exactly the file
reads it runs today; nothing new executes.

**Alternatives considered**:

- *Everything from `specify integration status --json`.* Rejected: it reports membership and
  modification state but **not** per-integration versions (F2), so it cannot answer the currency
  question on its own — and it would put a subprocess in the path of every `spectra version`.
- *Compute modification state ourselves from the manifests' recorded hashes.* Rejected: it is the
  dependency's contract with its own installed files, and a divergence in hashing would produce a
  disclosure that does not match what the upgrade will actually overwrite — the worst possible failure
  for a consent gate.
- *Glob `.specify/integrations/*.manifest.json` for membership.* Rejected on evidence: that directory
  also holds `speckit.manifest.json`, which is shared infrastructure and not an integration (F8,
  FR-002).

---

## R2 — How one report row represents many integrations

**Decision**: Keep four `ComponentStatus` rows. The `Core agents` row gains an ordered list of
`IntegrationState` children, and its own status is **derived** from them by a pure aggregation
function.

Precedence, highest first:

| # | Condition | Row status |
| - | --------- | ---------- |
| 1 | any integration is behind | `NEEDS_UPDATING` |
| 2 | any integration's state is unestablished | `UNKNOWN` |
| 3 | every integration is ahead | `AHEAD` |
| 4 | otherwise (all current, or a mix of current and ahead) | `UP_TO_DATE` |

**Rationale**: Rule 1 outranks rule 2 because a behind integration is *actionable* — an unreadable
sibling must not hide work that can be done (and the unknown sibling is still never attempted, FR-015).
Rule 2 outranks rules 3 and 4 because the row must never claim currency it has not established: FR-006
permits `UP_TO_DATE` only when **every** installed integration is current, and an unknown one is not
current, it is unknown. Rule 3 is FR-009 verbatim.

Rule 4 resolves a tension worth naming: FR-006 says "up to date only when every integration is
current", and FR-009 says "ahead only when every integration is ahead" — which leaves a mix of ahead
and current unassigned. It reports `UP_TO_DATE`, because "ahead" is a flavour of not-behind and the row
exists to answer "is anything stale here?".

**Alternatives considered**:

- *A fifth report row per integration.* Rejected: FR-011 and the four-component contract from
  `007-unified-version-update` are explicit, and the four-row shape is asserted in `tests/test_health.py`
  and `tests/test_version_update.py`, documented in the README, and shown on the docs site.
- *Report only the default integration and mention the others in a footnote.* Rejected: it reintroduces
  the silent drift this feature exists to remove, and the spec records the rejection as an assumption.
- *Aggregate inside the renderer.* Rejected: the verdict decides whether the walk runs, so it must exist
  before rendering and be unit-testable without a terminal.

---

## R3 — Upgrade mechanism and order

**Decision**: Iterate `specify integration upgrade <key>` over the behind integrations, **never**
switching the project default (FR-017). Within the walk, **the default integration goes last** when it
is among those being upgraded.

**Rationale**: Naming the key is supported and does not disturb the default (F3), which is what makes
FR-017 satisfiable at all. Order matters because of what the dependency does on each kind of upgrade
(F4): upgrading a non-default key installs shared infrastructure aligned to the *default*, while
upgrading the default key refreshes shared infrastructure as its own and re-registers extension and
preset commands. Ending on the default therefore makes the last write to shared infrastructure the
default-aligned, managed-refresh one — which is exactly the end state FR-018 requires.

**Alternatives considered**:

- *Switch the default to each integration, upgrade, switch back* — the manual workaround users are
  driven to today. Rejected by FR-017: it mutates committed project configuration, it rewrites shared
  templates once per switch, and an interrupt mid-walk would leave the project pointing somewhere the
  team did not choose. Its one advantage (it re-registers extension commands for each agent) is
  deliberately given up and reported instead (R7).
- *Default first.* Rejected: the default's own upgrade is the only one that performs the managed
  refresh, so running it first lets a later non-default upgrade write over it.
- *Alphabetical or recorded order.* Rejected: neither has a reason behind it, and both leave FR-018
  to luck.

---

## R4 — How overwrite consent is obtained

**Decision**: **Plan, disclose, ask once, then walk.** Before any upgrade is attempted, the modification
report is fetched (R1) and reduced to the set of behind integrations whose managed files are modified.
If that set is empty, nothing new is printed and nothing is asked. If it is not, the affected files are
listed — grouped per integration, and shared Spec Kit infrastructure as its own group — and a single
question is asked, defaulting to **no**. Overwrite is then applied only to the integrations in that set.

**Rationale**: This is the only ordering that can disclose files *before* asking, which FR-025 requires.
It also matches the shape `cmd_update` already has — list what will change, ask once — so the run keeps
one confirmation, not two.

Shared infrastructure is disclosed even though it is never what triggers the block, because the
dependency's overwrite is not scoped to the offending files (F6): authorizing it for one integration
also overwrites customized shared templates and scripts. A disclosure that hid that would be a lie in
the one place where lying is most expensive. In the measured project the shared group is exactly the
spec, plan, and tasks templates — the files a team is most likely to have deliberately customized.

**Alternatives considered**:

- *Attempt without force, catch the failure, then ask and retry.* Rejected: the failure arrives after
  other integrations may already have been upgraded, the file list is only available by parsing the
  dependency's human-formatted refusal (FR-041), and the user would be asked mid-walk rather than as
  part of the one plan they approved.
- *Ask per integration.* Rejected: N prompts for one decision, and the shared-infrastructure group
  would be re-disclosed with each, training the user to skim exactly the group that matters most.
- *Force whenever the block is detected, since "it just reinstalls".* Rejected on evidence: it discards
  the team's modified content (F5, F6), and it is the specific decision the existing published contract
  refuses to make on the user's behalf.

---

## R5 — Where `--force` lives on the command surface

**Decision**: `--force` is registered on the **`update` subparser only**, not on the shared flag set.
Code reads it as `bool(getattr(args, "force", False))`.

**Rationale**: `--yes` and `--no-update-check` are shared because they are meaningful for several
commands; `--force` is meaningful for exactly one. Registering it globally would make
`spectra uninstall --force` parse, where force already has a different, weaker meaning (it suppresses a
confirmation), which is the collision the spec's clarification set out to contain. Typing
`spectra --force update` produces this CLI's existing error path — the message plus the full help
panels, exit 2 — which names the flag in its correct position.

**Alternatives considered**:

- *Add it to `_add_shared`.* Rejected for the collision above.
- *Reuse `--yes`.* Rejected by FR-027; it is the entire point of the consent model.
- *A distinct name such as `--overwrite-modified`.* Considered and decided against by the user in the
  spec's Clarifications, with the mitigation recorded in FR-028.

---

## R6 — Degrading when modification state cannot be read

**Decision**: If `specify integration status --json` cannot be run or parsed, **attempt the upgrades
without force** and let the dependency refuse the ones it must. Never force blindly.

**Rationale**: Not knowing what would be overwritten is precisely the state in which overwriting must
not happen. The dependency's own refusal is informative (it names the files and the flag), and the
attempt still upgrades every integration that has nothing modified — so the run makes real progress
instead of stalling. Reporting `UNKNOWN` for the whole row instead would remove capability that exists
today.

**Alternatives considered**:

- *Skip the integration component entirely when the pre-check fails.* Rejected: it would make an
  unrelated probe failure block updates that would have succeeded.
- *Parse the dependency's human-formatted refusal to recover the file list.* Rejected by FR-041, and by
  the same reasoning that keeps `parse_self_check` matching on stable prefixes only.

---

## R7 — The coverage advisory: detect, do not act

**Decision**: Read `extensions.spectra.registered_commands` from `.specify/extensions/.registry` — a map
keyed by agent — and compare its keys against the installed integrations. Report any installed
integration missing from that map as an advisory below the four rows, naming
`specify integration use <key>` and stating that it changes the project's default integration. Never run
it (FR-040).

**Rationale**: The registry is *recorded state*, not an inference about the dependency's policy, so the
advisory is true regardless of why the gap exists. Verified shape: in the measured drifted project the
map contains `kiro-cli` only, which matches the absent `.claude/skills/speckit-spectra-*` files exactly.
There is also no public lever for fixing it — no `specify extension` verb takes an agent argument — so
the only remedy is a default change, which belongs to the team (F4, and the scope rule the whole feature
is bounded by).

An unreadable or absent registry yields **no advisory at all** (FR-039). In this very repository there
is no `spectra` entry, because the repo is the extension's source rather than a consumer of it — a live
example of the case that must stay silent instead of guessing.

**Alternatives considered**:

- *Detect by looking for command files in each agent's directory.* Rejected: it hard-codes per-agent
  layout knowledge (skills vs commands, differing separators) that the dependency owns.
- *Fan out registration ourselves.* Rejected by FR-040 and out of scope in the spec.
- *Say nothing.* Rejected: the situation is silent today and that is the complaint.

---

## R8 — Falling back on an older Spec Kit

**Decision**: When `installed_integrations` is absent or no per-integration manifest can be read, fall
back to **today's behaviour**: one unnamed integration judged by the `version` field in
`.specify/integration.json`, upgraded with a bare `specify integration upgrade`. Detected by absence of
data, not by comparing version numbers.

**Rationale**: The spec's assumption is explicit — losing capability that exists today would be worse
than reporting less detail. Keying off data presence rather than a version comparison means the
fallback also covers a project whose state predates the current layout, and it needs no minimum-version
constant to be maintained as the dependency moves.

**Alternatives considered**:

- *Report `UNKNOWN` on older Spec Kit.* Rejected: it takes away a working update path.
- *Pin and enforce a minimum `specify` version.* Rejected as unnecessary: the data-presence check is
  strictly more accurate than a version number, and one fewer constant can go stale.

---

## R9 — Per-integration outcomes inside a one-row report

**Decision**: `UpdateResult` gains an optional ordered list of child results, one per attempted
integration. The parent's outcome is the **worst** of its children (`FAILED` > `UPDATED` > `SKIPPED`),
and the renderer prints the parent row plus one indented line per child. Verification (FR-022) re-reads
each integration's own manifest version, so "reported success but the version is unchanged" is decided
per integration.

**Rationale**: It preserves both existing invariants at once — every component is visited and produces
exactly one row, and skips never influence the exit code — while making the failure attributable to the
integration that failed (FR-021, FR-023). Worst-of is what keeps FR-023 true without special-casing:
one failed child makes the component failed, and a component of only skipped children stays inert.

**Alternatives considered**:

- *Return N flat results for the integration component.* Rejected: it breaks the one-row-per-component
  correspondence that `_outcome_row` and the report's four-row contract depend on.
- *Report only the aggregate.* Rejected by FR-021, and it would hide which of two integrations failed —
  the exact information a user needs to act.

---

## R10 — Test fixtures this requires

**Decision**: Three fixture changes in `tests/helpers.py`, all additive with today's defaults preserved:

1. `temp_project(...)` accepts an `integrations=` mapping (`{"kiro-cli": "0.15.1", "claude": "0.16.5"}`)
   that writes `installed_integrations`, `default_integration`, and one manifest per key. Omitting it
   keeps the current single-record fixture, so existing tests are untouched.
2. `fake_specify` becomes **argument-aware**: it currently prints the same canned text whatever it is
   asked, so it would answer `integration status --json` with self-check output. It must dispatch on the
   subcommand and serve a JSON payload for `integration status`, self-check text for `self check`, and
   exit 0 otherwise.
3. A `modified=` option on the same stub to seed per-integration and shared `modified_files` lists, which
   is what makes the disclosure and consent paths testable end to end.

**Rationale**: The suite deliberately exercises the real subprocess path rather than mocking the parse
function, and that property is worth keeping for a feature whose correctness depends on how the child is
invoked. Argument-awareness is the smallest change that keeps it.

**Alternatives considered**:

- *Mock the new status reader directly.* Rejected: it would stop testing argv construction, which is
  where `upgrade <key> --force` can go wrong in the way that matters most.
- *A second stub script.* Rejected: two stubs on PATH answering different subcommands of one command is
  harder to reason about than one stub with a case statement.

---

## Unknowns resolved

Every `NEEDS CLARIFICATION` from the plan's Technical Context is closed above: truth source (R1),
aggregation (R2), mechanism and order (R3), consent flow (R4), flag placement (R5), degradation (R6, R8),
advisory source (R7), result shape (R9), fixtures (R10). No open unknowns remain for `/speckit.tasks`.
