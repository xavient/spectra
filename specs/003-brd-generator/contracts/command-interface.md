# Contract: Command Interface — `speckit.spectra.brd`

Defines the observable interface of the command: its name, arguments, the inputs it reads, its
interactive behavior, what it writes, what it reports, and how it degrades. This is the behavioral
contract the command prompt (`spectra/commands/brd.md`) must satisfy.

## Identity

| Field | Value |
|-------|-------|
| Manifest command name | `speckit.spectra.brd` |
| Command file | `spectra/commands/brd.md` |
| Namespace check | matches `^speckit\.spectra\.[a-z-]+$` (extension id `spectra`, command `brd`) |
| Front matter | YAML with a `description` field |
| Effect | `read-write` (writes limited to BRD files under `/brds`) |
| Trigger (per agent) | Claude `/speckit-spectra-brd` · kiro-cli `/speckit.spectra.brd` (manifest name identical) |

## Arguments (`$ARGUMENTS`)

`$ARGUMENTS` is free-form and MAY contain any of:

- **Inline requirement text** — a sentence/paragraph describing the business need.
- **A document path** — a path to `.md` / `.txt` / `.docx` / `.pdf` containing the requirement.
- **Both** — a document path plus inline guidance.
- **Empty** — the command MUST prompt for a requirement (text) or a document path before drafting
  (FR-014); it MUST NOT produce an empty or fabricated BRD.

When both text and a file are present, the **file is primary** and the inline text is additional
guidance (clarification Q3).

## Inputs read (context-aware — FR-017)

Before drafting, when present:

- The bundled BRD template (`.specify/extensions/spectra/templates/brd-template.md`; inline skeleton
  fallback if unreadable).
- The user-supplied requirement (inline text and/or extracted document text).
- The constitution (`.specify/memory/constitution.md`), existing BRDs under `/brds`, and prior specs
  under `specs/` — for grounding/deconfliction and to pick the next `NNN`. These MUST NOT add scope.

## Interaction (clarifying questions — FR-005)

- After gathering context, assess the requirement for **material gaps/ambiguities**.
- If gaps exist: ask **up to five** targeted, project-specific clarifying questions; present them and
  wait for answers before drafting.
- If the requirement is already complete: **skip** questioning.
- If the user declines to answer: proceed best-effort and record remaining gaps as **Open Questions**.

## Outputs (writes)

- Exactly one BRD Markdown file at `/brds/NNN-<kebab-title>.md` (folder created if absent; `NNN` is the
  next sequential number; never overwrites — FR-008/FR-009).
- No other writes. MUST NOT create/modify the spec, plan, tasks, constitution, or source code (FR-013).
- MUST NOT invoke `/speckit-specify` (FR-012).

The written file MUST satisfy the [BRD output contract](./brd-output.md).

## Chat report (FR-012)

On success, report:

1. The output file path (e.g. `/brds/003-brd-generator.md`).
2. A one-line summary of the BRD's title/intent.
3. The next step, verbatim intent: *You can now run `/speckit-specify` with this BRD to create the spec.*

## Errors & graceful degradation

| Condition | Behavior |
|-----------|----------|
| No input supplied | Prompt for requirement text or a document path (FR-014); do not write. |
| Document path unreadable / unsupported / image-only (no text) | Report the problem and the formats it can read; do **not** fabricate a BRD (FR-002). |
| Requirement is thin/ambiguous | Ask clarifying questions (up to 5); if unanswered, write a best-effort BRD with explicit Assumptions and Open Questions. |
| Requirement describes multiple unrelated features | Flag that more than one BRD/spec may be warranted rather than forcing one incoherent document (FR-015). |
| Requirement conflicts with the constitution | Note the tension as an Open Question; never silently override or edit the constitution. |
| `/brds` or a same-titled BRD already exists | Create the folder if missing; write a new file with the next `NNN`; never overwrite (FR-009). |

## Acceptance (maps to spec)

- FR-001/FR-002 — input modes and extraction/degradation.
- FR-005 — gated clarifying questions (≤5).
- FR-006/FR-017 — grounded, never-invented, context-aware.
- FR-007 — specify-ready output (see brd-output.md).
- FR-008/FR-009/FR-010/FR-011 — file location, naming, no-overwrite, clean fill, Document Control.
- FR-012/FR-013 — report + handoff; bounded writes.
- FR-014/FR-015/FR-016 — empty-input prompt, multi-feature flag, agent-agnostic.
