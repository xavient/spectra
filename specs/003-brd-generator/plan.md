# Implementation Plan: BRD Generator (`speckit.spectra.brd`)

**Branch**: `003-brd-generator` | **Date**: 2026-07-14 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/003-brd-generator/spec.md`

## Summary

**BRD Generator** adds a new command, `speckit.spectra.brd`, to the single Spectra extension. It sits at
the front of the SDLC (Requirements & Discovery): it takes a raw business requirement — typed inline or
supplied as a document file (`.docx`, `.pdf`, `.md`, `.txt`) — and transforms it into a **structured,
specify-ready BRD** that follows Spectra's canonical BRD template. It works interactively (like the ADR
agent), asking up to five clarifying questions *only* when the requirement has material gaps. It writes
one Markdown file per BRD to a `/brds` folder at the project root (`NNN-<kebab-title>.md`, never
overwriting), then instructs the user to run `/speckit-specify` with the BRD to create the spec.

Technical approach: this is **not** application code. The deliverable is a new agent-agnostic Markdown
command prompt (`spectra/commands/brd.md`, Spec Kit command format using `$ARGUMENTS`) plus a bundled
template asset (`spectra/templates/brd-template.md`, a copy of the repo's `brds/template.md`) shipped
inside the single self-contained `spectra/` extension. There is no runtime service, database, or
compiled artifact — the host coding agent interprets the prompt, reads the requirement (extracting text
from documents where it can), reads available project context to ground/deconflict, and writes the BRD.
The `adr` and `domain-analyzer` commands are the reference patterns (both embed/ship a template and
follow a numbered-file convention). Distribution follows Constitution Principle V: hand-maintained
`catalog.json`, `docs/packages/spectra.zip`, and `docs/index.html` over raw `raw.githubusercontent.com`
links (there is no build script).

## Technical Context

**Language/Version**: Agent-agnostic Markdown command prompt (Spec Kit command format using
`$ARGUMENTS`) with YAML front matter (`description`). No compiled language; no version runtime of its
own. The bundled template is Markdown.

**Primary Dependencies**: Spec Kit (host) and the team's coding agent at runtime, which interprets the
prompt and performs file reading + document text extraction. No third-party runtime libraries. Document
text extraction relies on the host agent's native file-reading capability (see research.md for the
supported-format baseline and graceful degradation).

**Storage**: None of its own. Writes BRD Markdown files under `/brds` at the project root (creating the
folder). Reads: the bundled BRD template, the user-supplied requirement (inline text and/or a document
file), and — for grounding only — the constitution (`.specify/memory/constitution.md`), existing BRDs
under `/brds`, and prior specs under `specs/`. It writes no source code, spec, plan, or constitution.

**Testing**: Manual end-to-end validation per Constitution Principle I / Development Workflow step 5:
install the working copy with `specify extension add --dev ./spectra` into a throwaway Spec Kit project
and exercise the scenarios in [quickstart.md](./quickstart.md) (text input, document input, unreadable
file, thin requirement → clarifying questions, no input, no-overwrite on re-run, handoff to
`/speckit-specify`). No automated test framework applies to a prompt artifact.

**Target Platform**: Any Spec Kit-initialized project (`.specify/` present) on whatever coding agent the
team uses. Slash/skill trigger differs per agent (Claude: `/speckit-spectra-brd`; kiro-cli:
`/speckit.spectra.brd`); the manifest command name `speckit.spectra.brd` is identical everywhere.

**Project Type**: Spec Kit extension command — a new command file plus a bundled template asset within
the single self-contained `spectra/` extension (id `spectra`). No `src/`, `tests/`, or runtime service.

**Performance Goals**: User-facing outcomes from the spec — a complete BRD from a single command run
(SC-001), the output path and next step reported on 100% of successful runs (SC-004), and at least a
50% reduction in time-to-first-BRD versus blank-template authoring (SC-008).

**Constraints**: Declared `effect: read-write`, but the only writes are BRD files under `/brds` (FR-013).
Must be agent-agnostic (Principle III) and context-aware (Principle IV / FR-017). MUST never invent
requirements the input does not support (FR-006); MUST record genuine unknowns as Open Questions. MUST
degrade gracefully when a document's text cannot be extracted (FR-002). MUST NOT overwrite an existing
BRD (FR-009). MUST NOT invoke `specify` itself (FR-012).

**Scale/Scope**: One new command (`speckit.spectra.brd`) plus one bundled template asset. Operates on a
single requirement per run, producing a single BRD file.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance | Notes |
|-----------|-----------|-------|
| **I. Spec-Driven Development** | ✅ Pass | Flows through specify → clarify → plan → tasks → implement; spec under `specs/003-brd-generator/`, developed on branch `003-brd-generator`. |
| **II. A Single Self-Contained Extension** | ✅ Pass | Adds a command file under `spectra/commands/brd.md` and a bundled asset under `spectra/templates/brd-template.md`, registered in the single `spectra/extension.yml`. No new top-level extension folder; no runtime dependency on any other extension. Bundled-asset precedent: the `git` extension ships `config-template.yml`/`git-config.yml`. |
| **III. Agent-Agnostic Commands** | ✅ Pass | Single command file in Spec Kit generic format using `$ARGUMENTS`; YAML front matter `description`; registered in `provides.commands`. Command name `speckit.spectra.brd` follows `^speckit\.<extension-id>\.<command>$` (extension id `spectra`, command `brd`). |
| **IV. Context-Aware by Default** | ✅ Pass | FR-017 requires reading the constitution, existing `/brds`, and prior specs to ground and deconflict the BRD before writing (without introducing requirements absent from the input). |
| **V. The Catalog and Package Are Maintained in Sync** | ✅ Pass (build-time) | Implement will bump `spectra/extension.yml` to `1.2.0` with a matching `CHANGELOG.md` entry, rebuild `docs/packages/spectra.zip` (single top-level `spectra/` folder), update `catalog.json` (`provides.commands` 3 → 4, add `brd`/`requirements` tags), `docs/index.html`, and the Agents tables in `README.md` and `AGENTS_LIST.md`. No hand-editing of generated output beyond what the constitution prescribes. |

**Result**: PASS — no violations. Complexity Tracking is empty.

## Project Structure

### Documentation (this feature)

```text
specs/003-brd-generator/
├── plan.md              # This file (/speckit-plan output)
├── spec.md              # Feature specification (with Clarifications)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── command-interface.md   # Command name, args, inputs read, interaction, outputs, chat report, errors
│   └── brd-output.md          # Output BRD file contract: location, filename, Document Control, sections, handoff
└── checklists/
    └── requirements.md  # Spec quality checklist (16/16)
```

### Source Code (repository root)

The deliverable is a new command file plus a bundled template asset inside the existing single
`spectra/` extension, together with the registration/sync artifacts Principle V requires. No `src/`,
`tests/`, or runtime service is created.

```text
spectra/                             # the single self-contained extension (id == folder name)
├── commands/
│   ├── adr.md
│   ├── create-pr.md
│   ├── domain-analyzer.md
│   └── brd.md                        # NEW — the command prompt (speckit.spectra.brd)
├── templates/                        # NEW directory (bundled assets)
│   └── brd-template.md               # NEW — copy of repo brds/template.md, shipped with the extension
├── extension.yml                     # MODIFIED — register speckit.spectra.brd; bump version 1.1.0 → 1.2.0
├── README.md                         # MODIFIED — Agents table + usage for the new command
├── CHANGELOG.md                      # MODIFIED — 1.2.0 entry
└── LICENSE

catalog.json                         # MODIFIED — provides.commands 3 → 4; add tags; bump version/updated_at
docs/
├── index.html                       # MODIFIED — list the new command
└── packages/
    └── spectra.zip                  # REBUILT (by hand) — zip of the spectra/ folder

README.md                            # MODIFIED — top-level Agents table
AGENTS_LIST.md                       # MODIFIED — add the brd agent entry
brds/
└── brd-generator.md                 # existing source BRD (the input to this spec) — unchanged
```

**Structure Decision**: Extend the single self-contained `spectra/` extension (Principle II) with one new
command file (`commands/brd.md`) and one new bundled asset directory (`templates/brd-template.md`),
mirroring how `adr` and `domain-analyzer` are authored and how the `git` extension ships non-command
assets. `catalog.json`, `docs/`, `README.md`, and `AGENTS_LIST.md` are the hand-maintained
sync/distribution artifacts updated during implement; `docs/packages/spectra.zip` is rebuilt by hand as
a single top-level `spectra/` folder (Principle V — there is no build script).

## Complexity Tracking

> No Constitution Check violations. No entries required.
