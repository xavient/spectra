# Phase 1 Data Model: BRD Generator (`speckit.spectra.brd`)

This command has no database or persistent runtime state. The "data model" is the set of conceptual
entities the prompt reasons over and the shape of the artifact it writes. All entities are files or
in-conversation values.

## Entity: Business Requirement (input)

The raw, unstructured statement of need that seeds a BRD.

| Field | Description | Notes |
|-------|-------------|-------|
| `inline_text` | Requirement text passed via `$ARGUMENTS` | Optional |
| `document_path` | Filesystem path to a requirement document | Optional (`.md`, `.txt`, `.docx`, `.pdf`) |
| `extracted_text` | Text content read/extracted from `document_path` | Derived; empty ⇒ extraction failed |
| `clarifying_answers` | User responses to clarifying questions | Optional; may be empty if declined |

**Rules**
- At least one of `inline_text` / `document_path` MUST be present; otherwise the command prompts for
  input (FR-014).
- When both are present, `document_path`/`extracted_text` is the **primary** requirement and
  `inline_text` is additional guidance (clarification Q3).
- If `document_path` is given but `extracted_text` cannot be obtained, the command reports the failure
  and does **not** fabricate a BRD (FR-002).
- `inline_text` + `clarifying_answers` are the **sole source of truth for scope**; project context never
  adds requirements (FR-006).

## Entity: BRD Template (bundled asset)

The canonical section structure the command fills, shipped with the extension.

| Field | Description |
|-------|-------------|
| `shipped_path` | `spectra/templates/brd-template.md` in source; `.specify/extensions/spectra/templates/brd-template.md` when installed |
| `sections` | Ordered sections: Document Control; 1 Executive Summary; 2 Business Context & Problem Statement; 3 Business Objectives & Goals; 4 Stakeholders & Users; 5 Scope (In / Out); 6 User Journeys; 7 Business Requirements; 8 Success Metrics; 9 Assumptions; 10 Constraints; 11 Dependencies; 12 Risks & Mitigations; 13 Open Questions; 14 Glossary |
| `inline_fallback` | Section skeleton embedded in the command, used only if `shipped_path` cannot be read |

**Rules**
- The generated BRD MUST follow this section order and headings.
- Guidance HTML comments and `[PLACEHOLDER]` tokens from the template MUST NOT remain in output (FR-010).
- Sections that genuinely do not apply are removed entirely, not left as "N/A" (FR-010).

## Entity: BRD (output)

A structured Markdown document, one file per requirement, written under `/brds`.

### Document Control fields (auto-populated — FR-011)

| Field | Value / Rule |
|-------|--------------|
| BRD ID | `BRD-NNN` (same `NNN` as the filename) |
| Title | Human-readable feature/product name derived from the requirement |
| Author | Project/team name inferred from context (constitution author, Git config, or repo metadata); falls back to a `[team]` placeholder if none found |
| Status | `Draft` |
| Version | `0.1.0` |
| Created | Today's date (`YYYY-MM-DD`) |
| Last updated | Today's date (`YYYY-MM-DD`) |
| Related documents | Links to relevant context (constitution, related BRDs/specs) when present |

### Identity & file rules (FR-008, FR-009 — clarification Q1)

| Field | Rule |
|-------|------|
| `folder` | `/brds` at the project root; created on first run |
| `filename` | `NNN-<kebab-title>.md` — `NNN` = zero-padded, three-digit, next sequential number after the highest existing under `/brds` (start `001`); `<kebab-title>` = title lowercased, spaces → hyphens |
| uniqueness | MUST NOT overwrite an existing BRD; a re-run produces a new `NNN` |

### Content rules

- **Section 6 (User Journeys)** MUST contain independently valuable, **prioritized** journeys (P1, P2, …),
  each with actor, trigger, outcome, flow, and **Given/When/Then acceptance** — this is the specify-ready
  contract (FR-007) and maps 1:1 to the eventual spec's user stories.
- **Section 7 (Business Requirements)** MUST be testable, business-voice, MUST/SHOULD, priority-tagged.
- **Section 13 (Open Questions)** MUST hold every genuine unknown rather than an invented answer (FR-006).
- **Section 9 (Assumptions)** MUST record reasonable defaults the command adopted.

### Lifecycle

`Draft` (as written by this command) → *(later, by humans / other agents)* In Review → Approved. This
command only ever emits `Draft` and never edits an existing BRD's lifecycle.

## Entity: `/brds` folder

Project-root directory that accumulates all BRDs over time.

**Rules**: created if absent (FR-008); scanned to determine the next `NNN` and to deconflict/deduplicate
against existing BRDs (FR-017); never has an existing entry overwritten (FR-009).

## Entity: Clarifying exchange (transient)

The optional interactive question/answer round.

**Rules**: at most five questions (D5); asked **only** when the requirement has material gaps; presented
before writing; unanswered gaps become Open Questions in the BRD (FR-005).

## Relationships

```text
Business Requirement ──(transformed by speckit.spectra.brd, using)──▶ BRD Template
        │                                                                   │
        └───────────────▶ BRD (output file /brds/NNN-<kebab-title>.md) ◀────┘
                                     │
                                     └──(user runs /speckit-specify with it)──▶ Feature Spec
Project context (constitution, /brds, specs/) ──(grounds/deconflicts, never adds scope)──▶ BRD
```
