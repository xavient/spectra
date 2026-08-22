# Tasks: Spec Discovery Without the Feature Record

**Input**: [spec.md](./spec.md), [plan.md](./plan.md)

**Branch**: `017-spec-discovery-without-feature-record`

---

## Phase 0 — Verification of the premise

- [X] T001 Confirm Spec Kit ignores `.specify/feature.json` by CLI rule: `SPECIFY_GITIGNORE_CONTENT` in
  `specify_cli/shared_infra.py` (installed `specify 1.0.1`), written through the managed-file writer.
- [X] T002 Confirm how it reached this project: `.specify/.gitignore` first appears in commit `93f8c4c`.
- [X] T003 Confirm the stale-pointer case is real, not theoretical: the file is still tracked here, matched by the ignore
  rule under `--no-index`, and `origin/main` carries `specs/016-issue-link-invariant`.
- [X] T004 Confirm the reliance is soft: tier 3 terminates the chain, the no-spec path is fully specified, and no other
  file in `spectra/` reads the record.

---

## Phase 1 — User Story 1: no spec is ever guessed (P1)

- [X] T005 Rewrite tier 2 of "Locating the spec" in `spectra/commands/review-pr.md`: a spec the reviewer names, read at
  `headRefOid`, falling through to tier 3 when it does not resolve there (FR-003, FR-004, D2, D5).
- [X] T006 Replace the branch-name paragraph with the two-item forbidden list — branch name and Spec Kit feature record —
  each with its reason, and state what a wrong guess costs (FR-001, FR-002, D1, D4).
- [X] T007 Reword the absent-vs-unreachable paragraph off "a legitimate tier-2 miss" without weakening the
  404-versus-wrong-repo distinction it protects.
- [X] T008 Spell out the three sources in the coverage line: found in the diff, named by the reviewer, or neither
  (FR-007).

**Checkpoint**: no instruction to read `feature.json` remains, and both forbidden guesses are named with reasons.

---

## Phase 2 — User Story 2: the addendum case survives, on evidence (P2)

- [X] T009 Turn the issue question into the run's **single context question**: both baselines in one ask when both are
  missing, referencing tier 2 for the path (FR-005, D3).
- [X] T010 Add the spec-only variant for a run whose issue is already in hand, and the explicit one-question-per-run rule
  (FR-005, FR-006).
- [X] T011 Narrow the `--issue` row in the argument table: it suppresses the issue question, not the spec question
  (FR-006).
- [X] T012 Name how the spec was located in Step 7 element 3 (FR-007).
- [X] T013 Confirm tier 1 and tier 3 wording is untouched, including the no-spec consequences in Step 5 (FR-008).

---

## Phase 3 — Tests (FR-009)

- [X] T014 Add `SpecDiscovery` to `tests/test_review_pr_flow.py`: diff-first, reviewer-named, read at the pinned revision,
  fall-through, addendum coverage, no-spec outcome, both bans with their reasons, the resolved-source report, the single
  question, and `--issue` not suppressing the spec ask.
- [X] T015 Add the mutation guard: `refuteStates("Read `feature_directory` from")` fails the build if the retired read
  returns.
- [X] T016 Update `test_declining_proceeds_on_the_constitution` from `means **no issue**` to `means **neither**`, since the
  one question can now ask for a spec as well.
- [X] T017 Mutation-check the new class: restore the old tier-2 text and confirm the suite fails by name, then revert.

---

## Phase 4 — Release (Principle V, one change)

- [X] T018 Bump `extension.version` to `1.10.0` in `spectra/extension.yml` (FR-010).
- [X] T019 Mirror `version` and both `updated_at` fields in `catalog.json` (FR-010).
- [X] T020 Add the `[1.10.0]` entry to `spectra/CHANGELOG.md`: what changed upstream, why the stale read was the real
  hazard, and what replaced the tier (FR-010).
- [X] T021 Rebuild `docs/packages/spectra.zip` with `python3 tools/build_package.py` (FR-010).

---

## Phase 5 — Documentation

- [X] T022 [P] `spectra/README.md` — step 4 of the review-pr walkthrough: diff, then a path you name, and neither branch
  name nor feature record.
- [X] T023 [P] `AGENTS_LIST.md` — a **Spec discovery** bullet in the review-pr block, and the one-question note on the
  Linked issue bullet.

---

## Phase 6 — Verification

- [X] T024 `python3 -m unittest discover -s tests` — full suite green.
- [X] T025 `python3 tools/generate_agent_docs.py --check` — no drift.
- [X] T026 `python3 tools/build_package.py` — deterministic rebuild, zip contents match `spectra/`.
- [X] T027 Grep the package for `feature.json` — the only hits are the prohibition, the changelog entry, and the README
  line documenting them; no read instruction survives (SC-001).

---

## Phase 7 — Repository hygiene (not part of the extension)

- [X] T028 Untrack this repository's own `.specify/feature.json` so the stale pointer stops being shared. Staged only —
  committing and pushing is the maintainer's call.

---

## Dependencies

- T001–T004 precede everything: the premise is verified before the tier is removed.
- T005 → T006 → T007 → T008 (one section, in order).
- T009 → T010 → T011 (the question, then what suppresses it).
- T014–T017 depend on T005–T013.
- T018–T021 depend on every prose edit being final; T021 depends on T018.
- T022–T023 depend on T005–T012.
- T024–T027 last. T028 is independent of the extension change.
