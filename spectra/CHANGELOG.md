# Changelog

All notable changes to the `spectra` extension are documented here. This project follows
[Semantic Versioning](https://semver.org/).

## [1.5.0] - 2026-08-19

### Changed
- **`speckit.spectra.create-pr` now hard-stops when `gh` is missing or unauthenticated**, instead of
  degrading to a printed manual fallback. The check runs as the first thing after you accept the offer —
  before the constitution is read, before a target branch is derived, before any `git` command — and it
  names which of the two failed, because the remedies differ: install the GitHub CLI, or run
  `gh auth login`. Nothing is mutated on that path, and when `gh` is absent the message no longer prints
  a `gh` command line; the only alternative it names is the GitHub web interface.

  This **reverses the difference recorded in 1.4.0**, where `create-pr` degrading was described as a
  deliberate contrast with `review-pr`. That justification does not survive contact with the two
  failures it was meant to serve. The printed fallback told the user to run `gh pr create` — the command
  they demonstrably did not have — and the duplicate-PR check is itself a `gh` call, so a run without
  `gh` could walk them into a second pull request for a branch that already had one. Both GitHub
  commands now gate identically. What differs is only what each hands over *after* the gate.

- **A refusal after the gate now degrades properly, and says what it changed.** A protected base branch,
  a token without push permission, or a fork restriction is reported with the underlying `git`/`gh`
  message, the manual commands including the derived base branch — runnable, because `gh` is present
  here — and, critically, the mutation state: *nothing reached the remote*, or *the branch is on the
  remote and no pull request exists*. The command previously had no instructions for this case at all,
  even though by then it may already have pushed.

- **A remote that is absent or not on `github.com` is now a stop with a scope statement**, not a
  degradation, and prints no `gh` fallback — there is nothing `gh` can do with a GitLab remote. GitHub
  Enterprise is named as out of scope rather than half-attempted.

- **The pull request body is passed on standard input** (`--body-file -`) rather than as a
  command-line argument, so spec prose carrying backticks, code fences, quotes, and blank lines reaches
  the pull request unaltered. `review-pr` already published review bodies this way.

- **Fork detection is read from the repository, not guessed from the URL.** One
  `gh repo view --json nameWithOwner,isFork,parent,defaultBranchRef,viewerPermission` call replaces the
  previous "if `origin` looks like a fork" heuristic *and* the separate default-branch lookup. Forks and
  multi-remote setups are still resolved by asking, and now for a stated reason: `gh pr list --head`
  rejects `<owner>:<branch>` while `gh pr create --head` accepts it, so an inferred fork flow would
  check for duplicates against one head and open against another.

- **`gh` is declared as the only route to GitHub** in the command's governing rule — no `curl`, no
  direct REST calls — matching `review-pr`.

`gh` remains **optional at the extension level**: `adr`, `brd`, and `domain-analyzer` never touch
GitHub, so requiring it would block installation for users who only want those.

A command changed behaviour, no argument or output contract did, which is why this is a MINOR.

## [1.4.0] - 2026-08-17

### Added
- **`speckit.spectra.review-pr` — a reviewing agent for the last manual gate in the lifecycle.** It
  reviews a GitHub pull request against **the intent and standards the PR carries**: the spec, plan,
  tasks, and ADRs read at the PR's own head revision, plus the constitution and ADRs in force on the
  **base** branch. That is what lets it report a task marked complete but absent from the diff, scope
  no requirement authorized, or a pattern an ADR forbids — none of which a diff-only reviewer can see.

  Two properties define it:

  - **Every finding is anchored and sourced.** A file, a line, and the clause, requirement id, or named
    principle it rests on. A finding that cannot be anchored and sourced is not reported at all.
  - **The human is the filter.** Nothing is pre-selected. The reviewer chooses which findings are
    published and which verdict to submit, sees the exact body first, and gives a final go-ahead before
    anything is posted. An empty selection posts nothing and is a normal outcome. Approving over a
    blocker the reviewer accepted requires a typed confirmation and is recorded in the published review.

  Findings are graded Blocker / Major / Minor / Nit / Question from a fixed rubric so repeated reviews of
  one revision agree, with floors that keep an explicit constitution violation at Major or above and an
  explicit compliance violation at Blocker. Low confidence cannot be a Blocker — it becomes a Question.

  Publication is a single review event through the reviewer's own `gh` authentication. The agent holds no
  credentials, adds no data path, and stores nothing between runs.

  Two behaviours differ from `create-pr` on purpose:

  - **It hard-stops when `gh` is missing or unauthenticated** rather than degrading, because a review's
    value is the analysis and the analysis needs the PR. Failures *after* that gate — a fork
    restriction, insufficient permission — still degrade gracefully to a rendered body for manual
    posting.
  - **It registers no hook.** Review is on demand only, since the reviewer should not be the author.

  GitHub only in this release, and single-body reviews only — line-anchored inline comments are a
  follow-on.

A command was added, which is why this is a MINOR.

## [1.3.1] - 2026-08-09

### Changed
- **The extension description is now the positioning line used everywhere else:** "TELUS Digital -
  Agentic software engineering across the entire SDLC." It previously enumerated the four shipped
  commands, which meant it needed editing every time an agent was added and disagreed with the
  wording on the landing page and in the README. One line, one place, no drift.
- **The Commands table in `README.md` is generated** from the new root `agents-list.json` roster
  rather than maintained by hand. The region is marked with
  `<!-- SPECTRA:GENERATED START id=spectra-readme-commands -->`; everything around it, including the
  four per-agent sections, stays hand-written. Its Effect column is dropped — `effect: read-write` is
  declared once for the extension in `extension.yml`.
- **The PR agent is titled "GitHub (PR)" everywhere.** It previously appeared as `github`, GitHub,
  GitHub (PR), and "GitHub PR delivery" across four documents. Its command is unchanged:
  `speckit.spectra.create-pr`.

No command was added, changed, or removed, which is why this is a PATCH.

## [1.3.0] - 2026-08-08

### Changed
- **Relicensed from MIT to the Apache License 2.0.** Spectra stays free to use, modify, and
  redistribute for any purpose, including commercially. Apache-2.0 adds an explicit patent grant and
  makes attribution enforceable: redistributions and derivative works must retain the copyright
  notice, ship the `LICENSE` and `NOTICE` files, and state which files were changed
  (§4(b)–4(d)).

### Added
- `NOTICE` — the attribution notice that downstream redistributors are required to carry forward
  under Apache-2.0 §4(d). It now ships inside the extension package.

## [1.2.0] - 2026-07-14

### Added
- **`speckit.spectra.brd`** — a Requirements & Discovery-phase command that transforms a raw business
  requirement (inline text or a `.docx`/`.pdf`/`.md`/`.txt` document) into a structured,
  specify-ready BRD written under `/brds`. It reads project context to ground the document, asks up to
  five clarifying questions only when the requirement has material gaps, never invents requirements
  (genuine unknowns become Open Questions), and hands off to the Spec Kit **specify** command. Its only
  write is the BRD file.
- Bundled the canonical BRD template as `templates/brd-template.md` so the command produces the same
  structure in any installed project.

## [1.1.0] - 2026-07-09

### Changed
- Consolidated the previously separate `adr`, `domain-analyzer`, and `github` extensions into a
  single `spectra` extension. Every capability is now a command under the unified `speckit.spectra.*`
  namespace, matching Spec Kit's `speckit.<extension-id>.<command>` rule (the extension `id` is
  `spectra`):
  - `speckit.adr.new` → `speckit.spectra.adr`
  - `speckit.domain-analyzer.analyze` → `speckit.spectra.domain-analyzer`
  - `speckit.github.create-pr` → `speckit.spectra.create-pr`
- Install once with `specify extension add spectra` to get all three commands. The `after_implement`
  hook now invokes `speckit.spectra.create-pr`.

### Commands
- **`speckit.spectra.adr`** — Create a context-aware Architecture Decision Record grounded in the
  codebase, prior ADRs, and the project constitution; asks up to five clarifying questions and writes
  the ADR under `Docs/ADR/`.
- **`speckit.spectra.domain-analyzer`** — Infer the project's business domain and write an opt-in
  proposal of evidence-backed candidate guardrails to `.specify/memory/domain-analysis.md` for SME
  review and handoff to `/speckit-constitution`. Never edits the constitution or source.
- **`speckit.spectra.create-pr`** — Offer to open a correctly-targeted GitHub PR for the current spec
  branch after `implement`, deriving the base branch from the promotion strategy, confirming before
  any push, and returning the PR URL — with a graceful manual fallback when `gh`, the remote, or the
  network is unavailable.
