# Implementation Plan: A Supplied Issue Always Reaches the Pull Request

**Branch**: `016-issue-link-invariant` | **Date**: 2026-08-21 | **Spec**: [spec.md](./spec.md)

## Summary

One loophole, closed. `create-pr` renders an issue reference correctly but treats it as presentation, so a project
override that trims the **Related Issues** section drops the link and `--issue` silently does nothing. The reference
becomes a command-emitted invariant: it goes in the template's section when there is one, is appended with a note when
there is not, and disappears only when there is no issue.

No rendering change. No new capability. A patch.

## Technical Context

**Language/Version**: Markdown command prompt; Python 3.9+ for tests

**Primary Dependencies**: unchanged — Spec Kit `>=0.11.0`, `gh` at run time

**Testing**: `python -m unittest discover -s tests`; `tools/generate_agent_docs.py --check`

**Constraints**: Markdown only; agent-agnostic; the command's write scope is untouched

**Scale/Scope**: 2 prose edits in one command, 1 clarifying line in one template, 2 test assertions, version sync

## Constitution Check

| Principle | Status | Note |
|---|---|---|
| I. Spec-Driven Development | ✅ | This spec/plan/tasks set on branch `016-issue-link-invariant`. |
| II. Single Self-Contained Extension | ✅ | No new files in the package. |
| III. Agent-Agnostic Commands | ✅ | Prose only. |
| IV. Context-Aware by Default | ✅ | Unaffected. |
| V. Catalog and Package in Sync | ✅ | Manifest, catalog, changelog, and zip move together. |
| VI. Two Versioned Channels | ✅ | Extension channel only: 1.9.0 → 1.9.1. No tag, `VERSION` untouched. |
| VII. Documents Under One Declared Root | ✅ | Unaffected. |
| VIII. Shaped by Overridable Templates | ✅ | This is VIII working as intended. VIII requires a resolved template be *honoured*; it does not require a command to abandon a functional obligation because a template has no heading for it. `review-template` already draws exactly this line for its anchor, disclosure, and coverage statement — the same distinction, now applied to `pr-template`. |

**Amendment classification**: none. The carve-out is a statement about what the template governs, consistent with the
precedent already in the codebase.

**Extension version classification**: PATCH — 1.9.0 → 1.9.1. No argument, command, or template added; one silent-failure
path removed.

## Phase 0 — Decisions

- **D1 — The reference is functional, not presentational.** `--issue` exists to link the PR. A shape choice in a template
  cannot cancel it, any more than an override of `review-template` can delete the coverage statement. This is the
  precedent set one release ago, applied consistently.
- **D2 — Append, and say so.** Silent insertion is as surprising as silent omission. One line — "your template has no
  section for issues, so I added one" — leaves the user able to fix their template if they would rather place it
  themselves.
- **D3 — Judge the section by intent, not by heading text.** A team's `## Ticket` or `## Linked work` is a place for the
  reference. Matching on the literal string "Related Issues" would append a duplicate section to a template that already
  handles issues perfectly well.
- **D4 — Rendering is untouched.** The default-branch keyword rule shipped in 1.8.0 and was verified again here; this
  change is about *whether* the reference appears, never *how*.

## Phase 1 — Design notes

Two edits in `spectra/commands/create-pr.md`:

1. **Step 10's filling rules** — the Related Issues bullet becomes explicit: the reference goes in the template's issue
   section, or an appended one, and vanishes only when there is no issue.
2. **The honour-don't-repair rule** — gains the carve-out, worded as a scope statement rather than an exception: the
   template governs shape; a resolved issue reference is the command's obligation.

One edit in `spectra/templates/pr-template.md`: the Related Issues guidance notes that removing the section does not
remove the link — the command will append one — so a team trimming the template knows what to expect.

## Risks

| Risk | Mitigation |
|---|---|
| A duplicate section appended to a template that already handles issues under another name | D3: judge by intent, not heading text |
| The append surprises a team that trimmed deliberately | D2: it is stated once, and the reviewer sees it in the pre-publish summary (FR-007) |
| The carve-out reads as a licence to override templates generally | Worded as scope, and the Constitution Check above records why it is consistent with VIII |

## Complexity Tracking

> No violations. The one judgment call — that a functional link outranks a template's shape — is recorded in D1 with its
> precedent.
