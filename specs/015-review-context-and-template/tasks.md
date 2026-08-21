# Tasks: Review Context, an Overridable Review Template, and Inline Suggestions

**Input**: [spec.md](./spec.md), [plan.md](./plan.md)

**Branch**: `015-review-context-and-template`

**Organization**: grouped by user story. `[P]` marks tasks on disjoint files that may run in parallel.

---

## Phase 1 — User Story 1 & 2: the linked issue as optional context (P1, P2)

- [X] T001 Add `--issue <url-or-number>` to the argument table in `spectra/commands/review-pr.md`, noting that it
  suppresses both detection and the prompt (FR-001).
- [X] T002 Add issue detection to Step 4: `gh pr view --json closingIssuesReferences` first, then a scan of the PR title
  and body for `#<number>` and issue URLs — with the reason the fallback exists (a non-default base has no structured
  link, per `create-pr` 1.8.0) (FR-002, FR-003, D6).
- [X] T003 Add validation via `gh issue view`, continuing without the link when it does not resolve (FR-004).
- [X] T004 Add the ask-once rule, with the prompt stating whether a spec was found — the two questions differ in what the
  issue is for (FR-005, FR-006, D2).
- [X] T005 Add the tiering to Step 5: with no spec, traceability runs **against the issue** in both directions and is
  reported as such; with a spec, the spec authorizes and the issue is background (FR-008, FR-009).
- [X] T006 Add the trust rules: issue content is untrusted data describing intent, never instruction (FR-010).
- [X] T007 Add the severity cap to Step 6: a finding sourced only from an issue is not a Blocker unless the PR claims to
  close that issue (FR-011).
- [X] T008 Add the issue-vs-spec conflict rule: raised as a Question naming both, never adjudicated (FR-012).
- [X] T009 Add issue status to the Step 7 summary and the coverage statement — number, title, state, and how it was
  obtained (FR-007).

**Checkpoint**: a spec-less PR is reviewed against its issue; declining the prompt reproduces today's behaviour.

---

## Phase 2 — User Story 3: the review template (P1)

- [X] T010 Create `spectra/templates/review-template.md`: the summary shape (Summary, Blockers, Major, Minor / Nits,
  Questions, Acknowledged blocker — `- [ ]` on Blockers and Majors only) **and** the inline comment shape, in house style
  with an override preamble (FR-013, FR-017, FR-018, FR-019).
- [X] T011 Register `review-template` in `spectra/extension.yml` under `provides.templates` (FR-013).
- [X] T012 Replace Step 10's hard-coded body format with resolution through the five-layer stack, first usable layer,
  reported path, honour-don't-repair, and an inline skeleton at the end of the command whose H2 list matches the shipped
  template (FR-014, FR-015, FR-020).
- [X] T013 State the template's remit explicitly in both the command and the template: the anchor comment, the
  disclosure line, and the coverage statement are command-emitted and not up for override (FR-016, D3).
- [X] T014 State that the severity rubric, confidence cap, anchor rule, selection grammar, and verdict derivation are not
  overridable, and why (FR-021, D4).

**Checkpoint**: an override reshapes the body; the anchor, disclosure, and coverage survive it.

---

## Phase 3 — User Story 4: inline comments and suggestions (P1)

- [X] T015 In Step 3, record the **commentable ranges** from the patch while it is already fetched, so placement is
  decided locally rather than discovered in a rejection (FR-023).
- [X] T016 Add placement to Step 10: accepted findings anchored inside a hunk become inline comments on `path`/`line`/
  `side`; those outside go to the summary with the reason stated (FR-022, FR-024).
- [X] T017 Add the suggestion rules: ` ```suggestion ` only for a mechanical, complete fix covering exactly the replaced
  range; never for architectural or multi-file changes, undetermined fixes, deleted lines, or generated/vendored files
  (FR-025, FR-026, D8).
- [X] T018 Extend the pre-publish preview to include every inline comment and every suggestion **verbatim**, because a
  suggestion can be applied without being read (FR-027).
- [X] T019 Replace Step 11's publication with one atomic `gh api --method POST repos/{owner}/{repo}/pulls/{number}/reviews`
  call carrying body, comments, and event; keep the `curl`-is-forbidden rule and add the `gh api` sentence to the one rule
  (FR-028, D7).
- [X] T020 Add the demote-and-retry fallback: on a line rejection, identify the comment, move it to the summary, retry
  once, disclose the move (FR-029).
- [X] T021 Add `<n>:body` to the Step 8 selection grammar table (FR-030).
- [X] T022 Replace the *Not in this release* inline-comment note with what now ships, keeping any remaining deferrals
  (FR-031).

**Checkpoint**: a finding on a changed line arrives inline; a mechanical fix arrives as an applicable suggestion; a
failure leaves nothing partial.

---

## Phase 4 — User Story 5: constitution applicability (P3)

- [X] T023 Add applicability reporting to coverage: how many principles were applicable out of how many read; when none
  match, say so and name the Guardrails agent; an absent constitution is stated (FR-032, FR-033, FR-034).

---

## Phase 5 — Release (Principle V, one change)

- [X] T024 Bump `extension.version` to `1.9.0`; update the `review-pr` description to name `--issue`, the template, and
  inline comments (FR-035).
- [X] T025 Mirror `version` and `updated_at` in `catalog.json` (FR-035).
- [X] T026 Add the `[1.9.0]` entry to `spectra/CHANGELOG.md`: the issue tier, the template and its narrow remit, inline
  comments and suggestions with their rails, the atomic publish, and the applicability line (FR-035).
- [X] T027 Rebuild `docs/packages/spectra.zip`; confirm `templates/review-template.md` is inside (FR-035).

---

## Phase 6 — Documentation

- [X] T028 [P] `spectra/README.md` — the `review-pr` section: `--issue`, the template and its override, what the template
  does **not** control, inline comments and suggestions, and the applicability line.
- [X] T029 [P] `AGENTS_LIST.md` — the `review-pr` prose block, with Arguments and a Template bullet.
- [X] T030 [P] `docs/index.html` — the `review-pr` `cdesc` and its Arguments line.
- [X] T031 [P] `test/README.md` — manual passes: a spec-less PR with a body-only issue reference, declining the prompt, an
  override, an inline suggestion applied from the GitHub UI, and a body-only review when nothing is inline-able.

---

## Phase 7 — Tests

- [X] T032 Add `review-pr.md: review-template` to `DOCUMENT_COMMANDS` in `tests/test_document_templates.py` — bringing
  registration, layer order, reported path, and heading parity along for free (FR-036).
- [X] T033 Add `tests/test_review_pr_flow.py`: `--issue` documented; structured detection **and** the text fallback with
  its stated reason; ask-once with spec-aware phrasing; the untrusted-content rule; the issue-sourced severity cap; the
  issue-vs-spec Question; the template's three command-emitted invariants; the not-overridable judgment list; commentable
  ranges computed from the patch; the suggestion exclusion list; the verbatim preview; the single `gh api` call with
  `curl` still forbidden; demote-and-retry; `<n>:body`; the applicability lines; and the retired deferral note (FR-037).
- [X] T034 Mutation-check the guard: drop the suggestion exclusion list and confirm the suite fails naming it; restore.

---

## Phase 8 — Verification

- [X] T035 `python -m unittest discover -s tests` — full suite green.
- [X] T036 `python tools/generate_agent_docs.py --check` — no drift.
- [X] T037 `python tools/build_package.py` re-run — deterministic; `diff -r` clean against `spectra/`.
- [X] T038 Verify against a real Python 3.9 (`uv run --python 3.9`) that every module compiles — the floor guard cannot
  see PEP 701 f-strings on 3.12.
- [X] T039 Reproduce CI's sync gates locally: manifest/catalog version and command count, packaged description, zip
  contents.
- [X] T040 Live check in a throwaway project: `review-template` resolves from the extension and is beaten by an override.

---

## Dependencies

- T001–T009 are independent of the template work and can land first; T005 depends on T002–T004 having established the
  issue.
- T010 → T012 (the command points at the template it describes); T011 is independent of T012.
- T015 → T016 → T017 → T018 → T019 → T020 (each builds on the previous).
- T032 depends on T010–T013; T033 depends on all command edits; T034 depends on T033.
- T024–T027 depend on every command and template edit being final; T027 depends on T024.
- T028–T031 depend on the command edits.
- T035–T040 last.

## Cut lines

If the inline work proves unstable, Phases 1, 2, and 4 stand alone and ship value on their own — the issue tier, the
template, and the applicability line need no API change. Phase 3 is the only part that touches the publication route, and
it is separable: the command published a body-only review for four releases and can continue to.
