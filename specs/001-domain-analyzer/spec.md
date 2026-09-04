# Feature Specification: Domain Analyzer

**Feature Branch**: `001-domain-analyzer`

**Created**: 2026-06-24

**Status**: Implemented

**Input**: User description: "@brds/domain-analyzer.md"

## Clarifications

### Session 2026-06-24

- Q: How is a candidate's stable identifier assigned so the same guardrail is recognized across re-runs? → A: Content-derived ID — a slug/hash of the normalized guardrail statement plus its target section, stable across reordering and edits to surrounding fields.
- Q: What does one candidate block look like in the proposal file (the handoff contract)? → A: A checkbox line carrying the guardrail statement, immediately followed by indented metadata fields (ID, target section, evidence, confidence, new/amendment marker); the `- [x]` line is the selection signal the constitution agent parses.
- Q: How precise must each candidate's evidence be? → A: A concrete file path plus an optional short quote or line reference.
- Q: How does the agent decide a guardrail is already covered by an existing constitution (avoid duplicates / mark amendments)? → A: Semantic/intent match against existing constitution principles; an overlapping-but-different rule is flagged as an amendment naming the principle it would change.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate domain-tailored guardrail proposals (Priority: P1)

A developer runs the Domain Analyzer on their Spec Kit project. The agent reads the
codebase, existing documentation, and the existing constitution (if any), infers the
team's business domain, and produces a single Markdown proposal file containing
evidence-backed candidate guardrails. It then tells the developer in chat where the
file is, what domain it inferred, and exactly what to do next. Even with no further
review, the team now has a tailored first draft instead of a blank page.

**Why this priority**: This is the core value proposition — it eliminates the
blank-page problem of authoring a constitution. Without it, none of the other stories
can exist. A single successful run already delivers a usable, domain-grounded draft.

**Independent Test**: Run the agent in a project with a readable codebase and docs;
verify that one Markdown proposal file is produced with at least one candidate
guardrail (each carrying an ID, statement, target section, evidence, and confidence)
and that a chat message reports the file path, inferred domain, and next steps.

**Acceptance Scenarios**:

1. **Given** a project with a readable codebase and documentation, **When** the
   analyzer runs, **Then** a single Markdown proposal file is produced containing at
   least one candidate guardrail, each with a stable ID, a declarative/testable
   statement, a target constitution section, supporting evidence, and a confidence
   rating.
2. **Given** the run completes, **When** the agent reports back in chat, **Then** the
   message states the proposal file path, a one-line summary of the inferred domain,
   and instructs the user to review, check the items they want, and run
   `/speckit-constitution` with the file.
3. **Given** a freshly generated proposal file, **When** it is opened, **Then** no
   candidate is pre-selected (every item is opt-in / unchecked).

---

### User Story 2 - SME reviews asynchronously and opts in (Priority: P2)

A subject-matter expert (domain, security, compliance, or architecture) receives the
proposal file in an editor or via a pull request. For each candidate they read the
statement, evidence, and confidence, then check the box to accept, edit the wording if
they wish, or leave it unchecked to reject. When done, the operator runs
`/speckit-constitution` against the file and only the checked items flow into the
constitution.

**Why this priority**: This is what keeps humans in control and makes the handoff
trustworthy. It depends on Story 1's output existing but is the gate that ensures
nothing enters the constitution without explicit human approval.

**Independent Test**: Take a generated proposal file, check some items and edit one,
leave others unchecked; verify that only the checked items (with any edits) are the
ones marked for adoption and that unchecked items are excluded.

**Acceptance Scenarios**:

1. **Given** a reviewed file with some items checked and some not, **When** the
   constitution agent consumes the file, **Then** only the checked items are
   incorporated into the constitution.
2. **Given** an SME edits the wording of a checked item, **When** it is adopted,
   **Then** the edited wording is what flows into the constitution.
3. **Given** a file where no items are checked, **When** the constitution agent
   consumes it, **Then** no guardrails are added.

---

### User Story 3 - Re-run preserves prior decisions (Priority: P3)

A developer re-runs the analyzer after the codebase has evolved. The agent detects the
existing proposal file and its reviewed state, appends only genuinely new candidates,
and leaves every previously reviewed item — including its checked/unchecked state and
any SME edits — untouched. It reports in chat how many new candidates were added.

**Why this priority**: It enables safe iteration over the life of the project. It is
lower priority because the first two stories already deliver end-to-end value; this
protects that value across repeated runs.

**Independent Test**: Run the analyzer twice on a project, with SME edits/selections
applied between runs and a change to the codebase; verify all prior items retain their
exact state and only new, non-duplicate candidates are appended.

**Acceptance Scenarios**:

1. **Given** an existing proposal file with reviewed items, **When** the analyzer
   re-runs, **Then** every prior item retains its exact selection state and any SME
   edits.
2. **Given** the codebase has gained new characteristics, **When** the analyzer
   re-runs, **Then** new candidates are appended and clearly distinguishable from
   previously reviewed ones.
3. **Given** nothing relevant changed, **When** the analyzer re-runs, **Then** no
   duplicate candidates are added.

---

### User Story 4 - Amend an existing constitution with deltas only (Priority: P3)

A developer runs the analyzer on a project that already has a ratified constitution.
The agent reads the existing constitution first and proposes only guardrails that are
absent, marking any candidate that would amend an existing principle and naming the
principle it would change. It never re-proposes already-ratified guardrails.

**Why this priority**: It avoids review fatigue on mature projects by limiting
proposals to true deltas. It is P3 because it refines behavior for an established case
rather than enabling the primary flow.

**Independent Test**: Run the analyzer on a project whose constitution already contains
a guardrail; verify no duplicate of that guardrail is proposed and that any
amendment-style candidate is labeled as an amendment naming the affected principle.

**Acceptance Scenarios**:

1. **Given** a constitution that already contains a guardrail, **When** the analyzer
   runs, **Then** it does not propose a duplicate of that guardrail.
2. **Given** a candidate that modifies an existing principle, **When** it appears in
   the file, **Then** it is marked as an amendment and names the principle it would
   change.

---

### Edge Cases

- **No existing constitution**: The agent still produces candidates and notes that the
  constitution will be created from the approved set.
- **Sparse or undocumented project**: With little evidence, the agent produces fewer
  candidates, marks them at lower confidence, and says so rather than inventing rules.
- **Ambiguous domain**: The agent presents its best inference with the evidence shown
  so the SME can correct it by editing or rejecting; it does not block.
- **Proposal file edited then re-run**: Prior decisions are preserved; the agent must
  not reorder or overwrite reviewed items.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The agent MUST read the project's codebase, existing documentation, and
  existing constitution (if present) before proposing anything.
- **FR-002**: The agent MUST infer the business domain and summarize the evidence basis
  for that inference in the output.
- **FR-003**: The agent MUST produce candidate guardrails as atomic, individually
  selectable items.
- **FR-004**: Each candidate MUST include a stable identifier (content-derived as a
  slug/hash of the normalized guardrail statement plus its target section), a
  declarative and testable guardrail statement, the target constitution section,
  supporting evidence (at least one concrete file path, optionally with a short quote
  or line reference), and a confidence rating.
- **FR-005**: Candidates MUST default to not selected (opt-in); the agent MUST NOT
  pre-select any item.
- **FR-006**: The agent MUST write all candidates to a single Markdown file at a
  defined, predictable location.
- **FR-007**: After writing, the agent MUST inform the user in chat that the file is
  ready, state its location, and give the exact next steps (review → check items → run
  `/speckit-constitution`).
- **FR-008**: The output MUST represent each candidate as a checkbox line bearing the
  guardrail statement, immediately followed by indented metadata fields (ID, target
  section, evidence, confidence, new/amendment marker), so the Guardrails /
  constitution agent can consume only the selected (checked) items together with their
  metadata. The `- [x]` checkbox line is the canonical selection signal.
- **FR-009**: When a constitution already exists, candidates MUST be marked as new or
  as an amendment, and the agent MUST NOT propose duplicates of already-ratified
  guardrails. Duplication and amendment status MUST be determined by semantic/intent
  match against existing constitution principles; an overlapping-but-different
  candidate MUST be marked as an amendment naming the principle it would change.
- **FR-010**: The agent MUST NOT modify the constitution, source code, or any existing
  project file; its only write is its own proposal artifact.
- **FR-011**: On re-run, the agent MUST preserve prior human decisions (accepted /
  rejected / edited) and append only new candidates; it MUST NOT overwrite or reorder
  previously reviewed items.
- **FR-012**: Each guardrail statement SHOULD be written in the constitution's voice
  (declarative, testable, MUST/SHOULD with rationale) to minimize rewriting during
  handoff.
- **FR-013**: The agent SHOULD group candidates by their target constitution section to
  make SME review efficient.
- **FR-014**: The agent SHOULD flag where a dedicated compliance add-on agent (e.g.,
  HIPAA, GDPR) appears relevant to the inferred domain, as a recommendation only.
- **FR-015**: The agent MUST operate as an agent-agnostic command and run on whatever
  coding agent the team uses.

### Key Entities *(include if feature involves data)*

- **Candidate guardrail**: A single proposed rule awaiting SME review. Attributes:
  stable identifier (content-derived from the normalized statement + target section),
  declarative/testable statement, target constitution section, supporting evidence
  (at least one concrete file path, optionally with a short quote or line reference),
  confidence rating, selection state (opt-in / checked), and a new-vs-amendment marker
  (with the named principle for amendments). On disk it is rendered as a checkbox line
  (the statement) followed by indented metadata fields.
- **Proposal file**: The single Markdown artifact holding all candidates plus the
  inferred-domain summary and its evidence. Lives at a predictable location beside the
  constitution; default-unselected; preserved and appended across re-runs. Each
  candidate's `- [x]` checkbox line is the canonical selection signal consumed at
  handoff.
- **Domain inference**: The agent's best determination of the team's business domain,
  accompanied by the evidence that justifies it.
- **Confidence rating**: A qualitative score (High / Medium / Low) attached to each
  candidate to support SME triage.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A first-time user obtains a domain-tailored guardrail draft from a single
  command run, with zero manual authoring required to produce the draft.
- **SC-002**: 100% of candidates include traceable evidence — every item references at
  least one concrete file path (optionally with a short quote or line reference) that
  justifies it.
- **SC-003**: An SME can complete a full review pass (accept / reject across all
  candidates) for a typical project in under 10 minutes.
- **SC-004**: At least 80% of accepted guardrails are adopted into the constitution
  without manual rewording (lossless handoff).
- **SC-005**: On re-run, 100% of prior human decisions are preserved (zero lost edits
  or selections).
- **SC-006**: Zero guardrails enter the constitution that the SME did not explicitly
  select (verifiable by comparing selected vs. adopted items).
- **SC-007**: Time to a first usable constitution is reduced by at least 50% versus
  authoring from a blank template.

## Assumptions

- The project uses the Spec Kit structure (a `.specify/` directory is present).
- The Guardrails capability is `/speckit-constitution`, and it remains the authority
  over final wording, numbering, section placement, and versioning of the constitution.
- SMEs review asynchronously in an editor or pull request, not in the terminal.
- The constitution lives at `.specify/memory/constitution.md` (present, or to be
  created from the approved set).
- The proposal file lives beside the constitution as a foundation-phase staging
  artifact at `.specify/memory/domain-analysis.md`.
- A Markdown checklist (`- [ ]` to reject / `- [x]` to accept) is an acceptable
  selection mechanism for SMEs.
- Confidence is expressed on a `High / Medium / Low` scale.
- "The same candidate" is recognized across runs by its content-derived stable
  identifier (a slug/hash of the normalized statement + target section), which is how
  re-run state preservation is anchored and stays robust to reordering and edits to
  surrounding fields.
- The command verb is `analyze` (command `speckit.domain-analyzer.analyze`).
- Compliance-add-on recommendations (FR-014) are included in the first version as
  recommendations only.

## Constraints

- Must conform to Spectra's own constitution: self-contained extension (Principle II),
  agent-agnostic, namespaced command using `$ARGUMENTS` (Principle III), and
  context-aware reading of real project state (Principle IV).
- The extension's declared effect is read-write, but writes are limited to creating or
  updating its own proposal artifact; it never mutates source code or the constitution.
- Publishing the extension requires regenerating the distribution site (Principle V) —
  a build-time constraint, not a runtime behavior.

## Dependencies

- **Downstream (output)**: `/speckit-constitution` (the Guardrails agent) consumes the
  approved file.
- **Optional integration**: a `before_constitution` hook in `.specify/extensions.yml`
  could offer the Domain Analyzer automatically before constitution authoring.
- **Input**: the constitution template's section structure, which defines the target
  sections that candidates are mapped to.

## Out of Scope

- Editing the constitution itself (the Guardrails agent's job; the Domain Analyzer never
  writes to `.specify/memory/constitution.md`).
- Auto-accepting or auto-adopting any guardrail — adoption is always an explicit human
  action.
- Interactive Q&A — review is file-based and asynchronous.
- Enforcing guardrails (CI gates, linting, build-time checks).
- Implementing specific compliance frameworks (HIPAA, GDPR, PCI-DSS); the analyzer may
  recommend enabling one but does not perform its work.
- Finalizing wording, numbering, section placement, or versioning of the constitution.
