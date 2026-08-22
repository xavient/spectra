# Feature Specification: Spec Discovery Without the Feature Record

**Feature Branch**: `017-spec-discovery-without-feature-record`

**Created**: 2026-08-22

**Status**: Draft

**Input**: Maintainer report — "as per the new spec-kit update, `feature.json` is ignored and not present in the remote.
`review-pr` relies on it, but it's not really mandatory. Validate that, and check if we can safely remove the reliance."

## Current State (verified against 1.9.1 and specify 1.0.1)

`spectra/commands/review-pr.md` Step 4 locates the governing spec through a three-tier chain (FR-006a of
[008-review-pr](../008-review-pr/spec.md)). Tier 2 reads `feature_directory` from `.specify/feature.json` at the pull
request's head revision, over `gh api repos/$REPO/contents/...`.

Spec Kit now keeps that file out of version control. The rule is not a project choice — it is a constant in the CLI
itself, `SPECIFY_GITIGNORE_CONTENT` in `specify_cli/shared_infra.py`, written into a managed `.specify/.gitignore` on
install and refresh:

```text
# Local pointer to the current feature directory. Rewritten every time you
# switch features, so it is per-checkout state rather than something to share.
feature.json
```

Two distinct consequences follow, and the second is the reason to act:

| Project | What tier 2 does now |
|---|---|
| Initialized or refreshed on Spec Kit ≥ 0.16.5 | The path is not in the tree, so the read 404s. Tier 2 never resolves; a wasted call, no wrong answer. |
| Committed the file before the ignore rule landed | Git keeps tracking it, so it is still on the remote — carrying whatever feature **its last committer** was on. |

This repository is the second case: `git ls-files .specify/feature.json` shows it tracked, and
`git show origin/main:.specify/feature.json` returns `{"feature_directory": "specs/016-issue-link-invariant"}`. A review
of any PR from another branch would adopt `specs/016-…/spec.md` as that PR's authorizing spec and report traceability
against it. That is the failure mode the same step already forbids for branch-name inference: *"a wrong guess means
reviewing a change against someone else's spec, which is worse than having no spec at all."*

The reliance is soft. Tier 3 already terminates the chain, and the no-spec path is fully specified — traceability
reported as not run, guardrails at full strength, intent-class findings capped at Question. Nothing else in the package
reads the file: the only references are `review-pr.md` lines 249–250 and one line in `spectra/README.md`.

**Supersession.** This feature replaces tier 2 of FR-006a in [008-review-pr](../008-review-pr/spec.md). Tiers 1 and 3 of
that requirement stand unchanged, as does its ban on branch-name inference; the `discoverySource` values recorded in that
feature's data model become `diff`, `named`, `none`.

## Clarifications

- Q: Is removing tier 2 a coverage loss?
  → A: For the **addendum case** — a spec merged by an earlier PR, so absent from this diff — yes, if nothing replaces it.
  So something replaces it: the reviewer names the path, in the question the run already asks.
- Q: Why not keep tier 2 and treat a stale read as best-effort?
  → A: A discovery tier that is sometimes right and sometimes points at an unrelated spec cannot be reported honestly in
  the coverage statement. Silence about a spec is recoverable; a confident wrong baseline is not.
- Q: Does this add a second question to the run?
  → A: No. The command asks for authorizing context **once**. When both are missing, the spec and the issue are asked for
  in that one question. `--issue` answers only the issue half.
- Q: Does the no-spec behaviour change?
  → A: No. Tier 3 is unchanged, in wording and in consequence.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - No spec is ever guessed (Priority: P1)

A reviewer runs `review-pr` on a PR in a project that still has `.specify/feature.json` committed. The review is not
measured against the spec that file points at.

**Why this priority**: it is the correctness bug. A review that claims traceability against a spec that never authorized
the change is worse than one that admits it had no spec, because the false claim is invisible to the reviewer.

**Independent Test**: read the command file — the feature record must be named as a forbidden source with its reason, and
no instruction to read `feature_directory` may remain.

**Acceptance Scenarios**:

1. **Given** a PR whose diff contains `specs/<dir>/spec.md`, **When** the spec is located, **Then** it comes from the diff
   — unchanged from 1.9.1.
2. **Given** a PR whose diff carries no spec, **When** discovery runs, **Then** `.specify/feature.json` is not read at any
   revision.
3. **Given** a project that still tracks that file, **When** the review is published, **Then** no spec is attributed to
   the PR on its basis.
4. **Given** either forbidden guess — branch name or feature record — **When** an editor reads the command, **Then** the
   prohibition and the reason for it are stated, not merely implied.

---

### User Story 2 - The addendum case survives, on evidence (Priority: P2)

A PR adds code for a spec that merged last week. The reviewer is asked for the spec path, gives it, and the review runs
with full traceability.

**Why this priority**: it preserves the coverage tier 2 was written for, without the dependency that made it unreliable.

**Independent Test**: name a path when asked; the review reads it at the pinned head revision and reports the spec as
found and how.

**Acceptance Scenarios**:

1. **Given** no spec in the diff, **When** the run asks for context, **Then** it asks for a spec path and an issue in
   **one** question.
2. **Given** a path that resolves at `headRefOid`, **When** it is read, **Then** the review proceeds with a spec and the
   coverage statement records that the reviewer named it.
3. **Given** a path that does not resolve at that revision, **When** the read fails, **Then** the command says so and
   falls through to the standalone review instead of substituting another file.
4. **Given** an empty answer, "no", or "skip", **When** the run continues, **Then** it is the no-spec path, and the
   question is not repeated.
5. **Given** `--issue` was supplied and the diff has no spec, **When** the run asks, **Then** it asks for the spec alone.

### Edge Cases

- **The reviewer names a directory rather than a file** — read `spec.md` inside it; the tier is about locating the spec,
  not about exact typing.
- **The named path exists on the base branch but not at the head revision** — that is a resolve failure at the pinned
  revision, so tier 3. Reviews are pinned; a spec read from anywhere else is not evidence about this revision.
- **A project deliberately commits `feature.json`** — still not read. Its meaning is per-checkout regardless of whether a
  team chose to share it.
- **`--issue` supplied, spec found in the diff** — no question at all, exactly as in 1.9.1.

## Requirements *(mandatory)*

- **FR-001**: `review-pr` MUST NOT read `.specify/feature.json`, at any revision, for any purpose.
- **FR-002**: The command MUST name both forbidden inference sources — the branch name and the feature record — and MUST
  record why each is forbidden.
- **FR-003**: Tier 2 MUST become a spec path the reviewer names, read at `headRefOid`.
- **FR-004**: A named path that does not resolve at the pinned revision MUST be reported and MUST fall through to the
  no-spec path, never to a substituted file.
- **FR-005**: The run MUST ask for authorizing context at most once. When both spec and issue are absent, both MUST be
  requested in that single question.
- **FR-006**: `--issue` MUST continue to suppress the issue question, and MUST NOT suppress the spec question when the
  diff carries no spec.
- **FR-007**: The coverage statement MUST continue to state which of the three sources resolved, with the second now
  reported as named by the reviewer.
- **FR-008**: Tier 1 and tier 3 behaviour MUST be unchanged, including the no-spec consequences (traceability not run,
  guardrails at full strength, intent findings capped at Question).
- **FR-009**: The test suite MUST assert every clause above that lives in the command's text, including a mutation guard
  that fails if the feature-record read returns.
- **FR-010**: The extension version MUST bump to `1.10.0` — a discovery tier is replaced, so behaviour changes
  observably — with manifest, catalog, changelog, and zip in sync.

## Success Criteria *(mandatory)*

- **SC-001**: No instruction to read `.specify/feature.json` remains anywhere in `spectra/` — the only occurrences are the
  prohibition itself, the changelog entry, and the documentation of both.
- **SC-002**: A PR that ships its spec produces a review identical in structure to 1.9.1.
- **SC-003**: A PR with no spec in its diff yields exactly one context question.
- **SC-004**: `python3 -m unittest discover -s tests`, `tools/generate_agent_docs.py --check`, and a
  `tools/build_package.py` rebuild all pass.

## Assumptions

- Command files are prompts: the enforceable surface is their text plus the CI guard on it.
- Spec Kit will not reintroduce a remote-readable feature pointer; the gitignore rule is in the CLI, not in a template a
  project might diverge from.
- Untracking this repository's own committed `feature.json` is repository hygiene, not part of the published extension —
  it stops the stale pointer being shared, and is worth doing for the same reason.
