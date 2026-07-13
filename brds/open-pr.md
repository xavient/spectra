# Business Requirements Document (BRD): Open PR

## Document Control

| Field             | Value                                                                                                                       |
| ----------------- | --------------------------------------------------------------------------------------------------------------------------- |
| BRD ID            | BRD-002                                                                                                                     |
| Title             | Open PR                                                                                                                     |
| Author            | Spectra / TELUS Digital                                                                                                     |
| Status            | Draft                                                                                                                      |
| Version           | 0.1.0                                                                                                                      |
| Created           | 2026-06-24                                                                                                                 |
| Last updated      | 2026-06-24                                                                                                                 |
| Related documents | `.specify/memory/constitution.md` (Version Control & Branching Strategy), `git` extension (`speckit.git.remote`), `/speckit-implement`, `brds/domain-analyzer.md` |

## 1. Executive Summary

The **Open PR** agent is a Spectra add-on (SDLC delivery step) that closes the loop on
spec-driven development: once the `implement` step finishes, it **offers** to open a pull request
for the completed spec. Before opening, it reads the project's **constitution** and **branching
strategy** to choose the correct base branch — **honoring a defined promotion flow** (e.g.,
feat → dev → main) automatically, or, when no promotion flow is defined, **confirming feat → main
with the user** before acting. It then opens the PR with the `gh` CLI and returns the PR link in
chat.

It removes the manual, error-prone last mile between "the code is done" and "a correctly-targeted
PR is open," so the agentic SDLC carries the work all the way to review instead of dropping the user
at the finish line.

## 2. Business Context & Problem Statement

Spectra automates the SDLC end to end — `specify` → `clarify` → `plan` → `tasks` → `implement` —
but the workflow stops at `implement`. Getting the finished work into review is left entirely to the
developer, by hand, and that last mile is where avoidable mistakes happen:

- **Forgotten or delayed PRs.** Nothing prompts the developer at the moment the work is actually
  ready, so PRs are opened late, inconsistently, or not at all.
- **Mis-targeted PRs.** Teams that promote through environments (feat → dev → main) frequently see
  PRs opened straight against `main`, bypassing the promotion flow. The correct base is project
  knowledge that lives in the constitution or branching config, not in the developer's head.
- **Inconsistent PR content.** Titles and descriptions are written from scratch each time, even
  though the spec already describes exactly what was built.
- **Repeated manual `git`/`gh` toil.** Pushing the branch, finding the right base, and crafting the
  `gh pr create` invocation is the same routine every spec — work the agent is well positioned to do.

The result is that the most automated part of the lifecycle ends with the least automated, most
error-prone step, weakening the very traceability (branch ↔ spec ↔ PR) the constitution's branching
strategy is designed to guarantee.

## 3. Business Objectives & Goals

- **G1 — Close the loop.** Turn "implementation complete" into "PR open" as a single, guided step
  offered at exactly the right moment.
- **G2 — Target the right branch.** Honor the project's promotion strategy automatically; never
  silently open a PR against a surprising base.
- **G3 — Keep humans in control.** Offer rather than auto-fire, and require explicit confirmation
  whenever the target is undefined or ambiguous.
- **G4 — Ground in project context.** Derive the source branch, target branch, and PR title/body
  from the constitution, the branching strategy, and the spec itself.
- **G5 — Degrade gracefully.** When `gh`, a GitHub remote, or network access is unavailable, explain
  the manual path instead of failing opaquely or guessing.

## 4. Stakeholders & Users

| Stakeholder / user                | Role in this product   | What they need from it                                                          |
| --------------------------------- | ---------------------- | ------------------------------------------------------------------------------- |
| Developer / operator              | Primary user           | Is offered a PR at the right moment; gets a correctly-targeted PR opened with minimal input, and the link back. |
| Reviewers / approvers             | Downstream consumers   | A consistent, self-describing PR that targets the correct branch in the promotion flow. |
| Engineering leads                 | Oversight              | Confidence that PRs respect the documented branching/promotion strategy by construction. |
| Constitution & branching strategy | Source of truth (input)| Read by the agent to determine the correct base branch and whether a promotion flow exists. |
| `git` extension                   | Capability provider    | Supplies remote detection and the post-implement hook the offer is surfaced through. |

## 5. Scope

### 5.1 In Scope

- **Offer to open a PR after `implement`** completes, at the moment the work is ready — and proceed
  only on the user's go-ahead.
- **Read the constitution and branching strategy** to determine whether a promotion flow is defined
  and what the correct base (target) branch is.
- **Honor a defined promotion flow** (e.g., feat → dev → main) by targeting the correct next branch
  in that flow, and stating which target was derived and why.
- **Confirm the target when no promotion flow is defined**, proposing the repository's default base
  (feat → main) and requiring explicit user confirmation of source and target before acting.
- **Derive the source branch** from the current spec branch (one-branch-per-spec) and **derive the
  PR title/body** from the spec.
- **Open the PR using `gh`** and **return the PR URL** to the user in chat.
- **Detect an existing open PR** for the source branch and return its link instead of opening a duplicate.
- **Degrade gracefully** when `gh`/remote/network is unavailable, explaining the manual fallback.
- Be **invocable on demand**, so a user who declined the post-implement offer can open the PR later.

### 5.2 Out of Scope

- **Merging, approving, or reviewing the PR.** The agent opens the PR; review and merge belong to
  reviewers and the platform.
- **Defining the promotion strategy.** The agent *reads and honors* the strategy; authoring it is the
  constitution's / Guardrails agent's responsibility.
- **Creating environments or long-lived branches** (e.g., creating `dev`). It targets branches that
  exist; missing target branches are surfaced, not created.
- **CI/CD configuration, status checks, or branch-protection rules.** Those are owned by the platform
  and downstream tooling.
- **Writing source code or editing the spec/constitution.** The agent's only mutations are
  Git/remote actions required to open the PR (pushing the source branch, creating the PR).
- **Non-GitHub providers** (GitLab, Bitbucket, Azure DevOps) in this version. `gh` + GitHub is the
  target; other providers are a possible later release.

## 6. User Journeys *(feeds the spec's prioritized user stories)*

### Journey 1 — Open a PR after implementation, confirming the target when none is defined (Priority: P1)

- **Actor:** Developer / operator
- **Trigger:** The `implement` step completes on a spec branch; the agent offers to open a PR.
- **Outcome / value:** With one confirmation, a correctly-targeted PR is opened against the default
  branch and its link is returned — no manual `git`/`gh` work. This is the MVP: it delivers value for
  any GitHub project even when no promotion flow is defined.
- **Flow:**
  1. Implementation finishes; the agent offers to open a PR for the completed spec.
  2. The user accepts.
  3. The agent reads the constitution and branching strategy and finds **no promotion flow**.
  4. It identifies the current spec branch as the source and proposes the repository's default branch
     (e.g., `main`) as the target, and asks the user to confirm source → target.
  5. On confirmation, it opens the PR with `gh` (pushing the source branch first if needed) using a
     title/body derived from the spec.
  6. It returns the PR URL in chat.
- **Acceptance:**
  - **Given** a completed implementation on a spec branch, **When** `implement` finishes, **Then** the
    agent offers to open a PR and does nothing further until the user responds.
  - **Given** no promotion flow is defined, **When** the user accepts, **Then** the agent proposes
    feat → default-branch and opens the PR only after explicit confirmation of source and target.
  - **Given** the PR is opened successfully, **When** the agent reports back, **Then** the chat message
    contains the PR URL.

### Journey 2 — Honor the project's promotion strategy (Priority: P2)

- **Actor:** Developer / operator on a project with a defined promotion flow
- **Trigger:** The agent runs where the constitution / branching strategy defines a promotion flow
  (e.g., feat → dev → main).
- **Outcome / value:** The PR automatically targets the **correct next branch** in the flow (e.g.,
  `dev`, not `main`), so the promotion strategy is enforced by construction rather than relying on the
  developer to remember it.
- **Flow:**
  1. The agent reads the constitution and branching strategy and detects a promotion flow.
  2. It determines the source (current spec branch) and the correct next target in the flow.
  3. It states the derived target and the rule it came from.
  4. It opens the PR against that target with `gh` and returns the link.
- **Acceptance:**
  - **Given** a promotion flow of feat → dev → main, **When** the agent opens the PR from a spec
    branch, **Then** the PR base is `dev` (the next branch in the flow), not `main`.
  - **Given** a derived target, **When** the agent acts, **Then** it states which target it chose and
    why (citing the promotion flow), so the user can catch a wrong inference before it opens.
  - **Given** the promotion flow and a clean run, **When** the user has already confirmed the flow,
    **Then** the agent does not additionally ask the user to pick a base it has unambiguously derived.

### Journey 3 — Decline now, open later on demand (Priority: P3)

- **Actor:** Developer / operator
- **Trigger:** The user declines the post-implement offer, then later decides to open the PR.
- **Outcome / value:** Declining is safe and non-destructive, and the PR can still be opened later via
  the same agent without re-running implementation.
- **Flow:**
  1. The agent offers to open a PR; the user declines.
  2. The agent takes no Git/remote action and notes that the PR can be opened later by invoking the
     command directly.
  3. Later, the user invokes the agent on the same spec branch and it runs the same targeting and
     confirmation flow.
- **Acceptance:**
  - **Given** the offer is declined, **When** the user responds "no," **Then** no branch is pushed and
    no PR is opened.
  - **Given** a later on-demand invocation on the spec branch, **When** the agent runs, **Then** it
    determines the target and opens the PR exactly as it would have immediately after `implement`.

### Edge Cases

- **`gh` not installed or not authenticated.** The agent does not fail opaquely; it explains the
  situation and provides the manual `gh`/`git` fallback (and the target it would have used).
- **Remote is not GitHub / no remote configured.** The agent detects this (via remote detection) and
  degrades gracefully rather than assuming GitHub.
- **A PR already exists for the source branch.** The agent returns the existing PR's link instead of
  opening a duplicate.
- **Run from `main`, a detached HEAD, or a non-spec branch.** The agent refuses to open a PR from a
  base/non-spec branch and explains why (one-branch-per-spec; nothing to propose).
- **Uncommitted or unpushed changes.** The agent surfaces them before opening, so the PR is not opened
  against an incomplete branch.
- **Target branch in the promotion flow does not exist** (e.g., `dev` is undefined). The agent
  surfaces this rather than silently retargeting `main` or creating the branch.
- **Constitution and branching config disagree** on the promotion flow. The agent surfaces the
  conflict and asks rather than silently choosing.

## 7. Business Requirements

| ID    | Requirement                                                                                                                                          | Priority |
| ----- | ---------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| BR-01 | After the `implement` step completes, the agent MUST offer to open a PR and MUST NOT open one without the user's explicit go-ahead.                  | P1       |
| BR-02 | The agent MUST read the project's constitution and branching strategy before determining the PR target branch.                                       | P1       |
| BR-03 | When a promotion flow is defined (e.g., feat → dev → main), the agent MUST target the correct next branch in that flow and MUST state which target it derived and why. | P1       |
| BR-04 | When no promotion flow is defined, the agent MUST propose the repository's default branch as the target and MUST obtain explicit user confirmation of source and target before opening the PR. | P1       |
| BR-05 | The agent MUST open the PR using `gh` and MUST return the resulting PR URL to the user in chat.                                                       | P1       |
| BR-06 | The agent MUST derive the PR source branch from the current spec branch and MUST NOT open a PR from `main`, a detached HEAD, or a non-spec branch.    | P1       |
| BR-07 | If `gh` is unavailable/unauthenticated, the remote is not GitHub, or no remote is configured, the agent MUST degrade gracefully and explain the manual fallback rather than failing silently or guessing. | P1       |
| BR-08 | The agent MUST NOT modify source code, the spec, or the constitution; its only mutations are the Git/remote actions required to open the PR (pushing the source branch, creating the PR). | P1       |
| BR-09 | The agent MUST operate as an agent-agnostic command and run on whatever coding agent the team uses.                                                   | P1       |
| BR-10 | If an open PR already exists for the source branch, the agent MUST detect it and return the existing PR link instead of opening a duplicate.          | P2       |
| BR-11 | The agent SHOULD derive the PR title and body from the spec (name, summary, and a link to the spec) so the PR is self-describing.                      | P2       |
| BR-12 | Before opening, the agent SHOULD verify the source branch is committed and pushed, and surface uncommitted/unpushed changes that would make the PR incomplete. | P2       |
| BR-13 | Where the constitution and a separate branching/promotion config disagree, the agent MUST surface the conflict rather than silently choosing a target. | P2       |
| BR-14 | If pushing the source branch to the remote is required to open the PR, the agent SHOULD confirm before pushing.                                        | P2       |
| BR-15 | The agent SHOULD be invocable on demand (not only via the post-implement offer), so a user who declined earlier can open the PR later.                 | P3       |

## 8. Success Metrics & Measurable Outcomes

- **SC-01** — From a completed implementation, a user opens a PR in a single confirmation step, with
  zero manual `git`/`gh` commands in the default flow.
- **SC-02** — When a promotion flow is defined, 100% of PRs opened target the branch dictated by that
  flow (zero PRs mis-targeted to `main` when an intermediate branch applies).
- **SC-03** — When no promotion flow is defined, 100% of PRs are opened only after explicit user
  confirmation of the target (zero surprise targets).
- **SC-04** — The PR link is returned to the user in chat in 100% of successful runs.
- **SC-05** — Zero duplicate PRs are opened for a source branch that already has an open PR.
- **SC-06** — When `gh`/remote/network is unavailable, 100% of runs explain the manual fallback rather
  than erroring opaquely.
- **SC-07** — The agent is never the cause of a PR opened from a non-spec branch (zero PRs opened from
  `main` or a detached HEAD).

## 9. Assumptions

- The project uses the Spec Kit structure (`.specify/` present) and the constitution's
  one-branch-per-spec convention, so the current branch is the spec branch and its name matches the
  spec directory.
- The `gh` CLI is installed and authenticated and the remote is GitHub in the common case; otherwise
  the agent degrades gracefully.
- Remote detection is available (the `git` extension's `speckit.git.remote`, or an equivalent
  `git config --get remote.origin.url` lookup).
- A promotion flow, when it exists, is expressed in the constitution's *Version Control & Branching
  Strategy* section and/or a branching config the agent can read.
- The post-implement offer is surfaced via an `after_implement` hook (the same hook mechanism the
  `git` extension already uses) or by direct invocation of the command.
- Opening a PR may require pushing the source branch to the remote first.

## 10. Constraints

- Must conform to Spectra's constitution: **self-contained extension** (Principle II),
  **agent-agnostic, namespaced command** using `$ARGUMENTS` (Principle III), and **context-aware**
  reading of real project state — constitution, branching strategy, current branch, remote
  (Principle IV).
- The extension performs **outward/remote actions** (pushing a branch, creating a PR via `gh`); its
  declared `effect` is **read-write**, and any push or PR creation MUST follow explicit user
  confirmation (BR-01, BR-04, BR-14).
- Requires the `gh` CLI and network access at runtime; behavior MUST degrade gracefully without them.
- Publishing the extension requires regenerating the distribution site (Principle V) — a build-time
  constraint, not a runtime behavior.

## 11. Dependencies

- **Upstream (trigger):** the `implement` step / `after_implement` hook, which surfaces the offer.
- **Input:** the constitution's *Version Control & Branching Strategy* section and/or branching
  config (promotion flow); the current branch; the spec (for title/body).
- **Capability:** Git remote detection — reuses the `git` extension's `speckit.git.remote` (or an
  equivalent) to confirm the remote is GitHub and resolve owner/repo.
- **External tool (output):** the `gh` CLI, which performs the PR creation against GitHub.

## 12. Risks & Mitigations

| Risk                                                          | Impact | Likelihood | Mitigation                                                                       |
| ------------------------------------------------------------- | ------ | ---------- | -------------------------------------------------------------------------------- |
| PR opened against the wrong base (e.g., `main` despite a promotion flow) | H  | M          | Read constitution + config first; honor the flow; state the derived target (BR-02, BR-03). |
| Outward action (push / PR) taken without consent              | H      | L          | Offer rather than auto-fire; explicit confirmation before push/open (BR-01, BR-04, BR-14). |
| `gh` not installed/authenticated or remote not GitHub         | M      | M          | Graceful degradation with a clear manual fallback (BR-07).                       |
| Duplicate PRs for the same branch                             | M      | M          | Detect an existing open PR and return its link (BR-10).                          |
| PR opened from a non-spec branch (e.g., `main`, detached HEAD)| M      | L          | Derive source from the spec branch; refuse otherwise (BR-06).                    |
| Ambiguous/conflicting strategy (constitution vs. config)      | M      | M          | Surface the conflict and ask rather than guess (BR-13).                          |
| Target branch in the promotion flow doesn't exist             | M      | L          | Surface the missing branch; never silently retarget or create it.                |

## 13. Open Questions

- **Command naming / placement** — confirm the namespaced command. Options: a standalone extension
  `open-pr` with verb (e.g., `speckit.open-pr.open` or `speckit.open-pr.create`), or a command inside
  the existing `git` extension (e.g., `speckit.git.pr`) since it reuses remote detection. Which is
  canonical?
- **Where is the promotion flow declared?** Constitution section only, a `git`/branching config key,
  or both — and what is the precedence/lookup order when they differ?
- **Push behavior** — should the agent push the source branch automatically (after confirmation) when
  it isn't on the remote, or require the user to push first?
- **Offer mechanism** — register an `after_implement` hook in `.specify/extensions.yml`, or rely on the
  host workflow to chain the command after `implement`?
- **Draft vs. ready PR** — should the PR open as a draft by default?
- **Effect taxonomy** — opening a PR is an outward/remote action; is `read-write` the right
  classification, or is a distinct "remote action" effect category warranted?
- **Fork / multi-remote workflows** — how should the source remote and base be chosen when `origin` is
  a fork or multiple remotes exist?

## 14. Glossary

| Term                       | Definition                                                                                                  |
| -------------------------- | ----------------------------------------------------------------------------------------------------------- |
| PR (Pull Request)          | A request to merge one branch into another on the hosting platform (here, GitHub via `gh`).                 |
| Promotion flow / strategy  | An ordered chain of branches a change is promoted through before release (e.g., feat → dev → main).         |
| Spec branch / feature branch | The dedicated branch for a single spec; per the constitution, its name equals the spec directory name.    |
| Base / target branch       | The branch a PR is opened against (merged into).                                                            |
| Source branch              | The branch whose changes the PR proposes (here, the current spec branch).                                   |
| Default branch             | The repository's primary branch (commonly `main`), used as the target when no promotion flow is defined.    |
| `gh`                       | The GitHub CLI used to create the PR.                                                                       |
| `after_implement` hook     | The Spec Kit hook fired after the `implement` step, used to surface the offer.                              |
| SDD                        | Spec-Driven Development — the `specify` → `clarify` → `plan` → `tasks` → `implement` workflow Spectra ships. |
