# Phase 1 — Data Model

Three models: the roster document, the installation state the project-scoped commands classify into, and
the generated-document model. Field-level validation rules trace to the FR they come from.

---

## 1. The roster document — `agents-list.json`

```json
{
  "schema_version": "1.0",
  "phases": [
    { "id": "foundation", "title": "Foundation", "aidlc": "Inception" }
  ],
  "agents": [
    {
      "id": "adr",
      "title": "Architecture Decision Records (ADR)",
      "description": "Create a context-aware ADR grounded in the codebase, prior ADRs, and the constitution.",
      "status": "available",
      "phase": "architecture-design",
      "type": "add-on",
      "provider": "spectra",
      "command": "speckit.spectra.adr"
    }
  ]
}
```

### Top-level fields

| Field | Type | Required | Rules | Source |
| --- | --- | --- | --- | --- |
| `schema_version` | string | yes | `"MAJOR.MINOR"`. Starts at `"1.0"`. Additive change bumps MINOR; reader-invalidating change bumps MAJOR. | FR-009 |
| `phases` | array | yes | Non-empty. Array order **is** phase presentation order. Ids unique. | FR-008 |
| `agents` | array | yes | Non-empty. Array order **is** presentation order within a phase. Ids unique. | FR-008 |

No `updated_at` field — see research decision 1.

### `phases[]`

| Field | Type | Required | Rules |
| --- | --- | --- | --- |
| `id` | string | yes | Lowercase slug, `[a-z0-9-]+`, unique. |
| `title` | string | yes | Display text for the SDLC phase, e.g. `Requirements & Discovery`. |
| `aidlc` | string | yes | One of `Inception`, `Construction`, `Operation`. Applies to every agent in the phase (FR-003, normalized — research decision 2). |

### `agents[]`

| Field | Type | Required | Rules | Source |
| --- | --- | --- | --- | --- |
| `id` | string | yes | Lowercase slug `[a-z0-9-]+`, unique across `agents`. The machine handle for prose matching, manifest cross-checks, and generated anchors. Never derived from `title`. | FR-003, FR-003a |
| `title` | string | yes | Display text. Exactly one per agent, used identically everywhere. Free to change without touching `id`. | FR-003, FR-003b, FR-010 |
| `description` | string | yes | **Single line.** No newline character permitted; verified by `--check`. | FR-003, FR-004 |
| `status` | enum | yes | `available` \| `planned`. | FR-003, FR-005 |
| `phase` | string | yes | Must match a `phases[].id`. | FR-003 |
| `type` | enum | yes | `core` \| `add-on`. Orthogonal to `provider` — `create-pr` is `core` and Spectra-provided. | FR-003 |
| `provider` | enum | yes | `spectra` \| `speckit`. Only `spectra` entries are installed, updated, or versioned by Spectra. | FR-003, FR-006 |
| `command` | string | conditional | Present iff `status == "available"`. Absent — not empty, not null — when `planned`. | FR-007 |

### Derived, never stored

- **AI-DLC phase per agent** — from `phases[].aidlc` via `phase`.
- **Status glyph** (`✅` / `🚧`) — a rendering concern owned by the generator and the CLI, not data.
- **Installed-here marker** — computed at run time by intersecting `provider == "spectra"` entries with
  the project's installation state (FR-048).

### Validation rules enforced by `--check`

1. Every required field present, every enum in range (FR-003).
2. `id` unique and slug-shaped; `phase` resolves to a known phase (FR-003a).
3. `description` contains no newline (FR-004).
4. `command` present iff `available` (FR-007).
5. The set of `provider == "spectra"` **and** `status == "available"` ids equals the set of commands in
   `spectra/extension.yml`, and each such entry's `command` string matches the manifest's registered
   command exactly. Descriptions are explicitly **not** compared (FR-019, FR-019a).
6. Every `provider == "spectra"`, `status == "available"` id has a prose anchor in `AGENTS_LIST.md`, and
   no anchor exists for an id outside that set (FR-018).

### Presentation order

`phases` order, then `agents` array order within each phase. One array, one order, consumed identically
by the generator and by `spectra agent-list` — which is what makes FR-008 checkable rather than
aspirational.

---

## 2. The agent id map — all 44 entries

The authoritative content to be written at implement time. Titles are taken from the README Agents table,
which is the wording already public. **44 entries: 13 available (4 Spectra, 9 Spec Kit), 31 planned.**

### Foundation — Inception

| id | Title | Type | Status | Provider | Command |
| --- | --- | --- | --- | --- | --- |
| `constitution` | Guardrails | core | available | speckit | `speckit.constitution` |
| `domain-analyzer` | Domain Analyzer | add-on | available | spectra | `speckit.spectra.domain-analyzer` |
| `fda-part-11-iec-62304` | FDA 21 CFR Part 11 & IEC 62304 | add-on | planned | spectra | — |
| `iso-27001-27701` | ISO 27001 / 27701 | add-on | planned | spectra | — |

### Requirements & Discovery — Inception

| id | Title | Type | Status | Provider | Command |
| --- | --- | --- | --- | --- | --- |
| `specify` | Requirements Analyst | core | available | speckit | `speckit.specify` |
| `brd` | BRD Generator | add-on | available | spectra | `speckit.spectra.brd` |
| `clarify` | Clarifier | add-on | available | speckit | `speckit.clarify` |
| `checklist` | Requirements Quality | add-on | available | speckit | `speckit.checklist` |
| `gdpr` | GDPR Compliance | add-on | planned | spectra | — |
| `canadian-privacy` | Canadian Privacy — PIPEDA / PHIPA / Law 25 | add-on | planned | spectra | — |
| `eu-ai-act` | EU AI Act & Responsible-AI Governance | add-on | planned | spectra | — |
| `legal-obligation-extraction` | Legal-Obligation Extraction | add-on | planned | spectra | — |

### Architecture & Design — Construction

| id | Title | Type | Status | Provider | Command |
| --- | --- | --- | --- | --- | --- |
| `plan` | Architecture Planner | core | available | speckit | `speckit.plan` |
| `adr` | Architecture Decision Records (ADR) | add-on | available | spectra | `speckit.spectra.adr` |
| `architecture-reviewer` | Architecture Reviewer | add-on | planned | spectra | — |
| `hipaa` | HIPAA Compliance | add-on | planned | spectra | — |
| `pci-dss` | PCI-DSS | add-on | planned | spectra | — |
| `threat-modeling` | Threat Modeling | add-on | planned | spectra | — |
| `performance-scalability` | Performance & Scalability | add-on | planned | spectra | — |
| `data-governance` | Data Governance & Privacy Engineering | add-on | planned | spectra | — |
| `api-design-contract` | API Design & Contract | add-on | planned | spectra | — |

### Planning — Construction

| id | Title | Type | Status | Provider | Command |
| --- | --- | --- | --- | --- | --- |
| `tasks` | Task Planner | core | available | speckit | `speckit.tasks` |
| `analyze` | Consistency | add-on | available | speckit | `speckit.analyze` |

### Implementation — Construction

| id | Title | Type | Status | Provider | Command |
| --- | --- | --- | --- | --- | --- |
| `implement` | Implementation | core | available | speckit | `speckit.implement` |
| `dependency-supply-chain` | Dependency & Supply-Chain | add-on | planned | spectra | — |
| `database-data-layer` | Database & Data-Layer | add-on | planned | spectra | — |
| `documentation-quality` | Documentation Quality | add-on | planned | spectra | — |
| `technical-debt` | Technical-Debt & Maintainability | add-on | planned | spectra | — |

### Testing & Quality — Construction

| id | Title | Type | Status | Provider | Command |
| --- | --- | --- | --- | --- | --- |
| `testing` | Testing | core | available | speckit | `speckit.implement` |
| `test-coverage` | Test Coverage Analyst | add-on | planned | spectra | — |
| `test-automation` | Test Automation Analyst | add-on | planned | spectra | — |
| `security-analyst` | Security Analyst | add-on | planned | spectra | — |
| `accessibility-wcag` | Accessibility & WCAG Compliance | add-on | planned | spectra | — |
| `carbon-green-software` | Carbon & Green-Software | add-on | planned | spectra | — |
| `i18n-readiness` | Internationalization Readiness | add-on | planned | spectra | — |
| `responsible-ai-bias` | Responsible-AI & Bias | add-on | planned | spectra | — |

### Deployment & Operations — Operation

| id | Title | Type | Status | Provider | Command |
| --- | --- | --- | --- | --- | --- |
| `create-pr` | GitHub (PR) | core | available | spectra | `speckit.spectra.create-pr` |
| `operations-monitor` | Operations Monitor | add-on | planned | spectra | — |
| `incident-responder` | Incident Responder | add-on | planned | spectra | — |
| `soc-2` | SOC 2 | add-on | planned | spectra | — |
| `sox-change-management` | SOX Change-Management | add-on | planned | spectra | — |
| `iac-analysis` | Infrastructure-as-Code Analysis | add-on | planned | spectra | — |
| `cost-finops` | Cost & FinOps | add-on | planned | spectra | — |
| `observability-readiness` | Observability Readiness | add-on | planned | spectra | — |

**Two entries deserve a note.**

`testing` is available but has no command of its own — Spec Kit runs it inside `speckit.implement`.
Its `command` is therefore `speckit.implement`, which is what a user actually runs. This is accurate
rather than invented, so FR-007 is satisfied; two entries sharing a command is harmless because the
manifest cross-check (rule 5) only looks at `provider == "spectra"` entries.

`create-pr` resolves the three-way name disagreement FR-010 calls out: `id: create-pr`,
`title: GitHub (PR)`. The `github` heading form in `AGENTS_LIST.md` and the bare `GitHub` are both retired.

---

## 3. Installation state

The single classification every project-scoped command branches on. Computed once per invocation.

```text
NOT_A_PROJECT   no ancestor directory contains .specify/
NOT_INSTALLED   project found; .specify/extensions/spectra/ absent
INCOMPLETE      folder present; extension.yml missing, unreadable, or carries no version
INSTALLED       folder present; extension.yml readable with a parsed version
```

### Transitions

```text
NOT_A_PROJECT ──(specify init, offered by `spectra check`)──> NOT_INSTALLED
NOT_INSTALLED ──(install flow, offered by `spectra check`)──> INSTALLED
INSTALLED     ──(spectra update)──────────────────────────> INSTALLED (version advanced)
INSTALLED     ──(spectra uninstall)───────────────────────> NOT_INSTALLED
INCOMPLETE    ──(spectra update / re-install)─────────────> INSTALLED
```

### Fields carried alongside

| Field | Type | Notes |
| --- | --- | --- |
| `state` | enum | One of the four above. |
| `project_root` | path or None | Nearest ancestor containing `.specify/`. `None` when `NOT_A_PROJECT`. |
| `installed_version` | string or None | Populated only when `INSTALLED`. |

Each state maps to exactly one message per command, which is what SC-009 measures. Full message and
exit-code matrix in [`contracts/cli-surface.md`](contracts/cli-surface.md).

### Version comparison

Reuses `version.compare_versions()` from `spectra_cli/version.py` — already component-wise, already
tolerant of a leading `v`, already treats an unparseable version as sorting below any real one. Three
verdicts: `up_to_date`, `out_of_date`, `ahead`. All three exit 0 (FR-032a).

---

## 4. Generated-document model

| Entity | Identity | Owner | Rules |
| --- | --- | --- | --- |
| Generated region | `id` in its start marker | generator | Rewritten in full on every run. Byte-identical across runs (FR-016). Missing or malformed marker is a hard error naming file and marker (FR-020). |
| Prose block | `id` in its `SPECTRA:AGENT` anchor | human | Never read, never written, never parsed for content by the generator — only its anchor's existence is checked (FR-013, FR-018). |
| Hand-authored surroundings | — | human | Byte-identical after any generator run (FR-015). |

Three regions exist, all with fixed ids:

| Region id | File | Content |
| --- | --- | --- |
| `readme-agents-table` | `README.md` | The Agents table, plus the sentence naming which ✅ agents are Spec Kit's rather than Spectra's. |
| `agents-list-speckit-core` | `AGENTS_LIST.md` | The Spec Kit core agents section body. |
| `agents-list-roadmap` | `AGENTS_LIST.md` | The Roadmap section body, grouped by phase, planned entries only. |

Marker syntax and anchor placement: [`contracts/generated-regions.md`](contracts/generated-regions.md).
