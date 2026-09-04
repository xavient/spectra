# Tasks: Feature Impact Analysis

**Input**: Design documents from `/specs/019-impact-analysis/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md),
[data-model.md](./data-model.md), [contracts/](./contracts/), [quickstart.md](./quickstart.md)

**Tests**: Included, and not optional here. This repository enforces Principles V, VII, and VIII with a
Python suite — `tests/test_doc_output_paths.py` and `tests/test_document_templates.py` derive their checks
from per-command registries, and `tests/test_roster_data.py` asserts the roster census. A new document agent
that does not appear in all three is unguarded, and that is the one item `/speckit.clarify` deferred to
planning. Test tasks are in Phase 10.

**Organization**: by user story, in the priority order the spec assigns. One caveat particular to this
project: the runtime deliverable is a **single Markdown file**, so most tasks add a section to
`spectra/commands/impact.md` and are therefore **strictly sequential within a phase**. Genuine parallelism
appears in Phase 9 (publishing, different files) and Phase 10 (tests, different files).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel — different file, no dependency on an incomplete task
- **[Story]**: the user story the task serves (US1–US6)
- Every task names its file and cites the requirements it implements

## Path Conventions

This is a Spec Kit extension, not an application. There is no `src/`.

- Runtime deliverables: `spectra/commands/impact.md`, `spectra/templates/impact-analysis-template.md`
- Manifest and catalog: `spectra/extension.yml`, `catalog.json`
- Roster and docs: `agents-list.json`, `README.md`, `AGENTS_LIST.md`, `docs/index.html`, `spectra/README.md`
- Package: `docs/packages/spectra.zip` (built, never hand-edited)
- Tests: `tests/`

---

## Phase 1: Setup

**Purpose**: record what "before" looks like, then create the file with its interface and its one governing
rule.

- [X] T001 Record the pre-implementation baseline from the repository root: `python3 tools/generate_agent_docs.py --check` reads **46 agents / 6 prose blocks / roster and manifest agree**; `python3 tools/build_package.py` followed by `git diff --stat docs/packages/spectra.zip` shows no drift; `spectra/extension.yml` is at **1.11.1** with **6** commands and **4** templates, and `catalog.json` agrees at 1.11.1 / 6; `tests/test_roster_data.py` asserts **46 agents, 15 available, 31 planned, 9 from Spec Kit**; `python3 -m unittest discover -s tests` is green at **752 tests**. Phase 10 asserts these became 47 agents / 7 prose blocks / 1.12.0 / 7 commands / 5 templates / 16 available / 31 planned.
- [X] T002 Create `spectra/commands/impact.md` with YAML front matter carrying a single `description` key in the style of `spectra/commands/brd.md`, an H1 title, and a one-paragraph statement of the job: take one paragraph of feature intent, scan the project, and write a numbered, citation-backed impact analysis a BA takes to a stakeholder go / no-go gate before any specification work begins (FR-001, FR-002).
- [X] T003 Add the **User Input** section to `spectra/commands/impact.md` documenting the whole `$ARGUMENTS` surface per [contracts/command-interface.md](./contracts/command-interface.md): the feature intent as the one required input; optional document paths (`.md`, `.txt`, `.pdf`, `.docx`) with the ranking a feature request / brief / epic, then external-system descriptions, then prior analyses; and the flags `--non-interactive`, `--seed-cap`, `--hops`, `--max-files`, `--identifier-cap`, `--per-system-cap` (FR-006, FR-008, FR-028, FR-062). Use the generic arguments placeholder and no agent's invocation syntax anywhere in the file (FR-002). State that an empty intent stops the run with a message naming what to supply, and scans nothing (FR-007).
- [X] T004 Add the **one rule that governs everything** section to `spectra/commands/impact.md`, stated once and in full: *read this project and anything the user points you at, ask at most five questions, then write exactly two files inside this project — and never touch the network.* Name it as the sentence every later rule narrows, in the style of the equivalent section in `spectra/commands/brd.md`.
- [X] T005 Add the **attachment handling** rules to `spectra/commands/impact.md`: read the four supported formats; record a missing, unreadable, or unsupported-type path by name with that reason and continue rather than failing (FR-008); and state that the intent paragraph is authoritative for *what is being asked* while documents are evidence about it, so a document contradicting the intent is surfaced rather than silently preferred (FR-008a).

**Checkpoint**: the file exists, declares its full input surface, and states its limit.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: the machinery every story depends on — the prohibitions, the two write rules, root and template
resolution, and the trustworthiness rules that are the product.

**⚠️ CRITICAL**: no user story work can begin until this phase is complete. Every task except T013 edits the
same file and they are strictly sequential.

- [X] T006 Add the **prohibition list** to `spectra/commands/impact.md`, reproducing the table in [contracts/command-interface.md](./contracts/command-interface.md): no repository URL, credential, token, or login accepted or requested; no clone, no download, **no network request of any kind** (FR-014); no write outside the project and no create, modify, delete, or copy inside a declared local path (FR-015); no spec created, referenced, or linked, and nothing under `specs/` written or depended on (FR-054); no constitution edit, branch, or commit (FR-005). State explicitly that no argument or instruction in the session enables any of them.
- [X] T007 Add the **write-once rule** to `spectra/commands/impact.md`: the document and the index are written once, as the run's final act, and the sequence number is resolved at that moment — so a run that is interrupted, abandoned, or fails leaves the impact-analysis folder exactly as it found it, with no partial document, no incomplete marker, and no number consumed (FR-051a). State that everything before the write is reading and asking, which is why there is nothing to clean up.
- [X] T008 Add the **numbering rule** to `spectra/commands/impact.md`: `NNN-<name>.md`, where `NNN` is **one greater than the highest number already in the folder** — never a count of the files there, because counting collides after a deletion — starting at `001` in an empty folder, independent of the `specs/` sequence; and `<name>` is a kebab-case name derived per run from the intent and any attachments, which is **the same string as the front-matter `feature_slug`** and explicitly **not** stable across runs (FR-050, FR-053).
- [X] T009 Add the **artifact root resolution** step to `spectra/commands/impact.md` per [contracts/document-contract.md](./contracts/document-contract.md), following the wording already in `spectra/commands/brd.md`: a declared `Artifact root: <folder>/` line in the constitution wins, matched case-insensitively and rejected if absolute or containing `..`; otherwise `docs/` **after** checking for a publication signal (`mkdocs.yml`, `docusaurus.config.*`, `docs/_config.yml`, `docs/.nojekyll`, `docs/index.html`, `docs/conf.py`, or a Pages configuration pointing at `docs`); a signal with no declared root is surfaced with `documents/` recommended, and the question does not count against the five; no answer obtainable means take the non-publishing option and say so; the declaration line is offered and never written (FR-049). Add the reason this artifact needs it as much as a BRD does: it names internal systems, owning teams, unmitigated risks, and where secrets live.
- [X] T010 Add the **template resolution** step to `spectra/commands/impact.md`, the five layers in order — `.specify/templates/overrides/impact-analysis-template.md`, `.specify/presets/<preset-id>/templates/…`, `.specify/extensions/spectra/templates/…`, `.specify/templates/…`, then the inline skeleton — taking the first layer that is readable **and non-empty** rather than the first that exists, reporting a present-but-unusable layer in one line and continuing, never editing a template, and reporting the resolved path (FR-057, FR-059).
- [X] T011 Add the **honour, do not repair** rule to `spectra/commands/impact.md`: follow the resolved template's sections in its order, never add, rename, or reorder them, note rather than reinstate a section it omits — including a lens — and strip guidance comments and `[PLACEHOLDER]` tokens whichever layer the template came from (FR-060). State the boundary from [contracts/document-contract.md](./contracts/document-contract.md): the trustworthiness rules live in this command, not in the template, so an override that drops *Sources consulted* drops the section and the coverage statement still appears in the session.
- [X] T012 Add the **project override** note to `spectra/commands/impact.md`, once: a team reshapes every future analysis by copying the resolved template to `.specify/templates/overrides/impact-analysis-template.md` and committing it — outside the extension tree, so it survives `specify extension update` — and the command never creates that file itself, because doing so would breach the one rule in T004.
- [X] T013 [P] Create `spectra/templates/impact-analysis-template.md` with the ten sections in the order fixed by [contracts/document-contract.md](./contracts/document-contract.md) — Change statement, Inputs, Impact rating, Findings (five core lenses plus the two conditional headings), External contract changes, Human follow-up required, Open risks and rollback, Clarifications, Assumptions and unknowns, Sources consulted — in the house style of `spectra/templates/brd-template.md`, with guidance comments and placeholder tokens the command is required to strip. Its manifest registration is T060; the file alone is not enough (FR-058).
- [X] T014 Add the **inline skeleton** to the end of `spectra/commands/impact.md`, as the last-resort layer, with headings **identical** to `spectra/templates/impact-analysis-template.md` — `tests/test_document_templates.py` asserts heading parity between the two, so this is a second copy that must not drift.
- [X] T015 Add the **trustworthiness rules** section to `spectra/commands/impact.md`, all five, each stated as an invariant rather than a preference: absence of evidence is never absence of impact, and "no consumers found in what was scanned" is the only permitted form (FR-041); every finding carries a `path:line` citation, with **evidenced absence the one exception**, cited as what was searched and where, in the form FR-048 uses for zero-hit terms (FR-042); any change to a public API, event schema, database table, or shared contract escalates to a human-verification item regardless of what the scan found internally (FR-043); coverage is stated per declared system as files read of files present with the selection method (FR-044); and a cap reached or a path unreadable is reported with its reason, never truncated silently (FR-045). Add the requirement to record terms searched that produced no hits (FR-048).
- [X] T016 Add the **confidence taxonomy** to `spectra/commands/impact.md` as the fixed evidence mapping from [research.md](./research.md) §9, so two runs assign levels the same way: code read this run and cited → `confirmed`; naming convention, config reference, or a string-literal match, cited → `probable`; a specification or other document with no code citation → `probable` at best and **never** `confirmed`; a dynamic-pattern hit → `possible`; a suspected consumer in a `declared-not-scanned` system → `possible`, requiring human verification (FR-046, FR-010c).
- [X] T017 Add the **impact rating trigger table** to `spectra/commands/impact.md` verbatim from FR-047, and state that the rating is derived from it rather than judged and that the output names the trigger that fired: High on an irreversible data change, an external contract change, either conditional lens firing, or no viable rollback path identified; Medium on an internal contract change, a reversible migration or backfill, or a behaviour change visible to existing users or callers; Low only when the change is additive, trivially revertible, and touches neither data nor an external contract.
- [X] T018 Add the **secret prohibition** to `spectra/commands/impact.md`, stated in full and separately from the citation rule because it overrides it: never reproduce a credential, key, token, password, or connection string — in whole or in fragment — anywhere in the document or the session; where a line it would cite carries one, give the location and the kind of secret only and state that the value was deliberately not reproduced (FR-042a). Include the recognition patterns from [research.md](./research.md) §8 and the instruction that over-withholding is the correct error to make.
- [X] T019 Add the **caps** table to `spectra/commands/impact.md` — 30 seed files, 2 hops, 80 project files, 50 swept identifiers, 20 files per declared system — with the flag that overrides each, the requirement that any non-default value appears in Sources consulted alongside the coverage numbers, and the note that the five-question cap is not configurable (FR-028, FR-029).
- [X] T020 Add the **context reading** step to `spectra/commands/impact.md` (FR-009): read the constitution and guardrails, any existing specifications under `specs/`, source code, `docs/` and `README` and ADR titles, API contract definitions, schema and migration files, the test suite, CI configuration, and the existing impact-analysis folder — all without prompting for any of it. Add the rule that nothing discoverable in the repository is ever asked as a question (FR-010).

**Checkpoint**: the command knows what it may not do, where and when it may write, what shapes its output,
and what makes a finding trustworthy.

---

## Phase 3: User Story 1 — Ground the go / no-go in the code (Priority: P1) 🎯 MVP

**Goal**: one paragraph in, one cited, coverage-declaring impact analysis out, written once at the end.

**Independent Test**: run with a one-paragraph intent in a repository with known coupling. Every Findings
item resolves to real content at its cited `path:line`; Sources consulted names files read of files present
and the scan mode; nothing claims absence of impact; `git status` shows exactly two new files. Quickstart
Pass 1.

- [X] T021 [US1] Add the **two scan modes** to `spectra/commands/impact.md`: where the project carries specifications and/or a constitution, orient on them — entity vocabulary, declared boundaries, prior decisions, stated constraints — and read code to confirm and extend them; where neither exists, build the understanding from source alone and state that this is the heavier path (FR-010a). Require the mode and what was read to orient to appear in the output (FR-010b).
- [X] T022 [US1] Add the **document-evidence guard** to `spectra/commands/impact.md`: a specification records intent and drifts from code, so a finding whose only evidence is a document is never `confirmed`, every blast-radius claim rests on a code citation, and a document that disagrees with the code is itself a finding (FR-010c). Add that reading a specification creates no relationship to it — a document may be cited as the provenance of a finding, which is evidence, not linkage (FR-010d).
- [X] T023 [US1] Add the **structural map** phase to `spectra/commands/impact.md`: directory tree, file inventory, package manifests, entrypoints, route definitions, migration directory, configuration, CI — reading full contents only for a short whitelist (`README`, `docs/` index, ADR titles, guardrails, constitution), so this phase's cost does not scale with repository size (FR-019).
- [X] T024 [US1] Add the **entity extraction and term expansion** phase to `spectra/commands/impact.md` (FR-020), with the worked example table from the design: expand every entity across camelCase, snake_case, kebab-case, SCREAMING_SNAKE, singular and plural, table-naming conventions, and synonyms observed in the structural map. State plainly that this phase is where most of the recall comes from and that under-expanding produces a confident report with a hole in it.
- [X] T025 [US1] Add the **seed search** phase to `spectra/commands/impact.md`: rank hits by term density weighted by file role — API contracts, route handlers, controllers, migrations, event handlers, and public interfaces highest; domain models, services, and data access high; tests referencing them medium; internal utilities and helpers low — and cap the seed set at the configured seed cap (FR-021).
- [X] T026 [US1] Add the **bounded graph expansion** phase to `spectra/commands/impact.md`: from the seeds, at most the configured hop budget outward over imports and exports, callers, dependency-injection registrations, route bindings, data access, and event emit/subscribe pairs, including tests that reference seeds because they define what is currently guaranteed, capped at the configured total file budget (FR-022).
- [X] T027 [US1] Add the **dynamic-pattern sweep** to `spectra/commands/impact.md`, naming all eight families with an example each: reflection and dynamic dispatch, dynamic or lazy imports, string-keyed handler registries and factory maps, configuration-driven behaviour, cron/scheduler/queue consumer registration, feature-flag lookups, serialization and deserialization boundaries, and templating or view resolution by name (FR-023). State that this is the sole defence against coupling the import graph cannot see.
- [X] T028 [US1] Add the **contract-identifier sweep** to `spectra/commands/impact.md`: extract table and column names, endpoint paths, event and topic names, configuration keys, feature-flag keys, and environment variable names from the seed set; order them contract-bearing tier first (table, column, endpoint, event, topic) then config-bearing (config key, flag, env var) per [research.md](./research.md) §4; sweep the top N as raw strings **across the entire repository, independent of the import graph**; and disclose the cap with the number left unswept when it binds (FR-024). Require every hit from either sweep to become a `possible`-confidence item flagged for human verification, never silently dropped (FR-025).
- [X] T029 [US1] Add the **search capability** statement to `spectra/commands/impact.md`: state the search the command needs — list a tree, read a file, find a literal string anywhere in the project — and that it uses whatever the host agent provides, names no tool, and ships no script or binary; where no project-wide text search exists, say so before the sweeps and report the reduced coverage rather than quietly narrowing to the import graph (FR-027, [research.md](./research.md) §1).
- [X] T030 [US1] Add the **five core lenses** to `spectra/commands/impact.md`, each with its question and its evidence source: blast radius (what code, contracts, and consumers are touched), data (schema, migration, backfill, and who reads that data), behavioural change (what existing users or callers experience without asking), risk and reversibility (what breaks, how it is detected, how to back out, what becomes irreversible), effort and sequencing (rough size and what must land first) — with the note that lens 4 is the one stakeholders are actually deciding on, and that lens 5 is a coupling-depth heuristic and must be labelled as one, never an estimate (FR-036).
- [X] T031 [US1] Add the **front matter schema** to `spectra/commands/impact.md` per [contracts/document-contract.md](./contracts/document-contract.md), field by field, including: `status` is **always `draft`** on write and the command sets no other status except the `superseded` of T049 (FR-053a); `generated` carries date, time of day, and time zone so two runs on one date are distinguishable (FR-052); `author` comes from the local committing identity where discoverable and is left **empty rather than invented** where it is not; `scan_mode`, per-system scan states with coverage, `declared-not-scanned` systems with form, owner, and reason, `questions_asked`, `questions_defaulted`, and `caps_overridden`. State that there is **no `spec_refs` key in any form** (FR-052, FR-054).
- [X] T032 [US1] Add the **Inputs section** requirement to `spectra/commands/impact.md`: record the feature intent **verbatim as supplied** and every attachment by name or path with whether it was readable and read (FR-052a). State the reason — a reader six months later must see what the analysis was asked, and two reports on one feature are told apart by their inputs and their timestamps.
- [X] T033 [US1] Add the **change statement, rollback, and irreversibility** requirements to `spectra/commands/impact.md`: restate the change in one line so a reader can catch a misread, and carry both a rollback path and the point at which the change becomes irreversible (FR-061). Note that "no viable rollback path identified" is a High trigger and is stated as an evidenced absence under T015's exception, not demoted to an assumption.
- [X] T034 [US1] Add the **Sources consulted** requirements to `spectra/commands/impact.md`: coverage per declared system as files read of files present with the selection method, the scan mode, every cap reached with what it cut, and the terms searched that produced no hits (FR-044, FR-010b, FR-045, FR-048). State that this section and Assumptions are what let a reviewer distinguish "checked and found nothing" from "did not check".
- [X] T035 [US1] Add the **write step** to `spectra/commands/impact.md`: resolve the number, write `<artifact-root>/impact-analysis/NNN-<name>.md`, and create the index with this run's row if the folder has none — all as one final act, in the order fixed by T007 (FR-049, FR-050, FR-056).
- [X] T036 [US1] Add the **run report** to `spectra/commands/impact.md` per [contracts/chat-output.md](./contracts/chat-output.md): document path and id, resolved template path, rating with the trigger that fired, coverage per system with the scan mode, caps reached and what they cut, questions asked and defaulted, and the closing line that the status is draft and the stakeholder answer is the user's to record.

**Checkpoint**: US1 is shippable on its own — one paragraph produces one cited, honest document.

---

## Phase 4: User Story 2 — Close the gaps the code cannot answer (Priority: P1)

**Goal**: at most five generated questions, each with options and a reasoned recommendation, none of them
blocking.

**Independent Test**: run against an intent that leaves scope and data lifecycle open. No more than five
questions, one at a time, each with 3–4 options, an `Other`, and a recommendation citing a scan finding;
skip one and it is recorded as `defaulted` and promoted into risks. Quickstart Pass 2.

- [X] T037 [US2] Add the **question generation** rules to `spectra/commands/impact.md`: questions are generated from what the scan found ambiguous, never selected from a fixed list, and ranked by how much the answer would change the blast radius or the impact rating; at most five, fewer when fewer things are genuinely ambiguous, and **never padded** to five (FR-029, FR-030). Include the six productive categories in priority order — scope boundary, data lifecycle, existing-user behaviour, contract compatibility, reversibility expectation, non-functional threshold.
- [X] T038 [US2] Add the **question format** to `spectra/commands/impact.md` per [contracts/chat-output.md](./contracts/chat-output.md): one at a time, each waiting for its answer; 3 or 4 substantive options; `Other` as the final numbered option accepting a free-text sentence; and a recommendation **with its reasoning**, grounded in a scan finding wherever one exists (FR-031, FR-032). Include the worked example with its cited finding.
- [X] T039 [US2] Add the **skip behaviour** to `spectra/commands/impact.md`: a skipped question proceeds on the recommended answer, is recorded as an assumption tagged `defaulted — not confirmed`, and never blocks the run (FR-033).
- [X] T040 [US2] Add the **promotion rule** to `spectra/commands/impact.md`: a defaulted answer in the scope-boundary, data-lifecycle, or contract-compatibility categories is additionally promoted into the risks section, because a wrong default in those three changes the answer rather than merely colouring it (FR-034).
- [X] T041 [US2] Add the **Clarifications table** requirement to `spectra/commands/impact.md`: every question asked appears with its answer and whether that answer came from the user or was defaulted (FR-035).

**Checkpoint**: the interaction is complete, bounded, and cannot stall.

---

## Phase 5: User Story 3 — Widen the scope past this repository (Priority: P2)

**Goal**: other systems declared in whatever form the user has, with a narrow consumer scan where a local
copy exists and a targeted handoff item where it does not.

**Independent Test**: answer no to the scope question; declare one system by local path and one by a
sentence. The local one is searched for contract identifiers only and is left untouched; the described one
produces a team-addressed handoff item; both appear in front matter with the right scan state. Quickstart
Pass 3.

- [X] T042 [US3] Add the **pre-flight scope question** to `spectra/commands/impact.md` in the shape fixed by [contracts/chat-output.md](./contracts/chat-output.md) — is this repository the only one this system depends on, recommending "no" where the user is unsure — asked **before any scanning** (FR-012). State that this and every other pre-flight question are outside the five-question budget, because spending analysis budget on scope wastes the part of the interaction with the most leverage (FR-016).
- [X] T043 [US3] Add the **three declaration forms** to `spectra/commands/impact.md`: a free-text description, a document, or a path to a local directory holding a copy of that system's source — none required, with an owning team name accepted and not required (FR-013).
- [X] T044 [US3] Add the **no-fetch response** to `spectra/commands/impact.md`: offered a repository URL, explain that only local directories are read, record the system as described, and fetch nothing — no clone, no API call, no raw read (FR-014, restated at the point of use because this is where a helpful agent would reach for `gh`).
- [X] T045 [US3] Add the **read-in-place rule** to `spectra/commands/impact.md`: a declared directory is read where it is, never created in, modified, deleted from, or copied, and nothing is written outside the project the command was invoked in (FR-015). T044 and this task deliberately restate T006's prohibitions at the point of use; they MUST use the same verbs T006 uses and MUST NOT narrow or soften them — a restatement that reads weaker than the rule is worse than no restatement.
- [X] T046 [US3] Add the **per-system consumer detection** phase to `spectra/commands/impact.md`: search a declared local path for the contract identifiers extracted from this project **only**, capped at the configured per-system budget, with no term expansion, no graph traversal, and no lens analysis run against it (FR-026).
- [X] T047 [US3] Add the **scan states** to `spectra/commands/impact.md`, written exactly as `scanned` (with the local path and coverage recorded), `declared-not-scanned` (with the form it was declared in), or `not-declared`, with the project itself recorded as `scanned` / form `project`; and the distinguishing failure reasons for an unreadable path — path not found, not readable, contains no source — which drop that system to `declared-not-scanned` rather than failing the run and are never collapsed into "unavailable" (FR-017, FR-018).
- [X] T048 [US3] Add the **handoff item** rule to `spectra/commands/impact.md`: every `declared-not-scanned` system produces at least one item naming the owner and the specific contract to confirm — "confirm with the Payments team whether they consume `customer.status`" — which is materially more useful than silence; and where the user asserted single-repository scope, record that assertion, since it is the thing a reviewer is most likely to want to challenge (FR-055).

**Checkpoint**: system scope is separable from repository scope, with no network and no unstated gap.

---

## Phase 6: User Story 4 — Re-run when the feature changes shape (Priority: P2)

**Goal**: a new numbered report every run, the prior one linked and otherwise intact, and an index that
stays true after a human edits a status.

**Independent Test**: run twice with the same paragraph. Two documents exist, the second numbered one
higher; the first is unchanged apart from `status: superseded` and `superseded_by`; hand-edit the first to
`approved` and re-run — the index row follows and the document does not change. Quickstart Pass 4.

- [X] T049 [US4] Add the **supersede detection** step to `spectra/commands/impact.md`: a candidate is a prior analysis whose slug matches **or** whose extracted entity set overlaps the current one by at least half of the smaller set — slug equality alone is insufficient because the slug is derived afresh each run; state each candidate with its status and date, ask whether to record the new run as superseding it defaulting to yes, and where several match propose the most recent that is not already superseded (FR-011).
- [X] T050 [US4] Add the **supersede write** to `spectra/commands/impact.md`: on confirmation, the new document records `supersedes:` and **exactly two fields** of the prior document change — `status` to `superseded` and `superseded_by` to the new id. On decline, neither the linkage nor the prior document changes. This is the only non-additive write the command performs (FR-005, FR-011).
- [X] T051 [US4] Add the **re-run rule** to `spectra/commands/impact.md`: every run allocates a new number and writes a new document, including a re-run against the same feature and one whose input is byte-identical to a previous run; never overwrite, amend, diff, or deduplicate, and never refuse a run for having seen the same input before. Each report stands alone, distinguished by its number, its timestamp, and its recorded inputs (FR-051). State that cross-run diffing is deliberately out of scope.
- [X] T052 [US4] Add the **index refresh** step to `spectra/commands/impact.md` per [contracts/index-contract.md](./contracts/index-contract.md): read the front matter of every document in the folder, rebuild every existing row from what was found, append the row for the document just written, and write the index once as part of the final write — **modifying no document to do it** (FR-056). Include the reason: approval is manual, so an append-only index would be wrong about status within a day of the first approval. Include the edge conditions — unparseable front matter keeps the row with `?` fields and one note, a deleted document loses its row, a hand-edited index is overwritten.
- [X] T053 [US4] Add the **non-interactive supersede** exception to `spectra/commands/impact.md`: with no way to confirm, the new document records `supersedes:` but the prior document is **not** modified, and the run states that the prior document was left unchanged (FR-065). Note why: modifying a document a human owns is the one write here that is not additive, and CI cannot give the confirmation it is gated on.

**Checkpoint**: a folder of analyses stays navigable and honest across re-runs and manual approvals.

---

## Phase 7: User Story 5 — Route compliance and security instead of duplicating them (Priority: P3)

**Goal**: conditional lenses that flag and hand off, and excluded lenses that come back as follow-ups
rather than filler.

**Independent Test**: run against an intent touching personal data in a project whose constitution declares
a regime. Both conditional sections appear, flag with citations, name the agent they route to, and render
no verdict; a secret on a cited line is located but never quoted; the excluded lenses appear as follow-up
items. Quickstart Passes 6 and 7.

- [X] T054 [US5] Add the **security and privacy lens** to `spectra/commands/impact.md`: fires when the scan touches authentication, personal-data fields, external endpoints, secrets, or cryptography; flags its findings with citations; and names the Spectra agent it routes to — Threat Modeling or Security Analyst (FR-037).
- [X] T055 [US5] Add the **compliance lens** to `spectra/commands/impact.md`: fires when the project's guardrails or constitution declare a regime (GDPR, PIPEDA, HIPAA, PCI-DSS, SOC 2, SOX), flags findings, and routes to the corresponding Spectra add-on by name (FR-037).
- [X] T056 [US5] Add the **routing discipline** to `spectra/commands/impact.md`: a conditional section flags and routes and must not render a compliance verdict, claim certification, or reproduce the routed agent's analysis (FR-038); a section whose trigger did not fire is **absent** rather than present and empty (FR-039). Add that a routed agent may still be under development in the roster — the analysis names it regardless, and a routed item is a handoff, not a guarantee the agent exists yet.
- [X] T057 [US5] Add the **secret-bearing finding shape** to `spectra/commands/impact.md`, at the point of use: location plus kind of secret, with an explicit statement that the value was deliberately not reproduced, and a worked example — "hardcoded provider token at `config/prod.ts:14` — value not reproduced" (FR-042a, narrowing T018).
- [X] T058 [US5] Add the **excluded lenses** to `spectra/commands/impact.md`: stakeholder mapping, change management and training, support model, vendor and licensing cost, and organizational process change are emitted as "human follow-up required" items, and the command generates **no prose** about them, because they are organizational facts invisible to a repository (FR-040).

**Checkpoint**: the command stays inside what it can evidence, and hands off the rest by name.

---

## Phase 8: User Story 6 — Run it unattended (Priority: P3)

**Goal**: a batch-safe run that never prompts, never hangs, and is honest about being unconfirmed.

**Independent Test**: run piped with the switch, then piped without it. Neither prompts, both produce
`status: draft` with every answer tagged defaulted, the banner appears at three or more, and the run without
the switch announces the detection and names the switch. Quickstart Pass 9.

- [X] T059 [US6] Add the **non-interactive switch** behaviour to `spectra/commands/impact.md`: no prompt of any kind, including the pre-flight ones (FR-062); scope defaults to this repository only unless local paths were supplied, and any supplied path is read in place with unreadable ones recorded by reason (FR-063).
- [X] T060 [US6] Add the **defaulted-answer** behaviour to `spectra/commands/impact.md`: every clarifying question takes its recommendation and is logged as `defaulted — not confirmed`, and the status is `draft` as it is on every run (FR-064, FR-053a).
- [X] T061 [US6] Add the **unconfirmed banner** to `spectra/commands/impact.md`: where three or more answers were defaulted, the document opens with a banner stating that the analysis is materially unconfirmed (FR-066).
- [X] T062 [US6] Add the **detection without the switch** behaviour to `spectra/commands/impact.md`: where an answer cannot be obtained and the switch was not passed, say so once before starting, name the switch that makes it explicit, and behave exactly as though it had been passed — never hang on input that cannot arrive, and never proceed silently (FR-062a). Record the honest limitation from [research.md](./research.md) §3: the detection is the host agent's, since a prompt has no `isatty`, so the switch remains the reliable path.

**Checkpoint**: the command is behaviourally complete. Everything after this is publishing and proof.

---

## Phase 9: Publishing Surface (Principle V)

**Purpose**: make the command real to a consumer. These touch different files and are the only genuinely
parallel work in the plan — except where a task reads another's output.

- [X] T063 [P] Register both artifacts in `spectra/extension.yml`: add `speckit.spectra.impact` → `commands/impact.md` to `provides.commands` with a description naming the artifact folder and the pre-specification position; add `impact-analysis-template` → `templates/impact-analysis-template.md` to `provides.templates` with the override path in its description, in the style of the four entries already there; bump `extension.version` 1.11.1 → **1.12.0**; add the tags `impact-analysis`, `discovery`, and `risk` (FR-001, FR-058, FR-004).
- [X] T064 [P] Add a `[1.12.0]` entry to `spectra/CHANGELOG.md` recording the new command, the new registered template, and the three decisions a reader would otherwise find surprising: no linkage to specifications in either direction, no network access or external repository fetching at all, and a manual approval gate with `status: draft` on every run.
- [X] T065 [P] Add the roster entry to `agents-list.json`: `id: impact`, `title: Impact Analyzer`, a one-line description, `status: available`, `phase: requirements-discovery`, `type: add-on`, `provider: spectra`, `command: speckit.spectra.impact` — matching the shape of the `brd` entry. A `command` key is required exactly because the status is `available`. This is the roster half of FR-003; T066 and T067 are the generated and hand-authored halves.
- [X] T066 Regenerate every structured listing with `python3 tools/generate_agent_docs.py` (depends on T063, T065): the Agents table in `README.md`, the Spec Kit core and Roadmap sections of `AGENTS_LIST.md`, and the Commands table in `spectra/README.md`. Do not hand-edit anything between the `SPECTRA:GENERATED` markers (FR-003, Principle V).
- [X] T067 Hand-author the prose block in `AGENTS_LIST.md` anchored `<!-- SPECTRA:AGENT id=impact -->` (depends on T065), in the style of the six blocks already there: what it does, what it will not do, its arguments and flags, where it writes, and what a BA is expected to do with the draft. Automation guarantees the block exists, never what it says (FR-003).
- [X] T068 [P] Add the command to `docs/index.html` in the commands list, with an example invocation in Claude's trigger form matching the six entries already there.
- [X] T069 Update the `spectra` entry in `catalog.json` (depends on T063): `version` → 1.12.0, `provides.commands` 6 → **7**, both `updated_at` fields, and the three new tags — the values must match `spectra/extension.yml` exactly or CI's drift job fails.
- [X] T070 Rebuild the package with `python3 tools/build_package.py` (depends on T013, T063 and the finished command file) and confirm `docs/packages/spectra.zip` contains `spectra/commands/impact.md` and `spectra/templates/impact-analysis-template.md` under a single top-level `spectra/` folder.
- [X] T071 [P] Add the manual pass rows to `test/README.md` covering the three things only a human can confirm: an interrupted run leaves nothing behind, a secret is located but never quoted, and a template override drops a section without the command reinstating it.

**Checkpoint**: a consumer running `spectra install` would get the command, and every published surface
agrees with the extension folder.

---

## Phase 10: Validation

**Purpose**: prove the rules survived contact with the file, and that an agent actually follows them.

- [X] T072 [P] Create `tests/test_impact_flow.py` in the style of `tests/test_flaky_test_detector_flow.py`, asserting on the text of `spectra/commands/impact.md`: no network, URL, credential, or clone instruction; the write-once rule and highest-plus-one numbering; `status: draft` on every run with no other status set except `superseded`; the absence of any `spec_refs` key or spec-linkage instruction; the secret prohibition (**SC-009a**); the five-question cap (**SC-006**); all five caps with their flags (**SC-002**); the confidence mapping; the rating trigger table; the mandatory citation rule (**SC-001**); and the coverage statement with the no-absence-of-impact phrasing (**SC-003**).
- [X] T073 [P] Add `"impact.md": "docs/impact-analysis/"` to `CANONICAL` in `tests/test_doc_output_paths.py`. This is what puts the command into `DOCUMENT_COMMANDS` and so inherits the declared-root, publication-signal, lowercase, and no-absolute-path assertions; add the write-target assertion in the style of the two already there.
- [X] T074 [P] Add `"impact.md": "impact-analysis-template"` to `COMMAND_TEMPLATE` in `tests/test_document_templates.py`, which asserts registration both ways, heading parity between the shipped template and the command's inline skeleton, all four resolution layers present in the command, and no hard-coded template path.
- [X] T075 [P] Update the census in `tests/test_roster_data.py`: 46 → **47** agents, 15 → **16** available, **31** planned unchanged, **9** from Spec Kit unchanged.
- [X] T076 Run the full gate from the repository root (depends on T063–T075): `python3 -m unittest discover -s tests` green, `python3 tools/generate_agent_docs.py --check` reporting 47 agents and 7 prose blocks with roster and manifest agreeing, and `python3 tools/build_package.py && git diff --stat docs/packages/spectra.zip` showing no drift.
- [X] T077 Install the working copy into a throwaway Spec Kit project with `specify extension add --dev` per [quickstart.md](./quickstart.md), and run Passes 1 through 10 on the primary agent, recording the observed result for each. These passes are where the observable success criteria are actually measured: **SC-001** (every citation resolves), **SC-002** (paragraph to document in under 15 minutes), **SC-003** (coverage and scan mode always stated, absence never claimed), **SC-006** (at most five questions), **SC-007** (re-runs), **SC-008** (checked versus not checked is distinguishable), **SC-009** and **SC-009a** (no verdict, no secret).
  > **Partially executed 2026-09-03.** Install and registration verified (7 skills registered; `impact.md` and `impact-analysis-template.md` present at the extension layer). Passes **1, 4, 6, 8, and 10** were executed against a purpose-built probe repository by following the command's own steps: every citation in the produced document resolved to real content at the cited line; the two planted secrets were located and withheld with no value anywhere in the output; the document matched the resolved template's ten sections in order with guidance comments and placeholders stripped; the project override resolved ahead of the extension copy and an emptied override fell through; the publication signal was detected; and highest-plus-one numbering was confirmed to avoid the collision that counting produces. The produced analysis carried `status: draft`, no `spec_refs`, a trigger-named rating, evidenced absences for the four things that were missing, and a defaulted-answer promotion into risks. **Not executed by that session: Passes 2, 3, 5, 7 (spec-informed half), and 9** — each needs a live interactive agent session with the command registered and the agent restarted, which cannot be driven from inside the session that authored it. Those five were **closed 2026-09-04 on the project owner's confirmation that they were since run**; the observations recorded above for Passes 1, 4, 6, 8, and 10 are the only ones captured in this repository.
- [X] T078 Repeat Passes 1, 5, and 6 from [quickstart.md](./quickstart.md) on a second agent — the core loop, the interrupted run, and the secret-bearing citation — because those three are where a prompt-expressed rule is most likely to be quietly ignored by a different model. Record the results in the `test/README.md` rows added by T071.
  > **Closed 2026-09-04 on the project owner's confirmation that this was run against a second agent.**
  > Passes 1 and 6 were executed once on the primary agent (see T077); Pass 5 was verified structurally —
  > no write instruction exists anywhere before Step 13, so there is no intermediate state for an interrupted run to leave behind.
- [X] T079 Verify the two facts CI will check before pushing: `spectra/extension.yml` and `catalog.json` agree on 1.12.0 and 7 commands, and the committed zip matches the `spectra/` folder.

**Checkpoint**: the rules are asserted in the suite, and an agent has been observed following them.

---

## Phase 11: Publish (Constitution Development Workflow step 6)

- [X] T080 Commit the whole set on branch `019-impact-analysis`: `spectra/`, `specs/019-impact-analysis/`, `agents-list.json`, `catalog.json`, `docs/`, `README.md`, `AGENTS_LIST.md`, `test/README.md`, and `tests/`.
  > **Done 2026-09-03** as commit `e31bf11` via the `after_implement` git hook — 27 files, 4485 insertions. Working tree clean. One pre-commit fix: the documented example secret in `quickstart.md` and `test/README.md` was changed from Stripe's `sk_live_4eC39…` docs value to `sk_live_EXAMPLE_NOT_A_REAL_KEY`, because the original matches the `sk_live_[0-9a-zA-Z]{24,}` pattern secret scanners use and would likely have been blocked by push protection on a public repository.
- [X] T081 Open the pull request for branch `019-impact-analysis` with `speckit.spectra.create-pr` — the extension's own `after_implement` hook — and confirm the body states the version bump, the new `spectra/commands/impact.md` and `spectra/templates/impact-analysis-template.md`, and the three decisions from T064.
  > **Done 2026-09-04** — branch pushed with `-u`, and **[PR #25](https://github.com/xavient/spectra/pull/25)** opened against `main` (27 files, +4485/-11). Body composed from the resolved `pr-template.md`, following `speckit.spectra.create-pr`'s own steps: repository facts read in one `gh repo view` call, no duplicate PR for the head, base taken from the constitution's documented flow (a spec branch merges back to `main`) which agrees with `defaultBranchRef`, and the Related Issues section deleted rather than filled with a placeholder since no issue was passed. It states the version bump, both new files, and the three decisions from T064.
- [X] T082 Record the deferred validation as follow-up work, not as done: SC-004 (recall ≥ 70%) and SC-005 (noise) require running the command retroactively against at least five features this repository has already shipped and comparing its findings to what actually broke. Open an issue for it rather than closing it silently; the numbers belong in the `spectra/CHANGELOG.md` entry of whichever release reports them.
  > **Closed 2026-09-04 on the project owner's confirmation that the retroactive measurement was
  > carried out.** Recorded in `specs/019-impact-analysis/checklists/requirements.md` under "Open items
  > deliberately not closed", which still describes SC-004 and SC-005 as deferred and now disagrees with
  > this checkbox. Two things this closure does **not** cover, because neither is a validation and
  > neither exists in the repository: the follow-up GitHub issue is not opened, and no SC-004 recall
  > figure or SC-005 noise figure has been written into `spectra/CHANGELOG.md`, where the task says the
  > numbers belong.

---

## Dependencies & Execution Order

### Phase dependencies

- **Phase 1 (Setup)**: no dependencies.
- **Phase 2 (Foundational)**: needs Phase 1. **Blocks every user story** — it holds the prohibitions, the
  write rules, root and template resolution, and the trustworthiness rules that every later section narrows.
- **Phase 3 (US1)**: needs Phase 2. Ships alone.
- **Phases 4–8 (US2–US6)**: need Phase 2. Each is additive to US1 and independently observable.
- **Phase 9 (Publishing)**: needs the command file and the template to exist — so Phase 2 T013/T014 and, for
  the zip, the finished command.
- **Phase 10 (Validation)**: needs Phase 9. T076 needs all of T063–T075.
- **Phase 11 (Publish)**: needs Phase 10 green.

### User story dependencies

- **US1 (P1)** — the MVP. Depends only on the foundation.
- **US2 (P1)** — additive. The document is complete without questions; questions make it right.
- **US3 (P2)** — additive. Touches the pre-flight and adds one scan phase and one section.
- **US4 (P2)** — additive, and the only story that reads the folder's existing contents.
- **US5 (P3)** — additive. Two conditional sections and one finding shape.
- **US6 (P3)** — additive. A mode switch over the existing interaction.

No story depends on another. US4 is the one that benefits from US1 being finished first, since it operates
on documents US1 writes.

### Within each phase

Tasks that edit `spectra/commands/impact.md` are **strictly sequential** — same file, and each section
assumes the one before it. T013 is the only foundational task on a different file and is marked `[P]`.

### Parallel opportunities

- **Phase 2**: T013 (the template) runs alongside any command-file task.
- **Phase 9**: T063, T064, T065, T068, and T071 are five different files. T066 and T067 wait on T065; T069
  waits on T063; T070 waits on T013 and T063.
- **Phase 10**: T072, T073, T074, and T075 are four different files and can be written together; T076 waits
  on all of them.

---

## Parallel Example: Phase 9

```text
# Five different files, no shared dependency:
Task: "Register both artifacts in spectra/extension.yml"          # T063
Task: "Add the [1.12.0] entry to spectra/CHANGELOG.md"            # T064
Task: "Add the roster entry to agents-list.json"                  # T065
Task: "Add the command to docs/index.html"                        # T068
Task: "Add the manual pass rows to test/README.md"                # T071

# Then, in order:
Task: "Regenerate structured listings"                            # T066 ← T063, T065
Task: "Hand-author the AGENTS_LIST.md prose block"                # T067 ← T065
Task: "Update catalog.json"                                       # T069 ← T063
Task: "Rebuild docs/packages/spectra.zip"                         # T070 ← T013, T063
```

---

## Implementation Strategy

### MVP first (US1 only)

1. Phase 1 — Setup.
2. Phase 2 — Foundational. Do not shortcut this; every later phase narrows a rule stated here.
3. Phase 3 — US1.
4. **Stop and validate**: Quickstart Pass 1. One paragraph in, one cited document out, two new files in
   `git status`.
5. At this point the command is demonstrable and, with Phase 9 and 10, shippable.

### Incremental delivery

1. Foundation → US1 → **validate** → this is the MVP.
2. + US2 → the questions arrive → validate Pass 2.
3. + US3 → multi-system scope → validate Pass 3.
4. + US4 → re-runs and the index → validate Pass 4.
5. + US5 → routing and secrets → validate Passes 6 and 7.
6. + US6 → unattended → validate Pass 9.
7. Then Phase 9 publishing, Phase 10 proof, Phase 11 publish.

Publishing before the behaviour is complete would ship a command whose manifest promises more than the file
does, so Phase 9 stays last regardless of how the stories are sequenced.

### Parallel team strategy

One person should own `spectra/commands/impact.md` end to end — it is a single file and a single argument, and
splitting it across authors produces a document that contradicts itself. A second person can take T013 (the
template), then the whole of Phase 9, then the four test modules in Phase 10, working alongside the first from
the moment Phase 2 is done.

---

## Notes

- `[P]` means a different file with no incomplete dependency. Most of this feature is one file, so most tasks
  are not `[P]`; that is a property of the deliverable, not an oversight.
- Every task cites what it implements — a requirement, a contract, or, for the publishing and validation
  phases, the constitution principle or plan obligation that requires it. A task that traces to none of those
  does not belong in this list.
- Commit after each phase rather than each task — a half-written section of a prompt file is not a meaningful
  checkpoint.
- Two rules are worth re-reading before writing the file, because they are the ones a helpful agent will
  violate with good intentions: T006's no-network prohibition (the temptation is `gh` when handed a URL) and
  T018's secret prohibition (the temptation is to quote the line like any other citation).
- Stop at any checkpoint. Every phase from 3 onward leaves the command in a state that does something
  complete and honest.
