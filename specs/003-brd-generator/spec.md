# Feature Specification: BRD Generator (`speckit.spectra.brd`)

**Feature Branch**: `003-brd-generator`

**Created**: 2026-07-14

**Status**: Draft

**Input**: User description: "@brds/brd-generator.md" — a Spectra add-on command (`speckit.spectra.brd`) that transforms a raw business requirement (plain text or a document file such as `.docx`/`.pdf`) into a structured, specify-ready BRD written under a `/brds` folder, working interactively with clarifying questions and shipping the BRD template with the extension.

## Clarifications

### Session 2026-07-14

- Q: Output filename convention for BRDs written under `/brds`? → A: `NNN-<kebab-title>.md` (numbered prefix mirroring `specs/`, e.g. `003-brd-generator.md`)
- Q: When does the command ask clarifying questions? → A: Only when the requirement has material gaps/ambiguities (up to 5); skip when already complete
- Q: When both inline text and a document file are supplied, which is primary? → A: The file is the primary requirement; inline text is additional guidance/focus
- Q: How much project context should the command read to ground the BRD? → A: Read available context (constitution, existing `/brds`, prior specs) to ground/deconflict, but the requirement stays the source of truth for scope

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Turn a plain-text requirement into a structured BRD (Priority: P1)

A developer or business analyst has a business need in their head or in a chat message. They invoke the command with the requirement typed as plain text. The command interprets it, asks a few targeted clarifying questions where the requirement is thin, and writes a complete, well-structured BRD (following the canonical template) as a single Markdown file under the project's `/brds` folder — then tells them they can now run `/speckit-specify` with it.

**Why this priority**: This is the MVP slice. It delivers value to any team with a requirement they can describe, eliminating the blank-page (and inconsistent-page) problem at the very front of the SDLC, with zero manual template-filling. Every other story builds on this core transform.

**Independent Test**: Run the command with a plain-text requirement and confirm that a single, complete BRD Markdown file (no leftover placeholder tokens or template guidance comments) appears under `/brds` and that the command reports the path and the next step — all without any downstream command being run.

**Acceptance Scenarios**:

1. **Given** a plain-text business requirement, **When** the command runs, **Then** a single Markdown BRD following the canonical template's section structure is written under `/brds`, with no `[PLACEHOLDER]` tokens or template guidance comments remaining.
2. **Given** an ambiguous or incomplete requirement, **When** the command drafts the BRD, **Then** it asks up to five targeted clarifying questions before writing (skipping questions when the requirement is already complete), folds any answers into the BRD, and still produces a best-effort BRD if the user declines to answer.
3. **Given** the BRD has been written, **When** the command reports back, **Then** the message states the output file path and tells the user they can now run `/speckit-specify` with the constructed BRD.
4. **Given** the requirement does not state something a template section needs, **When** the BRD is written, **Then** that gap appears as an Open Question or a stated Assumption — never as an invented requirement.

---

### User Story 2 - Turn a requirement document into a structured BRD (Priority: P2)

A business analyst or product owner already has the requirement captured in a document — a `.docx`, `.pdf`, `.md`, or `.txt` file. They invoke the command pointing at that file. The command extracts the document's text content, treats it as the raw requirement, and produces the same structured BRD as in Story 1 — so a requirement trapped in an attachment becomes a versioned, structured BRD in the repository without anyone retyping or reformatting it.

**Why this priority**: Requirements frequently arrive as documents rather than typed prose. Supporting file input meets teams where their requirements actually live and is independently valuable, but it layers document-text extraction on top of the core transform delivered by Story 1.

**Independent Test**: Point the command at a supported document containing extractable text and confirm a BRD derived from that document's content is written under `/brds`; then point it at an unreadable/image-only file and confirm it reports the problem instead of producing a BRD.

**Acceptance Scenarios**:

1. **Given** a supported document with extractable text, **When** the command runs against it, **Then** a BRD derived from the document's content is written under `/brds` following the template structure.
2. **Given** a file whose text cannot be extracted (unsupported format, corrupt, or image-only with no text layer), **When** the command runs, **Then** it explains the problem and the formats it can read, and does **not** fabricate a BRD.
3. **Given** both an inline text prompt and a document file are supplied, **When** the command runs, **Then** it treats the document as the primary requirement and the inline text as additional guidance, rather than silently dropping either.

---

### User Story 3 - Hand the BRD off to `specify` to create the spec (Priority: P3)

After a BRD exists under `/brds`, the developer runs `/speckit-specify` referencing it. The BRD flows losslessly into the spec: the prioritized user journeys in the BRD become the prioritized, independently testable user stories in the spec — closing the loop from raw requirement → structured BRD → spec.

**Why this priority**: This realizes the end-to-end value of the feature, but it depends on a BRD already existing (Stories 1/2) and on a separate core command (`/speckit-specify`) doing the consumption. The command's own responsibility ends at producing a specify-ready BRD and instructing the handoff.

**Independent Test**: Take a BRD produced by the command, run `/speckit-specify` with it, and confirm the resulting spec's prioritized user stories correspond to the BRD's user journeys (same priorities, same acceptance intent).

**Acceptance Scenarios**:

1. **Given** a BRD produced by the command, **When** it is fed to `/speckit-specify`, **Then** the resulting spec's prioritized user stories correspond one-to-one to the BRD's user journeys.
2. **Given** the BRD's User Journeys section, **When** it is authored, **Then** each journey is independently valuable and testable with Given/When/Then acceptance, so `specify` has unambiguous input.

---

### Edge Cases

- **No input supplied.** The command prompts for the requirement text or a file path rather than producing an empty or fabricated BRD.
- **Unsupported / unreadable / image-only document.** The command surfaces the problem and the formats it can read, instead of guessing or failing opaquely.
- **Very thin or ambiguous requirement.** After its clarifying questions (or if they go unanswered), the command still produces a best-effort BRD, marking its interpretation as Assumptions and its gaps as Open Questions rather than blocking or inventing.
- **`/brds` folder or an existing BRD already present.** The command creates the folder if missing and writes a **new** file with a unique identifier and filename; it never overwrites an existing BRD.
- **Requirement describes multiple unrelated features.** The command flags that the requirement may warrant more than one BRD/spec rather than forcing an incoherent single document.
- **Requirement conflicts with the project constitution.** The command may note the tension as an Open Question; it does not silently override or rewrite the constitution.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The command MUST accept a raw business requirement as input, provided either as plain text passed directly to the command or as a path/reference to a document file (e.g., `.docx`, `.pdf`, `.md`, `.txt`).
- **FR-002**: When a document file is supplied, the command MUST extract its text content and use it as the requirement; when the text cannot be extracted (unsupported format, corrupt, or image-only with no text layer), it MUST report this clearly and MUST NOT fabricate a BRD.
- **FR-003**: The command MUST transform the raw requirement into a structured BRD that follows the canonical BRD template's section structure (Document Control through Glossary).
- **FR-004**: The command MUST use a BRD template that is shipped with it, so the same canonical structure is produced in any project without depending on any external repository.
- **FR-005**: The command MUST assess the requirement for material gaps or ambiguities and, only when such gaps exist, ask up to five targeted clarifying questions before writing; it MUST incorporate the user's answers into the BRD, skip questioning when the requirement is already complete, and still produce a best-effort BRD if the user declines to answer.
- **FR-006**: The command MUST treat the supplied requirement and the user's clarifying answers as the sole source of truth for *what to build*; it MUST NOT invent requirements the input does not support, and MUST record genuine unknowns as Open Questions.
- **FR-007**: The generated BRD MUST be specify-ready: its User Journeys section MUST contain independently valuable, prioritized journeys, each with Given/When/Then acceptance, so the BRD can be fed to `/speckit-specify` as a feature description.
- **FR-008**: The command MUST write the resulting BRD as a single Markdown file under a `/brds` folder at the project root, creating the folder if it does not exist; the `/brds` folder MUST accumulate all BRDs for the project.
- **FR-009**: The command MUST assign each BRD a unique, sequential identifier and write it to a file named `NNN-<kebab-title>.md` — a sequential numeric prefix (mirroring the `specs/` convention, e.g. `003-brd-generator.md`) followed by a kebab-case title derived from the requirement — and MUST NOT overwrite an existing BRD.
- **FR-010**: The command MUST fill every applicable template placeholder and remove the template's guidance comments and any sections that genuinely do not apply, leaving no placeholder tokens or guidance comments in the output.
- **FR-011**: The command MUST populate the BRD's Document Control fields from context: identifier, title, status = `Draft`, version, and created / last-updated dates; **author** MUST be the project/team name inferred from available context (e.g. the constitution's author, Git config, or repository metadata), falling back to a `[team]` placeholder when none can be determined.
- **FR-012**: After writing, the command MUST report the output file path and instruct the user that they can now run the Spec Kit **specify** command with the constructed BRD to generate the spec (the exact trigger is agent-specific — e.g. `/speckit-specify` on Claude); it MUST NOT invoke `specify` itself.
- **FR-013**: The command MUST NOT create or modify the spec, plan, tasks, constitution, or source code; its only write is the BRD file(s) under `/brds`.
- **FR-014**: If invoked with no input, the command MUST prompt the user for the requirement text or a file path rather than producing an empty BRD.
- **FR-015**: When the requirement describes multiple unrelated features, the command MUST flag that more than one BRD/spec may be warranted rather than forcing an incoherent single document.
- **FR-016**: The command MUST operate as an agent-agnostic command and run on whatever coding agent the team uses.
- **FR-017**: The command MUST read available project context when present — the constitution (`.specify/memory/constitution.md`), existing BRDs under `/brds`, and prior specs — and use it to ground and deconflict the BRD (align terminology, avoid contradicting ratified guardrails, avoid duplicating an existing BRD) without introducing requirements absent from the input; when no such context exists, it proceeds from the requirement alone.

### Key Entities *(include if feature involves data)*

- **Business requirement (input)**: The raw, unstructured statement of need supplied by the user — either inline text or a document file — that seeds the BRD.
- **BRD (output)**: A structured Markdown document following the canonical template. Carries Document Control metadata (unique identifier, title, status, version, dates) and the template's sections (executive summary, scope, prioritized user journeys, business requirements, success metrics, assumptions, open questions, etc.).
- **BRD template**: The canonical section structure the command fills, shipped with the command so it is available in any installed project.
- **`/brds` folder**: The project-root directory where generated BRDs are written and accumulated over time.
- **Clarifying exchange**: The interactive question/answer round the command may run while drafting to strengthen the BRD; optional for the user to answer.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user turns a raw requirement (plain text or a supported document) into a complete, structured BRD in a single command run, with zero manual template-filling.
- **SC-002**: 100% of generated BRDs contain every applicable template section with no leftover placeholder tokens or template guidance comments.
- **SC-003**: A BRD produced by the command is accepted by `/speckit-specify` as a feature description and yields a spec whose prioritized user stories correspond one-to-one to the BRD's user journeys.
- **SC-004**: 100% of successful runs report the output file location and the next step (run `specify`).
- **SC-005**: Supported document inputs are ingested successfully; for unreadable or unsupported inputs, 100% of runs produce a clear message rather than a fabricated BRD (zero silent failures).
- **SC-006**: Zero requirements appear in a generated BRD that are not traceable to the supplied input or the user's clarifying answers; genuine unknowns are captured as Open Questions instead of invented.
- **SC-007**: Multiple BRDs coexist under `/brds` with unique identifiers and filenames; zero existing BRDs are overwritten across runs.
- **SC-008**: Time to a first usable BRD is reduced by at least 50% versus authoring one from a blank template.

## Assumptions

- The project uses the Spec Kit structure (a `.specify/` directory is present) and the host coding agent can read files the user references from the local filesystem.
- The `/brds` folder at the project root is the home for BRDs, created on first run (matching this repository's own `brds/` convention).
- The downstream consumer is `/speckit-specify` (the Requirements Analyst), which turns a BRD into structured, prioritized user stories.
- The BRD template shipped with the command mirrors the canonical `brds/template.md` section structure.
- Supported input file formats include at least `.md`, `.txt`, `.docx`, and `.pdf` with extractable text; the command reads the document's *text content* only (no OCR of scanned/image-only files).
- BRD identifiers are sequential (`BRD-001`, `BRD-002`, …), continuing from any BRDs already present in `/brds`; each file is named `NNN-<kebab-title>.md` with a numeric prefix mirroring the `specs/` convention (clarified 2026-07-14).
- Clarifying questions are capped at five (like the `speckit.spectra.adr` agent), presented before the BRD is written, and asked only when the requirement has material gaps — skipped when it is already complete (clarified 2026-07-14).
- When both an inline text prompt and a document file are supplied, the file is treated as the primary requirement and the inline text as additional guidance/focus (clarified 2026-07-14).
- The command's effect is read-write, but its only writes are BRD files (and the `/brds` folder); it never mutates source code, specs, or the constitution.
