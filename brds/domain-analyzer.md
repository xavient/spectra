# Business Requirements Document (BRD): Domain Analyzer

## Document Control

| Field             | Value                                                                                                  |
| ----------------- | ------------------------------------------------------------------------------------------------------ |
| BRD ID            | BRD-001                                                                                                 |
| Title             | Domain Analyzer                                                                                         |
| Author            | Spectra / TELUS Digital                                                                                 |
| Status            | Draft                                                                                                   |
| Version           | 0.1.0                                                                                                   |
| Created           | 2026-06-24                                                                                              |
| Last updated      | 2026-06-24                                                                                              |
| Related documents | `docs/capability-brief.html` (SDLC Phase 00 — Foundation agents), `.specify/memory/constitution.md`, `/speckit-constitution` |

## 1. Executive Summary

The **Domain Analyzer** is a Spectra add-on agent (SDLC Phase 00 — Foundation) that reads a
project's codebase, existing documentation, and current constitution, infers the team's business
domain, and proposes the guardrails best suited to it. It writes those proposals to a single,
reviewable Markdown file in which subject-matter experts (SMEs) **opt in** to the guardrails they
want. The approved set is then fed to the Guardrails / constitution agent (`/speckit-constitution`)
and becomes part of the project's enforced guardrails.

It removes the blank-page problem of authoring a constitution and ensures that the foundation every
downstream agent inherits is **grounded in the actual project** and **approved by humans**.

## 2. Business Context & Problem Statement

In Spectra, the constitution is the foundation of the agentic SDLC: it is set before any code, and
every downstream agent inherits it automatically (the Guardrails core agent "encodes your coding,
security, and architecture standards once — so every agent downstream inherits them automatically").
If the constitution is weak, generic, or incomplete, the entire agentic delivery chain is weakened.

Today, authoring that constitution is a manual, blank-page exercise:

- **Teams don't know which guardrails their domain needs.** A fintech back-end, a healthcare app,
  and an internal CLI demand very different rules, and teams rarely start from a domain-aware baseline.
- **Domain, security, and compliance knowledge lives in SMEs' heads**, not in machine-usable
  guardrails the agents can act on.
- **Manual authoring produces generic or inconsistent constitutions**, which produces inconsistent
  downstream behavior across all agents.
- **Guardrails without evidence are hard to trust or audit.** A reviewer cannot easily tell *why* a
  rule exists or whether it actually applies to this codebase.

The result is that the most leverage-rich artifact in the whole system — the constitution — is the
one most likely to be thin, because getting it started is hard and nobody is sure what belongs in it.

## 3. Business Objectives & Goals

- **G1 — Eliminate the blank page.** Produce a strong, domain-appropriate first draft of guardrails
  automatically, so teams start from a tailored baseline rather than nothing.
- **G2 — Keep humans in control.** SMEs decide what is adopted; nothing reaches the constitution
  without an explicit human choice.
- **G3 — Ground every suggestion in evidence.** Each proposed guardrail is traceable to the project
  artifact(s) that justify it, so SMEs can review quickly and auditors can trust the result.
- **G4 — Hand off losslessly.** The output flows directly into the existing Guardrails / constitution
  agent with minimal rewriting.
- **G5 — Support iteration.** The analysis can be re-run as the project evolves without discarding
  prior human decisions.

## 4. Stakeholders & Users

| Stakeholder / user                       | Role in this product | What they need from it                                                       |
| ---------------------------------------- | -------------------- | --------------------------------------------------------------------------- |
| Developer / operator                     | Primary user         | Runs the agent; gets a tailored proposal file and clear next steps.         |
| SMEs (domain, security, compliance, architecture) | Key reviewers | Review asynchronously; accept only the guardrails they want, with evidence to judge each. |
| Guardrails / constitution agent (`/speckit-constitution`) | Downstream consumer | A file structured so it can ingest exactly the approved guardrails. |
| All downstream Spectra agents            | Indirect beneficiaries | A stronger, domain-grounded constitution to inherit.                      |
| Engineering leads / auditors             | Oversight            | Traceability — visibility into why each guardrail exists and that humans approved it. |

## 5. Scope

### 5.1 In Scope

- Read and analyze the project's **codebase**, **existing documentation**, and **existing
  constitution** (if one is present).
- **Infer the business domain** and summarize the evidence behind that inference.
- **Generate candidate guardrails**, each as an atomic, individually selectable item carrying a
  stable ID, a declarative/testable statement, a target constitution section, supporting evidence,
  and a confidence rating.
- Write all candidates to a **single Markdown file** at a predictable location, with every item
  **default-unselected (opt-in)**.
- **Notify the user in chat** that the file is ready, where it is, and the exact next steps (review →
  check the items to adopt → run `/speckit-constitution` with the file).
- **Preserve-and-append on re-run**: keep prior human decisions and add only genuinely new candidates.
- Define and honor the **handoff contract** so the constitution agent consumes only the selected items.

### 5.2 Out of Scope

- **Editing the constitution itself.** That is the Guardrails / constitution agent's job; the Domain
  Analyzer never writes to `.specify/memory/constitution.md`.
- **Auto-accepting or auto-adopting** any guardrail. Adoption is always an explicit human action.
- **Interactive Q&A.** Review is pure file-based and asynchronous; the agent does not interrogate the
  user in a live session.
- **Enforcing guardrails** (CI gates, linting, build-time checks). Enforcement belongs to downstream
  agents and tooling.
- **Implementing specific compliance frameworks** (e.g., HIPAA, GDPR, PCI-DSS). Those are separate
  Spectra add-on agents; the Domain Analyzer may *recommend* enabling one but does not perform its work.
- **Finalizing wording, numbering, section placement, or versioning** of the constitution. The
  Guardrails / constitution agent remains the authority over the final document.

## 6. User Journeys

### Journey 1 — Generate domain-tailored guardrail proposals (Priority: P1)

- **Actor:** Developer / operator
- **Trigger:** Runs the Domain Analyzer on their project.
- **Outcome / value:** A single Markdown proposal file, populated with domain-appropriate,
  evidence-backed candidate guardrails, plus a chat message confirming it is ready and what to do
  next. Even with zero further review, the team now has a tailored draft instead of a blank page.
- **Flow:**
  1. Operator runs the agent in a project that uses Spec Kit.
  2. The agent reads the codebase, existing docs, and the existing constitution (if any).
  3. It infers the domain and drafts candidate guardrails grouped by target constitution section.
  4. It writes the proposal file with every candidate left unselected.
  5. It reports in chat: the file location, a one-line summary of the inferred domain, and the next steps.
- **Acceptance:**
  - **Given** a project with a readable codebase and docs, **When** the analyzer runs, **Then** a
    single Markdown proposal file is produced containing at least one candidate guardrail, each with
    an ID, a statement, a target section, evidence, and a confidence rating.
  - **Given** the run completes, **When** the agent reports back, **Then** the chat message states the
    file path and instructs the user to review, check the items they want, and run `/speckit-constitution`.
  - **Given** a freshly generated file, **When** it is opened, **Then** no candidate is pre-selected.

### Journey 2 — SME reviews asynchronously and opts in (Priority: P2)

- **Actor:** SME (domain / security / compliance / architecture)
- **Trigger:** Receives the proposal file (in an editor or via a pull request) after the analyzer run.
- **Outcome / value:** Only the guardrails the SME explicitly approves are carried into the
  constitution; the rest are ignored.
- **Flow:**
  1. SME opens the proposal file.
  2. For each candidate, the SME reads the statement, evidence, and confidence, then **checks the box
     to accept**, edits the wording if desired, or leaves it unchecked to reject.
  3. When done, the operator runs `/speckit-constitution` referencing the file.
  4. Only the checked items flow into the constitution; the constitution agent normalizes and versions them.
- **Acceptance:**
  - **Given** a reviewed file with some items checked and some not, **When** the constitution agent
    consumes the file, **Then** only the checked items are incorporated into the constitution.
  - **Given** an SME edits the wording of a checked item, **When** it is adopted, **Then** the edited
    wording is what flows into the constitution.
  - **Given** a file where no items are checked, **When** the constitution agent consumes it, **Then**
    no guardrails are added.

### Journey 3 — Re-run preserves prior decisions (Priority: P3)

- **Actor:** Developer / operator (returning)
- **Trigger:** Re-runs the analyzer after the codebase has evolved.
- **Outcome / value:** New candidates surface without losing any of the SME's earlier accept / reject /
  edit decisions.
- **Flow:**
  1. Operator re-runs the agent on a project that already has a proposal file.
  2. The agent detects the existing file and its reviewed state.
  3. It appends only genuinely new candidates and leaves previously reviewed items (and their
     checked/unchecked/edited state) untouched.
  4. It reports in chat how many new candidates were added.
- **Acceptance:**
  - **Given** an existing proposal file with reviewed items, **When** the analyzer re-runs, **Then**
    every prior item retains its exact selection state and any SME edits.
  - **Given** the codebase has new characteristics, **When** the analyzer re-runs, **Then** new
    candidates are appended and clearly distinguishable from previously reviewed ones.
  - **Given** nothing relevant changed, **When** the analyzer re-runs, **Then** no duplicate candidates
    are added.

### Journey 4 — Amend an existing constitution with deltas only (Priority: P3)

- **Actor:** Developer / operator on a project that already has a ratified constitution
- **Trigger:** Runs the analyzer where `.specify/memory/constitution.md` already contains guardrails.
- **Outcome / value:** Suggestions are limited to new or changed guardrails; the SME is not asked to
  re-review rules that are already in force.
- **Flow:**
  1. The agent reads the existing constitution before drafting candidates.
  2. It proposes only guardrails that are absent, and marks any that would amend an existing principle.
  3. It does not re-propose guardrails already ratified.
- **Acceptance:**
  - **Given** a constitution that already contains a guardrail, **When** the analyzer runs, **Then**
    it does not propose a duplicate of that guardrail.
  - **Given** a candidate that modifies an existing principle, **When** it appears in the file, **Then**
    it is marked as an amendment and names the principle it would change.

### Edge Cases

- **No existing constitution.** The agent still produces candidates and notes that the constitution
  will be created from the approved set.
- **Sparse or undocumented project.** With little evidence, the agent produces fewer candidates,
  marks them lower confidence, and says so rather than inventing rules.
- **Ambiguous domain.** The agent presents its best inference with the evidence shown, so the SME can
  correct it by editing or rejecting — it does not block.
- **Proposal file edited then re-run.** Prior decisions are preserved (Journey 3); the agent must not
  reorder or overwrite reviewed items.

## 7. Business Requirements

| ID    | Requirement                                                                                                                                                       | Priority |
| ----- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| BR-01 | The agent MUST read the project's codebase, existing documentation, and existing constitution (if present) before proposing anything.                            | P1       |
| BR-02 | The agent MUST infer the business domain and summarize the evidence basis for that inference in the output.                                                       | P1       |
| BR-03 | The agent MUST produce candidate guardrails as atomic, individually selectable items.                                                                             | P1       |
| BR-04 | Each candidate MUST include a stable identifier, a declarative and testable guardrail statement, the target constitution section, supporting evidence, and a confidence rating. | P1       |
| BR-05 | Candidates MUST default to **not selected** (opt-in); the agent MUST NOT pre-select any item.                                                                     | P1       |
| BR-06 | The agent MUST write all candidates to a single Markdown file at a defined, predictable location.                                                                 | P1       |
| BR-07 | After writing, the agent MUST inform the user in chat that the file is ready, state its location, and give the exact next steps (review → check items → run `/speckit-constitution`). | P1       |
| BR-08 | The output MUST be structured so the Guardrails / constitution agent can consume **only** the selected (checked) items.                                           | P1       |
| BR-09 | When a constitution already exists, candidates MUST be marked as new or as an amendment, and the agent MUST NOT propose duplicates of already-ratified guardrails. | P2       |
| BR-10 | The agent MUST NOT modify the constitution, source code, or any existing project file; its only write is its own proposal artifact.                               | P1       |
| BR-11 | On re-run, the agent MUST preserve prior human decisions (accepted / rejected / edited) and append only new candidates; it MUST NOT overwrite or reorder previously reviewed items. | P3       |
| BR-12 | Each guardrail statement SHOULD be written in the constitution's voice (declarative, testable, MUST/SHOULD with rationale) to minimize rewriting during handoff.  | P2       |
| BR-13 | The agent SHOULD group candidates by their target constitution section to make SME review efficient.                                                              | P2       |
| BR-14 | The agent SHOULD flag where a dedicated compliance add-on agent (e.g., HIPAA, GDPR) appears relevant to the inferred domain, as a recommendation only.            | P3       |
| BR-15 | The agent MUST operate as an agent-agnostic command and run on whatever coding agent the team uses.                                                               | P1       |

## 8. Success Metrics & Measurable Outcomes

- **SC-01** — A first-time user obtains a domain-tailored guardrail draft from a single command run,
  with zero manual authoring required to produce the draft.
- **SC-02** — 100% of candidates include traceable evidence: every item references the project
  artifact(s) that justify it.
- **SC-03** — An SME can complete a full review pass (accept / reject across all candidates) for a
  typical project in under 10 minutes, because items are atomic and evidenced.
- **SC-04** — At least 80% of accepted guardrails are adopted into the constitution without manual
  rewording (lossless handoff).
- **SC-05** — On re-run, 100% of prior human decisions are preserved (zero lost edits or selections).
- **SC-06** — Zero guardrails enter the constitution that the SME did not explicitly select (opt-in
  safety, verifiable by comparing selected vs. adopted items).
- **SC-07** — Time to a first usable constitution is reduced by at least 50% versus authoring from a
  blank template.

## 9. Assumptions

- The project uses the Spec Kit structure (a `.specify/` directory is present).
- The Guardrails capability is `/speckit-constitution`, and it remains the authority over final
  wording, numbering, section placement, and versioning of the constitution.
- SMEs review asynchronously in an editor or pull request, not in the terminal.
- The constitution lives at `.specify/memory/constitution.md` (present, or to be created from the
  approved set).
- The proposal file lives beside the constitution as a foundation-phase staging artifact (proposed:
  `.specify/memory/domain-analysis.md` — see Open Questions).
- A Markdown checklist (`- [ ]` to reject / `- [x]` to accept) is an acceptable selection mechanism
  for SMEs.

## 10. Constraints

- Must conform to Spectra's own constitution: **self-contained extension** (Principle II),
  **agent-agnostic, namespaced command** using `$ARGUMENTS` (Principle III), and **context-aware**
  reading of real project state (Principle IV).
- The extension's declared effect is **read-write**, but writes are limited to creating or updating
  its own proposal artifact; it never mutates source code or the constitution.
- Publishing the extension requires regenerating the distribution site (Principle V) — a build-time
  constraint, not a runtime behavior.

## 11. Dependencies

- **Downstream (output):** `/speckit-constitution` (the Guardrails agent) consumes the approved file.
- **Optional integration:** a `before_constitution` hook in `.specify/extensions.yml` could offer the
  Domain Analyzer automatically before constitution authoring (the same hook mechanism the
  constitution command already checks).
- **Input:** the constitution template's section structure, which defines the target sections that
  candidates are mapped to.

## 12. Risks & Mitigations

| Risk                                                       | Impact | Likelihood | Mitigation                                                                 |
| ---------------------------------------------------------- | ------ | ---------- | ------------------------------------------------------------------------- |
| Low-quality or generic suggestions erode SME trust         | H      | M          | Require evidence and a confidence rating per item; opt-in review.         |
| SMEs rubber-stamp without genuine review                    | M      | M          | Opt-in default-unchecked; atomic items force a decision per guardrail.    |
| Domain is misinferred                                      | M      | M          | Present inference as a suggestion with evidence shown; SME edits/rejects. |
| Re-run clobbers prior SME edits                            | H      | L          | Preserve-and-append behavior (BR-11, SC-05).                              |
| Scope creep into enforcement or compliance execution       | M      | M          | Explicitly out of scope; compliance is a recommendation only.            |
| Duplicate or conflicting suggestions vs. existing constitution | M  | M          | New-vs-amends marking and no duplicate proposals (BR-09).                 |

## 13. Open Questions

- **Output location / filename** — confirm `.specify/memory/domain-analysis.md`, or prefer another
  path (e.g., under `specs/` or a dedicated `guardrails/` directory)?
- **Confidence taxonomy** — is `High / Medium / Low` the right scale for SME triage?
- **Re-run identity** — how should "the same candidate" be recognized across runs to preserve state
  (stable IDs vs. matching on content)?
- **Compliance recommendations (BR-14)** — include in the first version, or defer to a later release?
- **Command verb** — confirm `analyze` (i.e., the command `speckit.domain-analyzer.analyze`).

## 14. Glossary

| Term                                | Definition                                                                                          |
| ----------------------------------- | -------------------------------------------------------------------------------------------------- |
| Constitution                        | The project's source-of-truth guardrails at `.specify/memory/constitution.md`.                     |
| Guardrail                           | A declarative, testable rule (principle, standard, or workflow constraint) that downstream agents honor. |
| Guardrails / constitution agent     | `/speckit-constitution`, which authors and updates the constitution.                                |
| SME                                 | Subject-Matter Expert (domain, security, compliance, or architecture).                             |
| Candidate / proposed guardrail      | A single suggested guardrail awaiting SME review.                                                   |
| Opt-in                              | Default-unselected; an item is adopted only if a human explicitly selects it.                       |
| Preserve-and-append                 | Re-run behavior that keeps prior human decisions and only adds new candidates.                      |
| Add-on agent                        | An optional Spectra agent enabled per project need, as opposed to a required core agent.            |
