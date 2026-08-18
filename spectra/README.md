# Spectra (`spectra`)

The Spectra extension for [Spec Kit](https://github.com/github/spec-kit) — a single self-contained
extension that bundles Spectra's agentic SDLC commands. Every command lives under the unified
`speckit.spectra.*` namespace and installs together in one step.

## Commands

<!-- SPECTRA:GENERATED START id=spectra-readme-commands -->
<!-- Generated from agents-list.json — do not edit by hand. Run: python tools/generate_agent_docs.py -->

| Command | What it does |
| ------- | ------------ |
| `speckit.spectra.domain-analyzer` | Infer the project's business domain from its code and docs, then propose opt-in candidate guardrails for SME review. |
| `speckit.spectra.brd` | Turn a raw business requirement, typed or in a document, into a structured, specify-ready BRD. |
| `speckit.spectra.adr` | Capture a context-aware Architecture Decision Record grounded in the codebase, prior ADRs, and the constitution. |
| `speckit.spectra.create-pr` | Open a correctly-targeted GitHub PR for the current spec branch and return its URL. |
| `speckit.spectra.review-pr` | Review a GitHub pull request against the spec, plan, tasks, ADRs, and constitution it carries, then publish a single human-curated review containing only the findings the reviewer selected. |
<!-- SPECTRA:GENERATED END id=spectra-readme-commands -->

## Install

You need a project already initialized with `specify init`; the commands register for whatever AI
agent that project uses. After installing, **restart your agent** so it picks up the new commands.

From the catalog (see the [repo root README](../README.md) for catalog setup):

```bash
specify extension add spectra
```

Or install a working copy directly:

```bash
specify extension add --dev ./spectra
```

To update later, add `--force` to overwrite your existing copy — e.g.
`specify extension add --dev ./spectra --force`.

## A note for mixed-agent teams

Commands are named `speckit.spectra.<command>` in the manifest, and Spec Kit rewrites each into your
agent's native format at install time — so the **trigger you type differs by agent**:

- **Claude** registers them as *skills*, invoked with a leading slash and dashes: `/speckit-spectra-adr`.
- **Other agents** (e.g. kiro-cli) keep the dots: `/speckit.spectra.adr`.

It's the same extension and the same source files across all of them. After install,
`specify extension info spectra` (or your agent's command/skill list) shows the exact triggers. If a
command doesn't show up, restart your agent so it re-scans its command/skill directory.

---

## `speckit.spectra.adr` — Architecture Decision Records (ADR)

Takes a short description of a decision and then:

1. Reads your project context — the constitution (`.specify/memory/constitution.md`), existing ADRs
   under `Docs/ADR/`, specs under `specs/`, and the relevant source code.
2. Asks up to **5** clarifying questions, specific to your project, before drafting anything.
3. Determines the next ADR number, drafts the ADR, and writes it to `Docs/ADR/ADR-NNN-<title>.md`.
4. Checks the decision against your constitution and, if significant, **recommends** a constitution
   update and offers to make it.
5. Suggests (does not run) the optional git commands to commit the new ADR.

Usage (Claude):

```
/speckit-spectra-adr We should standardize on PostgreSQL for all primary data stores
```

The argument is a one-or-two-sentence description of the decision; if omitted, the command asks you
for one before drafting. ADRs are written to `Docs/ADR/` (created automatically), numbered
zero-padded to three digits.

---

## `speckit.spectra.domain-analyzer` — Domain Analyzer

A foundation-phase command that reads your project, infers its **business domain**, and proposes
**evidence-backed, opt-in guardrails** for your constitution. It:

1. Reads your project context — constitution, docs and specs, source code and dependency manifests,
   and any prior proposal file.
2. Infers your business domain and summarizes the evidence.
3. Generates atomic candidate guardrails, each with a stable ID, a declarative/testable statement, a
   target constitution section, file-path evidence, and a confidence rating.
4. Writes them to `.specify/memory/domain-analysis.md`, with **every item left unchecked (opt-in)**.

It never edits the constitution or your source — its only write is its own proposal file. Review the
file, check `- [x]` the guardrails you want (edit wording freely), then run `/speckit-constitution`
referencing it to adopt **only the checked items**.

Usage (Claude):

```
/speckit-spectra-domain-analyzer
```

No arguments required — it analyzes the whole project. Optionally pass a focus hint, e.g.
`/speckit-spectra-domain-analyzer focus on security`. Re-running preserves prior decisions, edits,
and ordering; only genuinely new candidates are appended under a dated heading.

---

## `speckit.spectra.create-pr` — GitHub (PR)

Closes the loop after `implement`: it **offers** to open a pull request for the completed spec,
targeting the **correct base branch** for your project's branching/promotion strategy, and returns
the PR link. When you accept the offer (or run it on demand) it:

1. Checks preconditions — `gh` installed and authenticated, remote is GitHub — and **degrades
   gracefully** with a manual fallback if any are missing.
2. Validates the **source branch** (one-branch-per-spec): refuses to open a PR from `main`, a
   detached HEAD, or a non-spec branch.
3. Detects an **existing open PR** and returns its link instead of opening a duplicate.
4. Determines the **target (base) branch** from the constitution's *Version Control & Branching
   Strategy* section and the branching config — honoring a defined promotion flow, or proposing the
   repository default branch with confirmation when none is defined.
5. Surfaces uncommitted changes and, on your confirmation, pushes the branch.
6. Opens the PR with `gh` (**ready-for-review by default**, `--draft` on request) using a title and
   body derived from the spec, and returns the PR URL.

Its only mutations are the Git/remote actions required to open the PR; it never edits your source,
spec, or constitution. It is also offered automatically by the `after_implement` hook.

Usage (Claude):

```
/speckit-spectra-create-pr
```

Optional arguments:

- `--draft` — open the PR as a draft instead of ready-for-review.
- `--base <branch>` — override the derived base branch (still confirmed before opening).

**GitHub only** in this version (via the `gh` CLI). When `gh`, a GitHub remote, or network access is
unavailable, the command explains the situation and prints the manual `git push` + `gh pr create`
commands (including the base branch it would have used).

---

## `speckit.spectra.review-pr` — Review PR

Covers the last fully manual gate in the lifecycle. Where `create-pr` opens a pull request, this
reviews one — judging it against **the intent and standards the PR carries**, not just the diff. It:

1. **Gates on `gh` first.** If `gh` is missing or unauthenticated it stops before any analysis, saying
   which of the two failed. Unlike `create-pr` this does **not** degrade, because a review's entire
   value is the analysis and the analysis needs the pull request.
2. Resolves the target — a URL, a number, or a pick from the repository's open PRs — and **pins the
   review to one head revision**, reported everywhere and re-checked before publishing.
3. Reads the PR's **spec, plan, tasks, and ADRs at that revision**, and the **constitution and ADRs in
   force on the base branch**. The revision split is deliberate: it is what lets the agent notice a PR
   that changes the rules it is being measured against.
4. Locates the governing spec by trying the PR's own diff, then the project's Spec Kit feature record,
   then treating the change as carrying no spec. Branch names are never used to guess.
5. Runs **traceability in both directions** (work claimed complete but absent; changes no task
   authorized), **guardrails** with the violated clause quoted, and **craft** lenses chosen from what
   the diff actually touches — reporting which lenses did not run, and why.
6. Grades every finding Blocker / Major / Minor / Nit / Question from a **fixed rubric** so repeated
   reviews of one revision agree, with a separate confidence axis that caps severity: a low-confidence
   finding becomes a Question rather than a Blocker.
7. Presents the findings numbered and ranked, with a severity tally, its own reading of the change, a
   recommended verdict, and a mandatory **coverage-and-limits** statement.
8. Hands control back: **nothing is pre-selected.** You choose which findings are published and which
   verdict to submit, you see the exact body first, and only then is a **single review event** posted
   under your own `gh` authentication.

**Every finding cites a file, a line, and the clause, requirement, or principle it rests on** — a
finding that cannot be anchored and sourced is not reported at all. An **empty selection posts nothing**,
which is a normal outcome, not a failure. Approving over a blocker you accepted requires a typed
confirmation and is recorded in the published review, so an override is never silent. The published body
declares that it was AI-assisted and human-curated.

Its only mutation is publishing that one review, after an explicit go-ahead. It never edits source, the
spec, the plan, the tasks, or the constitution, never touches your working tree, holds no credentials of
its own, and stores nothing between runs.

Usage (Claude):

```
/speckit-spectra-review-pr https://github.com/acme/api/pull/142
```

Optional arguments:

- *(none)* — offers the current branch's open PR, then lists open PRs to pick from.
- `<url>` or `<number>` — review that pull request.
- `--since <revision>` — review only the delta since a revision you reviewed before, reporting which
  previously published findings now appear resolved. Prior findings are recovered by reading the earlier
  review off the pull request itself, since nothing is stored locally.

Deliberately **on demand only** — there is no hook, because a reviewer should not be the author.
**GitHub only** in this version (via the `gh` CLI), and single-body reviews only; line-anchored inline
comments are a follow-on. Failures *after* the `gh` gate — a fork restriction, insufficient permission —
degrade to handing you the rendered review body for manual posting.

---

## `speckit.spectra.brd` — BRD Generator

A Requirements & Discovery-phase command at the front of the workflow: it turns a raw business
requirement into a structured, **specify-ready** BRD. It:

1. Reads the requirement — inline text, or a `.docx`/`.pdf`/`.md`/`.txt` document whose text it
   extracts (when both are supplied, the document is primary and the text is guidance). Unreadable or
   image-only files are reported, not fabricated.
2. Reads project context — the shipped BRD template, the constitution, existing BRDs under `/brds`, and
   prior specs — to ground and deconflict, without adding scope the requirement didn't state.
3. Asks up to **5** clarifying questions, but only when the requirement has material gaps.
4. Writes one BRD to `/brds/NNN-<title>.md` (folder created automatically, numbered zero-padded to
   three digits, never overwriting), following the canonical template — genuine unknowns become Open
   Questions and adopted defaults become Assumptions.
5. Reports the path and tells you to run the Spec Kit **specify** command with the BRD.

Its only write is the BRD file; it never edits your spec, constitution, or source, and never invokes
`specify` itself.

Usage (Claude):

```
/speckit-spectra-brd Support agents need to merge duplicate customer tickets while preserving history
```

Or point it at a document:

```
/speckit-spectra-brd reqs/ticket-merge-brief.docx
```

With no input it asks for a requirement or a file path.

## License

Apache License 2.0 — see [LICENSE](./LICENSE).

Free to use, modify, and redistribute. Attribution is required: keep the copyright notice, the
`LICENSE`, and the [`NOTICE`](./NOTICE) file in any redistribution or derivative work, and state
which files you changed.
