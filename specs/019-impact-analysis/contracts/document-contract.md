# Contract — The Document

The shape of what the command writes, and the boundary between what a project may reshape and what it may not.

## Location

```text
<artifact-root>/impact-analysis/NNN-<name>.md
```

Default: `docs/impact-analysis/`. Lowercase, project-relative, created on demand, one artifact type in it
(FR-049).

### Root resolution, in order

1. **Declared root wins.** A line reading `Artifact root: <folder>/` in `.specify/memory/constitution.md`,
   matched case-insensitively. Reject a value with a leading `/` or a `..` segment, say why, fall back to the
   default.
2. **Otherwise `docs/`, after a publication check.** Signals: `mkdocs.yml`, `docusaurus.config.*`,
   `docs/_config.yml`, `docs/.nojekyll`, `docs/index.html`, `docs/conf.py`, or a Pages configuration pointing
   at `docs`.
3. **Signal found and no declared root**: raise it, recommend `documents/`, ask. The question is about where to
   write, so it does not count against the five. No answer obtainable → `documents/`, and say so.
4. **Offer the declaration line, never write it.** Show the user
   `Artifact root: documents/` and let them add it.

An impact analysis names internal systems, owning teams, unmitigated risks, and where secrets live. Publishing
one accidentally is worse than misfiling it, so where the choice cannot be obtained the non-publishing option
wins.

### Numbering

`NNN` is **one greater than the highest number already in the folder** — not a count of the files there, so a
deleted or archived analysis cannot cause a collision. `001` in an empty folder. Independent of the `specs/`
sequence. Resolved at write time, so an interrupted run consumes nothing (FR-050, FR-051a).

`<name>` is kebab-case, derived per run from the intent and any attachments, and is **the same string as the
front-matter `feature_slug`** — one value in two places. Not stable across runs (FR-050, FR-053).

## Template resolution

Five layers, first **readable and non-empty** wins — not merely the first that exists:

1. `.specify/templates/overrides/impact-analysis-template.md` — the project's override. Wins outright.
2. `.specify/presets/<preset-id>/templates/impact-analysis-template.md` — any installed preset, in registry
   priority order.
3. `.specify/extensions/spectra/templates/impact-analysis-template.md` — shipped with this extension.
4. `.specify/templates/impact-analysis-template.md` — a core template, if the project keeps one.
5. The **inline skeleton** at the end of the command file — last resort, for a project with no `.specify/`.

A layer that is present but empty or unreadable is reported in one line and skipped. A template is input and is
never edited. The resolved path is reported (FR-057 to FR-060).

**Registration**: `spectra/templates/impact-analysis-template.md`, declared in `spectra/extension.yml` under
`provides.templates` with `name`, `file`, and `description` (FR-058).

**The supported customization point is layer 1.** It is committed, applies to the team, sits outside the
extension tree, and survives `specify extension update`. Editing the installed copy under `.specify/extensions/`
is not the customization path — extension files are replaced wholesale on update.

## Front matter

```yaml
---
id: 003
feature_slug: cart-abandonment-recovery
title: Cart abandonment recovery
status: draft                     # always draft when written
impact: high                      # high | medium | low
generated: 2026-09-03T20:41:12-07:00
author: A. Bahaloo                # empty rather than invented
supersedes: 001
superseded_by: null
scan_mode: spec-informed          # spec-informed | source-only
systems_scanned:
  - name: checkout-api
    form: project
    coverage: 62/1400 files
  - name: notifications-svc
    form: local-path
    path: ../notifications-svc
    coverage: 14/380 files
systems_declared_not_scanned:
  - name: billing-service
    owner: Payments team
    form: free-text
    reason: no local copy
questions_asked: 4
questions_defaulted: 1
caps_overridden:
  - identifier-cap: 80
---
```

`status` is always `draft` on write (FR-053a). `generated` carries the time of day and zone so two runs on one
date are distinguishable (FR-052). There is **no `spec_refs` key, in any form** (FR-052, FR-054).

## Sections

Order comes from the resolved template. The shipped template ships these, in this order:

| # | Section | Must contain |
|---|---|---|
| 1 | Change statement | One line, restated by the command so a misread is catchable (FR-061) |
| 2 | Inputs | The intent verbatim; every attachment by name with `read` / `unreadable` / `missing` / `unsupported` (FR-052a) |
| 3 | Impact rating | The rating and the trigger that produced it (FR-047) |
| 4 | Findings | Five core lenses; conditional sections only when their trigger fired (FR-036, FR-039) |
| 5 | External contract changes | One row per contract, what changes, who verifies, status (FR-043) |
| 6 | Human follow-up required | The excluded lenses that look relevant — flagged, never written about (FR-040) |
| 7 | Open risks and rollback | Rollback path; the point at which the change becomes irreversible (FR-061) |
| 8 | Clarifications | Question, answer, and `user` or `defaulted` per row (FR-035) |
| 9 | Assumptions and unknowns | Every defaulted answer tagged `defaulted — not confirmed`; the standing limitations (FR-033) |
| 10 | Sources consulted | Coverage per system, scan mode, caps reached and what they cut, terms searched and not found (FR-044, FR-048) |

A banner precedes section 1 when three or more answers were defaulted (FR-066).

## What an override may and may not change

**May**: drop a section, rename a heading, reorder, add one of its own, change wording. Including dropping a
lens — the command notes the omission and does not reinstate it (FR-060).

**May not**, because these live in the command and not the template:

| Rule | Requirement |
|---|---|
| Every finding cited, or cited as an evidenced absence | FR-042 |
| Confidence level on every finding, from the fixed mapping | FR-046 |
| No secret value reproduced anywhere | FR-042a |
| Rating derived from triggers, with the trigger named | FR-047 |
| No claim of absence of impact | FR-041 |
| External contract change always escalates | FR-043 |
| Coverage stated, caps disclosed | FR-044, FR-045 |
| No compliance verdict or certification claim | FR-038 |

An override that removes *Sources consulted* removes the section; the coverage statement still appears in the
session. This is the division `review-template` already records in the manifest — the revision anchor, the
AI-assisted disclosure, and the coverage statement stay with the command.
