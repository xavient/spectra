# Impact Analysis: [FEATURE NAME]

<!--
  HOW TO USE THIS TEMPLATE
  - This document is produced by `speckit.spectra.impact` before any specification work begins. A
    Business Analyst takes it to stakeholders for a go / no-go decision.
  - Fill every [PLACEHOLDER]. Delete any section that genuinely does not apply — remove it entirely
    rather than leaving "N/A". The command honours what this template says: a section you delete stays
    deleted, and the command notes the omission instead of putting it back.
  - What this template CANNOT change: every finding carries a citation, every finding carries a
    confidence level, the rating comes from the trigger table, no secret value is ever reproduced, and
    coverage is always stated. Those rules live in the command, not here.
  - HTML comments like this one are guidance and are stripped from the output.
-->

## Change statement

<!-- One line, restated by the agent so a reader can catch a misread of the intent. -->

## Inputs

<!--
  What the analysis was asked, verbatim, plus every document supplied and whether it was read. This is
  how two reports on the same feature are told apart.
-->

**Feature intent as supplied:**

> [VERBATIM INTENT]

**Supporting documents:**

| Document | Read? | Note |
|---|---|---|
| [path] | read / unreadable / missing / unsupported | [reason where not read] |

## Impact rating

<!-- High | Medium | Low, followed by the trigger that produced it. Not a judgement — a lookup. -->

**[HIGH / MEDIUM / LOW]** — [which trigger fired]

## Findings

<!--
  The five core lenses always appear. The two conditional ones appear only when their trigger fired;
  delete them otherwise rather than leaving them empty.
  Every item: a statement, a `path/to/file.ext:line` citation, and a confidence level.
-->

### 1. Blast radius

- [Finding] `path/to/file.ext:142` · `confirmed`

### 2. Data

### 3. Behavioural change

### 4. Risk & reversibility

### 5. Effort & sequencing

<!-- Coupling depth, not an estimate. Say so. -->

### Security & privacy

<!-- Only when the trigger fired. Flag and route; never judge. -->

Routed to: `speckit.spectra.[agent]`

### Compliance

<!-- Only when the project's guardrails declare a regime. Flag and route; never judge. -->

Routed to: `speckit.spectra.[agent]`

## External contract changes — human verification required

<!-- Every public API, event schema, database table, or shared contract that changes. Always populated
     when one changes, regardless of what the scan found internally. -->

| Contract | Change | Verify with | Status |
|---|---|---|---|

## Human follow-up required

<!--
  The questions a repository cannot answer: stakeholders, change management and training, support model,
  vendor and licensing cost, organizational process change. Flagged, never written about.
-->

## Open risks and rollback

**Rollback path:**

**Becomes irreversible at:**

## Clarifications

| # | Question | Answer | Source |
|---|---|---|---|
| 1 | [question] | [answer] | user / **defaulted** |

## Assumptions and unknowns

<!-- Including every defaulted answer, tagged. The standing limitations belong here too. -->

- Systems outside what was scanned were not analyzed.
- Coupling expressed neither in imports nor in string literals may not have been detected.

## Sources consulted

<!--
  The section that lets a reviewer tell "checked and found nothing" from "did not check". Per system:
  files read of files present, and how they were selected. Then the scan mode, every cap that bound, and
  the terms that were searched for and produced nothing.
-->

**[system]** ([form]): [n] of [total] files, selected by [method].

**Scan mode:** [spec-informed / source-only] — [what was read to orient].

**Caps reached:** [which, and what it cut].

**Searched for and not found:** [terms with zero hits — a finding, not an absence].
