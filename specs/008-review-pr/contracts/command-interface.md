# Contract: Command Interface

**Feature**: `008-review-pr` | **Command**: `speckit.spectra.review-pr`

The interface a reviewer sees. This is the contract the command file must honour; violations are
observable from a session transcript alone.

---

## Registration

| Property | Value | Enforced by |
|---|---|---|
| Command name | `speckit.spectra.review-pr` | Spec Kit validates `^speckit\.<extension-id>\.<command>$`; Principle III |
| File | `spectra/commands/review-pr.md` | Principle II — inside the single extension |
| Front matter | YAML with a `description` key | Principle III |
| Input mechanism | `$ARGUMENTS` | Principle III — never an agent-specific syntax |
| Manifest entry | `provides.commands[]` with `name`, `file`, `description` | Publishing standards |
| Hooks | none | research R-011 — on-demand only |

**Invocation differs by agent** and the command must not assume one form. Claude registers it as a skill
(`/speckit-spectra-review-pr`); kiro-cli keeps the dots (`/speckit.spectra.review-pr`). The command file
refers to itself by name, never by trigger syntax.

---

## Arguments

All optional. The command is fully functional with none.

| Argument | Effect |
|---|---|
| *(none)* | Offer the current branch's open PR first, then list open PRs for explicit choice (FR-004) |
| `<url>` | Review that pull request |
| `<number>` | Review that pull request in the current repository |
| `--since <revision>` | Delta re-review against a named prior revision (FR-039) |

Unrecognized arguments are noted briefly and ignored; the command continues with default behaviour
rather than failing. This mirrors `create-pr.md`'s established handling.

**Argument passing**: the reference is handed to `gh` unparsed (research R-001) — `gh` natively accepts
`<number> | <url> | <branch>`.

---

## The governing rule

> The only permitted mutation is publishing one review, after explicit confirmation.

The command MUST NOT modify source code, the spec, the plan, the tasks, or the constitution (FR-008),
and MUST NOT alter the working tree — including checking out the PR's branch — without explicit
permission (FR-007). Its only optional local write is the reviewer-requested review file (FR-038),
which defaults to off.

---

## Ordered flow and its gates

| Step | Gate | On failure |
|---|---|---|
| 1 | **Pre-flight** — `gh` installed and authenticated | **HARD STOP.** Distinguish missing binary from missing login, state the remedy, do not analyze (FR-001) |
| 2 | Resolve the target; pin `headRefOid` | Stop with an explanation |
| 3 | Detect self-review, fork, draft, existing own review | Never a stop — these adjust what is offered later |
| 4 | Gather metadata, file list, budget, artifacts at revision | Degrade with a declared limit; never refuse |
| 5 | Analyze — lens selection, traceability, guardrails, craft | — |
| 6 | Present ranked summary with a recommendation | — |
| 7 | **Selection gate** — nothing pre-selected | Empty/absent selection ⇒ publish nothing, terminal success (FR-023) |
| 8 | State accepted **and** dropped | Must precede any outward action (FR-025) |
| 9 | **Verdict gate** — reviewer chooses | Agent must not choose (FR-027). Blocker + approve ⇒ typed confirmation (FR-028) |
| 10 | **Preview gate** — show the exact body | No go-ahead ⇒ publish nothing (FR-031) |
| 11 | **Freshness gate** — re-read `headRefOid` | Moved ⇒ warn, offer re-analysis, do not publish (FR-032) |
| 12 | Publish one review; return the URL | Hand over the rendered body for manual posting (FR-035) |

Steps 1, 7, 9, 10, and 11 are **hard gates**. No outward action may occur unless all five have been
passed in order.

---

## Exit paths

Every path is enumerated. There is no unhandled state.

| Exit | Published? | Class |
|---|---|---|
| `gh` missing or unauthenticated | no | Hard stop with remedy |
| Target unresolvable | no | Stop with explanation |
| No open PRs to pick from | no | Clean informational stop, not an error |
| Reviewer picks nothing from the list | no | Clean stop |
| Empty selection | no | **Success** — the filter worked |
| No final go-ahead | no | **Success** — the gate worked |
| Revision moved before publishing | no | Warn plus re-analysis offer |
| Permission or fork restriction | no | Degrade: rendered body handed over (FR-035) |
| Published | **yes** | Success, URL returned |

A run that publishes nothing is not a failure. Four of the nine exits are deliberate no-publish
successes, which is the direct consequence of FR-023's "nothing pre-selected".

---

## Degradation policy

Two distinct behaviours that must not be conflated:

| Situation | Behaviour | Why |
|---|---|---|
| `gh` missing or unauthenticated | **Hard stop before analysis** | FR-001. Analysing first would waste the reviewer's time on a review that provably cannot be published, and the remedy is one command away |
| Any failure *after* pre-flight passed | **Degrade and hand over** | FR-035. The analysis is already done and has value; the reviewer can post it by hand |

This is a deliberate departure from `create-pr.md`, which degrades on a missing `gh` rather than
stopping. The difference is justified: `create-pr` can meaningfully print manual `git`/`gh` commands a
user can run verbatim, whereas a review's value is the *analysis*, which cannot be produced at all
without reading the PR through `gh`.

---

## Confirmation semantics

| Gate | Accepted input | Why this strength |
|---|---|---|
| Selection | Explicit finding numbers or an explicit `none`/`all` | Silence must not be read as consent (FR-023) |
| Verdict | One of three named values | The closed set prevents an invented verdict (FR-022) |
| Blocker override | **A typed confirmation, not a bare yes** | Approving over a known blocker can unblock a merge; the friction is proportional to the consequence (FR-028) |
| Final go-ahead | Explicit affirmative after seeing the exact body | Last reversible moment (FR-031) |

---

## Credential and trust posture

- The command holds **no credentials** and acts solely through the reviewer's existing `gh`
  authentication (FR-002).
- All pull request interaction goes through `gh` exclusively (FR-003) — the closed set is fixed in
  [gh-operations.md](./gh-operations.md).
- No telemetry, no new data path, no new trust boundary. Whatever governs the reviewer's coding agent
  and `gh` already governs this command.
- Nothing is persisted between runs (FR-026).
