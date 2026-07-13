# Phase 0 Research: Open PR

All clarifications from `/speckit-clarify` (Session 2026-06-24) are already encoded in the spec. This
document resolves the remaining design unknowns surfaced in the BRD's open questions and the plan's
Technical Context, so Phase 1 can proceed without `NEEDS CLARIFICATION` markers.

## R1 — Base-branch targeting algorithm (promotion flow vs. default)

- **Decision**: Determine the target branch as follows. (1) Read the promotion flow from both the
  constitution's *Version Control & Branching Strategy* section and the `git` extension's branching
  config (`.specify/extensions/git/git-config.yml`). (2) If both define a flow and they **disagree**,
  surface the conflict and ask the user (FR-013) — do not apply a precedence. (3) If a single,
  unambiguous flow is defined (e.g., feat → dev → main), target the **next** branch after the spec
  branch's stage and state the rule it came from (FR-003), without asking the user to re-pick. (4) If
  **no** flow is defined, propose the repository's default branch (resolved via
  `gh repo view --json defaultBranchRef` or `git symbolic-ref refs/remotes/origin/HEAD`) and require
  explicit confirmation of source → target (FR-004).
- **Rationale**: Matches the clarified "read both, surface conflict" rule and the spec's promotion-flow
  semantics. Deriving "next stage" keeps the promotion strategy enforced by construction (SC-002).
- **Alternatives considered**: Constitution-only or config-only source (rejected in clarification —
  both are read). Fixed precedence on conflict (rejected — clarified to surface and ask).

## R2 — Promotion-flow representation

- **Decision**: Treat the promotion flow as an ordered list of branch names. In the constitution it is
  expressed in prose/list form under *Version Control & Branching Strategy* (the agent parses the
  ordered chain, e.g., "feat → dev → main"). In `git-config.yml` it is an optional key the agent reads
  if present. The current Spectra constitution defines **one-branch-per-spec with no promotion flow**,
  so the default-branch path (R1 step 4) is the live behavior today.
- **Rationale**: No new schema is imposed on the constitution; the agent reads what is written. The
  `git` config is the natural machine-readable home if a team formalizes a flow later.
- **Alternatives considered**: Inventing a strict YAML schema for the flow (rejected — out of scope;
  the agent reads existing human-authored strategy text, Principle IV).

## R3 — Source-branch validation (one-branch-per-spec)

- **Decision**: Derive the source branch from `git rev-parse --abbrev-ref HEAD`. Refuse to proceed if
  HEAD is detached, or the branch is the default/base branch (`main`), or it does not match a spec
  directory under `specs/` (the constitution's branch-name == spec-dir rule). Explain why and stop
  (FR-005, SC-007).
- **Rationale**: Guarantees the PR is always opened from a real spec branch and never from `main`.
- **Alternatives considered**: Trusting the current branch unconditionally (rejected — would allow PRs
  from `main`/detached HEAD).

## R4 — Existing-PR detection (no duplicates)

- **Decision**: Before opening, run `gh pr list --head <source-branch> --state open --json url` (or
  `gh pr view <branch>`). If an open PR exists for the source branch, return its URL instead of opening
  a new one (FR-010, SC-005).
- **Rationale**: `gh` already exposes head-branch filtering; cheapest reliable dedup signal.
- **Alternatives considered**: Searching by title (rejected — titles are not unique/stable).

## R5 — Push behavior

- **Decision**: Detect whether the source branch exists on the remote (`git ls-remote --heads origin
  <branch>` or upstream tracking). If not pushed (or has unpushed commits), surface this, ask the user
  to push, and on confirmation run `git push -u origin <branch>` before opening the PR. Never push
  without confirmation (FR-014). Also surface uncommitted changes before opening (FR-012).
- **Rationale**: Matches the clarified push behavior; keeps the single-confirmation default flow
  (SC-001) while honoring "no outward action without consent."
- **Alternatives considered**: Require manual push first (rejected in clarification); auto-push without
  confirmation (rejected — violates consent constraint).

## R6 — Opening the PR and draft default

- **Decision**: Open with `gh pr create --base <target> --head <source> --title <derived> --body
  <derived>`. PR is **ready-for-review by default**; a draft is an explicit opt-in (`--draft`, exposed
  via the command's `$ARGUMENTS`, e.g., a `--draft` token, mapping to `gh pr create --draft`) (FR-016).
  Title/body derive from the spec name, summary, and a link to the spec file (FR-011).
- **Rationale**: Matches the clarified draft-vs-ready decision; self-describing PRs satisfy reviewer
  needs.
- **Alternatives considered**: Draft by default / ask each time (rejected in clarification).

## R7 — Graceful degradation (gh / remote / network)

- **Decision**: Probe preconditions in order and degrade with a clear manual fallback (never fail
  opaquely) (FR-007, SC-006): (a) `gh` installed? (`command -v gh`); (b) `gh` authenticated?
  (`gh auth status`); (c) remote configured and GitHub? (parse `git config --get remote.origin.url`,
  confirm `github.com`, per `speckit.git.remote` behavior). On any failure, print the exact manual
  `git push` + `gh pr create` (or web-UI) commands the user can run, including the target branch the
  agent would have used.
- **Rationale**: Matches FR-007; reuses the proven remote-parsing logic from `speckit.git.remote`
  (re-implemented in-prompt per Principle II, see plan Complexity Tracking).
- **Alternatives considered**: Assuming GitHub (rejected — `speckit.git.remote` explicitly cautions
  against assuming the remote is GitHub).

## R8 — Offer mechanism (after_implement hook)

- **Decision**: Declare an `after_implement` hook in `github/extension.yml` under `hooks:`, `optional:
  true`, command `speckit.github.create-pr`, with an offer-style prompt. Spec Kit merges declared hooks into the
  project's `.specify/extensions.yml` at install time — exactly how the `git` extension contributes its
  hooks today. The command is also directly invocable on demand (FR-015).
- **Rationale**: Matches the clarification ("the extension contributes the hook when installed");
  consistent with the established `git` extension mechanism; `optional: true` preserves "offer, don't
  auto-fire" (FR-001).
- **Alternatives considered**: No hook / host-chained (rejected in clarification); mandatory hook
  (rejected — would auto-fire without an offer, violating FR-001).

## R9 — Effect classification

- **Decision**: `effect: read-write`. Opening a PR is an outward/remote action; Spectra's taxonomy has
  no distinct "remote action" category, and the constitution's constraints already classify this work
  as `read-write` with mandatory confirmation before any push/PR.
- **Rationale**: Consistent with constitution Constraints and the `adr`/`domain-analyzer` precedent.
- **Alternatives considered**: A new "remote-action" effect (deferred — taxonomy change is out of scope
  for this feature; noted as a possible future enhancement).

## R10 — Fork / multi-remote handling

- **Decision**: This version targets the common single-remote `origin`-is-GitHub case. When multiple
  remotes exist or `origin` is a fork, the agent surfaces the ambiguity and asks which remote/base to
  use rather than guessing. Full fork-workflow automation is out of scope for v1.0.0.
- **Rationale**: Keeps the MVP focused (BRD §5.2, §13) while never silently choosing a surprising
  remote/base (SC-003 spirit).
- **Alternatives considered**: Full fork automation (deferred to a later release per the BRD).
