# Feature Specification: One Document-Output Convention — a Declared Artifact Root

**Feature Branch**: `012-doc-output-convention`

**Created**: 2026-08-21

**Status**: Implemented

**Input**: User description: "currently adr commands writes the md files into `Docs/ADR/` (project root) and brd writes
into `/brds`. I want a consistent way for producing brds and adrs. On any project that Spectra is installed and being
used, adrs should be produced in `docs/adr` (project root), and brds should be produced in `docs/brd`. Also, I want this
to be a part of the constitution so that moving forward when we introduce new document-producing agents, they will
follow the same pattern (meaning they all go to their own subfolder in the `docs` folder in the root project folder)."

Follow-up: "`docs` could be used for GitHub Pages, so I am afraid if we use it as the default folders, users who have
their GitHub pages in that folder will not have the best experience."

## Clarifications

- Q: What happens in a project that already has `Docs/ADR/` or `brds/` from an earlier Spectra version?
  → A: **Legacy-read.** The command writes only to the canonical folder, but reads the earlier one for context and
  for number continuity, reports it once, and suggests a `git mv` the user can run. It never relocates files itself.
- Q: Does Spectra's own repository migrate its existing `brds/` to the new location?
  → A: No. The 8 existing BRDs stay at `brds/` — they are historical inputs cross-referenced from `specs/`, and moving
  them would break those links for no benefit. Only newly generated BRDs land in the canonical folder.
- Q: `docs/` is GitHub Pages' only non-root branch source and the default source directory for MkDocs and Docusaurus.
  How do we avoid publishing a BRD or breaking a docs build on those projects?
  → A: **Keep `docs/` as the default, make the root declarable, and check before defaulting.** A project sets
  `Artifact root: <folder>/` in its constitution and every document agent honours it. Before defaulting into `docs/`,
  a command looks for a publication signal, surfaces it, recommends `documents/`, and asks. Unanswered, it takes the
  non-publishing option, because publication is the irreversible direction. Commands offer the declaration line but
  never write it — editing governance is not a side effect of producing a document.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Predictable output folders in a fresh project (Priority: P1)

A developer installs Spectra into a project and runs the ADR agent, then later the BRD agent. Both deliverables appear
under one parent — `docs/adr/` and `docs/brd/` — rather than in two unrelated top-level folders whose names they have to
learn per agent.

**Why this priority**: This is the whole point of the change. It is the smallest slice that delivers the consistency the
user asked for, and it is what every future document-producing agent inherits.

**Independent Test**: In a throwaway Spec Kit project with Spectra installed, run the `adr` command and confirm the file
lands at `docs/adr/ADR-001-<title>.md`; run the `brd` command and confirm the file lands at `docs/brd/001-<title>.md`.
No `Docs/`, no `brds/`, and no other new top-level directory is created.

**Acceptance Scenarios**:

1. **Given** a project with no `docs/` folder, **When** the ADR agent writes its first ADR, **Then** `docs/adr/` is
   created and the file is `docs/adr/ADR-001-<kebab-title>.md`.
2. **Given** a project with no `docs/` folder, **When** the BRD agent writes its first BRD, **Then** `docs/brd/` is
   created and the file is `docs/brd/001-<kebab-title>.md`.
3. **Given** a project that already has an unrelated `docs/` folder, **When** either agent runs, **Then** it adds only
   its own subfolder and touches nothing else under `docs/`.
4. **Given** either agent has just written a file, **When** it reports the result, **Then** the path it prints is
   project-relative and lowercase (`docs/adr/…`, `docs/brd/…`), never prefixed with `/`.

---

### User Story 2 - An existing project keeps its numbering (Priority: P2)

A team that has been using Spectra already has `Docs/ADR/ADR-001…ADR-004` (or `brds/001…003`). After updating the
extension, the next artifact continues the sequence instead of restarting at `001`, and the team is told once that the
old folder exists and how to move it if they want to.

**Why this priority**: Without it the update silently produces a duplicate `ADR-001` and splits one decision log across
two folders. It is second only because a fresh project is the more common case and does not depend on it.

**Independent Test**: Seed a project with `Docs/ADR/ADR-004-something.md`, run the ADR agent, and confirm the new file is
`docs/adr/ADR-005-<title>.md`, that `Docs/ADR/` is unchanged on disk, and that the agent's report names the legacy folder
and offers a `git mv`.

**Acceptance Scenarios**:

1. **Given** `Docs/ADR/` contains `ADR-004-*.md` and `docs/adr/` does not exist, **When** the ADR agent runs, **Then**
   the new ADR is numbered `005` and written under `docs/adr/`.
2. **Given** `brds/` contains `003-*.md` and `docs/brd/` does not exist, **When** the BRD agent runs, **Then** the new
   BRD is numbered `004` and written under `docs/brd/`.
3. **Given** both the legacy and the canonical folder contain artifacts, **When** either agent computes the next number,
   **Then** it uses the highest number found across both folders.
4. **Given** a legacy folder was found, **When** the agent reports, **Then** it states the legacy path once, suggests a
   `git mv` into the canonical folder, and confirms it moved nothing itself.
5. **Given** a legacy folder was found, **When** the run completes, **Then** no file outside the single new artifact has
   been created, modified, deleted, or moved.

---

### User Story 3 - A project that publishes `docs/` is not ambushed (Priority: P2)

A team whose `docs/` folder is a GitHub Pages source (or a MkDocs / Docusaurus source directory) runs the BRD agent.
Instead of silently publishing a document full of revenue targets and stakeholder names, the agent raises the conflict
before writing, recommends `documents/`, and offers the one-line declaration that settles it for every Spectra agent.

**Why this priority**: The damage here is the worst in the change — a published BRD cannot be recalled from caches,
clones, or forks, and a docs build that turns red blames a documentation agent. It ranks alongside numbering continuity
because both are about not harming an existing project.

**Independent Test**: In a throwaway project, `touch mkdocs.yml`, run the BRD agent, and confirm it raises the
publication risk before writing and recommends a non-publishing root. Separately, add `Artifact root: documents/` to the
constitution and confirm both agents write to `documents/adr/` and `documents/brd/` without asking anything.

**Acceptance Scenarios**:

1. **Given** a project containing `mkdocs.yml` (or `docusaurus.config.js`, `docs/_config.yml`, `docs/.nojekyll`,
   `docs/index.html`, `docs/conf.py`, or a Pages config pointing at `docs`) and no declared root, **When** either agent
   is about to write, **Then** it states that `docs/` is a published source, recommends `documents/`, and asks.
2. **Given** the same project, **When** the user does not answer, **Then** the agent writes to `documents/<artifact>/`
   and says which root it used and why.
3. **Given** a constitution containing `Artifact root: documents/`, **When** either agent runs, **Then** it writes to
   `documents/adr/` or `documents/brd/` and does not ask about the root at all.
4. **Given** a declared root of `/etc/` or `../outside/`, **When** either agent resolves it, **Then** it refuses the
   value, explains why, and falls back to the default.
5. **Given** any root choice, **When** the agent reports, **Then** it offers the `Artifact root:` line for the user to
   add and does not modify `.specify/memory/constitution.md` itself.
6. **Given** a project with `docs/brd/` already populated and a root later declared as `documents/`, **When** the BRD
   agent computes the next number, **Then** it counts the artifacts in `docs/brd/` too.

---

### User Story 4 - The convention outlives this change (Priority: P3)

A contributor adds a new document-producing agent (a threat model, an API design record). They do not have to decide
where its output goes or ask — the constitution answers it, and CI fails if they answer differently.

**Why this priority**: It is the durability the user explicitly asked for, but it delivers value only once a *next*
agent exists, so it ranks behind the behavioral slices.

**Independent Test**: Point a command file at a non-conforming output folder (e.g. `Docs/ADR/`) and confirm the test
suite fails with a message naming the offending file and the required shape.

**Acceptance Scenarios**:

1. **Given** the constitution, **When** a contributor looks for where a new document agent should write, **Then**
   Principle VII states `<artifact-root>/<artifact>/` with a lowercase kebab-case slug, one artifact type per folder,
   and the duty to honour a declared root.
2. **Given** a command file under `spectra/commands/` that instructs a write into `Docs/ADR` or `/brds`, **When** the
   test suite runs, **Then** it fails and names the file and line.
3. **Given** a document command that stops resolving the declared root or stops checking for the publication signal,
   **When** the test suite runs, **Then** it fails and says which duty was dropped.

---

### Edge Cases

- **A case-insensitive filesystem already aliased the old path.** On macOS (APFS/HFS+, case-insensitive by default)
  `Docs/ADR/` resolves into an existing `docs/` folder, so an "old" ADR set may already physically live at `docs/ADR/`.
  The legacy scan MUST therefore treat a case-variant match as legacy rather than assuming a distinct `Docs/`.
- **A project has both `Docs/ADR/` and `docs/adr/`** (possible on a case-sensitive filesystem after a partial manual
  move). Numbering takes the maximum across both; the write still goes to the canonical folder.
- **`docs/` exists as a file, not a directory** — report the collision and stop rather than clobbering it.
- **`docs/` is a published site source.** Handled as User Story 3: detect, surface, recommend `documents/`, and prefer
  the non-publishing option when no answer arrives.
- **The declared root is unusable** — absolute, contains `..`, or names a file. Refuse it, explain, fall back to `docs/`.
- **The declared root is `docs/`** — an explicit declaration matching the default suppresses the publication question,
  because the user has answered it.
- **Spectra's own repository publishes `docs/` via GitHub Pages** (`main` `/docs`). Its own future artifacts are
  therefore subject to exactly the check above, which is the dogfooding case that motivated it.
- **The legacy folder exists but is empty** — no numbering contribution, and no legacy notice worth printing.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The ADR command MUST write its output to `<artifact-root>/adr/ADR-NNN-<kebab-title>.md`,
  project-relative, creating the folder if absent.
- **FR-002**: The BRD command MUST write its output to `<artifact-root>/brd/NNN-<kebab-title>.md`, project-relative,
  creating the folder if absent.
- **FR-003**: Both commands MUST express every path project-relative and lowercase — no leading `/`, no `Docs`.
- **FR-004**: Both commands MUST read the canonical folder for existing artifacts when gathering context.
- **FR-005**: Both commands MUST also read the locations earlier versions wrote to (`Docs/ADR/` for ADR, `brds/` for
  BRD, including case-variant forms) and — when a root other than `docs/` is in force — the default `docs/<artifact>/`.
- **FR-006**: The next sequence number MUST be one greater than the highest number found across the canonical folder
  **and** every superseded one, zero-padded to three digits, starting at `001` when none contain artifacts.
- **FR-007**: Neither command may move, rename, modify, or delete anything in a superseded folder.
- **FR-008**: When a superseded folder is found, the command MUST report it once, name the canonical folder, and offer a
  `git mv` the user can choose to run.
- **FR-009**: Each command's total write footprint MUST remain exactly one new artifact file (plus the folder that
  contains it), with the ADR command's existing exceptions unchanged: the superseded-ADR status line, and the
  constitution edit the user explicitly approves.
- **FR-010**: The ADR command's suggested `git add` MUST name the canonical path.
- **FR-011**: The extension manifest's `brd` command description MUST NOT name `/brds`.
- **FR-012**: The constitution MUST carry a principle establishing `<artifact-root>/<artifact>/` as the output
  convention for every document-producing agent, with `<artifact>` a lowercase kebab-case slug and one artifact type per
  folder.
- **FR-013**: The principle MUST exempt Spec Kit-owned locations (`.specify/`, `specs/`) so that context writes such as
  `domain-analyzer`'s `.specify/memory/domain-analysis.md` remain compliant.
- **FR-014**: The repository MUST fail its test suite when a shipped command file instructs a write into a superseded
  path, names an absolute or mixed-case output path, stops resolving the declared root, or stops checking for the
  publication signal.
- **FR-015**: Every user-facing description of where these agents write — extension manifest, extension README,
  `AGENTS_LIST.md`, the landing page, the manual-test checklist — MUST name the canonical folders and the override.
- **FR-016**: The extension version MUST bump to `1.6.0` in `spectra/extension.yml` and `catalog.json`, with a matching
  `spectra/CHANGELOG.md` entry and a rebuilt `docs/packages/spectra.zip`, so the change reaches installs via
  `spectra update`.
- **FR-017**: Spectra's own `brds/` directory MUST be left exactly as it is.
- **FR-018**: The artifact root MUST default to `docs/` and MUST be overridable by a single constitution line matched
  case-insensitively: `Artifact root: <folder>/`.
- **FR-019**: A declared root MUST be honoured by every document-producing command, so one declaration covers all
  present and future agents.
- **FR-020**: A declared root MUST be validated as project-relative — no leading `/`, no `..` — and an unusable value
  MUST be reported and replaced by the default rather than guessed at.
- **FR-021**: Before defaulting into `docs/`, a command MUST check whether `docs/` is a published site source, looking
  for `mkdocs.yml`, `docusaurus.config.*`, `docs/_config.yml`, `docs/.nojekyll`, `docs/index.html`, `docs/conf.py`, or a
  GitHub Pages configuration pointing at `docs`.
- **FR-022**: On finding such a signal with no declared root, a command MUST surface the publication risk before
  writing, recommend `documents/`, and ask the user which root to use.
- **FR-023**: That question MUST NOT count against either command's five-question limit, because it concerns where to
  write rather than what to record.
- **FR-024**: Where the user's choice cannot be obtained, a command MUST take the non-publishing option and state which
  root it used.
- **FR-025**: A command MUST offer the exact `Artifact root:` line for the user to add, and MUST NOT write that
  declaration into the constitution itself.

### Key Entities

- **Artifact root**: the project's single parent for generated documents. `docs/` by default; overridden by an
  `Artifact root: <folder>/` line in the constitution.
- **Canonical artifact folder**: `<artifact-root>/<artifact>/`. One artifact type per folder; created on demand; holds
  numbered Markdown deliverables.
- **Superseded artifact folder**: a location an earlier run wrote to — `Docs/ADR/` (any case variant), `brds/`, or
  `docs/<artifact>/` once a different root is declared. Read-only input for context and numbering.
- **Artifact slug**: the lowercase kebab-case name of the artifact type — `adr`, `brd`, and by construction
  `threat-model`, `api-design`, … for future agents.
- **Publication signal**: evidence that `docs/` is a published site source — `mkdocs.yml`, `docusaurus.config.*`,
  `docs/_config.yml`, `docs/.nojekyll`, `docs/index.html`, `docs/conf.py`, or a Pages configuration pointing at `docs`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In a fresh project, running both agents produces exactly two new directories, `docs/adr/` and
  `docs/brd/`, and no other top-level directory.
- **SC-002**: In a project seeded with legacy artifacts, the next artifact's number is exactly one greater than the
  highest legacy number, and `git status` shows zero changes to the legacy folder.
- **SC-003**: A repository-wide grep for `Docs/ADR` and `/brds` returns hits only in historical artifacts
  (`specs/003-brd-generator/`, `specs/012-doc-output-convention/`, `brds/`, the `CHANGELOG.md` entries that record the
  old behavior, and the legacy-handling clauses that exist to read them) — zero hits as write instructions.
- **SC-004**: `python -m unittest discover -s tests`, `python tools/generate_agent_docs.py --check`, and a
  `tools/build_package.py` rebuild all pass with no drift.
- **SC-005**: A contributor adding a document-producing agent can determine its output folder from the constitution
  alone, without reading any command file.
- **SC-006**: Declaring `Artifact root: documents/` moves both agents' output with no further configuration and no
  question asked at run time.
- **SC-007**: In a project where `docs/` is a published site source, neither agent writes into `docs/` without first
  stating the risk, and an unanswered prompt results in a non-published location.

## Assumptions

- Command files are prompts, not code: "MUST" in a command file is an instruction the agent follows, and the
  enforceable part of this change is the text of those instructions plus the CI guard on that text.
- `docs/` remains the right default. It is what most teams expect and what ADR tooling conventionally uses; the projects
  where it is unsafe are a minority, and they are served by one declaration line rather than by making everyone else
  learn a novel folder name.
- `documents/` is the recommended alternative because no tool claims it and it does not appear in `.gitignore`
  templates. `artifacts/` was rejected for exactly that reason — it is gitignored in common .NET/CI templates, and a BRD
  written into an ignored folder would be silently lost, which is worse than one published by accident.
- Filename conventions stay as they are — `ADR-NNN-<title>.md` for ADRs, `NNN-<title>.md` for BRDs. Unifying the
  filename shape would renumber or rename existing artifacts in consumer projects for cosmetic gain.
- No installed-side migration tooling ships with this change; the `git mv` suggestion is the migration path.
- The `spectra` CLI needs no change: it reads `catalog.json` at run time, so a version bump alone reaches installs.
