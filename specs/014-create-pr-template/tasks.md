# Tasks: A Templated, Issue-Linked `create-pr`

**Input**: [spec.md](./spec.md), [plan.md](./plan.md)

**Branch**: `014-create-pr-template`

**Organization**: grouped by user story. `[P]` marks tasks on disjoint files that may run in parallel.

---

## Phase 1 — Governance

- [X] T001 Clarify Principle VIII in `.specify/memory/constitution.md`: it covers documents a command **emits** —
  including a pull request body — not only files written to disk. Bump 1.7.0 → 1.7.1 (PATCH) and prepend the sync-impact
  report (FR-023).

---

## Phase 2 — User Story 1: A PR that follows the project's template (P1)

- [X] T002 Create `spectra/templates/pr-template.md`: Summary, Related Issues, Type of Change, Changes, How to Test,
  Screenshots / Evidence, Breaking Changes, Notes for Reviewers. House style — guidance in HTML comments, `[PLACEHOLDER]`
  tokens, an override preamble. **No checklist section** (FR-005, FR-006, D3).
- [X] T003 Register `pr-template` in `spectra/extension.yml` under `provides.templates` (FR-005).
- [X] T004 Add template resolution to `spectra/commands/create-pr.md`: the five-layer stack, first usable layer,
  report-the-path, honour-don't-repair, and an inline skeleton at the end of the file whose H2 list matches the shipped
  template (FR-004, FR-007, FR-008).
- [X] T005 Add body composition: fill from `spec.md`/`plan.md`/`tasks.md` when the branch has a spec directory, from
  commit messages otherwise, and derive **Changes** from `git diff --name-status <base>...HEAD` in both cases
  (FR-009, FR-010).

---

## Phase 3 — User Story 2: An optional linked issue that actually links (P1)

- [X] T006 Add `--issue <url-or-number>` to the User Input section, and the ask-once-then-drop rule (FR-001, FR-002).
- [X] T007 Add validation via `gh issue view`, continuing without the link when it does not resolve (FR-003).
- [X] T008 Add the rendering rule: closing keyword **only** when the base is `defaultBranchRef`; otherwise a plain
  reference plus an explicit note that GitHub will not link or auto-close it on this merge. Cross-repository issues are
  referenced by full URL and never with a keyword (FR-013, D5).

---

## Phase 4 — User Story 3: Uncommitted work is not silently left behind (P1)

- [X] T009 Replace the dirty-tree warning in Step 8 (today: *"do not commit on their behalf"*) with the file list and the
  question *"there are uncommitted changes, should I proceed with committing and pushing first?"* (FR-014).
- [X] T010 Add the yes path: stage the listed files, commit with a descriptive message, push, report what was done; hooks
  intact, `--no-verify` never used; credential-shaped filenames called out before staging (FR-015, FR-016).
- [X] T011 Add the no path: open from committed work and state plainly that the uncommitted changes are excluded
  (FR-017).
- [X] T012 Restate the command's one rule to permit a commit with explicit consent while still forbidding edits to the
  spec, the constitution, and unrelated source (FR-021).

---

## Phase 5 — User Story 4: One final gate (P2)

- [X] T013 Rework base derivation: documented flow cited when present; otherwise carry a proposal to the gate rather than
  confirming it separately (FR-011, FR-012, D1).
- [X] T014 Add the consolidated pre-flight summary — source → base and its origin, issue or nothing, draft/ready,
  resolved template path — with one yes/no and nothing created before an affirmative (FR-018).
- [X] T015 Add the correction loop: a new base re-checks existence on the remote and recomputes the closing-keyword
  decision before proceeding (FR-012, FR-013).

---

## Phase 6 — User Story 5: Any branch (P2)

- [X] T016 Replace the one-branch-per-spec refusal in Step 5 with detached-HEAD and equal-to-base refusals only, noting
  that a spec branch yields richer body material (FR-019, D4).
- [X] T017 Update the Edge cases table for the relaxed rule and for every new failure mode (empty diff, unresolvable
  issue, corrected base missing on the remote, cross-repo issue).

---

## Phase 7 — Release (Principle V, one change)

- [X] T018 Bump `extension.version` to `1.8.0`; update the `create-pr` description to name `--issue` and stop presenting
  the promotion strategy as the whole story of base derivation (FR-022).
- [X] T019 Mirror `version` and `updated_at` in `catalog.json` (FR-022).
- [X] T020 Add the `[1.8.0]` entry to `spectra/CHANGELOG.md`, including the widened write scope and the closing-keyword
  caveat (FR-022).
- [X] T021 Rebuild `docs/packages/spectra.zip`; confirm `templates/pr-template.md` is inside (FR-022).

---

## Phase 8 — Documentation

- [X] T022 [P] `spectra/README.md` — rewrite the `create-pr` section: `--issue`, the template and its override, the
  commit offer, the final gate, any-branch, and the auto-close caveat.
- [X] T023 [P] `AGENTS_LIST.md` — the `create-pr` prose block, with Arguments and a Template bullet.
- [X] T024 [P] `docs/index.html` — the `create-pr` `cdesc` and its Arguments line.
- [X] T025 [P] `test/README.md` — manual passes: issue on a default-branch PR vs a `dev`-targeted one, dirty-tree yes and
  no, a base correction at the gate, and a run from a non-spec branch.

---

## Phase 9 — Tests

- [X] T026 Add `create-pr.md: pr-template` to `DOCUMENT_COMMANDS` in `tests/test_document_templates.py`, which then
  enforces registration, layer order, reported path, and heading parity for free (FR-024).
- [X] T027 Add `tests/test_create_pr_flow.py`: `--issue` documented in User Input; `gh issue view` validation present;
  the closing keyword tied to the default branch; the commit-and-push question present with the no-`--no-verify` and
  credential-callout rails; the final summary gate present; the one-branch-per-spec refusal gone while detached-HEAD and
  equal-to-base remain; and the surviving guarantees still stated (hard `gh` gate, `--body-file -`, explicit `--head`)
  (FR-020, FR-024).
- [X] T028 Mutation-check the new guard: drop the default-branch condition from the keyword rule and confirm the suite
  fails naming it; restore.

---

## Phase 10 — Verification

- [X] T029 `python -m unittest discover -s tests` — full suite green.
- [X] T030 `python tools/generate_agent_docs.py --check` — no drift.
- [X] T031 `python tools/build_package.py` re-run — deterministic; `diff -r` clean against `spectra/`.
- [X] T032 Reproduce CI's sync gates locally: manifest/catalog version and command count, packaged description, zip
  contents.
- [X] T033 Live check in a throwaway project: install the working copy, confirm `pr-template` resolves from the extension
  and from an override.

---

## Dependencies

- T001 first (the clarification authorizes T004's application of VIII to an emitted document).
- T002 → T004 (the command points at the template it describes); T003 independent of T004.
- T006 → T007 → T008 (gather, validate, render).
- T013 → T014 → T015 (derive, summarize, correct).
- T026 depends on T002–T004; T027 depends on T004–T016; T028 depends on T027.
- T018–T021 depend on every command and template edit being final; T021 depends on T018.
- T022–T025 depend on T004–T016.
- T029–T033 last.
