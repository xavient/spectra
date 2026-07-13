# Feature Specification: Open PR

**Feature Branch**: `002-open-pr`

**Created**: 2026-06-24

**Status**: Draft

**Input**: User description: "@brds/open-pr.md"

## Clarifications

### Session 2026-06-24

- Q: Command naming / placement (standalone extension vs. part of `git`)? → A: Standalone `github` extension, command `speckit.github.create-pr`
- Q: Where is the promotion flow declared, and what is the precedence? → A: Read both the constitution's *Version Control & Branching Strategy* section and the `git` branching config; if they disagree, surface the conflict and ask the user (no silent precedence)
- Q: How is the post-implement offer surfaced? → A: The extension contributes an `after_implement` hook to the project when it is installed (offer-style/optional, like the `git` extension's hooks); direct invocation of `speckit.github.create-pr` remains the on-demand path
- Q: Push behavior when the source branch isn't on the remote? → A: Detect the unpushed branch, ask to push, and push automatically on confirmation, then open the PR
- Q: Should the PR open as a draft or ready-for-review by default? → A: Ready-for-review by default; draft available as an explicit opt-in option/flag

### Session 2026-06-25

- Q: Final extension/command naming (the original `speckit.open-pr` failed Spec Kit's required `speckit.{extension}.{command}` pattern)? → A: Extension id `github`, command `speckit.github.create-pr` (folder `github/`, command file `commands/create-pr.md`, Claude trigger `/speckit-github-create-pr`). This satisfies the naming pattern, so the earlier Principle III deviation no longer applies.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Open a PR after implementation, confirming the target when none is defined (Priority: P1)

After the `implement` step finishes on a spec branch, the agent offers to open a pull request for
the completed spec. The user accepts, the agent reads the constitution and branching strategy, finds
no promotion flow, proposes the repository's default branch as the target, asks the user to confirm
source → target, and on confirmation opens the PR and returns its link in chat.

**Why this priority**: This is the MVP. It delivers value for any GitHub project even when no
promotion flow is defined — turning "implementation complete" into "PR open" with a single
confirmation and zero manual `git`/`gh` commands.

**Independent Test**: On a completed spec branch in a GitHub repo with no promotion flow defined,
trigger the agent, accept the offer, confirm the proposed source → default-branch target, and verify
a correctly-targeted PR is opened and its URL is returned in chat.

**Acceptance Scenarios**:

1. **Given** a completed implementation on a spec branch, **When** `implement` finishes, **Then** the
   agent offers to open a PR and takes no Git or remote action until the user responds.
2. **Given** no promotion flow is defined, **When** the user accepts the offer, **Then** the agent
   proposes feat → default-branch and opens the PR only after explicit confirmation of source and
   target.
3. **Given** the PR is opened successfully, **When** the agent reports back, **Then** the chat message
   contains the PR URL.
4. **Given** the user declines the offer, **When** they respond "no," **Then** no branch is pushed and
   no PR is opened.

---

### User Story 2 - Honor the project's promotion strategy (Priority: P2)

On a project whose constitution or branching strategy defines a promotion flow (e.g.,
feat → dev → main), the agent automatically targets the correct next branch in that flow rather than
the default branch, states the target it derived and the rule it came from, and opens the PR.

**Why this priority**: It enforces the documented promotion strategy by construction, removing the
most common and most damaging mistake — PRs opened straight against `main` when an intermediate
branch applies. It builds on the P1 flow but is only relevant where a promotion flow exists.

**Independent Test**: On a project with a constitution defining feat → dev → main, run the agent from
a spec branch and verify the opened PR's base is `dev` (the next branch in the flow), and that the
agent stated `dev` was chosen because of the promotion flow.

**Acceptance Scenarios**:

1. **Given** a promotion flow of feat → dev → main, **When** the agent opens the PR from a spec
   branch, **Then** the PR base is `dev` (the next branch in the flow), not `main`.
2. **Given** a derived target, **When** the agent acts, **Then** it states which target it chose and
   why (citing the promotion flow), so the user can catch a wrong inference before the PR opens.
3. **Given** the promotion flow and an unambiguous derived target, **When** the agent runs, **Then**
   it does not additionally ask the user to pick a base it has already derived without ambiguity.

---

### User Story 3 - Decline now, open later on demand (Priority: P3)

The user declines the post-implement offer. Later, on the same spec branch, the user invokes the
agent directly, and it runs the same targeting and confirmation flow to open the PR without re-running
implementation.

**Why this priority**: It makes declining safe and non-destructive and ensures the loop can still be
closed later. Valuable but not required for the core "offer at the right moment" value.

**Independent Test**: Decline the offer, confirm nothing was pushed or opened, then invoke the agent
directly on the same spec branch and verify it determines the target and opens the PR exactly as it
would have immediately after `implement`.

**Acceptance Scenarios**:

1. **Given** the offer is declined, **When** the user responds "no," **Then** no branch is pushed and
   no PR is opened.
2. **Given** a later on-demand invocation on the spec branch, **When** the agent runs, **Then** it
   determines the target and opens the PR exactly as it would have immediately after `implement`.

---

### Edge Cases

- **`gh` not installed or not authenticated**: the agent does not fail opaquely; it explains the
  situation and provides the manual `gh`/`git` fallback, including the target it would have used.
- **Remote is not GitHub / no remote configured**: the agent detects this via remote detection and
  degrades gracefully rather than assuming GitHub.
- **A PR already exists for the source branch**: the agent returns the existing PR's link instead of
  opening a duplicate.
- **Run from `main`, a detached HEAD, or a non-spec branch**: the agent refuses to open a PR and
  explains why (one-branch-per-spec; there is nothing to propose).
- **Uncommitted or unpushed changes**: the agent surfaces them before opening, so the PR is not opened
  against an incomplete branch.
- **Target branch in the promotion flow does not exist** (e.g., `dev` is undefined): the agent
  surfaces this rather than silently retargeting `main` or creating the branch.
- **Constitution and branching config disagree** on the promotion flow: the agent surfaces the
  conflict and asks rather than silently choosing.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: After the `implement` step completes, the system MUST offer to open a PR for the
  completed spec and MUST NOT open one without the user's explicit go-ahead. The offer MUST be
  surfaced via an `after_implement` hook that the extension registers in the project's
  `.specify/extensions.yml` at install time (offer-style/optional, mirroring the `git` extension's
  hooks).
- **FR-002**: The system MUST read both the constitution's *Version Control & Branching Strategy*
  section and the `git` extension's branching config before determining the PR target branch.
- **FR-003**: When a promotion flow is defined (e.g., feat → dev → main), the system MUST target the
  correct next branch in that flow and MUST state which target it derived and why.
- **FR-004**: When no promotion flow is defined, the system MUST propose the repository's default
  branch as the target and MUST obtain explicit user confirmation of source and target before opening
  the PR.
- **FR-005**: The system MUST derive the PR source branch from the current spec branch and MUST NOT
  open a PR from `main`, a detached HEAD, or a non-spec branch.
- **FR-006**: The system MUST open the PR using the GitHub CLI (`gh`) and MUST return the resulting PR
  URL to the user in chat.
- **FR-007**: When `gh` is unavailable or unauthenticated, the remote is not GitHub, or no remote is
  configured, the system MUST degrade gracefully and explain the manual fallback (including the target
  it would have used) rather than failing silently or guessing.
- **FR-008**: The system MUST NOT modify source code, the spec, or the constitution; its only
  mutations MUST be the Git/remote actions required to open the PR (pushing the source branch,
  creating the PR).
- **FR-009**: The system MUST be packaged as a standalone, self-contained `github` extension exposing
  the agent-agnostic, namespaced command `speckit.github.create-pr`, and MUST run on whatever coding agent the
  team uses.
- **FR-010**: If an open PR already exists for the source branch, the system MUST detect it and return
  the existing PR link instead of opening a duplicate.
- **FR-011**: The system SHOULD derive the PR title and body from the spec (name, summary, and a link
  to the spec) so the PR is self-describing.
- **FR-012**: Before opening, the system SHOULD verify the source branch is committed and pushed, and
  surface uncommitted or unpushed changes that would make the PR incomplete.
- **FR-013**: Where the constitution's branching section and the `git` branching config disagree on
  the promotion flow, the system MUST surface the conflict and ask the user rather than silently
  applying a precedence or choosing a target.
- **FR-014**: If the source branch is not on the remote, the system MUST detect this, ask the user to
  push, and on confirmation push the branch automatically before opening the PR; it MUST NOT push
  without that confirmation.
- **FR-015**: The system SHOULD be invocable on demand (not only via the post-implement offer), so a
  user who declined earlier can open the PR later.
- **FR-016**: The system MUST open the PR as ready-for-review by default and MUST provide an explicit
  opt-in (option/flag) to open it as a draft instead.

### Key Entities *(include if feature involves data)*

- **Spec branch (source branch)**: the dedicated branch for the current spec, whose name equals the
  spec directory name (one-branch-per-spec). The PR proposes its changes.
- **Target / base branch**: the branch the PR is opened against — the next branch in the promotion
  flow when one is defined, otherwise the repository's default branch.
- **Promotion flow / strategy**: an ordered chain of branches a change is promoted through before
  release (e.g., feat → dev → main), declared in the constitution's *Version Control & Branching
  Strategy* section and/or a branching config.
- **Pull Request**: the request to merge the source branch into the target branch on GitHub, with a
  title and body derived from the spec and a returned URL.
- **Remote**: the configured Git remote, inspected to confirm it is GitHub and to resolve owner/repo.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: From a completed implementation, a user opens a PR in a single confirmation step, with
  zero manual `git`/`gh` commands in the default flow.
- **SC-002**: When a promotion flow is defined, 100% of PRs opened target the branch dictated by that
  flow (zero PRs mis-targeted to `main` when an intermediate branch applies).
- **SC-003**: When no promotion flow is defined, 100% of PRs are opened only after explicit user
  confirmation of the target (zero surprise targets).
- **SC-004**: The PR link is returned to the user in chat in 100% of successful runs.
- **SC-005**: Zero duplicate PRs are opened for a source branch that already has an open PR.
- **SC-006**: When `gh`, the remote, or network access is unavailable, 100% of runs explain the manual
  fallback rather than erroring opaquely.
- **SC-007**: Zero PRs are opened from a non-spec branch (`main` or a detached HEAD) as a result of the
  agent.

## Assumptions

- The project uses the Spec Kit structure (`.specify/` present) and the constitution's
  one-branch-per-spec convention, so the current branch is the spec branch and its name matches the
  spec directory.
- In the common case the `gh` CLI is installed and authenticated and the remote is GitHub; otherwise
  the agent degrades gracefully.
- Remote detection is available — the `git` extension's `speckit.git.remote`, or an equivalent
  `git config --get remote.origin.url` lookup.
- A promotion flow, when it exists, is expressed in the constitution's *Version Control & Branching
  Strategy* section and/or the `git` extension's branching config; both are read, and disagreement is
  treated as a conflict to surface rather than resolved by a fixed precedence.
- The post-implement offer is surfaced via an `after_implement` hook that the `github` extension
  contributes to `.specify/extensions.yml` when it is installed (the same hook mechanism the `git`
  extension already uses); direct invocation of the command is the on-demand alternative.
- Opening a PR may require pushing the source branch to the remote first.
- GitHub is the only supported provider in this version; non-GitHub providers (GitLab, Bitbucket,
  Azure DevOps) are out of scope and a possible later release.
- Merging, approving, or reviewing the PR is out of scope; the agent opens the PR only. Defining the
  promotion strategy, creating long-lived branches (e.g., `dev`), and CI/CD or branch-protection
  configuration are also out of scope.
