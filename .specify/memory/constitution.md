<!--
SYNC IMPACT REPORT
==================
Version: 1.7.0 → 1.7.1
Bump type: PATCH — a clarification. No new obligation; no principle added, removed, or redefined.
Rationale: Principle VIII requires a template for "every command that produces a durable Markdown
  deliverable". Applying it to `speckit.spectra.create-pr` exposed an ambiguity: a pull request body is a
  Markdown document a human reads, but it is emitted to GitHub rather than written into the artifact root.
  A literal reader could argue VIII does not reach it, which would leave PR bodies as the one document
  Spectra composes with no template and no override — exactly the gap VIII exists to close.

  The clarification says the obvious thing explicitly: a deliverable is the document, not the destination.
  A file in `docs/adr/` is one; so is a PR body, a review comment, or an issue description. Only Principle
  VII's *location* rules are limited to files on disk.

Modified principles:
  VIII — one paragraph added stating that emitted documents count as deliverables
Added sections: (none)
Removed sections: (none)

Templates & docs in sync:
  - spectra/templates/pr-template.md ✅ — new: the PR body structure, overridable like adr/brd
  - spectra/commands/create-pr.md ✅ — resolves pr-template through the stack and reports the path
  - spectra/extension.yml, catalog.json, spectra/CHANGELOG.md, docs/packages/spectra.zip ✅ — 1.8.0
  - spectra/README.md, AGENTS_LIST.md, docs/index.html, test/README.md ✅ — the override documented
  - tests/test_document_templates.py ✅ — pr-template joins the guarded set
  - specs/014-create-pr-template/ ✅ — spec, plan, tasks

Follow-up TODOs: (none)

--- Previous report ---
Version: 1.6.0 → 1.7.0
Bump type: MINOR — one new principle. No existing principle redefined or removed.
Rationale: Principle VII settled *where* a produced document goes. Nothing said anything about *how it
  is shaped*, and the two shipped document agents had drifted into opposite answers. `brd` loaded a
  shipped asset — `spectra/templates/brd-template.md` — from a hard-coded path. `adr` carried its
  structure as a fenced literal inside the command file, introduced by "use **exactly** this template …
  do not add, rename, or reorder sections". One was an asset a team could in principle change; the other
  could not be changed at all.

  Neither was actually overridable in a way that survives. Spec Kit already resolves templates through a
  four-layer stack — project override, presets, extension, core — but `brd` read layer 3 directly, so an
  override at `.specify/templates/overrides/brd-template.md` was silently ignored. That left editing the
  installed copy as the only route, and measurement against Spec Kit 0.16.5 confirmed it is a trap: an
  edit inside `.specify/extensions/spectra/templates/` survives a no-op update but is destroyed by the
  tree-replace that any version bump performs, while `.specify/.gitignore` tracks the edit — so it is
  committed, looks durable, and is reverted later as noise in an unrelated diff.

  Principle VIII fixes the shape question the way VII fixed the location question: one rule, stated once,
  inherited by every future document agent. A document's structure comes from a registered template
  resolved through the stack, with an inline last-resort skeleton; the command reports which template won,
  honours what the resolved template says rather than repairing it, and never hard-codes a path.

  Two constraints are written in because they are easy to violate with good intentions. Resolution MUST be
  prompt-expressed: `resolve_template()` is a Bash function in core's script tree, so calling it breaks
  PowerShell-only setups (Principle III), and shipping our own resolver script would break the
  Markdown-only supply-chain promise the README makes and the security review depends on. And a resolved
  template MUST be honoured as authored — a command that quietly re-adds a section the team deleted has
  turned their override into a suggestion.

Modified principles: (none)
Added sections:
  VIII — Documents Are Shaped by Overridable Templates
Removed sections: (none)
Other edits: Development Workflow step 2 cites Principle VIII alongside VII in the Constitution Check gate.

Templates & docs in sync:
  - spectra/templates/adr-template.md ✅ — new: today's ADR structure, verbatim, in the house style of
    brd-template.md. No new sections, so no existing user's output changes.
  - spectra/templates/brd-template.md ✅ — content unchanged
  - spectra/commands/adr.md ✅ — Step 4 resolves the template through the stack; the former literal is now
    the inline last-resort skeleton at the end of the file; reports the resolved path
  - spectra/commands/brd.md ✅ — the hard-coded read is replaced by the same resolution block; same
    reporting, fall-through, and honour-don't-repair rules
  - spectra/extension.yml ✅ — provides.templates declares adr-template and brd-template; version 1.7.0
  - catalog.json ✅ — version and updated_at (the catalog schema carries a command count only)
  - spectra/CHANGELOG.md ✅ — [1.7.0]
  - docs/packages/spectra.zip ✅ — rebuilt; contains both templates
  - spectra/README.md, AGENTS_LIST.md, docs/index.html, test/README.md ✅ — the override path is
    documented as the supported customization point, and stated to survive extension updates
  - CONTRIBUTING.md ✅ — a new document agent ships a registered template and resolves it through the stack
  - tests/test_document_templates.py ✅ — new: registration completeness both ways, heading parity between
    each shipped template and its command's inline skeleton, four-layer coverage in both commands, no
    hard-coded template path, and no script or binary in the package
  - .specify/templates/*.md ✅ — the Constitution Check gate is generic; no principle names cited
  - specs/013-overridable-templates/ ✅ — spec, plan, tasks, incl. the Phase 0 measurements

Deliberately unchanged:
  - the ADR template's section list — enriching it is now every project's own call
  - VERSION / spectra_cli/ — the CLI channel did not change (Principle VI)

Follow-up TODOs: (none)

--- Previous report ---
Version: 1.5.0 → 1.6.0
Bump type: MINOR — one new principle. No existing principle was redefined or removed.
Rationale: Spectra's two document-producing agents each invented their own output location. `adr` wrote
  `Docs/ADR/ADR-NNN-*.md`; `brd` wrote `/brds/NNN-*.md`. Nothing in the constitution said where a
  deliverable belongs, so each command answered the question independently and gave two different
  answers — differing in parent folder, in case, and in whether the path was even project-relative
  (`/brds` names the filesystem root when read literally).

  The roster is 44 agents, many of them document producers still under development (threat model, API
  design, Article 30 records, PIAs). Left unstated, that convention would be re-invented 20 more times
  and a consumer's project root would accumulate an unrelated top-level folder per agent. Principle VII
  settles it once: `<artifact-root>/<artifact>/`, lowercase kebab-case slug, one artifact type per
  folder, created on demand. `adr` → `docs/adr/`, `brd` → `docs/brd/`, and every future agent inherits
  the answer instead of choosing.

  The root is **declarable rather than fixed**, defaulting to `docs/`. `docs/` is GitHub Pages' only
  non-root branch source and the default source directory for MkDocs and Docusaurus, so for a minority of
  projects writing there publishes the artifact to the public web or breaks a docs build — and a BRD
  carries revenue targets, named stakeholders, and competitive rationale. Whether `docs/` is safe is a
  fact about the project, unknowable when the command is authored, so a project overrides it with one
  line in its constitution (`Artifact root: documents/`) that every document agent honours. Commands must
  check for the publication signal before defaulting into `docs/`, recommend `documents/` when they find
  one, and take the non-publishing option when the choice cannot be obtained: a misplaced private file
  moves with one command, a published BRD cannot be recalled from caches or forks. Commands offer the
  declaration line and never write it themselves — producing a document is not a licence to edit
  governance.

  Two details are recorded because they are correctness, not style. Paths MUST be lowercase and
  project-relative: `Docs/ADR/` is a distinct directory on Linux but silently aliases into an existing
  `docs/` on a case-insensitive macOS filesystem, so the same command produced different layouts on
  different machines. And a command MUST read the locations earlier versions wrote to for numbering while
  never relocating them — without that, updating the extension gives a team a second `ADR-001` and splits
  one decision log across two folders, while moving files for them would exceed a documentation agent's
  write scope.

  Spec Kit's own locations are carved out. `.specify/` and `specs/` are Spec Kit's, and a command
  writing there — as `domain-analyzer` does with `.specify/memory/domain-analysis.md` — is writing
  context for another command to consume, not a deliverable for a human to read.

Modified principles: (none)
Added sections:
  VII — Document Artifacts Live Under One Declared Root
Removed sections: (none)
Other edits: Development Workflow step 2 now cites Principle VII in the Constitution Check gate.

Templates & docs in sync:
  - spectra/commands/adr.md ✅ — `Docs/ADR/` → `<artifact-root>/adr/` (default `docs/adr/`) throughout,
    incl. the suggested `git add`; resolves the declared root and checks for the publication signal
    before defaulting; legacy `Docs/ADR/` read for context and numbering, reported once, never moved
  - spectra/commands/brd.md ✅ — `/brds` → `<artifact-root>/brd/` (default `docs/brd/`) throughout, incl.
    the front-matter description and the one-rule write scope; same root resolution, with the extra note
    that a BRD's contents make publication the more damaging default; legacy `brds/` read, never moved
  - spectra/extension.yml ✅ — `brd` description no longer names `/brds`; version 1.5.0 → 1.6.0
  - catalog.json ✅ — version and `updated_at` mirrored (1.6.0)
  - spectra/CHANGELOG.md ✅ — `[1.6.0]` entry records both moves, the declarable root, the publication
    check, and the legacy-read behavior
  - docs/packages/spectra.zip ✅ — rebuilt with tools/build_package.py
  - spectra/README.md, AGENTS_LIST.md, docs/index.html, test/README.md ✅ — every user-facing statement
    of where these agents write now names the canonical folders and the override
  - CONTRIBUTING.md ✅ — new document-producing agents are pointed at Principle VII, including the duty
    to honour a declared root
  - tests/test_doc_output_paths.py ✅ — new: fails the suite when a shipped command file names a legacy
    path or a non-conforming output folder, when a document command stops resolving the declared root, or
    when it stops checking for the publication signal — so the principle is enforced rather than reviewed
  - .specify/templates/*.md ✅ — the Constitution Check gate is generic; no principle names cited
  - README.md ✅ — states no output paths; nothing to change
  - specs/012-doc-output-convention/ ✅ — spec, plan, and tasks for this change

Deliberately unchanged:
  - brds/ (this repository's own 8 BRDs) — historical inputs cross-referenced from specs/; Principle VII
    governs newly produced artifacts and does not require relocating an existing set
  - VERSION / spectra_cli/ — the CLI channel did not change (Principle VI)

Follow-up TODOs: (none)

--- Previous report ---
Version: 1.4.0 → 1.5.0
Bump type: MINOR — materially expanded guidance in Principle VI (one new MUST), plus a factual
  correction in the same principle.
Rationale: CLI 6.0.0 retired `spectra cli version` and `spectra cli update`, folding both into the
  top-level `spectra version` / `spectra update`, which now report and update all four components of the
  stack (Spec Kit's CLI, the core agents, the `spectra` command, and Spectra's agents).

  That made one sentence in Principle VI false: it named `spectra cli update` as a consumer of
  `/releases/latest`. Corrected to `spectra update`.

  It also created a governance-relevant constraint that nothing previously recorded. Because
  `spectra version` reports the whole stack, it requires a Spec Kit project with Spectra installed — so
  it cannot answer "what version is this command?" in a bare directory. Three checks need exactly that
  answer: CI's `VERSION`-parity assertion, the release smoke test, and the clean-room check that a
  project uninstall leaves the command intact. All three now read the `cli vX.Y.Z` line from bare
  `spectra`, and the last one runs precisely in the state where `spectra version` correctly refuses.
  Principle VI now makes that line a MUST, so a future change cannot quietly remove it and break the
  release procedure without failing loudly.

Modified principles:
  VI — `spectra cli update` → `spectra update` (the subcommand was retired in CLI 6.0.0); new MUST
       requiring the CLI's own version to stay readable outside a Spec Kit project
Added sections: (none)
Removed sections: (none)

Templates & docs in sync:
  - .specify/templates/plan-template.md ✅ — Constitution Check gate is generic; no principle names cited
  - .specify/templates/spec-template.md ✅ — no constitution references
  - .specify/templates/tasks-template.md ✅ — no constitution references
  - .kiro/prompts/speckit.*.md ✅ — none pin a constitution version or principle number
  - README.md ✅ — "Keeping everything up to date" rewritten for the unified commands; 6.0.0 note added
  - CONTRIBUTING.md ✅ — release smoke test now reads bare `spectra`; stale command references fixed
  - docs/index.html ✅ — landing page advertises the two unified commands
  - test/README.md ✅ — clean-room rows 1b, 5, 6b, 9, 10 rebuilt around the new surface
  - .github/workflows/ci.yml ✅ — VERSION parity asserted via `importlib.metadata` plus the bare-`spectra`
    banner; a new step covers the retired subcommands
  - VERSION ✅ — 6.0.0 (CLI channel, MAJOR: the command surface lost two verbs)
  - spectra/extension.yml, catalog.json ✅ — unchanged at 1.3.1; the channels stayed decoupled, as
    Principle VI requires

Follow-up TODOs: (none)

--- Previous report ---
Version: 1.3.0 → 1.4.0
Bump type: MINOR — materially expanded guidance in Principle V.
Rationale: Principle V asserted two things this repository no longer does. It said there is no build
  script, and that the Agents table in README.md is updated by hand when a command introduces or
  changes an agent. Both became untrue with the agent roster: `agents-list.json` is now the single
  source of truth for what Spectra offers, and `tools/generate_agent_docs.py` rewrites every
  *structured* agent listing from it — the README Agents table, the Spec Kit core and Roadmap sections
  of AGENTS_LIST.md, and the Commands table in spectra/README.md. `tools/build_package.py` likewise
  builds the zip that used to be assembled by hand.

  The amendment adds the roster to Principle V's sync list, states the generated/hand-authored split
  explicitly (if it is a table or a list it is generated; if it is a paragraph it is written), extends
  the no-drift clause to AGENTS_LIST.md and the roster, generalizes the landing page's
  no-hard-coded-versions rule to cover the extension description and agent data the page now fetches,
  and records the new CI assertions that make the split enforceable rather than aspirational. Also
  updates two references to the `spectra --update` / README-table workflow that CLI 5.0.0 and the
  generator replaced.

Modified principles:
  V  — no-build-script clause removed; roster and generator added to the sync obligations; the
       generated vs hand-authored boundary stated; no-drift and no-hard-coded rules widened
  VI — `spectra --update` → `spectra cli update` (the flag was removed in CLI 5.0.0)
Added sections: (none)
Removed sections: (none)

Templates & docs in sync:
  - agents-list.json ✅ — new: the roster, 44 agents
  - tools/generate_agent_docs.py ✅ — new: owns four generated regions; `--check` verifies them
  - tools/build_package.py ✅ — new: deterministic zip rebuild
  - README.md / AGENTS_LIST.md / spectra/README.md ✅ — agent listings are now generated regions
  - CONTRIBUTING.md ✅ — "Add a new command" names the roster, the generator, and the prose block
  - .github/workflows/ci.yml ✅ — runs `tools/generate_agent_docs.py --check`
  - .specify/templates/*.md ✅ — unaffected (the Constitution Check gate is generic)

Follow-up TODOs: (none)

--- Previous report ---
Version: 1.2.0 → 1.3.0
Bump type: MINOR — materially expanded guidance in Principle VI and Publishing & Distribution
  Standards; two factual corrections in Principle V.
Rationale: The installer channel changed shape. `spectra-setup.py` — a standalone script downloaded
  from a GitHub Release asset — is retired in favour of `spectra_cli/`, installed as a `uv` tool from
  this repo's git URL and exposing a `spectra` command. Principle VI now describes that channel, and
  settles the question the change surfaced: with two independently-versioned channels in one repo,
  which one owns git tags. Answer: the CLI, exclusively — the catalog has nothing to tag, since
  merging to `main` is its release. Adds the run-time catalog read that makes channel independence
  real (adding an agent needs no CLI release), the VERSION single-sourcing rule the release workflow
  enforces, and the no-hard-coded-versions rule for the landing page.

  Two corrections to Principle V, which asserted things that were not true: GitHub Pages is enabled
  (serving `main` `/docs`), not disabled; and the catalog/package sync is now CI-enforced rather than
  purely a review obligation.

Principles:
  I.   Spec-Driven Development (We Dogfood Spec Kit)
  II.  A Single Self-Contained Extension
  III. Agent-Agnostic Commands
  IV.  Context-Aware by Default
  V.   The Catalog and Package Are Maintained in Sync
  VI.  Two Independently-Versioned Release Channels

Sections: Publishing & Distribution Standards · Development Workflow ·
  Version Control & Branching Strategy · Governance

Modified principles:
  V  — corrects the GitHub Pages claim; adds the no-hard-coded-versions rule for docs/index.html;
       points the channel cross-reference at the CLI instead of the retired script
  VI — installer channel → CLI channel; adds the tags-belong-to-the-CLI rule and the run-time
       catalog read
Added sections: (none)
Removed sections: (none)

Templates & docs in sync:
  - .specify/templates/plan-template.md ✅ (Constitution Check gate is generic)
  - .specify/templates/spec-template.md ✅
  - .specify/templates/tasks-template.md ✅
  - README.md ✅ — Installation rewritten around `uv tool install`; adds "Two release channels"
  - CONTRIBUTING.md ✅ — "Release the CLI (spectra-cli)" replaces "Release the installer"
  - catalog.json / spectra/extension.yml (extension/catalog version) ✅ — unchanged at 1.3.0
  - VERSION (CLI version) ✅ — 3.0.0, succeeding installer v2.0.0
  - .github/workflows/{ci,release}.yml ✅ — enforce VERSION/tag parity and catalog sync

Follow-up TODOs: (none)
-->

# Spectra Constitution

Spectra is a curated set of [Spec Kit](https://github.com/github/spec-kit) commands — delivered as a
single self-contained Spec Kit extension — that enable full agentic development across the entire
software development lifecycle (SDLC), built and maintained by TELUS Digital. This constitution
governs how Spectra itself is built and how every command in the extension is authored, published,
and maintained.

## Core Principles

### I. Spec-Driven Development (We Dogfood Spec Kit)

Spectra is built using the same spec-driven workflow it ships to others. Non-trivial work MUST flow
through Spec Kit — `specify` → `plan` → `tasks` → `implement` — rather than ad-hoc edits. Specs live
under `specs/`, and the project constitution under `.specify/memory/` is the source of truth that
plans are checked against.

Rationale: Spectra's value proposition is agentic SDD across the SDLC. If we do not use it to build
ourselves, we cannot credibly recommend it, and we lose our best feedback loop on the extension we
publish.

### II. A Single Self-Contained Extension

Spectra ships as exactly **one** self-contained Spec Kit extension: a single folder `spectra/` at the
repository root whose name equals the extension `id` (`spectra`, lowercase). It MUST contain one
`extension.yml` (with `id: spectra`), a `commands/` directory, `README.md`, `CHANGELOG.md`, and
`LICENSE`. Every Spectra capability MUST be a command file under `spectra/commands/`, registered in
the single `spectra/extension.yml`; new top-level extension folders MUST NOT be created for new
capabilities. The extension MUST NOT depend on any other extension; it installs and runs on its own.
The authoritative structure is the [Spec Kit Extension Development Guide](https://github.com/github/spec-kit/blob/main/extensions/EXTENSION-DEVELOPMENT-GUIDE.md).

Rationale: Users install one extension — `specify extension add spectra` — and get every command.
Spec Kit's own command-name rule (Principle III) forces this: because a command's namespace segment
must equal the extension `id`, every `speckit.spectra.*` command can only live in a single extension
whose id is `spectra`. One extension keeps the package portable, versioned as a whole, and consistent
by construction.

### III. Agent-Agnostic Commands

Command files MUST be written in Spec Kit's generic format using `$ARGUMENTS` for user input, and
MUST NOT hard-code any single agent's invocation syntax. Each command MUST be namespaced
`speckit.spectra.<command>` — a fixed `spectra` segment followed by a clear, descriptive command
name (for example `speckit.spectra.adr`, `speckit.spectra.domain-analyzer`,
`speckit.spectra.create-pr`) — MUST begin with YAML front matter containing a `description`, and MUST
be registered in `provides.commands`.

The namespace is not a stylistic choice: Spec Kit validates command names against the pattern
`^speckit\.<extension-id>\.<command>$`, so the **middle segment MUST equal the extension `id`**.
Spectra's id is `spectra`, therefore every command is `speckit.spectra.<command>`. When constructing
or reviewing a command, consult the authoritative
[Spec Kit Extension Development Guide](https://github.com/github/spec-kit/blob/main/extensions/EXTENSION-DEVELOPMENT-GUIDE.md)
for the manifest schema, the command-name pattern, the command-file format, and validation rules.

Rationale: Spec Kit translates one source file into each agent's native format at install time. A
single agent-neutral source supports every agent (slash-command and skills mode alike); hard-coding
one agent's syntax breaks that promise. Grounding command construction in the upstream guide keeps
Spectra valid against the exact rules Spec Kit enforces at install time.

### IV. Context-Aware by Default

Commands MUST read real project context — the constitution under `.specify/memory/`, specs under
`specs/`, existing artifacts, and source code — before acting, rather than blindly filling a
template. A command that ignores the project it runs in is a defect.

Rationale: The differentiator for Spectra commands over generic boilerplate is that they ground
their output in the actual codebase and its constitution. Context-awareness is the feature.

### V. The Catalog and Package Are Maintained in Sync

The repository is **public** — anyone can access it with no authentication — and Spectra is
distributed straight from it over direct `raw.githubusercontent.com` links: the root `catalog.json`
is the install-facing catalog and the single downloadable package lives at `docs/packages/spectra.zip`.
GitHub Pages serves `main` `/docs` at <https://xavient.github.io/spectra/>, but it publishes the
landing page only — **no part of the install path depends on it.** **Anyone can add the catalog and
install the extension anonymously.** Two small maintainer scripts under `tools/` produce the generated
artifacts — `build_package.py` for the zip and `generate_agent_docs.py` for the agent listings — and
their output is committed rather than built on demand, so the repository always reads correctly for
someone who never runs either. Everything else is maintained by hand. Completing, changing, or releasing
the extension MUST include, in the same change:

- registering the agent in `agents-list.json` — the **single source of truth for the roster**;
- building the package into `docs/packages/spectra.zip` (a single top-level `spectra/` folder, the
  layout Spec Kit expects) with `tools/build_package.py`;
- updating `catalog.json` — the single source of truth for the catalog — so the `spectra` entry
  (name, description, version, tags, command count, and `download_url`) matches `spectra/extension.yml`
  and the new zip;
- updating `docs/index.html` so the landing page lists the extension and its commands;
- regenerating every structured agent listing with `tools/generate_agent_docs.py`, and hand-writing the
  per-agent prose block a newly shipped agent needs; and
- committing `agents-list.json`, `catalog.json`, `docs/`, `README.md`, `AGENTS_LIST.md`, and the
  `spectra/` folder, then pushing to `main`.

**The roster is authored once and published everywhere.** `agents-list.json` declares which agents
Spectra offers; every *structured* listing of agents is generated from it and MUST NOT be hand-edited.
The generated regions — the Agents table in `README.md`, the Spec Kit core and Roadmap sections of
`AGENTS_LIST.md`, and the Commands table in `spectra/README.md` — are delimited by
`<!-- SPECTRA:GENERATED START id=… -->` markers and carry a do-not-edit notice. Per-agent explanatory
prose stays hand-authored and MUST NOT be generated; automation guarantees only that it *exists*, never
what it says. The division is by kind of content, not by file: if it is a table or a list, it is
generated; if it is a paragraph, it is written.

`catalog.json`, `docs/index.html`, `README.md`, `AGENTS_LIST.md`, and the published
`docs/packages/spectra.zip` MUST never drift from the `spectra/` folder or from `agents-list.json`.

This sync obligation governs the **catalog channel only** (the extension, its package, and the pages
that link to them). The `spectra` CLI is a *separate* distribution channel with its own version and is
NOT expected to move in lockstep with the catalog — it is governed by Principle VI.

The landing page MUST NOT hard-code data that another artifact already defines — neither channel's
version number, nor the extension's description, nor the agent roster. `docs/index.html` reads the
extension version and description from `catalog.json`, the agent information from `agents-list.json`,
and the CLI version from the newest published GitHub Release, all at page load. A value typed into HTML
is drift waiting to happen; a value fetched from the artifact that defines it cannot drift.

Rationale: The repo is the catalog channel's only distribution point — users discover and install the
extension entirely from it, against the raw `catalog.json`. A stale catalog or a missing zip ships a
broken install. Keeping a single catalog entry and rebuilding the zip as part of finishing a command
keeps the landing page, catalog, and download link consistent by construction.

### VI. Two Independently-Versioned Release Channels

Spectra ships through **two** distribution channels, and each carries its **own** version number on its
**own** cadence. They are NOT 1:1 and MUST be versioned independently:

- **Catalog channel** — the `spectra` extension, distributed over the raw `catalog.json` and
  `docs/packages/spectra.zip` links. Its version is authoritative in `spectra/extension.yml` (mirrored
  into the `spectra` entry of `catalog.json`) and MUST bump — per SemVer — whenever a command (agent) is
  added, changed, or removed. This channel is **never tagged**: merging to `main` is its release.
- **CLI channel** — the `spectra_cli/` package, distributed as a `uv` tool installed from this repo's
  git URL (`uv tool install spectra-cli --from git+https://github.com/xavient/spectra`). Its version is
  authoritative in the root `VERSION` file (read by `pyproject.toml`, reported at runtime via
  `importlib.metadata`, and mirrored by the release tag) and MUST bump — per SemVer — only when the CLI
  itself changes in a way consumers should pick up.

**Git tags and GitHub Releases on this repository belong to the CLI channel, and only to it.** Tags MUST
be bare semver (`X.Y.Z`); Releases MUST be titled `Spectra CLI X.Y.Z`. The catalog channel MUST NOT be
tagged or released. Reserving tags for one channel is what makes `/releases/latest` an unambiguous
answer to "what is the newest `spectra` command" — which both `spectra update` and the landing page
depend on. If the catalog also cut releases, the CLI's update check could resolve to an extension
release and attempt to install it as a version of itself.

**The CLI's own version MUST remain readable outside a Spec Kit project.** `spectra version` reports the
whole stack, so it legitimately requires a project with Spectra installed and cannot answer "what version
is this command?" from an arbitrary directory. Bare `spectra` MUST therefore keep printing a `cli vX.Y.Z`
line, and MUST keep working anywhere while changing nothing. Three things depend on exactly that: the CI
assertion that the installed distribution matches the committed `VERSION`, the release smoke test, and the
clean-room check that removing a project's agents leaves the command intact. None of them can use
`spectra version` — the last one deliberately runs in the state where `spectra version` correctly
refuses. A change that drops the banner's version line would break all three without failing loudly.

The two version numbers MUST NOT be coupled: adding or changing a command (an agent/extension) bumps the
catalog/extension version **without necessarily** touching the CLI, and changing `spectra_cli/` bumps the
CLI version **without necessarily** touching the extension or catalog. A change to one channel MUST NOT
force a version bump of the other, and the two versions are not expected to match at any point in time.

To keep that independence real rather than aspirational, the CLI MUST NOT hard-code the set of
extensions it installs. It MUST read `catalog.json` at run time and install what the catalog
advertises, so adding an agent reaches every existing install with no CLI release at all.

Rationale: The catalog and the CLI serve different needs and change for different reasons — the catalog
evolves as we add SDLC agents, while the CLI changes only when the onboarding flow does. Forcing a
shared version number would either inflate the CLI on every agent addition or block agent releases on
unrelated CLI work. Independent SemVer per channel keeps each artifact's version honest about what
actually changed in it.

### VII. Document Artifacts Live Under One Declared Root

Every command that produces a durable Markdown **deliverable** for the user's project MUST write it into
`<artifact-root>/<artifact>/`, where `<artifact>` is the artifact type as a lowercase kebab-case slug and
`<artifact-root>` is the project's single artifact root. The subfolder MUST be created on demand, MUST hold
exactly **one** artifact type, and the command MUST NOT write anywhere else. Filenames MUST carry a
zero-padded three-digit sequence number scoped to that subfolder, starting at `001`. The two shipped
document agents define the pattern: `<artifact-root>/adr/ADR-NNN-<kebab-title>.md` and
`<artifact-root>/brd/NNN-<kebab-title>.md`. A new document-producing agent MUST take its own sibling
subfolder — `<artifact-root>/threat-model/`, `<artifact-root>/api-design/` — and MUST NOT introduce a
top-level folder of its own.

**The root defaults to `docs/` and is declarable per project.** A project overrides it with a single line
in its constitution, matched case-insensitively:

```text
Artifact root: documents/
```

A declared root MUST be honoured by **every** document-producing command, so a project decides this once
and every present and future agent inherits it. It MUST be project-relative — no leading slash, no `..` —
and a command that finds an unusable value MUST say so and fall back to the default rather than guess.

**A command MUST NOT write that declaration itself.** It offers the exact line and lets the user add it.
Producing a document is not a licence to edit governance; the one constitution change a Spectra command
may propose is one that is *about* the decision it just recorded, and even that requires explicit
approval.

**Defaulting into `docs/` requires a publication check first.** `docs/` is GitHub Pages' only non-root
branch source and the default source directory for MkDocs and Docusaurus, so on a minority of projects
writing there publishes the artifact to the web or breaks a documentation build. Before defaulting, a
command MUST look for that signal — `mkdocs.yml`, `docusaurus.config.*`, `docs/_config.yml`,
`docs/.nojekyll`, `docs/index.html`, `docs/conf.py`, or a Pages configuration pointing at `docs` — and,
finding one with no declared root, MUST surface it, recommend `documents/`, and let the user choose. Where
the choice cannot be obtained it MUST take the non-publishing option: a document written to the wrong
private folder is moved with one command, while a business requirements document served on the public web
cannot be recalled from caches, clones, or forks.

**Spec Kit's own locations are outside this rule.** `.specify/` (constitution, memory, extension assets)
and `specs/` belong to Spec Kit, and a command writing there — as `speckit.spectra.domain-analyzer` does
with `.specify/memory/domain-analysis.md` — is writing **context** for another command to consume, not a
deliverable for a human to read. The rule governs deliverables.

**Paths MUST be lowercase and project-relative.** Not `Docs/`, not `/docs/`. This is correctness, not
style: mixed case is a distinct directory on Linux but silently aliases into an existing `docs/` on a
case-insensitive macOS filesystem, so one command produces two different layouts; and a leading slash
names the filesystem root rather than the project.

**A location an earlier version wrote to MUST be read, reported, and left alone.** That covers both the
pre-1.6.0 folders (`Docs/ADR/`, `brds/`) and the default root itself once a project declares a different
one. The command MUST read those locations — matching case-insensitively — for context and for sequence
continuity, so the next number is one greater than the highest found across the canonical folder *and*
every superseded one. It MUST report the superseded folder once, name the canonical one, and offer the
move as a command the user can run. It MUST NOT move, rename, modify, or delete anything there itself.

Rationale: A consumer installs **one** extension and gets many document-producing agents. If each picks
its own folder, the project root accumulates an unrelated top-level directory per agent and nobody can
predict where an agent's output went — the roster already lists a dozen more document producers under
development. One root, one subfolder per artifact type, decided once, means every future agent inherits
the answer instead of inventing one. The root is declarable rather than fixed because whether `docs/` is
safe is a fact about the project that cannot be known when the command is authored: `docs/adr/` is the
convention most teams expect, and the minority who publish `docs/` need an escape hatch that costs them
one line and then applies everywhere. Reading superseded locations rather than ignoring them is what keeps
a cut-over from producing a duplicate `ADR-001`; refusing to move them is what keeps a documentation agent
inside the write scope it promises.

### VIII. Documents Are Shaped by Overridable Templates

Where Principle VII settles **where** a produced document goes, this settles **how it is shaped**. Every
command that produces a durable Markdown deliverable MUST take its structure from a **template**, and that
template MUST be:
- **Shipped as an asset**, not embedded as a literal in the command file — one file per document type under
  `spectra/templates/`, named `<artifact>-template.md`;
- **Registered** in `spectra/extension.yml` under `provides.templates` with `name`, `file`, and
  `description`. An unregistered template file, or a registered entry whose file is missing, is a defect;
- **Resolved through Spec Kit's stack**, highest priority first: `.specify/templates/overrides/<name>.md` →
  `.specify/presets/<preset-id>/templates/<name>.md` → `.specify/extensions/<ext-id>/templates/<name>.md` →
  `.specify/templates/<name>.md` → the command's own inline skeleton as the last resort. A command MUST NOT
  hard-code a single template path, and MUST take the first readable, non-empty layer.

**"Deliverable" means the document, not the destination.** A file written into the artifact root is one; so is a
Markdown document a command **emits** without saving locally — a pull request body, a review comment, an issue
description. If a human reads it and a command composed it, it is shaped by a template. Only the *location*
rules of Principle VII are limited to files on disk.

**The project override is the supported customization point.** `.specify/templates/overrides/<name>.md` is
committed, applies to the whole team, and sits outside the extension tree — so it survives
`specify extension update`. Editing the *installed* copy under `.specify/extensions/` MUST NOT be documented
as the way to customize anything: extension-provided files resolve as `replace`, so a version bump discards
the edit, and because the path is tracked by Git the change looks durable until it silently reverts.

**A resolved template is honoured, not repaired.** A command MUST follow the sections the resolved template
declares, in its order, and MUST NOT add, rename, or reorder them. Where a template omits a section the
command would ordinarily fill, the command MUST note the omission rather than reinstating it — anything else
turns a team's override into a suggestion. Guidance comments and `[PLACEHOLDER]` tokens MUST be stripped from
the output whichever layer the template came from.

**The command MUST report which template it used**, naming the resolved path. Without that, an override that
failed to apply is indistinguishable from one that applied, and the user's first clue is a wrongly-shaped
document.

**Resolution MUST be expressed as prompt instructions.** Spec Kit's `resolve_template()` is a Bash function
in core's script tree: depending on it would break agent-agnosticism (Principle III) wherever Bash is not the
script flavour, and shipping a resolver of our own would break the Markdown-only guarantee the published
package makes — no scripts, no binaries, no post-install hooks. The commands therefore state the same
priority order in prose.

Rationale: A template is the difference between a consistent document set and a pile of differently-shaped
files, and an *overridable* template is the difference between Spectra's opinion and the team's. Both shipped
document agents had a template; only one was a file, and neither honoured the project's own override — so a
team's only lever was editing an installed file that the next update deletes. Shipping the structure as a
registered asset resolved through the stack means one file in a repository changes every document produced
from then on, for everyone, permanently. Requiring the same of future document agents keeps that promise from
being re-litigated per agent, which is exactly how the `adr`/`brd` divergence arose in the first place.

## Publishing & Distribution Standards
- **Semantic Versioning (per channel).** Both release channels follow [SemVer](https://semver.org/) on
  independent cadences (Principle VI). Each **extension (catalog) release** MUST bump `extension.version`
  in `spectra/extension.yml` and the matching `version` in the `catalog.json` entry, and add a matching
  `spectra/CHANGELOG.md` entry under that version heading; renaming or removing a command is a breaking
  (MAJOR) change. Each **CLI release** MUST bump the root `VERSION` file and be published under a
  matching bare-semver Git tag `X.Y.Z`; a breaking change to the install flow, the command surface, or
  the prerequisites is MAJOR. A bump to one channel MUST NOT be mirrored onto the other unless that
  channel actually changed.
- **The CLI version is single-sourced and CI-enforced.** `VERSION` is the sole source of truth for the
  CLI: `pyproject.toml` reads it and the tool reports it via `importlib.metadata`. The release workflow
  MUST refuse to publish when the pushed tag and `VERSION` disagree, so the committed version, the git
  tag, and the installed version cannot drift.
- **Compatibility pinning.** `spectra/extension.yml` MUST set `requires.speckit_version` to the Spec
  Kit version range actually tested against. Re-test when Spec Kit is upgraded.
- **Required manifest fields.** `extension.yml` MUST provide `schema_version`, `id`, `name`,
  `version`, `description`, `category`, `effect` (`read-only` or `read-write`), `author`,
  `repository`, `license`, `requires.speckit_version`, and `provides.commands[]` (with each command's
  `name`, `file`, and `description`).
- **Authorship & license.** Author is `TELUS Digital`; the extension is Apache-2.0 licensed unless
  explicitly stated otherwise, and carries its own `LICENSE` **and** `NOTICE`. Both MUST ship inside
  the published package — Apache-2.0 §4(d) makes the `NOTICE` attribution binding on downstream
  redistributors, so dropping it silently weakens the attribution requirement.
- **No silent drift.** Before publishing, verify that `catalog.json`, `docs/packages/spectra.zip`, and
  `docs/index.html` all agree with the `spectra/` folder and use the raw
  `raw.githubusercontent.com/xavient/spectra/main/...` URLs; any mismatch MUST be resolved first. CI
  enforces this: `.github/workflows/ci.yml` fails when `extension.yml` and `catalog.json` disagree on
  the version or the command count, when the committed zip has drifted from the `spectra/` folder, or
  when `tools/generate_agent_docs.py --check` finds a generated region out of date with
  `agents-list.json`, a shipped agent with no prose block, a prose block for an agent the roster does
  not ship, a hand-written heading drifted from an agent's canonical title, or a disagreement between
  the roster and the manifest about the shipped set.

## Development Workflow

Adding or changing a command MUST flow through the Spec Kit spec-driven commands (Principle I) — the
`spectra/` folder MUST NOT be hand-created or edited ad hoc, and new capabilities are added as commands
under it, never as new extensions:

1. **Specify** (`specify`) — describe the command in plain language: its purpose and `read-only` vs
   `read-write` effect. This creates the spec branch (via the `before_specify` hook, per the Version
   Control & Branching Strategy) and `specs/<NNN>-<name>/spec.md`. Run `clarify` to resolve open
   questions before planning.
2. **Plan** (`plan`) — generate the design artifacts. The Constitution Check gate enforces the single
   self-contained `spectra/` extension (Principle II), a new command file under `spectra/commands/`
   registered in `spectra/extension.yml`, agent-agnostic `$ARGUMENTS` commands under the
   `speckit.spectra.<command>` namespace (Principle III), context-awareness (Principle IV), the
   catalog/package sync obligations (Principle V), and — for any command that produces a document —
   the artifact-root output convention (Principle VII) and the registered, overridable template it is
   shaped by (Principle VIII).
3. **Tasks** (`tasks`) — produce the dependency-ordered task list.
4. **Implement** (`implement`) — execute the tasks: add the command file under `spectra/commands/`,
   register it in `spectra/extension.yml`, bump `extension.version` with a matching
   `spectra/CHANGELOG.md` entry, rebuild `docs/packages/spectra.zip` (a single top-level `spectra/`
   folder), update the `spectra` entry in `catalog.json` (the single source of truth) and
   `docs/index.html`, register the agent in `agents-list.json`, and regenerate the structured agent
   listings with `tools/generate_agent_docs.py` (Principle V).
5. **Test locally** by installing the working copy with `specify extension add --dev <path-to-spectra>`
   into a throwaway Spec Kit project and exercising every command end to end before publishing.
6. **Publish** by committing the `spectra/` folder, the `specs/` artifacts, the updated `catalog.json`,
   `docs/`, and `README.md`, then pushing to `main`; the catalog and package are live immediately at
   their `raw.githubusercontent.com` links.

User-facing documentation (`README.md`) and contributor documentation (`CONTRIBUTING.md`) MUST be
kept consistent with these principles whenever behavior changes.

## Version Control & Branching Strategy

Every spec is developed in isolation on its own dedicated Git branch. Work for a spec MUST NOT be
committed directly to `main`; it flows through that spec's branch and is merged back only when the
spec is complete.

- **One branch per spec.** Each new spec MUST get its own branch. A single branch MUST NOT hold work
  for more than one spec, and a single spec MUST NOT be split across multiple branches.
- **Branch name equals spec name.** The branch name MUST exactly match the spec's directory name
  under `specs/` — identical sequential number and identical kebab-case title (for example, spec
  `001-domain-analyzer` is developed on branch `001-domain-analyzer`).
- **Create the branch before specifying.** The spec branch MUST exist before specification work
  begins. The `before_specify` Git hook (`speckit.git.feature`) automates this; if it is unavailable,
  the branch MUST be created manually with the matching name before `specify` runs.

Rationale: Spectra dogfoods the same Git workflow its `git` extension ships. Pinning the branch
name to the spec name keeps the branch, the spec directory, and downstream automation (feature
hooks, PRs, issue links) trivially traceable to one another, and one-branch-per-spec keeps `main`
releasable and each spec's history reviewable in isolation.

## Governance

This constitution supersedes ad-hoc practice for the Spectra repository. All plans, reviews, and
changes MUST verify compliance with the principles above; any deviation MUST be justified in the
plan's Complexity Tracking (or equivalent) and approved before merge.

**Amendment procedure.** Amendments are proposed via a normal change (PR), MUST document what changed
and why, and MUST update this file together with any dependent templates and docs in the same change.

**Versioning policy.** This constitution is versioned with Semantic Versioning:
- **MAJOR** — backward-incompatible governance changes or principle removals/redefinitions.
- **MINOR** — a new principle or section, or materially expanded guidance.
- **PATCH** — clarifications, wording, and non-semantic refinements.

**Compliance review.** Reviewers MUST treat the Constitution Check gate in the plan template as
binding. Complexity that violates a principle MUST be justified or removed; unjustified violations
block merge.

**Version**: 1.7.1 | **Ratified**: 2026-07-12 | **Last Amended**: 2026-08-21
