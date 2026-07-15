---
description: "Task list for BRD Generator (speckit.spectra.brd)"
---

# Tasks: BRD Generator (`speckit.spectra.brd`)

**Input**: Design documents from `/specs/003-brd-generator/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Not applicable. The deliverable is an agent-agnostic command prompt (not code); the
constitution's testing strategy is **manual end-to-end validation via [quickstart.md](./quickstart.md)**.
Validation tasks below reference the quickstart scenarios instead of automated test files.

**Organization**: Tasks are grouped by user story. ⚠️ Because the whole command is authored in a single
file (`spectra/commands/brd.md`), the user-story phases here **edit the same file and are therefore
sequential**, not parallelizable with one another (unlike a typical multi-file feature). Parallelism
exists mainly in Setup and the Polish/distribution phase, where separate files are touched.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Paths are repository-relative.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Bring the new command and its bundled asset into the single `spectra/` extension so it can
be installed with `specify extension add --dev ./spectra` and validated.

- [ ] T001 [P] Create `spectra/templates/` and copy `brds/template.md` verbatim to `spectra/templates/brd-template.md` (the shipped BRD template asset — research.md D1).
- [ ] T002 Scaffold `spectra/commands/brd.md`: YAML front matter with a `description`, the H1 title, and empty step headings matching the flow in [contracts/command-interface.md](./contracts/command-interface.md) (Principle III; command name `speckit.spectra.brd`).
- [ ] T003 Register the command in `spectra/extension.yml` under `provides.commands` (name `speckit.spectra.brd`, file `commands/brd.md`, description) so the `--dev` install exposes it — version bump deferred to Polish (Principle II/III).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The shared command "spine" every user story depends on. All tasks edit
`spectra/commands/brd.md` and are therefore sequential.

**⚠️ CRITICAL**: No user story behavior can be validated until this phase is complete.

- [ ] T004 Add the User-Input / `$ARGUMENTS` handling to `spectra/commands/brd.md`: accept inline text, a document path, or both (file is primary, inline text is guidance); if empty, prompt for a requirement or path (FR-001, FR-014, clarification Q3).
- [ ] T005 Add the "Gather project context" step to `spectra/commands/brd.md`: read the constitution (`.specify/memory/constitution.md`), existing BRDs under `/brds`, and prior `specs/`; load the shipped template from `.specify/extensions/spectra/templates/brd-template.md` with an inline section-skeleton fallback (FR-017, research.md D1/D4).
- [ ] T006 Add the BRD numbering/location logic to `spectra/commands/brd.md`: create `/brds` if absent, scan for the highest `NNN`, compute the next zero-padded 3-digit number, build `NNN-<kebab-title>.md`, and never overwrite an existing file (FR-008, FR-009, clarification Q1, research.md D2).
- [ ] T007 Add the "write the BRD" step to `spectra/commands/brd.md`: reproduce the template's 14 sections in order, auto-populate Document Control (BRD-NNN, Title, Author, Status Draft, Version 0.1.0, dates), remove all guidance comments and `[PLACEHOLDER]` tokens, and drop non-applicable sections; guard that the ONLY write is the BRD file under `/brds` (FR-010, FR-011, FR-013, [contracts/brd-output.md](./contracts/brd-output.md)).
- [ ] T008 Add the "report & handoff" step to `spectra/commands/brd.md`: print the output path, a one-line title summary, and instruct the user (in agent-neutral wording — the specify trigger varies per agent, e.g. `/speckit-specify` on Claude) to run the Spec Kit specify command with the BRD — explicitly NOT invoking `specify` (FR-012).

**Checkpoint**: The command can read a requirement, ground it in context, and write a correctly-named BRD.

---

## Phase 3: User Story 1 - Plain-text requirement → structured BRD (Priority: P1) 🎯 MVP

**Goal**: Turn an inline text requirement into a complete, specify-ready BRD under `/brds`, asking
clarifying questions only when the requirement has material gaps.

**Independent Test**: quickstart Scenario 1 — run with a text requirement and confirm a complete BRD
(no placeholders/comments, prioritized Given/When/Then journeys) is written and the path + next step are
reported.

*(Tasks T009–T011 edit `spectra/commands/brd.md`; sequential.)*

- [ ] T009 [US1] Add the transform rules to `spectra/commands/brd.md`: populate all 14 sections grounded in the requirement + clarifying answers only; put genuine unknowns in Open Questions and adopted defaults in Assumptions; never invent requirements (FR-003, FR-006).
- [ ] T010 [US1] Add the specify-ready User-Journeys authoring rules to `spectra/commands/brd.md`: independently valuable, prioritized (P1, P2…) journeys, each with actor/trigger/outcome/flow and Given/When/Then acceptance (FR-007, [contracts/brd-output.md](./contracts/brd-output.md) handoff contract).
- [ ] T011 [US1] Add the clarifying-questions step to `spectra/commands/brd.md`: assess for material gaps, ask up to 5 targeted questions only when gaps exist, wait for answers, fold them in, and proceed best-effort (gaps → Open Questions) if declined; also flag when the requirement spans multiple unrelated features (FR-005, FR-015, research.md D5).
- [ ] T012 [US1] Validate User Story 1 by installing `--dev` and running [quickstart.md](./quickstart.md) Scenarios 1, 4, 5, 6 (text input; thin→questions; empty→prompt; re-run→no overwrite).

**Checkpoint**: MVP — the command produces specify-ready BRDs from text input.

---

## Phase 4: User Story 2 - Requirement document → structured BRD (Priority: P2)

**Goal**: Accept a document file, extract its text, and produce the same structured BRD; degrade
gracefully when text can't be extracted.

**Independent Test**: quickstart Scenario 2 (document → BRD) and Scenario 3 (unreadable/image-only →
clear message, no file written).

*(Task T013 edits `spectra/commands/brd.md`; sequential after Foundational.)*

- [ ] T013 [US2] Add document handling to `spectra/commands/brd.md`: extract text from a supplied path; supported baseline `.md`/`.txt` always and `.docx`/`.pdf` when the host agent can extract text; on unsupported/corrupt/image-only input, report the problem and the readable formats and do NOT fabricate a BRD; reaffirm file-primary precedence when both text and file are given (FR-002, clarification Q3, research.md D3).
- [ ] T014 [US2] Validate User Story 2 via [quickstart.md](./quickstart.md) Scenarios 2 and 3.

**Checkpoint**: Both text and document inputs work; unreadable inputs degrade cleanly.

---

## Phase 5: User Story 3 - Handoff to `/speckit-specify` (Priority: P3)

**Goal**: Guarantee the produced BRD is specify-ready and the command clearly hands off (without
invoking specify).

**Independent Test**: quickstart Scenario 7 — feed a produced BRD to `/speckit-specify` and confirm the
resulting spec's prioritized user stories map one-to-one to the BRD's journeys.

*(Task T015 edits `spectra/commands/brd.md`; sequential.)*

- [ ] T015 [US3] Finalize the handoff in `spectra/commands/brd.md`: ensure the report's next-step wording tells the user to run the Spec Kit specify command with the BRD in agent-neutral phrasing (trigger varies per agent, e.g. `/speckit-specify` on Claude), confirm the command never auto-invokes it, and verify the written BRD satisfies the specify-ready handoff contract in [contracts/brd-output.md](./contracts/brd-output.md) (FR-007, FR-012).
- [ ] T016 [US3] Validate User Story 3 via [quickstart.md](./quickstart.md) Scenarios 7 (handoff) and 8 (context-aware grounding/deconfliction).

**Checkpoint**: End-to-end loop raw requirement → BRD → spec is demonstrable.

---

## Phase 6: Polish & Cross-Cutting Concerns (Principle V — Distribution Sync)

**Purpose**: Version, document, and publish-sync the extension. Tasks touching different files are [P].

- [ ] T017 Bump `extension.version` `1.1.0` → `1.2.0` in `spectra/extension.yml` (new command = MINOR; research.md D7).
- [ ] T018 [P] Add a `1.2.0` entry to `spectra/CHANGELOG.md` describing the `speckit.spectra.brd` command and bundled template.
- [ ] T019 [P] Update `spectra/README.md`: add `speckit.spectra.brd` to the Agents table and add usage/examples.
- [ ] T020 [P] Update `catalog.json`: set `provides.commands` to `4`, add tags (`brd`, `requirements`), bump `version` to `1.2.0` and `updated_at`.
- [ ] T021 [P] Update `docs/index.html` to list the new command on the landing page.
- [ ] T022 [P] Update the Agents table in the top-level `README.md` with the BRD Generator agent.
- [ ] T023 [P] Update `AGENTS_LIST.md`: add the `brd` agent entry (description, arguments, use-it-when, examples) under the shipped agents.
- [ ] T024 Rebuild `docs/packages/spectra.zip` by hand as a single top-level `spectra/` folder, including `templates/brd-template.md` (after all `spectra/` edits are final; Principle V — no build script).
- [ ] T025 Publish gate: verify `catalog.json`, `docs/index.html`, and `docs/packages/spectra.zip` all agree with the `spectra/` folder and use raw `raw.githubusercontent.com/xavient/spectra/main/...` URLs; run a full pass of [quickstart.md](./quickstart.md).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies. T001 [P] with T002; T003 after T002.
- **Foundational (Phase 2, T004–T008)**: after Setup. Sequential (all edit `brd.md`). BLOCKS all stories.
- **User Stories (Phases 3–5)**: after Foundational. **Sequential across stories** because they all edit
  `spectra/commands/brd.md` (US1 → US2 → US3 recommended in priority order). Each story's validation task
  additionally requires T003 (command registered) so the `--dev` install exposes it.
- **Polish (Phase 6)**: after all desired stories. T017 sequential (edits `extension.yml`); T018–T023 [P]
  (distinct files); T024 after every `spectra/` edit; T025 last.

### Within a story

- Prompt-authoring tasks before the validation task.
- Validation runs against an installed `--dev` copy.

### Parallel Opportunities

- T001 ∥ T002 (Setup, different files).
- T018, T019, T020, T021, T022, T023 (Polish) can all run in parallel — separate files.
- The user-story authoring tasks are **not** parallel with each other (single shared file).

---

## Parallel Example: Phase 6 (Polish)

```bash
# After the command file (spectra/commands/brd.md) and version bump are final, sync in parallel:
Task: "Add 1.2.0 entry to spectra/CHANGELOG.md"
Task: "Update spectra/README.md Agents table"
Task: "Update catalog.json (commands 3→4, tags, version, updated_at)"
Task: "Update docs/index.html to list the new command"
Task: "Update top-level README.md Agents table"
Task: "Update AGENTS_LIST.md brd entry"
# Then (sequential): rebuild docs/packages/spectra.zip, then run the publish gate.
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Phase 1 Setup (T001–T003).
2. Phase 2 Foundational (T004–T008).
3. Phase 3 User Story 1 (T009–T012).
4. **STOP and VALIDATE**: quickstart Scenarios 1, 4, 5, 6 — the command produces specify-ready BRDs from
   text input. Demoable MVP.

### Incremental Delivery

1. Setup + Foundational → command spine ready.
2. + User Story 1 → text → BRD (MVP). Validate.
3. + User Story 2 → document → BRD + graceful degradation. Validate.
4. + User Story 3 → confirmed specify-ready handoff. Validate.
5. Phase 6 → version/docs/catalog/zip sync → publishable.

### Notes

- [P] = different files, no dependencies. The single command file makes story phases sequential — do not
  attempt to parallelize US1/US2/US3.
- No automated tests: validation is the manual quickstart (prompt artifact).
- Commit after each task or logical group; the `git` extension offers commit hooks around each step.
