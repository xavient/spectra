# Implementation Plan: Domain Analyzer

**Branch**: `001-domain-analyzer` | **Date**: 2026-06-24 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-domain-analyzer/spec.md`

## Summary

The Domain Analyzer is a Spectra add-on extension (SDLC Phase 00 — Foundation) that ships
a single agent-agnostic command, `speckit.domain-analyzer.analyze`. The command reads the
target project's codebase, documentation, and existing constitution; infers the business
domain; and writes a single, opt-in Markdown proposal file of evidence-backed candidate
guardrails at `.specify/memory/domain-analysis.md`. SMEs review asynchronously by checking
boxes; `/speckit-constitution` then consumes only the checked items. Re-runs preserve prior
human decisions by matching on a content-derived stable ID.

Technical approach: this is **not** application code. The deliverable is a self-contained
Spec Kit extension folder (`domain-analyzer/`) whose "logic" lives entirely in a Markdown
command prompt that instructs the host coding agent how to gather context, generate
candidates, and write/merge the proposal artifact. There is no runtime service, database,
or compiled artifact — distribution is via the generated GitHub Pages catalog. Following
the reference `adr/` extension is the primary design pattern.

## Technical Context

**Language/Version**: Agent-agnostic Markdown command prompt (Spec Kit command format using
`$ARGUMENTS`) + YAML manifest (`extension.yml`, `schema_version: "1.0"`). Python 3 is used
only for the site build step (`build_packages.py`).

**Primary Dependencies**: Spec Kit (host); the team's coding agent at runtime (Claude or
other). No third-party runtime libraries — the command is interpreted by the agent.

**Storage**: Files only. The command's sole write in a target project is a single Markdown
artifact at `.specify/memory/domain-analysis.md` (create on first run, preserve-and-append
on re-run). It never writes source code or the constitution.

**Testing**: Manual end-to-end validation per Constitution Principle I / Workflow step 4:
install the working copy with `specify extension add --dev ./domain-analyzer` into a
throwaway Spec Kit project and exercise the command (fresh run, SME-edited re-run, run with
an existing constitution). No automated test framework applies to a prompt artifact.

**Target Platform**: Any Spec Kit-initialized project (`.specify/` present), on whatever
coding agent the team uses. Slash/skill trigger differs per agent (e.g. Claude:
`/speckit-domain-analyzer-analyze`).

**Project Type**: Spec Kit extension — a single self-contained repository-root folder
(`domain-analyzer/`), mirroring the `adr/` reference extension.

**Performance Goals**: User-facing outcomes from the spec — a usable domain-tailored draft
from one command run (SC-001); SME full review pass under 10 minutes (SC-003); ≥50%
reduction in time-to-first-constitution (SC-007).

**Constraints**: Declared `effect: read-write`, but writes are confined to the extension's
own proposal artifact (FR-010). Must be agent-agnostic (Principle III) and context-aware
(Principle IV). Opt-in safety: no candidate pre-selected (FR-005, SC-006). Lossless handoff
contract to `/speckit-constitution` (FR-008).

**Scale/Scope**: One command (`analyze`). Operates over a typical project's codebase and
docs; degrades gracefully on sparse projects (fewer, lower-confidence candidates).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance | Notes |
|-----------|-----------|-------|
| **I. Spec-Driven Development** | ✅ Pass | This feature flows through specify → clarify → plan → tasks → implement; spec under `specs/001-domain-analyzer/`. |
| **II. Self-Contained Extensions** | ✅ Pass | Deliverable is `domain-analyzer/` (id == folder name) containing `extension.yml` (matching `id`), `commands/`, `README.md`, `CHANGELOG.md`, `LICENSE`. No shared state with other extensions. Modeled on `adr/`. |
| **III. Agent-Agnostic Commands** | ✅ Pass | Single command file in Spec Kit generic format using `$ARGUMENTS`; namespaced `speckit.domain-analyzer.analyze`; YAML front matter `description`; registered in `provides.commands`. |
| **IV. Context-Aware by Default** | ✅ Pass | FR-001 requires reading constitution, docs, and codebase before proposing; FR-009 reads existing constitution to mark new/amendment. |
| **V. Generated Site Stays in Sync** | ✅ Pass (build-time) | After authoring, register in canonical `catalog.json`, run `python3 build_packages.py`, and commit regenerated `docs/`. No hand-editing of `docs/`. |

**Result**: PASS — no violations. Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/001-domain-analyzer/
├── plan.md              # This file (/speckit-plan command output)
├── spec.md              # Feature specification
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   ├── command-interface.md   # Command name, args, inputs read, outputs, chat report
│   └── proposal-file.md       # The proposal-file format + handoff contract
└── checklists/
    └── requirements.md  # Spec quality checklist
```

### Source Code (repository root)

The deliverable is one new self-contained extension folder at the repo root, plus the
registration/build artifacts the constitution requires. No `src/`, `tests/`, or runtime
service is created — the extension's behavior is defined entirely by its command prompt.

```text
domain-analyzer/                 # NEW — the extension (id == folder name)
├── extension.yml                # Manifest: id, name, version, effect: read-write, provides.commands
├── commands/
│   └── analyze.md               # Agent-agnostic command prompt (speckit.domain-analyzer.analyze)
├── README.md                    # User-facing docs (what it does, install, usage, output location)
├── CHANGELOG.md                 # SemVer history; 1.0.0 initial release
└── LICENSE                      # MIT (TELUS Digital)

catalog.json                     # MODIFIED — add the "domain-analyzer" entry (canonical metadata)

docs/                            # REGENERATED by build_packages.py (NOT hand-edited)
├── index.html                   # rebuilt landing page
├── catalog.json                 # rebuilt hosted catalog (URLs injected from site.config.json)
└── packages/
    └── domain-analyzer.zip      # rebuilt package
```

**Structure Decision**: Single self-contained extension folder `domain-analyzer/` at the
repository root, mirroring the existing `adr/` extension (Principle II). The command prompt
`commands/analyze.md` is the unit of "implementation". `catalog.json` is edited by hand (it
is the canonical input); everything under `docs/` is generated output produced by
`python3 build_packages.py` and must be committed but never hand-edited (Principle V).

## Complexity Tracking

> No constitution violations — this section intentionally left empty.
