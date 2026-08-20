# Contract: Command Interface

**Feature**: `009-create-pr-gh-gate` | **Command**: `speckit.spectra.create-pr`

The interface a user sees. `002-open-pr` established this contract; this document **restates it with the
gate change applied** and marks every row that moves. Rows marked *unchanged* are reproduced so the
contract can be read on its own, not because they are being re-decided.

---

## Registration — unchanged

| Property | Value | Enforced by |
|---|---|---|
| Command name | `speckit.spectra.create-pr` | Spec Kit validates `^speckit\.<extension-id>\.<command>$`; Principle III |
| File | `spectra/commands/create-pr.md` | Principle II — inside the single extension |
| Front matter | YAML with a `description` key | Principle III |
| Input mechanism | `$ARGUMENTS` | Principle III |
| Manifest entry | `provides.commands[]` with `name`, `file`, `description` | Publishing standards |
| Hooks | `after_implement`, `optional: true` | 002 FR-001 — the hook **offers**, it never auto-opens |

---

## Arguments — unchanged

| Argument | Effect |
|---|---|
| *(none)* | Full default flow; opens a **ready-for-review** pull request |
| `--draft` | Open as a draft instead |
| `--base <branch>` | Override the derived base; still confirmed before opening |

Unrecognized arguments are noted briefly and ignored rather than treated as failures.

---

## The governing rule — extended

> The only permitted mutations are the Git/remote actions required to open the pull request — pushing the
> source branch and creating the pull request — each preceded by an explicit user go-ahead.

**Added by this feature**: all pull-request interaction goes through `gh` exclusively. `curl`, direct REST
calls, and any other route MUST NOT be used (FR-008). The closed set of calls is fixed in
[gh-operations.md](./gh-operations.md).

---

## Ordered flow and its gates

| Step | Gate | On failure | Status |
|---|---|---|---|
| 1 | **Offer** and await go-ahead | Decline ⇒ clean stop, nothing checked, nothing mutated (FR-005) | unchanged |
| 2 | **Pre-flight** — `gh` installed, `gh` authenticated | **HARD STOP.** Distinguish the two, state the one remedy that fits, mutate nothing (FR-001–FR-004) | **CHANGED — was "degrade gracefully"** |
| 3 | **Remote scope** — remote exists and is on `github.com` | **HARD STOP** with a GitHub-only scope statement; no `gh` fallback printed (FR-006) | **CHANGED — was degrade** |
| 4 | **Repository facts** — one structured query for default branch, fork status, parent, permission | Several remotes or a fork ⇒ **ask** which remote and base (FR-007, FR-009) | **CHANGED — was a URL-shape guess** |
| 5 | **Source-branch validation** — one branch per spec | Refuse: `main`, detached HEAD, or non-spec branch (002 FR-005) | unchanged |
| 6 | **Existing-PR detection** | An open PR exists ⇒ return its URL, open nothing (002 FR-010) | unchanged |
| 7 | **Target derivation** — promotion flow, else default branch | Conflict or missing target ⇒ surface and stop; never silently retarget `main` (002 FR-003, FR-013) | unchanged |
| 8 | **Push gate** — dirty tree surfaced; push only on confirmation | Refusal ⇒ post-gate degradation (FR-010, FR-011) | **CHANGED — failure path added** |
| 9 | **Create gate** — body on stdin, `--draft` only if requested | Refusal ⇒ post-gate degradation stating the mutation state (FR-010–FR-012) | **CHANGED — failure path added** |
| 10 | **Report** — URL, base branch, and the rule that derived it | — | unchanged |

Steps 2, 3, 8, and 9 are the gates that end or divert a run. Their **order is normative**: the `gh` gate
precedes every read of project context, so a run that cannot open a pull request never spends the user's
time deriving one (FR-001, SC-001).

**Why step 4 now precedes step 5**: the structured repository query supplies the default branch, which
source-branch validation needs to recognise "you are on the base branch". Previously that value came from
a `gh repo view` call in step 7 with a `git symbolic-ref` fallback for the `gh`-less case; the gate makes
the fallback dead code (research R-007).

---

## Exit paths

Every path is enumerated. There is no unhandled state.

| Exit | PR opened? | Class | Mutations |
|---|---|---|---|
| Offer declined | no | Clean stop | none |
| `gh` not installed | no | **Hard stop** — install remedy | none |
| `gh` not authenticated | no | **Hard stop** — `gh auth login` | none |
| No remote configured | no | **Hard stop** — scope statement | none |
| Remote not on `github.com` | no | **Hard stop** — scope statement | none |
| Several remotes / fork, user does not choose | no | Clean stop after asking | none |
| `main`, detached HEAD, or non-spec branch | no | Refusal with reason | none |
| Open PR already exists | no | **Success** — existing URL returned | none |
| Promotion-flow conflict, or derived target missing on the remote | no | Stop with the conflict surfaced | none |
| Push refused | no | **Degrade** — manual commands, state `none` | none |
| Creation refused | no | **Degrade** — manual commands, state `branch_pushed` | branch pushed |
| Pull request opened | **yes** | Success, URL returned | branch pushed, PR open |

Eleven of the twelve exits mutate nothing or are explicitly reported as partial. That accounting is the
point of FR-011: the user always knows which of the twelve they are in.

---

## Degradation policy — the replacement

Two behaviours, and the rule for telling them apart is **position relative to the gate**, not severity:

| Situation | Behaviour | Why |
|---|---|---|
| `gh` missing or unauthenticated | **Hard stop before any project read or remote call** | FR-001. The product is the pull request and the pull request needs `gh`. The remedy is one command; a partial run that ends in commands the user cannot execute is worse than a stop |
| Remote absent or not on `github.com` | **Hard stop with a scope statement, no `gh` fallback** | FR-006. There is no `gh` command that helps against a non-GitHub remote |
| Any refusal *after* the gate passed | **Degrade and hand over**, stating the mutation state | FR-010, FR-011. `gh` exists here, so the printed command runs; and the branch may already be pushed, which the user must be told |

> **Supersedes** `specs/008-review-pr/contracts/command-interface.md` §Degradation policy, which recorded
> `create-pr` degrading on a missing `gh` as a deliberate difference from `review-pr`. Both commands now
> hard-gate. What still differs between them is only what happens *after* the gate: `review-pr` hands over
> a rendered review body, `create-pr` hands over `git`/`gh` commands plus the mutation state.

---

## Confirmation semantics — unchanged

| Gate | Accepted input | Why this strength |
|---|---|---|
| The offer | Explicit acceptance | The hook offers; it never opens (002 FR-001) |
| Target confirmation | Explicit confirmation when the target was proposed rather than derived | Prevents a surprise base (002 FR-004) |
| Push | Explicit confirmation | First irreversible-ish step: it publishes a branch |
| Creation | Explicit confirmation | Opens something other people will be asked to review |

An unambiguously derived target is **stated, not re-asked** (002 FR-003) — the gate change does not soften
that.

---

## Message requirements introduced by this feature

Testable from a transcript alone:

| Rule | Requirement |
|---|---|
| The two `gh` failures produce different text | FR-002, SC-002 |
| A missing `gh` message contains no `gh …` command line | FR-003, SC-003 |
| A non-GitHub remote message contains no `gh …` command line | FR-006, SC-003 |
| A post-gate failure names the derived base branch | FR-010, SC-004 |
| A post-gate failure states whether the branch reached the remote | FR-011, SC-004 |
| A gate failure reports no mutation, because none occurred | FR-004, SC-001 |
