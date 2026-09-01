# Implementation Plan: Open PR

**Branch**: `002-open-pr` | **Date**: 2026-06-24 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/002-open-pr/spec.md`

## Summary

**Open PR** is a Spectra add-on extension (SDLC delivery step) that closes the loop on spec-driven
development: after `implement` completes, it offers to open a pull request for the finished spec. It
reads the project's constitution (*Version Control & Branching Strategy*) and the `git` extension's
branching config to choose the correct base branch — honoring a defined promotion flow (e.g.,
feat → dev → main) automatically, or proposing and confirming feat → default-branch when no flow is
defined. It derives the source branch from the current spec branch, derives the PR title/body from
the spec, opens the PR (ready-for-review by default) with the `gh` CLI, and returns the PR URL in
chat. It degrades gracefully when `gh`, a GitHub remote, or the network is unavailable.

Technical approach: this is **not** application code. The deliverable is a single self-contained Spec
Kit extension folder (`github/`) whose behavior lives entirely in an agent-agnostic Markdown command
prompt (`commands/create-pr.md`) plus a YAML manifest (`extension.yml`) that declares the command and an
`after_implement` hook. There is no runtime service, database, or compiled artifact — the host coding
agent interprets the prompt, and the only external tools invoked are `git` and the `gh` CLI.
Distribution is via the generated GitHub Pages catalog (`build_packages.py`). The `adr/` and
`domain-analyzer/` extensions are the reference patterns; remote detection mirrors the `git`
extension's `speckit.git.remote`.

## Technical Context

**Language/Version**: Agent-agnostic Markdown command prompt (Spec Kit command format using
`$ARGUMENTS`) + YAML manifest (`extension.yml`, `schema_version: "1.0"`). Python 3 is used only for
the site build step (`build_packages.py`).

**Primary Dependencies**: Spec Kit (host); the team's coding agent at runtime. Runtime external tools:
`git` (branch/remote/push) and the `gh` CLI (PR create/detect). Remote detection reuses the `git`
extension's `speckit.git.remote` behavior (or `git config --get remote.origin.url`). No third-party
runtime libraries — the command is interpreted by the agent.

**Storage**: None of its own. The extension reads files (constitution, `git-config.yml`, spec) and
mutates only Git/remote state (push the source branch, create the PR). It writes no source code, spec,
or constitution content.

**Testing**: Manual end-to-end validation per Constitution Principle I / Workflow step 4: install the
working copy with `specify extension add --dev ./github` into a throwaway Spec Kit project and
exercise the scenarios in [quickstart.md](./quickstart.md) (no promotion flow, defined promotion flow,
decline-then-on-demand, `gh` unavailable, existing PR, non-spec branch). No automated test framework
applies to a prompt artifact.

**Target Platform**: Any Spec Kit-initialized project (`.specify/` present) with a GitHub remote, on
whatever coding agent the team uses. Slash/skill trigger differs per agent (e.g., Claude:
`/speckit-github-create-pr`).

**Project Type**: Spec Kit extension — a single self-contained repository-root folder (`github/`),
mirroring the `adr/` and `domain-analyzer/` reference extensions.

**Performance Goals**: User-facing outcomes from the spec — a PR opened in a single confirmation step
with zero manual `git`/`gh` commands in the default flow (SC-001); the PR link returned in chat on
100% of successful runs (SC-004).

**Constraints**: Declared `effect: read-write` (outward/remote actions: push, PR create), but every
push or PR creation MUST follow explicit user confirmation (FR-001, FR-004, FR-014). Must be
agent-agnostic (Principle III) and context-aware (Principle IV). GitHub-only this version; graceful
degradation without `gh`/remote/network (FR-007). No duplicate PRs (FR-010). Never opens from a
non-spec branch (FR-005).

**Scale/Scope**: One command (`speckit.github.create-pr`) plus one `after_implement` hook. Operates on a single
spec branch per run.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance | Notes |
|-----------|-----------|-------|
| **I. Spec-Driven Development** | ✅ Pass | Flows through specify → clarify → plan → tasks → implement; spec under `specs/002-open-pr/`, developed on branch `002-open-pr`. |
| **II. Self-Contained Extensions** | ✅ Pass | Deliverable is `github/` (id == folder name) with `extension.yml` (matching `id`), `commands/`, `README.md`, `CHANGELOG.md`, `LICENSE`. No shared state; reuses `git` remote-detection *behavior* by re-implementing it in-prompt rather than depending on the `git` extension at runtime (Principle II forbids cross-extension dependencies). |
| **III. Agent-Agnostic Commands** | ✅ Pass | Single command file in Spec Kit generic format using `$ARGUMENTS`; YAML front matter `description`; registered in `provides.commands`. Command name `speckit.github.create-pr` follows the required `speckit.<extension>.<command>` pattern (extension `github`, command `create-pr`). |
| **IV. Context-Aware by Default** | ✅ Pass | FR-002 requires reading the constitution's branching section and the `git` branching config; the command derives source branch, target, and PR title/body from real project state before acting. |
| **V. Generated Site Stays in Sync** | ✅ Pass (build-time) | After authoring, add the `github` entry to canonical `catalog.json`, run `python3 build_packages.py`, and commit the regenerated `docs/`. No hand-editing of `docs/`. |

**Result**: PASS — no violations. (An earlier draft used `speckit.open-pr`, which failed Spec Kit's
naming pattern; it was renamed to `speckit.github.create-pr`, resolving the deviation.)

## Project Structure

### Documentation (this feature)

```text
specs/002-open-pr/
├── plan.md              # This file (/speckit-plan command output)
├── spec.md              # Feature specification
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   ├── command-interface.md   # Command name, args, inputs read, decisions, outputs, chat report
│   └── hook-and-targeting.md  # after_implement hook contract + base-branch targeting algorithm
└── checklists/
    └── requirements.md  # Spec quality checklist
```

### Source Code (repository root)

The deliverable is one new self-contained extension folder at the repo root, plus the
registration/build artifacts the constitution requires. No `src/`, `tests/`, or runtime service is
created — the extension's behavior is defined entirely by its command prompt and manifest.

```text
github/                          # NEW — the extension (id == folder name)
├── extension.yml                 # Manifest: id, name, version, effect: read-write,
│                                 #   provides.commands (speckit.github.create-pr), hooks.after_implement (optional)
├── commands/
│   └── create-pr.md                # Agent-agnostic command prompt (speckit.github.create-pr)
├── README.md                     # User-facing docs (what it does, install, usage, fallback behavior)
├── CHANGELOG.md                  # SemVer history; 1.0.0 initial release
└── LICENSE                       # Apache-2.0 (TELUS Digital)

catalog.json                      # MODIFIED — add the "github" entry (canonical metadata)

docs/                             # REGENERATED by build_packages.py (NOT hand-edited)
├── index.html                    # rebuilt landing page
├── catalog.json                  # rebuilt hosted catalog (URLs injected from site.config.json)
└── packages/
    └── github.zip               # rebuilt package
```

**Structure Decision**: Single self-contained extension folder `github/` at the repository root,
mirroring the existing `adr/` and `domain-analyzer/` extensions (Principle II). The command prompt
`commands/create-pr.md` and the `extension.yml` manifest (including its `hooks.after_implement`
declaration) are the unit of "implementation." `catalog.json` is edited by hand (it is the canonical
input); everything under `docs/` is generated output produced by `python3 build_packages.py` and must
be committed but never hand-edited (Principle V).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Re-implementing GitHub remote detection in-prompt instead of calling the `git` extension | Principle II forbids runtime dependencies between extensions; `github` must install and run on its own even if `git` is absent. | Depending on `git`'s `speckit.git.remote` at runtime would couple the two extensions and break standalone installs. The detection logic (`git config --get remote.origin.url`, parse owner/repo, confirm github.com) is small and self-contained. |
