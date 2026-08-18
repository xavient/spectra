# Feature Specification: Review PR

**Feature Branch**: `008-review-pr`

**Created**: 2026-08-17

**Status**: Draft

**Input**: `brds/review-pr.md` (BRD-005, v0.1.0) — the Review PR agent (`speckit.spectra.review-pr`):
a GitHub-only conformance review agent that judges a pull request against the spec, plan, tasks, ADRs,
and constitution it carries, then publishes a human-curated, severity-ranked review through the
reviewer's own GitHub credentials.

## Clarifications

### Session 2026-08-17

- Q: How does the agent locate the pull request's spec, plan, and tasks? → A: Try three sources in
  order — (1) a spec present in the pull request's own diff, (2) the feature directory recorded in the
  project's Spec Kit feature record at the head revision, (3) treat as no-spec. Branch-name convention
  is deliberately not used.
- Q: When a diff is too large to review fully, what decides the cut? → A: A declared review budget —
  full-fidelity review within it, risk-ranked subset beyond it, always disclosed. The budget is a
  stated figure, not a runtime judgment, and not a reviewer prompt.
- Q: How is SC-007 measured, when FR-026 forbids persistence? → A: SC-007 is an out-of-band evaluation
  metric, validated by the team observing real sessions. The agent never measures, records, or reports
  it. FR-026 and the no-telemetry rule stand unchanged.
- Q: Where is the severity rubric defined? → A: In the spec — FR-016 now states all five levels with
  explicit assignment criteria and merge effect, retaining the two floors. A constitution-overridable
  rubric was considered and deferred as a follow-on.
- Q: On re-review, where do the previously published findings come from? → A: Read the agent's own
  prior review back off the pull request, identified by the FR-034 disclosure line and its pinned head
  revision. No persistence is introduced.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Review a pull request by URL and publish a curated review (Priority: P1)

A reviewing developer — someone who did not write the code — has a pull request URL. They invoke the
command with it. The agent reads the change together with the spec, plan, tasks, ADRs, and
constitution that the pull request carries, and comes back with a ranked list of numbered findings,
each anchored to a file and line and justified by a rule or requirement, plus a severity tally, a
plain statement of what the agent understood the change to do, an honest account of what it did and
did not review, and a recommended verdict.

The reviewer then curates. They pick the findings worth raising, discard the rest, choose the verdict
themselves, see the exact text that will be posted, and give a final go-ahead. One review is posted
under their own name, and they get a link to it.

**Why this priority**: This is the whole product in one flow. It delivers conformance review — the
capability no diff-only reviewer can offer — and it delivers the safeguard that makes conformance
review trustworthy: a person, not the agent, decides what reaches the pull request. Shipped alone,
with no other story, it is a complete and useful agent.

**Independent Test**: Point the command at a real pull request that carries a spec and a constitution.
Verify the summary is anchored, severity-classified, and honest about coverage; verify an empty
selection posts nothing; verify a curated selection posts exactly what was selected, with a preview
and a final confirmation before anything leaves the terminal; verify the returned link resolves to the
posted review.

**Acceptance Scenarios**:

1. **Given** a pull request URL, **When** the agent finishes analysis, **Then** the summary names the
   exact revision reviewed, and every finding carries a file and line, the rule or requirement it
   derives from, a severity, and a confidence level.
2. **Given** the presented summary, **When** the reviewer submits an empty selection, **Then** nothing
   is posted to the pull request and the agent says so.
3. **Given** a selection of findings, **When** the agent proceeds, **Then** it first states both the
   findings being posted and the findings being dropped, and posts only the selected ones.
4. **Given** a selected blocker, **When** the reviewer chooses to approve, **Then** the agent states
   the contradiction, requires a typed confirmation rather than a bare yes, and records the
   acknowledged blocker in the posted review body.
5. **Given** a chosen verdict, **When** the agent is ready to post, **Then** it displays the exact
   review body and posts nothing until the reviewer gives a final go-ahead.
6. **Given** a successful publication, **When** the agent reports back, **Then** it returns a link to
   the posted review.
7. **Given** new commits landed on the pull request after analysis began, **When** the agent is about
   to post, **Then** it detects the moved revision, warns, and offers to re-analyze instead of posting
   against code that is no longer current.

---

### User Story 2 - Discover and pick a pull request to review (Priority: P2)

A reviewer wants to review something but does not have a URL to hand. They invoke the command with no
arguments. If the branch they are standing on has an open pull request, the agent offers that one
first. Otherwise it lists the repository's open pull requests with number, title, author, and target
branch, and waits for an explicit choice. Once chosen, the review proceeds exactly as in Story 1.

**Why this priority**: Removes the trip to a browser to fetch a URL, which is the most common reason a
terminal-based review breaks flow. It is P2 rather than P1 because Story 1 is complete without it —
this is a convenience layer on the same engine.

**Independent Test**: Run the command with no arguments in a repository with several open pull
requests. Verify the current branch's pull request is offered first when one exists, that the list is
shown otherwise, that nothing is reviewed until a choice is made, and that a repository with no open
pull requests produces a clear message rather than an error.

**Acceptance Scenarios**:

1. **Given** no arguments and an open pull request for the current branch, **When** the agent runs,
   **Then** it offers that pull request first rather than listing everything.
2. **Given** no arguments and several open pull requests, **When** the agent runs, **Then** it lists
   them with number, title, author, and target branch, and reviews nothing until one is chosen.
3. **Given** no open pull requests exist, **When** the agent runs, **Then** it says so and stops
   without an error.

---

### User Story 3 - Review a pull request that carries no spec (Priority: P3)

A reviewer points the agent at a pull request on a repository, or a branch, with no spec, plan, or
tasks. Rather than declining, the agent reviews the change on its own terms and is explicit that it is
doing so: it states that no spec was found, reports the traceability pass as not run rather than
passed, still applies the constitution at full strength because standards exist independently of any
spec, and caps anything it might say about intent at the level of a question rather than a defect.

**Why this priority**: Makes the agent useful on repositories that are not fully spec-driven, which is
most of them, and protects the credibility of the coverage statement. It is P3 because the
conformance-review capability that distinguishes this agent is at its weakest here.

**Independent Test**: Point the command at a pull request with no spec but with a constitution present
on the base branch. Verify the summary declares the absence, verify traceability is listed as not run
and never as passed, verify guardrail findings are still produced with their clause quoted, and verify
no intent-class observation is rated a blocker or major.

**Acceptance Scenarios**:

1. **Given** a pull request with no spec, **When** the agent reviews it, **Then** the summary states
   that no spec was found and that the change was reviewed standalone.
2. **Given** no spec, **When** the coverage statement is produced, **Then** the traceability pass is
   listed as not run and is never reported as passed.
3. **Given** no spec but a constitution on the base branch, **When** the agent reviews, **Then**
   guardrail findings are still produced and still quote the clause they rest on.
4. **Given** no spec, **When** an intent-class concern arises, **Then** it is raised as a question and
   never as a blocker or a major finding.

---

### User Story 4 - Re-review after the author pushes changes (Priority: P4)

A reviewer returns to a pull request they already reviewed, after the author has pushed new commits.
They name the revision they reviewed last time. The agent recovers what it said before by reading its
own earlier review back off the pull request — it keeps no history of its own — then reviews only what
changed between that revision and the current head, and reports which of those earlier findings now
appear addressed and which remain open, without claiming a resolution it cannot evidence.

**Why this priority**: Turns the second and third pass into minutes rather than a full re-read. It is
P4 because it depends on the first pass existing and is an efficiency gain rather than a new
capability.

**Independent Test**: Review a pull request, have new commits pushed, then re-run naming the earlier
revision. Verify the findings reported are scoped to the delta, verify both revisions are stated,
verify previously raised findings are sorted into apparently-resolved and still-open with no
unevidenced claims, and verify a pull request with no readable prior review degrades to reporting the
delta alone.

**Acceptance Scenarios**:

1. **Given** a named prior revision, **When** the agent re-reviews, **Then** it reports findings for
   the delta and states both the prior and the current revision.
2. **Given** findings published on an earlier pass, **When** the agent re-reviews, **Then** it states
   which appear resolved and which remain open, and does not assert a resolution it cannot evidence.
3. **Given** no prior review by the agent that can be read back from the pull request, **When** the
   agent re-reviews, **Then** it says so and reports the delta alone rather than inventing a baseline.

---

### Edge Cases

- **The GitHub command-line tool is absent or not authenticated.** The agent stops before doing any
  analysis, distinguishes a missing tool from a missing login, states the exact remedy, and does not
  proceed. This is a hard stop by design, not a degraded review.
- **The pull request comes from a fork, or the reviewer cannot post a review.** The fork is noted
  upfront to set expectations; the full review still runs; if publication is refused, the agent hands
  over the rendered review body for manual use and explains what failed.
- **The reviewer is the author.** Self-approval is unavailable. The agent says so and offers the
  remaining verdicts rather than attempting an action that will fail.
- **New commits land mid-session.** The revision is re-checked immediately before publishing; if it
  moved, the agent warns and offers to re-analyze.
- **A review by the same reviewer already exists on this pull request.** Surfaced, with a choice
  between superseding it and adding another, rather than silently stacking duplicates.
- **The diff is too large to review at full fidelity.** The agent never refuses on size. It ranks
  files by risk, reviews the highest-risk subset properly, states precisely what it did not review,
  and may raise the size itself as a finding.
- **The pull request modifies the constitution or an ADR.** Treated as a governance change and always
  surfaced for human attention, whatever its severity.
- **The reviewer's local checkout is on a different branch than the pull request.** All of the pull
  request's own context is read at the pull request's revision; the local working tree is never
  trusted for it and never modified without permission.
- **The pull request is a draft.** The draft state is reported so the reviewer can judge whether a
  formal review is premature.
- **Generated files appear in the diff** (lock files, build output, vendored trees). Excluded from
  review and named as excluded in the coverage statement.
- **The diff is empty or trivial.** Reported as such. No findings are manufactured to justify the run.
- **Publication fails part-way.** The agent does not leave half a review behind; it falls back to the
  simplest complete form and states what it did.

## Requirements *(mandatory)*

### Functional Requirements

**Pre-flight and credentials**

- **FR-001**: The agent MUST verify, before beginning any work, that the GitHub command-line tool is
  installed and authenticated. If it is missing or not authenticated, the agent MUST distinguish which
  of the two failed, state the remedy, and MUST NOT proceed to analysis. This is a hard gate, not a
  degradation.
- **FR-002**: The agent MUST hold no credentials of its own and MUST act solely through the reviewer's
  existing GitHub authentication.
- **FR-003**: All pull request interaction — discovery, metadata retrieval, diff retrieval, retrieval
  of a file at a specific revision, and review publication — MUST go through the GitHub command-line
  tool exclusively.

**Target resolution and revision pinning**

- **FR-004**: The agent MUST accept an optional pull request URL. With no argument it MUST offer the
  current branch's open pull request first, then list the repository's open pull requests, and MUST
  review nothing until the reviewer chooses.
- **FR-005**: The agent MUST pin the review to a specific head revision and MUST report that revision
  both in the summary and in the published review.
- **FR-006**: The agent MUST read the pull request's spec, plan, tasks, and ADRs at the pull request's
  head revision, never from the reviewer's local working tree.
- **FR-006a**: The agent MUST locate the governing spec by trying three sources in this order, stopping
  at the first that resolves:
  1. **A spec present in the pull request's own diff.** The normal case when the change was built
     spec-driven: the spec ships in the same pull request as the code it authorizes.
  2. **The feature directory recorded in the project's Spec Kit feature record at the head revision.**
     Covers the case where the spec was merged by an earlier pull request and this one is an addendum
     to it.
  3. **Neither** — the pull request is treated as carrying no spec, and review proceeds per FR-012.

  The agent MUST NOT infer the spec location from the branch name, because branch-to-spec naming is a
  project convention rather than a guarantee. The agent MUST state which of the three sources applied,
  so the coverage statement reflects what was actually read.
- **FR-007**: The agent MUST NOT alter the reviewer's working tree — including checking out the pull
  request's branch — without explicit permission.
- **FR-008**: The agent MUST NOT modify source code, the spec, the plan, the tasks, or the
  constitution. Publishing the review, after explicit confirmation, is its only permitted mutation.

**Analysis**

- **FR-009**: The agent MUST evaluate guardrails against the constitution and ADRs in force on the
  **base** branch, and MUST surface any change to the constitution or an ADR as a governance change
  regardless of its severity.
- **FR-010**: The agent MUST perform traceability in both directions: work claimed complete but absent
  from the diff, and changes present in the diff that no task or requirement authorized.
- **FR-011**: The agent MUST select review lenses based on what the diff actually touches, and MUST
  state which lenses ran and which did not, with the reason for each omission.
- **FR-012**: When no spec is found, the agent MUST review the change standalone rather than declining;
  MUST state that no spec was found; MUST list traceability as not run rather than passed; MUST still
  apply guardrails at full strength; and MUST cap intent-class findings at question severity.
- **FR-013**: The agent MUST NOT refuse a review on the grounds of diff size. It MUST work against a
  **declared review budget**: every file within the budget is reviewed at full fidelity, and beyond it
  the agent MUST rank the remaining files by risk and review the highest-risk of them at full fidelity.
  The budget MUST be a stated, assertable figure rather than an implicit runtime judgment, and MUST NOT
  be surfaced to the reviewer as a choice. Whenever the budget is exceeded, the agent MUST disclose that
  subsetting occurred, name what it did not review, and MAY raise the size itself as a finding.
- **FR-014**: The agent MUST exclude generated files — lock files, build output, vendored trees — from
  review, and MUST name them as excluded.

**Findings**

- **FR-015**: Every reported finding MUST cite a file and line plus the source it derives from: a
  constitution or ADR clause, a requirement identifier, or a named engineering principle. A finding
  without such an anchor MUST NOT be reported.
- **FR-016**: Every finding MUST carry exactly one of five severities, assigned from the rubric below,
  so that repeated reviews of the same revision agree. Short forms shown in parentheses are the display
  labels used in the summary.

  | Severity | Assign when | Effect on merge |
  | -------- | ----------- | --------------- |
  | **Blocker** (S1) | The change is unsafe or incorrect to merge as it stands: it loses or corrupts data, exposes a secret or a vulnerability, breaks a published contract with no migration path, violates an explicit compliance or regulatory requirement, or fails to deliver a requirement it claims to satisfy. | Must be resolved before merge. |
  | **Major** (S2) | The change functions, but it violates an explicit constitution or ADR clause, diverges from the spec, introduces scope no task authorized, or ships behaviour with no test covering it. Merging leaves a known defect or an unrecorded decision. | Should be resolved before merge; merging it is consciously accepted debt. |
  | **Minor** (S3) | A real defect of bounded consequence — a missed edge case, a misleading name, a duplicated fragment, a documentation gap. Merging is reasonable; leaving it carries a small ongoing cost. | May be deferred. |
  | **Nit** (S4) | Style, formatting, or preference with no functional consequence, on a point where the project has stated no rule. | Never blocks. |
  | **Question** (Q) | The agent lacks the information to judge, or the answer turns on intent only a human holds. Includes any finding downgraded under FR-017 and any intent-class observation when no spec was found (FR-012). | Not a defect; requests information. |

  Two floors override the table: an explicit constitution MUST violation is never classified below
  **Major**, and an explicit compliance or regulatory MUST violation is never classified below
  **Blocker**.
- **FR-017**: Every finding MUST carry a confidence level, and a low-confidence finding MUST NOT be
  classified a blocker — it MUST be raised as a question instead.
- **FR-018**: Findings MUST be grouped by who owns the resolution: intent divergence needing a human
  decision, guardrail violations that are objective and clause-cited, and craft findings.
- **FR-019**: Findings MUST be numbered in a single flat sequence in presentation order, so the
  reviewer can select them by number.
- **FR-020**: The agent SHOULD group repeated instances of the same finding into one entry with a count
  and its locations, rather than listing each occurrence separately.

**Presentation**

- **FR-021**: The summary MUST contain: pull request identity, author, source and target branch, head
  revision, change size, the linked spec or a statement of its absence, continuous-integration status,
  a recommended verdict, the agent's own reading of the change, a severity tally, the findings, an
  explicit coverage-and-limits statement, and next actions.
- **FR-022**: The recommended verdict MUST be derived mechanically from the findings, drawn from a
  closed set of three — approve, request changes, comment only — and presented as a recommendation
  only.

**Selection and verdict**

- **FR-023**: The agent MUST require an explicit selection of findings to publish, with nothing
  pre-selected. An empty or absent selection MUST result in nothing being posted.
- **FR-024**: The selection input MUST accept individual numbers, comma-separated lists, ranges,
  severity groups, `all`, `none`, and exclusions such as "all except N".
- **FR-025**: After selection and before publishing, the agent MUST state both the findings being
  posted and the findings being dropped, so the full record exists in the session transcript.
- **FR-026**: The agent MUST NOT persist findings, rejections, or review history anywhere between runs.
- **FR-027**: The agent MUST ask the reviewer to choose the verdict — approve, request changes, or
  comment only — and MUST NOT select one on the reviewer's behalf.
- **FR-028**: If the chosen verdict contradicts the selected findings — above all an approval alongside
  a selected blocker — the agent MUST state the contradiction, MUST require a typed confirmation rather
  than a bare yes, and MUST record the acknowledged blocker in the published review body. It MUST NOT
  refuse the reviewer's choice outright.
- **FR-029**: If the authenticated reviewer is the pull request's author, the agent MUST explain that
  self-approval is unavailable and offer the remaining verdicts rather than attempting an action that
  will fail.
- **FR-030**: The selection input SHOULD allow the reviewer to override a finding's severity as well as
  accept or drop it.

**Publication**

- **FR-031**: Before any outward action the agent MUST display the exact review it will publish and
  MUST obtain a final go-ahead.
- **FR-032**: The agent MUST re-check the head revision immediately before publishing and, if it has
  moved, MUST warn and offer to re-analyze rather than publish against stale code.
- **FR-033**: The agent MUST publish as a single review event carrying both the verdict and the review
  body, and MUST return a link to the published review.
- **FR-034**: The published review MUST disclose that it was AI-assisted and human-curated.
- **FR-035**: When publication fails after the pre-flight gate passed — insufficient permission or a
  fork restriction — the agent MUST present the review in the session, hand over the rendered body for
  manual posting, and explain what failed. It MUST NOT leave a partially published review.
- **FR-036**: The agent SHOULD detect an existing review by the same reviewer on the same pull request
  and ask whether to supersede it or add another.
- **FR-037**: The agent SHOULD support publishing findings as line-anchored inline comments, placing
  anchorable findings inline and the remainder in the review body, still as a single review event.
- **FR-038**: The agent SHOULD offer, at the end of a review, to save the complete review — including
  the findings the reviewer dropped — to a local file, defaulting to not saving.

**Re-review**

- **FR-039**: The agent SHOULD support reviewing only the delta since a reviewer-named prior revision,
  and reporting which previously published findings appear resolved and which remain open, without
  asserting a resolution it cannot evidence. It MUST source those earlier findings by reading its own
  prior review back from the pull request — located by the FR-034 disclosure line and the head revision
  recorded in it (FR-005) — and MUST NOT introduce any stored review history to support this (FR-026).
  Where no such prior review can be read, the agent MUST say so and report the delta alone.

**Packaging and portability**

- **FR-040**: The agent MUST be a single command file inside the existing self-contained `spectra`
  extension, registered in that extension's manifest, and MUST NOT introduce a new extension.
- **FR-041**: The command MUST be namespaced `speckit.spectra.review-pr`, MUST take its input through
  the generic arguments placeholder, and MUST NOT hard-code any single coding agent's invocation
  syntax, so it runs on whatever coding agent the team uses.
- **FR-042**: Shipping the agent MUST include registering it in the agent roster and regenerating the
  structured agent listings, so the roster, README, and extension documentation do not drift.

### Key Entities

- **Review target**: The pull request under review — its number, title, author, source and target
  branch, draft and fork status, and continuous-integration status.
- **Head revision**: The single commit the review is pinned to. A review is valid only for this
  revision, which is why it is reported in both the summary and the published review.
- **Authorizing context**: The spec, plan, tasks, and ADRs read at the head revision — located by the
  ordered chain in FR-006a — plus the constitution and ADRs in force on the base branch. Establishes
  what the change was authorized to do and which standards it must meet.
- **Lens**: One focused review pass over the diff — correctness, security, tests, data and migrations,
  API contract and compatibility, performance, operability, maintainability, docs, dependencies,
  accessibility, internationalization — selected by what the change touches, and reported as run or
  not run with a reason.
- **Finding**: A single reported concern. Carries a sequence number, a class (intent, guardrail,
  craft), a file and line, the source it derives from, a severity, a confidence level, an impact, and a
  suggested fix. A finding without an anchor and a source cannot exist.
- **Severity**: Blocker, major, minor, nit, or question — how much the finding should hold up the
  merge, assigned from the rubric in FR-016, with floors for constitution and compliance violations.
- **Confidence**: How certain the agent is that a finding is real. A separate axis from severity and a
  cap on it: low confidence cannot be a blocker.
- **Coverage and limits statement**: Which lenses ran, which did not and why, which files were
  excluded, and what evidence was unavailable. Prevents a review from implying more assurance than it
  earned.
- **Selection**: The reviewer's explicit choice of which findings to publish. Nothing is pre-selected;
  an empty selection publishes nothing.
- **Verdict**: What the reviewer submits — approve, request changes, or comment only. Recommended by
  the agent, always chosen by the human.
- **Published review**: The single review event posted under the reviewer's own credentials, containing
  the selected findings, the head revision, the AI-assisted-and-human-curated disclosure, and any
  acknowledged blocker override.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of published findings were individually selected by the reviewer. Zero findings
  reach a pull request without explicit human selection.
- **SC-002**: 100% of reported findings carry a file and line plus a cited source. Zero unanchored
  assertions.
- **SC-003**: 100% of reviews state their coverage and limits, including which lenses did not run and
  what was excluded.
- **SC-004**: Repeated reviews of the same revision assign the same severity to the same finding.
- **SC-005**: Zero outward actions occur without a preview and a final go-ahead.
- **SC-006**: For every pull request the agent can resolve, the run ends in either a published review
  or an explicitly stated degradation with a reason and a manual path. The agent never simply declines.
- **SC-007** *(measured out-of-band)*: A large majority of the blocker and major findings surfaced are
  kept by reviewers rather than dropped, evidencing that high-severity output is signal rather than
  noise. This is validated by the team observing real review sessions during evaluation. The agent MUST
  NOT measure, record, or report it — FR-026 forbids persistence and the project ships no telemetry.
- **SC-008**: A reviewer completes the loop from URL to published review without leaving the terminal
  and without composing platform commands by hand.
- **SC-009**: Every approval published over a selected blocker carries that acknowledgement in the
  review body. Zero silent overrides.
- **SC-010**: Reviews of pull requests that carry a spec surface intent divergence and unauthorized
  scope that a diff-only review cannot detect.
- **SC-011**: When the required tooling is missing or unauthenticated, 100% of runs stop before any
  analysis and name the specific remedy.
- **SC-012**: A reviewer can go from an unfamiliar pull request to a decision they are confident in
  within a single session, without opening the repository in a browser to gather context.
- **SC-013**: Every review whose diff exceeded the declared review budget names the files it excluded
  and why. Zero silent partial reviews.

## Assumptions

These are reasonable defaults adopted where BRD-005 left a question open. Each is a decision that can
be revisited during clarification or planning without reshaping the feature.

- **The reviewer is not the author.** The agent runs in a fresh session with no memory of the code
  being written; that absence of memory is what makes the review independent. Self-review is detected
  and handled (FR-029) rather than prevented.
- **The GitHub command-line tool is present and authenticated in normal use.** The pre-flight gate
  exists for the exception, not the rule.
- **The reviewer's working tree is usually on a different branch than the pull request**, so all of the
  pull request's context is read at its own revision.
- **The constitution in force is the one on the base branch**, since those are the rules the change is
  being merged into.
- **Reviewers will drop some findings, and that is correct behaviour** rather than a defect. The human
  is the noise filter.
- **Continuous-integration status informs the recommended verdict**: the agent does not recommend
  approval while required checks are failing. It remains a recommendation only, and the reviewer may
  still approve.
- **Draft pull requests are reviewed, with the draft state reported** so the reviewer can decide
  whether a formal review is premature. Drafts are not declined.
- **Questions are published inside the single review body**, under their own heading, rather than as a
  separate lighter-weight comment. This preserves the one-review-event guarantee (FR-033).
- **There is no hard cap on the number of findings surfaced.** Volume is managed by ranking, by
  collapsing minors and nits, and by grouping repeats (FR-020), not by silently discarding findings.
- **An optional saved review is written to a reviewer-chosen path outside the spec directory**, since
  the reviewer is typically not on the pull request's branch. Saving is off by default (FR-038).
- **The whole diff is reviewed even in a repository with code-ownership rules.** Scoping to owned paths
  is not attempted; the coverage statement describes what was reviewed.
- **Reviewing an arbitrary commit range is out of scope.** The unit of review is a pull request.
- **The permission a reviewer holds is discovered by attempting the action, not predicted.** Exact
  rules vary by repository visibility and role, so the agent reacts to failure (FR-035).
- **Only GitHub is supported.** GitLab, Bitbucket, and Azure DevOps are explicitly out of scope for
  this feature, and no platform-abstraction layer is built in anticipation of them.
- **The severity rubric is fixed, not project-configurable.** FR-016 defines it. Letting a project
  override the ladder from its constitution was considered and deferred: most constitutions define no
  severity ladder, so the option would add a second source of truth for little gain until the default
  has proven itself.
- **Publishing a review is the highest-consequence action in the Spectra roster**, because it can
  satisfy a branch-protection requirement and unblock a merge. It therefore warrants a stricter
  confirmation gate than opening a pull request.
