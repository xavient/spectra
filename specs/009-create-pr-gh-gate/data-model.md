# Phase 1 Data Model: Create PR Gates on `gh`

**Feature**: `009-create-pr-gh-gate` | **Date**: 2026-08-19

The command holds no persistent data. These are the **conceptual entities the instructions reason about**
within one run — the vocabulary the command file must use consistently, and the states a run can end in.
Entities carried over unchanged from `002-open-pr` (source branch, target branch, promotion flow, pull
request) are not restated; only what this feature introduces or redefines appears here.

---

## Preflight

The ordered set of checks whose failure ends the run. Evaluated as the first action after the go-ahead
(FR-001), and never before the offer (FR-005).

| Field | Type | Notes |
|---|---|---|
| `gh_present` | bool | `command -v gh` succeeded |
| `gh_authenticated` | bool | `gh auth status --hostname github.com` exited 0. Not evaluated when `gh_present` is false |
| `remote_url` | string \| null | `git config --get remote.origin.url`; null when no remote is configured |
| `remote_host` | string \| null | Host parsed from `remote_url` — HTTPS and SSH forms both accepted |
| `owner` / `repo` | string \| null | Parsed only when `remote_host` is `github.com` |
| `remote_count` | int | Number of configured remotes |
| `is_fork` | bool | From `gh repo view --json isFork` — never inferred from the URL (FR-007) |
| `parent` | string \| null | From `gh repo view --json parent`; the upstream when `is_fork` |
| `default_branch` | string | From `gh repo view --json defaultBranchRef` |
| `viewer_permission` | string \| null | From `gh repo view --json viewerPermission`; null is "unknown", not "denied" |

**Evaluation order is normative** — each check is only meaningful once the previous one passed:

```text
gh_present → gh_authenticated → remote_url → remote_host == github.com → remote_count / is_fork
```

The last four fields come from the single structured query in
[contracts/gh-operations.md](./contracts/gh-operations.md) OP-2, which is why they are unavailable — and
irrelevant — when the first two checks fail.

---

## GateFailure

Produced when `Preflight` fails. Exactly one instance ends the run; there is no aggregation, because the
user acts on one remedy at a time.

| Field | Type | Notes |
|---|---|---|
| `kind` | enum | `gh_missing` · `gh_unauthenticated` · `remote_absent` · `remote_not_github` |
| `statement` | string | What was found, in the user's terms |
| `remedy` | string \| null | The single action that fixes it; null for the scope kinds |
| `may_name_gh_command` | bool | **false** for `gh_missing`, `remote_absent`, `remote_not_github` |

| `kind` | `statement` | `remedy` |
|---|---|---|
| `gh_missing` | The GitHub CLI is not installed | Install it — <https://cli.github.com> |
| `gh_unauthenticated` | `gh` is installed but not logged in to github.com | `gh auth login` |
| `remote_absent` | No Git remote is configured | *(scope statement — nothing to fix in the tool)* |
| `remote_not_github` | `origin` points at `<host>`; this version supports GitHub only | *(scope statement)* |

**Validation rules**:

- **V-1** — `gh_missing` MUST NOT be reported with a `gh` command in the output. Only the GitHub web
  interface may be named as an alternative (FR-003).
- **V-2** — `gh_unauthenticated` and `gh_missing` MUST produce different text (FR-002, SC-002).
- **V-3** — A `GateFailure` of any kind MUST be reached with zero mutations recorded (FR-004).
- **V-4** — The scope kinds MUST NOT print a manual `gh pr create` line (FR-006, SC-003).

---

## MutationState

The single fact that distinguishes "nothing happened" from "half of it happened". Tracked from the moment
the gate passes and reported verbatim in any failure after it.

| Value | Meaning |
|---|---|
| `none` | Nothing has reached the remote |
| `branch_pushed` | The source branch is on the remote; no pull request exists |
| `pr_open` | The pull request exists — terminal success |

Transitions are one-way: `none → branch_pushed → pr_open`. Each transition requires its own explicit user
confirmation (002 FR-001, FR-014; retained by FR-013).

---

## PostGateFailure

Produced when an outward action is refused **after** the gate passed. Unlike `GateFailure`, the work done
so far is not discarded (FR-010).

| Field | Type | Notes |
|---|---|---|
| `attempted` | enum | `push` · `pr_create` |
| `cause` | string | What `gh` or `git` reported, surfaced rather than paraphrased away |
| `mutation_state` | MutationState | Stated explicitly, always (FR-011) |
| `target_branch` | string | The base the command derived — the value the user needs to finish by hand |
| `manual_commands` | string[] | Runnable, because `gh` exists and is authenticated at this point |
| `presented_as_success` | bool | MUST be false (FR-010) |

**Validation rules**:

- **V-5** — `manual_commands` MUST include the derived `target_branch` (FR-010).
- **V-6** — `mutation_state` MUST be stated even when it is `none` (FR-011). Silence is the failure mode
  this rule exists to prevent.
- **V-7** — An exit code of 4 from any post-gate `gh` call MUST be reported as an authentication problem
  with the `gh auth login` remedy, not as a permission problem (research R-003).

---

## Run outcome

Every run ends in exactly one of these. The set is closed; the command file must not invent a sixth.

| Outcome | Reached when | Mutations |
|---|---|---|
| `declined` | The user declines the offer | none — the gate never runs (FR-005) |
| `gated` | `Preflight` failed | none (V-3) |
| `refused` | Source branch is `main`, detached, or non-spec (002 FR-005) | none |
| `existing_pr` | An open pull request already exists for the branch (002 FR-010) | none |
| `degraded` | `PostGateFailure` | `none` or `branch_pushed`, stated |
| `opened` | The pull request was created | `pr_open`, URL returned |

`gated` and `refused` are distinct on purpose: one is an environment problem with a remedy, the other is a
correctness refusal with no remedy but a different branch. Collapsing them would tell a user on `main` to
install `gh`.

---

## Requirement traceability

| Entity / rule | Requirements |
|---|---|
| `Preflight` evaluation order | FR-001, FR-005, FR-009 |
| `GateFailure.kind`, V-1, V-2 | FR-002, FR-003, SC-002, SC-003 |
| V-3 | FR-004, SC-001 |
| V-4 | FR-006 |
| `Preflight.is_fork`, `remote_count` | FR-007 |
| `MutationState` | FR-011 |
| `PostGateFailure`, V-5, V-6, V-7 | FR-010, FR-011, SC-004 |
| Run outcome set | FR-013 (nothing else changes) |
