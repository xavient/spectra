# Changelog

All notable changes to the `spectra` extension are documented here. This project follows
[Semantic Versioning](https://semver.org/).

## [1.7.0] - 2026-08-21

### Added
- **Both document agents are now driven by an overridable template.** `speckit.spectra.adr` used to carry its
  structure as a literal block inside the command file — there was no file to change. It now ships as
  `templates/adr-template.md`, alongside the BRD template, and both are declared in `extension.yml` under
  `provides.templates`.

- **`.specify/templates/overrides/<name>.md` is the supported way to customize them.** Drop
  `.specify/templates/overrides/adr-template.md` (or `brd-template.md`) into your project, edit it, commit it —
  every document produced from then on follows your structure, on every teammate's machine. Add the sections
  your governance needs, or delete ones you don't want.

  Both commands now resolve their template through Spec Kit's stack, first usable layer wins: project override
  → installed presets → this extension → core `.specify/templates/` → the command's inline skeleton as a last
  resort. A layer that exists but is empty or unreadable is reported and skipped rather than being fatal.

  **This is the part that was broken before.** `brd` read the extension's copy at a hard-coded path, so an
  override was silently ignored, which left editing the installed copy as the only lever — and that edit does
  not survive: extension files are replaced wholesale when the extension updates. Because the path is tracked
  by Git, the edit looks durable and then reverts later inside an unrelated diff. An override lives outside the
  extension tree and survives.

- **Each command reports which template it used**, by path. An override that silently failed to apply
  otherwise looks exactly like one that worked, and the first clue would be a wrongly-shaped document.

### Changed
- **A resolved template is honoured, not repaired.** If your override renames, renumbers, drops, or adds
  sections, the command follows *your* structure and mentions once what it left out, instead of quietly
  reinstating it. Where your template adds sections, they are filled from the same gathered context; where
  there is genuinely nothing to say, the command says so rather than inventing content.

- **The ADR's section list is unchanged**: Context, Decision, Consequences, with the same `Date` and `Status`
  header. With no override in place, output is structurally identical to 1.6.0. Enriching the default was
  deliberately left out of this release — now that every project can add sections itself, changing the shipped
  default would have altered everyone's output while claiming to be additive.

- Constitution **Principle VIII — Documents Are Shaped by Overridable Templates** (constitution 1.7.0) records
  the rule so future document agents inherit it: the structure comes from a registered template resolved
  through the stack, with an inline fallback and never a hard-coded path; the resolved template is honoured as
  authored; the command names the template it used. Resolution stays prompt-expressed, because calling Spec
  Kit's Bash `resolve_template()` would break agent-agnosticism and shipping a resolver of our own would break
  the Markdown-only guarantee — the package still contains no scripts, no binaries, and no hooks.

## [1.6.0] - 2026-08-21

### Changed
- **ADRs and BRDs now go to one place: `docs/adr/` and `docs/brd/`.** `speckit.spectra.adr` used to write
  `Docs/ADR/ADR-NNN-*.md` and `speckit.spectra.brd` used to write `/brds/NNN-*.md` — two different parent
  folders, two different capitalizations, and one path that named the filesystem root rather than the
  project. Both now write under a single root, project-relative and lowercase, one subfolder per artifact
  type. Filenames are unchanged: `docs/adr/ADR-NNN-<title>.md` and `docs/brd/NNN-<title>.md`. The root
  itself is a project setting — see **Added** below.

  The lowercasing is a fix, not a preference. `Docs/ADR/` is a distinct directory on Linux but silently
  aliases into an existing `docs/` folder on a case-insensitive macOS filesystem, so the same command
  produced different layouts on different machines.

- **Existing projects keep their numbering, and their old folder.** Both commands still read the earlier
  locations — `Docs/ADR/` (matched case-insensitively), `brds/`, and `docs/<artifact>/` when a project
  declares a different root — for context and for the next number, so the sequence after this update
  continues from the highest artifact found across old and new instead of restarting at `001`. Those folders
  are read-only to the agent: it reports them once, offers a `git mv` you can run, and moves nothing itself.
  If a new ADR supersedes one that still lives in an earlier folder, the supersession is recorded in the new
  ADR and reported to you rather than written into the old file.

- **Every write scope is unchanged in size.** `brd` still writes exactly one file; `adr` still writes one
  ADR plus, only with your agreement, the superseded-status line and a constitution edit.

### Added
- **A project can move the artifact root with one line.** `docs/` is the default, not a hard-coded path.
  Put this in `.specify/memory/constitution.md` and every Spectra document agent — these two and every one
  we ship later — writes there instead:

  ```text
  Artifact root: documents/
  ```

  The commands offer that line but never write it themselves: producing a document is not a licence to edit
  governance.

- **A publication check before defaulting into `docs/`.** `docs/` is GitHub Pages' only non-root branch
  source and the default source directory for MkDocs and Docusaurus, so on some projects writing there
  publishes the document or breaks a docs build. Both commands now look for that signal — `mkdocs.yml`,
  `docusaurus.config.*`, `docs/_config.yml`, `docs/.nojekyll`, `docs/index.html`, `docs/conf.py`, or a Pages
  configuration pointing at `docs` — and when they find one with no declared root, they say so before
  writing, recommend `documents/`, and ask. Unanswered, they take the non-publishing option: a misplaced
  private file is one `git mv` away, while a BRD served on the public web cannot be recalled from caches or
  forks. The question does not count against either command's five-question limit, because it is about
  where to write rather than what to record.

- **Constitution Principle VII — Document Artifacts Live Under One Declared Root** (constitution 1.6.0).
  Every command producing a durable Markdown deliverable writes it to `<artifact-root>/<artifact>/` with a
  lowercase kebab-case slug, one artifact type per folder, three-digit numbering. Spec Kit's own
  `.specify/` and `specs/` are carved out, so `speckit.spectra.domain-analyzer` writing
  `.specify/memory/domain-analysis.md` stays compliant — that is context for another command, not a
  deliverable. The point is forward-looking: the roster has a dozen more document producers under
  development, and each one now inherits its output location instead of choosing a new top-level folder.

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
