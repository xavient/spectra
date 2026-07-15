# Contract: BRD Output File

Defines the artifact the command writes and the handoff contract to `/speckit-specify`. A file that
does not satisfy this contract is a defect.

## Location & filename

- **Folder**: `/brds` at the project root (created on first run).
- **Filename**: `NNN-<kebab-title>.md` where:
  - `NNN` = zero-padded, three-digit sequential number = (highest existing `NNN` under `/brds`) + 1,
    starting at `001` when none exist.
  - `<kebab-title>` = the BRD title, lowercased, spaces → hyphens, special characters removed.
  - Example: `003-brd-generator.md`.
- **No overwrite**: if a target name would collide, the command still selects the next unused `NNN`; an
  existing BRD is never overwritten.

## Structure

The file MUST reproduce the shipped template's sections, in order, with no leftover guidance comments
or `[PLACEHOLDER]` tokens:

1. `# Business Requirements Document (BRD): <Title>`
2. **Document Control** table
3. `## 1. Executive Summary`
4. `## 2. Business Context & Problem Statement`
5. `## 3. Business Objectives & Goals`
6. `## 4. Stakeholders & Users`
7. `## 5. Scope` (`### 5.1 In Scope`, `### 5.2 Out of Scope`)
8. `## 6. User Journeys` **(specify-ready — see below)**
9. `## 7. Business Requirements`
10. `## 8. Success Metrics & Measurable Outcomes`
11. `## 9. Assumptions`
12. `## 10. Constraints`
13. `## 11. Dependencies`
14. `## 12. Risks & Mitigations`
15. `## 13. Open Questions`
16. `## 14. Glossary`

Sections that genuinely do not apply are removed entirely (not left as "N/A").

## Document Control (auto-populated)

| Field | Rule |
|-------|------|
| BRD ID | `BRD-NNN` (same number as filename) |
| Title | derived from the requirement |
| Author | project/team from context (constitution author / Git config / repo metadata); `[team]` placeholder fallback |
| Status | `Draft` |
| Version | `0.1.0` |
| Created / Last updated | today (`YYYY-MM-DD`) |
| Related documents | links to relevant context when present |

## Specify-ready User Journeys (Section 6) — the handoff contract

This is the section `/speckit-specify` consumes as prioritized user stories, so it MUST be the
strongest part of the document:

- Each journey MUST be **independently valuable and testable** (an MVP slice on its own).
- Journeys MUST be **prioritized** (P1 = most critical, then P2, P3…).
- Each journey MUST include: **Actor**, **Trigger**, **Outcome/value**, a step-by-step **Flow**, and at
  least one **Given/When/Then** acceptance.
- Genuine unknowns belong in **Section 13 (Open Questions)**, never as invented journey detail.

Consumption expectation: running `/speckit-specify` with this file yields a spec whose prioritized user
stories correspond one-to-one to these journeys (same priorities, same acceptance intent) — the
verifiable outcome for SC-003 / User Story 3.

## Provenance rules

- Every requirement/journey/objective MUST be traceable to the supplied requirement or a clarifying
  answer (FR-006). Project context may inform wording and dedup, but MUST NOT introduce scope.
- Stated defaults the command adopted MUST appear under **Assumptions**; genuine unknowns under **Open
  Questions**.
