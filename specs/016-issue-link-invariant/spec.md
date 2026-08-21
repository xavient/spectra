# Feature Specification: A Supplied Issue Always Reaches the Pull Request

**Feature Branch**: `016-issue-link-invariant`

**Created**: 2026-08-21

**Status**: Draft

**Input**: Maintainer question — "when using `create-pr` we pass the issue to it; does that get saved in the PR as
`Closes <issue>`?" Verification found the rendering already correct, and one loophole: the reference is presentational, so
a project override that removes the **Related Issues** section drops the link entirely.

## Current State (verified in 1.9.0)

Rendering is already right. `spectra/commands/create-pr.md` Step 9 writes a closing keyword (`Closes #42`) when the base
is the repository's default branch, a plain `#42` reference on any other base — because GitHub ignores closing keywords
outside the default branch, creating no link and closing nothing — and a full URL for an issue in another repository.
`spectra/templates/pr-template.md` carries a **Related Issues** section repeating that rule in its guidance.

The loophole is in how the two interact:

| Line | Says |
|---|---|
| `create-pr.md:340` | *"Related Issues — per Step 9, or the whole section deleted when there is no issue."* |
| `create-pr.md:352` | *"Honour the template; do not repair it. If the resolved template drops sections, follow it as authored and mention the omission once."* |

Together those mean a project whose `.specify/templates/overrides/pr-template.md` has no Related Issues section gets a
pull request with **no issue link at all** — the agent notes the omission in chat and opens an unlinked PR. Passing
`--issue` then does nothing to the artifact it was passed for.

Nothing in the test suite covers it: `tests/test_create_pr_flow.py` asserts the *command* states the keyword rule, and no
assertion checks that the reference reaches the body.

## Clarifications

- Q: Should an override be able to remove the issue link?
  → A: **No.** An override governs *shape*, not whether a functional link exists. This is the same distinction
  `review-template` already makes for the revision anchor, the AI-assisted disclosure, and the coverage statement: those
  are command-emitted and survive any override.
- Q: Where does the reference go when the template has no section for it?
  → A: The command appends a short section and says once that it did so, and why. Silent insertion would be as surprising
  as silent omission.
- Q: Does this change the rendering rules?
  → A: No. Keyword on the default branch, plain reference elsewhere, full URL cross-repository — all unchanged.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A supplied issue is always linked (Priority: P1)

A team overrides `pr-template.md` and, in trimming it, removes **Related Issues**. They still run
`create-pr --issue 42`, and the pull request still references issue 42.

**Why this priority**: it is the whole point of the argument. An `--issue` that sometimes does nothing is worse than no
argument, because the failure is silent and the PR looks complete.

**Independent Test**: override the template without a Related Issues section, run with `--issue <n>`, and confirm the
published body references the issue and the run says the section was added.

**Acceptance Scenarios**:

1. **Given** an issue and a template **with** a Related Issues section, **When** the body is composed, **Then** the
   reference goes in that section, rendered per the base branch — unchanged from 1.9.0.
2. **Given** an issue and a template **without** one, **When** the body is composed, **Then** the command appends a short
   Related Issues section carrying the reference, and states once that it added it because the template had no place for
   it.
3. **Given** **no** issue, **When** the body is composed, **Then** nothing is appended and any Related Issues section in
   the template is removed — no placeholder, no empty heading.
4. **Given** either case, **When** the reference is rendered, **Then** the base-branch rules apply exactly as before:
   keyword on the default branch, plain reference elsewhere, full URL cross-repository.
5. **Given** an appended section, **When** the reviewer sees the pre-publish summary, **Then** the appended text is part
   of what they approve.

---

### User Story 2 - The template keeps the guidance that explains the rule (Priority: P3)

A maintainer editing `pr-template.md` cannot quietly delete the explanation of why a closing keyword is default-branch
only.

**Why this priority**: it protects an explanation rather than behaviour — the command owns the rule either way — but an
unexplained rule is one edit from being "simplified".

**Independent Test**: remove the default-branch caveat from the shipped template and confirm the suite fails.

**Acceptance Scenarios**:

1. **Given** the shipped template, **When** the suite runs, **Then** it asserts a Related Issues section exists and that
   its guidance states the default-branch condition.

### Edge Cases

- **The template has a differently-named section for issues** (say `## Ticket`) — treat it as the place for the
  reference; append nothing. The obligation is that the reference appears, not that a heading matches a string.
- **The template mentions issues only in a comment** — comments are deleted when filling, so that is not a place; append.
- **The issue could not be resolved** (`gh issue view` failed) — there is no reference to write, so nothing is appended;
  this is unchanged behaviour.

## Requirements *(mandatory)*

- **FR-001**: When an issue was supplied or detected and resolved, the reference MUST appear in the published pull request
  body regardless of the resolved template's structure.
- **FR-002**: When the resolved template provides a section for issues, the reference MUST go there.
- **FR-003**: When it does not, the command MUST append a short section carrying the reference, and MUST say once that it
  appended it and why.
- **FR-004**: When there is no issue, nothing MUST be appended, and any issue section in the template MUST be removed
  rather than left empty.
- **FR-005**: The rendering rules MUST be unchanged: closing keyword only when the base is the repository's default
  branch, plain reference otherwise, full URL for another repository.
- **FR-006**: The honour-don't-repair rule MUST be narrowed to state that the issue reference is a command-emitted
  invariant, mirroring how `review-pr` treats its anchor, disclosure, and coverage statement.
- **FR-007**: An appended section MUST be visible in the pre-publish summary the reviewer approves.
- **FR-008**: The test suite MUST assert that the command names the issue reference as an invariant.
- **FR-009**: The test suite MUST assert that the shipped `pr-template.md` retains a Related Issues section whose
  guidance states the default-branch condition.
- **FR-010**: The extension version MUST bump to `1.9.1` — a patch: no new capability, one loophole closed — with
  catalog, changelog, and zip in sync.

## Success Criteria *(mandatory)*

- **SC-001**: With any override, a resolved issue is referenced in the published body.
- **SC-002**: A run with no issue produces no issue section and no appended text.
- **SC-003**: Rendering is byte-identical to 1.9.0 for a template that has the section.
- **SC-004**: `python -m unittest discover -s tests`, `tools/generate_agent_docs.py --check`, and a
  `tools/build_package.py` rebuild all pass.

## Assumptions

- Command files are prompts; the enforceable surface is their text plus the CI guard on it.
- "A section for issues" is judged by intent, not by an exact heading string — a team's `## Ticket` counts.
- This does not widen the command's write scope: it changes what the composed body contains, not what the command
  mutates.
