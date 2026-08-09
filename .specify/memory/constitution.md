<!--
SYNC IMPACT REPORT
==================
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
answer to "what is the newest `spectra` command" — which both `spectra cli update` and the landing page
depend on. If the catalog also cut releases, the CLI's update check could resolve to an extension
release and attempt to install it as a version of itself.

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
   `speckit.spectra.<command>` namespace (Principle III), context-awareness (Principle IV), and the
   catalog/package sync obligations (Principle V).
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

**Version**: 1.4.0 | **Ratified**: 2026-07-12 | **Last Amended**: 2026-08-09
