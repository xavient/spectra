# Contract: CLI Surface

**Feature**: `010-multi-integration-updates` | **Date**: 2026-08-20

The user-visible surface after this change: what flags exist, what the output looks like, what the exit
codes mean, and which published decision this feature supersedes.

This contract **extends** `specs/007-unified-version-update/contracts/cli-surface.md`. Everything not
mentioned here is unchanged.

---

## 1 · Commands

No command is added, removed, or renamed. Two change behaviour:

| Command | Change |
| --- | --- |
| `spectra version` | The `Core agents` row reflects every installed integration; a breakdown and a coverage advisory may follow |
| `spectra update` | Upgrades every behind integration; may disclose modified files and ask once; gains `--force` |

`spectra check`, `spectra install`, `spectra uninstall`, `spectra agent-list`, and `spectra cli
uninstall` are untouched. `spectra check` deliberately does **not** gain the coverage advisory (spec
Assumptions).

---

## 2 · Flags

| Flag | Scope | Meaning |
| --- | --- | --- |
| `--force` | **`update` subparser only** | Authorize overwriting modified managed files (FR-028) |
| `--yes` / `-y` | shared, unchanged | Approve the update plan. **Never** authorizes an overwrite (FR-027) |
| `--no-update-check` | shared, unchanged | Suppress the latest-release lookup |

**Placement (research R5)**: `--force` is registered on the `update` subparser, not in `_add_shared`, so
it cannot be typed at other commands where "force" already means something weaker. Code reads it as
`bool(getattr(args, "force", False))` because it is absent from other namespaces.

`spectra --force update` is a usage error and takes the existing error path: the message plus the full
help panels, exit `EXIT_USAGE` (2).

**Help text** must state the consequence, not the mechanism, because the word is overloaded across this
CLI (FR-028):

```text
--force   Overwrite managed files that have been modified locally (spectra update)
```

---

## 3 · `spectra version` output

### Single integration — unchanged (FR-012, SC-005)

```text
  Specify CLI:     ✓ up to date (0.16.5)
  Core agents:     ✓ up to date (0.16.5)
  Spectra CLI:     ✓ up to date (6.1.0)
  Spectra agents:  ✓ up to date (1.3.1)
```

Byte-identical to the previous release. No breakdown, no advisory, no added blank line.

### Several integrations, not uniform — breakdown appears

```text
  Specify CLI:     ✓ up to date (0.16.5)
  Core agents:     ! needs updating (0.15.1 -> 0.16.5) — kiro-cli, claude
                     kiro-cli:  ! needs updating (0.15.1 -> 0.16.5)
                     claude:    ! needs updating (0.15.1 -> 0.16.5)
  Spectra CLI:     ✓ up to date (6.1.0)
  Spectra agents:  ✓ up to date (1.3.1)
```

- Row version is the **oldest** among the integrations (FR-007); behind keys are named on the row
  (FR-008).
- Child lines are indented under the row and reuse the same glyph vocabulary, rendered by the same
  helper — one renderer, so the columns cannot drift.
- Child lines appear **only** when more than one integration is installed and they are not uniform
  (FR-013).

### Several integrations, uniform — no breakdown

```text
  Core agents:     ✓ up to date (0.16.5)
```

### Coverage advisory (US5)

Rendered after the table and any update hint, never as a row, never affecting the exit code (FR-038):

```text
  ! Spectra commands are registered for kiro-cli only.
    claude is installed here but has no Spectra commands.
    To scaffold them: specify integration use claude
    (this changes the project's default integration for everyone.)
```

Suppressed entirely when the registry cannot be read (FR-039) or coverage is complete.

---

## 4 · `spectra update` flow

```text
1. classify the project            (unchanged: not-a-project / not-installed / incomplete)
2. check_all()                     -> the same four-row report `version` renders
3. render the report               (unchanged)
4. nothing behind                  -> report and exit 0                        (unchanged)
5. confirm the plan                -> lists each component, and each integration by name
6. build the overwrite plan        -> modification_report(), reduced to behind integrations
7. if candidates: disclose, then resolve authorization                          (§ 5)
8. walk                            -> per component; per integration inside Core agents
9. re-check and render outcomes    -> per component; per integration inside Core agents
```

Step 6 runs **after** the plan is confirmed and **before** anything is attempted. That ordering is what
lets the disclosure list real files while still leaving the run abortable at no cost.

### The plan listing (step 5)

```text
The following components need updating:
  • Core agents: 0.15.1 -> 0.16.5 (kiro-cli, claude)
  • Spectra agents: 1.3.0 -> 1.3.1

Proceed? [Y/n]
```

Integrations are named here because they are what will be acted on (FR-016).

---

## 5 · Disclosure and authorization

Shown only when at least one integration **about to be upgraded** has modified files (FR-034). Otherwise
this whole section prints nothing and asks nothing.

```text
! Modified files detected. Upgrading will overwrite them with the bundled versions.

  kiro-cli — 10 managed file(s)
    .kiro/prompts/speckit.analyze.md
    …

  Shared Spec Kit infrastructure — 3 file(s)
    .specify/templates/spec-template.md
    .specify/templates/plan-template.md
    .specify/templates/tasks-template.md

  There is no way to show what changed in these files, so the choice is to overwrite
  them or leave these integrations as they are.

Overwrite these files? [y/N]
```

Requirements this shape satisfies:

- Files are listed **before** the question (FR-025), grouped per integration and shared infrastructure
  separately — shared is included because the overwrite is not scoped to the files that caused the block
  (finding F6).
- The prompt defaults to **no** (FR-026); pressing Enter overwrites nothing.
- The closing sentence states the two real options and does **not** advise reviewing a difference the
  command cannot display (FR-035, finding F9).
- All affected files are listed in full, not truncated (spec Assumptions).

### Authorization resolution

| Situation | Result | Output |
| --- | --- | --- |
| `--force` passed | every candidate authorized | disclosure still printed (FR-032) |
| TTY, answered yes | every candidate authorized | — |
| TTY, answered no | nothing authorized | candidates skipped with the options |
| No TTY, no `--force` | nothing authorized | candidates skipped; **`--force` named** (FR-031) |
| Modification state unestablished | nothing authorized | no disclosure; walk proceeds unforced (R6) |

Nothing is remembered between runs (FR-033). A project that needs an overwrite is asked every time.

---

## 6 · Outcome output

```text
  Specify CLI:     – skipped (already up to date)
  Core agents:     ✓ updated (0.16.5)
                     kiro-cli:  ✓ updated (0.16.5)
                     claude:    – skipped (overwrite not authorized)
  Spectra CLI:     – skipped (already up to date)
  Spectra agents:  ✓ updated (1.3.1)
```

- The component row shows the **worst** child outcome; children are listed beneath it (FR-021, R9).
- Versions in both the row and the children are **re-read after** the walk, so a delegated success that
  moved nothing renders as "reported success, but the version is unchanged" (FR-022).
- Skip reasons are specific: `already up to date`, `ahead of the published version`,
  `status could not be determined`, `overwrite not authorized`.

When integrations were skipped for want of authorization, the run closes with the remedy:

```text
  claude was left at 0.15.1. To upgrade it, re-run with --force to overwrite the
  modified files, or restore them and run spectra update again.
```

---

## 7 · Exit codes

Unchanged from the 007 contract. What is new is only which conditions map onto them:

| Code | Name | Reached when |
| --- | --- | --- |
| 0 | `EXIT_OK` | Every attempted upgrade succeeded — including a run where integrations were skipped for want of authorization (FR-030) |
| 1 | `EXIT_DECLINED` | The user declined the **update plan** at step 5. Declining the *overwrite* is not this |
| 2 | `EXIT_USAGE` | Bad flag, including `--force` at the wrong level |
| 4 | `EXIT_DELEGATION` | Any **attempted** integration upgrade failed |
| 5 | `EXIT_PROJECT_STATE` | Not a Spec Kit project / Spectra not installed |
| 130 | interrupt | The user cancelled; the walk stopped where it was |

The load-bearing distinction: a declined overwrite produces skips, and **skips never reach the exit
code**. A project that cannot be fully updated still exits 0 having said exactly why.

---

## 8 · Supersession

`specs/007-unified-version-update/contracts/health-check.md` § "New delegation helpers" states:

> Neither passes `--force`. `specify integration upgrade` blocks on locally modified managed files by
> design, and silently overriding that on the user's behalf would discard their edits — exactly the class
> of destructive action that belongs behind Spec Kit's own gate rather than behind ours.

**Superseded by FR-026–FR-033.** The reasoning is kept in full; the conclusion is narrowed. What that
decision actually protects is the user's content, and it protected it by making the override unreachable.
This feature makes the override reachable *only* through a disclosure of the exact files plus an
authorization act performed in the same run — so the protected property ("no edits are discarded without
the user saying so") still holds, while the dead end the blanket refusal created (a project that cannot
be updated at all, with no explanation) is removed.

The word "silently" is what changed. Nothing here is silent.

**Implementation obligation**: edit that paragraph in the 007 contract to record the supersession and
point at this document. Leaving two contracts in disagreement is the failure mode this note exists to
prevent — the same treatment feature 009 gave its own reversal.
