# Business Requirements Document (BRD): Review PR

## Document Control

| Field             | Value                                                                                                                                                                              |
| ----------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| BRD ID            | BRD-005                                                                                                                                                                            |
| Title             | Review PR                                                                                                                                                                          |
| Author            | Spectra / TELUS Digital                                                                                                                                                            |
| Status            | Draft                                                                                                                                                                              |
| Version           | 0.1.0                                                                                                                                                                              |
| Created           | 2026-08-17                                                                                                                                                                         |
| Last updated      | 2026-08-17                                                                                                                                                                         |
| Related documents | `.specify/memory/constitution.md`, `brds/open-pr.md` (BRD-002), `spectra/commands/create-pr.md`, `/speckit-implement`, `/speckit-tasks`, `/speckit-constitution`, `brds/domain-analyzer.md` (BRD-001) |

## 1. Executive Summary

The **Review PR** agent (`speckit.spectra.review-pr`) is a Spectra core agent for the Deployment &
Operations / review gate. A reviewing developer — **not** the author — points it at a GitHub pull
request, by URL or by picking from the repository's open PRs. It reads the diff **together with the
spec, plan, tasks, ADRs, and constitution that the PR carries**, and produces a severity-categorized
set of findings with a recommended verdict.

It then runs a second, deliberate phase: the reviewer **chooses which findings to publish**, chooses
the verdict (approve / request changes / comment), and only then does the agent post a single review
to GitHub under the reviewer's own credentials via the `gh` CLI.

The distinguishing capability is **conformance review** — does this change do what the spec said,
only what the spec said, and in the way the constitution requires? Generic AI reviewers see the diff
alone and cannot answer any of those questions. The distinguishing safeguard is that **the human is
the filter**: nothing reaches the pull request that a person did not individually select.

## 2. Business Context & Problem Statement

Spectra now carries work from requirement to open pull request (BRD-002), and then stops. Review is
the last remaining fully manual gate in the lifecycle — and it is the gate where quality is actually
decided.

- **Reviewers lack the context the author had.** The author spent hours in the spec, plan, and tasks.
  The reviewer arrives cold at a diff and, under time pressure, reviews the code for correctness
  while silently skipping the harder question of whether it matches what was agreed. Intent
  divergence and scope creep pass review routinely because checking them is expensive by hand.
- **Written standards are not enforced at the gate.** A project's constitution encodes coding,
  security, and architecture guardrails, but nothing checks a diff against them. A standard nobody
  verifies is a suggestion.
- **Generic AI reviewers review the diff in isolation.** They can flag a missing null check. They
  cannot know that a requirement was marked complete without being implemented, that a change was
  never authorized by any task, or that an ADR forbids the pattern just introduced. The context they
  need is sitting in the repository, unused.
- **Unfiltered AI review destroys reviewer trust.** Tools that post every finding they generate bury
  the two that matter under thirty that do not, mixing blocking defects with style preferences.
  Authors learn to skim; reviewers learn to ignore. Volume is not the product — a short, correct,
  human-endorsed review is.
- **Review effort is spent in the wrong place.** Senior reviewers hand-check mechanical properties
  (are there tests, is there a rollback, is the contract backwards compatible) instead of exercising
  judgment on design and risk.

The result is that the most context-rich part of the lifecycle produces the most context-starved
review, and the guardrails the team wrote down are enforced only by memory.

## 3. Business Objectives & Goals

- **G1 — Review against intent, not just code.** Judge the diff against the spec, plan, tasks, ADRs,
  and constitution the pull request carries, so divergence and unauthorized scope are caught at the
  gate.
- **G2 — Make written standards enforceable.** Turn constitution and ADR clauses into citable
  findings, so a documented standard is checked by construction rather than remembered.
- **G3 — Keep the human as the filter.** The agent proposes findings and a verdict; a person selects
  what is published and decides the outcome. Nothing is posted unselected.
- **G4 — Publish a review a team would want to receive.** Short, ranked, evidence-anchored, honest
  about what was not reviewed.
- **G5 — Never refuse to review.** No spec, an oversized diff, or a `gh` CLI issue degrades the
  review with a declared limit — it does not decline.
- **G6 — Be truthful about coverage and confidence.** State which lenses ran, what was skipped and
  why, and how confident each finding is. Overstated coverage is worse than admitted gaps.
- **G7 — Gate on `gh` authentication.** Verify the `gh` CLI is installed and authenticated before
  any work begins; if it is not, tell the user exactly what to fix and stop.

## 4. Stakeholders & Users

| Stakeholder / user                     | Role in this product     | What they need from it                                                                                                       |
| -------------------------------------- | ------------------------ | ---------------------------------------------------------------------------------------------------------------------------- |
| Reviewing developer                    | Primary user             | Fast, grounded understanding of an unfamiliar PR; a shortlist of findings worth raising; full control over what gets posted.  |
| PR author                              | Downstream consumer      | One coherent review, ranked by severity, with each point anchored to a line and justified by a rule — not a wall of nits.     |
| Engineering leads                      | Oversight                | Confidence that specs and constitution guardrails are actually checked at the gate, and that AI output is human-endorsed.     |
| Compliance / audit                     | Indirect                 | A traceable record: what was raised, what the reviewer accepted, what verdict was given, and any override of a blocker.       |
| Constitution, ADRs, spec, plan, tasks  | Sources of truth (input) | Read at the PR's revision to establish the standards in force and the intent the change was authorized against.              |
| GitHub CLI (`gh`)                      | Capability provider      | Supplies PR discovery, metadata, diff, file contents, and review publication under the reviewer's existing GitHub authentication. |

## 5. Scope

### 5.1 In Scope

- **`gh` CLI pre-flight gate.** Before any work, verify `gh` is installed and authenticated
  (`gh auth status`). If the check fails, tell the user exactly what is wrong and how to fix it
  (e.g. `gh auth login`), and stop — do not proceed to analysis.
- **Resolve the review target** from an optional URL argument; with no argument, offer the open PR for
  the current branch first, then list the repository's open PRs and let the user pick.
- **Pin the review to a commit.** Capture and report the head revision the review was performed
  against.
- **Read the PR's own context at its head revision** — spec, plan, tasks, ADRs — rather than trusting
  the reviewer's local working tree, which is usually on a different branch.
- **Traceability review in both directions** — tasks claimed complete that are absent from the diff,
  and changes in the diff that no task or requirement authorized.
- **Guardrail review** against the constitution and ADRs in force on the base branch, with the
  violated clause quoted.
- **Craft review** through lenses selected by what the diff actually touches (correctness, security,
  tests, data and migrations, API contract and compatibility, performance, operability,
  maintainability, docs, dependencies, accessibility, internationalization).
- **Severity and confidence classification** of every finding, grouped by who owns the fix.
- **A ranked chat summary** including a statement of the agent's own reading of the change, a severity
  tally, the findings, an explicit coverage-and-limits statement, and a recommended verdict.
- **Reviewer selection of findings to publish**, with nothing pre-selected, followed by an explicit
  confirmation of what will be posted and what was dropped.
- **Verdict selection** — approve, request changes, or comment only — with the contradiction between
  an accepted blocker and an approval challenged once and recorded when overridden.
- **Publication as a single review event** via `gh` under the reviewer's existing GitHub
  authentication, after a preview and a final go-ahead.
- **Graceful degradation** when the PR is from a fork or the reviewer lacks permission to post —
  presenting the rendered review for manual use.

### 5.2 Out of Scope

- **Merging the pull request.** The agent reviews; merging belongs to the author, GitHub, and
  branch protection.
- **Fixing the findings.** The agent does not modify source code, the spec, the plan, the tasks, or
  the constitution. Handing blockers to `/speckit-tasks` as fix work is a possible later capability,
  not this one.
- **Deciding the outcome.** The agent recommends a verdict; the reviewer chooses it. The agent never
  selects a verdict on the user's behalf.
- **Publishing anything the reviewer did not select.** There is no "post everything" default path.
- **Persisting review state.** No local database of findings, rejections, or history. What the
  reviewer needs to keep is stated in the transcript for them to copy.
- **Authoring standards.** The agent reads and cites the constitution and ADRs; authoring them belongs
  to `/speckit-constitution`, the Guardrails agent, and `speckit.spectra.adr`.
- **Replacing CI.** Static analysis, test execution, linting, and scanning belong to the pipeline. The
  agent reads CI status as evidence; it does not re-run or replace those checks.
- **Approving on behalf of a human, or holding its own credentials.** Every outward action uses the
  reviewer's existing `gh` login.
- **GitLab, Bitbucket, Azure DevOps, and other platforms.** This agent targets GitHub exclusively.
  GitLab or other platform support is a future capability, not this version.
- **Inline, line-anchored comments** in the first release. The first release publishes a single review
  body; inline anchoring is a follow-on.

## 6. User Journeys *(feeds the spec's prioritized user stories)*

### Journey 1 — Review a pull request by URL, publish a curated review (Priority: P1)

- **Actor:** Reviewing developer (not the PR author)
- **Trigger:** The reviewer invokes the command with a PR URL.
- **Outcome / value:** Within one session the reviewer understands an unfamiliar PR, sees findings
  they would have taken an hour to find by hand, discards the ones they disagree with, and posts a
  review under their own name. This is the MVP: it delivers the whole value of the agent on its own.
- **Flow:**
  1. The reviewer runs the command with the PR URL.
  2. The agent resolves the PR and pins its head revision.
  3. It gathers metadata, the diff, commit series, and CI status, and reads the spec, plan, tasks, and
     relevant ADRs at that revision, plus the constitution in force on the base branch.
  4. It selects lenses based on what the diff touches, runs the traceability, guardrail, and craft
     passes, and assigns severity and confidence to each finding.
  5. It presents the ranked summary with numbered findings, a severity tally, its own reading of the
     change, a coverage-and-limits statement, and a recommended verdict.
  6. The reviewer selects which findings to publish. Nothing is pre-selected.
  7. The agent confirms what will be posted and what is being dropped.
  8. The agent asks for the verdict, recommending one, and challenges the selection if it contradicts
     the accepted findings.
  9. The agent shows the exact review to be posted and asks for a final go-ahead.
  10. On confirmation it posts one review and returns the link to it.
- **Acceptance:**
  - **Given** a PR URL, **When** the agent completes its analysis, **Then** the summary names the head
    revision reviewed, every finding cites a file and line plus the rule or requirement it comes from,
    and every finding carries a severity and a confidence.
  - **Given** the presented summary, **When** the reviewer submits an empty selection, **Then** nothing
    is posted to the pull request.
  - **Given** a selection of findings, **When** the agent proceeds, **Then** it first states both the
    accepted and the dropped findings, and posts only the accepted ones.
  - **Given** an accepted blocker, **When** the reviewer chooses approve, **Then** the agent states the
    contradiction, requires a typed confirmation, and records the acknowledged blocker in the posted
    review body.
  - **Given** a chosen verdict, **When** the agent is ready to post, **Then** it shows the exact review
    body and posts nothing until the reviewer gives a final go-ahead.
  - **Given** a successful publication, **When** the agent reports back, **Then** it returns the link
    to the posted review.

#### Illustrative output — the summary the reviewer sees (Journey 1, step 5)

<!-- Product surface, not implementation: this is the artifact the user reads and acts on. -->

```text
PR #142 · Add rate limiting to public API · @author
feat/012-rate-limit → dev · head 4a9f2c1 · 14 files, +612/−87
Spec: specs/012-rate-limit/spec.md · CI: 2 passed, 1 failing

RECOMMENDED VERDICT: Request changes — 1 blocker, 3 major

What this PR does (my reading)
Adds a token-bucket limiter as middleware, backed by Redis, applied to all
/api/v1/public routes. Adds per-key limit config and a 429 response with
Retry-After.

Findings          S1  S2  S3  Nit   Q
Intent/spec        0   1   0    0    1
Guardrails         0   1   1    0    0
Craft              1   1   4    6    1
                   1   3   5    6    2

── BLOCKERS ──────────────────────────────────────────────────
[1] S1 · Security · confidence: high
    Redis connection string used without TLS enforcement
    src/limiter/redis.ts:34
    Violates constitution § Security: "all external data stores MUST be
    reached over TLS."
    Impact: limiter state, including API keys used as bucket keys, crosses
    the network in cleartext.
    Fix: enable TLS on the client and fail closed on a non-TLS scheme.

── MAJOR ─────────────────────────────────────────────────────
[2] S2 · Intent · confidence: high
    FR-004 (burst allowance) has no implementation in this diff, but T-011
    is marked complete
    specs/012-rate-limit/tasks.md:24
    Needs a human call: implement it, or amend the spec.
[3] S2 · Tests · confidence: high     … src/limiter/index.ts:71
[4] S2 · Data · confidence: medium    … migrations/0007_buckets.sql:1

── MINOR [5]–[9] · NITS [10]–[15] ────────────────────────────
Collapsed. 4 of the nits are the same missing-return-type pattern in
src/limiter/*.ts.

── QUESTIONS ─────────────────────────────────────────────────
[16] Why is /api/v1/public/health exempted? Not mentioned in the spec —
     intentional, or an oversight? src/limiter/index.ts:58

── COVERAGE & LIMITS ─────────────────────────────────────────
Reviewed 14 files at 4a9f2c1. Lenses run: intent/traceability, guardrails,
security, tests, API contract, operability. Not run: performance (no hot
path touched), data-layer schema (no schema change beyond the migration
above). Not reviewed: package-lock.json (generated).
No load-test evidence available, so the 429 path is unverified.
Overall confidence: medium-high.

── SELECT ────────────────────────────────────────────────────
Which findings do you want to post? Nothing is selected by default.
  all · none · 1,2,4,6 · 1-4 · blockers+major · all except 10-15
Selection:
```

### Journey 2 — Discover and pick a PR to review (Priority: P2)

- **Actor:** Reviewing developer with no URL in hand
- **Trigger:** The reviewer invokes the command with no arguments.
- **Outcome / value:** The reviewer starts a review without leaving the terminal to hunt for a URL,
  and cannot accidentally review the wrong PR because the choice is explicit.
- **Flow:**
  1. The reviewer invokes the command with no arguments.
  2. If the current branch has an open PR, the agent offers that one first.
  3. Otherwise, or if declined, the agent lists the repository's open PRs with number, title, author,
     and target branch, and asks which to review.
  4. On selection, the agent proceeds exactly as in Journey 1.
- **Acceptance:**
  - **Given** no arguments and an open PR for the current branch, **When** the agent runs, **Then** it
    offers that PR first rather than listing everything.
  - **Given** no arguments and several open PRs, **When** the agent runs, **Then** it lists them and
    waits for an explicit choice, reviewing nothing until one is chosen.
  - **Given** no open PRs exist, **When** the agent runs, **Then** it says so and stops without error.

### Journey 3 — Review a pull request that has no spec (Priority: P3)

- **Actor:** Reviewing developer on a repository, or a branch, without Spec Kit artifacts
- **Trigger:** The agent finds no spec associated with the PR.
- **Outcome / value:** The agent is useful on any repository, not only fully spec-driven ones — and it
  is honest that it is reviewing a change with no authorized baseline rather than pretending to check
  conformance it cannot check.
- **Flow:**
  1. The agent resolves the PR and finds no spec, plan, or tasks at the head revision.
  2. It states this in the summary header and reviews the change as a standalone diff.
  3. It omits the traceability lens from the coverage list rather than reporting it as passed.
  4. It still runs the guardrail lens at full strength, since the constitution exists independently of
     any spec.
  5. It caps intent-class observations at Question severity and proceeds through selection and
     publication as in Journey 1.
- **Acceptance:**
  - **Given** a PR with no spec, **When** the agent reviews it, **Then** the summary states that no
    spec was found and that the change was reviewed standalone.
  - **Given** no spec, **When** the coverage statement is produced, **Then** the traceability lens is
    listed as not run, and is never reported as passed.
  - **Given** no spec but a constitution, **When** the agent reviews, **Then** guardrail findings are
    still produced and still cite their clause.
  - **Given** no spec, **When** an intent-class concern is raised, **Then** it is raised as a Question
    and not as S1 or S2.

### Journey 4 — Re-review after the author pushes changes (Priority: P4)

- **Actor:** Reviewing developer returning to a PR they already reviewed
- **Trigger:** New commits have landed since the previously reviewed revision.
- **Outcome / value:** The second pass costs a fraction of the first: the reviewer sees what changed
  and which previously posted findings are now resolved, instead of re-reading the whole PR.
- **Flow:**
  1. The reviewer invokes the command on a PR they have reviewed before, naming the previously
     reviewed revision.
  2. The agent reviews the delta between that revision and the current head.
  3. It reports which previously published findings appear addressed and which remain open.
  4. Selection, verdict, and publication proceed as in Journey 1.
- **Acceptance:**
  - **Given** a prior reviewed revision, **When** the agent re-reviews, **Then** it reports findings
    for the delta and states both revisions.
  - **Given** previously published findings, **When** the agent re-reviews, **Then** it states which
    appear resolved and which remain open, without asserting resolution it cannot evidence.

### Edge Cases

- **`gh` CLI not installed or not authenticated.** The agent stops at the pre-flight gate, tells the
  user exactly what is wrong (missing binary vs. not logged in), states the fix (`gh auth login`),
  and does not proceed to analysis. This is a hard stop, not a degradation.
- **Fork PR, or reviewer lacks permission to post.** The agent notes the fork upfront to set
  expectations, runs the full review regardless, and on a permission failure at publication degrades
  to presenting the rendered review for manual use.
- **Reviewer is the PR author.** GitHub rejects self-approval. The agent explains this and offers the
  remaining options rather than attempting an action that will fail.
- **New commits land mid-session.** The agent re-checks the head revision immediately before
  publishing; if it moved, it warns and offers to re-analyze instead of posting a review of code that
  is no longer current.
- **A review from the same user already exists.** The agent surfaces it and asks whether to supersede
  or add a new one instead of quietly stacking duplicates.
- **Oversized diff.** The agent risk-ranks files, reviews the highest-risk subset at full fidelity,
  states precisely what was not reviewed, and raises the size itself as a finding.
- **The PR modifies the constitution or an ADR.** Treated as a governance change and always surfaced
  for human attention, independent of its severity.
- **The reviewer's local checkout differs from the PR.** The agent reads the PR's context at its head
  revision and never relies on the local working tree for it.
- **Draft PR.** The agent notes the draft state so the reviewer can decide whether a formal review is
  premature.
- **Generated files in the diff** (lock files, build output, vendored trees). Excluded from review and
  named as excluded.
- **Empty or trivial diff.** Reported as such; no findings are manufactured to justify the run.
- **Publication partially fails.** The agent does not leave half a review; it falls back to the
  simplest complete form and says what it did.

## 7. Business Requirements

| ID    | Requirement                                                                                                                                                                     | Priority |
| ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| BR-01 | The agent MUST accept an optional PR URL. With no argument it MUST offer the current branch's open PR first, then list the repository's open PRs, and MUST review nothing until the user chooses. | P1       |
| BR-02 | The agent MUST pin the review to a specific head revision and MUST report that revision in the summary and in the published review.                                              | P1       |
| BR-03 | The agent MUST read the PR's spec, plan, tasks, and ADRs at the PR's head revision, not from the reviewer's local working tree.                                                  | P1       |
| BR-04 | The agent MUST NOT alter the reviewer's working tree — including checking out the PR branch — without explicit permission.                                                       | P1       |
| BR-05 | The agent MUST evaluate guardrails against the constitution and ADRs in force on the **base** branch, and MUST surface any change to the constitution or an ADR as a governance change regardless of severity. | P1       |
| BR-06 | The agent MUST NOT modify source code, the spec, the plan, the tasks, or the constitution. Its only permitted mutation is publishing the review, after explicit confirmation.     | P1       |
| BR-07 | The agent MUST perform traceability in both directions: work claimed complete but absent from the diff, and changes in the diff not authorized by any task or requirement.        | P1       |
| BR-08 | The agent MUST select review lenses based on what the diff actually touches, and MUST state which lenses ran and which did not, with the reason.                                 | P1       |
| BR-09 | Every reported finding MUST cite a file and line and the source it derives from — a constitution or ADR clause, a requirement identifier, or a named engineering principle. A finding without such an anchor MUST NOT be reported. | P1       |
| BR-10 | Every finding MUST carry a severity of S1 Blocker, S2 Major, S3 Minor, S4 Nit, or Question, assigned from a stated rubric so repeated reviews of the same revision agree. An explicit constitution MUST violation floors at S2; an explicit compliance or regulatory MUST violation floors at S1. | P1       |
| BR-11 | Every finding MUST carry a confidence level, and a low-confidence finding MUST NOT be classified S1 — it MUST be raised as a Question instead.                                   | P1       |
| BR-12 | Findings MUST be grouped by who owns the resolution: intent divergence (needs a human decision), guardrail violation (objective, clause cited), and craft findings.              | P1       |
| BR-13 | When no spec is found, the agent MUST review the change standalone rather than declining; MUST state that no spec was found; MUST list traceability as not run rather than passed; MUST still apply guardrails at full strength; and MUST cap intent-class findings at Question. | P1       |
| BR-14 | The agent MUST NOT refuse a review on the grounds of diff size. It MUST risk-rank the diff, review the highest-risk subset at full fidelity, state what was not reviewed, and MAY raise the size itself as a finding. | P1       |
| BR-15 | The summary MUST contain: PR identity, author, source and target branch, head revision, change size, linked spec (or its absence), CI status, a recommended verdict, the agent's own reading of the change, a severity tally, the findings, an explicit coverage-and-limits statement, and next actions. | P1       |
| BR-16 | Findings MUST be numbered in a single flat sequence in presentation order, so a reviewer can select them by number.                                                              | P1       |
| BR-17 | The recommended verdict MUST be derived mechanically from the findings and drawn from a closed set, and MUST be presented as a recommendation only.                              | P1       |
| BR-18 | The agent MUST require an explicit selection of findings to publish, with nothing pre-selected. An empty or absent selection MUST result in nothing being posted.                | P1       |
| BR-19 | The selection input MUST accept individual numbers, comma-separated lists, ranges, severity groups, `all`, `none`, and exclusions such as `all except N`.                        | P1       |
| BR-20 | After selection and before publishing, the agent MUST state both the findings being posted and the findings being dropped, so the full record exists in the transcript. The agent MUST NOT persist findings, rejections, or review history anywhere. | P1       |
| BR-21 | The agent MUST ask the reviewer to choose the verdict — approve, request changes, or comment only — and MUST NOT select one on the reviewer's behalf.                            | P1       |
| BR-22 | If the chosen verdict contradicts the accepted findings — most importantly an approval alongside an accepted blocker — the agent MUST state the contradiction, MUST require a typed confirmation rather than a bare yes, and MUST record the acknowledged blocker in the published review body. It MUST NOT refuse the reviewer's choice outright. | P1       |
| BR-23 | Before any outward action the agent MUST show the exact review it will publish and MUST obtain a final go-ahead.                                                                 | P1       |
| BR-24 | The agent MUST re-check the head revision immediately before publishing and, if it has moved, MUST warn and offer to re-analyze rather than publishing against stale code.       | P1       |
| BR-25 | The agent MUST publish as a single review event carrying the verdict and the review body, and MUST return a link to the published review.                                        | P1       |
| BR-26 | The published review MUST disclose that it was AI-assisted and human-curated.                                                                                                   | P1       |
| BR-27 | The agent MUST hold no credentials of its own and MUST act solely through the reviewer's existing `gh` authentication.                                                           | P1       |
| BR-28 | The agent MUST verify that the `gh` CLI is installed and authenticated before beginning any work. If `gh` is not found or `gh auth status` reports failure, the agent MUST tell the user what is wrong, state the fix (e.g. `gh auth login`), and MUST NOT proceed. This is a hard gate, not a degradation. | P1       |
| BR-29 | All pull request interaction — discovery, metadata retrieval, diff retrieval, file retrieval at a revision, and review publication — MUST use `gh` CLI commands exclusively.       | P1       |
| BR-30 | When publication fails after the pre-flight passed — insufficient permission or a fork restriction — the agent MUST degrade gracefully: present the review in chat, hand over the rendered body for manual posting, and explain what failed. It MUST NOT leave a partially published review. | P1       |
| BR-31 | The agent MUST operate as an agent-agnostic command and run on whatever coding agent the team uses.                                                                              | P1       |
| BR-32 | If the authenticated user is the PR author, the agent MUST explain that self-approval is unavailable and offer the remaining verdicts rather than attempting an action that will fail. | P1       |
| BR-33 | The agent SHOULD group repeated instances of the same finding into one entry with a count and locations, rather than listing each occurrence separately.                          | P2       |
| BR-34 | The agent SHOULD detect an existing review by the same user on the same PR and ask whether to supersede or add a new one.                                                        | P2       |
| BR-35 | The agent SHOULD support publishing findings as line-anchored inline comments, placing anchorable findings inline and the remainder in the review body, still as a single review event. | P2       |
| BR-36 | The agent SHOULD offer, at the end of a review, to save the complete review — including findings the reviewer dropped — to a local file, defaulting to not saving.                | P2       |
| BR-37 | The selection input SHOULD allow the reviewer to override a finding's severity as well as accept or drop it.                                                                     | P3       |
| BR-38 | The agent SHOULD support re-reviewing only the delta since a previously reviewed revision, and reporting which previously published findings appear resolved.                     | P3       |

## 8. Success Metrics & Measurable Outcomes

- **SC-01** — 100% of published findings were individually selected by the reviewer; zero findings
  reach a pull request without explicit human selection.
- **SC-02** — 100% of reported findings carry a file and line plus a cited source; zero unanchored
  assertions.
- **SC-03** — 100% of reviews state their coverage and limits, including which lenses did not run and
  what was excluded.
- **SC-04** — Repeated reviews of the same revision produce the same severity for the same finding.
- **SC-05** — Zero outward actions occur without a preview and a final go-ahead.
- **SC-06** — The agent never declines: 100% of resolvable pull requests yield either a published
  review or an explicit degradation with a stated reason and a manual path.
- **SC-07** — Of the S1 and S2 findings surfaced, a large majority are accepted by reviewers rather
  than dropped, evidencing that high-severity output is signal and not noise.
- **SC-08** — A reviewer completes the loop from URL to published review without leaving the terminal
  and without composing `gh` commands by hand.
- **SC-09** — Every approval published over an accepted blocker carries that acknowledgement in the
  review body; zero silent overrides.
- **SC-10** — Reviews of pull requests carrying a spec surface intent divergence and unauthorized
  scope that a diff-only review cannot detect.

## 9. Assumptions

- The reviewer is not the author. The agent is invoked in a fresh session with no memory of the code
  being written, which is what makes the review independent.
- The pull request carries its own spec, plan, and tasks in the branch when the project is
  spec-driven; when it does not, Journey 3 applies.
- The reviewer's working tree is usually on a different branch than the PR, so the PR's context must
  be read at its own revision.
- The `gh` CLI is installed and authenticated. The agent gates on this at startup and does not
  proceed without it.
- The reviewer has permission to submit a review on the target repository in the common case; the
  exact permission rules differ by visibility and role, so the agent reacts to failure rather than
  predicting it.
- The constitution in force for the review is the one on the base branch, since those are the rules
  the change is being merged into.
- A reviewer will drop some findings, and that is the intended behaviour rather than a defect — the
  human is the noise filter.
- What the reviewer wants to remember from a session, they can copy from the transcript; the agent
  stores nothing between runs.

## 10. Constraints

- Must conform to Spectra's constitution: a **self-contained extension**, an **agent-agnostic
  namespaced command** using `$ARGUMENTS`, and **context-aware** reading of real project state.
- The command performs **outward actions** on a shared system — publishing a review that may satisfy a
  branch-protection requirement and unblock a merge. Its effect is **read-write**, and every outward
  action requires explicit confirmation. This is the highest-consequence action in the Spectra roster
  and warrants a stricter gate than opening a pull request.
- Spectra introduces no new trust boundary: no credentials of its own, no new data path, no telemetry.
  All GitHub access flows through the reviewer's existing `gh` CLI authentication.
- Requires network access and the `gh` CLI at runtime. The `gh` pre-flight gate is a hard stop — the
  agent MUST NOT proceed without a working, authenticated `gh`.
- GitHub exposes a three-state review verdict directly (approve, request changes, comment). The agent
  uses this native model without translation.
- Line-anchored comments are only possible for lines present in the diff. The single-body form ships
  first; inline anchoring is a follow-on.
- The review is valid only for the revision it was performed against.

## 11. Dependencies

- **Input:** the pull request itself — metadata, diff, commit series, CI status — read from GitHub
  via `gh`.
- **Input:** the PR's spec, plan, tasks, and ADRs at its head revision; the constitution and ADRs in
  force on the base branch.
- **Capability (input and output):** the GitHub CLI (`gh`) for discovery, retrieval, and publication
  under the reviewer's existing authentication.
- **Upstream (context):** `speckit.spectra.create-pr` (BRD-002) produces the pull requests this agent
  reviews, closing the loop from implementation to review.
- **Upstream (standards):** `/speckit-constitution`, the Guardrails agent, the Domain Analyzer
  (BRD-001), and `speckit.spectra.adr` author the standards this agent cites. The quality of guardrail
  findings is bounded by the quality of those documents.
- **Downstream (possible):** `/speckit-tasks`, if accepted blockers are later handed off as fix work.
- **Delivery (roster update):** On release, `agents-list.json` must be updated to include the
  `review-pr` agent with its description, and the README agents table regenerated via
  `python tools/generate_agent_docs.py`. This happens once the agent is developed, not before.

## 12. Risks & Mitigations

| Risk                                                                                         | Impact | Likelihood | Mitigation                                                                                                          |
| -------------------------------------------------------------------------------------------- | ------ | ---------- | ------------------------------------------------------------------------------------------------------------------- |
| False positives erode reviewer trust and the agent stops being used                          | H      | H          | Anchor and cite every finding (BR-09); confidence gating so uncertain findings become Questions (BR-11); human selection filter (BR-18); group repeats (BR-33). |
| Unreviewed AI output published under a human's name                                          | H      | M          | Nothing pre-selected and empty selection posts nothing (BR-18); accepted-and-dropped confirmation (BR-20); preview and final go-ahead (BR-23). |
| An approval unblocks a merge the reviewer did not intend                                      | H      | L          | Verdict always chosen by the human (BR-21); contradictions challenged with typed confirmation and recorded (BR-22); preview before publishing (BR-23). |
| A real blocker is waved through because its severity was misjudged                            | H      | M          | Stated severity rubric with floors for constitution and compliance violations (BR-10); overrides recorded in the published body (BR-22). |
| Review overstates its coverage and creates false assurance                                    | H      | M          | Mandatory coverage-and-limits statement (BR-08, BR-15); lenses not run are never reported as passed (BR-13); size limits declared (BR-14). |
| Reviewing the wrong revision — local tree, or code superseded mid-session                     | M      | M          | Pin and report the revision (BR-02); read context at the PR's revision (BR-03); re-check before publishing (BR-24).  |
| `gh` CLI not installed or not authenticated blocks the reviewer entirely                      | M      | L          | Hard gate with a clear, actionable error message stating exactly what to run (BR-28); this is a deliberate trade-off favouring correctness over partial operation. |
| Duplicate or stacked reviews clutter the pull request                                         | L      | M          | Detect an existing review by the same user and ask (BR-34).                                                         |
| Guardrail findings are weak because the constitution is thin                                  | M      | M          | Dependency stated explicitly; the Guardrails and Domain Analyzer agents own improving the source documents.          |
| Volume overwhelms the author and the important findings are missed                            | M      | M          | Ranked presentation with collapsed minors and nits (BR-15); grouping of repeats (BR-33); human curation before publishing. |

## 13. Open Questions

- **Should the review be offered by a hook, or only on demand?** Offering it after `create-pr` would
  close the loop, but self-review conflicts with the independence this agent depends on. On-demand
  only is the safe default — is there a hook worth adding for a *different* actor?
- **Where should the optional saved review live**, and should it be ignored by version control? The
  reviewer is typically not on the PR's branch, so the spec directory is the wrong home.
- **Should a recommended verdict take CI status into account** — for example, never recommending
  approve while required checks are failing?
- **Is there a cap on how many findings to surface**, and if so, what is dropped and how is that
  disclosed?
- **How should Questions be published?** Mixed into the review body, or held back as a separate
  lighter-weight comment given they are requests for information rather than defects?
- **Should draft pull requests be reviewed** by default, warned about, or declined?
- **In a monorepo with code ownership rules**, should the review scope to the paths the reviewer owns,
  or always cover the whole diff?
- **What exactly can a reviewer submit** on public versus private repositories, and at which
  permission level? To be verified during implementation rather than assumed.
- **Should the agent support reviewing an arbitrary commit range** rather than a whole pull request?

## 14. Glossary

| Term                        | Definition                                                                                                                                    |
| --------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| PR                          | Pull request — a GitHub request to merge one branch into another.                                                                              |
| Conformance review          | Review that judges a change against the intent and standards it was authorized under, not only against the code in the diff.                   |
| Intent divergence           | A disagreement between the diff and the spec. Resolution needs a human: either the code is wrong or the spec is stale.                          |
| Guardrail violation         | A change that contradicts an explicit constitution or ADR clause, reported with that clause quoted.                                            |
| Craft finding               | A conventional code-review finding — correctness, security, tests, performance, maintainability.                                                |
| Unauthorized scope          | A change in the diff that no task or requirement calls for; scope creep detected by reverse traceability.                                       |
| Lens                        | One focused review pass over the diff (security, tests, API contract, and so on), selected based on what the change touches.                    |
| Severity (S1–S4, Question)  | Blocker, Major, Minor, Nit, and Question — how much a finding should hold up the merge, assigned from a stated rubric.                          |
| Confidence                  | How certain the agent is that a finding is real; a separate axis from severity, and a cap on it.                                                |
| Verdict                     | The outcome the reviewer submits: approve, request changes, or comment only.                                                                    |
| Selection                   | The reviewer's choice of which findings to publish. Nothing is pre-selected; an empty selection publishes nothing.                              |
| Head revision               | The specific commit the review was performed against. A review is only valid for that revision.                                                |
| Coverage and limits         | The explicit statement of which lenses ran, which did not and why, and what was excluded from review.                                            |
| `gh` CLI                    | GitHub's official command-line interface, used for all pull request interaction — discovery, retrieval, and publication.                          |
| Governance change           | A pull request that modifies the constitution or an ADR — always surfaced for human attention regardless of severity.                            |
