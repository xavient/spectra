# Implementation Plan: Spec Discovery Without the Feature Record

**Branch**: `017-spec-discovery-without-feature-record` | **Date**: 2026-08-22 | **Spec**: [spec.md](./spec.md)

## Summary

One discovery tier replaced. `review-pr` read `.specify/feature.json` at a pull request's head revision to find the spec;
Spec Kit now gitignores that file as per-checkout state, so the read is either a 404 or — in a project that committed it
earlier — a stale pointer to an unrelated feature. The tier becomes *a spec the reviewer names*, read at the same pinned
revision, asked for in the single context question the run already asks. Tiers 1 and 3 are untouched.

## Technical Context

**Language/Version**: Markdown command prompt; Python 3.9+ for tests

**Primary Dependencies**: unchanged — Spec Kit `>=0.11.0`, `gh` at run time

**Testing**: `python3 -m unittest discover -s tests`; `tools/generate_agent_docs.py --check`

**Constraints**: Markdown only; agent-agnostic; no change to the command's write scope; the one-question rule holds

**Scale/Scope**: one section rewritten and three lines adjusted in one command, two doc lines, one new test class, version
sync

## Evidence

| Claim | How it was verified |
|---|---|
| Spec Kit ignores `feature.json` by CLI rule, not project choice | `SPECIFY_GITIGNORE_CONTENT` in `specify_cli/shared_infra.py:22` (installed `specify 1.0.1`), routed through the managed-file writer at `shared_infra.py:627` |
| The rule reached this project with the Spec Kit upgrade | `.specify/.gitignore` first appears in commit `93f8c4c` ("upgraded spec-kit to 0.16.5") |
| A pre-existing copy stays tracked and shared | `git ls-files .specify/feature.json` → tracked; `git check-ignore -v --no-index` → matched by `.specify/.gitignore:6` |
| The shared copy is a stale pointer, not this PR's spec | `git show origin/main:.specify/feature.json` → `specs/016-issue-link-invariant` |
| The reliance is soft | `review-pr.md` tier 3 plus the no-spec rules in Step 5; the file is referenced nowhere else in `spectra/` |

## Constitution Check

| Principle | Status | Note |
|---|---|---|
| I. Spec-Driven Development | ✅ | This spec/plan/tasks set on branch `017-spec-discovery-without-feature-record`. |
| II. Single Self-Contained Extension | ✅ | No files added or removed from the package. |
| III. Agent-Agnostic Commands | ✅ | Prose only; no agent-specific syntax. |
| IV. Context-Aware by Default | ✅ | This is IV enforced rather than weakened: the command still reads real project context, and now refuses to read a file whose content is not context *about this pull request*. Availability was never the test — authority is. |
| V. Catalog and Package in Sync | ✅ | Manifest, catalog, changelog, and zip move together. |
| VI. Two Versioned Channels | ✅ | Extension channel only: 1.9.1 → 1.10.0. No tag, `VERSION` untouched. |
| VII. Documents Under One Declared Root | ✅ | Unaffected. |
| VIII. Shaped by Overridable Templates | ✅ | Unaffected; discovery is not template-shaped. |

**Amendment classification**: none.

**Extension version classification**: MINOR — 1.9.1 → 1.10.0. No argument or command is added or removed, but a
discovery tier is replaced and one question's wording changes, so behaviour differs observably from 1.9.1. Not a patch;
not breaking either, since every input that worked before still works.

## Phase 0 — Decisions

- **D1 — Remove the read rather than tolerate it.** A tier that resolves correctly in new projects (never) and incorrectly
  in old ones (a stale pointer) cannot be described honestly in a coverage statement. The command's one hard rule is that
  it must not produce a false coverage claim.
- **D2 — Replace the tier, don't drop it.** Dropping tier 2 outright would silently downgrade every addendum PR to a
  standalone review. A reviewer-named path preserves the coverage and improves its provenance: a human vouches for the
  baseline, and it is still read at the pinned revision.
- **D3 — Fold the ask into the existing question.** The run already asks once for an issue. Asking separately for a spec
  would double the interruptions for the case that needs it most. One question, two possible answers.
- **D4 — Name the forbidden sources, with reasons.** The branch-name ban survived because its reason was written down. The
  feature-record ban gets the same treatment — "per-checkout state… describes a working copy, never a pull request" —
  otherwise the next editor restores the tier to recover the addendum case.
- **D5 — A failed named read falls through, never substitutes.** The command may not go looking for a nearby spec. Tier 3
  is a supported outcome; a guessed baseline is not.

## Phase 1 — Design notes

`spectra/commands/review-pr.md`:

1. **Step 4, "Locating the spec"** — tier 2 rewritten as the reviewer-named path with its read revision and its
   fall-through; the branch-name paragraph widened into a two-item forbidden list carrying D4's reason; the
   absent-vs-unreachable paragraph reworded off "tier-2 miss"; the coverage line spells out the three sources.
2. **Step 4, the issue question** — becomes the run's single context question: both baselines in one ask when both are
   missing, a spec-only variant when the issue is already in hand, and an explicit one-question-per-run rule.
3. **The argument table** — `--issue` no longer suppresses the spec ask.
4. **Step 7 element 3** — spec status names how the spec was located.

`tests/test_review_pr_flow.py`: a `SpecDiscovery` class covering each clause, including `refuteStates` on the retired
read. One existing assertion moves from `means **no issue**` to `means **neither**`.

Docs: `spectra/README.md` step 4 and the `AGENTS_LIST.md` review-pr block gain a spec-discovery line.

## Risks

| Risk | Mitigation |
|---|---|
| Addendum PRs get reviewed standalone because reviewers skip the question | D2/D3: the ask is inline in the flow the reviewer is already answering, and the no-spec consequences are stated in the summary |
| A future editor restores the feature-record tier | D4 records the reason in the command; a `refuteStates` test fails the build if the read returns |
| Two questions creep back in | An explicit "one question per run" rule, asserted by test |
| A reviewer supplies a path from the base branch that is absent at head | D5: reported and treated as no spec, so the review never rests on an unpinned read |

## Complexity Tracking

> No violations. One tier swapped for a better-sourced one; no new surface.
