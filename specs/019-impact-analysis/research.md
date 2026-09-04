# Phase 0 — Research: `speckit.spectra.impact`

**Feature**: [spec.md](./spec.md) · **Plan**: [plan.md](./plan.md) · **Date**: 2026-09-03

Nine decisions. Each is one the command file cannot be written without, and each had a plausible alternative
that was rejected for a stated reason. Where the honest answer is a limitation rather than a solution, it is
recorded as one.

---

## 1. Expressing repository-wide search without naming a tool

**Decision**: the command states the **search it needs** and delegates the mechanism to the host agent. Three
capabilities are named in prose — list a directory tree, read a file, find a literal string anywhere in the
project — and every phase is written against those. Where the host cannot search project-wide text, FR-027
requires the command to say so and report the reduced coverage rather than quietly narrowing to the import
graph.

**Rationale**: the design spec names ripgrep in four phases. Depending on it breaks two commitments at once.
Principle III forbids hard-coding one environment's tooling, and the published package is Markdown only — no
scripts, no binaries, no post-install hooks — which is the basis of the supply-chain claim in the project
README and the reason a security review does not have to reopen. Every agent Spec Kit supports already has
some form of grep; none of them has the same one.

**Alternatives rejected**:

- *Require ripgrep and gate on it at run time, as `create-pr` gates on `gh`.* The `gh` precedent does not
  transfer: `gh` is the only way to talk to GitHub, whereas text search is something every agent already has
  in its own form. Gating would exclude agents that can do the job.
- *Ship a search script.* Breaks the Markdown-only guarantee and would need a Bash and a PowerShell variant,
  which is exactly the split Principle VIII's resolution rule exists to avoid.
- *Traverse only the import graph.* Deletes Phase 5b, which the design spec calls the sole defence against
  coupling the graph cannot see. That is the feature, not an optimization.

---

## 2. Enforcing caps in prose

**Decision**: caps are stated as **numbered budgets with a disclosure obligation**, not as loop bounds. The
command tells the agent the order to work in — rank, then take the top N — and requires the count actually
reached, the cap that bound it, and what was left out to appear in Sources consulted (FR-045, FR-028). Five
caps: 30 seed files, 2 hops, 80 project files, 50 swept identifiers, 20 files per declared system, each
overridable in the invocation.

**Rationale**: a prompt cannot enforce an upper bound the way a program can, so the design has to make
exceeding one *visible* instead of impossible. Ranking is what makes that safe: because FR-021 orders seeds by
file role and FR-024 orders identifiers by boundary class, the items that fall past a cap are by construction
the least likely to matter. A cap without a ranking is a coin flip; a cap with one is a stated trade.

**Alternatives rejected**:

- *No caps, rely on the agent's own limits.* The agent's limit is a context window, which produces a silent
  truncation at an arbitrary point — the exact failure R5 exists to prevent.
- *One global file budget.* Whichever phase runs last gets starved, and the phase that runs last is Phase 5b.
- *A wall-clock budget.* Non-deterministic: the same repository yields different coverage run to run, which
  undermines the coverage statement even though it is disclosed.

---

## 3. Detecting a non-interactive session from inside a prompt

**Decision**: the command instructs the agent to treat "I cannot obtain an answer" as the trigger, announce it
in one line naming the explicit switch, and proceed as though the switch had been passed (FR-062a). **The
detection is the host agent's, not the command's** — a Markdown prompt has no `isatty`. Where the agent cannot
tell, the explicit switch remains the reliable path, and the announcement is what makes the difference visible
either way.

**Rationale**: this is the one place in the design where the mechanism is genuinely outside the command's
reach, and it is better to say so than to write a requirement that reads like a capability. What the command
*can* guarantee is the behaviour on both sides of the branch: never hang on input that cannot arrive, never
proceed silently, and tag every defaulted answer regardless of how the mode was reached. The `spectra` CLI
handles the same situation for its own prompts, so the project gives one answer to "no terminal" rather than
two.

**Alternatives rejected**:

- *Require the switch and hang otherwise.* Hangs a pipeline on a prompt nobody will read, which is the failure
  this exists to prevent.
- *Refuse when the switch is absent and interaction is impossible.* Loses the analysis entirely for a run that
  could have produced a correctly-labelled draft — and the labelling machinery (defaulted tags, the
  three-or-more banner) already exists.
- *Proceed silently.* The document would carry the tags, but the operator would learn the mode after the fact
  from a file rather than at the start from the run.

---

## 4. Ranking contract identifiers by boundary class

**Decision**: two tiers. **Contract-bearing** identifiers first — table and column names, endpoint paths,
event and topic names — then **configuration-bearing** ones — configuration keys, feature-flag keys,
environment variable names. Sweep the top 50 by that order, disclose the cap and the number left unswept
(FR-024).

**Rationale**: the sweep exists to find consumers, and a consumer couples to a *contract*. A column name or a
topic name appearing in a second component is close to proof of coupling; an environment variable name
appearing there is usually two components reading the same deployment convention. The classes also differ in
population: a schema change yields tens of column names, while a mature service has hundreds of config keys and
env vars, so an unranked cap would spend the whole budget on the least informative tier. This is the same move
FR-021 already makes one level up, where files are weighted by role.

**Alternatives rejected**:

- *Sweep contract classes in full and cap only config classes.* Guarantees contract coverage but leaves the
  worst case unbounded — a 200-column migration is precisely a High-impact change where the run is already long.
  Recorded as the fallback if the ranked cap proves too tight in validation.
- *Cap by count with no ordering.* Arbitrary: the dropped identifiers would be whichever the extraction
  happened to find last.
- *Let the user list the identifiers.* Requires the BA to know the schema, which is the thing they came here
  not knowing.

---

## 5. Artifact-root resolution: reuse, do not re-derive

**Decision**: reproduce the resolution sequence `brd` and `adr` already carry — declared root wins if
`Artifact root: <folder>/` appears in the constitution (matched case-insensitively, rejected if absolute or
containing `..`), otherwise default to `docs/` **after** checking for a publication signal (`mkdocs.yml`,
`docusaurus.config.*`, `docs/_config.yml`, `docs/.nojekyll`, `docs/index.html`, `docs/conf.py`, or a Pages
configuration pointing at `docs`), recommend `documents/` when a signal is found, take the non-publishing
option when the choice cannot be obtained, and offer the declaration line without ever writing it.

**Rationale**: three document agents each deriving this independently is how the `Docs/ADR` versus `/brds`
divergence happened in the first place. The wording is already measured against Spec Kit 0.16.5 behaviour and
already asserted by `tests/test_doc_output_paths.py`; adding `impact.md` to that module's `CANONICAL` dict
inherits every one of those assertions for free.

**One difference from `brd` worth stating**: `brd` argues that a BRD is the worst artifact to publish
accidentally because it names stakeholders and revenue targets. An impact analysis is in the same class or
worse — it names internal systems, owning teams, unmitigated risks, and the location of secrets — so the same
"take the non-publishing option when in doubt" rule applies with the same force, and the resolution question
does not count against the five clarifying questions.

**Alternatives rejected**:

- *Hard-code `docs/impact-analysis/`, as the design spec does.* Violates VII's declarable root and would fail
  the existing test the moment the command joins `DOCUMENT_COMMANDS`.
- *Write into `.specify/memory/`, as `domain-analyzer` does.* That location is for context another command
  consumes. This document is read by a human at a stakeholder gate, which is the definition of a deliverable.

---

## 6. Template resolution: five layers, stated in prose

**Decision**: reproduce the five-step lookup the two document commands already state — project override,
preset, extension, core, inline skeleton — taking the first layer that is readable **and non-empty**, never
stopping at one that merely exists, reporting the resolved path, and treating a template as input that is
never edited (FR-057 to FR-060).

**Rationale**: Principle VIII requires prose expression specifically because `resolve_template()` is a Bash
function in core's script tree, so calling it would break PowerShell-only setups, and shipping our own resolver
would break the Markdown-only promise. `tests/test_document_templates.py` asserts heading parity between the
shipped template and the command's inline skeleton, so the skeleton is not decoration — it is a second copy
that must not drift.

**What the template does not own**: the trustworthiness rules. `review-template`'s manifest entry already
records this pattern — "the revision anchor, the AI-assisted disclosure, and the coverage statement stay with
the command" — and the same division applies here: an override may drop a section, but it cannot make the
command stop citing, stop rating, or stop reporting coverage.

---

## 7. Refreshing the index without owning the status

**Decision**: on every run, read the front matter of each document in the folder, rewrite the index rows from
what it finds, then append the new row (FR-056). The command modifies no document while doing so.

**Rationale**: the approval gate is manual by decision — the command writes `draft` and a human later edits the
front matter to `approved` or `rejected` (FR-053a). An index that copied status at write time would therefore be
stale within a day of the first approval, which defeats the reason it exists. Reading N front matters in one
folder is cheap, self-healing, and needs no state: whatever a human did to a document since the last run shows
up on the next one.

**Alternatives rejected**:

- *Omit status from the index.* Cheaper, but the index's job is telling a BA which analysis is current, and
  status is most of that answer.
- *Have the command manage approval itself.* Rejected at clarification: the gate is a conversation with
  stakeholders, and a tool that recorded approval would be recording something it did not witness.
- *Derive status lazily at read time.* There is no reader — the index is a Markdown file a human opens.

---

## 8. Recognizing a secret without executing anything

**Decision**: pattern recognition on content already being read, then a **prohibition on reproduction** rather
than an attempt at classification. The command watches for the shapes — assignment to a name containing
`secret`, `token`, `key`, `password`, `credential`, `passwd`, `api_key`; high-entropy string literals in
configuration; PEM and SSH key headers; connection strings with embedded credentials; known provider token
prefixes — and where a line it would cite carries one, it gives the location and the kind only and states that
the value was withheld (FR-042a).

**Rationale**: the command is already reading these files for other reasons, so recognition costs nothing extra
and needs no tool. The important half is the second half: FR-042a is written as a rule about **output**, not
about detection, which means an imperfect detector still cannot cause the harm — the command's instruction is
"never reproduce a value that looks like a secret", and over-withholding costs a reader one extra file open
while under-withholding copies a live credential into a committed document.

**Alternatives rejected**:

- *Run a secret scanner.* Requires a binary and possibly network; both are out.
- *Quote a redacted fragment so a reader can match it to a vault entry.* A prefix is often the whole
  identifying part of a provider token, and the matching use case is the security agent's job, not this one's.
- *Cite normally and rely on the publication check.* Leaves the value in a second file and makes safety depend
  on getting the folder right. FR-042a composes with the publication check instead of depending on it.

---

## 9. Mapping the confidence taxonomy onto kinds of evidence

**Decision**: a fixed mapping, so the level is derived rather than judged (FR-046, FR-010c).

| Evidence | Level |
|---|---|
| Code read in this run, cited `path:line` | `confirmed` |
| Naming convention, configuration reference, or a Phase 5b string-literal match, cited | `probable` |
| Specification, ADR, or other document only — no code citation | `probable` at best, never `confirmed` |
| Dynamic-pattern hit from Phase 5a | `possible` |
| Suspected consumer in a system declared but `declared-not-scanned` | `possible` |
| Evidenced absence — searched, not found | cited as a search, level from the search's completeness |

**Rationale**: three levels with a stated evidence requirement each are only useful if two runs assign them the
same way. The two rows that carry real weight are the document row and the dynamic-pattern row. A specification
records intent and drifts from code, so letting a spec-only finding reach `confirmed` would turn the cheaper
spec-informed scan mode into a way of sounding more certain about code nobody opened — which is why FR-010c
also makes a spec/code disagreement a finding in its own right. And a Phase 5a hit is by definition something
static traversal could not resolve, so it is never better than `possible` no matter how suggestive it looks.

**Alternatives rejected**:

- *Let the agent judge confidence per finding.* Produces ratings that are not comparable between runs, which
  makes the whole taxonomy decorative.
- *Two levels — confirmed and unconfirmed.* Collapses "a config file names this table" with "this handler is
  registered by string key", and the second needs a human where the first often does not.
