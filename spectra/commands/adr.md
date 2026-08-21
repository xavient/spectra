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
   The ADR must be consistent with them (or explicitly acknowledge tension). Also read it for the
   **artifact root** — see the next item.
2. **The artifact root** — where this project keeps generated documents. Resolve it before you look for
   anything else, because every path below hangs off it:
   - **Declared root wins.** If the constitution contains a line reading `Artifact root: <folder>/`
     (match case-insensitively), use that folder. It MUST be project-relative — reject a value with a
     leading `/` or a `..` segment, say why, and fall back to the default.
   - **Otherwise the default is `docs/`** — but check first whether `docs/` is a **published site
     source** in this project. Signals: `mkdocs.yml`, `docusaurus.config.*`, `docs/_config.yml`,
     `docs/.nojekyll`, `docs/index.html`, `docs/conf.py`, or a GitHub Pages configuration pointing at
     `docs` (Pages' only non-root branch source is `/docs`).
   - **If you find a signal and no declared root**, raise it with the user before writing: writing to
     `docs/adr/` would publish the ADR on their site or add it to a generated documentation build.
     Recommend `documents/` and ask which they want. This question is about *where to write*, not about
     the decision, so it does not count against the five in Step 2. If you cannot get an answer, use
     `documents/` and say so — a file in the wrong private folder is one `git mv` away, a published one
     cannot be recalled from caches or forks.
   - **Offer the declaration; never write it.** Whatever root is chosen, show the user the line that
     makes it permanent for every Spectra agent, and let them add it themselves:

     ```text
     Artifact root: documents/
     ```

     Until that line exists you will ask again on the next run. Do **not** edit
     `.specify/memory/constitution.md` for this — the only constitution change you may propose is the
     one in Step 6, about the decision itself.
   - From here on, `<artifact-root>/adr/` is this project's ADR folder — `docs/adr/` unless the root was
     declared or changed above.
3. **Existing ADRs** — every `*.md` file under `<artifact-root>/adr/`. Use these to:
   - understand decisions already made and the conventions/numbering in use,
   - avoid duplicating or silently contradicting a prior ADR,
   - detect if this new decision **supersedes** an existing one.

   **Also check the locations earlier runs used.** Extension versions before 1.6.0 wrote ADRs to
   `Docs/ADR/` — compare case-insensitively, since on macOS `Docs/ADR/` may already resolve to
   `docs/ADR/`. And if the root was declared as something other than `docs/`, check `docs/adr/` too.
   Read any you find, for exactly the same purposes and for the numbering in Step 3. Treat them as
   **read-only**: you never move, rename, modify, or delete anything in them.
4. **Specifications and plans** — anything under `specs/` (spec.md, plan.md, research.md,
   data-model.md, contracts/, tasks.md) relevant to the area being decided.
5. **Source code** — locate and skim the parts of the codebase the decision actually touches
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

- Ensure the directory `<artifact-root>/adr/` exists at the project root; create it if it does not. With
  the default root that is `docs/adr/`. The path is **project-relative and lowercase** — not `Docs/ADR/`,
  not `/docs/adr/`.
- Scan `<artifact-root>/adr/` for existing files named `ADR-NNN-*.md` and find the highest `NNN`.
- If Step 1 found ADRs in an earlier location (`Docs/ADR/`, or `docs/adr/` when the root is declared
  elsewhere), scan those the same way and take the **highest `NNN` across every folder**, so the decision
  log keeps one continuous sequence across the move.
- The new number is that value + 1, zero-padded to **three digits** (e.g. `001`, `002`, `017`).
  If no ADRs exist anywhere, start at `001`.

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
  **Exception:** if the superseded ADR lives in one of the earlier locations from Step 1 (a legacy
  `Docs/ADR/`, or `docs/adr/` when the root is declared elsewhere), do not edit it there — those folders
  are read-only. Record the supersession in the new ADR's Context and tell the user which file to update
  once they move it.

## Step 5 — Write the file

Create the file at:

```
<artifact-root>/adr/ADR-NNN-<kebab-case-title>.md
```

which with the default root is:

```
docs/adr/ADR-NNN-<kebab-case-title>.md
```

where `<kebab-case-title>` is the title lowercased with spaces replaced by hyphens and special
characters removed (e.g. `ADR-003-adopt-postgres-for-primary-store.md`).

Show the user the path you created and a short summary of the ADR.

**If Step 1 found ADRs in an earlier location**, say so once, in one short note — and no more than once
per run:

- state where ADRs live now and that this ADR was written there,
- confirm you left the earlier folder untouched,
- offer the move as a command they can run if they want the history in one place (substitute the actual
  folders):

  ```bash
  git mv Docs/ADR/*.md docs/adr/ && rmdir Docs/ADR
  ```

Do **not** run it, and do not move the files yourself. Continuing the numbering across every folder means
nothing breaks if they never move them.

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
constitution file only if it was edited, and use the real artifact root):

```bash
git add docs/adr/ADR-NNN-<kebab-case-title>.md
git commit -m "docs(adr): ADR-NNN <title>"
```

If a constitution update was made, suggest staging that file in the same commit. Make clear
this step is optional and the user can adjust the branch, message, or scope as they prefer.
