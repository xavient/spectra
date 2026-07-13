# Spectra Agents — full reference

What every agent does, its status, and how to run it where available. For the at-a-glance roster
(SDLC phase, AI-DLC phase, type, status), see the [Agents table in the README](README.md#agents).

**Status:** ✅ available today · 🚧 under development.

Every Spectra command lives under the unified `speckit.spectra.*` namespace. Triggers below use
**Claude's form** (`/speckit-spectra-<command>`). Other agents register the same command under a
slightly different trigger — kiro-cli, for instance, keeps the dots (`/speckit.spectra.adr`). The
manifest name (`speckit.spectra.<command>`) is the same everywhere.

## Contents

- [Shipped Spectra agents](#shipped-spectra-agents) — installable from the catalog today
- [Spec Kit core agents](#spec-kit-core-agents) — available, shipped by Spec Kit itself
- [Roadmap](#roadmap) — under development, grouped by SDLC phase

---

## Shipped Spectra agents

These three ship in the `spectra` extension today. Install them all at once with
`specify extension add spectra`, then restart your AI agent so it picks up the commands.

### `adr` — Architecture Decision Records ✅

**`speckit.spectra.adr`** — Create a context-aware Architecture Decision Record grounded in your codebase,
prior ADRs, and the project constitution. It gathers project context, asks up to five clarifying
questions, writes the ADR under `Docs/ADR/`, and flags any constitution update the decision implies.

- **Arguments** — a one-or-two-sentence description of the decision. If omitted, the command asks you
  for one before drafting.
- **Use it when** — you're making a significant architecture or technology choice and want it captured
  and checked against the constitution as you decide.
- **Example (Claude)** —
  ```
  /speckit-spectra-adr We should standardize on PostgreSQL for all primary data stores
  ```

### `domain-analyzer` — Domain Analyzer ✅

**`speckit.spectra.domain-analyzer`** — Scan the existing codebase, docs, and ADRs to infer the
project's business domain, then write an opt-in proposal of candidate guardrails to
`.specify/memory/domain-analysis.md` for SME review and handoff to `/speckit-constitution`. It never
edits the constitution or source — you choose which guardrails to adopt.

- **Arguments** — none required. Optionally pass a focus or a domain hint to steer the analysis.
- **Use it when** — bootstrapping constitution guardrails for a brownfield project (no args — it infers
  the domain from what's already there), or when you already know the domain and want to anchor the
  analysis to it.
- **Examples (Claude)** —
  ```
  /speckit-spectra-domain-analyzer
  /speckit-spectra-domain-analyzer this is a banking system
  ```

### `github` — GitHub ✅

**`speckit.spectra.create-pr`** — Open a correctly-targeted GitHub PR for the current spec branch. It
derives the base branch from your promotion strategy, confirms before any push or PR creation, and
returns the PR URL — degrading gracefully with a manual fallback when `gh`, the remote, or the network
is unavailable. Also offered automatically by an `after_implement` hook once `implement` finishes, so
you don't have to invoke it by hand.

- **Arguments** — all optional:
  - *(none)* — open a **ready-for-review** PR (the default).
  - `--draft` — open the PR as a **draft** instead.
  - `--base <branch>` — override the derived base branch (still confirmed with you before opening).
- **Use it when** — implementation is done and you want the PR opened against the right base without
  running `git`/`gh` by hand.
- **Examples (Claude)** —
  ```
  /speckit-spectra-create-pr
  /speckit-spectra-create-pr --draft
  /speckit-spectra-create-pr --base develop
  ```

---

## Spec Kit core agents

Available today, but shipped by **Spec Kit** itself — Spectra layers on top of them. No installation
beyond Spec Kit is needed; run them with their built-in commands.

### Guardrails — `speckit.constitution` ✅

Encodes your coding, security, and architecture standards once — so every agent downstream inherits
them automatically.

- **Run it (Claude)** — `/speckit-constitution`

### Requirements Analyst — `speckit.specify` ✅

Turns a BRD or product brief into structured user stories with clear, testable acceptance criteria.

- **Run it (Claude)** — `/speckit-specify <what you want to build>`

### Clarifier — `speckit.clarify` ✅

Interrogates vague or missing requirements up front, before they turn into expensive rework later.

- **Run it (Claude)** — `/speckit-clarify`

### Requirements Quality — `speckit.checklist` ✅

Scores the spec for completeness, clarity, and consistency — effectively unit tests for your
requirements.

- **Run it (Claude)** — `/speckit-checklist`

### Architecture Planner — `speckit.plan` ✅

Produces the technical plan and tech-stack decisions, choosing the design patterns that fit the
problem — not the hype.

- **Run it (Claude)** — `/speckit-plan`

### Task Planner — `speckit.tasks` ✅

Breaks the plan into an ordered, dependency-aware task list — and can sync it straight to your issue
tracker.

- **Run it (Claude)** — `/speckit-tasks`

### Consistency — `speckit.analyze` ✅

Cross-checks spec, plan, and tasks for drift, gaps, and contradictions before the build kicks off.

- **Run it (Claude)** — `/speckit-analyze`

### Implementation — `speckit.implement` ✅

Executes the task list in dependency order, building to spec with tests written alongside the code.

- **Run it (Claude)** — `/speckit-implement`

### Testing — part of `speckit.implement` ✅

Generates unit, integration, smoke, and end-to-end tests, each mapped back to an acceptance
criterion. Today this runs as part of the Implementation agent — tests are written alongside the code
rather than as a separate command.

- **Run it (Claude)** — covered by `/speckit-implement`

---

## Roadmap

Planned agents, grouped by SDLC phase. Descriptions reflect intended scope; the command lands when
each one ships. All are **🚧 under development**.

### Foundation

- **FDA 21 CFR Part 11 & IEC 62304** (Add-on) — Checks electronic-records and e-signature integrity
  (Part 11) and medical-device software-lifecycle rigor (IEC 62304) — traceability, audit trails, and
  risk files mapped to software safety class.
- **ISO 27001 / 27701** (Add-on) — Audits ISMS and privacy-management controls against Annex A,
  reusing shared evidence so one control can satisfy SOC 2, ISO, and HIPAA at once.

### Requirements & Discovery

- **GDPR Compliance** (Add-on) — Verifies data-subject rights, lawful basis and consent, data
  minimization, retention and erasure, and cross-border transfer — and scaffolds the Article 30
  records of processing.
- **Canadian Privacy — PIPEDA / PHIPA / Law 25** (Add-on) — Evaluates Canada's federal and provincial
  privacy duties — PIPEDA's fair-information principles plus Quebec Law 25's mandatory PIAs,
  privacy-by-default, and cross-border assessments.
- **EU AI Act & Responsible-AI Governance** (Add-on) — Classifies AI components by risk tier and
  assembles the transparency disclosures and Annex IV technical documentation the EU AI Act requires.
- **Legal-Obligation Extraction** (Add-on) — Turns regulatory and contractual text into testable
  acceptance criteria — the connective tissue that lets any new regime flow into the spec and the
  compliance agents.

### Architecture & Design

- **Architecture Reviewer** (Add-on) — Audits the design against best practices, design principles,
  and your own standards before a line is written.
- **HIPAA Compliance** (Add-on) — Audits PHI handling against the Security Rule technical safeguards —
  access control, audit logging, integrity, authentication, and transmission encryption — and maps
  gaps to §164.312.
- **PCI-DSS** (Add-on) — Scopes the cardholder-data environment and checks secure-development,
  storage, transmission-crypto, and testing controls against PCI-DSS v4.0.1.
- **Threat Modeling** (Add-on) — Generates design-time STRIDE and attack-surface analysis from
  data-flow and architecture, complementing the runtime focus of the Security Analyst.
- **Performance & Scalability** (Add-on) — Static hot-path, complexity, and N+1 analysis with
  load-model sanity checks, surfacing scalability risk before the build.
- **Data Governance & Privacy Engineering** (Add-on) — Discovers PII and PHI across code and schemas,
  maps data flows and lineage, and classifies data — feeding the privacy and HIPAA agents.
- **API Design & Contract** (Add-on) — Lints OpenAPI specs, detects breaking changes, and enforces
  versioning and backward compatibility.

### Implementation

- **Dependency & Supply-Chain** (Add-on) — Generates an SBOM, runs reachability-aware vulnerability
  and license analysis, and flags transitive supply-chain risk.
- **Database & Data-Layer** (Add-on) — Reviews schema design, migration safety, and indexing —
  flagging lock risk and backward-incompatible changes before they ship.
- **Documentation Quality** (Add-on) — Assesses API doc coverage, README and runbook completeness, and
  drift where the code changed but the docs didn't.
- **Technical-Debt & Maintainability** (Add-on) — Quantifies complexity, duplication, dead code, and
  code smells into a maintainability rating and remediation estimate.

### Testing & Quality

- **Test Coverage Analyst** (Add-on) — Finds the gaps against the test pyramid, so coverage is real
  protection — not just a percentage.
- **Test Automation Analyst** (Add-on) — Recommends what's worth automating and where each test should
  run across the pipeline.
- **Security Analyst** (Add-on) — Surfaces threat exposure and OWASP-class issues through static and
  dynamic analysis of the change.
- **Accessibility & WCAG Compliance** (Add-on) — Audits the UI against WCAG 2.2 AA and maps
  conformance to the laws that adopt it — ADA, Section 508, and EN 301 549 — then scaffolds a VPAT.
- **Carbon & Green-Software** (Add-on) — Estimates software carbon intensity using the ISO-standard
  SCI methodology and surfaces the efficiency hotspots that move it.
- **Internationalization Readiness** (Add-on) — Flags hardcoded strings, locale and RTL handling, and
  un-externalized resources so the product is ready to localize.
- **Responsible-AI & Bias** (Add-on) — Audits ML components for bias, fairness, and explainability,
  and scaffolds the model card.

### Deployment & Operations

- **Operations Monitor** (Add-on) — Continuously analyzes logs, latency, and error signals
  post-deployment; surfaces anomalies and predicts SLA violations before they impact users.
- **Incident Responder** (Add-on) — Correlates incident signals with recent deployments, recommends a
  targeted rollback or fix, and validates the resolution against the original spec.
- **SOC 2** (Add-on) — Maps controls to the AICPA Trust Services Criteria and assembles continuous,
  change-managed evidence — every control change traceable to a commit.
- **SOX Change-Management** (Add-on) — Validates segregation of duties and change-approval evidence for
  financially relevant systems, producing an immutable release-approval trail.
- **Infrastructure-as-Code Analysis** (Add-on) — Detects Terraform, CloudFormation, and Kubernetes
  misconfigurations and drift, mapped to CIS, PCI, and SOC 2 baselines.
- **Cost & FinOps** (Add-on) — Estimates cloud cost from IaC, flags right-sizing and waste, and shows
  the cost delta of each change.
- **Observability Readiness** (Add-on) — Checks whether logs, metrics, and traces are instrumented,
  SLOs defined, and alert coverage adequate against the golden signals.
