# Tasks: Overridable Document Templates

**Input**: [spec.md](./spec.md), [plan.md](./plan.md)

**Branch**: `013-overridable-templates`

**Organization**: grouped by user story so each can be verified on its own. `[P]` marks tasks touching disjoint files that
may run in parallel. Nothing is checked off — this is a plan awaiting approval.

---

## Phase 0 — Close the open questions (blocks everything)

- [X] T000a Resolved **OQ-1** in `/tmp/tmpl-probe` (Spec Kit 0.16.5): the whole extension tree is copied whether or not a
  template is registered, so both variants land at `.specify/extensions/spectra/templates/`; a manifest with
  `provides.templates` validates and installs cleanly; `specify extension info spectra` lists commands only. Recorded in
  [spec.md](./spec.md) § Phase 0 findings, and User Story 3 rewritten to drop the discoverability claim.
- [X] T000b Resolved **OQ-2**: overrides at `.specify/templates/overrides/` survived a `--dev` install, a forced catalog
  install, and `specify extension update spectra`; `remove` scopes itself to the extension tree and its configs. A marker
  written into the installed template was destroyed by `add --force` — the same replace a version bump performs.
  Story 2's promise holds.
- [X] T000c Resolved **OQ-3** with the maintainer: new **Principle VIII** — "Documents Are Shaped by Overridable
  Templates".

**Checkpoint**: all three answered; implementation unblocked.

---

## Phase 1 — Governance

- [X] T001 Amend `.specify/memory/constitution.md` per T000c: a document command's structure comes from a **registered,
  overridable template resolved through Spec Kit's four-layer stack**, with an inline last-resort fallback and never a
  hard-coded path; the command reports which template it used, honours the resolved template rather than repairing it, and
  the resolution is prompt-expressed because the package stays Markdown-only. Bump 1.6.0 → 1.7.0 and prepend the
  sync-impact report (FR-020).

---

## Phase 2 — User Story 1: A project shapes its own ADRs (P1)

- [X] T002 Create `spectra/templates/adr-template.md` reproducing the current inline ADR structure **verbatim** —
  `# ADR-NNN: [Title]`, `**Date:**`, `**Status:**`, Context, Decision, Consequences — in the house style of
  `brd-template.md` (guidance comments in HTML comments, `[PLACEHOLDER]` tokens, a "delete these notes as you fill"
  preamble). No new sections (FR-001, D1).
- [X] T003 Register both templates in `spectra/extension.yml` under `provides.templates` with `name`, `file`, and
  `description`: `adr-template` → `templates/adr-template.md`, `brd-template` → `templates/brd-template.md` (FR-002).
- [X] T004 Rewrite `spectra/commands/adr.md` Step 4 to resolve the template through the five-step order in
  [plan.md](./plan.md) Phase 1, restate "use exactly this template" so the **resolved** template is authoritative, keep
  the current literal at the end of the file as the inline skeleton, and report the resolved path (FR-003 – FR-010).

**Checkpoint**: an override drives the ADR; with none, output matches 1.6.0.

---

## Phase 3 — User Story 2: The same override works for BRDs (P1)

- [X] T005 Replace the hard-coded read in `spectra/commands/brd.md` Step 2 item 1 with the same resolution order, tie the
  existing inline skeleton in as the last resort, and report the resolved path (FR-003 – FR-009).
- [X] T006 Add the fall-through-and-say-so rule to both commands: a layer that exists but is empty or unreadable is
  reported and skipped, never fatal (FR-007).
- [X] T007 Add the honour-don't-repair rule to both commands: a resolved template that omits a section the command would
  normally fill is followed as written, with the omission noted in chat (FR-008, D4).

**Checkpoint**: both agents resolve identically; an override survives `specify extension update spectra`.

---

## Phase 4 — User Story 3: Both templates are declared (P2)

- [X] T008 Update `catalog.json` — version and `updated_at`. The catalog schema carries a command count only, so no
  template count is added (FR-014).
- [X] T009 Confirm the registered manifest installs cleanly and lands both templates at
  `.specify/extensions/spectra/templates/` (measured in T000a; re-confirm against the final manifest).

---

## Phase 5 — User Story 4: The two structures cannot drift (P3)

- [X] T010 Add `tests/test_document_templates.py`: every file in `spectra/templates/` is registered in
  `provides.templates` and every registered entry's file exists; each shipped template's section headings match the
  corresponding command's inline skeleton, in order; both document commands name all four resolution layers plus the
  inline fallback; neither command hard-codes a single template path; no script or binary has entered `spectra/`
  (FR-015 – FR-017, FR-011).
- [X] T011 Mutation-check the new guard: change one heading in `spectra/templates/adr-template.md`, confirm the suite
  fails naming both files, and revert.

---

## Phase 6 — Release (Principle V, one change)

- [X] T012 Bump `extension.version` to `1.7.0` in `spectra/extension.yml` (FR-019).
- [X] T013 Add the `[1.7.0]` entry to `spectra/CHANGELOG.md`: the ADR template becomes an asset, both templates are
  registered, both commands resolve through the stack, `.specify/templates/overrides/<name>.md` is the supported
  customization point and survives updates, and output is unchanged without an override (FR-019).
- [X] T014 Rebuild `docs/packages/spectra.zip` with `python tools/build_package.py`; confirm it contains
  `spectra/templates/adr-template.md` (FR-013).

---

## Phase 7 — Documentation (FR-018)

- [X] T015 [P] `spectra/README.md` — a "Customize the templates" section: the override path per template, that it is
  committed and team-wide, that it survives extension updates, and that omitting sections is honoured.
- [X] T016 [P] `AGENTS_LIST.md` — one line per document agent naming its template and the override path.
- [X] T017 [P] `docs/index.html` — both `cdesc` blocks note the overridable template.
- [X] T018 [P] `CONTRIBUTING.md` — a new document-producing agent ships a registered template and resolves it through the
  stack; it never hard-codes a path.
- [X] T019 [P] `test/README.md` — manual passes: override each template and confirm it drives the output; then
  `specify extension update spectra` and confirm the override survives.

---

## Phase 8 — Verification

- [X] T020 `python -m unittest discover -s tests` — full suite green including the new guard.
- [X] T021 `python tools/generate_agent_docs.py --check` — no generated-region drift.
- [X] T022 `python tools/build_package.py` re-run — deterministic; `diff -r spectra /tmp/unzipped/spectra` clean.
- [X] T023 Reproduce CI's sync gates locally: manifest/catalog version and command count, packaged description, zip
  contents.
- [X] T024 Manual end-to-end in a throwaway project per T019, including the no-override case to confirm SC-003.

---

## Dependencies

- T000a–T000c block everything. T000b in particular can invalidate Story 2.
- T001 depends on T000c.
- T002 → T004 (the command points at the asset it describes); T003 depends on T000a.
- T005–T007 depend on T004's wording being settled, to keep both commands identical in shape.
- T010 depends on T002–T007; T011 depends on T010.
- T012–T014 depend on all command and template edits being final; T014 depends on T012.
- T015–T019 depend on T004–T007.
- T020–T024 run last.

## Cut lines

Phase 0 found no trouble, so nothing is being cut. The degradation paths stay on record in case a later Spec Kit release
changes the ground:

- **Registration rejected by a future validator** → drop Phase 4 and ship resolution alone. Users still get overrides;
  the manifest just stays quiet about templates.
- **A future update starts touching `.specify/templates/`** → stop. Overrides that do not survive updates are the status
  quo dressed up, and shipping them as a feature would be a false promise.
