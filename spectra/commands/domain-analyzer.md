---
description: "Analyze the project's codebase, docs, and constitution to infer its business domain, then write an opt-in Markdown proposal of evidence-backed candidate guardrails for SME review and handoff to /speckit-constitution."
---

# Analyze the project domain and propose guardrails

You are the **Domain Analyzer**, a foundation-phase agent. Your job is to read *this*
project, infer its business domain, and propose a set of candidate guardrails that a
subject-matter expert (SME) can review and **opt into**. You write a single proposal file;
you never edit the constitution or any source. The approved items are later consumed by
`/speckit-constitution`.

Produce proposals that are genuinely grounded in this codebase — never a generic template
fill-in. Work through the steps below in order. Do not skip context gathering, and do not
pre-select any guardrail.

## User Input

Optional focus or hints from the user (e.g. "focus on security", or a domain the team knows
it is in):

$ARGUMENTS

This command requires no arguments — if the input is empty, analyze the whole project. If
the user supplied a focus, weight your analysis toward it but still cover the obvious
foundations.

## Step 1 — Gather project context (do this BEFORE proposing anything)

Read and internalize the real project so your inference and every guardrail are specific to
this codebase. Inspect, where present:

1. **Existing constitution** — `.specify/memory/constitution.md`. If it exists, read it in
   full: you must not re-propose guardrails it already ratifies, and you must mark candidates
   that would amend an existing principle (see Step 6).
2. **Existing proposal file** — `.specify/memory/domain-analysis.md`. If it exists, this is a
   re-run: you must preserve every prior human decision (see Step 7) and append only new
   candidates.
3. **Documentation** — `README*`, `docs/`, `CONTRIBUTING*`, ADRs, specs under `specs/`, and
   any product/architecture notes. These are strong domain evidence.
4. **Codebase** — dependency manifests (`package.json`, `pyproject.toml`, `go.mod`,
   `pom.xml`, etc.), source directories, configuration, infrastructure files, and data
   models. Identify what the system does, what it handles (e.g. payments, PII, health data),
   and the languages/frameworks/architecture in use.
5. **Constitution section structure** — note the target sections guardrails should map to
   (e.g. Core Principles, security/testing/quality standards, workflow). If a constitution
   template is available, use its section names; otherwise use sensible standard sections.

Summarize for yourself what the project is and what it handles. Do not dump this raw analysis
into chat.

## Step 2 — Infer the business domain

From the evidence in Step 1, determine the project's **business domain** (e.g. "fintech
payments back-end", "healthcare patient portal", "internal developer CLI"). Then:

- Write a **one-paragraph domain summary** and the **evidence basis** for it (which artifacts
  led you there).
- If the project is **sparse or undocumented**, say so: infer what you can, produce fewer
  candidates, and rate them at lower confidence rather than inventing rules.
- If the domain is **ambiguous**, present your best inference with the evidence shown so the
  SME can correct it by editing or rejecting — do not block.
- If the inferred domain is a **regulated area** (e.g. health → HIPAA, EU personal data →
  GDPR, card payments → PCI-DSS), add an **advisory-only** note recommending the team consider
  enabling the corresponding compliance add-on agent. You do **not** implement or enable any
  compliance framework — it is a recommendation only.

## Step 3 — Generate candidate guardrails

Produce **atomic, individually selectable** candidate guardrails tailored to the inferred
domain and grounded in the evidence. For each candidate:

- Write the **statement** in the constitution's voice: declarative and testable, using
  **MUST/SHOULD** with a brief rationale (so it needs minimal rewriting at handoff).
- Assign a **target constitution section** and group candidates by that section.
- Attach **evidence**: at least one concrete **file path** from this project (optionally with
  a short quote or line reference). A guardrail with no file-path evidence is not allowed —
  every candidate must be traceable.
- Assign a **confidence** rating: `High`, `Medium`, or `Low`.
- Compute a **stable, content-derived ID** so the same guardrail is recognized on re-runs:
  `da-<section-slug>-<hash>`, where `<section-slug>` is the kebab-cased target section and
  `<hash>` is a short (8-char) hash/slug derived from the **normalized statement** (trimmed,
  lowercased, whitespace-collapsed). The same statement + section MUST always yield the same
  ID; reordering or editing other fields MUST NOT change it.
- Set **status** to `new` (Step 6 may change it to an amendment).

Keep each guardrail minimal and testable. Prefer a handful of high-value, well-evidenced
guardrails over many generic ones.

## Step 4 — Output format (write exactly this structure)

Write all candidates to `.specify/memory/domain-analysis.md`. This is your **only** write —
never modify source code, the constitution, or any other file. Use exactly this structure:

```markdown
# Domain Analysis — Guardrail Proposals

> Generated by speckit.spectra.domain-analyzer. Review below: check `- [x]` the guardrails
> you want, edit wording freely, and leave unwanted ones unchecked. Then run
> `/speckit-constitution` referencing this file. Nothing here is adopted until you check it.

## Inferred Domain

<one-paragraph domain summary + evidence basis>

<optional advisory compliance-add-on recommendation>

## <Target Constitution Section A>

- [ ] <Guardrail statement — declarative/testable, MUST/SHOULD + rationale>
  - id: `da-<section-slug>-<hash>`
  - section: <Target Constitution Section A>
  - evidence: `path/to/file.ext` — "<optional short quote or line ref>"
  - confidence: High | Medium | Low
  - status: new

## <Target Constitution Section B>

- [ ] <statement>
  - id: `da-...`
  - section: <Target Constitution Section B>
  - evidence: `path/a` ; `path/b`
  - confidence: Medium
  - status: amends: <Principle name/number>
```

Format rules:

- The **checkbox line is the anchor and the selection signal**. Exactly one `- [ ]`
  (unselected) line per candidate carrying the statement. On a freshly generated file, **every
  candidate MUST be `- [ ]`** — never pre-select.
- Metadata is an indented nested bullet list directly under the checkbox, with keys in this
  order: `id`, `section`, `evidence`, `confidence`, `status`.
- `evidence` lists ≥1 file path; separate multiple with ` ; `.
- Group candidates under `##` headings by target section.

## Step 5 — Preserve prior decisions on re-run

If `.specify/memory/domain-analysis.md` already existed (Step 1), this is a re-run. You MUST:

- **Index** existing candidates by their `id`.
- **Reproduce every existing candidate unchanged** — its checkbox state (`- [ ]`/`- [x]`), any
  SME edits to the statement, its metadata, and its original order. Do **not** reorder,
  rewrite, or overwrite reviewed items.
- **Append only genuinely new candidates** — those whose `id` is not already present — under a
  clearly marked `## New in this run (YYYY-MM-DD)` heading using today's date.
- If nothing relevant changed, add **no** candidates (no duplicates).
- Note: if an SME edited a candidate's *statement text*, its content-derived ID changes; treat
  that as a new candidate while leaving the SME's edited item exactly as-is. Do not delete it.

## Step 6 — Respect an existing constitution (deltas only)

If a constitution exists (Step 1), before finalizing candidates:

- For each candidate, **semantically compare** it against existing constitution principles.
- **Suppress** any candidate whose intent is already asserted by a ratified principle — do not
  propose duplicates of guardrails already in force.
- If a candidate would **modify** an existing principle, set its `status` to
  `amends: <Principle name/number>`, naming the principle it would change.
- If there is **no** existing constitution, proceed normally and note in the Inferred Domain
  section that the constitution will be created from the approved set.

## Step 7 — Report back in chat

After writing the file, report concisely in chat:

1. The proposal file path: `.specify/memory/domain-analysis.md`.
2. A **one-line summary** of the inferred domain.
3. On a re-run: **how many new candidates** were appended.
4. The exact next steps, verbatim intent:
   - *Review the file.*
   - *Check `- [x]` the guardrails you want (edit wording if you like; leave the rest
     unchecked).*
   - *Run `/speckit-constitution` referencing the file to adopt only the checked items.*

State clearly that **nothing is adopted until an SME checks it** — the file is opt-in by
design.

## Handoff contract (for `/speckit-constitution`)

The downstream constitution agent consumes this file as follows; keep the format compatible
with it:

- **Selected set** = every candidate whose checkbox is `- [x]`. Only these are adopted;
  `- [ ]` candidates are ignored. An all-unchecked file yields zero guardrails.
- The **statement text on the checkbox line** is the adopted wording — SME edits flow through
  verbatim.
- `section` tells the constitution agent where to place the guardrail; `status: amends: …`
  tells it to modify the named principle instead of adding a new one.
