# Implementation Plan: Review Context, an Overridable Review Template, and Inline Suggestions

**Branch**: `015-review-context-and-template` | **Date**: 2026-08-21 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/015-review-context-and-template/spec.md`

## Summary

Four changes to `review-pr`, in rising order of risk. A linked issue becomes optional extra context in both PR shapes —
auto-detected, asked for once, never required. The hard-coded review body becomes `review-template`, registered and
overridable, with a deliberately narrower remit than the other templates. Accepted findings whose anchors sit inside the
diff are published as **inline comments**, carrying ` ```suggestion ` blocks where the fix is mechanical. And coverage
states how much of the constitution was actually applicable, so a thin constitution reads as thin.

Nothing about the command's judgment moves: the lens set, the anchor rule, the severity rubric and its floors, the
confidence cap, the selection grammar, and the mechanical verdict derivation all stay exactly where they are.

## Technical Context

**Language/Version**: Markdown command prompts (Spec Kit generic format); Python 3.9+ for tools and tests

**Primary Dependencies**: Spec Kit `>=0.11.0`; `gh` at run time — now including `gh api` for the reviews endpoint

**Storage**: none. The command stores nothing between runs; the published review is the record.

**Testing**: `python -m unittest discover -s tests`; `tools/generate_agent_docs.py --check`; the manual pass in
`test/README.md`, extended for the issue prompt, an override, and an inline suggestion

**Target Platform**: every agent and OS Spec Kit supports; all detection and resolution expressed as prompt instructions

**Constraints**: Markdown only — no scripts, binaries, or hooks; agent-agnostic prompts (Principle III); `gh` remains the
sole route to GitHub; no credentials held; one atomic publication

**Scale/Scope**: 1 new template, 1 command edited in ~6 places, 1 manifest, 1 catalog entry, 1 changelog, 1 zip,
~5 doc files, test updates

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Note |
|---|---|---|
| I. Spec-Driven Development | ✅ | This spec/plan/tasks set on branch `015-review-context-and-template`. |
| II. A Single Self-Contained Extension | ✅ | One new asset under the existing `spectra/templates/`. |
| III. Agent-Agnostic Commands | ✅ | Text only. `$ARGUMENTS` gains `--issue`; the API call is a `gh` invocation, not agent-specific syntax. |
| IV. Context-Aware by Default | ✅ | Strengthened on both axes: a third context tier (the issue) and honesty about how much of the constitution applied. |
| V. Catalog and Package in Sync | ✅ | Manifest, catalog, changelog, zip, landing page, and hand-authored prose all move together. |
| VI. Two Independently-Versioned Channels | ✅ | Extension channel only: 1.8.0 → 1.9.0. `VERSION` untouched, no tag. |
| VII. Documents Under One Declared Root | ✅ | Not engaged — a review is emitted to GitHub, not written under the artifact root. |
| VIII. Shaped by Overridable Templates | ✅ | `review-template` is its fourth application, and the one the 1.7.1 clarification named ("a review comment"). Its narrower remit is a scope limit, not an exemption — see D3. |

**Amendment classification**: none. Principle VIII already covers emitted documents after 1.7.1, and D3's carve-out is a
statement about *what the template governs*, not a loosening of any rule.

**Extension version classification**: MINOR — 1.8.0 → 1.9.0. New argument, new template, new publication capability. No
command renamed or removed; a run with no issue and no override behaves as it does today apart from the added coverage
line and inline placement.

**The one rule, re-read.** The command's rule is *"your only permitted mutation is publishing one review, after an
explicit go-ahead"*, and *"all pull request interaction goes through `gh`"*. Inline comments do not widen that: the review
is still one review, still one go-ahead, still `gh`. What changes is the verb — `gh api` instead of `gh pr review` —
because `gh pr review` cannot carry inline comments. Worth stating plainly rather than leaving to inference.

## Project Structure

```text
spectra/
├── templates/review-template.md         # NEW — summary shape + inline comment shape
├── commands/review-pr.md                # --issue, issue tiering, template, inline comments, coverage
├── extension.yml                        # + review-template; description; version → 1.9.0
├── CHANGELOG.md                         # [1.9.0]
└── README.md                            # the review-pr section
catalog.json                             # version → 1.9.0, updated_at
docs/
├── index.html                            # review-pr cdesc + arguments
└── packages/spectra.zip                 # rebuilt — must contain review-template.md
AGENTS_LIST.md                           # review-pr prose block
test/README.md                           # manual passes for the new flow
tests/test_document_templates.py         # + review-pr.md → review-template
tests/test_review_pr_flow.py             # NEW — issue flow, template remit, inline rails, atomic publish
```

## Phase 0 — Decisions

**Settled with the maintainer:**

- **D1 — No criteria file.** The constitution is the criteria. A second policy file would compete with it, require
  precedence rules, need its own citable IDs to satisfy the anchor rule, and split standards across two locations.
  Everything a criteria file would have said — test expectations, path obligations, compliance duties, enforceable style
  — belongs in the constitution, which is what the Guardrails agent writes and what this command already reads at
  `baseRefOid`. Operational knobs (budget, exclusions, risk ranking) are configuration rather than policy and would
  belong in Spec Kit's extension-config convention if they are ever needed; ownership mapping is `CODEOWNERS`, which
  already exists.
- **D2 — The issue is context in both shapes, weighted differently.** Spec-less: the issue is the only intent source, so
  the traceability lens runs against it. Spec-backed: the spec authorizes and the issue is background. The prompt states
  which situation it is in, because "no spec found; an issue would give me something to check against" and "there's a
  spec; an issue would add background" are different questions.
- **D3 — The template governs presentation, not the machine contract.** Three elements stay command-emitted: the
  `<!-- spectra:review-pr revision=… -->` anchor (how `--since` and self-review detection find previous reviews), the
  AI-assisted/human-curated disclosure line, and the coverage statement (what stops a review implying assurance it did
  not earn). Giving the template a narrower scope is cleaner than letting it own these and then policing the result: an
  override cannot break a contract it never held.
- **D4 — Judgment stays in the command.** Severity rubric, floors, confidence cap, anchor rule, selection grammar,
  verdict derivation. If a project could redefine "Blocker" or make approval recommendable over open Blockers, review
  consistency — the reason this command exists — would become per-project.
- **D5 — Placement is derived; `<n>:body` is the escape hatch.** The reviewer already decides *what* is published;
  asking them to also decide *where* each finding goes is a second decision with no better basis than the diff itself.

**Established by research:**

- **D6 — `closingIssuesReferences` exists, and is not sufficient alone.** `gh pr view --json` accepts the field
  (verified against `gh` 2.97.0 by listing available fields). But GitHub only creates that structured link when a PR
  targets the **default branch** — the same rule that made `create-pr` write a plain reference on other bases in 1.8.0.
  So on a `dev`-targeted PR the field is empty while the body says `Closes #42`. Structured detection first, text
  fallback second; without the fallback the command would ask for an issue already on the PR.
- **D7 — Inline comments no longer need position arithmetic.** The reviews endpoint accepts `path` + `line` + `side`
  (and `start_line`/`start_side` for a range), so the "diff-position arithmetic" cited in the command's deferral note is
  obsolete. `gh api --method POST repos/{owner}/{repo}/pulls/{number}/reviews --input -` posts body, comments, and event
  in one call, which is strictly better than two calls: there is no partial-review state to explain.
- **D8 — A suggestion is one click from a commit.** ` ```suggestion ` blocks render with a "Commit suggestion" button, so
  the author can apply the command's text without reading it closely. That is why FR-025/FR-026 are requirements rather
  than advice, and why FR-027 puts every suggestion in the pre-publish preview verbatim.

## Phase 1 — Design notes

Where each change lands in the existing 12 steps:

| Step | Change |
|---|---|
| User Input | `--issue <url-or-number>` added to the argument table |
| One rule | a sentence naming `gh api` as the publication route, with the reason |
| Step 3 (budget/diff) | record the **commentable ranges** from the patch while it is already in hand (FR-023) |
| Step 4 (context) | a third tier: detect → validate → ask once → proceed without; state which situation the prompt is in |
| Step 5 (analyze) | traceability runs against the issue when there is no spec; issue-vs-spec conflict is a Question |
| Step 6 (classify) | the issue-sourced severity cap (FR-011) |
| Step 7 (summary) | constitution applicability line; issue status |
| Step 8 (selection) | `<n>:body` added to the grammar table |
| Step 10 (preview) | resolve `review-template`; preview inline comments and suggestions verbatim |
| Step 11 (publish) | one `gh api` call; demote-and-retry on a line rejection |
| Step 12 (report) | resolved template path; what went inline vs body; the issue used |
| Not in this release | the inline-comment deferral is replaced by what ships |

**The template's two shapes.** `review-template.md` defines the summary body (Summary, Blockers, Major, Minor / Nits,
Questions, Acknowledged blocker — with `- [ ]` on the two actionable severities) **and** the inline comment shape (what
is wrong, the cited source, impact, fix, and where a suggestion goes). One asset, two shapes, because both are findings
presentation and a team that restyles one will want the other to match.

## Risks

| Risk | Mitigation |
|---|---|
| A suggestion is applied blind and is wrong | Mechanical-and-complete-only (FR-025), a hard exclusion list (FR-026), verbatim preview (FR-027) |
| An override drops the anchor or coverage | They are command-emitted, outside the template's remit (D3) |
| The API rejects one comment and the whole review fails | Lines validated locally from the patch first (FR-023); demote-and-retry with disclosure as the fallback (FR-029) |
| Prompt fatigue from asking for an issue every run | Asked once per run, skippable, and `--issue` skips it entirely |
| An issue's text is treated as instruction | FR-010 states it is data about intent, never direction |
| Teams read a thin constitution as a clean review | FR-032–FR-034 quantify applicability instead of implying it |

## Complexity Tracking

> No Constitution Check violations. D3's narrower template remit is recorded above so a later reader does not mistake it
> for an exemption from Principle VIII.
