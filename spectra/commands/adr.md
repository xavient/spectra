---
description: "Create a context-aware Architecture Decision Record (ADR) grounded in the codebase, prior ADRs, and the project constitution."
---

# Create an Architecture Decision Record

You are helping the user capture an **Architecture Decision Record (ADR)**. Your job is to
produce an ADR that is genuinely relevant to *this* project — not a generic template fill-in.
Work through the steps below in order. Do not skip the context-gathering or the clarifying
questions.

## User Input

The user's description of the decision to record:

$ARGUMENTS

If this is empty, ask the user for a one or two sentence description of the decision before
continuing.

## Step 1 — Gather project context (do this BEFORE asking anything)

Read and internalize the relevant project context so your questions and the ADR itself are
specific to this codebase. Inspect, where present:

1. **Constitution** — `.specify/memory/constitution.md`. These are the governing principles.
   The ADR must be consistent with them (or explicitly acknowledge tension).
2. **Existing ADRs** — every `*.md` file under `Docs/ADR/`. Use these to:
   - understand decisions already made and the conventions/numbering in use,
   - avoid duplicating or silently contradicting a prior ADR,
   - detect if this new decision **supersedes** an existing one.
3. **Specifications and plans** — anything under `specs/` (spec.md, plan.md, research.md,
   data-model.md, contracts/, tasks.md) relevant to the area being decided.
4. **Source code** — locate and skim the parts of the codebase the decision actually touches
   (relevant modules, configs, dependency manifests like package.json / pyproject.toml /
   go.mod, infrastructure files). Ground your understanding in what exists today.

Summarize for yourself what the decision affects and where it sits relative to existing
decisions. Do not show this raw dump to the user unless it helps frame a question.

## Step 2 — Ask clarifying questions (maximum 5)

Ask the user **up to 5** clarifying questions, and no more. Fewer is better — only ask what
you genuinely cannot determine from Step 1.

- Each question must be specific to this project and informed by the context you gathered
  (reference the actual modules, prior ADRs, or constitution principles involved).
- Skip anything the description or the codebase already answers.
- Prioritize questions that change the *substance* of the decision: alternatives considered,
  constraints, scope/boundaries, migration impact, and reversibility.
- Present the questions, then wait for the user's answers before drafting. If the user
  declines to answer some, proceed with reasonable, clearly-stated assumptions.

## Step 3 — Determine the ADR number and location

- Ensure the directory `Docs/ADR/` exists at the project root; create it if it does not.
- Scan `Docs/ADR/` for existing files named `ADR-NNN-*.md` and find the highest `NNN`.
- The new number is that value + 1, zero-padded to **three digits** (e.g. `001`, `002`, `017`).
  If no ADRs exist yet, start at `001`.

## Step 4 — Draft the ADR

Write the ADR using **exactly** this template and section structure. Do not add, rename, or
reorder sections.

```
# ADR-NNN: [Title]

**Date:** YYYY-MM-DD

**Status:** Proposed | Accepted | Deprecated | Superseded

## Context

What is the issue or problem that motivates this decision?

## Decision

What is the change that we're proposing and/or doing?

## Consequences
What becomes easier or harder as a result of this decision?
```

Filling rules:
- **NNN** — the zero-padded number from Step 3.
- **Title** — a short, descriptive title in title case.
- **Date** — today's date in `YYYY-MM-DD` format.
- **Status** — set to `Proposed` for a new ADR. Keep the other options out of the final file;
  only the chosen status remains on the line (e.g. `**Status:** Proposed`).
- **Context** — ground this in the real problem, referencing the relevant code/specs/prior ADRs
  you found. Capture the user's answers from Step 2.
- **Decision** — state the concrete decision clearly and unambiguously.
- **Consequences** — be honest about both the benefits and the trade-offs / things that get
  harder.
- If this decision supersedes an existing ADR, say so in Context, and after writing the new
  file, update the superseded ADR's status line to `Superseded` (referencing the new number).

## Step 5 — Write the file

Create the file at:

```
Docs/ADR/ADR-NNN-<kebab-case-title>.md
```

where `<kebab-case-title>` is the title lowercased with spaces replaced by hyphens and special
characters removed (e.g. `ADR-003-adopt-postgres-for-primary-store.md`).

Show the user the path you created and a short summary of the ADR.

## Step 6 — Check the ADR against the constitution (your recommendation)

Compare the decision against `.specify/memory/constitution.md` and decide whether this is a
**significant** ADR. Treat it as significant if it does any of the following:

- introduces or changes a cross-cutting standard or principle (e.g. a default tech choice,
  a security/testing/quality bar, an architectural boundary),
- contradicts, narrows, or extends an existing constitution principle,
- establishes a convention future work is expected to follow.

Then:

- **If significant:** explicitly recommend to the user that the constitution be updated, and
  state *what* you would add or change (quote the specific principle text you propose). Offer
  to make the edit. Only modify `.specify/memory/constitution.md` if the user agrees. The
  recommendation must come from you — do not wait to be asked.
- **If not significant:** briefly note that the ADR does not warrant a constitution change and
  why, then continue.

## Step 7 — Suggest committing the ADR (optional, do not run automatically)

Do **not** run git commands yourself. Instead, present them as an optional suggestion the user
can copy. Tailor the message and the file list to what you actually changed (include the
constitution file only if it was edited):

```bash
git add Docs/ADR/ADR-NNN-<kebab-case-title>.md
git commit -m "docs(adr): ADR-NNN <title>"
```

If a constitution update was made, suggest staging that file in the same commit. Make clear
this step is optional and the user can adjust the branch, message, or scope as they prefer.
