<!--
SYNC IMPACT REPORT
==================
Version: 1.0.0 (initial ratification)
Rationale: First constitution for the public Spectra repository. Establishes the principles that
  govern how Spectra is built and how every command in the single `spectra/` extension is authored,
  published, and maintained. Spectra is distributed from a public catalog, installable with no
  authentication.

Principles:
  I.   Spec-Driven Development (We Dogfood Spec Kit)
  II.  A Single Self-Contained Extension
  III. Agent-Agnostic Commands
  IV.  Context-Aware by Default
  V.   The Catalog and Package Are Maintained in Sync

Sections: Publishing & Distribution Standards · Development Workflow ·
  Version Control & Branching Strategy · Governance

Templates & docs in sync:
  - .specify/templates/plan-template.md ✅ (Constitution Check gate is generic)
  - .specify/templates/spec-template.md ✅
  - .specify/templates/tasks-template.md ✅
  - README.md ✅ — install flow and Agents table aligned
  - CONTRIBUTING.md ✅ — repository layout, workflow, and publishing steps aligned
  - catalog.json / spectra/extension.yml / docs/index.html ✅ — metadata and URLs aligned

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
GitHub Pages is disabled. **Anyone can add the catalog and install the extension anonymously.** There
is no build script: the catalog and package are maintained by hand and committed. Completing, changing,
or releasing the extension MUST include, in the same change:

- building the package into `docs/packages/spectra.zip` (a single top-level `spectra/` folder, the
  layout Spec Kit expects);
- updating `catalog.json` — the single source of truth for the catalog — so the `spectra` entry
  (name, description, version, tags, command count, and `download_url`) matches `spectra/extension.yml`
  and the new zip;
- updating `docs/index.html` so the landing page lists the extension and its commands;
- updating the Agents table in `README.md` when a command introduces or changes an agent; and
- committing `catalog.json`, `docs/`, `README.md`, and the `spectra/` folder, then pushing to `main`.

`catalog.json`, `docs/index.html`, `README.md`, and the published `docs/packages/spectra.zip` MUST
never drift from the `spectra/` folder.

Rationale: The repo is Spectra's only distribution channel — users discover and install entirely
from it, against the raw `catalog.json`. A stale catalog or a missing zip ships a broken install.
Keeping a single catalog entry and rebuilding the zip as part of finishing a command keeps the landing
page, catalog, and download link consistent by construction.

## Publishing & Distribution Standards

- **Semantic Versioning.** The extension follows [SemVer](https://semver.org/). Each release MUST
  bump `extension.version` and add a matching `CHANGELOG.md` entry under that version heading.
  Renaming or removing a command is a breaking (MAJOR) change.
- **Compatibility pinning.** `spectra/extension.yml` MUST set `requires.speckit_version` to the Spec
  Kit version range actually tested against. Re-test when Spec Kit is upgraded.
- **Required manifest fields.** `extension.yml` MUST provide `schema_version`, `id`, `name`,
  `version`, `description`, `category`, `effect` (`read-only` or `read-write`), `author`,
  `repository`, `license`, `requires.speckit_version`, and `provides.commands[]` (with each command's
  `name`, `file`, and `description`).
- **Authorship & license.** Author is `TELUS Digital`; the extension is MIT licensed unless explicitly
  stated otherwise, and carries its own `LICENSE`.
- **No silent drift.** Before publishing, verify that `catalog.json`, `docs/packages/spectra.zip`, and
  `docs/index.html` all agree with the `spectra/` folder and use the raw
  `raw.githubusercontent.com/xavient/spectra/main/...` URLs; any mismatch MUST be resolved first.

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
   `docs/index.html`, and update the Agents table in `README.md` when a new agent is introduced
   (Principle V).
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

**Version**: 1.0.0 | **Ratified**: 2026-07-12 | **Last Amended**: 2026-07-12
