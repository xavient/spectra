# Feature Specification: Create PR Gates on `gh`

**Feature Branch**: `009-create-pr-gh-gate`

**Created**: 2026-08-19

**Status**: Implemented

**Input**: User description: "Take a look at `review-pr` command and how that relies on `gh`. We want to
do the same for `create-pr` — both commands rely on `gh` being available and authenticated."

Both shipped GitHub commands depend on the same tool, and until now they disagreed about what to do
when it is missing. `speckit.spectra.review-pr` treats an unusable `gh` as a **hard stop** with a named
remedy. `speckit.spectra.create-pr` treats it as a **graceful degradation**, printing a manual
`git push` + `gh pr create` fallback. This feature makes `create-pr` gate the way `review-pr` does, and
moves the manual fallback to the place where it is actually usable: failures that happen *after* the
gate.

## Clarifications

### Session 2026-08-19

- Q: Hard gate, or keep `create-pr`'s graceful degradation? → A: **Hard gate**, matching `review-pr`.
  The published justification for degrading was that `create-pr` can still print a useful manual path,
  but that path instructs the user to run `gh pr create` — the very command they do not have — and the
  duplicate-PR check cannot run either, so the "fallback" can walk the user into a second pull request.
- Q: Does the non-GitHub / missing-remote case also become a stop? → A: Yes. It stops with a statement
  that the command is GitHub-only. It MUST NOT print a `gh` fallback, because there is nothing `gh` can
  do with a non-GitHub remote.
- Q: Does the gate run before the post-`implement` offer, or after the user accepts? → A: **After.**
  The offer costs nothing and a user who declines never needed `gh`. Gating before the offer would turn
  every `implement` on a machine without `gh` into an error the user did not ask for.
- Q: Where does the manual fallback survive? → A: In post-gate failures only — a refused push, a
  protected base branch, a fork restriction, an insufficient token. There, `gh` exists and the printed
  command is runnable.
- Q: What version bump does this carry? → A: **MINOR** (`1.4.0` → `1.5.0`). A shipped command's
  behaviour changes, which Constitution Principle VI requires be published; no argument, no output
  contract, and no command name changes.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - An unusable `gh` stops the command with the remedy that fits (Priority: P1)

A developer finishes `implement` and accepts the offer to open a pull request. `gh` is either not
installed on the machine or installed but not logged in. Instead of a partial run that ends in a list
of commands they cannot execute, the command stops immediately — before it reads the constitution,
before it validates the branch, before it touches the remote — and tells them exactly one thing to do:
install the GitHub CLI, or run `gh auth login`.

**Why this priority**: This is the feature. It removes the one behaviour that made the two GitHub
commands disagree about their shared dependency, and it removes a fallback that could produce a
duplicate pull request. Shipped alone it delivers the whole change.

**Independent Test**: Run the command with `gh` off `PATH`, then again while logged out. Verify each run
stops before any target derivation or remote mutation, that the two messages differ, and that neither
tells the user to run a `gh` command they cannot run.

**Acceptance Scenarios**:

1. **Given** `gh` is not installed, **When** the user accepts the offer to open a pull request,
   **Then** the command stops, states that the GitHub CLI is not installed, points at the official
   install location, and performs no Git or remote action.
2. **Given** `gh` is installed but not authenticated, **When** the user accepts the offer, **Then** the
   command stops and names `gh auth login` as the remedy — a different message from the missing-binary
   case.
3. **Given** either failure, **When** the command stops, **Then** it has not pushed the branch, has not
   derived a target branch, and has not opened anything.
4. **Given** `gh` is unavailable, **When** the command explains the situation, **Then** the only
   alternative route it names is the GitHub web interface — never a `gh` command.
5. **Given** the post-`implement` offer is made on a machine with no `gh` at all, **When** the user
   declines the offer, **Then** the command ends silently with no gate error, because the gate belongs
   after the go-ahead.

---

### User Story 2 - A failure after the gate hands over a runnable manual path (Priority: P2)

`gh` is present and authenticated, the target branch is derived, the user confirms — and the outward
action is refused: the base branch is protected, the token cannot push to the repository, or the pull
request is on a fork the user cannot open against. The work already done is not thrown away. The
command reports what failed, hands over the exact commands to finish by hand including the target
branch it derived, and states plainly whether the branch was already pushed.

**Why this priority**: This is where the fallback text belongs, and it is the gap the old design left
open — `create-pr` had no instructions for a failure *after* the gate, even though it mutates the remote
by then. It is P2 because Story 1 stands without it, but a partial mutation left unexplained is the
worst outcome the command can produce.

**Independent Test**: Point the command at a repository whose base branch rejects the push or whose
token cannot open pull requests. Verify the run states what failed, whether the push landed, and gives a
command the user can actually run.

**Acceptance Scenarios**:

1. **Given** an authenticated `gh` and a refused pull-request creation, **When** the command reports
   back, **Then** it names the failure, gives the manual `gh pr create` line including the derived base
   branch, and does not present the run as a success.
2. **Given** the source branch was pushed and creation then failed, **When** the command reports back,
   **Then** it states explicitly that the branch is on the remote and no pull request exists.
3. **Given** the push itself was refused, **When** the command reports back, **Then** it states that
   nothing reached the remote.

---

### User Story 3 - A non-GitHub remote stops honestly (Priority: P3)

A developer runs the command in a repository whose `origin` is GitLab, or which has no remote at all.
The command does not guess that it is GitHub, and does not offer a `gh` fallback that could not work. It
states that this version supports GitHub only, names what it found, and stops.

**Why this priority**: It closes the last path by which the old degradation could print unusable
instructions. It is P3 because it affects only projects the command was never able to serve.

**Independent Test**: Run in a repository with a GitLab `origin`, then in one with no remote. Verify
both stop with a GitHub-only statement and no `gh` command in the output.

**Acceptance Scenarios**:

1. **Given** an `origin` that is not on `github.com`, **When** the command runs, **Then** it stops,
   names the host it found, states that GitHub is the only supported provider in this version, and
   prints no `gh` fallback command.
2. **Given** no remote is configured, **When** the command runs, **Then** it stops and says so.
3. **Given** several remotes, or an `origin` that is a fork, **When** the command runs, **Then** it asks
   the user which remote and base to use rather than guessing — and bases the fork determination on
   structured repository data, not on the shape of the URL.

---

### Edge Cases

- **An expired or revoked token**: `gh` is installed and `gh auth status` fails — treated exactly as
  the unauthenticated case, with the same remedy.
- **The offer is declined**: the gate never runs. Nothing is checked, nothing is reported, nothing
  mutates.
- **GitHub Enterprise**: a remote on a host other than `github.com` stops as a non-GitHub remote.
  Enterprise support is out of scope for this release and is named as such rather than half-attempted.
- **Authenticated but unauthorized**: the gate passes and the refusal surfaces later, so it is a
  post-gate degradation, not a gate failure.
- **Network loss after the gate**: the same path as any other post-gate failure — report, hand over the
  manual command, state the mutation state.
- **A spec body carrying backticks, quotes, or newlines**: reaches the pull request unaltered, because
  the body is never passed as a shell argument.

## Requirements *(mandatory)*

### Functional Requirements

#### The gate

- **FR-001**: The `gh` pre-flight check MUST be the first action the command takes after the user's
  go-ahead — before source-branch validation, duplicate detection, reading the constitution or branching
  config, target derivation, and any Git or remote command. A failed check MUST stop the run.
- **FR-002**: The check MUST distinguish **not installed** from **installed but not authenticated**, and
  MUST state the single remedy that fits: the official GitHub CLI install location for the former,
  `gh auth login` for the latter.
- **FR-003**: When `gh` is unavailable, the stop message MUST NOT instruct the user to run any `gh`
  command. The only alternative route it may name is the GitHub web interface.
- **FR-004**: A failed gate MUST leave zero mutations: no push, no branch created, no pull request, and
  no file written.
- **FR-005**: The gate MUST NOT be applied before the post-`implement` offer. A declined offer MUST end
  the run without reporting a gate failure.

#### Scope of the remote

- **FR-006**: A missing remote, or a remote whose host is not `github.com`, MUST stop the run with a
  statement that this version supports GitHub only, naming what was found. It MUST NOT print a `gh`
  fallback command.
- **FR-007**: Several configured remotes, or an `origin` that is a fork, MUST be resolved by asking the
  user which remote and base to use. Fork status MUST be read from structured repository data rather
  than inferred from the remote URL.

#### `gh` is the only route

- **FR-008**: All pull-request interaction MUST go through `gh`. `curl`, direct REST calls, and any
  other route MUST NOT be used.
- **FR-009**: The repository facts the command needs — default branch, fork status, and parent
  repository — MUST be read in one structured `gh` query rather than derived from separate ad-hoc
  probes.

#### After the gate

- **FR-010**: Once the gate has passed, a refused push or a refused pull-request creation MUST degrade
  rather than fail opaquely: the command MUST name what failed, hand over the manual commands to finish
  by hand including the derived target branch, and MUST NOT present the run as successful.
- **FR-011**: A post-gate failure MUST state the mutation state explicitly — whether the source branch
  reached the remote — so a partial outcome is never left implicit.
- **FR-012**: The pull-request body MUST be passed to `gh` on standard input rather than as a
  command-line argument, so spec-derived prose containing backticks, quotes, or newlines cannot be
  mangled by shell escaping.

#### Continuity and publication

- **FR-013**: Every other behaviour specified for the command MUST be unchanged: the offer-first flow,
  explicit confirmation before each of the push and the creation, refusal to open from `main`, a
  detached HEAD, or a non-spec branch, existing-PR detection, target derivation from the promotion flow
  with conflicts surfaced rather than resolved, `--draft` and `--base`, and the returned pull-request
  URL.
- **FR-014**: `gh` MUST remain declared as an **optional** tool in the extension manifest, because the
  commands that never touch GitHub must stay installable without it. The manifest MUST document that
  both GitHub commands now hard-gate on `gh`.
- **FR-015**: Every artifact that describes the command's `gh` behaviour MUST be updated in the same
  change — the manifest, the changelog, the extension README, the agent roster prose, the catalog, the
  published package, and the landing page — so no document claims the superseded behaviour
  (Constitution Principle V).

### Key Entities *(include if feature involves data)*

- **Pre-flight gate**: the ordered pair of checks — `gh` present, `gh` authenticated — whose failure
  ends the run. Carries the failure kind and the single remedy that matches it.
- **Gate failure kind**: one of *not installed*, *not authenticated*, *remote absent*, *remote not
  GitHub*. Each maps to exactly one remedy or statement of scope.
- **Post-gate failure**: a refusal of an outward action after the gate passed. Carries what was
  attempted, what failed, the mutation state, and the manual command that completes the work.
- **Mutation state**: whether the source branch reached the remote at the moment of a failure — the fact
  that distinguishes "nothing happened" from "half of it happened".

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In 100% of runs where `gh` is missing or unauthenticated, the command stops before any
  target derivation and before any Git or remote mutation.
- **SC-002**: The two `gh` failures produce different messages, each naming exactly one remedy.
- **SC-003**: Zero runs print a `gh` command while `gh` is unavailable, and zero runs print a `gh`
  fallback for a non-GitHub remote.
- **SC-004**: In 100% of post-gate failures the user is left with the derived target branch, a runnable
  manual command, and an explicit statement of whether the branch was pushed.
- **SC-005**: A pull-request body containing backticks, quotes, and newlines reaches the pull request
  unaltered.
- **SC-006**: Zero shipped documents describe `create-pr` as degrading when `gh` is unavailable; every
  document that mentions the pre-flight behaviour of the two GitHub commands describes it identically.
- **SC-007**: Every functional requirement of `002-open-pr` other than the superseded FR-007 still
  holds after the change.

## Assumptions

- The common case is unchanged: `gh` is installed, authenticated, and the remote is GitHub, so the gate
  is invisible to most runs.
- A user who has no `gh` is one command away from having it; a stop with the right remedy is therefore
  more useful than a partial run.
- The value of `create-pr` is the pull request itself, not the analysis it performs on the way there.
  This is what makes a hard gate correct here for the same reason it is correct in `review-pr`, where
  the value *is* the analysis and it needs `gh` to exist.
- `gh` remains a runtime dependency of the command, not an install-time dependency of the extension.
- GitHub is still the only supported provider; nothing in this change moves toward GitLab, Bitbucket,
  Azure DevOps, or GitHub Enterprise.
- The behaviour lives entirely in one command file — the change is to instructions, not to code — so
  "testing" means executing the documented scenarios against a real repository, plus the repository's
  own sync and roster checks.

## Supersedes

This feature changes decisions recorded in earlier specs. Those documents stay as history; this section
is the authoritative record of what no longer applies.

| Artifact | What it said | Status |
| --- | --- | --- |
| `specs/002-open-pr/spec.md` **FR-007** | `gh` unavailable, unauthenticated, or a non-GitHub remote MUST degrade gracefully and explain the manual fallback | **Superseded** by FR-001–FR-006 and FR-010 — the gate stops; the fallback survives only after the gate |
| `specs/002-open-pr/spec.md` **SC-006** | 100% of runs without `gh` explain the manual fallback | **Superseded** by SC-001–SC-004 |
| `specs/002-open-pr/quickstart.md` **S6** | "Graceful degradation (no `gh` / non-GitHub remote)" scenario | **Superseded** by this feature's quickstart scenarios |
| `specs/008-review-pr/contracts/command-interface.md` §Degradation policy | Justifies `create-pr` degrading where `review-pr` stops | **Superseded** — both hard-gate; the justification for the split no longer holds |
| `specs/008-review-pr/research.md` **R-009** | Records the two commands' differing treatment of a missing `gh` | **Partially superseded** — `gh` stays extension-optional; the difference in handling is gone |
| `brds/open-pr.md` **BR-07**, **G5** | Business rule requiring graceful degradation without `gh` | **Superseded** at the business-rule level by this spec's Clarifications |

Everything else in `002-open-pr` — its remaining functional requirements, its targeting algorithm, and
its hook design — remains in force, and FR-013 of this spec requires it.
