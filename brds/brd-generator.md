# Business Requirements Document (BRD): BRD Generator

## Document Control

| Field             | Value                                                                                                                       |
| ----------------- | --------------------------------------------------------------------------------------------------------------------------- |
| BRD ID            | BRD-003                                                                                                                     |
| Title             | BRD Generator                                                                                                              |
| Author            | Spectra / TELUS Digital                                                                                                     |
| Status            | Draft                                                                                                                      |
| Version           | 0.1.0                                                                                                                      |
| Created           | 2026-07-14                                                                                                                 |
| Last updated      | 2026-07-14                                                                                                                 |
| Related documents | `brds/template.md` (the BRD template this agent fills), `/speckit-specify` (Requirements Analyst — downstream consumer), `.specify/memory/constitution.md`, `brds/domain-analyzer.md`, `brds/open-pr.md` |

## 1. Executive Summary

The **BRD Generator** is a Spectra add-on agent (SDLC Phase — Requirements & Discovery) that sits at
the very front of the spec-driven workflow. It takes a **raw business requirement** — either typed as
plain text or supplied as a document (`.docx`, `.pdf`, `.md`, `.txt`, …) — and transforms it into a
**structured, specify-ready BRD** that follows Spectra's canonical BRD template. It works
**interactively**, like the ADR agent: while drafting it asks a few targeted clarifying questions when
the requirement is thin or ambiguous, so the BRD comes out stronger than the raw input. It then writes
the BRD as a single Markdown file under a `/brds` folder in the project and tells the user they can now
run `/speckit-specify` with the constructed BRD to create the spec.

It removes the blank-page (and inconsistent-page) problem at the start of the SDLC: instead of
hand-authoring a BRD or feeding a loose paragraph straight into `specify`, teams turn a rough
requirement into a complete, well-structured, prioritized BRD in one step — so the requirement that
seeds every downstream agent is grounded, consistent, and ready to spec.

## 2. Business Context & Problem Statement

Spectra automates the SDLC once a **structured requirement** exists — `specify` → `clarify` → `plan` →
`tasks` → `implement` — but the workflow assumes that structured requirement is already written. In
practice it usually is not, and the very first step is where quality is won or lost:

- **Requirements arrive raw and unstructured.** A Slack message, a one-paragraph email, a product
  brief, or a Word/PDF doc is what teams actually have — not a BRD. Feeding that straight into
  `specify` produces thin, under-scoped specs.
- **Manual BRD authoring is a blank-page chore.** Writing a good BRD by hand — executive summary,
  scope in/out, prioritized user journeys with acceptance criteria, success metrics — is slow, and
  most teams skip it, so the requirement is never captured at the level `specify` needs.
- **Inconsistent structure across requirements.** Every BRD is written differently (or not at all),
  so `specify` gets wildly varying input quality and downstream traceability suffers.
- **Requirements trapped in documents.** Business requirements frequently live in `.docx` / `.pdf`
  attachments that never make it into the repository in a machine-usable form, so the source of truth
  for *why* a feature exists is disconnected from the spec it produced.

The result is that the most leverage-rich moment in the whole lifecycle — turning a business need into
a structured requirement — is the least supported, so the agentic SDLC starts from a weak foundation
no matter how good the downstream agents are.

## 3. Business Objectives & Goals

- **G1 — Eliminate the blank page at the front of the SDLC.** Turn a raw requirement into a complete,
  well-structured BRD in a single command run.
- **G2 — Meet requirements where they live.** Accept the requirement as plain text *or* as a document
  file, so teams don't have to retype or reformat what they already have.
- **G3 — Produce specify-ready output.** Every BRD is structured so it can be fed directly to
  `/speckit-specify`, with prioritized, independently testable user journeys that map to user stories.
- **G4 — Ground in the requirement, never invent.** Populate the BRD only from the supplied input and
  project context; record genuine unknowns as Open Questions rather than guessing.
- **G5 — Keep requirements in the repository.** Persist every BRD as Markdown under `/brds`, so the
  business "why" is versioned alongside the specs it seeds.

## 4. Stakeholders & Users

| Stakeholder / user                     | Role in this product     | What they need from it                                                                 |
| -------------------------------------- | ------------------------ | -------------------------------------------------------------------------------------- |
| Developer / operator                   | Primary user             | Runs the agent with a raw requirement (text or file); gets a complete BRD file and the exact next step. |
| Business analyst / product owner       | Requirement author       | Their rough requirement or document becomes a structured, reviewable BRD without manual formatting. |
| Requirements Analyst (`/speckit-specify`) | Downstream consumer   | A specify-ready BRD it can turn into prioritized, testable user stories. |
| Reviewers / stakeholders               | Oversight                | A consistent, self-describing BRD to review and align on *before* the build starts. |
| BRD template (`brds/template.md`)      | Source of truth (input)  | Defines the canonical section structure the agent fills; shipped with the extension. |

## 5. Scope

### 5.1 In Scope

- **Accept a raw business requirement as input** — either as **plain text** passed directly to the
  command, or as a **path/reference to a document file** (`.docx`, `.pdf`, `.md`, `.txt`, and similar
  text-bearing formats).
- **Extract the requirement text from a document file** when a file is supplied, and use that as the
  raw requirement.
- **Transform the raw requirement into a structured BRD** that follows the shipped BRD template's
  section structure (Document Control through Glossary), populated only from the supplied input and
  real project context.
- **Ask targeted clarifying questions while drafting** (interactive, in the spirit of
  `speckit.spectra.adr`) when the requirement is thin or ambiguous, to strengthen the BRD — while still
  producing a best-effort BRD if the user declines to answer.
- **Ship the BRD template with the Spectra extension** so the command produces the same structure in
  any installed project, without depending on the Spectra repository.
- **Write the BRD as a single Markdown file under a `/brds` folder** at the project root, creating the
  folder on first run; `/brds` accumulates all BRDs for the project.
- **Assign each BRD a unique identifier and a descriptive filename**, and never overwrite an existing
  BRD.
- **Author specify-ready user journeys** (Section 6 of the template): independently valuable,
  prioritized, and testable with Given/When/Then acceptance.
- **Record genuine unknowns as Open Questions** and stated defaults as Assumptions, rather than
  inventing requirements the input does not support.
- **Report the output path and the next step in chat**: run `/speckit-specify` referencing the BRD to
  generate the spec.

### 5.2 Out of Scope

- **Creating the spec, plan, tasks, or any downstream artifact.** The agent produces the BRD;
  turning it into a spec is `/speckit-specify`'s job, and everything after that belongs to the
  respective Spec Kit / Spectra agents.
- **Authoring the raw requirement.** The agent structures what it is given; it does not invent the
  business need or fabricate requirements absent from the input.
- **Defining or enforcing guardrails / the constitution.** That is the Domain Analyzer's and
  `/speckit-constitution`'s responsibility; the BRD Generator may read the constitution for context but
  never writes it.
- **Deciding technical design (HOW).** The BRD stays on WHAT the business needs and WHY; tech stack,
  architecture, and API design are decided later in `/speckit-plan`.
- **OCR of image-only / scanned documents.** The agent extracts *text content*; a file with no
  extractable text is surfaced, not guessed at.
- **Editing or approving BRDs on the user's behalf.** Review and sign-off remain human actions; the
  BRD is emitted as a Draft.

## 6. User Journeys *(feeds the spec's prioritized user stories)*

### Journey 1 — Turn a plain-text requirement into a structured BRD (Priority: P1)

- **Actor:** Developer / operator (or business analyst)
- **Trigger:** Runs the command with a raw requirement typed as plain text.
- **Outcome / value:** A complete, structured, specify-ready BRD is written to `/brds`, and the user is
  told where it is and to run `/speckit-specify` next. This is the MVP: it delivers value for any team
  with a requirement in their head, with zero manual template-filling.
- **Flow:**
  1. The user runs the command and passes the business requirement as text.
  2. The agent reads project context (the shipped BRD template, existing BRDs in `/brds`, the
     constitution) and interprets the requirement.
  3. Where the requirement is thin or ambiguous, the agent asks a few targeted clarifying questions and
     folds the answers into the draft (proceeding best-effort if the user declines to answer).
  4. It fills the template's sections from the requirement and answers, assigns the next BRD ID and a
     descriptive filename, and records genuine unknowns as Open Questions.
  5. It creates `/brds` if needed and writes the BRD there as a single Markdown file.
  6. It reports the file path and tells the user they can now run `/speckit-specify` with the BRD.
- **Acceptance:**
  - **Given** a plain-text requirement, **When** the command runs, **Then** a single Markdown BRD is
    written under `/brds` following the template's section structure, with no `[PLACEHOLDER]` tokens or
    template guidance comments left behind.
  - **Given** an ambiguous or incomplete requirement, **When** the agent drafts, **Then** it may ask a
    few targeted clarifying questions before writing, and still produces a best-effort BRD if the user
    does not answer.
  - **Given** the BRD is written, **When** the agent reports back, **Then** the chat message states the
    file path and tells the user they can now run `/speckit-specify` with the constructed BRD.
  - **Given** the requirement does not state something a section needs, **When** the BRD is written,
    **Then** that gap appears as an Open Question or a stated Assumption — never as an invented
    requirement.

### Journey 2 — Turn a requirement document into a structured BRD (Priority: P2)

- **Actor:** Business analyst / product owner
- **Trigger:** Runs the command pointing at a requirement document (`.docx`, `.pdf`, `.md`, `.txt`).
- **Outcome / value:** A requirement trapped in a document becomes a structured BRD in the repository,
  without anyone retyping or reformatting it. Independently valuable for teams whose requirements
  arrive as attachments.
- **Flow:**
  1. The user runs the command and supplies the path to a requirement document.
  2. The agent extracts the document's text content and treats it as the raw requirement.
  3. It transforms that content into a structured BRD exactly as in Journey 1 and writes it to `/brds`.
  4. It reports the file path and the next step.
- **Acceptance:**
  - **Given** a supported document with extractable text, **When** the command runs, **Then** a BRD
    derived from the document's content is written under `/brds`.
  - **Given** a file whose text cannot be extracted (unsupported format, corrupt, or image-only),
    **When** the command runs, **Then** the agent explains the problem clearly and does **not** fabricate
    a BRD from nothing.

### Journey 3 — Hand the BRD off to `specify` to create the spec (Priority: P3)

- **Actor:** Developer / operator
- **Trigger:** After a BRD exists in `/brds`, the user runs `/speckit-specify` referencing it.
- **Outcome / value:** The BRD flows losslessly into the spec: the prioritized user journeys in the
  BRD become the prioritized, independently testable user stories in the spec — closing the loop from
  raw requirement → structured BRD → spec.
- **Flow:**
  1. The user takes the BRD file the agent produced.
  2. They run `/speckit-specify` with the BRD as the feature description.
  3. `specify` produces a spec whose user stories trace back to the BRD's Section 6 journeys.
- **Acceptance:**
  - **Given** a BRD produced by this agent, **When** it is fed to `/speckit-specify`, **Then** the
    resulting spec's prioritized user stories map to the BRD's Section 6 journeys (same priorities,
    same acceptance intent).
  - **Given** the BRD's Section 6, **When** it is authored, **Then** each journey is independently
    valuable and testable with Given/When/Then acceptance, so `specify` has unambiguous input.

### Edge Cases

- **No input supplied.** The agent asks for the requirement text or a file path rather than producing
  an empty or fabricated BRD.
- **Unsupported / unreadable / image-only document.** The agent surfaces the problem and the formats it
  can read, instead of guessing or failing opaquely.
- **Very thin or ambiguous requirement.** The agent still produces a best-effort BRD, marking its
  interpretation as Assumptions and its gaps as Open Questions, rather than blocking or inventing.
- **`/brds` folder or an existing BRD is already present.** The agent creates the folder if missing and
  writes a **new** file with a unique ID/filename; it never overwrites an existing BRD.
- **Both text and a file are supplied.** The agent uses both as the requirement (or states which it
  treats as primary) rather than silently dropping one — see Open Questions.
- **Requirement describes multiple unrelated features.** The agent flags that the requirement may
  warrant more than one BRD/spec rather than forcing an incoherent single document.

## 7. Business Requirements

| ID    | Requirement                                                                                                                                             | Priority |
| ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| BR-01 | The command MUST accept a raw business requirement either as plain text passed directly to the command or as a path/reference to a document file (e.g., `.docx`, `.pdf`, `.md`, `.txt`). | P1       |
| BR-02 | When a document file is supplied, the command MUST extract its text content and use it as the requirement; when the text cannot be extracted (unsupported, corrupt, or image-only), it MUST say so clearly and MUST NOT fabricate a BRD. | P1       |
| BR-03 | The command MUST transform the raw requirement into a structured BRD that follows the shipped BRD template's section structure (Document Control through Glossary). | P1       |
| BR-04 | The BRD template MUST be shipped with the Spectra extension so the command produces the canonical structure in any installed project, without depending on the Spectra repository. | P1       |
| BR-05 | The command MUST write the resulting BRD as a single Markdown file under a `/brds` folder at the project root, creating the folder if it does not exist; `/brds` MUST accumulate all BRDs. | P1       |
| BR-06 | After writing, the command MUST report the output file path in chat and instruct the user that they can now run `/speckit-specify` with the constructed BRD to generate the spec; it MUST NOT invoke `specify` itself. | P1       |
| BR-07 | The command MUST populate the BRD only from the supplied requirement and real project context; it MUST NOT invent requirements the input does not support, and MUST record genuine unknowns as Open Questions. | P1       |
| BR-08 | The generated BRD MUST be specify-ready: Section 6 (User Journeys) MUST contain independently valuable, prioritized journeys with Given/When/Then acceptance so the BRD can be fed to `/speckit-specify` as the feature description. | P1       |
| BR-09 | The command MUST NOT create the spec, plan, tasks, constitution, or any downstream artifact; its only write is the BRD file(s) under `/brds`. | P1       |
| BR-10 | The command MUST assign each BRD a unique, sequential identifier and a descriptive filename derived from the requirement, and MUST NOT overwrite an existing BRD. | P2       |
| BR-11 | The command SHOULD remove the template's guidance comments and fill every applicable `[PLACEHOLDER]`, deleting sections that genuinely do not apply rather than leaving them empty. | P2       |
| BR-12 | The command SHOULD auto-populate Document Control (ID, Title, Author, Status = Draft, Version, Created / Last updated dates) from context. | P2       |
| BR-13 | Where the requirement is thin or ambiguous, the command SHOULD still produce a best-effort BRD, marking its interpretation as Assumptions and gaps as Open Questions rather than blocking. | P2       |
| BR-14 | The command SHOULD work interactively (in the spirit of `speckit.spectra.adr`), asking a few targeted clarifying questions while drafting when the requirement is thin or ambiguous, and MUST still produce a best-effort BRD if the user declines to answer. | P2       |
| BR-15 | If invoked with no input, the command SHOULD prompt the user for the requirement text or a file path rather than producing an empty BRD. | P3       |
| BR-16 | The command MUST operate as an agent-agnostic command and run on whatever coding agent the team uses. | P1       |

## 8. Success Metrics & Measurable Outcomes

- **SC-01** — From a single command run with a raw requirement (text or file), a user obtains a
  complete structured BRD under `/brds`, with zero manual template-filling.
- **SC-02** — Every applicable template section is populated; zero `[PLACEHOLDER]` tokens or template
  guidance comments remain in the output.
- **SC-03** — The BRD is accepted by `/speckit-specify` as a feature description and yields a spec whose
  prioritized user stories map 1:1 to the BRD's Section 6 journeys.
- **SC-04** — 100% of successful runs report the output file path and the next step (run `specify`).
- **SC-05** — Supported document formats (`.docx`, `.pdf`, `.md`, `.txt`) are ingested successfully;
  unsupported or unreadable inputs produce a clear message rather than a fabricated BRD (zero silent
  failures).
- **SC-06** — Zero requirements appear in the BRD that are not traceable to the provided input; genuine
  unknowns are captured as Open Questions instead of invented.
- **SC-07** — Multiple BRDs coexist under `/brds` with unique IDs and filenames; zero accidental
  overwrites of an existing BRD.

## 9. Assumptions

- The project uses the Spec Kit structure (a `.specify/` directory is present) and the host coding
  agent can read files the user references from the local filesystem.
- The `/brds` folder at the project root is the home for BRDs, created on first run (matching this
  repository's own `brds/` convention).
- The downstream consumer is `/speckit-specify` (the Requirements Analyst), which turns a BRD into
  structured, prioritized user stories.
- The shipped BRD template mirrors `brds/template.md` and defines the canonical section structure the
  command fills.
- Supported input file formats include at least `.docx`, `.pdf`, `.md`, and `.txt` with extractable
  text; the command reads the *text content* of the document.
- BRD identifiers are sequential (`BRD-001`, `BRD-002`, …), continuing from any BRDs already present in
  `/brds`.

## 10. Constraints

- Must conform to Spectra's constitution: a **single self-contained extension** (Principle II) — a new
  command file under `spectra/commands/` plus the shipped BRD-template asset, registered in
  `spectra/extension.yml`; an **agent-agnostic, namespaced command** `speckit.spectra.brd` using
  `$ARGUMENTS` (Principle III); and **context-aware** behavior (Principle IV) — reading the shipped
  template, existing `/brds` contents, and project context before writing.
- The extension's declared `effect` is **read-write**, but writes are limited to creating BRD files
  (and the `/brds` folder); it never mutates source code, specs, or the constitution.
- The command extracts **text content** only; document formats vary in what can be read, and behavior
  MUST degrade gracefully when a format cannot be parsed.
- Publishing the command requires keeping the catalog, package, and site in sync (Principle V) — a
  build-time constraint, not a runtime behavior.

## 11. Dependencies

- **Input:** the raw business requirement (plain text or a document file) supplied by the user, and the
  shipped BRD template (which defines the output structure).
- **Downstream (output):** `/speckit-specify` (Requirements Analyst) consumes the BRD as its feature
  description to produce the spec.
- **Related context (optional):** `speckit.spectra.domain-analyzer` / `/speckit-constitution` establish
  the guardrails the requirement lives within; the command may read the constitution for context.

## 12. Risks & Mitigations

| Risk                                                          | Impact | Likelihood | Mitigation                                                                       |
| ------------------------------------------------------------- | ------ | ---------- | -------------------------------------------------------------------------------- |
| Agent invents requirements not present in the input           | H      | M          | Populate only from the supplied input; record genuine unknowns as Open Questions (BR-07, SC-06). |
| BRD is not specify-ready (weak or missing user journeys)      | H      | M          | Require independently testable, prioritized Section 6 journeys with Given/When/Then acceptance (BR-08, SC-03). |
| Document cannot be read (unsupported / corrupt / image-only)  | M      | M          | Extract text content only; surface the problem and readable formats rather than fabricating (BR-02, SC-05). |
| An existing BRD is overwritten                                | M      | L          | Unique sequential IDs and descriptive filenames; never overwrite (BR-10, SC-07). |
| Leftover template placeholders / guidance comments in output  | M      | M          | Fill every applicable placeholder and delete guidance comments and N/A sections (BR-11, SC-02). |
| Thin requirement yields a hollow BRD                          | M      | M          | Ask targeted clarifying questions while drafting and record explicit Assumptions / Open Questions (BR-13, BR-14). |

## 13. Open Questions

- **Filename & ID convention** — what exact naming does the command use (e.g., `NNN-title.md`,
  `BRD-003-<title>.md`)? Does it derive the next number by scanning `/brds`, and how is the
  human-readable title chosen?
- **Supported formats** — which document formats are *guaranteed* supported (`.docx`, `.pdf`, `.md`,
  `.txt`, others like `.rtf`/`.odt`), and how are formats the host agent cannot read handled?
- **Clarifying-question limit** — how many questions should the agent ask at most before drafting
  (e.g., the ADR agent's up-to-five), and should it batch them or ask iteratively?
- **Text + file together** — when both a text prompt and a file are supplied, which is primary, and are
  they merged?

## 14. Glossary

| Term                          | Definition                                                                                                    |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------- |
| BRD (Business Requirements Document) | A structured document that captures WHAT the business needs and WHY, following Spectra's BRD template. |
| Business requirement          | The raw, unstructured statement of need supplied by the user (text or document) that seeds the BRD.           |
| BRD template                  | `brds/template.md` — the canonical section structure the agent fills; shipped with the Spectra extension.     |
| `/brds` folder                 | The project-root directory where generated BRDs are written and accumulated.                                  |
| Requirements Analyst          | `/speckit-specify`, which turns a BRD or product brief into structured, prioritized user stories.             |
| Specify-ready                 | A BRD structured so it can be fed directly to `/speckit-specify` — notably its prioritized, testable journeys. |
| User journey                  | An independently valuable, testable flow (Section 6) that becomes a prioritized user story in the spec.       |
| `$ARGUMENTS`                  | Spec Kit's agent-agnostic placeholder for user input in a command file.                                       |
| Add-on agent                  | An optional Spectra command enabled per project need, as opposed to a required core agent.                    |
| SDD                           | Spec-Driven Development — the `specify` → `clarify` → `plan` → `tasks` → `implement` workflow Spectra ships.   |
