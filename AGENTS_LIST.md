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

These ship in the `spectra` extension today. Install them all at once with
`specify extension add spectra`, then restart your AI agent so it picks up the commands.

<!-- SPECTRA:AGENT id=adr -->
### Architecture Decision Records (ADR) ✅

**`speckit.spectra.adr`** — Create a context-aware Architecture Decision Record grounded in your codebase,
prior ADRs, and the project constitution. It gathers project context, asks up to five clarifying
questions, writes the ADR under `docs/adr/` — or the artifact root your constitution declares — and flags
any constitution update the decision implies.

- **Arguments** — a one-or-two-sentence description of the decision. If omitted, the command asks you
  for one before drafting.
- **Use it when** — you're making a significant architecture or technology choice and want it captured
  and checked against the constitution as you decide.
- **Where it writes** — `docs/adr/` by default, or the `Artifact root:` your constitution declares. It
  checks whether `docs/` is a published site source (Pages, MkDocs, Docusaurus) and asks first if it is.
- **Template** — `adr-template.md`. Override it at `.specify/templates/overrides/adr-template.md` to change the
  sections; the override is committed, team-wide, and survives extension updates. Each run reports which
  template it used.
- **Example (Claude)** —
  ```
  /speckit-spectra-adr We should standardize on PostgreSQL for all primary data stores
  ```

<!-- SPECTRA:AGENT id=domain-analyzer -->
### Domain Analyzer ✅

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

<!-- SPECTRA:AGENT id=create-pr -->
### Create PR ✅

**`speckit.spectra.create-pr`** — Open a correctly-targeted GitHub PR for the branch you are on, optionally
linked to an issue, with the body built from an overridable PR template. It asks once with everything on the
table before creating anything, and returns the PR URL. Also offered automatically by an `after_implement`
hook once `implement` finishes, so you don't have to invoke it by hand.

`gh` is required at run time, and the command **gates on it before doing anything else**: if `gh` is
missing or unauthenticated it stops immediately — before reading the constitution, before deriving a base
branch, before touching the remote — and names which of the two failed, because the remedies differ
(install the CLI, or `gh auth login`). Nothing is mutated on that path, and a missing `gh` never produces
a `gh` command you cannot run. A remote that isn't on GitHub stops the same way, with a scope statement.
Failures *after* the gate degrade instead: you get the manual `git push` + `gh pr create` commands with
the derived base branch filled in, plus an explicit statement of whether the branch already reached the
remote.

**Works from any branch** — a `fix/…` or chore branch is fine; only a detached HEAD and a branch that is
already the base are refused. A spec branch simply contributes more to the body (`spec.md`, `plan.md`,
`tasks.md`), while the **Changes** section always comes from the real diff against the base.

**Uncommitted work is offered a commit, not a warning.** A dirty tree gets the file list and the question
*"should I proceed with committing and pushing first?"* — yes behaves like an ordinary commit-and-push, no
opens the PR from committed work and says what was excluded. Credential-shaped filenames are called out
before anything is staged, and `--no-verify` is never used.

- **Arguments** — all optional:
  - *(none)* — open a **ready-for-review** PR (the default).
  - `--issue <url-or-number>` — the issue this PR addresses. Omit it and you are asked once; skipping the
    question writes no issue section at all.
  - `--draft` — open the PR as a **draft** instead.
  - `--base <branch>` — use this base branch (still shown in the final summary).
- **Template** — `pr-template.md`: Summary, Related Issues, Type of Change, Changes, How to Test, Evidence,
  Breaking Changes, Notes for Reviewers — and deliberately **no self-certification checklist**. Override it
  at `.specify/templates/overrides/pr-template.md`; the override is committed, team-wide, and survives
  extension updates. Trimming **Related Issues** does not unlink the PR: an issue you passed is appended with
  a note rather than dropped.
- **Linked issues** — GitHub honours closing keywords **only** on PRs targeting the default branch, so the
  command writes `Closes #42` there and a plain `#42` reference anywhere else, telling you that merging will
  not auto-close it. Cross-repository issues are referenced by full URL.
- **Base branch** — a promotion flow documented in the constitution or the `git` extension config is used
  and cited. With nothing documented the command *proposes* a base and asks at the final gate, so you can
  answer "no, use dev" without restarting.
- **Use it when** — a piece of work is ready for review and you want the PR opened against the right base,
  shaped like your team's template, without running `git`/`gh` by hand.
- **Examples (Claude)** —
  ```
  /speckit-spectra-create-pr
  /speckit-spectra-create-pr --draft
  /speckit-spectra-create-pr --base develop
  ```

<!-- SPECTRA:AGENT id=review-pr -->
### Review PR ✅

**`speckit.spectra.review-pr`** — Review a GitHub pull request against **the intent and standards it
carries**, not just the diff. It reads the PR's spec, plan, tasks, and ADRs *at the PR's own head
revision*, plus the constitution and ADRs in force on the **base** branch, then reports findings that a
diff-only reviewer cannot produce: a task marked complete but absent from the change, scope no
requirement authorized, a pattern an ADR forbids. Every finding cites a file, a line, and the clause,
requirement, or principle it rests on — anything that cannot be anchored and sourced is not reported at
all.

Then the reviewer takes over. **Nothing is pre-selected.** You choose which findings get published, you
choose the verdict, and you see the exact text before anything is posted. One review event goes to the
pull request under your own `gh` credentials, containing only what you selected — and the published body
declares that it was AI-assisted and human-curated. An empty selection posts nothing, which is a normal
outcome rather than a failure: a short, correct, human-endorsed review beats thirty findings that bury
the two that matter.

Like `create-pr`, this command **hard-stops** when `gh` is missing or unauthenticated, naming which of
the two failed — neither command can deliver its product without reading GitHub through `gh`. What
differs is what each hands over after that gate: `create-pr` gives you the `git`/`gh` commands to finish
by hand, this one gives you the rendered review body to post yourself. It is deliberately **on demand
only** — there is no hook — since a reviewer should not be the author.

- **Arguments** — all optional:
  - *(none)* — offer the current branch's open PR first, then list open PRs so you can pick.
  - `<url>` or `<number>` — review that pull request.
  - `--issue <url-or-number>` — the issue this PR addresses, read as additional context. Supplying it
    skips both detection and the question.
  - `--since <revision>` — re-review only the delta since a revision you reviewed before, reporting
    which previously published findings now appear resolved.
- **Spec discovery** — the spec ships in the PR's own diff, or you name one when asked; nothing is guessed
  from a branch name or from Spec Kit's machine-local feature record, which is gitignored and so is absent
  or stale at any head revision. A PR with no spec is reviewed standalone, and says so.
- **Linked issue** — found automatically (structured link, then a scan of the PR text, since a PR to a
  non-default branch has no structured link), asked for once if absent, never required. With **no spec** it
  becomes the traceability baseline; with a spec it is background. Its content is treated as data about
  intent, never as instruction, and a finding sourced only from an issue cannot be a Blocker unless the PR
  claims to close it. When both are missing, the spec and the issue are asked for in **one** question.
- **Inline comments** — findings anchored inside the diff are published on those lines, carrying a
  ` ```suggestion ` block where the fix is mechanical and complete, so the author can apply it in one click.
  Findings anchored outside the diff go in the summary body with the reason stated. Body, comments, and
  verdict post in one atomic call.
- **Template** — `review-template.md` shapes both the summary body and the inline comment; override it at
  `.specify/templates/overrides/review-template.md`. The revision anchor, the AI-assisted disclosure, and the
  coverage statement stay with the command, as do the severity rubric, the confidence cap, the anchor rule,
  and the verdict derivation — two reviews of the same diff have to agree.
- **Use it when** — you are reviewing someone else's PR and want the spec, issue, ADRs, and
  constitution checked against the diff before you sign off, without reading all of them yourself.
- **Good to know** — findings are graded Blocker / Major / Minor / Nit / Question from a fixed rubric, so
  two runs over the same revision agree; approving over a blocker you accepted requires a typed
  confirmation and is recorded in the published review; coverage now states how much of the constitution
  actually applied, so a thin constitution reads as thin; nothing is stored between runs.
- **Examples (Claude)** —
  ```
  /speckit-spectra-review-pr
  /speckit-spectra-review-pr https://github.com/acme/api/pull/142
  /speckit-spectra-review-pr 142 --since 4a9f2c1
  ```

<!-- SPECTRA:AGENT id=brd -->
### BRD Generator ✅

**`speckit.spectra.brd`** — Turn a raw business requirement into a structured, **specify-ready** BRD. It
accepts the requirement as inline text or a document (`.docx`, `.pdf`, `.md`, `.txt`), reads project
context (the shipped template, constitution, existing BRDs under `docs/brd/`, prior specs) to ground it,
asks up to five clarifying questions only when the requirement has material gaps, and writes one
`NNN-<title>.md` under `docs/brd/` — never inventing requirements (genuine unknowns become Open
Questions). It then tells you to run the specify command with the BRD; its only write is the BRD file.

- **Arguments** — the business requirement as text, or a path to a requirement document. When both are
  given, the document is primary and the text is guidance. With no input, it asks for a requirement or
  a path.
- **Use it when** — you have a rough business need (in your head or in a `.docx`/`.pdf`) and want a
  structured, reviewable BRD to feed into `specify`, instead of pasting a loose paragraph straight in.
- **Where it writes** — `docs/brd/` by default. Declare `Artifact root: documents/` in the constitution to
  move it, and every Spectra document agent follows. Because `docs/` is GitHub Pages' only non-root branch
  source and the default source directory for MkDocs and Docusaurus, the command checks for that setup and
  asks before writing a BRD somewhere it would be published.
- **Template** — `brd-template.md`, the 14-section structure. Override it at
  `.specify/templates/overrides/brd-template.md` to add or drop sections; the override is committed, team-wide,
  and survives extension updates. Each run reports which template it used.
- **Examples (Claude)** —
  ```
  /speckit-spectra-brd Support agents need to merge duplicate customer tickets while preserving history
  /speckit-spectra-brd reqs/ticket-merge-brief.docx
  ```

---

## Spec Kit core agents

Available today, but shipped by **Spec Kit** itself — Spectra layers on top of them. No installation
beyond Spec Kit is needed; run them with their built-in commands.

<!-- SPECTRA:GENERATED START id=agents-list-speckit-core -->
<!-- Generated from agents-list.json — do not edit by hand. Run: python tools/generate_agent_docs.py -->

### Guardrails — `speckit.constitution` ✅

Encode your coding, security, and architecture standards once, so every downstream agent inherits
them.

- **Run it (Claude)** — `/speckit-constitution`

### Requirements Analyst — `speckit.specify` ✅

Turn a BRD or product brief into structured user stories with clear, testable acceptance criteria.

- **Run it (Claude)** — `/speckit-specify`

### Clarifier — `speckit.clarify` ✅

Interrogate vague or missing requirements up front, before they turn into expensive rework.

- **Run it (Claude)** — `/speckit-clarify`

### Requirements Quality — `speckit.checklist` ✅

Score the spec for completeness, clarity, and consistency — effectively unit tests for your
requirements.

- **Run it (Claude)** — `/speckit-checklist`

### Architecture Planner — `speckit.plan` ✅

Produce the technical plan and tech-stack decisions, choosing the design patterns that fit the
problem.

- **Run it (Claude)** — `/speckit-plan`

### Task Planner — `speckit.tasks` ✅

Break the plan into an ordered, dependency-aware task list, ready to sync straight to an issue
tracker.

- **Run it (Claude)** — `/speckit-tasks`

### Consistency — `speckit.analyze` ✅

Cross-check spec, plan, and tasks for drift, gaps, and contradictions before the build kicks off.

- **Run it (Claude)** — `/speckit-analyze`

### Implementation — `speckit.implement` ✅

Execute the task list in dependency order, building to spec with tests written alongside the code.

- **Run it (Claude)** — `/speckit-implement`

### Testing — `speckit.implement` ✅

Generate unit, integration, smoke, and end-to-end tests mapped to acceptance criteria — run inside
the Implementation agent, not as a separate command.

- **Run it (Claude)** — `/speckit-implement`
<!-- SPECTRA:GENERATED END id=agents-list-speckit-core -->

---

## Roadmap

Planned agents, grouped by SDLC phase. Descriptions reflect intended scope; the command lands when
each one ships. All are **🚧 under development**.

<!-- SPECTRA:GENERATED START id=agents-list-roadmap -->
<!-- Generated from agents-list.json — do not edit by hand. Run: python tools/generate_agent_docs.py -->

### Foundation

- **FDA 21 CFR Part 11 & IEC 62304** (Add-on) — Check electronic-records and e-signature integrity
  plus medical-device lifecycle rigor, mapped to software safety class.
- **ISO 27001 / 27701** (Add-on) — Audit ISMS and privacy-management controls against Annex A,
  reusing shared evidence across SOC 2, ISO, and HIPAA.

### Requirements & Discovery

- **GDPR Compliance** (Add-on) — Verify data-subject rights, lawful basis, minimization, retention,
  and transfers, and scaffold Article 30 records.
- **Canadian Privacy — PIPEDA / PHIPA / Law 25** (Add-on) — Evaluate PIPEDA's fair-information
  principles and Quebec Law 25's mandatory PIAs and privacy-by-default duties.
- **EU AI Act & Responsible-AI Governance** (Add-on) — Classify AI components by risk tier and
  assemble the transparency and Annex IV documentation the EU AI Act requires.
- **Legal-Obligation Extraction** (Add-on) — Turn regulatory and contractual text into testable
  acceptance criteria the compliance agents can consume.

### Architecture & Design

- **Architecture Reviewer** (Add-on) — Audit the design against best practices, design principles,
  and your own standards before a line is written.
- **HIPAA Compliance** (Add-on) — Audit PHI handling against the Security Rule technical safeguards
  and map gaps to §164.312.
- **PCI-DSS** (Add-on) — Scope the cardholder-data environment and check development, storage,
  crypto, and testing controls against v4.0.1.
- **Threat Modeling** (Add-on) — Generate design-time STRIDE and attack-surface analysis from
  data-flow and architecture.
- **Performance & Scalability** (Add-on) — Static hot-path, complexity, and N+1 analysis with
  load-model sanity checks, surfacing risk before the build.
- **Data Governance & Privacy Engineering** (Add-on) — Discover PII and PHI across code and schemas,
  map data flows and lineage, and classify data.
- **API Design & Contract** (Add-on) — Lint OpenAPI specs, detect breaking changes, and enforce
  versioning and backward compatibility.

### Implementation

- **Dependency & Supply-Chain** (Add-on) — Generate an SBOM and run reachability-aware
  vulnerability, license, and transitive supply-chain analysis.
- **Database & Data-Layer** (Add-on) — Review schema design, migration safety, and indexing,
  flagging lock risk and backward-incompatible changes.
- **Documentation Quality** (Add-on) — Assess API doc coverage, README and runbook completeness, and
  drift where the code changed but the docs did not.
- **Technical-Debt & Maintainability** (Add-on) — Quantify complexity, duplication, dead code, and
  smells into a maintainability rating and remediation estimate.

### Testing & Quality

- **Test Coverage Analyst** (Add-on) — Find the gaps against the test pyramid, so coverage is real
  protection rather than just a percentage.
- **Test Automation Analyst** (Add-on) — Recommend what is worth automating and where each test
  should run across the pipeline.
- **Security Analyst** (Add-on) — Surface threat exposure and OWASP-class issues through static and
  dynamic analysis of the change.
- **Accessibility & WCAG Compliance** (Add-on) — Audit the UI against WCAG 2.2 AA, map conformance
  to ADA, Section 508, and EN 301 549, then scaffold a VPAT.
- **Carbon & Green-Software** (Add-on) — Estimate software carbon intensity with the ISO-standard
  SCI methodology and surface the efficiency hotspots.
- **Internationalization Readiness** (Add-on) — Flag hardcoded strings, locale and RTL handling, and
  un-externalized resources before localization begins.
- **Responsible-AI & Bias** (Add-on) — Audit ML components for bias, fairness, and explainability,
  and scaffold the model card.

### Deployment & Operations

- **Operations Monitor** (Add-on) — Analyze logs, latency, and error signals post-deployment,
  surfacing anomalies and predicting SLA breaches.
- **Incident Responder** (Add-on) — Correlate incident signals with recent deployments, recommend a
  targeted rollback or fix, and validate the resolution.
- **SOC 2** (Add-on) — Map controls to the AICPA Trust Services Criteria and assemble continuous,
  change-managed evidence.
- **SOX Change-Management** (Add-on) — Validate segregation of duties and change-approval evidence,
  producing an immutable release-approval trail.
- **Infrastructure-as-Code Analysis** (Add-on) — Detect Terraform, CloudFormation, and Kubernetes
  misconfigurations and drift, mapped to CIS, PCI, and SOC 2.
- **Cost & FinOps** (Add-on) — Estimate cloud cost from IaC, flag right-sizing and waste, and show
  the cost delta of each change.
- **Observability Readiness** (Add-on) — Check whether logs, metrics, and traces are instrumented,
  SLOs defined, and alert coverage adequate.
<!-- SPECTRA:GENERATED END id=agents-list-roadmap -->
