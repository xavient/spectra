# Tasks: Agent Roster & Project-Scoped CLI Commands

**Input**: Design documents from `/specs/006-agent-roster-cli/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Included. The plan specifies a `tests/` suite using standard-library `unittest`, run as
`python -m unittest discover -s tests`, plus CI shell assertions. pytest is deliberately not used — the
zero-dependency constraint applies to the whole repository, not just the shipped wheel.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US7)
- Every task names the exact file it touches

## Path Conventions

Repository root layout, per plan.md: `spectra_cli/` (the shipped CLI), `tools/` (maintainer-only,
excluded from the wheel by `pyproject.toml`'s explicit package list), `tests/` (stdlib unittest),
`spectra/` (the extension payload), `docs/` (the published surface), and `agents-list.json` at the root
beside `catalog.json`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: The test seam every later phase writes against

- [ ] T001 Create `tests/helpers.py` with the fixtures every later test file needs: a temp Spec Kit project builder (writes `.specify/`, optionally `.specify/extensions/spectra/extension.yml` at a given version), a roster builder returning a valid in-memory roster dict, a `serve_roster()` context manager wrapping `http.server` on an ephemeral port for `SPECTRA_RAW_BASE`, and an `unreachable_base()` helper returning `http://127.0.0.1:9`
- [ ] T002 [P] Add a `python -m unittest discover -s tests` step to the `cli` job in `.github/workflows/ci.yml`, after the existing install step

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The roster itself, the four shared CLI modules, and the parser restructure. Every user story
reads from at least one of these.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T003 Create `agents-list.json` at the repository root: `schema_version` `"1.0"`, the 7 `phases` with their `aidlc` values, and all 44 `agents` entries exactly as tabulated in `specs/006-agent-roster-cli/data-model.md` §2 — ids, titles, types, statuses, providers, and `command` present only on the 13 available entries. One-line descriptions only (FR-001, FR-003, FR-003a, FR-003b, FR-004, FR-005, FR-006, FR-007, FR-008)
- [ ] T004 [P] Create `spectra_cli/net.py`: a 10-second-bounded anonymous fetch over `urllib.request`, a `raw_base()` reader honouring `SPECTRA_RAW_BASE` and defaulting to `https://raw.githubusercontent.com/xavient/spectra/main`, and a `FetchError` carrying a human-readable reason (offline, timeout, HTTP status, malformed body) so callers can print why rather than what (FR-041, FR-041a)
- [ ] T005 [P] Create `spectra_cli/project.py`: walk `[Path.cwd(), *Path.cwd().parents]` for `.specify/` reusing the pattern in `install.py:check_in_specify_project`, then classify into `NOT_A_PROJECT` / `NOT_INSTALLED` / `INCOMPLETE` / `INSTALLED` returning `state`, `project_root`, and `installed_version` (FR-040, FR-044, FR-045)
- [ ] T006 Create `spectra_cli/roster.py` with one parser used by two callers: `parse(dict)` validating and returning ordered agents grouped by phase, `load(path)` for the generator, and `fetch()` for the CLI via `net.py`. Include the schema gate — newer MINOR renders with a notice, newer MAJOR refuses (FR-008, FR-009, FR-009a, FR-009b). Depends on T004
- [ ] T007 [P] Create `spectra_cli/extension.py`: `installed_version(project_root)` scanning `^  version: "(.*)"$` in `.specify/extensions/spectra/extension.yml`, `published_version()` scanning the same expression over the raw `spectra/extension.yml`, and `delegate_update()` / `delegate_remove(force)` shelling out to `specify extension update|remove spectra` with a clear failure when `specify` is not on PATH (FR-031, FR-046). Depends on T004
- [ ] T008 Restructure `spectra_cli/cli.py` from a single flat parser to `argparse` subparsers, preserving today's observable behaviour exactly — `install`, the three flags, `--yes`, `--no-update-check`, the bare-command overview, and the `_Parser.error` panel rendering all unchanged. This is a pure refactor; the flags are removed later in US5
- [ ] T009 [P] Create `tests/test_net.py`: timeout is bounded and reported, `SPECTRA_RAW_BASE` overrides the default, and each failure reason produces a distinct message
- [ ] T010 [P] Create `tests/test_roster.py`: phase and within-phase ordering is roster order, grouping is stable, newer MINOR renders plus notice, newer MAJOR refuses, unknown fields are ignored, malformed and version-less documents are rejected with a reason
- [ ] T011 [P] Create `tests/test_project.py`: all four states, resolution from a nested subdirectory, and an extension folder that exists but has no readable manifest version classifying as `INCOMPLETE`
- [ ] T012 [P] Create `tests/test_extension.py`: the manifest version scan against a real manifest shape and against missing, unreadable, and version-less manifests; `specify`-absent handling; and that delegation passes `--force` only when asked
- [ ] T013 [P] Create `tests/test_roster_data.py` asserting the committed `agents-list.json` satisfies every rule in `specs/006-agent-roster-cli/contracts/agents-list.schema.json`: 44 entries, unique slug ids, `phase` resolving to a known phase, single-line descriptions, and `command` present exactly when `status` is `available`
- [ ] T014 Run `python -m unittest discover -s tests/` and smoke `spectra --help`, `spectra`, and `spectra install --help` to confirm the `spectra_cli/cli.py` restructure in T008 changed no observable behaviour

**Checkpoint**: The roster exists and is validated; the four shared modules are covered; the parser is
ready to grow subcommands. User stories can now proceed.

---

## Phase 3: User Story 1 - Discover what agents Spectra offers (Priority: P1) 🎯 MVP

**Goal**: `spectra agent-list` prints the published roster from any directory, grouped so 44 entries stay
readable, with status, type, provider, and command unambiguous per row.

**Independent Test**: Install the CLI, run `spectra agent-list` from a folder that is not a Spec Kit
project, and confirm all 44 agents appear correctly grouped with no planned agent showing a command.

- [ ] T015 [US1] Add the roster renderer to `spectra_cli/ui.py`: one block per phase showing the phase title and its AI-DLC phase, then one row per agent with status glyph, title, type, provider, and either its command or "under development" — rendered through the existing `panel()`/palette rather than a second visual language (FR-025)
- [ ] T016 [US1] Add the `agent-list` subcommand to `spectra_cli/cli.py`: fetch via `roster.fetch()`, apply the schema gate, render, and exit 0. On fetch failure or a newer MAJOR schema, print the reason and exit 3 without printing a partial list. Must not require a Spec Kit project (FR-026, FR-027, FR-041). Depends on T006, T015
- [ ] T017 [US1] In `spectra_cli/cli.py`, mark which Spectra-provided agents are installed here when `agent-list` runs inside a project, by intersecting `provider == "spectra"` entries with `project.classify()` — the marker is absent entirely when run outside a project (FR-048). Depends on T005, T016
- [ ] T018 [P] [US1] Create `tests/test_agent_list.py`: grouping order matches roster order, planned entries render no command, the newer-MINOR notice appears with the full listing, newer MAJOR exits 3 with nothing listed, an unreachable base exits 3, and the installed marker appears only inside a project
- [ ] T019 [P] [US1] Create `tests/test_no_hardcoded_agents.py` asserting no agent title or roster description string appears anywhere under `spectra_cli/` (FR-042, SC-002)
- [ ] T020 [US1] Run step 5 of `specs/006-agent-roster-cli/quickstart.md` and confirm the output by eye against its stated expectations (SC-001, SC-004)

**Checkpoint**: `spectra agent-list` works standalone. This is the MVP — a user can discover the roster
from the terminal with nothing installed in the project.

---

## Phase 4: User Story 2 - Confirm Spectra is installed in this project (Priority: P1)

**Goal**: `spectra check` gives a definitive, distinguishable answer for each of four project states, and
offers to fix the one it can.

**Independent Test**: Run `check` in a folder that is not a Spec Kit project, a Spec Kit project without
Spectra, a project with a half-written extension folder, and a project with Spectra installed; confirm
four different messages and the documented exit codes.

- [ ] T021 [US2] Add the `check` subcommand to `spectra_cli/cli.py`, branching on `project.classify()` with one distinct message and exit code per state exactly as tabulated in `specs/006-agent-roster-cli/contracts/cli-surface.md` — 0 installed, 5 for incomplete and not-a-project (FR-028, FR-044, FR-045). Depends on T005
- [ ] T022 [US2] In `spectra_cli/cli.py`, wire the not-installed branch to offer installation and call `run_install()` from `spectra_cli/install.py` unchanged, exiting 1 when declined and 4 when the install itself fails; honour `--yes` as accepting the offer (FR-029)
- [ ] T023 [P] [US2] Create `tests/test_check.py`: four states produce four distinct messages and the documented exit codes, declining exits 1, and running from a nested subdirectory reports on the enclosing project
- [ ] T024 [US2] Run steps 6 and 7 of `specs/006-agent-roster-cli/quickstart.md`, confirming all four messages are different sentences rather than one sentence with a swapped noun (SC-001, SC-009, SC-012)

**Checkpoint**: US1 and US2 both work independently.

---

## Phase 5: User Story 3 - Find out whether my agents are current, and update them (Priority: P1)

**Goal**: `spectra version` delivers a verdict and names the fix; `spectra update` applies it in one step.

**Independent Test**: Hand-edit an installed manifest to an older version, confirm `version` reports both
and names `spectra update`, run it, and confirm a second `version` reports up to date.

- [ ] T025 [US3] Add the `version` subcommand to `spectra_cli/cli.py`: compare installed against published using the existing `version.compare_versions()`, print one of three verdicts — up to date, out of date naming `spectra update`, or ahead of published with no update offered — and exit 0 for all three; exit 3 when the published version is unreachable and 5 for any bad project state (FR-030, FR-031, FR-032, FR-032a). Depends on T005, T007
- [ ] T026 [US3] Add the `update` subcommand to `spectra_cli/cli.py`: delegate to `extension.delegate_update()` when behind, report and change nothing when already current or ahead, use the update path as the documented repair for `INCOMPLETE`, and exit 4 when Spec Kit fails or is absent (FR-033, FR-046). Depends on T007
- [ ] T027 [P] [US3] Create `tests/test_version_update.py`: all three verdicts exit 0, unreachable-published exits 3 without implying currency, not-installed exits 5 with its own message, already-current update makes no subprocess call, and ahead-of-published offers no update
- [ ] T028 [US3] Run step 8 of `specs/006-agent-roster-cli/quickstart.md`, including timing the offline case to confirm it returns inside ~10 seconds (SC-001, SC-007, SC-013)

**Checkpoint**: All three P1 user-facing stories work. Every project-scoped read command is done.

---

## Phase 6: User Story 4 - Add an agent once and have every listing update itself (Priority: P1)

**Goal**: The roster becomes the source of truth in fact, not just in principle — three structured
listings are generated from it and no hand-edit survives CI.

**Independent Test**: Add an entry to the roster, run the generator, confirm every structured listing
contains it with an identical title; then hand-edit a generated region and confirm `--check` fails and
names the file.

- [ ] T029 [US4] Wrap the Agents table in `README.md` in `<!-- SPECTRA:GENERATED START id=readme-agents-table -->` / `END` markers per `specs/006-agent-roster-cli/contracts/generated-regions.md`, drawing the region to include the trailing sentence that names which ✅ agents are Spec Kit's own rather than Spectra's (FR-012, FR-014)
- [ ] T030 [US4] Restructure `AGENTS_LIST.md`: add the `agents-list-speckit-core` and `agents-list-roadmap` generated regions around those two section bodies, add a `<!-- SPECTRA:AGENT id=… -->` anchor above each of the four prose blocks (`adr`, `domain-analyzer`, `create-pr`, `brd`), retitle the `### \`github\` — GitHub ✅` heading to the canonical `GitHub (PR)` form, and reword "These four ship in the `spectra` extension today" to drop the count (FR-010, FR-013, FR-014)
- [ ] T031 [US4] Restructure `spectra/README.md`: wrap its Commands table in `<!-- SPECTRA:GENERATED START id=spectra-readme-commands -->` / `END` markers, dropping the Effect column (the roster does not model per-agent effect; `spectra/extension.yml` already declares `effect: read-write` for the extension, and the surrounding prose says so), and retitle the `## \`speckit.spectra.create-pr\` — GitHub PR delivery` heading to the canonical `GitHub (PR)` form. This file ships inside `docs/packages/spectra.zip`, so a stale copy is republished to every downloader (FR-002, FR-002a, FR-010, FR-012)
- [ ] T032 [US4] Reword the inline list of the four command names in `README.md` lines 277–278 so it names the namespace rather than enumerating the shipped set, matching the treatment T030 gives "These four ship…" — it sits outside every generated region and would be wrong the first time a fifth agent ships (FR-002a)
- [ ] T033 [US4] Create `tools/generate_agent_docs.py`: load the roster through `spectra_cli.roster.load()` so the generator and the CLI cannot diverge on validation, render the four regions, and rewrite only the marked spans. Missing, malformed, duplicated, or unknown markers are hard errors naming the file and the marker, and must leave the file unwritten (FR-011, FR-012, FR-015, FR-016, FR-020). Depends on T003, T006, T029, T030, T031
- [ ] T034 [US4] Add `--check` to `tools/generate_agent_docs.py` asserting all five classes from `specs/006-agent-roster-cli/contracts/generated-regions.md`: region freshness naming the stale file, prose-anchor presence and absence of orphans naming the agent id, each shipped agent's canonical title appearing in `spectra/README.md` naming the agent and the file, roster↔manifest set-and-command agreement over `provider: spectra` entries only, and the roster field rules. Descriptions must **not** be compared (FR-017, FR-018, FR-018a, FR-019, FR-019a)
- [ ] T035 [US4] Run `python tools/generate_agent_docs.py` and commit the regenerated regions in `README.md`, `AGENTS_LIST.md`, and `spectra/README.md`, verifying with `git diff` that every hand-authored line outside the regions is byte-identical; then rebuild `docs/packages/spectra.zip`, because `spectra/README.md` ships inside it and CI's zip-drift check would otherwise fail (FR-015, FR-024, constitution Principle V)
- [ ] T036 [P] [US4] Create `tests/test_generator.py`: two consecutive runs are byte-identical, content outside regions is untouched, each of the five failure modes fails and names its culprit, a description differing from the manifest's passes, a heading whose wording drifts from the canonical title fails and names the agent and file, a malformed marker leaves the file unwritten, and renaming a title while keeping the id keeps prose matching and passes (SC-005, SC-006, SC-011)
- [ ] T037 [US4] Add a `python tools/generate_agent_docs.py --check` step to the `catalog` job in `.github/workflows/ci.yml`, after T035 so the step lands green
- [ ] T038 [US4] Update `CONTRIBUTING.md`: name the roster and the generator in the "Add a new command" procedure (step 4 currently says to add a row to the README Agents table by hand), and correct the "There is no build script" assertion in the "What ships" section (FR-021)
- [ ] T039 [US4] Amend `.specify/memory/constitution.md` Principle V: remove "There is no build script", replace the hand-maintained README Agents table clause with the roster-and-generator rule, add `agents-list.json` to the sync list and the generated-docs check to "No silent drift", update the `spectra --update` reference on line 174 to `spectra cli update`, generalize the existing no-hard-coded-versions rule so it covers the extension description and agent data the landing page now fetches, bump the version to 1.4.0, and record the change in the sync-impact header (FR-022)
- [ ] T040 [US4] Run steps 1, 2, and 3 of `specs/006-agent-roster-cli/quickstart.md` — determinism, all six verification cases including the deliberate pass, and the rename-survives check (SC-003, SC-005, SC-006, SC-011)

**Checkpoint**: The roster is the single source of truth and drift is mechanically impossible to merge.
All four P1 stories are done.

---

## Phase 7: User Story 5 - Manage the tool itself, unambiguously (Priority: P2)

**Goal**: Tool operations move under `spectra cli`, the three flags are gone, and the help screen makes
the project/tool split obvious.

**Independent Test**: Run each `cli` subcommand and confirm it acts on the tool; run each removed flag and
confirm it exits 2 naming its replacement.

**⚠️ Land T042 and T044 together.** Removing the flags breaks the CI assertion that runs
`spectra --version`; separating them turns `main` red.

- [ ] T041 [US5] Add the `cli` subcommand group to `spectra_cli/cli.py` wrapping the existing `cmd_version`, `cmd_update`, and `cmd_uninstall` unchanged, keeping the bare version on the first line of `cli version` output (FR-036)
- [ ] T042 [US5] Remove `--version`/`-V`, `--update`, and `--uninstall` from the parser in `spectra_cli/cli.py` — not as hidden aliases — and detect them in `argv` before parsing to emit a message naming the replacement command, exiting 2. `--version` names both `spectra cli version` and `spectra version`, since it was the ambiguous one (FR-038, FR-039)
- [ ] T043 [US5] Rebuild the help surface in `spectra_cli/cli.py` as three panels — Project commands, Tool commands, Options — driven from module-level lists so the rendered table and the parser keep reading from one source (FR-037, FR-043, SC-008)
- [ ] T044 [US5] Move the version-parity assertion in `.github/workflows/ci.yml` from `spectra --version` to `spectra cli version | head -1`, keeping the comparison against the committed `VERSION`
- [ ] T045 [US5] Bump `VERSION` from `4.0.0` to `5.0.0` (FR-049)
- [ ] T046 [P] [US5] Create `tests/test_cli_surface.py`: each removed flag exits 2 with its replacement named, each `cli` subcommand dispatches to the tool-scoped function, bare `spectra` exits 0 and writes nothing to the working directory, and the help output contains all three panel titles (FR-047)
- [ ] T047 [US5] Run step 10 of `specs/006-agent-roster-cli/quickstart.md`, including the `VERSION` parity check and the bare-command no-op assertion

**Checkpoint**: The command surface is final. This is the breaking change; everything after it is additive.

---

## Phase 8: User Story 6 - Remove Spectra's agents from a project (Priority: P2)

**Goal**: `spectra uninstall` cleans the project and leaves the machine's `spectra` command alone.

**Independent Test**: Run it in a project with Spectra installed, confirm the extension is gone and
`spectra cli version` still works; run it again and confirm it reports absence and changes nothing.

- [ ] T048 [US6] Add the `uninstall` subcommand to `spectra_cli/cli.py`: confirm state first, delegate to `extension.delegate_remove()` letting Spec Kit own the prompt and passing `--force` only with `--yes`, exit 0 when Spectra is already absent because the requested end state holds, and exit 5 when the folder is not a Spec Kit project (FR-034, FR-035). Depends on T007
- [ ] T049 [P] [US6] Create `tests/test_uninstall.py`: installed delegates with the right argv, `--yes` adds `--force` and bare does not, absent exits 0 with no subprocess call, not-a-project exits 5, and no code path touches uv or the installed distribution
- [ ] T050 [US6] Run step 11 of `specs/006-agent-roster-cli/quickstart.md`

**Checkpoint**: The full project-scoped lifecycle works — discover, check, version, update, uninstall.

---

## Phase 9: User Story 7 - Spectra is described the same way everywhere (Priority: P2)

**Goal**: One positioning line across every published surface, and a landing page whose agent section is
fetched rather than typed.

**Independent Test**: Grep the description across every published copy and confirm they match; load the
page and confirm a roster edit changes it with no HTML change.

- [ ] T051 [US7] Change `extension.description` in `spectra/extension.yml` to "TELUS Digital - Agentic software engineering across the entire SDLC." and bump `extension.version` from `1.3.0` to `1.3.1` (FR-051)
- [ ] T052 [US7] Add the `1.3.1` entry to `spectra/CHANGELOG.md` recording the description change and noting that no command changed
- [ ] T053 [P] [US7] Update the `spectra` entry's `description` and `version` in `catalog.json` to match `spectra/extension.yml` exactly (FR-051)
- [ ] T054 [US7] Update `docs/index.html`: fetch `agents-list.json` at load and render the Agents section's roster-derived content from it — titles, statuses, phases, one-line descriptions, commands — keeping the hand-written per-command arguments and examples, and read the extension description from the already-fetched `catalog.json` instead of the hard-coded paragraph (FR-051, FR-052)
- [ ] T055 [US7] Rebuild `docs/packages/spectra.zip` as a single top-level `spectra/` folder and verify with `unzip -p docs/packages/spectra.zip spectra/extension.yml` that the packaged manifest carries the new description and version (constitution Principle V)
- [ ] T056 [US7] Add a description-parity step to the `catalog` job in `.github/workflows/ci.yml` asserting the agreed line appears identically in `spectra/extension.yml` and `catalog.json` (SC-010)
- [ ] T057 [US7] Run step 12 of `specs/006-agent-roster-cli/quickstart.md`, including serving `docs/` locally and confirming the description is absent from the HTML source

**Checkpoint**: All seven user stories are complete.

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: The documentation and guard-rail work that spans stories. The three doc tasks have exact line
references from a grep of the current tree.

- [ ] T058 [P] Update `README.md`: replace the removed-flag references on lines 191, 192, 208, 209, and the `spectra --update` cell on line 309 with their `spectra cli …` equivalents, and document the five new project-scoped commands in the Installation section
- [ ] T059 [P] Update `CONTRIBUTING.md`: replace the removed-flag references on lines 307, 362, 372, and 385, and update the copy of the old extension description so it does not contradict `spectra/extension.yml`
- [ ] T060 [P] Update `test/README.md`: replace the removed-flag references in the scenario table on lines 67 and 74 with `spectra cli version` and `spectra cli update` / `spectra cli uninstall`, and add rows for the new project-scoped commands
- [ ] T061 Add a step to `.github/workflows/ci.yml` that builds the wheel and asserts neither `tools/` nor `tests/` appears in it, making FR-023 machine-checked rather than a property of `pyproject.toml` that a future edit could quietly break
- [ ] T062 Refresh the managed region in `CLAUDE.md` by running `/speckit.agent-context.update` so the two-channel note names `agents-list.json` and the generator, rather than hand-editing inside the `<!-- SPECKIT START -->` markers
- [ ] T063 Run `python -m unittest discover -s tests` and every step of `specs/006-agent-roster-cli/quickstart.md` in order, then confirm `git status` is clean — a dirty tree after a full run means something is not deterministic
- [ ] T064 Run steps 5 through 11 of `specs/006-agent-roster-cli/quickstart.md` in PowerShell on Windows, watching specifically that a generator run leaves `git diff --exit-code` clean (line endings written `\n`) and that `spectra check` resolves the project root from a nested path (FR-050)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS every user story
- **US1 (Phase 3)**: Needs T003, T004, T005, T006, T008
- **US2 (Phase 4)**: Needs T005, T008 and the existing `install.py`
- **US3 (Phase 5)**: Needs T005, T007, T008
- **US4 (Phase 6)**: Needs T003 and T006. Independent of every CLI subcommand — it touches `tools/`, the docs, `spectra/README.md`, and the constitution, not `cli.py`
- **US4 ↔ US7 overlap**: both rebuild `docs/packages/spectra.zip` — T035 because `spectra/README.md` is generated into the package, T055 because the manifest description changes. Whichever lands second must rebuild again, or CI's zip-drift check fails. This is the only file the two otherwise-independent tracks share
- **US5 (Phase 7)**: Needs T008, and should follow US1–US3 so the project commands exist before the help panels advertise them
- **US6 (Phase 8)**: Needs T007, T008
- **US7 (Phase 9)**: Needs T003 (the page fetches the roster). Otherwise independent
- **Polish (Phase 10)**: T058–T060 depend on US5 landing; T061 and T063 depend on everything

### User Story Dependencies

- **US1, US2, US3, US6** are siblings: each adds one subcommand to `cli.py`. Independently testable, but
  they edit the same file, so they serialize in practice unless split by developer with care.
- **US4** shares no file with any other story. It is the natural parallel track.
- **US5** must come after the stories whose commands its help panels list, and its two coupled tasks
  (T042, T044) must land together.
- **US7** is independent of the CLI entirely.

### Within Each User Story

- Modules before the subcommand that calls them
- Subcommand before its tests
- Tests before the quickstart step that confirms the story by hand
- Story complete and checkpointed before moving to the next priority

### Parallel Opportunities

- **Phase 2**: T004, T005, and T007 have no relationship to each other. T009–T013 can all be written at
  once against the modules as they land
- **Phase 6 alongside Phases 3–5**: US4 touches `tools/`, `README.md`, `AGENTS_LIST.md`, `spectra/README.md`,
  `CONTRIBUTING.md`, and the constitution — zero overlap with `cli.py`. The largest genuine parallel win in
  this plan
- **Phase 9 alongside anything after T003**: US7 touches `spectra/`, `catalog.json`, and `docs/`
- **Phase 10**: T058, T059, and T060 are three different files

---

## Parallel Example: Phase 2 Foundational

```bash
# Three independent modules, no shared file:
Task: "Create spectra_cli/net.py — bounded fetch, SPECTRA_RAW_BASE, FetchError"
Task: "Create spectra_cli/project.py — root discovery and four-state classification"
Task: "Create spectra_cli/extension.py — manifest scan, published fetch, delegation"

# Then their tests together:
Task: "Create tests/test_net.py"
Task: "Create tests/test_project.py"
Task: "Create tests/test_extension.py"
Task: "Create tests/test_roster_data.py"
```

## Parallel Example: two tracks after Phase 2

```bash
# Track A — the CLI (serialized on cli.py):
US1 agent-list -> US2 check -> US3 version/update -> US5 cli group -> US6 uninstall

# Track B — the roster's documentation contract (no cli.py contact):
US4 markers -> generator -> --check -> regenerate -> CI -> CONTRIBUTING -> constitution
US7 description, catalog, landing page, zip
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Phase 1: Setup
2. Phase 2: Foundational — the roster and the shared modules
3. Phase 3: User Story 1
4. **STOP and VALIDATE**: `spectra agent-list` answers "what agents exist?" from any directory
5. Demo-able on its own: discovery without a browser, with no project changes

### Incremental Delivery

1. Setup + Foundational → the roster is published and validated
2. US1 → discovery works → demo (MVP)
3. US2 → "is it installed here?" answered
4. US3 → "are they current?" answered, and fixable in one command
5. US4 → the roster becomes the source of truth and drift stops being mergeable
6. US5 → the breaking rename; release the CLI as `5.0.0`
7. US6 → project-scoped removal completes the lifecycle
8. US7 → presentation converges

Note on ordering: the four P1 stories are US1–US4, and US4 is the one the *maintainers* feel. Shipping
US1–US3 without US4 is coherent — the roster works, it is simply still hand-copied into the docs — but the
reverse is not, because US4's `--check` asserts against a roster only US1's foundation provides.

### Release Sequencing

Two channels move for independent reasons, and neither bump waits on the other:

- **Extension `1.3.1`** ships with US7 — description metadata only, no command touched
- **CLI `5.0.0`** ships after US5 — MAJOR, because three flags are gone. Tag `5.0.0`; the release workflow
  refuses to publish if the tag and `VERSION` disagree
- The roster itself needs **no release at all**: merging to `main` publishes it over the raw link, which is
  the property FR-026 and SC-004 depend on

### Parallel Team Strategy

With two developers, the split is clean because the tracks share no file:

1. Both complete Setup + Foundational
2. Developer A takes the CLI track: US1 → US2 → US3 → US5 → US6
3. Developer B takes the documentation track: US4, then US7
4. Reconvene for Phase 10, where T058–T060 depend on A's US5 landing

---

## Notes

- 64 tasks. 20 marked `[P]`
- Tests are stdlib `unittest`; there is no pytest and adding one would break the zero-dependency
  constraint that `pyproject.toml`'s empty `dependencies` documents deliberately
- `T042` and `T044` must land in one commit, or CI goes red on the assertion that runs the flag being
  removed
- `T035` produces a large diff by design. The thing to review is not the generated content but that
  everything *outside* the regions is byte-identical
- Commit after each task or logical group; stop at any checkpoint to validate a story in isolation
- Avoid: editing generated regions by hand (T034 will catch it, but the point is not to), comparing
  roster and manifest descriptions (deliberately independent), adding a second confirmation prompt in
  `uninstall` where Spec Kit already has one, and forgetting the zip rebuild after `spectra/README.md`
  changes
