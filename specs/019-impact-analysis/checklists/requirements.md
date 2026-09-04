# Specification Quality Checklist: Feature Impact Analysis

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-09-03
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic (no implementation details)
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification

## Notes

- Items marked incomplete require spec updates before `/speckit.clarify` or `/speckit.plan`

### Validation record — 2026-09-03 (iteration 1)

- **No implementation details.** The spec names no language, library, or search binary. The design
  spec's references to ripgrep and `git clone --depth 1` are deliberately generalized to "whatever
  repository-wide text search the host agent provides" (FR-027) and "the method that inherits the
  user's existing access" (FR-014), because hard-coding either would violate agent-agnosticism and the
  Markdown-only package guarantee. References to a command file, `extension.yml`, `agents-list.json`,
  and the template stack are Spectra's own delivery obligations under Principles II, III, V, VII, and
  VIII — this repository's product *is* the command file, so those are the feature's requirements, not
  implementation leakage.
- **Non-technical readability.** The primary user is a Business Analyst, and the user stories are
  written from their seat: one paragraph in, a cited document out, five questions in between.
- **Testable requirements.** Each FR is stated as an observable obligation with an inspectable
  artifact — a citation that resolves, a scan state in front matter, an absent section when a trigger
  did not fire, a prior document left unmodified.
- **Measurable, technology-agnostic success criteria.** SC-001 to SC-010 measure citation integrity,
  time-to-document, coverage disclosure, retroactive recall and noise, question count, re-run linkage,
  auditability, absence of verdicts, and gate self-sufficiency. None names a tool.
- **Edge cases.** Fourteen are enumerated, covering empty input, zero-hit expansion, saturated caps,
  missing search capability, four distinct access failures, publication signals, unusable declared
  roots, and same-day re-runs.
- **Scope boundaries.** The design spec's §3 boundary table is honoured: no solution design, no story
  points, no requirements, no compliance verdict (FR-038, FR-040, SC-009).
- **One [NEEDS CLARIFICATION] marker remained after iteration 1** — FR-055, where a secondary
  repository's shallow clone is written and whether it is removed. Resolved in iteration 2 by removing
  the premise: see below.

### Validation record — 2026-09-03 (iteration 2 — all items pass)

Both markers were answered by the user and the spec rewritten so that each is a decision rather than a
question. No markers remain.

- **Resolved — no linkage to specifications.** The design spec's forward link (`spec_refs` plus a soft
  lookup inside `speckit.specify`) is dropped in full: the two are independent processes, and a team that
  wants an analysis to inform a spec passes the document as an input, which is already possible. This also
  removes the only part of the design that reached outside the Spectra extension. FR-052 forbids the
  front-matter field, FR-053 narrows `feature_slug` to supersede detection, and FR-054 states the
  prohibition, including no dependency on the `specs/` tree or on Spec Kit's own command files.
- **Resolved — no external repository access.** Shallow clone, API read, and raw URL read are gone. The
  command asks whether this is the only repository the system depends on, and where it is not, each other
  system is declared as free text, a document, or a path to a local copy on the machine (FR-012, FR-013).
  FR-014 forbids URLs, credentials, cloning, downloading, and any network request; FR-015 requires a
  declared path to be read in place with no write outside the project. This eliminated the access-method
  matrix, the per-repository method question, the reuse prompt, four network failure modes, and the clone
  lifetime question that produced the marker. User Story 3, three of its scenarios, the edge cases, the
  non-interactive requirements, Key Entities, and Assumptions were all rewritten to match; FR-018 now
  carries the three local failure reasons and FR-044/FR-045 report per declared system.
- **Recheck of the other items.** Both rewrites narrowed scope rather than widening it: no new
  implementation detail entered (the network prohibition is a behavioural constraint, not a technology
  choice), every changed FR remains individually testable, and no success criterion depended on either
  dropped capability — SC-003 was reworded from "per declared repository or system" to "per declared
  system" and is otherwise unchanged. The full FR set is FR-001 to FR-066 with no gaps.

### Validation record — 2026-09-03 (iteration 3 — all items pass)

Four further decisions from the user, plus two internal contradictions they exposed. No markers introduced.

- **Approval stays manual.** Every run writes `status: draft` (FR-053a); the BA takes the draft to
  stakeholders and records the outcome by hand. The command never sets, prompts for, or infers any other
  status, except marking a prior analysis `superseded` on confirmation. The consequence — a hand-edited
  status leaving the index stale — is closed by FR-056, which refreshes existing index rows from the
  documents' front matter on each run without modifying any document.
- **Two scan modes.** FR-010a to FR-010d: a spec'd project is oriented on its specifications and
  constitution with code read to confirm and extend them; an unspec'd one is reconstructed from source
  alone, which the output declares as the heavier path. FR-010b requires the mode to be stated, FR-010c
  caps document-only evidence below `confirmed` and keeps blast-radius claims on code citations while
  making a spec/code disagreement a finding in its own right, and FR-010d keeps reading a spec from
  creating a relationship to it. **FR-054 was narrowed accordingly** — it previously forbade reading
  `specs/` at all, which would have blocked this; it now forbids creating, linking to, modifying, or
  depending on specifications, which is what the no-linkage decision actually meant. Reading them is
  required by Principle IV regardless.
- **Numbering and naming.** FR-050: `NNN-<name>.md`, the number one greater than the **highest** already in
  the folder rather than a count of files, since counting collides after a deletion (`001` + `003` →
  count-plus-one is `003`). The name is derived per run from the intent and any attachments.
- **Slug stability claim removed.** A per-run derived name cannot be stable, so FR-053 no longer asserts it
  and no longer serves as a join key. Relating two analyses now rests on FR-011, which defines the
  detection signal — slug match or an entity overlap of at least half the smaller set — requires user
  confirmation, and proposes the most recent unsuperseded candidate where several match. Previously "high
  entity overlap" had no threshold, which was the weakest sentence in the spec given that a false positive
  proposes rewriting a document someone else owns.
- **FR-042 vs FR-047 contradiction fixed.** FR-042 required a `path:line` citation on every finding, while
  FR-047 makes "no viable rollback path identified" a High trigger — and absence has no line to cite, so
  the most consequential trigger could not legally be stated as a finding. FR-042 now carves out evidenced
  absence, citing what was searched and where, in the form FR-048 already uses for zero-hit terms.
- **FR-005 off-by-one fixed.** It permitted editing "one front-matter field" of a superseded document while
  FR-052 requires both `status` and `superseded_by`. Both are now named.
- **Recheck.** 71 requirements (FR-001 to FR-066 plus FR-010a–d and FR-053a), no gaps, 10 success criteria.
  User Story 1 gained five scenarios covering evidenced absence, both scan modes, spec/code disagreement,
  and the draft status; User Story 4 gained three covering multi-candidate selection, highest-plus-one
  numbering, and index refresh from a hand-edited status. Five edge cases added. No new implementation
  detail entered: the scan-mode split is a behavioural rule about what to read first, not a technology
  choice.

### Validation record — 2026-09-03 (iteration 4 — all items pass)

- **Re-runs never overwrite, and identical input still produces a report.** FR-051 already forbade
  overwriting; it now also forbids amending, diffing, deduplicating, and refusing a run for having seen the
  same input before. Two gaps this exposed are closed: the front matter carried only a `date`, so two runs
  on the same day were indistinguishable — it now carries a timestamp with the time of day and time zone
  (FR-052) — and nothing recorded what the analysis was *asked*. FR-052a now requires the feature intent
  verbatim plus every attachment by name with whether it was read, which is what makes a folder of reports
  navigable without cross-run diffing. Two User Story 4 scenarios, one edge case, SC-007, and two
  assumptions updated to match. 72 requirements, no gaps.

### Clarification session — 2026-09-03 (`/speckit.clarify`, 5 of 5 questions asked and answered)

All four items previously logged as open were put to the user; three are now closed as requirements and one
is deferred to planning. Two further ambiguities surfaced during the taxonomy scan and were also closed. No
checkbox state changed: 16/16 items were passing before and after, since every change added or tightened a
requirement rather than loosening one.

- **Q1 — identifier sweep bound (data volume, performance).** Answered A: a ranked cap. FR-024 now orders
  identifiers by boundary class — table and column names, endpoint paths, event and topic names above
  configuration keys, flags, and environment variables — sweeps the top N at a default of 50, and discloses
  the cap with the count left unswept. `--identifier-cap` joins FR-028's flags; the caps assumption and the
  cap-saturation edge case updated.
- **Q2 — secrets in citations (security and privacy).** Answered A: cite the location, never the value.
  FR-042a forbids reproducing any credential, key, token, password, or connection string in whole or in
  fragment, anywhere in the document or the session; the finding gives the location and the kind of secret and
  states that the value was withheld. SC-009a makes it measurable, with a User Story 5 scenario and an edge
  case. This was a genuine hole: the spec required a `path:line` citation for every finding, fired the
  security lens exactly when the scan touched secrets, and defaulted the output into `docs/` — which on some
  projects is published.
- **Q3 — attachment mechanics (integration, data formats).** Answered A: file paths in the invocation,
  reading `.md`, `.txt`, `.pdf`, `.docx`, matching `speckit.spectra.brd`. FR-008 records an unreadable,
  missing, or unsupported file by name with its reason and continues. The precedence half of the question had
  a safe default and was applied rather than asked: FR-008a makes the intent paragraph authoritative for what
  is being asked, documents evidence about it, and a contradiction between them a surfaced finding.
- **Q4 — partial runs (reliability).** Answered A: nothing on disk. FR-051a requires the document and index
  row to be written once as the run's final act with the sequence number resolved at that moment, so an
  interrupted run leaves the folder untouched and consumes no number. This mattered more than it looked:
  numbers come from the highest file present, so a half-written report would have pushed the next run's number
  off a document nobody approved.
- **Q5 — no terminal, no switch (interaction, failure handling).** Answered A: detect it, announce it once,
  and behave as though the switch were passed. FR-062a forbids both hanging on input that cannot arrive and
  proceeding silently, matching what the `spectra` CLI already does. Two User Story 6 scenarios and an edge
  case added.

Also normalized during the pass: FR-063's opening line and FR-043's were each briefly clobbered by an
insertion and restored; User Story 5's scenarios renumbered after an insertion. Final counts: 76 requirement
definitions spanning FR-001 to FR-066 with suffixed additions and no gaps or duplicates, 11 success criteria,
0 clarification markers.

**A third clobber was missed here and caught later by `/speckit.analyze`** — see the analysis remediation
record below. The count in this paragraph read 75 because FR-052's bullet had been overwritten the same way,
and its orphaned body still read as plausible prose.

### Analysis remediation — 2026-09-03 (`/speckit.analyze`, all 10 findings applied)

The cross-artifact pass found one CRITICAL, four MEDIUM, four LOW, and one intentional-duplication finding. All
were remediated; the checklist state did not change, since every fix restored or clarified an existing
requirement rather than adding one.

- **F1 (CRITICAL) — FR-052 had no definition.** Its opening bullet had been overwritten when FR-051a was
  inserted during clarification, leaving its body as orphaned prose that read as a continuation of FR-051a —
  so a sequential reader would have attributed the front-matter schema to the write-once rule. Seven artifacts
  cited FR-052, including task T031. The bullet is restored; the spec now has **76** requirement definitions
  with no referenced-but-undefined id and no duplicates. This was the third instance of the same
  insertion-clobber pattern in this spec; the two earlier ones were caught in iteration 3, and this one
  survived because the orphaned text was plausible on its own.
- **F2 (MEDIUM) — the count was wrong in two places.** `plan.md` and this checklist both said 75 requirement
  definitions, which was the bullet count *including* FR-051a and *excluding* FR-052. Both now say 76.
- **T1 (MEDIUM) — four spellings of one scan state.** `declared-not-scanned`, `declared-but-unscanned`,
  "declared but not scanned", and `declared-but-not-scanned` were all in use, and one of them is a front-matter
  key, so the drift reached the output format. Normalized to `declared-not-scanned` in all 18 occurrences
  across spec.md, research.md, and tasks.md. FR-017 now states the three states as exact literals.
- **T2 (MEDIUM) — `<name>` and `feature_slug` were not tied together.** Nothing said whether the filename
  component and the front-matter key held the same string, so `003-cart-abandonment.md` with
  `feature_slug: cart-abandonment-recovery` would have been a legal reading. FR-050, the document contract,
  the data model, Key Entities, and task T008 now all state that it is one value used in two places.
- **T3 (LOW) — the primary repository had no modelled form.** The front-matter example put it in
  `systems_scanned` with `form: project`, but FR-017's enum was written for declared systems only. FR-017 now
  names the project's own entry, and the data model's `form` and `scan_state` enums are complete.
- **C1, C2 (MEDIUM) — two requirements were implemented but uncited.** FR-002 (agent-agnostic, generic
  arguments placeholder) is now cited by T002 and T003; FR-003 (roster registration) by T065, T066, and T067.
  Coverage of defined requirements is now **76 of 76**.
- **C3 (LOW) — success criteria were verified but unnamed.** T072 and T077 now name the ten criteria they
  measure. SC-010 remains deliberately unnamed: it is a post-launch outcome metric, not buildable work.
- **D1 (LOW, intentional) — FR-014 and FR-015 are restated at the point of use.** Kept, because T044 is
  exactly where a helpful agent reaches for `gh`. T045 now requires the restatements to use T006's verbs and
  forbids narrowing them, so the two cannot drift apart.
- **S1 (LOW) — tasks.md contradicted its own note.** It claimed every task cites an FR or a contract while
  twelve publishing and validation tasks legitimately cite a constitution principle or a plan obligation
  instead. The note now says so.

Post-remediation verification: 76 requirement definitions, 0 undefined references, 0 duplicates, 82 tasks with
sequential ids, 76/76 requirement coverage, 10 of 11 success criteria named in tasks, 1 scan-state spelling.

### Open items deliberately not closed

- **Enforcement-test coverage.** No requirement ties the new command into `tests/test_doc_output_paths.py`
  and `tests/test_document_templates.py`, which are what make Principles VII and VIII enforced rather than
  reviewed in this repository. Deferred deliberately: this is a planning-phase concern, and the Constitution
  Check gate in the plan template is where it belongs.
