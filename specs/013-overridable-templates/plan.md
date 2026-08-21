# Implementation Plan: Overridable Document Templates

**Branch**: `013-overridable-templates` | **Date**: 2026-08-21 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/013-overridable-templates/spec.md`

**Status**: Phase 0 closed — OQ-1 and OQ-2 answered by measurement against Spec Kit 0.16.5, OQ-3 decided by the
maintainer (new Principle VIII). Implementation may proceed.

## Summary

Make both document agents template-driven the same way, and make that template overridable per project. Ship the ADR's
structure as `spectra/templates/adr-template.md` instead of a literal inside the command, register both templates in
`provides.templates`, and replace the BRD command's hard-coded path with the four-layer resolution order Spec Kit already
defines — project override, presets, extension, core — with each command's inline skeleton as the last resort.

The user-visible outcome is one file per template: drop `.specify/templates/overrides/adr-template.md` into a repo and
every ADR follows it, for the whole team, surviving extension updates. With no override present, output is structurally
identical to 1.6.0.

## Technical Context

**Language/Version**: Markdown command prompts (Spec Kit generic format); Python 3.9+ for maintainer tools and tests

**Primary Dependencies**: Spec Kit `>=0.11.0` — specifically its template resolution stack and the `provides.templates`
manifest field. No new runtime dependency.

**Storage**: N/A. Templates are files in the consumer's project; documents land under the artifact root (Principle VII).

**Testing**: `python -m unittest discover -s tests` (new assertions in `tests/`), `tools/generate_agent_docs.py --check`,
plus the manual end-to-end pass in `test/README.md` extended with an override scenario and an update scenario

**Target Platform**: every agent and OS Spec Kit supports — which is why resolution is prompt-expressed rather than
script-backed

**Project Type**: Spec Kit extension (Markdown commands + template assets) & maintainer tooling

**Constraints**: **Markdown only** — no scripts, binaries, or post-install hooks may enter the package (README supply
chain claim); agent-agnostic prompts (Principle III); each command's write footprint unchanged

**Scale/Scope**: 1 new template asset, 2 command files, 1 manifest, 1 catalog entry, 1 changelog, 1 zip, ~5 doc files,
new test assertions, 1 constitution amendment

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Note |
|---|---|---|
| I. Spec-Driven Development | ✅ | This spec/plan/tasks set on branch `013-overridable-templates`; constitution amendment ships in the same change. |
| II. A Single Self-Contained Extension | ✅ | Adds one asset under the existing `spectra/templates/`, already precedented by `brd-template.md`. No new extension, no dependency. |
| III. Agent-Agnostic Commands | ✅ | Resolution is prompt-expressed. Calling core's Bash `resolve_template()` would break PowerShell-only setups, and shipping a script would break the Markdown-only promise — see D2. |
| IV. Context-Aware by Default | ✅ | Strengthened: the commands now read the project's own template preferences instead of assuming one path. |
| V. Catalog and Package in Sync | ✅ | `extension.yml`, `catalog.json`, `CHANGELOG.md`, the zip, `docs/index.html`, and the hand-authored prose all move in this change; generated regions re-verified with `--check`. |
| VI. Two Independently-Versioned Channels | ✅ | Extension/catalog channel only: 1.6.0 → 1.7.0. `VERSION` and the CLI untouched; no tag. |
| VII. Documents Under One Declared Root | ✅ | Untouched. Where a document goes is orthogonal to how it is shaped. |
| VIII. Documents Are Shaped by Overridable Templates | ➕ | Added by this change (OQ-3 decided: its own principle, not a VII clause). The two command rewrites are its first application. |

**Amendment classification**: MINOR either way — a new principle, or materially expanded guidance in an existing one.
Constitution 1.6.0 → 1.7.0.

**Extension version classification**: MINOR — 1.6.0 → 1.7.0. New capability; no command renamed or removed; with no
override present, output is unchanged.

## Project Structure

### Documentation (this feature)

```text
specs/013-overridable-templates/
├── spec.md      # Feature specification (carries OQ-1..OQ-3)
├── plan.md      # This file
└── tasks.md     # Dependency-ordered task list
```

No `data-model.md` or `contracts/`: the data model is two filenames and a priority order, and the contract is the command
text plus the test assertions, which are executable rather than prose. `research.md` is replaced by Phase 0 below, whose
open items are the three OQs.

### Source Code (repository root)

```text
.specify/memory/constitution.md          # the template rule (Principle VIII or a VII clause)
spectra/
├── templates/
│   ├── adr-template.md                  # NEW — today's inline ADR structure, verbatim
│   └── brd-template.md                  # unchanged content
├── commands/
│   ├── adr.md                           # inline literal → resolved template; report the path
│   └── brd.md                           # hard-coded path → resolution stack; report the path
├── extension.yml                        # + provides.templates; version → 1.7.0
├── CHANGELOG.md                         # [1.7.0]
└── README.md                            # how to override, and that overrides survive updates
catalog.json                             # version → 1.7.0 (+ template count if the schema carries one)
docs/
├── index.html                           # both agents' cdesc: templates are overridable
└── packages/spectra.zip                 # rebuilt — must contain both templates
AGENTS_LIST.md                           # "Where it writes" gains a template note
CONTRIBUTING.md                          # new document agents ship a registered template
test/README.md                           # override scenario + survives-update scenario
tests/test_document_templates.py         # NEW — registration, drift, four-layer coverage
```

**Structure Decision**: existing layout; the only new directory entry is one file under the existing
`spectra/templates/`.

## Phase 0 — Decisions and research

**Settled:**

- **D1 — The shipped ADR template reproduces today's structure verbatim.** Changing sections in the same release that
  makes them overridable would alter every existing user's output while claiming to be additive. Teams wanting
  Alternatives Considered are precisely who the override serves.
- **D2 — Resolution is prompt-expressed, not script-backed.** `resolve_template()` is a Bash function in core's script
  tree; depending on it breaks PowerShell-only setups (Principle III), and shipping our own resolver script would break
  the README's "Markdown only … no scripts, no binaries, no post-install hooks" claim, which is load-bearing for the
  security review. The commands therefore instruct the agent to check the four locations in order — the same list, stated
  as prose.
- **D3 — Report the resolved path.** Without it, an override that silently fails to apply is indistinguishable from one
  that applied, and the user's first clue is a wrongly-shaped document.
- **D4 — Honour the template, never repair it.** If a project's override drops a section the command usually fills, the
  command notes the omission instead of adding it back. Anything else makes the override advisory.
- **D5 — Drift is a CI concern.** A shipped template and an inline fallback stating different structures is the exact bug
  nobody notices; the suite compares their headings. `brd.md` already carries this risk today, so the check covers both.

**Closed by measurement (probe project `/tmp/tmpl-probe`, Spec Kit 0.16.5) — see the spec's Phase 0 findings:**

- **OQ-1 — closed.** Registration changes neither placement nor behavior: the whole extension tree is copied either way,
  and `specify extension info` prints commands only on 0.16.5. Registration is therefore a correctness and
  forward-compatibility measure, and User Story 3 was rewritten to stop claiming discoverability it does not deliver.
  `resolve_template` was exercised directly and returns the extension copy with no override, the override once present.
- **OQ-2 — closed.** Overrides survived a `--dev` install, a forced install from the published catalog, and
  `specify extension update spectra`; `remove` enumerates only the extension tree and its configs. A marker written into
  the *installed* template was destroyed by `add --force`, the same tree-replace a version bump performs — confirming
  that editing the installed copy is not durable and an override is.
- **OQ-3 — closed.** New **Principle VIII**, not a clause in VII.

**Consequences for the plan:** Phase 4 (registration) no longer carries a discoverability claim, and the cut line that
would have dropped it is retained only for validation failures, which did not occur. Nothing else changed.

## Phase 1 — Design notes

**Both commands get the same resolution block**, worded per command:

```text
1. `.specify/templates/overrides/<name>-template.md`   ← project override, wins outright
2. `.specify/presets/<preset-id>/templates/<name>-template.md`  ← installed presets, registry priority
3. `.specify/extensions/spectra/templates/<name>-template.md`   ← shipped default
4. `.specify/templates/<name>-template.md`             ← core, if a project keeps one there
5. the inline skeleton at the end of this command      ← last resort
```

Take the first readable, non-empty hit; if a layer exists but cannot be read, say so and continue; report the winning
path in the run's output.

**`adr.md`** loses its "use **exactly** this template" literal in Step 4, which becomes "follow the resolved template's
sections exactly, in its order" — with the same block retained at the end of the file as the inline skeleton, mirroring
how `brd.md` is already organized.

**`brd.md`** replaces the single hard-coded read in Step 2 item 1 with the block above; its existing inline skeleton is
already the last resort and needs only a wording tie-in.

**Filling rules** in both commands stay as they are, with one addition: they apply *to the sections the resolved template
declares*.

## Risks

| Risk | Mitigation |
|---|---|
| OQ-1 resolves badly — registration changes install layout or rejects the manifest | Registration (T003) is separable from resolution (T004–T005); if it misbehaves, ship the resolution change alone and drop `provides.templates` to a follow-up. Story 3 is P2 precisely so it can be cut. |
| An agent skips the priority order and grabs the first file it finds | Report-the-path (D3) makes the failure visible immediately; the manual pass in `test/README.md` exercises it. |
| Prose resolution drifts between the two commands | The new test asserts both name all four layers. |
| A project's override omits sections the command's rules assume | D4: honour and note. Covered by an acceptance scenario. |

## Complexity Tracking

> No Constitution Check violations. OQ-3 decides where the new rule lives, not whether it is justified.
