---
description: "Task list for Domain Analyzer extension implementation"
---

# Tasks: Domain Analyzer

**Input**: Design documents from `/specs/001-domain-analyzer/`

**Prerequisites**: [plan.md](./plan.md) (required), [spec.md](./spec.md) (required), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/](./contracts/)

**Tests**: No automated tests requested. This is a Spec Kit extension whose behavior is a Markdown command prompt; validation is manual end-to-end via [quickstart.md](./quickstart.md) (Constitution Principle I / Workflow step 4). No test tasks are generated.

**Organization**: Tasks are grouped by user story. NOTE: all runtime behavior lives in the single command-prompt file `domain-analyzer/commands/analyze.md`. Story phases therefore build that one file incrementally and are **sequential** (same file = no cross-story `[P]`). Each story still yields an independently testable increment of the command's behavior.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Paths are repo-root-relative.

## Path Conventions

This project is a Spec Kit **extension catalog**, not application code. The deliverable is a self-contained folder `domain-analyzer/` at the repo root (modeled on `adr/`), plus registration in `catalog.json` and regenerated `docs/`. There is no `src/` or `tests/` tree.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Scaffold the self-contained extension folder (Constitution Principle II).

- [X] T001 Create the `domain-analyzer/` folder with the standard extension layout (`commands/`, `README.md`, `CHANGELOG.md`, `LICENSE`, `extension.yml`) by copying the `adr/` extension as a starting template, then clearing `adr`-specific content
- [X] T002 [P] Author `domain-analyzer/extension.yml`: `schema_version: "1.0"`; `id: domain-analyzer`; name "Domain Analyzer"; `version: 1.0.0`; `category` (e.g. "governance"); `effect: read-write`; `author: TELUS Digital`; `license: MIT`; `repository`/`homepage` per `adr/`; `requires.speckit_version: ">=0.11.0"` (research D3); `provides.commands` with `speckit.domain-analyzer.analyze` → `commands/analyze.md` and a one-line description; relevant `tags`
- [X] T003 [P] Add `domain-analyzer/LICENSE` (MIT, TELUS Digital — copy from `adr/LICENSE`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Create the command-prompt skeleton, the shared context-gathering step, and the embedded proposal-file format that every user story depends on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete (all stories edit `commands/analyze.md`).

- [X] T004 Create `domain-analyzer/commands/analyze.md` with YAML front matter (`description`) and an overall step outline; handle `$ARGUMENTS` as optional and ensure the command runs with empty input (FR-015, Principle III) — per [contracts/command-interface.md](./contracts/command-interface.md)
- [X] T005 Add the "Gather project context" step to `domain-analyzer/commands/analyze.md`: read the codebase, documentation, existing constitution (`.specify/memory/constitution.md`), and any existing proposal file (`.specify/memory/domain-analysis.md`) BEFORE proposing anything (FR-001); written agent-agnostically
- [X] T006 Embed the proposal-file format spec into `domain-analyzer/commands/analyze.md`: file skeleton, per-candidate checkbox-anchor block with indented metadata (`id`, `section`, `evidence`, `confidence`, `status`), content-derived stable-ID scheme (`da-<section-slug>-<hash>`, research D5), file-path evidence rule (≥1, SC-002), `High/Medium/Low` confidence, and `##`-grouping by target constitution section (FR-003, FR-004, FR-006, FR-013) — per [contracts/proposal-file.md](./contracts/proposal-file.md) and [data-model.md](./data-model.md)

**Checkpoint**: Command exists, gathers context, and knows the output format — user stories can now be layered on.

---

## Phase 3: User Story 1 - Generate domain-tailored guardrail proposals (Priority: P1) 🎯 MVP

**Goal**: One command run reads the project, infers the domain, and writes a single opt-in proposal file of evidence-backed candidates, then reports next steps in chat.

**Independent Test**: Run in a throwaway project with code+docs and no existing proposal file; verify a single `.specify/memory/domain-analysis.md` is created with ≥1 candidate (each carrying id, section, ≥1 file-path evidence, confidence, status), no candidate pre-checked, and a chat message stating the path, inferred domain, and next steps (quickstart Scenario 1).

- [X] T007 [US1] Add the "Infer domain" step to `domain-analyzer/commands/analyze.md`: write a one-paragraph inferred-domain summary with its evidence basis, and an advisory-only compliance add-on recommendation when the domain warrants it (FR-002, FR-014, research D9)
- [X] T008 [US1] Add the "Generate candidates" step to `domain-analyzer/commands/analyze.md`: produce atomic, individually selectable candidates with `id`/`statement`/`section`/`evidence`/`confidence`/`status: new`, statements written in the constitution's MUST/SHOULD+rationale voice, every candidate default-unchecked `- [ ]`, and fewer/lower-confidence candidates when evidence is sparse rather than inventing rules (FR-003, FR-004, FR-005, FR-012; edge cases)
- [X] T009 [US1] Add the "Write proposal file" step to `domain-analyzer/commands/analyze.md`: create `.specify/memory/domain-analysis.md` (and only that file) using the embedded format; explicitly forbid writing source code or the constitution (FR-006, FR-010)
- [X] T010 [US1] Add the "Report in chat" step to `domain-analyzer/commands/analyze.md`: state the file path, a one-line inferred-domain summary, and the exact next steps (review → check items → run `/speckit-constitution`) (FR-007)

**Checkpoint**: MVP — a fresh run yields a complete, opt-in proposal file plus the chat report.

---

## Phase 4: User Story 2 - SME reviews asynchronously and opts in (Priority: P2)

**Goal**: The generated file is structured so that `/speckit-constitution` adopts exactly the checked items (with any SME edits) and nothing else.

**Independent Test**: Take a generated file, check two items and edit one's wording, leave the rest unchecked; verify the handoff yields only the checked items with edited wording, and that an all-unchecked file yields zero guardrails (quickstart Scenario 2).

- [X] T011 [US2] Add an explicit "Handoff contract" section to `domain-analyzer/commands/analyze.md` documenting that the `- [x]` checkbox is the sole selection signal, that the checkbox-line statement text (including SME edits) is the adopted wording, and that `status: amends:` directs modification of a named principle (FR-008) — per [contracts/proposal-file.md](./contracts/proposal-file.md)
- [X] T012 [US2] Document the SME review + handoff flow in `domain-analyzer/README.md` (review → check `- [x]` → optionally edit wording → run `/speckit-constitution` referencing the file; opt-in safety — nothing adopted until checked)

**Checkpoint**: The opt-in handoff is unambiguous and documented for SMEs and the downstream agent.

---

## Phase 5: User Story 3 - Re-run preserves prior decisions (Priority: P3)

**Goal**: Re-running surfaces only genuinely new candidates without disturbing any prior human decision.

**Independent Test**: With a reviewed file present (some checked, one edited), change the codebase and re-run; verify all prior candidates keep exact checkbox state, edited text, and order, new candidates appear under a dated group, and a no-change re-run adds no duplicates (quickstart Scenario 3).

- [X] T013 [US3] Add the "Preserve-and-append on re-run" step to `domain-analyzer/commands/analyze.md`: when a proposal file exists, index existing candidates by `id`, reproduce them (checkbox state, edited statements, order) byte-for-byte, and append only candidates whose `id` is absent under a `## New in this run (YYYY-MM-DD)` heading — never reorder/overwrite, never duplicate (FR-011, research D7) — per [contracts/proposal-file.md](./contracts/proposal-file.md)
- [X] T014 [US3] Extend the chat-report step in `domain-analyzer/commands/analyze.md` to state how many new candidates were appended on a re-run (Journey 3)

**Checkpoint**: Iteration is safe — prior SME work is never lost.

---

## Phase 6: User Story 4 - Amend an existing constitution with deltas only (Priority: P3)

**Goal**: On projects with a ratified constitution, propose only new or changed guardrails and mark amendments.

**Independent Test**: Run in a project whose constitution already asserts a guardrail; verify no duplicate of it is proposed and that an overlapping-but-different candidate is marked `status: amends: <Principle>` (quickstart Scenario 4).

- [X] T015 [US4] Add the "Dedup & amendment marking" step to `domain-analyzer/commands/analyze.md`: semantically compare each candidate against existing constitution principles, suppress candidates whose intent is already ratified, and mark overlapping-but-different candidates as `status: amends: <Principle name/number>` (FR-009, research D8)
- [X] T016 [US4] Add the "no existing constitution" handling to `domain-analyzer/commands/analyze.md`: still produce candidates and note in the file/chat that the constitution will be created from the approved set (edge case)

**Checkpoint**: All four stories are independently functional within the single command.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, catalog registration, site regeneration, and end-to-end validation.

- [X] T017 [P] Complete `domain-analyzer/README.md` (modeled on `adr/README.md`): what it does, install (`--dev` and catalog), usage with per-agent trigger note (e.g. Claude `/speckit-domain-analyzer-analyze`), output location `.specify/memory/domain-analysis.md`, and the mixed-agent note
- [X] T018 [P] Author `domain-analyzer/CHANGELOG.md` with a `## [1.0.0] - <date>` entry summarizing the initial release (modeled on `adr/CHANGELOG.md`)
- [X] T019 Register the extension in the canonical `catalog.json`: add a `domain-analyzer` entry mirroring the `adr` entry's fields (name, id, description, category, effect, version 1.0.0, repository/homepage/documentation/changelog URLs, license, requires, provides.commands count, tags) — do NOT set catalog/download URLs (generated)
- [X] T020 Run `python3 build_packages.py` from repo root and commit the regenerated `docs/` (index.html, catalog.json, packages/domain-analyzer.zip); resolve any `!` URL-drift warning before publishing (Constitution Principle V)
- [X] T021 Execute the [quickstart.md](./quickstart.md) validation scenarios (1–4 + edge checks) by installing with `specify extension add --dev ./domain-analyzer` into a throwaway Spec Kit project; confirm no file other than `.specify/memory/domain-analysis.md` is written in the target project

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories.
- **User Stories (Phases 3–6)**: All depend on Foundational. Because every story edits the same file (`commands/analyze.md`), they proceed **sequentially in priority order** (US1 → US2 → US3 → US4); they are not parallelizable against each other.
- **Polish (Phase 7)**: T019/T020/T021 depend on the command and docs being complete; T017/T018 (docs) can begin once US1 behavior is settled.

### User Story Dependencies

- **US1 (P1)**: Depends only on Foundational. The MVP.
- **US2 (P2)**: Builds on the US1 output format (handoff semantics + docs). Independently testable.
- **US3 (P3)**: Adds re-run behavior on top of the US1 write step. Independently testable.
- **US4 (P3)**: Adds constitution-aware dedup. Independently testable.

### Within Each User Story

- Steps are added to `commands/analyze.md` in listed order; later steps assume earlier ones exist.

### Parallel Opportunities

- Setup: T002 and T003 run in parallel ([P]) — different files from T001's scaffold.
- Polish: T017 and T018 run in parallel ([P]) — different files.
- Cross-story parallelism is NOT available (single shared command file).

---

## Parallel Example: Setup

```bash
# After T001 scaffolds the folder, author these two files in parallel:
Task: "Author domain-analyzer/extension.yml manifest"
Task: "Add domain-analyzer/LICENSE (MIT, TELUS Digital)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1: Setup → 2. Phase 2: Foundational (CRITICAL) → 3. Phase 3: US1.
4. **STOP and VALIDATE**: quickstart Scenario 1 — a fresh run produces an opt-in, evidenced proposal file + chat report.
5. The MVP already delivers the core value: a tailored draft instead of a blank page.

### Incremental Delivery

1. Setup + Foundational → command scaffold ready.
2. US1 → fresh-run proposal (MVP) → validate.
3. US2 → opt-in handoff contract + docs → validate.
4. US3 → safe re-runs → validate.
5. US4 → constitution-aware deltas → validate.
6. Polish → README/CHANGELOG, register in `catalog.json`, rebuild `docs/`, run quickstart.

### Notes

- [P] = different files, no dependencies. The single command file makes most work sequential.
- Each user story is an independently demoable behavior of the command.
- Per Constitution Principle V, the feature is not "done" until `docs/` is regenerated and committed.
- Commit after each task or logical group.
