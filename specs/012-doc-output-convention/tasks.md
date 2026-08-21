# Tasks: One Document-Output Convention — a Declared Artifact Root

**Input**: [spec.md](./spec.md), [plan.md](./plan.md)

**Branch**: `012-doc-output-convention`

**Organization**: grouped by user story so each story can be verified on its own. `[P]` marks tasks that touch disjoint
files and may run in parallel.

---

## Phase 1 — Governance (blocks everything else)

The constitution is the source of truth the command edits implement, so it lands first.

- [X] T001 Amend `.specify/memory/constitution.md`: add **Principle VII — Document Artifacts Live Under One Declared
  Root** covering the canonical shape, the `docs/` default with the `Artifact root:` override, the publication check
  before defaulting, the suggest-never-write rule, lowercase/project-relative paths, one artifact type per folder,
  three-digit numbering, the `.specify/` + `specs/` carve-out, and the legacy read/report/never-move clause
  (FR-012, FR-013, FR-018 – FR-025).
- [X] T002 In the same file, bump **1.5.0 → 1.6.0** and prepend a sync-impact report naming every file this change
  touches; keep prior reports as history.

**Checkpoint**: the convention exists in writing before any file implements it.

---

## Phase 2 — User Story 1: Predictable output folders in a fresh project (P1)

- [X] T003 [P] Rewrite the five `Docs/ADR/` references in `spectra/commands/adr.md` to `docs/adr/` — Step 1 context
  read, Step 3 folder creation and scan, Step 5 write path, Step 7 `git add` (FR-001, FR-003, FR-010).
- [X] T004 [P] Rewrite the eight `/brds` references in `spectra/commands/brd.md` to `docs/brd/` — front-matter
  `description`, intro, the one-rule write-scope clause, Step 2 context read, Step 4 numbering, Step 6 write, Step 7
  report example (FR-002, FR-003).
- [X] T005 Update the `speckit.spectra.brd` description in `spectra/extension.yml` so it no longer names `/brds`
  (FR-011).

**Checkpoint**: a fresh-project run writes to `docs/adr/` and `docs/brd/` and nowhere else.

---

## Phase 3 — User Story 2: An existing project keeps its numbering (P2)

- [X] T006 Add the legacy-read clause to `spectra/commands/adr.md`: read `Docs/ADR/` (any case variant) when present,
  number from the highest across both folders, never move or modify it, and report it once with a `git mv` suggestion
  (FR-005, FR-006, FR-007, FR-008).
- [X] T007 Add the same legacy-read clause to `spectra/commands/brd.md` for `brds/`, keeping the one-file write scope
  intact (FR-005, FR-006, FR-007, FR-008, FR-009).

**Checkpoint**: a seeded legacy project continues its sequence and its old folder is untouched.

---

## Phase 4 — User Story 3: A project that publishes `docs/` is not ambushed (P2)

- [X] T008a Add root resolution to `spectra/commands/adr.md` Step 1: read `Artifact root: <folder>/` from the
  constitution, validate it as project-relative, otherwise default to `docs/` after checking for a publication signal
  (`mkdocs.yml`, `docusaurus.config.*`, `docs/_config.yml`, `docs/.nojekyll`, `docs/index.html`, `docs/conf.py`, a Pages
  config naming `docs`), recommend `documents/` when found, exempt the question from the five-question limit, fall back to
  the non-publishing option when unanswered, and offer the declaration line without writing it
  (FR-018 – FR-025).
- [X] T008b Add the same root resolution to `spectra/commands/brd.md` Step 2, with the stronger publication warning a
  BRD's contents warrant, and a note that writing the declaration would break its one-rule write scope
  (FR-018 – FR-025).
- [X] T008c Thread the resolved root through both commands' numbering, write, and report steps, and add
  `docs/<artifact>/` to the superseded locations read for numbering when a different root is in force (FR-001, FR-002,
  FR-005, FR-006).

**Checkpoint**: a declared root moves both agents; a published `docs/` is raised before anything is written.

---

## Phase 5 — User Story 4: The convention outlives this change (P3)

- [X] T008 Add `tests/test_doc_output_paths.py`: assert no command file *instructs a write* into a superseded folder;
  assert `adr.md` and `brd.md` name their canonical folders and write targets; assert every `docs/<slug>/` reference uses
  a lowercase kebab-case slug; assert no absolute output path; assert both commands resolve the declared root, refuse to
  write it, check every publication signal, and recommend `documents/`; assert the manifest description is clean; assert
  the constitution carries Principle VII with its carve-out, legacy read, declarable root, and publication check
  (FR-014).
- [X] T009 Add a note to `CONTRIBUTING.md` telling a contributor adding a document-producing agent to follow
  Principle VII — including honouring a declared root, checking before defaulting into `docs/`, and never writing the
  declaration — and recording that Spectra's own `brds/` is deliberately left in place (FR-017).

**Checkpoint**: a non-conforming command file fails the suite by name.

---

## Phase 6 — Release the extension (Principle V, one change)

- [X] T010 Bump `extension.version` to `1.6.0` in `spectra/extension.yml` (FR-016).
- [X] T011 Mirror `version` and `updated_at` in the `spectra` entry of `catalog.json` (FR-016).
- [X] T012 Add the `[1.6.0]` entry to `spectra/CHANGELOG.md`: both old paths, both new ones, the declarable root, the
  publication check, the legacy-read behavior, and the new principle (FR-016).
- [X] T013 Rebuild `docs/packages/spectra.zip` with `python tools/build_package.py` (FR-016).

---

## Phase 7 — Documentation echoes (FR-015)

- [X] T014 [P] `spectra/README.md` — the `adr` and `brd` sections, including the root override, the publication check,
  and the legacy-read behavior.
- [X] T015 [P] `AGENTS_LIST.md` — the hand-authored `adr` and `brd` prose blocks, each with a "Where it writes" bullet.
- [X] T016 [P] `docs/index.html` — the `cdesc` text for `speckit.spectra.brd` and `speckit.spectra.adr`.
- [X] T017 [P] `test/README.md` — the manual-test expectations, plus a pass for the declared root and the publication
  prompt.

---

## Phase 8 — Verification

- [X] T018 `python -m unittest discover -s tests` — full suite green, including the new guard.
- [X] T019 `python tools/generate_agent_docs.py --check` — no generated-region drift, no missing prose block.
- [X] T020 `python tools/build_package.py` re-run — zip is deterministic and matches the working tree.
- [X] T021 Repository grep for `Docs/ADR` and `/brds` — hits only in historical artifacts and legacy-handling clauses
  (SC-003).
- [X] T022 Confirm `git status` shows no modification under `brds/` (FR-017).

---

## Dependencies

- T001–T002 (governance) precede everything.
- T003–T005 precede T006–T007, which precede T008a–T008c (same files, layered: canonical paths, then legacy reading,
  then the declared root that generalizes both).
- T008 depends on T001 and T003–T008c (it asserts their result).
- T010–T013 depend on the command edits being final; T013 depends on T010.
- T014–T017 depend on T003–T008c (they describe the new behavior).
- T018–T022 run last.
