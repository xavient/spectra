# Phase 1 Data Model: Domain Analyzer

The "data" here is the content of the single proposal artifact the command produces, not a
database. Entities below define the logical fields each artifact element must carry; the
on-disk rendering is specified in [contracts/proposal-file.md](./contracts/proposal-file.md).

## Entity: Proposal File

The single Markdown artifact at `.specify/memory/domain-analysis.md`.

| Field | Description | Source / Rule |
|-------|-------------|---------------|
| Domain summary | One-paragraph inferred business domain + evidence basis | FR-002; shown in chat too (FR-007) |
| Compliance note (optional) | Recommendation to enable a compliance add-on, advisory only | FR-014, D9 — present only when domain suggests it |
| Candidate groups | Candidates grouped under `##` headings by target constitution section | FR-013 |
| New-in-run group | Candidates added on the latest re-run, date-stamped | FR-011, D7 |

**Rules**
- Exactly one such file per project; create on first run, preserve-and-append on re-run (D7).
- The command's only write target (FR-010). Never writes elsewhere.
- On a fresh file, no candidate is checked (FR-005).

## Entity: Candidate Guardrail

An atomic, individually selectable proposed rule (FR-003).

| Field | Type | Required | Description / Rule |
|-------|------|----------|--------------------|
| `id` | string | yes | Content-derived stable ID — slug/hash of normalized statement + target section (D5). Stable across re-runs. |
| `statement` | string | yes | Declarative, testable guardrail in the constitution's voice (MUST/SHOULD + rationale) (FR-004, FR-012). Rendered as the checkbox line text. |
| `selected` | boolean | yes | Selection state. Defaults to **false** / `- [ ]` on creation (FR-005). Set by the SME. |
| `target_section` | string | yes | Which constitution section the guardrail belongs to (FR-004, FR-013). |
| `evidence` | list<EvidenceRef> | yes (≥1) | Why this guardrail applies — see Evidence Reference (FR-004, SC-002). |
| `confidence` | enum | yes | `High` \| `Medium` \| `Low` (spec Assumptions). Lower when evidence is sparse (edge case). |
| `status` | enum | yes | `new` \| `amends:<Principle>`. `amends` names the existing principle it would change (FR-009, D8). |

**Rules**
- Each candidate maps to exactly one target section.
- `evidence` MUST contain at least one reference (SC-002 — 100% traceable).
- An already-ratified guardrail (intent already in the constitution) MUST NOT appear (FR-009/D8).
- Identity for re-run preservation is `id` only (D5/D7).

## Entity: Evidence Reference

A single pointer to the project artifact that justifies a candidate.

| Field | Type | Required | Description / Rule |
|-------|------|----------|--------------------|
| `path` | string (file path) | yes | Concrete path to a real project file (spec clarification Q3). |
| `quote_or_lines` | string | no | Optional short quote or line reference for fast SME verification. |

**Rules**
- `path` must reference an artifact that actually exists in the analyzed project.
- Free-form prose ("the project seems to…") is not valid evidence — a path is required.

## Entity: Domain Inference

The agent's determination of the business domain (FR-002).

| Field | Description |
|-------|-------------|
| `domain` | Best-inference label/phrase for the business domain |
| `evidence_basis` | The artifacts/signals that justify the inference |
| `confidence_note` | Stated lower confidence when the project is sparse or the domain is ambiguous (edge cases) |

## State & Lifecycle

```text
(no file)
   │  first analyze run
   ▼
Proposal File created ── all candidates selected=false ───────────────┐
   │                                                                   │
   │  SME review (external edit): check / edit wording / leave blank   │
   ▼                                                                   │
Reviewed Proposal File                                                 │
   │  re-run analyze: index by id, keep reviewed items verbatim,       │
   │  append only new ids in a dated group  ◄───────────────────────────┘
   ▼
/speckit-constitution consumes ONLY selected==true candidates (handoff)
```

- Selection transitions are made by humans editing the file; the command never sets
  `selected=true` (FR-005, SC-006).
- Re-run never mutates an existing candidate's `selected`, `statement`, or order (FR-011).
