# Feature Specification: Feature Impact Analysis

**Feature Branch**: `019-impact-analysis`

**Created**: 2026-09-03

**Status**: Draft

**Input**: Command design spec `speckit.spectra.impact` (rev 2, draft for review) — a Requirements &
Discovery add-on agent that produces a codebase-grounded feature impact analysis a Business Analyst
takes to stakeholders for a go / no-go decision **before** any specification work begins. The design
spec settles fourteen sections' worth of decisions: a nine-phase execution flow (pre-flight scope →
structural map → term expansion → seed search → bounded graph expansion → dark-matter and
string-literal sweep → consumer detection in any other system the user can point at locally → at most
five clarifying questions → five core lenses plus two conditional ones → a numbered document under
`docs/impact-analysis/`), five
hard rules that make the output trustworthy (absence of evidence is never absence of impact, no finding
without a citation, external contract changes always escalate, coverage is stated, degrade loudly),
three confidence levels, a defined impact-rating trigger table, and a non-interactive mode for CI.
Two of the design spec's decisions are reversed here at the user's direction and recorded under
Clarifications: the forward link to `specify` is dropped in full, and external repository access —
shallow clone, API read, raw URL read — is replaced by local paths, documents, and free-text
descriptions, leaving the command with no network access at all.

## Clarifications

### Session 2026-09-03

The design spec arrived with §12 "Resolved decisions" already settled and §13 recording known
limitations. Those are carried into this spec as decisions rather than as open questions. What follows
records the decisions this spec adds — points where the design spec is silent, or where it conflicts
with Spectra's own constitution and the constitution wins.

- Q: The design spec writes output to `docs/impact-analysis/`. Constitution Principle VII makes the
  artifact root **declarable** (`Artifact root: documents/`) with `docs/` only the default, and requires
  a publication check before defaulting into `docs/`. Which applies? → A: **Principle VII applies.**
  Output goes to `<artifact-root>/impact-analysis/`, resolving a declared root first, checking for the
  publication signal (`mkdocs.yml`, `docusaurus.config.*`, `docs/_config.yml`, `docs/.nojekyll`,
  `docs/index.html`, `docs/conf.py`, or a Pages configuration pointing at `docs`) before defaulting, and
  taking the non-publishing option when the choice cannot be obtained. An impact analysis names internal
  systems, owning teams, and unmitigated risks; publishing one to the web is the more damaging default.
  `docs/impact-analysis/` remains what the majority of projects will see.
- Q: The design spec carries the document structure as an inline fenced template. Does Principle VIII
  apply to it? → A: **Yes, in full.** The analysis is a durable Markdown deliverable a human reads, so
  its structure ships as a registered asset — `spectra/templates/impact-analysis-template.md`, declared
  in `provides.templates` — resolved through Spec Kit's four-layer stack with the command's inline
  skeleton as the last resort. The command reports the resolved path and honours the resolved template
  rather than repairing it. This is the `adr`/`brd` divergence the principle exists to prevent; there is
  no reason to re-create it on the third document agent.
- Q: Is an auto-maintained index file compatible with Principle VII's "exactly one artifact type per
  folder"? → A: **Yes.** The index is navigation, not an artifact — it carries no sequence number and
  describes the folder's contents. It lives at `<artifact-root>/impact-analysis/README.md`.
- Q: The design spec's Phase 3–6 name ripgrep. Can the command depend on it? → A: **No.** Principle III
  forbids hard-coding one environment's tooling and the published package ships no scripts or binaries,
  so the command states the *search* it needs and uses whatever full-text search the host agent
  provides. Where the agent has no repository-wide text search, the run says so and reports the reduced
  coverage under hard rule R5 rather than silently narrowing to the import graph.
- Q: The caps in §10 are marked "configurable" with no mechanism. What is it? → A: **Flags in the same
  invocation**, parsed out of the generic arguments string (`--seed-cap`, `--hops`, `--max-files`,
  `--identifier-cap`, `--per-system-cap`). Any non-default value is stated in Sources consulted, so a reader
  can tell a narrow scan from a narrow codebase. The five-question cap stays fixed, as the design spec
  requires.
- Q: In non-interactive mode, does supersede detection still rewrite the prior analysis's `status` to
  `superseded`? → A: **No.** The new document records `supersedes:` and the run states that the prior
  document was left untouched. Modifying a document a human owns is the one write in this command that
  is not additive, and the design spec gates it on an explicit confirmation that CI cannot give.
- Q: The design spec's Phase 0c offers four access methods per external repository — shallow clone (its
  recommendation), API read with a token, raw URL read, or skip. Does that ship? → A: **No. External
  repository access is dropped entirely.** The command asks one question — is this the only repository the
  system depends on — and where the answer is no, the user describes each other system in whichever form
  they have: free text, a document, or a path to a local copy already on the machine. A local path is read
  in place; nothing is cloned, downloaded, or copied, no URL is accepted, and no credential or token is
  ever requested. This removes the whole access-method matrix, the per-repository method question, the
  reuse prompt, the four network failure modes, and the question of where a clone lives and when it is
  deleted. It also keeps the command inside the promise Spectra makes about itself — that it opens no
  channel the host agent does not already use — since a run now makes no network request at all. The cost
  is that a system with no local checkout is described rather than searched, which is the
  `declared-not-scanned` state the design already handles and already converts into a targeted handoff
  item.
- Q: How does an analysis get approved, and does the command track that? → A: **The gate is manual and the
  command stays out of it.** Every run writes `status: draft`. The BA takes the draft to stakeholders, and
  comes back and records approval or rejection by hand. The command never sets, prompts for, or infers any
  status other than the `draft` it writes and the `superseded` it marks on a prior analysis when the user
  confirms (FR-053a). One consequence had to be settled: the index copies `status`, so a hand-edited
  approval would leave it stale within a day. Each run therefore refreshes the existing index rows from the
  documents' front matter before appending its own (FR-056) — self-healing, and it modifies no document.
- Q: Does the scan always have to reconstruct the system from source? → A: **No — a spec'd project is
  scanned differently.** Where the project carries specifications and a constitution, those are the primary
  orientation: entity vocabulary, declared boundaries, prior decisions, stated constraints. Code is then
  read to confirm and extend them. Where they are absent the command reads code alone to build the
  understanding, which is the heavier path, and says so. The output states which mode ran, because a reader
  must be able to tell an analysis grounded in declared intent from one reconstructed from source
  (FR-010a, FR-010b).

  Two guards come with it. A specification documents *intent* and drifts from code, so a finding whose only
  evidence is a document cannot be `confirmed`, blast-radius claims still require code citations, and a
  document that disagrees with the code is itself a finding (FR-010c). And reading a spec creates no
  relationship to it: a document may be cited as the provenance of a finding — that is evidence — but the
  analysis records no informing, related, or superseded work (FR-010d). FR-054 is narrowed accordingly: it
  now forbids creating, linking to, modifying, or depending on specifications, rather than reading them,
  which Principle IV requires anyway.
- Q: How are the file's number and name chosen? → A: **`NNN-<name>.md`, with the number one greater than
  the highest already in the folder and the name derived per run from the intent and any supplied
  documents.** Highest-plus-one rather than a count, because counting collides as soon as an analysis is
  deleted or archived — with `001` and `003` on file, count-plus-one is `003`. The name is inferred from
  the hints in the prompt and the attachments, which means it is **not stable across runs**: the same
  feature described differently produces a different name. FR-053 therefore no longer claims slug
  stability, and relating two analyses rests on FR-011's confirmed detection — slug match *or* an entity
  overlap of at least half the smaller set — with the user confirming, and the most recent unsuperseded
  candidate proposed where several match.
- Q: Can a finding ever be stated without a `path:line` citation? → A: **Only for evidenced absence.** A
  High rating can be triggered by "no viable rollback path identified", and absence has no line to cite —
  so as written, the most consequential trigger could not legally appear as a finding. Such a finding cites
  what was searched and where, in the same form FR-048 already uses for terms with no hits (FR-042).
- Q: What happens on a re-run whose input is identical to an earlier one? → A: **A new report, always.**
  Every run allocates a new number and writes a new document; nothing is overwritten, amended, diffed, or
  deduplicated, and no run is refused for having been seen before (FR-051). What keeps that navigable is
  that each report records its own inputs — the feature intent verbatim, and every attachment by name with
  whether it was read — alongside a timestamp carrying the time of day, so two reports on the same feature
  on the same date are told apart by what they were asked and when (FR-052, FR-052a). This is the simple
  behaviour on purpose: cross-run diffing was left on the design spec's "possible later additions" list.
- Q: Who is `author:` in the front matter? → A: **The committing identity where one is discoverable**
  (`git config user.name`), otherwise the field is written empty rather than invented. A wrong name on a
  document that goes to a stakeholder gate is worse than a blank one.
- Q: Does the command create the spec, the branch, or a commit as a follow-on? → A: **No.** It writes
  the analysis, the index row, and — on confirmation — one front-matter field in the superseded
  document. Nothing else. The gate after it is organizational, and `specify` remains the user's call.
- Q: The design spec links an analysis forward to a spec by slug (`spec_refs`, and a soft lookup inside
  `speckit.specify` that prints a notice on a match). Does that ship? → A: **No — there is no linkage in
  either direction.** Impact analysis and specification are two independent processes. The BA produces
  the analysis and stops; `specify` starts separately and knows nothing about it. A team that wants the
  analysis to inform a spec passes the document as an input to `specify`, which is possible today and
  requires nothing from this command. Dropping the link also removes the only part of the design that
  reached outside the Spectra extension: `speckit.specify` is Spec Kit's own file, and a local edit to it
  is discarded on the next Spec Kit update. `feature_slug` is retained as the document's own descriptive
  identifier and as one signal in supersede detection — see the numbering decision below, which settles
  that it is derived per run and therefore not stable.
- Q: What does the command do when the feature intent's entities produce zero hits anywhere? → A:
  **Reports the searched terms as a finding.** "Searched for and not found" is the evidence that
  distinguishes a genuinely additive feature from a failed term expansion, and it is the line a reviewer
  uses to catch the second case.

- Q: How should the contract-identifier sweep be bounded, given that it searches every identifier it
  extracts across the whole project with no limit on how many identifiers there are? → A: **A ranked cap.**
  Identifiers are ordered by boundary class — table and column names, endpoint paths, event and topic names
  first; configuration keys, feature-flag keys, and environment variable names last — and the top N are
  swept, default 50, configurable like the other caps, with the cap and the skipped remainder disclosed
  (FR-024, FR-028). This was the one phase whose cost was the product of two numbers while every other
  phase capped one, and it is the most likely place a run exceeds SC-002's 15 minutes. Ranking is what makes
  the cap safe rather than arbitrary: it is the same move FR-021 already makes one level up, where files are
  weighted by role, so the identifiers that fall off the end are the ones least likely to name a contract a
  consumer depends on.

- Q: When a citation points at a line that contains a secret — a hardcoded credential, a private key, a
  token — what should the analysis put in the document? → A: **Cite the location, never the value.** The
  finding names the kind of secret and where it is ("hardcoded token at `config/prod.ts:14`") and states
  that the value was deliberately not reproduced (FR-042a). The citation stays actionable for whoever has to
  fix it, and the secret is never copied into a second file — one that is committed, and on a project that
  publishes `docs/` may be served. This composes with FR-049's publication check rather than depending on
  it: if the value is never quoted, whether the location is safe stops mattering.

- Q: How are supporting documents handed to the command, and which formats must it read? → A: **File paths
  in the invocation, reading `.md`, `.txt`, `.pdf`, and `.docx`** — the same set `speckit.spectra.brd`
  already accepts, so a BA who uses both agents does the same thing in both. An unreadable, missing, or
  unsupported file is recorded by name with its reason and the run continues, which is FR-018's
  reason-per-failure pattern applied to inputs rather than to declared systems (FR-008). One thing the
  question exposed and that follows by default rather than by choice: the intent paragraph is authoritative
  for *what is being asked* and documents are evidence about it, so a document that contradicts the intent is
  surfaced rather than silently preferred either way — the same treatment FR-010c gives a specification that
  disagrees with the code (FR-008a).

- Q: If a run stops partway through — interrupted, or failed — what should exist on disk afterwards? → A:
  **Nothing.** The document and its index row are written once as the run's final act, and the sequence number
  is resolved at that moment, so an interrupted run leaves the folder exactly as it found it: no partial
  document, no incomplete marker, no number consumed (FR-051a). This needs no cleanup logic and no recovery
  path because everything before the write is reading and asking. It also matters more than it looks: numbers
  come from the highest file present, so a half-written report would both mislead a reader and push the next
  run's number off a document nobody approved.

- Q: What should the command do when it needs to ask something but no one can answer — a piped session where
  the switch was not passed? → A: **Detect it and proceed as if the switch were passed, saying so once.** No
  prompts, recommendations taken, every answer tagged defaulted, banner at three or more — and one line up
  front stating that it detected a non-interactive session and naming the switch that makes it explicit
  (FR-062a). This is what the `spectra` CLI already does in the same situation, so the project has one answer
  to "no terminal" rather than two. It neither hangs on input that cannot arrive nor proceeds silently: the
  tags and the banner make the result honest, and the announcement means nobody discovers the mode from the
  document afterwards.

No questions remain open. Every marker raised during validation is settled above.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ground the go / no-go in the code (Priority: P1)

A Business Analyst types one paragraph describing what should be true after a feature ships, in a
repository they have never read. Where the project is spec'd, the agent orients itself on the
specifications and the constitution and reads code to confirm and extend them; where it is not, it builds
the same understanding from source alone, and says which of the two it did. Either way it finds what the
change would touch and writes a numbered impact analysis whose every finding cites a file and line —
followed by a plain statement of how much of the repository it actually read and what it could not see.

**Why this priority**: this is the MVP and the whole differentiator. A BA cannot read a repository, so
conventional impact analysis is a memory-and-interview exercise that systematically misses coupling.
Every other story is a refinement of this one; none is worth building if the cited findings are not
credible.

**Independent Test**: run the command with a one-paragraph intent in a repository with known coupling,
then verify every Findings item resolves to real content at the cited `file:line`, that the coverage
statement names files-read out of files-present, and that no statement in the document claims absence of
impact.

**Acceptance Scenarios**:

1. **Given** a feature intent and no attachments, **When** the agent runs, **Then** it produces a
   document containing a restated change statement, an impact rating with the trigger that produced it,
   the five core lenses, and a Sources consulted section.
2. **Given** any item in the Findings section, **When** its citation is opened, **Then** the cited path
   exists and the cited line contains the referenced code.
3. **Given** an inference the agent could not cite, **When** the document is read, **Then** that
   inference appears under Assumptions and unknowns and **not** under Findings.
4. **Given** a finding that something is missing — no rollback path, no backfill tooling, no covering
   test — **When** it is read, **Then** it cites what was searched and where, rather than being demoted
   out of Findings.
5. **Given** the scan found no consumers of a touched contract, **When** the document states that,
   **Then** it is phrased as no consumers found in what was scanned, and the document nowhere asserts
   that there is no downstream impact.
6. **Given** the scan completed, **When** Sources consulted is read, **Then** it states files read out
   of files present, the selection method, and the terms that were searched for and not found.
7. **Given** the project carries specifications and a constitution, **When** the document is read,
   **Then** it states that it oriented on them, and every blast-radius claim still cites code rather than
   a specification.
8. **Given** the project carries no specifications, **When** the document is read, **Then** it states
   that the understanding was reconstructed from source alone.
9. **Given** a specification and the code disagree, **When** the document is written, **Then** the
   disagreement appears as a finding.
10. **Given** any run, **When** the front matter is read, **Then** `status` is `draft`.
11. **Given** the run finished, **When** the working tree is inspected, **Then** the only changes are the
    new analysis file and the index row.

---

### User Story 2 - Close the gaps the code cannot answer (Priority: P1)

Before writing, the agent asks at most five questions — each generated from something the scan found
genuinely ambiguous, each with three or four substantive options, an "Other" escape, and a stated
recommendation that cites a scan finding. Pressing enter accepts the recommendation, and the document
records that the answer was defaulted rather than confirmed.

**Why this priority**: there is no `spec.md` to read at this point in the lifecycle. The intent
paragraph plus these questions are the entire requirements signal, so question quality carries
disproportionate weight — and a question the user cannot skip is a command that stalls in CI and
annoys everyone else.

**Independent Test**: run against an intent that leaves scope and data lifecycle open, confirm no more
than five questions arrive one at a time, confirm each carries options plus a reasoned recommendation,
skip one, and verify the document records it as `defaulted — not confirmed` and promotes it into risks.

**Acceptance Scenarios**:

1. **Given** the scan is complete, **When** questions are asked, **Then** there are at most five, they
   arrive one at a time, and each waits for an answer before the next is asked.
2. **Given** a question is presented, **When** it is read, **Then** it offers three or four substantive
   options, "Other" as the final numbered option accepting a free-text sentence, and a recommendation
   with its reasoning.
3. **Given** the answer to a question is discoverable in the repository, **When** questions are
   selected, **Then** that question is not asked.
4. **Given** the user presses enter, **When** the document is written, **Then** the recommended answer
   is used, the Clarifications table records the source as `defaulted`, and the run does not block.
5. **Given** a defaulted answer in scope boundary, data lifecycle, or contract compatibility, **When**
   the document is written, **Then** it also appears in the risks section.
6. **Given** fewer than five things are ambiguous, **When** questions are asked, **Then** fewer than
   five are asked.

---

### User Story 3 - Widen the scope past this repository (Priority: P2)

The agent asks, before scanning, whether this repository is the only one the system depends on. If it is
not, the BA describes each other system in whichever form they actually have: a sentence of free text, a
document, or — if a copy happens to be checked out on the machine — a local directory path. A local path
gets a narrow consumer-detection pass; text and documents still produce targeted handoff items. Every
system's scan state lands in the document.

**Why this priority**: repository scope is not system scope, and under-declaring is the most common
cause of a missed impact. A system described in one sentence still converts silence into "confirm with
the Payments team whether they consume `customer.status`", which is the difference between a gap and a
surprise.

**Independent Test**: answer no to the scope question, declare one system by local path and one by a
sentence of text, then confirm the local one is searched for contract identifiers only, the described one
generates a team-addressed handoff item, and both appear in front matter with the right scan state.

**Acceptance Scenarios**:

1. **Given** the pre-flight scope question, **When** it is presented, **Then** it asks whether this
   repository is the only one the system depends on, is asked before any scanning begins, and recommends
   answering no when the user is unsure.
2. **Given** the user answers no, **When** each other system is declared, **Then** the agent accepts free
   text, a document, or a path to a local directory, and requires none of them in particular.
3. **Given** a declared local path, **When** the scan runs, **Then** it searches only for the contract
   identifiers extracted from the primary repository, reads at most the per-system cap, and runs no term
   expansion, graph traversal, or lens analysis.
4. **Given** a declared local path, **When** the run completes, **Then** nothing in that directory was
   created, modified, or deleted, and no copy of it was made.
5. **Given** a system declared as text or a document, **When** the document is written, **Then** it
   carries state `declared-not-scanned` with whatever owner was given, and produces at least one handoff
   item naming the owner and the contract to confirm.
6. **Given** a declared path cannot be read, **When** the document is written, **Then** it records a
   distinguishing reason — path not found, not readable, contains no source — rather than "unavailable",
   and the system drops to `declared-not-scanned`.
7. **Given** any run, **When** it completes, **Then** the command made no network request and asked for
   no credential, token, or login.
8. **Given** these pre-flight questions were asked, **When** the clarifying questions begin, **Then**
   the five-question budget is untouched by them.

---

### User Story 4 - Re-run when the feature changes shape (Priority: P2)

Weeks later the feature is reshaped and the BA runs the command again. The agent recognizes the prior
analysis, offers to record the new one as superseding it, allocates a fresh number, and appends a row to
the folder index so that the current analysis is findable six months later.

**Why this priority**: an impact analysis is a decision input with a shelf life. Without supersede
linkage a reviewer cannot tell which of two documents the stakeholders actually approved, and silently
overwriting the first destroys the record of what was decided.

**Independent Test**: run twice against the same feature, confirm two numbered files exist, that the
second records `supersedes` and the first `superseded_by` / `status: superseded`, that the second's number
is one greater than the first's, and that the index lists both with the relationship.

**Acceptance Scenarios**:

1. **Given** a prior analysis whose slug matches or whose entity set overlaps the current one by at least
   half of the smaller set, **When** the run starts, **Then** the agent names it with its status and date
   and asks to confirm the supersede linkage, defaulting to yes.
2. **Given** confirmation, **When** the documents are written, **Then** the new one records
   `supersedes:` the prior id and the prior one is updated to `superseded`.
3. **Given** the user declines, **When** the documents are written, **Then** neither the linkage nor the
   prior document's status changes.
4. **Given** several candidates match, **When** the agent proposes one, **Then** it is the most recent
   candidate that is not already superseded.
5. **Given** any run, **When** the file is named, **Then** its number is one greater than the highest
   already in the folder rather than a count of the files there, and no existing analysis is overwritten.
6. **Given** two analyses of the same feature, **When** they are compared, **Then** the relationship is
   the confirmed `supersedes` / `superseded_by` pair, never a shared number or an assumed slug match, and
   neither references a specification.
7. **Given** a re-run with the same intent and the same attachments, **When** it completes, **Then** a new
   report exists, the earlier one is byte-for-byte unchanged apart from any confirmed supersede fields, and
   the run neither diffed nor refused.
8. **Given** any report, **When** its inputs section is read, **Then** it carries the feature intent
   verbatim, every attachment by name with whether it was read, and a timestamp including the time of day.
9. **Given** a status a human edited by hand, **When** the next run writes the index, **Then** that
   status appears in the index row and the document itself is not modified.
10. **Given** any run, **When** the index is read, **Then** it has one row per analysis carrying id,
    title, status, impact rating, date, and supersede relationships.

---

### User Story 5 - Route compliance and security instead of duplicating them (Priority: P3)

The scan touches an authentication path and the project's guardrails declare PIPEDA. The document flags
what it found, names the Spectra agent that owns the question, and stops — no verdict, no invented
regulatory prose. Lenses that a repository simply cannot answer — stakeholders, training, support model,
vendor cost — come back as explicit human follow-up items rather than filler.

**Why this priority**: it keeps the command thin and the roster coherent, and it is what stops the
output from reading as a compliance opinion it is not qualified to give. It is P3 only because the core
five lenses are what the gate actually turns on.

**Independent Test**: run against an intent touching personal data in a project whose constitution
declares a regime, and confirm the document flags the finding, names the routed agent, renders no
verdict, and lists the excluded lenses as follow-up items.

**Acceptance Scenarios**:

1. **Given** the scan touches authentication, personal-data fields, external endpoints, secrets, or
   cryptography, **When** the document is written, **Then** the security and privacy section appears,
   flags the findings with citations, and names the agent it routes to.
2. **Given** a cited line contains a secret, **When** the finding is read, **Then** it gives the location
   and the kind of secret, states that the value was not reproduced, and the value appears nowhere in the
   document or the session.
3. **Given** the guardrails or constitution declare a compliance regime, **When** the document is
   written, **Then** the compliance section appears and routes to the corresponding Spectra add-on.
4. **Given** either conditional lens fired, **When** its section is read, **Then** it contains no
   compliance verdict, certification claim, or reproduction of the routed agent's analysis.
5. **Given** neither trigger fired, **When** the document is written, **Then** the corresponding section
   is absent rather than present and empty.
6. **Given** an excluded lens is relevant, **When** the document is written, **Then** it appears as a
   human-follow-up item and the agent generates no prose about it.

---

### User Story 6 - Run it unattended (Priority: P3)

A pipeline runs the command with `--non-interactive` against a batch of candidate features. Nothing
prompts, every question takes its recommendation, each default is recorded as unconfirmed, the status is
draft as it always is, and a run with three or more defaults carries a banner saying the analysis is
materially unconfirmed. A session that simply cannot accept an answer gets the same treatment, announced
up front, rather than hanging on a prompt nobody will see.

**Why this priority**: it makes the command usable for triage at volume, and the honesty machinery — the
tagging and the banner — is what keeps a batch-produced draft from being mistaken for a reviewed one.
Last because the primary user is a human BA in a terminal.

**Independent Test**: run with `--non-interactive` in a repository with a prior matching analysis and no
terminal, and confirm nothing prompts, the status is `draft`, every question is logged as defaulted, the
prior document is untouched, and the banner appears when three or more were defaulted.

**Acceptance Scenarios**:

1. **Given** `--non-interactive`, **When** the run executes, **Then** no prompt of any kind is emitted,
   including the pre-flight ones.
2. **Given** `--non-interactive` with no declared paths, **When** scope is resolved, **Then** it is
   treated as this repository only and the document says so.
3. **Given** `--non-interactive` with declared local paths, **When** each is read, **Then** it is read in
   place and any unreadable one is recorded with its reason.
4. **Given** `--non-interactive`, **When** the document is written, **Then** `status` is `draft` and
   every clarifying answer is recorded as `defaulted — not confirmed`.
5. **Given** three or more answers were defaulted, **When** the document is written, **Then** a banner at
   the top states that the analysis is materially unconfirmed.
6. **Given** a prior matching analysis exists, **When** the run completes, **Then** the new document
   records `supersedes:` and the prior document's `status` is unchanged, and the run states that.
7. **Given** a session that cannot accept an answer and no switch was passed, **When** the run starts,
   **Then** it states once that it detected this and names the switch, then behaves exactly as though the
   switch had been passed.
8. **Given** that same session, **When** the run executes, **Then** it never waits on a prompt and never
   proceeds without having said what it was doing.

---

### Edge Cases

- **Empty argument.** No feature intent supplied: the command states what to provide and stops without
  scanning.
- **Intent with zero hits.** Term expansion produces no matches anywhere: the document reports the
  searched terms under "searched for and not found", and does not conclude the feature is additive.
- **Repository with no source.** Documentation-only or empty repository: the structural map reports what
  exists, findings are empty, and the coverage statement carries the whole explanation.
- **Every cap hit.** Seed set, hop budget, file budget, and identifier sweep all saturated: each is named in
  Sources consulted with the cap that bound it and what went unread or unswept, and nothing is truncated
  silently.
- **No repository-wide text search available.** The command states the limitation, restricts itself to
  what it can traverse, and reports the reduced coverage.
- **A declared path cannot be read.** Path does not exist, is not readable, or holds no source: each
  recorded as its own reason, and the system drops to `declared-not-scanned` without failing the run.
- **A declared path is the project itself**, or a subdirectory of it: recognized and reported rather than
  scanned twice.
- **The user offers a repository URL anyway.** The command explains it reads only local directories, and
  records the system as described rather than fetching anything.
- **A cited line contains a secret.** The finding gives the location and the kind of secret, states that the
  value was not reproduced, and the value appears nowhere in the document or the session.
- **An attachment cannot be read** — missing path, unsupported type, unreadable file: recorded by name with
  that reason in the inputs section, and the run continues on what it has.
- **An attachment contradicts the intent paragraph.** The contradiction is surfaced; the paragraph governs
  what is being asked.
- **The run is interrupted.** Ctrl-C, a closed terminal, or a failure at any point before the final write:
  the impact-analysis folder is unchanged, no number is consumed, and the next run is unaffected.
- **No terminal and no switch.** A piped or otherwise non-interactive session is detected, announced once
  with the switch that makes it explicit, and run as though the switch had been passed.
- **Prior analysis exists but was rejected.** The match is still surfaced with its status, and supersede
  linkage is still offered.
- **A human set a status to `approved`, then a re-run happens.** The re-run reads that status, reflects it
  in the index, and does not change it. Only a confirmed supersede writes to a prior document.
- **The folder has a gap in its numbering** — `001` and `003`, with `002` deleted. The next analysis is
  `004`, because the number is one greater than the highest present rather than a count.
- **The project's specifications are stale.** Where a specification and the code disagree, the
  disagreement is reported as a finding rather than resolved silently in either direction.
- **The project has specifications but no constitution**, or the reverse. Whichever exists is used for
  orientation, and the output states what it had.
- **Publication signal present with no declared root.** The command surfaces the signal, recommends
  `documents/`, and where the choice cannot be obtained takes the non-publishing option.
- **Declared artifact root is unusable** (absolute, or escaping the project): the command says so and
  falls back to the default rather than guessing.
- **The user answers "Other" to every question.** Free-text answers are recorded verbatim in the
  Clarifications table with source `user`.
- **A prior analysis folder exists from a superseded default root.** Read for numbering continuity,
  reported once, and left in place.
- **Two runs in one day for the same feature.** Both get their own number and their own timestamp; the
  second supersedes the first.
- **A re-run with identical input.** Same paragraph, same attachments, nothing changed in the repository: a
  new report is written anyway. The command does not deduplicate, diff, or refuse — the inputs and the
  timestamp in each report are what tell them apart.
- **Feature intent is a bug fix with no domain nouns.** Fewer than five questions are asked and the
  document is correspondingly short; padding is not permitted.

## Requirements *(mandatory)*

### Functional Requirements

#### Command shape and registration

- **FR-001**: The capability MUST ship as exactly one new command file under `spectra/commands/`,
  registered in the single `spectra/extension.yml` under `provides.commands` with the name
  `speckit.spectra.impact`, a `file`, and a `description`. No new top-level extension folder is created.
- **FR-002**: The command file MUST be agent-agnostic — generic arguments placeholder, YAML front matter
  carrying a `description`, and no agent's invocation syntax hard-coded anywhere in it.
- **FR-003**: The agent MUST be registered in `agents-list.json` in the `requirements-discovery` phase
  as an add-on provided by Spectra, and every structured listing regenerated from it rather than
  hand-edited; the per-agent prose block MUST be hand-written.
- **FR-004**: The change MUST bump the extension version with a matching changelog entry, rebuild the
  published package, and update the catalog entry and the landing page so none of them drifts from the
  extension folder.
- **FR-005**: The command MUST write only the analysis document, the folder index, and — on explicit
  confirmation — the `status` and `superseded_by` fields of the analysis it supersedes. It MUST NOT edit the
  constitution, create a spec, create a branch, or commit.

#### Inputs

- **FR-006**: The command MUST accept a one-paragraph feature intent as its only required input, and
  MUST require no documents at all.
- **FR-007**: Given no intent, the command MUST stop with a message naming what to supply, and MUST NOT
  scan.
- **FR-008**: The command MUST accept optional supporting documents as file paths given in the invocation,
  and MUST be able to read `.md`, `.txt`, `.pdf`, and `.docx` — the same set `speckit.spectra.brd` accepts.
  A path that is unreadable, missing, or of an unsupported type MUST be recorded by name with that reason and
  MUST NOT fail the run. Documents are ranked as the design spec ranks them: a feature request, brief, or
  epic first, then any document describing systems outside the repository, then prior related analyses.
- **FR-008a**: The feature intent supplied in the invocation is authoritative for **what is being asked**;
  supporting documents are evidence about it. Where a document contradicts the intent, the command MUST
  surface the contradiction rather than silently preferring either one — the same treatment FR-010c gives a
  specification that disagrees with the code.
- **FR-009**: The command MUST read project context without prompting for it: the constitution and
  guardrails, any existing specifications under `specs/`, source code, `docs/` and `README` and ADR titles,
  API contract definitions, schema and migration files, the test suite, CI configuration, and the existing
  impact-analysis folder.
- **FR-010**: The command MUST NOT ask any question whose answer is discoverable in the repository.

#### Two scan modes

- **FR-010a**: Where the project carries specifications and a constitution, the command MUST use them as
  its primary orientation — entity vocabulary, declared boundaries, prior decisions, and stated
  constraints — and scan code to confirm and extend what they describe. Where they are absent, the command
  MUST build its understanding by reading code alone, and MUST state that this is the heavier path.
- **FR-010b**: The command MUST state in the output which mode it ran and what it read to orient itself,
  so a reader can tell an analysis grounded in declared intent from one reconstructed from source.
- **FR-010c**: A specification, ADR, or other document is evidence of intent, not of current behaviour. A
  finding whose only evidence is such a document MUST NOT be recorded as `confirmed`, and every
  blast-radius claim MUST rest on a code citation. Where a document and the code disagree, the
  disagreement is itself a finding.
- **FR-010d**: Reading a specification MUST NOT create a relationship between the analysis and that
  specification. The command MAY cite a document as the provenance of a finding; it MUST NOT record the
  specification as related, informing, or superseded work. See FR-054.

#### Pre-flight

- **FR-011**: Before scanning, the command MUST look for a prior analysis of the same feature and MUST NOT
  rely on slug equality alone to find one, since the slug is derived afresh each run. A candidate is a
  prior analysis whose slug matches, or whose extracted entity set overlaps the current one by at least
  half of the smaller set. The command MUST state each candidate with its status and date, MUST ask whether
  to record the new run as superseding it, defaulting to yes, and where several candidates match MUST
  propose the most recent one that is not already superseded.
- **FR-012**: Before scanning, the command MUST ask whether this repository is the only one the system
  depends on, and MUST recommend answering no where the user is unsure.
- **FR-013**: Where the answer is no, the command MUST let the user declare each other system in whichever
  form they have — free-text description, a document, or a path to a local directory holding a copy of
  that system's source — and MUST NOT require any particular form. It MUST also accept an owning team name
  for each, and MUST NOT require one.
- **FR-014**: The command MUST NOT ask for, accept, or use a repository URL, credential, token, or login,
  MUST NOT clone or download anything, and MUST make no network request.
- **FR-015**: A declared local directory MUST be read in place. The command MUST NOT create, modify, or
  delete anything inside it, MUST NOT copy it, and MUST NOT write anywhere outside the project it was
  invoked in.
- **FR-016**: Pre-flight questions MUST NOT consume any part of the clarifying-question budget.
- **FR-017**: Every system MUST carry a scan state, written exactly as one of `scanned` (with the local path
  and coverage recorded), `declared-not-scanned` (with the form it was declared in), or `not-declared`, and
  that state MUST appear in the output. The project the command was invoked in is itself recorded as
  `scanned` with the form `project`, so a reader can tell at a glance what was read and what was only named.
- **FR-018**: A declared path that cannot be read MUST be recorded with a distinguishing reason — path
  not found, not readable, contains no source — MUST NOT be collapsed into a single "unavailable", and
  MUST drop that system to `declared-not-scanned` rather than failing the run.

#### Scan

- **FR-019**: The command MUST build a structural map — directory tree, file inventory, package
  manifests, entrypoints, route definitions, migrations, configuration, CI — reading full contents only
  for a short whitelist, so that this phase's cost does not scale with repository size.
- **FR-020**: The command MUST extract domain entities from the intent and attachments and expand each
  into search variants covering camelCase, snake_case, kebab-case, SCREAMING_SNAKE, singular and plural,
  table-naming conventions, and synonyms observed in the structural map.
- **FR-021**: The command MUST rank seed hits by term density weighted by file role, placing
  boundary-crossing files above internal utilities, and MUST cap the seed set at the configured seed cap.
- **FR-022**: The command MUST expand outward from the seeds by at most the configured hop budget, over
  imports and exports, callers, dependency-injection registrations, route bindings, data access, and
  event emit/subscribe pairs, including tests that reference seeds, and MUST cap total primary-repository
  files read at the configured file budget.
- **FR-023**: The command MUST sweep for the coupling patterns static traversal cannot see — reflection
  and dynamic dispatch, dynamic or lazy imports, string-keyed registries and factory maps,
  configuration-driven behaviour, scheduler and queue consumer registration, feature-flag lookups,
  serialization boundaries, and view resolution by name.
- **FR-024**: The command MUST extract concrete contract identifiers from the seed set — table and column
  names, endpoint paths, event and topic names, configuration keys, feature-flag keys, environment
  variable names — and search for each as a raw string across the entire repository, independent of the
  import graph. The identifiers MUST be ordered by boundary class, with table and column names, endpoint
  paths, and event and topic names ranked above configuration keys, feature-flag keys, and environment
  variable names, and the sweep MUST be capped at the configured identifier cap. Where the cap is reached
  the command MUST state it and MUST state how many identifiers went unswept.
- **FR-025**: Every hit from either sweep MUST become an item at `possible` confidence flagged for human
  verification, and MUST NOT be silently dropped.
- **FR-026**: A declared local directory MUST be searched only for those contract identifiers, capped at
  the configured per-system budget, with no term expansion, graph traversal, or lens analysis run against
  it.
- **FR-027**: The command MUST use whatever repository-wide text search the host agent provides, MUST NOT
  require or ship a script or binary of its own, and where no such search is available MUST state the
  limitation and report the reduced coverage.
- **FR-028**: Scan caps MUST be overridable in the invocation, and any non-default value MUST be stated
  in the output alongside the coverage numbers.

#### Clarifying questions

- **FR-029**: The command MUST ask at most five clarifying questions, MUST ask fewer when fewer things
  are genuinely ambiguous, and MUST NOT pad to five.
- **FR-030**: Questions MUST be generated from what the scan found ambiguous and ranked by how much the
  answer would change the blast radius or the impact rating.
- **FR-031**: Questions MUST be asked one at a time, each waiting for its answer.
- **FR-032**: Every question MUST offer three or four substantive options, "Other" as the final numbered
  option accepting a free-text sentence, and a recommendation with its reasoning grounded in a scan
  finding wherever one exists.
- **FR-033**: A skipped question MUST proceed on the recommended answer, MUST be recorded as an
  assumption tagged as defaulted and not confirmed, and MUST NOT block the run.
- **FR-034**: A defaulted answer in the scope-boundary, data-lifecycle, or contract-compatibility
  categories MUST additionally be promoted into the risks section.
- **FR-035**: Every question asked MUST appear in the output with its answer and whether that answer came
  from the user or was defaulted.

#### Lenses

- **FR-036**: The command MUST always run five lenses — blast radius, data, behavioural change, risk and
  reversibility, effort and sequencing — each grounded in cited evidence.
- **FR-037**: The command MUST add a security and privacy section when the scan touches authentication,
  personal-data fields, external endpoints, secrets, or cryptography, and a compliance section when the
  guardrails or constitution declare a regime; each MUST name the Spectra agent it routes to.
- **FR-038**: A conditional section MUST flag findings and route, and MUST NOT render a compliance
  verdict, claim certification, or reproduce the routed agent's analysis.
- **FR-039**: A conditional section whose trigger did not fire MUST be absent from the output rather than
  present and empty.
- **FR-040**: Lenses the repository cannot evidence — stakeholder mapping, change management and
  training, support model, vendor and licensing cost, organizational process change — MUST be emitted as
  human-follow-up items, and the command MUST NOT generate prose about them.

#### Trustworthiness rules

- **FR-041**: The output MUST NOT state absence of impact. It MAY state that no consumers were found in
  what was scanned.
- **FR-042**: Every item in the findings sections MUST carry a `path:line` citation; an inference that
  cannot be cited MUST appear under assumptions instead. **Evidenced absence is the one exception**: a
  finding that something is missing — no rollback path, no backfill tooling, no test covering a touched
  path — MUST instead cite what was searched and where, in the same form FR-048 uses for terms with no
  hits. Without this a High rating triggered by "no viable rollback path identified" could never be
  stated as a finding.
- **FR-042a**: The command MUST NOT reproduce a secret value in the output — no credential, key, token,
  password, or connection string, in whole or in fragment. Where a cited line contains one, the finding MUST
  give the location and the kind of secret only, and MUST state that the value was deliberately not
  reproduced. This holds for every section of the document and for anything the command says in the session.
- **FR-043**: Any change to a public API, event schema, database table, or shared contract MUST produce
  an external-contract-change item requiring human verification, regardless of what the scan found
  inside the repository.
- **FR-044**: The output MUST state, per declared system, how many files were read out of how many exist
  and by what selection method.
- **FR-045**: A cap reached or a declared path that could not be read MUST be reported with its reason;
  the command MUST NOT truncate silently.
- **FR-046**: Every finding MUST carry one of exactly three confidence levels — confirmed (direct cited
  evidence), probable (indirect but cited), possible (dynamic-pattern hit or a consumer in an unscanned
  declared system, requiring human verification).
- **FR-047**: The impact rating MUST be derived from the defined trigger set rather than judged, and the
  output MUST name the trigger that produced it. High follows from an irreversible data change, an
  external contract change, either conditional lens firing, or no viable rollback path; medium from an
  internal contract change, a reversible migration or backfill, or a behaviour change visible to existing
  users or callers; low only when the change is additive, trivially revertible, and touches neither data
  nor an external contract.
- **FR-048**: The output MUST record the terms that were searched for and produced no hits.

#### Output

- **FR-049**: The document MUST be written into `<artifact-root>/impact-analysis/` in the target project,
  honouring a root declared in the project's constitution, defaulting to `docs/` only after checking for
  the documentation-publication signal, recommending the non-publishing root when that signal is present,
  and taking the non-publishing option where the choice cannot be obtained. The path MUST be lowercase
  and project-relative, and the folder MUST be created on demand.
- **FR-050**: The filename MUST be `NNN-<name>.md`, where `NNN` is a zero-padded three-digit sequence
  number scoped to that folder and `<name>` is a kebab-case name the command derives from the feature
  intent and any supplied documents. `<name>` and the front-matter `feature_slug` MUST be the same string —
  one value, used in two places. The sequence MUST be one greater than the highest number already
  present in the folder — not a count of the files there, so that a deleted or archived analysis cannot
  cause a collision — and MUST start at 001 in an empty folder. The sequence MUST be independent of the
  `specs/` sequence.
- **FR-051**: Every run MUST allocate a new number and write a new document, including a re-run against the
  same feature and including a re-run whose input is identical to a previous one. The command MUST NOT
  overwrite, replace, amend, or diff an existing analysis, and MUST NOT refuse a run on the grounds that it
  has seen the same input before. Each report stands alone, distinguished by its number, its timestamp, and
  its recorded inputs.
- **FR-051a**: The document and its index row MUST be written once, as the run's final act, and the sequence
  number MUST be resolved at that moment. A run that stops before that point — interrupted, abandoned, or
  failed — MUST leave the impact-analysis folder exactly as it found it: no partial document, no document
  marked incomplete, and no number consumed. Everything before the write is reading and asking, so there is
  nothing on disk to clean up or recover.
- **FR-052**: The document MUST carry front matter recording the id, feature slug, title, status, impact
  rating, the generation timestamp including the time of day and the time zone, author, supersede
  relationships in both directions, per-system scan states with the local path and coverage where one was
  read, `declared-not-scanned` systems with the form they were declared in plus owner and reason, and the
  number of questions asked and defaulted. It MUST NOT carry a
  spec-reference field. The timestamp carries the time of day so that two runs on the same date are
  distinguishable.
- **FR-052a**: The document MUST record its own inputs: the feature intent **verbatim as supplied**, and
  every attachment by name or path with whether it was readable and read. A reader six months later must be
  able to see what the analysis was asked, not only what it concluded — and two reports on the same feature
  are told apart by their inputs and their timestamps.
- **FR-053**: The `feature_slug` is derived per run from the intent and any supplied documents. The command
  MUST NOT assume it is stable across runs and MUST NOT rely on it alone to relate one analysis to another;
  relating them is FR-011's confirmed detection. Linkage MUST NOT rely on a shared sequence number.
- **FR-053a**: The command MUST write `status: draft` on every run, interactive or not. Approval is a
  manual, human-owned step taken outside the tool — the BA takes the draft to stakeholders and records the
  outcome themselves — so the command MUST NOT set, prompt for, or infer any other status, with the single
  exception of marking a prior analysis `superseded` under FR-011. It MUST NOT interpret a status a human
  has set beyond reading it.
- **FR-054**: The command MUST NOT create a specification, MUST NOT record a link, reference, or
  relationship to one, and MUST NOT modify anything under `specs/` or depend on Spec Kit's own command
  files. Reading existing specifications as context is required by FR-010a and creates no such
  relationship: a document may be cited as the provenance of a finding, which is evidence, not linkage. An
  impact analysis and a specification remain independent processes; where a team wants to feed an analysis
  into `specify`, they do it by passing the document as an input, which needs nothing from this command.
- **FR-055**: The document MUST record every declared system by name, its scan state, and the form it was
  declared in, so a reader can tell a system that was read from one that was only described.
- **FR-056**: The command MUST append one index row per run to the impact-analysis folder's index,
  carrying id, title, status, impact rating, date, and supersede relationships, creating the index on
  demand. Because a human owns the status after the draft is written (FR-053a), the command MUST also
  refresh the existing rows from each document's front matter on every run, so an approval or rejection
  recorded by hand reaches the index. It MUST NOT modify any document in order to do so.
- **FR-057**: The document's section structure MUST come from a registered template resolved through
  Spec Kit's stack — project override, then preset, then extension, then core, then the command's inline
  skeleton as the last resort — taking the first readable non-empty layer.
- **FR-058**: The template MUST ship as an asset under `spectra/templates/` and be registered in
  `spectra/extension.yml` under `provides.templates` with a name, file, and description.
- **FR-059**: The command MUST report which template path it resolved.
- **FR-060**: The command MUST follow the resolved template's sections in its order, MUST NOT add,
  rename, or reorder them, MUST note rather than reinstate a section the template omits, and MUST strip
  guidance comments and placeholder tokens from the output.
- **FR-061**: The document MUST restate the change in one line so a reader can catch a misread, and MUST
  carry a rollback path and the point at which the change becomes irreversible.

#### Non-interactive mode

- **FR-062**: The command MUST accept a non-interactive switch that emits no prompt of any kind,
  including the pre-flight questions.
- **FR-062a**: Where the session cannot accept an answer and the switch was not passed, the command MUST
  detect that and proceed as though it had been: no prompts, recommendations taken, every answer tagged
  defaulted, and the banner where three or more were. It MUST say once, before it starts, that it is doing so
  and name the switch that makes it explicit. It MUST NOT hang waiting for input that cannot arrive, and MUST
  NOT proceed silently.
- **FR-063**: Non-interactively, scope MUST default to this repository only unless local paths are
  supplied, and any supplied path MUST be read in place with unreadable ones recorded by reason.
- **FR-064**: Non-interactively, every clarifying question MUST take its recommendation and be logged as
  defaulted and not confirmed. The document status is `draft` as it is on every run (FR-053a).
- **FR-065**: Non-interactively, a detected prior analysis MUST be recorded as superseded by the new
  document without modifying the prior document, and the output MUST state that the prior document was
  left unchanged.
- **FR-066**: Where three or more answers were defaulted, the document MUST open with a banner stating
  that the analysis is materially unconfirmed.

### Key Entities

- **Feature intent**: the one-paragraph statement of what should be true after the feature ships. The
  only required input, and the source of the entity set.
- **Feature slug**: the kebab-case name the command derives per run from the intent and any supplied
  documents. It is one value used in two places — the filename's `<name>` and the front-matter
  `feature_slug` — and it describes the document; it is not stable across runs and carries no
  relationship to anything outside the impact-analysis folder.
- **Scan mode**: whether the run oriented on the project's specifications and constitution or
  reconstructed its understanding from source alone. Recorded in the output.
- **Impact analysis**: the numbered Markdown deliverable — front matter, restated change, rating,
  lens findings, contract-verification table, follow-ups, risks and rollback, clarifications,
  assumptions, and coverage.
- **Scope declaration**: the set of other systems the user declares, each with the form it was declared in
  — free text, a document, or a local directory path — and a resulting scan state.
- **Finding**: one observation with a citation, a lens, and a confidence level.
- **Contract identifier**: a concrete string naming a boundary — table, column, endpoint, event, topic,
  configuration key, flag, environment variable — used both to sweep this repository and to detect
  consumers in any declared local copy of another system.
- **Clarification**: a question, its options, the recommendation, the answer, and whether the answer was
  given or defaulted.
- **Impact rating**: high, medium, or low, derived from the defined trigger set and reported with the
  trigger that fired.
- **Index**: the folder-level list of every analysis with its status and supersede relationships.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of items in the findings sections carry a citation that resolves to real content at
  the cited location; a citation that does not resolve is a defect.
- **SC-002**: A Business Analyst who has never read the repository can complete a run and have a
  document in hand in under 15 minutes, without opening a source file.
- **SC-003**: 100% of outputs state, per declared system, how much was read out of what exists and by what
  method, and which of the two scan modes ran — and 0% assert absence of impact.
- **SC-004**: Run retroactively against at least five already-shipped features, the analysis names at
  least 70% of the impacts that actually caused an incident, hotfix, or late review catch.
- **SC-005**: Of the items an analysis flags for verification, at least half turn out to be real
  couplings — high enough that reviewers keep reading the list.
- **SC-006**: Every run asks at most five clarifying questions, and at least 80% of them are answerable
  with a single keystroke.
- **SC-007**: 100% of re-runs against the same feature — including a re-run with identical input — produce a
  new numbered document, leave the prior one in place, and record the relationship in both documents and the
  index.
- **SC-008**: A reviewer picking up an analysis cold can tell, for every conclusion, whether the agent
  checked and found nothing or did not check — in 100% of documents.
- **SC-009**: 0 documents contain a compliance verdict, certification claim, or prose about a lens the
  repository cannot evidence.
- **SC-009a**: 0 documents reproduce a secret value, in whole or in fragment.
- **SC-010**: A stakeholder gate can be held on the document alone, without a follow-up request to read
  code, in at least 80% of reviews.

## Assumptions

- The user runs the command from inside a Spec Kit project, and the repository they run it in is the
  primary system under analysis.
- The host agent can read files, list directories, and search repository-wide text. Where it cannot
  search, the run degrades and says so rather than failing.
- The command makes no network request, requires no credential, and depends on no external service. It
  reads the project it was invoked in, plus any local directory the user points it at — in place, without
  copying — and writes only inside the project.
- Scan caps default to 30 seed files, 2 hops, 80 files in the project, 50 swept contract identifiers, and 20
  files per declared local system, and are overridable per invocation. The five-question cap is not.
- The author field is filled from the local committing identity where one is discoverable, and left empty
  rather than invented where it is not.
- Coupling that is neither imported nor named as a string anywhere in the source may go undetected. Git
  co-change analysis was considered and excluded: it is noisy on high-churn repositories, meaningless on
  quiet ones, and unavailable on a shallow checkout. Every output states this limitation.
- A system with no local checkout is described rather than searched. That is the expected case, not a
  degraded one: the analysis converts the description into a targeted handoff item addressed to the owning
  team.
- A consumer nobody declares and nobody remembers remains invisible. Scope declaration and the
  absence-of-evidence rule mitigate this; they do not solve it.
- Effort output is a coupling-depth heuristic, not an estimate, and is labelled as such.
- Impact analysis and specification are independent processes with no tooling link between them. The gate
  after this command is organizational, `specify` behaves exactly as it does today and is unaware the
  analysis exists, and a team that wants one to inform the other passes the document to `specify` as an
  input — which is possible today and needs nothing from this command. Existing specifications are read as
  evidence when they exist, which is context rather than linkage.
- Every run produces a new report. Nothing is overwritten, amended, or deduplicated, and identical input
  twice produces two reports — which is the simple behaviour on purpose. Each report carries its own inputs
  and timestamp, so telling two of them apart never depends on remembering what was run.
- Cross-run diffing is out of scope. Comparing two analyses is a human reading them side by side.
- Approval is a manual step outside the tool. Every document is written as a draft; the BA takes it to
  stakeholders and records the outcome by hand. The command's only later involvement is refreshing the
  index from what it finds, and marking a prior analysis superseded when the user confirms.
- A spec'd project produces a cheaper and better-oriented analysis than an unspec'd one. Neither is
  refused, and the output always says which it was.
- Compliance and security routing targets may still be under development in the roster; the analysis
  names the agent regardless, and a routed item is a handoff rather than a guarantee that the agent
  exists yet.
