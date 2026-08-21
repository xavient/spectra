# Implementation Plan: One Document-Output Convention — a Declared Artifact Root

**Branch**: `012-doc-output-convention` | **Date**: 2026-08-21 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/012-doc-output-convention/spec.md`

## Summary

Two shipped document-producing agents each invented their own output location: `adr` writes
`Docs/ADR/ADR-NNN-*.md` and `brd` writes `/brds/NNN-*.md`. This change replaces both with one convention —
`<artifact-root>/adr/` and `<artifact-root>/brd/`, project-relative and lowercase, defaulting to `docs/` — and records
that convention as constitution Principle VII so every future document agent inherits it instead of choosing again.

Because `docs/` is GitHub Pages' only non-root branch source and the default source directory for MkDocs and Docusaurus,
the root is **declarable** rather than fixed: one constitution line (`Artifact root: documents/`) moves every document
agent at once, and before defaulting into `docs/` a command must check for a publication signal, surface it, and ask.
Commands offer that line but never write it.

The work is prompt text plus documentation plus one CI guard. Both commands also gain a legacy-read step: they read the
locations earlier versions used for context and number continuity, report them once with a `git mv` suggestion, and never
touch them. The extension bumps to 1.6.0 with a rebuilt zip so existing installs pick the change up through
`spectra update`.

## Technical Context

**Language/Version**: Markdown command prompts (Spec Kit generic format); Python 3.11+ for the maintainer tools and tests

**Primary Dependencies**: Spec Kit `>=0.11.0` (unchanged); `tools/build_package.py`, `tools/generate_agent_docs.py`

**Storage**: N/A for the extension itself. The commands write Markdown into the *consumer* project at
`docs/adr/` and `docs/brd/`.

**Testing**: `python -m pytest` (repository suite, plus a new `tests/test_doc_output_paths.py`);
`python tools/generate_agent_docs.py --check`; manual end-to-end run per `test/README.md`

**Target Platform**: any OS Spec Kit supports — including case-insensitive macOS filesystems, which is why the legacy
scan must tolerate case variants

**Project Type**: Spec Kit extension (Markdown commands) + maintainer CLI/tooling

**Performance Goals**: N/A

**Constraints**: no new dependency; no change to the `spectra` CLI; command files stay agent-agnostic; each command's
write footprint stays one artifact file

**Scale/Scope**: 2 command files, 1 manifest, 1 catalog entry, 1 changelog, 1 zip, 5 documentation files, 1 new test
file, 1 constitution amendment

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Note |
|---|---|---|
| I. Spec-Driven Development | ✅ | This spec/plan/tasks set on branch `012-doc-output-convention`; the constitution amendment ships in the same change, per the amendment procedure. |
| II. A Single Self-Contained Extension | ✅ | Edits two existing files under `spectra/commands/`. No new extension, no new dependency. |
| III. Agent-Agnostic Commands | ✅ | Text-only edits; `$ARGUMENTS`, front matter, and the `speckit.spectra.*` names are untouched. The `brd` front-matter `description` changes wording only. |
| IV. Context-Aware by Default | ✅ | Strengthened: both commands now read two locations (canonical + legacy) instead of one. |
| V. Catalog and Package in Sync | ✅ | `extension.yml`, `catalog.json`, `spectra/CHANGELOG.md`, `docs/packages/spectra.zip`, `docs/index.html`, and the hand-authored prose in `spectra/README.md` / `AGENTS_LIST.md` all move in this change. Generated regions are unaffected (they contain no paths) and are re-verified with `--check`. |
| VI. Two Independently-Versioned Channels | ✅ | Extension/catalog channel only: 1.5.0 → 1.6.0. Root `VERSION` and the CLI are untouched; no tag. |
| VII. Document Artifacts Under One Declared Root | ➕ | Added by this change; the two command edits are its first application. |

**Amendment classification**: MINOR — a new principle, no existing principle redefined. Constitution 1.5.0 → 1.6.0.

**Extension version classification**: MINOR — 1.5.0 → 1.6.0. No command is renamed or removed (the constitution's MAJOR
trigger), and legacy-read means no consumer loses artifacts or restarts numbering. A hard switch that ignored legacy
folders would have been MAJOR.

## Project Structure

### Documentation (this feature)

```text
specs/012-doc-output-convention/
├── spec.md      # Feature specification
├── plan.md      # This file
└── tasks.md     # Dependency-ordered task list
```

No `research.md`, `data-model.md`, `contracts/`, or `quickstart.md`: there is nothing to research (both decisions were
settled in Clarifications), no data model beyond two folder names, and the contract *is* the command text plus
`tests/test_doc_output_paths.py`, which is executable rather than prose.

### Source Code (repository root)

```text
.specify/memory/constitution.md      # + Principle VII, 1.5.0 → 1.6.0, sync-impact report
spectra/
├── commands/
│   ├── adr.md                       # Docs/ADR/ → <root>/adr/ + root resolution + legacy-read
│   └── brd.md                       # /brds → <root>/brd/ + root resolution + legacy-read
├── extension.yml                    # brd description; version → 1.6.0
├── CHANGELOG.md                     # [1.6.0] entry
└── README.md                        # ADR + BRD prose sections
catalog.json                         # version → 1.6.0, updated_at
docs/
├── index.html                       # the two agent cdesc blocks
└── packages/spectra.zip             # rebuilt
AGENTS_LIST.md                       # adr + brd prose blocks (+ "Where it writes")
CONTRIBUTING.md                      # Principle VII pointer for new document agents
test/README.md                       # manual-test expectations incl. the root override
tests/test_doc_output_paths.py       # new: CI guard on the convention
```

**Structure Decision**: existing layout, no new directories in this repository. `brds/` stays exactly where it is
(spec Clarification 2); the only new directories this change creates anywhere are `docs/adr/` and `docs/brd/` inside
*consumer* projects at run time.

## Phase 0 — Decisions (settled in the spec's Clarifications)

- **D1 — Legacy handling: read, report, never move.** Writing to the canonical folder while reading the earlier ones
  keeps numbering monotonic across the cut-over without a migration tool. Moving files was rejected because both commands
  carry an explicit one-file write scope, and silently relocating a team's decision log is not a documentation agent's
  call. Ignoring the old folders entirely was rejected because it produces a second `ADR-001`.
- **D2 — Case-insensitive filesystems.** `Docs/ADR/` on macOS already aliases into `docs/`, so the legacy scan matches
  case-insensitively and treats a case-variant hit as legacy. This is also why the new paths are specified lowercase:
  a lowercase-only convention cannot alias.
- **D3 — Filenames unchanged.** `ADR-NNN-<title>.md` and `NNN-<title>.md` stay as they are. Unifying them would rename
  artifacts in consumer projects for cosmetic symmetry.
- **D4 — Enforcement in tests, not review.** This repository already gates its principles in CI (catalog/zip sync,
  generated-region drift, retired CLI verbs). A principle about paths that only a reviewer checks would drift, so
  `tests/test_doc_output_paths.py` asserts the shipped command text directly.
- **D5 — `docs/` stays the default; the root becomes declarable.** Whether `docs/` is safe is a property of the project,
  not of the command: it is Pages' only non-root branch source and the default `docs_dir` for MkDocs and Docusaurus. A
  fixed novel folder would penalize the majority to protect a minority, and any name we picked would collide with
  something. One declaration line, honoured by every agent, resolves it per project and scales to agents that do not
  exist yet.
- **D6 — `documents/` as the recommended alternative.** No tool claims it and it is absent from `.gitignore` templates.
  `artifacts/` was rejected precisely because it *is* commonly gitignored — a BRD written there could be silently lost,
  which is worse than one accidentally published. Hidden roots (`.spectra/`) were rejected because these are documents
  humans review in pull requests, and per-artifact top-level folders were rejected as the sprawl this change removes.
- **D7 — Unanswered means non-publishing.** Publication is the irreversible direction: a misplaced private file moves
  with one `git mv`, while a BRD served on the public web persists in caches, clones, and forks. So the fallback when the
  user does not answer is `documents/`, stated explicitly in the report.
- **D8 — Commands offer the declaration and never write it.** Editing governance as a side effect of producing a
  document would break `brd`'s one-rule write scope and blur `adr`'s existing approval-gated constitution edit, which is
  about the *decision*, not about tool configuration.

## Phase 1 — Design notes

**Both command files gain the same four-part treatment**, worded per command:

1. *Root resolution* — read the constitution for `Artifact root: <folder>/`; validate it as project-relative; otherwise
   default to `docs/` after checking for a publication signal; offer the declaration line without writing it.
2. *Context step* — read the canonical folder, then the superseded ones if present (case-insensitive), using both to
   avoid duplicating prior artifacts.
3. *Numbering step* — create the canonical folder; take the highest `NNN` across every folder found; add one; pad to
   three digits; start at `001`.
4. *Report step* — print the canonical, project-relative path; if a superseded folder was found, say so once, name the
   canonical folder, offer a `git mv`, and state that nothing was moved.

**The ADR command additionally** updates the `git add` suggestion to the canonical path, and its supersede clause now
refuses to edit a superseded ADR that still lives in a read-only folder.

**The BRD command's "one rule that governs everything"** is restated around `<artifact-root>/brd/`, preserving its
explicit prohibition on writing the spec, plan, tasks, constitution, or source — which is also why it may not write the
root declaration. Its publication warning is worded more strongly than the ADR's, because a BRD carries stakeholders,
revenue targets, and competitive rationale.

## Complexity Tracking

> No Constitution Check violations. Nothing to justify.
