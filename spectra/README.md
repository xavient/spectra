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
| `speckit.spectra.impact` | Find out what a proposed feature would actually touch, with cited evidence, before anyone commits to building it. |
| `speckit.spectra.adr` | Capture a context-aware Architecture Decision Record grounded in the codebase, prior ADRs, and the constitution. |
| `speckit.spectra.flaky-test-detector` | Find the tests that pass and fail on the same code, then fix the ones you approve, one at a time. |
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
   under `docs/adr/`, specs under `specs/`, and the relevant source code.
2. Asks up to **5** clarifying questions, specific to your project, before drafting anything.
3. Determines the next ADR number, drafts the ADR, and writes it to `docs/adr/ADR-NNN-<title>.md`.
4. Checks the decision against your constitution and, if significant, **recommends** a constitution
   update and offers to make it.
5. Suggests (does not run) the optional git commands to commit the new ADR.

Usage (Claude):

```
/speckit-spectra-adr We should standardize on PostgreSQL for all primary data stores
```

The argument is a one-or-two-sentence description of the decision; if omitted, the command asks you
for one before drafting. ADRs are written to `docs/adr/` (created automatically), numbered
zero-padded to three digits.

**Somewhere other than `docs/`?** One line in `.specify/memory/constitution.md` moves every Spectra
document agent at once:

```text
Artifact root: documents/
```

The command reads that line and writes to `documents/adr/` instead. It offers the line but never adds it
for you. It also checks whether `docs/` is a published site source in your project — `mkdocs.yml`,
`docusaurus.config.*`, `docs/_config.yml`, `docs/.nojekyll`, `docs/index.html`, `docs/conf.py`, or a Pages
configuration pointing at `docs` — and asks before defaulting there, since that would publish the ADR or
add it to a generated docs build.

Upgrading from an older version? If the project still has a `Docs/ADR/` folder from before 1.6.0, the
command reads it for context and continues its numbering, tells you once where ADRs live now, and offers a
`git mv` you can run. It never moves or edits anything in the old folder.

### Change the shape of your ADRs

The ADR's section structure comes from `adr-template.md`, shipped with the extension. To use your own — extra
sections your governance requires, or fewer than the default — copy it into your project's override slot and
edit it there:

```bash
mkdir -p .specify/templates/overrides
cp .specify/extensions/spectra/templates/adr-template.md .specify/templates/overrides/adr-template.md
```

Commit that file. Every ADR from then on follows your structure, for everyone on the team, and **the override
survives extension updates** because it lives outside the extension's own directory. The command resolves the
template in this order and uses the first one it can read:

1. `.specify/templates/overrides/adr-template.md` — yours
2. `.specify/presets/<preset-id>/templates/adr-template.md` — an installed preset
3. `.specify/extensions/spectra/templates/adr-template.md` — the shipped default
4. `.specify/templates/adr-template.md` — a core template, if you keep one there
5. a skeleton inside the command itself — only when there is no `.specify/` at all

Every run tells you which template it used, so an override that isn't being picked up is obvious. Sections you
delete stay deleted: the command follows your template and mentions what it left out rather than adding it
back. Do **not** edit the copy under `.specify/extensions/` — extension files are replaced when the extension
updates, and your edit goes with them.

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

## `speckit.spectra.create-pr` — Create PR

Opens a pull request for the branch you are on — optionally linked to an issue, with the body built from
your project's **PR template** — and returns the link. It runs on demand from any branch, and is also
offered automatically by the `after_implement` hook. When you accept the offer (or run it directly) it:

1. **Gates on `gh` first.** If `gh` is missing or unauthenticated it **stops before anything else** —
   before the constitution is read, before a target branch is derived, before any `git` command — saying
   which of the two failed, because the remedies differ (install the CLI, or `gh auth login`). Nothing is
   mutated on that path.
2. Confirms the remote is on GitHub. A missing remote, or one on another host, stops with a scope
   statement rather than a `gh` fallback that could not work.
3. Checks the branch. Only two refusals: a **detached HEAD**, and a branch that is **already the base**.
   A `fix/…` or chore branch is fine — a spec branch just contributes more material to the body.
4. Detects an **existing open PR** and returns its link instead of opening a duplicate.
5. Determines the **base branch**. A promotion flow documented in the constitution's *Version Control &
   Branching Strategy* section or `.specify/extensions/git/git-config.yml` is used and cited. With nothing
   documented it *proposes* one — the branch yours appears to be cut from, else the repository default —
   and asks you at the final gate.
6. **Offers to commit and push** when the working tree is dirty: it lists the files and asks whether to
   commit and push first. Say yes and it behaves like an ordinary commit-and-push; say no and the PR is
   opened from committed work with the exclusion stated. Clean tree, unpushed commits — it asks to push.
7. **Asks for a linked issue** if you did not pass `--issue`, and accepts a skip.
8. **Resolves the PR template**, fills it from the real diff (plus `spec.md`/`plan.md`/`tasks.md` on a
   spec branch), and reports which template it used.
9. **Asks once, with everything on the table**: source → base and where the base came from, the issue or
   nothing, draft or ready, the template path, and anything it has already done. Nothing is created before
   you say yes — and you can redirect the base right there ("no, use dev").
10. Opens the PR with `gh` (**ready-for-review by default**, `--draft` on request) and returns the URL.

Its mutations are the Git and remote actions needed to open the PR — including a commit **when you ask for
one** — and nothing else: never your source, spec, plan, tasks, or constitution.

Usage (Claude):

```
/speckit-spectra-create-pr
/speckit-spectra-create-pr --issue 42
/speckit-spectra-create-pr --draft --base dev
```

Optional arguments:

- `--issue <url-or-number>` — the issue this PR addresses. Omit it and you are asked once; skip the
  question and no issue section is written.
- `--draft` — open the PR as a draft instead of ready-for-review.
- `--base <branch>` — use this base branch (still shown in the final summary).

### One thing to know about linked issues

GitHub interprets closing keywords **only when a PR targets the repository's default branch**. On any other
base they are ignored: no link is created and merging closes nothing. So the command writes `Closes #42`
only when the base *is* the default branch. Targeting a `dev` in a promotion flow, it writes a plain `#42`
reference instead — which still records a cross-reference on the issue — and tells you auto-close will not
happen on this merge. An issue in another repository is referenced by full URL, never with a keyword.

### Change the shape of your PRs

The body's structure comes from `pr-template.md`. Override it exactly like the ADR and BRD templates:

```bash
mkdir -p .specify/templates/overrides
cp .specify/extensions/spectra/templates/pr-template.md .specify/templates/overrides/pr-template.md
```

Commit it, and every PR the command opens follows your structure — resolution order, the reported template
path, and the survives-updates guarantee are identical to the ADR agent's, described
[above](#change-the-shape-of-your-adrs). Sections you delete stay deleted.

The shipped template has **no self-certification checklist** on purpose: an agent cannot honestly tick "I
have self-reviewed the full diff". If your override adds one, the command leaves those boxes unchecked and
tells you it left them for you.

One thing the template does *not* control: whether the PR is linked to the issue you passed. Trim the
**Related Issues** section and the command appends a short one rather than dropping the link — saying that it
did. Keep the section if you would rather choose where it sits.

**GitHub only** in this version (via the `gh` CLI), and `gh` is required at run time rather than
optional: without it the command stops with the remedy instead of half-running. Failures *after* that
gate — a protected base branch, a token without push permission, a fork restriction — degrade to the
manual `git push` + `gh pr create` commands (including the base branch it derived) plus an explicit
statement of whether the branch already reached the remote.

---

## `speckit.spectra.review-pr` — Review PR

Covers the last fully manual gate in the lifecycle. Where `create-pr` opens a pull request, this
reviews one — judging it against **the intent and standards the PR carries**, not just the diff. It:

1. **Gates on `gh` first.** If `gh` is missing or unauthenticated it stops before any analysis, saying
   which of the two failed. `create-pr` gates the same way, for the same reason: neither command can
   deliver its product — a review here, a pull request there — without reading GitHub through `gh`.
2. Resolves the target — a URL, a number, or a pick from the repository's open PRs — and **pins the
   review to one head revision**, reported everywhere and re-checked before publishing.
3. Reads the PR's **spec, plan, tasks, and ADRs at that revision**, and the **constitution and ADRs in
   force on the base branch**. The revision split is deliberate: it is what lets the agent notice a PR
   that changes the rules it is being measured against.
4. Locates the governing spec from the PR's own diff, and — when the diff carries none — from a path you
   name in the run's single context question, before treating the change as carrying no spec. Neither the
   branch name nor Spec Kit's machine-local feature record (`.specify/feature.json`) is ever used to guess:
   Spec Kit keeps that file out of version control, so at a PR's head revision it is absent or stale.
5. Reads the **linked issue as optional extra context** — found automatically, asked for once if absent,
   never required. On a PR with **no spec** the issue becomes the traceability baseline; with a spec it is
   background, and where the two disagree that is a Question naming both.
6. Runs **traceability in both directions** (work claimed complete but absent; changes no task
   authorized), **guardrails** with the violated clause quoted, and **craft** lenses chosen from what
   the diff actually touches — reporting which lenses did not run, and why.
7. Grades every finding Blocker / Major / Minor / Nit / Question from a **fixed rubric** so repeated
   reviews of one revision agree, with a separate confidence axis that caps severity: a low-confidence
   finding becomes a Question rather than a Blocker.
8. Presents the findings numbered and ranked, with a severity tally, its own reading of the change, a
   recommended verdict, and a mandatory **coverage-and-limits** statement — which now also says how much
   of the constitution actually applied to this diff, rather than only that guardrails ran.
9. Hands control back: **nothing is pre-selected.** You choose which findings are published and which
   verdict to submit, you see the exact review first — body *and* every inline comment — and only then is a
   **single review event** posted under your own `gh` authentication.

**Every finding cites a file, a line, and the clause, requirement, or principle it rests on** — a
finding that cannot be anchored and sourced is not reported at all. An **empty selection posts nothing**,
which is a normal outcome, not a failure. Approving over a blocker you accepted requires a typed
confirmation and is recorded in the published review, so an override is never silent. The published body
declares that it was AI-assisted and human-curated.

Its only mutation is publishing that one review, after an explicit go-ahead. It never edits source, the
spec, the plan, the tasks, or the constitution, never touches your working tree, holds no credentials of
its own, and stores nothing between runs.

### Findings land on the lines they are about

Accepted findings whose anchors fall **inside the diff** are published as comments on those lines, and where
the fix is mechanical the comment carries a ` ```suggestion ` block you can apply from the GitHub UI in one
click. Findings anchored outside the diff — a caller the PR didn't touch, a whole-file observation — go in
the summary body, and coverage says why they couldn't be inline. Add `<n>:body` to your selection to force
any finding into the body.

Because a suggestion is one click from a commit, they are offered narrowly: only for a mechanical, complete
fix covering exactly the commented lines, never for architectural or multi-file changes, never on a
low-confidence finding, and never in a generated file. **Every suggestion appears verbatim in the preview
you approve** — nothing that can be applied without being read is summarized.

Body, comments, and verdict post in one atomic call, so a failure can't leave the comments on the PR
without the verdict.

Usage (Claude):

```
/speckit-spectra-review-pr https://github.com/acme/api/pull/142
```

Optional arguments:

- *(none)* — offers the current branch's open PR, then lists open PRs to pick from.
- `<url>` or `<number>` — review that pull request.
- `--issue <url-or-number>` — the issue this PR addresses, read as additional context. Supplying it skips
  both detection and the question.
- `--since <revision>` — review only the delta since a revision you reviewed before, reporting which
  previously published findings now appear resolved. Prior findings are recovered by reading the earlier
  review off the pull request itself, since nothing is stored locally.

### Change the shape of your reviews

The findings presentation comes from `review-template.md` — the summary body *and* the inline comment shape.
Override it exactly like the other templates:

```bash
mkdir -p .specify/templates/overrides
cp .specify/extensions/spectra/templates/review-template.md .specify/templates/overrides/review-template.md
```

Three things are **not** the template's to change, and survive any override: the
`<!-- spectra:review-pr revision=… -->` anchor that `--since` and self-review detection depend on, the
AI-assisted disclosure line, and the **Coverage and limits** section — the one that stops a review implying
assurance it didn't earn.

Judgment isn't overridable either. The severity rubric and its floors, the confidence cap, the anchor rule,
the selection grammar, and how the verdict is derived stay in the command, because two reviews of the same
diff have to agree. The template governs how findings *read*, not what counts as a Blocker.

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
2. Reads project context — the shipped BRD template, the constitution, existing BRDs under `docs/brd/`,
   and prior specs — to ground and deconflict, without adding scope the requirement didn't state.
3. Asks up to **5** clarifying questions, but only when the requirement has material gaps.
4. Writes one BRD to `docs/brd/NNN-<title>.md` (folder created automatically, numbered zero-padded to
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

BRDs land in `docs/brd/` by default, and the same one-line override applies — `Artifact root: documents/`
in `.specify/memory/constitution.md` sends them to `documents/brd/` instead. The command checks whether
`docs/` is a published site source before defaulting there and asks first if it is; a BRD carries
stakeholders, revenue targets, and competitive rationale, so publishing one by accident is the mistake
worth one question. Unanswered, it picks the non-publishing folder.

Upgrading from an older version? A `brds/` folder from before 1.6.0 is read for context and numbering, so
the next BRD continues the sequence; the command says once where BRDs live now and offers a `git mv`.
Nothing in the old folder is moved or modified.

### Change the shape of your BRDs

Same mechanism as the ADR agent, with `brd-template.md`:

```bash
mkdir -p .specify/templates/overrides
cp .specify/extensions/spectra/templates/brd-template.md .specify/templates/overrides/brd-template.md
```

Commit it, and every BRD follows your structure — the 14 shipped sections are a default, not a fixed contract.
Resolution order, the reported template path, and the survives-updates guarantee are identical to the ADR
agent's, described [above](#change-the-shape-of-your-adrs).

One caveat worth knowing: **Section 6 — User Journeys** is what the Spec Kit `specify` command leans on most
heavily. Dropping it is allowed, and the command will say it did so, but expect the resulting spec to have
thinner user stories.

## `speckit.spectra.impact` — Impact Analyzer

A Requirements & Discovery-phase command that runs **before** the spec-driven loop. Give it one paragraph
describing what should be true after a feature ships, and it produces a numbered impact analysis a Business
Analyst takes to stakeholders for a go / no-go decision — before the organization commits development spend.
It:

1. Reads the project — the constitution, existing specs, source, ADRs, API contracts, migrations, tests, CI.
   Where specs and a constitution exist it orients on them and reads code to confirm and extend them; where
   they do not, it reconstructs the same understanding from source and says so. Which mode it ran is in the
   output.
2. Asks, before scanning, whether this repository is the whole system. Other systems are declared as a
   sentence, a document, or a **path to a local copy read in place**. It accepts no repository URL and makes
   no network request at all.
3. Scans in five bounded phases — structural map, term expansion across naming conventions, a role-weighted
   seed search, two-hop graph expansion, and two sweeps for what static reading misses: dynamic dispatch and
   string-keyed registries, then every contract identifier (tables, columns, endpoints, events, topics,
   config keys, flags, env vars) swept as a raw string across the whole project.
4. Asks at most **5** clarifying questions, generated from what the scan found ambiguous, each with options
   and a recommendation grounded in a cited finding. Pressing enter accepts the recommendation and records
   the answer as unconfirmed.
5. Analyzes through five core lenses — blast radius, data, behavioural change, risk and reversibility, effort
   and sequencing — plus security/privacy and compliance lenses that fire on trigger and **route to the agent
   that owns the question** rather than answering it.
6. Writes one analysis to `docs/impact-analysis/NNN-<name>.md` plus an index, and reports coverage.

Every finding carries a `path/to/file.ts:142` citation and one of three confidence levels, fixed by the kind
of evidence rather than by how convincing it felt. The impact rating is derived from a defined trigger set
rather than judged, and reported with the trigger that fired. The output never claims absence of impact — "no
consumers found in what was scanned" is as far as it goes — and it never reproduces a secret value: where a
cited line holds one, it gives the location and the kind and says the value was withheld.

Usage (Claude):

```
/speckit-spectra-impact We want to email customers who leave items in their cart for more than 24 hours
```

With a supporting document, or unattended in CI:

```
/speckit-spectra-impact Add a nickname field to accounts reqs/nickname-brief.docx
/speckit-spectra-impact --non-interactive Retire the v1 pricing endpoint
```

Analyses land in `docs/impact-analysis/` by default, and the same one-line override applies —
`Artifact root: documents/` in `.specify/memory/constitution.md` sends them to `documents/impact-analysis/`
instead. The command checks whether `docs/` is a published site source before defaulting there and asks first
if it is; an impact analysis names internal systems, owning teams, unmitigated risks, and where secrets live.
Unanswered, it picks the non-publishing folder.

**Approval is manual, and stays yours.** Every run writes `status: draft`. You take it to your stakeholders
and record the outcome in the front matter yourself; the command never sets any other status. The folder index
is rebuilt from the documents on every run, so an approval you record by hand appears there without the
command editing a document to do it.

**Re-runs never overwrite.** Every run takes the next number — one greater than the highest present, not a
count of the files — and writes a new document, including a re-run with identical input. Each report carries
its own timestamp and a verbatim copy of what it was asked, and the analysis it supersedes is linked rather
than replaced. An interrupted run leaves the folder untouched and consumes no number.

It does not design the solution, estimate in story points, write requirements, or create or link a spec.
Impact analysis and specification are independent processes; nothing under `specs/` is written or depended
on, and there is no `spec_refs` field.

### Change the shape of your impact analyses

Same mechanism as the ADR and BRD agents, with `impact-analysis-template.md`:

```bash
mkdir -p .specify/templates/overrides
cp .specify/extensions/spectra/templates/impact-analysis-template.md \
   .specify/templates/overrides/impact-analysis-template.md
```

Commit it, and every analysis follows your structure — the ten shipped sections are a default, not a fixed
contract. Delete a section, including a whole lens, and the command notes the omission rather than putting it
back. Resolution order, the reported template path, and the survives-updates guarantee are identical to the
ADR agent's, described [above](#change-the-shape-of-your-adrs).

What an override **cannot** change is the part that makes the document usable at a gate: citations, confidence
levels, the rating and its trigger, the coverage statement, the no-absence-of-impact phrasing, and the refusal
to reproduce a secret. Those live in the command. Drop *Sources consulted* and the section goes — the command
still tells you what it read and what it could not reach.

## `speckit.spectra.flaky-test-detector` — Flaky Test Detector

A Testing & Quality-phase command, and the only Spectra agent that edits code you wrote. It finds the
tests that pass and fail on the same code, and — with your go-ahead twice — fixes them. It:

1. Reads `.specify/memory/flaky-test-analysis.md` **first**, before anything else, and branches on what it
   finds: no file, unfinished work, a completed list, or a file it cannot parse.
2. Identifies your test suites from the working tree — runner configuration, test scripts in the project
   manifest, directory conventions, filename patterns — and reports each with its framework and file count
   before naming a single candidate. Several suites in several languages are fine.
3. Reads the tests for the eight signal categories: timing and async, isolation and shared state, unmocked
   external dependencies, non-determinism, brittle assertions, parallel-execution conflicts, environment
   coupling, and existing retry or known-flaky annotations.
4. Reports a ranked table — test, file, confidence, and a specific fix — plus an honest statement of what
   it did not examine, then **stops and asks** before writing anything.
5. On your go-ahead writes the plan: a run summary, one `[ ]` row per candidate, the evidence behind each,
   and what it could not analyse. Then it stops again, and tells you to delete the rows you disagree with.
6. On a second go-ahead works the surviving rows in file order, ticking each `[x]` on disk as it lands, and
   closes with what it fixed, what it left open and why, and every file it touched.

**It never runs anything** — not your suite, not a build, not an install, and not to verify a fix it just
applied. Detection is a read of the source, which is why it works on the day you install it with no CI
integration, no results store, and no waiting for run history. The no-verification rule is deliberate
rather than an omission: an agent that can run the tests it just edited can iterate until green, and that
is how tests get weakened.

**A fix removes the cause.** Deleting an assertion, loosening one so it always passes, skipping the test,
marking it expected-to-fail, adding a retry wrapper, or lengthening a sleep are forbidden as remedies.
Edits stay in test and test-support files — it may create a helper or a mock where a fix needs one, and it
will say so — but never production source, and never a new dependency. Where the real remedy is in your
application code, the item stays open with a note about what would need to change and where. Nothing is
committed: the working-tree diff is your review surface.

Usage (Claude):

```
/speckit-spectra-flaky-test-detector
```

Or narrow it to one part of a monorepo:

```
/speckit-spectra-flaky-test-detector api/
```

### The list is meant to outlive the session

There is exactly **one** analysis file, at `.specify/memory/flaky-test-analysis.md`, at any time. Close
your terminal mid-run and the file is still exactly true — progress is written after every single fix, not
batched at the end — so the next run picks up the remaining items without re-analysing and without
discarding the pruning you did. A completed list is never replaced without asking. A file it cannot parse
is never overwritten silently; it says what it could not read and waits. And before a run scoped to one
suite replaces a plan covering more, it names the pending items that would be dropped.

The file is yours to edit. Delete rows to exclude those tests, reword a suggested fix and it acts on your
wording, tick an item yourself and it skips it. Only structural damage — a missing `## Tasks` heading,
rows it cannot resolve — counts as unreadable.

### Confidence, and what it is not

High, Medium, or Low, rating **the strength of the evidence in your source**, not a measured failure rate.
High requires the triggering construct in the test's own body or its direct fixtures, citable by line.
With no run history there is no denominator, so the command emits no percentage, score, or flakiness
index — inventing one would be the easiest way to sound authoritative and be wrong.

Your project's constitution binds the fix it chooses. If a guardrail rules out the only available remedy —
no mocking libraries, no new test dependencies — the item is left open with that rule named, rather than
producing a change your own review would reject.

## License, trademarks, and disclaimer

Apache License 2.0 — see the [`LICENSE`](./LICENSE) and [`NOTICE`](./NOTICE) files shipped with this
extension. Attribution is a licence condition: keep the copyright notice, the `LICENSE`, and the
`NOTICE` file with any derivative work, and state which files you changed.

Trademarks are not licensed. "TELUS", "TELUS Digital", "Spectra", and the TELUS Digital logo are
excluded from the grant; forks must rebrand. See [`TRADEMARK.md`](./TRADEMARK.md).

Spectra agents produce drafts for human review. Output is not legal, regulatory, medical,
financial, or compliance advice and does not constitute certification or audit. Compliance agents
are readiness-support tooling only — running them does not make a system compliant, and Spectra is
not certified by or affiliated with any standards body or regulator.
