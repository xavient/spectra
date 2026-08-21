# Tasks: A Supplied Issue Always Reaches the Pull Request

**Input**: [spec.md](./spec.md), [plan.md](./plan.md)

**Branch**: `016-issue-link-invariant`

---

## Phase 1 — User Story 1: a supplied issue is always linked (P1)

- [X] T001 Rewrite the **Related Issues** filling rule in `spectra/commands/create-pr.md` Step 10: the reference goes in
  the template's issue section when it has one — judged by intent, not by the exact heading — or into a short appended
  section when it does not, with one line saying it was appended and why; and it disappears only when there is no issue
  (FR-001 – FR-004, D2, D3).
- [X] T002 Narrow the honour-don't-repair rule in the same step: the template governs shape, and a resolved issue
  reference is a command-emitted obligation — the same line `review-template` draws for its anchor, disclosure, and
  coverage statement (FR-006, D1).
- [X] T003 Confirm the appended section is covered by the pre-publish summary the reviewer approves (FR-007).
- [X] T004 Note in `spectra/templates/pr-template.md` that removing the section does not remove the link — the command
  appends one — so a team trimming the template knows what to expect.

**Checkpoint**: an override without an issue section still yields a linked PR; a run with no issue yields no section.

---

## Phase 2 — User Story 2: the guidance cannot quietly vanish (P3)

- [X] T005 Add to `tests/test_create_pr_flow.py`: the command names the issue reference as an invariant that survives a
  template lacking a section (FR-008).
- [X] T006 Add to the same file: the shipped `pr-template.md` retains a Related Issues section whose guidance states the
  default-branch condition (FR-009).
- [X] T007 Mutation-check both: delete the carve-out from the command and the caveat from the template, confirm each
  fails by name, restore.

---

## Phase 3 — Release (Principle V, one change)

- [X] T008 Bump `extension.version` to `1.9.1` in `spectra/extension.yml` (FR-010).
- [X] T009 Mirror `version` and `updated_at` in `catalog.json` (FR-010).
- [X] T010 Add the `[1.9.1]` entry to `spectra/CHANGELOG.md`: what was already correct, the loophole, and the fix
  (FR-010).
- [X] T011 Rebuild `docs/packages/spectra.zip` (FR-010).

---

## Phase 4 — Documentation

- [X] T012 [P] `spectra/README.md` — one line in the `create-pr` template section: trimming Related Issues does not
  unlink the PR.
- [X] T013 [P] `AGENTS_LIST.md` — same, in the `create-pr` Template bullet.

---

## Phase 5 — Verification

- [X] T014 `python -m unittest discover -s tests` — full suite green.
- [X] T015 `python tools/generate_agent_docs.py --check` — no drift.
- [X] T016 `python tools/build_package.py` re-run — deterministic; `diff -r` clean against `spectra/`.
- [X] T017 Reproduce CI's sync gates locally: manifest/catalog version and command count, packaged description, zip
  contents.
- [X] T018 Real Python 3.9 compile of every module (`uv run --python 3.9`).

---

## Dependencies

- T001 → T002 (same step; the rule is narrowed after the obligation is stated).
- T005–T006 depend on T001–T004; T007 depends on T005–T006.
- T008–T011 depend on every prose edit being final; T011 depends on T008.
- T012–T013 depend on T001–T004.
- T014–T018 last.
