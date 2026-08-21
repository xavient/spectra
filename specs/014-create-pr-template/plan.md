# Implementation Plan: A Templated, Issue-Linked `create-pr`

**Branch**: `014-create-pr-template` | **Date**: 2026-08-21 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/014-create-pr-template/spec.md`

## Summary

Five changes to one command, plus its first template. `create-pr` gains an optional `--issue`, a registered and
overridable `pr-template` for the PR body, an offer to commit-and-push uncommitted work instead of warning about it, a
single consolidated confirmation gate where an undocumented base branch gets settled, and the removal of the
spec-branch-only restriction so bugs and chores can use it.

The template work is a straight application of Principle VIII, established last release for `adr` and `brd` — which
means the existing guard in `tests/test_document_templates.py` covers `pr-template` the moment it joins that map.

## Technical Context

**Language/Version**: Markdown command prompts (Spec Kit generic format); Python 3.9+ for maintainer tools and tests

**Primary Dependencies**: Spec Kit `>=0.11.0`; `gh` and `git` at run time (already declared optional in the manifest and
hard-gated inside the command)

**Storage**: none. The command emits a PR body to GitHub and writes no file into the project.

**Testing**: `python -m unittest discover -s tests`, `tools/generate_agent_docs.py --check`, plus the manual pass in
`test/README.md`

**Target Platform**: every agent and OS Spec Kit supports; all resolution and detection expressed as prompt instructions

**Constraints**: Markdown only — no scripts, binaries, or hooks in the package; agent-agnostic prompts (Principle III);
`gh` remains the sole route to GitHub; no credentials held

**Scale/Scope**: 1 new template, 1 command rewritten in five places, 1 manifest, 1 catalog entry, 1 changelog, 1 zip,
~5 doc files, test updates, 1 constitution clarification

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Note |
|---|---|---|
| I. Spec-Driven Development | ✅ | This spec/plan/tasks set on branch `014-create-pr-template`. |
| II. A Single Self-Contained Extension | ✅ | One new asset under the existing `spectra/templates/`; no new extension, no dependency. |
| III. Agent-Agnostic Commands | ✅ | Text only. `$ARGUMENTS` gains `--issue`; no agent-specific syntax. |
| IV. Context-Aware by Default | ✅ | Strengthened: the body is now built from the real diff and the project's own template rather than spec prose alone. |
| V. Catalog and Package in Sync | ✅ | Manifest, catalog, changelog, zip, landing page, and hand-authored prose all move in this change. |
| VI. Two Independently-Versioned Channels | ✅ | Extension channel only: 1.7.0 → 1.8.0. `VERSION` untouched, no tag. |
| VII. Documents Under One Declared Root | ✅ | Not engaged — a PR body is emitted to GitHub, not written under the artifact root. |
| VIII. Shaped by Overridable Templates | ✅ + clarified | `pr-template` is its third application. VIII's wording is clarified to cover emitted documents, not only files written to disk (FR-023). |

**Amendment classification**: PATCH — 1.7.0 → 1.7.1. The clarification states what VIII already intends; it adds no new
obligation. (A reader could argue "durable Markdown deliverable" excludes a PR body, which is exactly the ambiguity being
closed.)

**Extension version classification**: MINOR — 1.7.0 → 1.8.0. New argument, new template, new gate, one refusal relaxed.
No command renamed or removed.

**One rule under revision.** `create-pr`'s write scope currently forbids committing. FR-021 widens it to *commit with
explicit consent* while still forbidding edits to the spec, the constitution, and unrelated source. This is a deliberate
expansion, recorded here rather than slipped in: the alternative — warning about uncommitted work and opening a PR without
it — is the behavior the change exists to remove.

## Project Structure

```text
.specify/memory/constitution.md              # VIII covers emitted documents; 1.7.0 → 1.7.1
spectra/
├── templates/pr-template.md                 # NEW — 8 sections, no checklist
├── commands/create-pr.md                    # --issue, template resolution, commit offer, final gate, any-branch
├── extension.yml                            # + pr-template; description; version → 1.8.0
├── CHANGELOG.md                             # [1.8.0]
└── README.md                                # the create-pr section
catalog.json                                 # version → 1.8.0, updated_at
docs/
├── index.html                                # create-pr cdesc
└── packages/spectra.zip                     # rebuilt — must contain pr-template.md
AGENTS_LIST.md                               # create-pr prose block
test/README.md                               # manual passes for the new flow
tests/test_document_templates.py             # + create-pr.md → pr-template
tests/test_create_pr_flow.py                 # NEW — the behaviors checkable as command text
```

## Phase 0 — Decisions

**Settled by the maintainer:**

- **D1 — Documented base wins; otherwise ask at the gate.** Read the constitution's Version Control section and the
  `git` extension's config. A documented promotion flow is used and cited. With nothing documented, the command proposes
  a base and asks at the final gate — "This PR will be created to merge into `main`, is that correct?" — accepting a
  correction in the same breath. Inference is never treated as settled.
- **D2 — Commit on consent.** A dirty tree prompts *"there are uncommitted changes, should I proceed with committing and
  pushing first?"*, and a yes behaves like any ordinary "commit and push" request.
- **D3 — No checklist.** Dropped from the template. An agent cannot honestly self-certify a diff review.
- **D4 — Any branch.** Only detached HEAD and "already on the base" remain refusals; a spec branch simply has richer
  material to draw on.

**Established by research:**

- **D5 — A closing keyword is only written when the base is the default branch.** GitHub's documentation is explicit:
  *"The special keywords in a pull request description are interpreted only when the pull request targets the
  repository's default branch. If the pull request targets any other branch, then these keywords are ignored, no links
  are created, and merging the PR has no effect on the issues."* Since this command's whole purpose includes targeting
  `dev` in a promotion flow, writing `Closes #42` there would produce a section that looks right and does nothing. On a
  non-default base the command writes a plain `#42` reference — which still creates a cross-reference on the issue — and
  says auto-close will not happen on this merge.
- **D6 — Git records no parent branch.** `@{upstream}` is the tracking branch, and `git merge-base --fork-point` reads
  the reflog, so it yields nothing in a fresh clone or CI checkout, and nothing useful when two candidates share a
  commit. This is why D1 asks instead of inferring silently.

## Phase 1 — Design notes

Step order in the rewritten command:

1. Offer (unchanged, ungated).
2. `gh` hard gate (unchanged).
3. GitHub remote (unchanged).
4. `gh repo view` — now also the source of **`defaultBranchRef` for the closing-keyword decision** (D5), not only for
   the base fallback.
5. **Branch sanity** — was one-branch-per-spec; becomes detached-HEAD and equal-to-base refusals only, with a note that a
   spec branch yields richer body material (D4).
6. Duplicate-PR check (unchanged).
7. **Base derivation** — documented flow cited, else proposal (fork point if determinable, else default branch) carried
   to the gate as a question (D1).
8. **Readiness** — dirty tree offers commit-and-push with the file list, a credential-shaped-file callout, hooks intact;
   clean-but-unpushed asks to push, as today (D2).
9. **Gather the issue** — `--issue`, else ask once, else nothing; validate with `gh issue view` (FR-001–FR-003).
10. **Resolve `pr-template`** through the five-layer stack; report the path (Principle VIII).
11. **Compose the body** — template sections filled from spec artifacts when present, commits and
    `git diff --name-status <base>...HEAD` always; issue rendered per D5.
12. **The final gate** — one summary, one yes/no; a base correction loops back to re-check the target's existence and
    recompute the keyword decision.
13. Create with `gh pr create --head … --body-file -` (unchanged mechanics).
14. Report — PR URL, base and its origin, template path, what was committed/pushed, and the auto-close caveat when it
    applies.

## Risks

| Risk | Mitigation |
|---|---|
| Committing sweeps in unrelated or secret files | List files before staging, call out credential-shaped names, stage only what was listed, never `git add -A` blindly, never `--no-verify` |
| The agent writes a closing keyword on a `dev`-targeted PR | D5 is a requirement (FR-013) and a test assertion; the report states the consequence |
| A base correction at the gate skips validation | FR-012 requires re-checking existence and recomputing the keyword decision |
| Relaxing the spec-branch rule weakens traceability | The spec branch path is unchanged and still preferred; only the refusal is removed |
| The template drifts from the command's inline skeleton | The existing heading-parity guard covers it once `pr-template` joins the map |

## Complexity Tracking

> No violations. The one-rule expansion (FR-021) is a deliberate scope change, recorded in the Constitution Check above
> rather than treated as incidental.
