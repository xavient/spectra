# Implementation Plan: Agent Roster & Project-Scoped CLI Commands

**Branch**: `006-agent-roster-cli` | **Date**: 2026-08-09 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/006-agent-roster-cli/spec.md`

## Summary

Publish `agents-list.json` at the repository root as the single source of truth for Spectra's agent
roster, generate every structured agent listing from it, and reorganize the `spectra` command so
top-level verbs act on the extension installed in the current project while tool self-management moves
under `spectra cli`.

Three separable pieces of work, in dependency order:

1. **The roster** — a new stdlib-parseable JSON document holding all 44 of today's roster entries, keyed
   by a stable slug per agent and carrying a `major.minor` schema version.
2. **The generator** — a maintainer-only script at `tools/generate_agent_docs.py` that rewrites four
   marked regions (the README Agents table, the Spec Kit core and Roadmap sections of `AGENTS_LIST.md`,
   and the Commands table in `spectra/README.md`) from the roster, and, under `--check`, verifies those
   regions plus prose-block presence plus title containment plus roster↔manifest agreement. CI runs
   `--check`; nothing ships it to users.
3. **The command surface** — five new project-scoped commands (`agent-list`, `check`, `version`,
   `update`, `uninstall`), a `cli` group for the three tool-scoped ones, and removal of the
   `--version` / `--update` / `--uninstall` flags. Three new stdlib-only modules (`roster.py`,
   `project.py`, `extension.py`) plus a shared bounded-fetch helper (`net.py`).

Delivered as 64 tasks and 256 tests. Two deviations from this plan are worth knowing: a fourth
generated region and a `spectra/README.md` retitle were added after cross-artifact analysis found that
file independently declaring all four shipped agents under a fourth name for one of them; and
`tools/build_package.py` was added so the package rebuild the constitution requires is reproducible
rather than manual.

Both release channels bump, for independent reasons: the CLI to `5.0.0` (MAJOR — the flags are removed),
the extension to `1.3.1` (PATCH — its description changes, no command does). Principle V of the
constitution is amended in the same change, because it currently asserts there is no build script and
that the README Agents table is maintained by hand.

## Technical Context

**Language/Version**: Python 3.9+ (the floor declared in `pyproject.toml`, exercised in CI on 3.9 and
3.12). Roster is JSON; generated documents are Markdown; the extension manifest is YAML; the landing
page is HTML with vanilla JS.

**Primary Dependencies**: None. The CLI stays standard-library only — `argparse`, `json`,
`urllib.request`, `pathlib`, `importlib.metadata`, `subprocess` — and shells out to `uv` and `specify`.
The generator is also stdlib-only by choice, so CI needs no install step and the repo gains no dev
dependency. No YAML library: the manifest is read with a narrow line scanner over its known shape, the
same approach `.github/workflows/ci.yml` already takes with `sed`.

**Storage**: Files only. `agents-list.json` (repo root, published over raw links);
`.specify/extensions/spectra/extension.yml` (the installed manifest, source of the installed version —
confirmed present for the `git` and `agent-context` extensions in this repo, with `  version: "1.0.0"`
nested under `extension:`).

**Testing**: `unittest` from the standard library, run as `python -m unittest discover -s tests`, added
to CI. Chosen over pytest to hold the zero-dependency line. Existing shell assertions in
`.github/workflows/ci.yml` are extended; `test/run.sh` container remains the end-to-end onboarding track.

**Target Platform**: macOS, Linux, Windows (FR-050). Windows matters concretely: `ui.py` already enables
ANSI processing and `version.py` already handles the locked-shim case for self-update.

**Project Type**: CLI tool (`spectra_cli/`) + maintainer documentation generator (`tools/`) + static
landing page (`docs/index.html`) + a data artifact (`agents-list.json`). No service, no database.

**Performance Goals**: Every network fetch bounded at 10 seconds (FR-041a, SC-013). The generator runs on
44 entries — effectively instantaneous; determinism (FR-016), not speed, is its requirement.

**Constraints**: Zero third-party runtime dependencies. Generated documents are committed, so the repo
reads correctly on GitHub for anyone who never runs the generator (FR-024). Removing the flags forces a
MAJOR CLI release (FR-049). One self-contained extension (Principle II) — this feature adds no
`speckit.spectra.*` command.

**Scale/Scope**: 44 roster entries today — 4 shipped by Spectra, 9 provided by Spec Kit, 31 planned —
across 7 SDLC phases. The planned set is what grows; the hand-authored prose set (4 blocks) grows once
per shipped agent.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Evaluated against `.specify/memory/constitution.md` v1.3.0.

| Gate | Verdict | Evidence |
| --- | --- | --- |
| **I — Spec-Driven Development** | PASS | Work is flowing through `specify` → `clarify` → `plan` on branch `006-agent-roster-cli`, with artifacts under `specs/006-agent-roster-cli/`. |
| **II — A Single Self-Contained Extension** | PASS | No new command and no new top-level extension folder. `spectra/` changes only in `extension.yml`'s `description` and `CHANGELOG.md`. `tools/` and `tests/` are repo tooling, excluded from the package by the explicit `packages = ["spectra_cli"]` in `pyproject.toml`. |
| **III — Agent-Agnostic Commands** | N/A | No `speckit.spectra.*` command is added or changed. The command-name pattern is untouched. |
| **IV — Context-Aware by Default** | PASS (by analogy) | Governs extension commands, not the CLI. The CLI equivalent is honoured: every project-scoped command reads real project state — walking up for `.specify/`, reading the installed manifest — rather than assuming. |
| **V — Catalog and Package in Sync** | **FAIL against current text** | Two clauses of Principle V become false with this change: "There is no build script" and "updating the Agents table in `README.md` when a command introduces or changes an agent". Amending them is in scope (FR-022) and tracked below in Complexity Tracking. The *sync obligation itself* is honoured: the description change and the newly generated Commands table in `spectra/README.md` together trigger a full catalog-channel sync — `extension.yml`, `spectra/README.md`, `catalog.json`, `docs/packages/spectra.zip`, `docs/index.html`, `spectra/CHANGELOG.md`. |
| **VI — Two Independently-Versioned Channels** | PASS | CLI `VERSION` 4.0.0 → 5.0.0 (MAJOR: flags removed). Extension 1.3.0 → 1.3.1 (PATCH: description only). Each bumps for its own reason; neither is bumped because the other moved. The run-time-read rule is strengthened, not weakened — FR-042 forbids hard-coding the agent list, exactly as `install.py` already refuses to hard-code the extension list. |
| **Publishing — SemVer per channel** | PASS | Extension bump carries a matching `spectra/CHANGELOG.md` entry; CLI bump is released by a bare semver tag `5.0.0`. |
| **Publishing — VERSION single-sourced, CI-enforced** | PASS, with a required CI edit | `release.yml` parity check is unaffected. `ci.yml` currently asserts `spectra --version` equals `VERSION`; that flag is being removed, so the assertion moves to `spectra cli version`, whose first output line stays the bare version precisely to keep it assertable. |
| **Publishing — required manifest fields** | PASS | Only `description` changes; every required field remains. |
| **Publishing — no silent drift** | PASS, extended | Existing catalog/zip drift checks are kept and three checks are added: generated-region freshness, prose-block presence, roster↔manifest agreement. |
| **Version Control & Branching** | PASS | Branch `006-agent-roster-cli` exactly matches spec directory `specs/006-agent-roster-cli`. |

**Post-Phase-1 re-check**: unchanged. The design adds no dependency, no shipped command, and no second
extension; the only outstanding item is the Principle V amendment, which is deliberate and in scope.

## Project Structure

### Documentation (this feature)

```text
specs/006-agent-roster-cli/
├── plan.md                          # This file
├── spec.md                          # Feature specification (with Clarifications)
├── research.md                      # Phase 0 output — 12 decisions
├── data-model.md                    # Phase 1 output — roster schema, states, id map
├── quickstart.md                    # Phase 1 output — validation scenarios
├── checklists/requirements.md       # Spec quality checklist
├── contracts/
│   ├── agents-list.schema.json      # The roster's contract
│   ├── cli-surface.md               # Command surface, arguments, exit codes, output
│   └── generated-regions.md         # Marker and prose-anchor contract
└── tasks.md                         # Phase 2 output (/speckit.tasks — NOT created here)
```

### Source Code (repository root)

```text
agents-list.json                 # NEW — the roster; single source of truth (FR-001)

spectra_cli/                     # the CLI channel (stdlib only)
├── __init__.py
├── cli.py                       # REWRITTEN — subcommand surface, `cli` group, help panels
├── net.py                       # NEW — 10s-bounded fetch + failure taxonomy (FR-041a)
├── roster.py                    # NEW — fetch/parse roster, schema gate, order & grouping
├── project.py                   # NEW — locate .specify/, classify installation state
├── extension.py                 # NEW — published version; delegate update/remove to specify
├── install.py                   # reused unchanged by `check` (FR-029)
├── ui.py                        # EXTENDED — roster rendering, grouped by phase
└── version.py                   # UNCHANGED — CLI channel self-management, now behind `cli`

tools/                           # NEW — maintainer only; kept out of the wheel by pyproject
├── generate_agent_docs.py       #   generator (default) and verifier (--check)
└── build_package.py             #   deterministic rebuild of docs/packages/spectra.zip

tests/                           # NEW — stdlib unittest, not packaged
├── helpers.py                   # temp projects in all four states, roster fixtures, local HTTP
├── test_net.py                  # bounded fetch, SPECTRA_RAW_BASE, failure taxonomy
├── test_roster.py               # schema gate, ordering, grouping, every field rule
├── test_roster_data.py          # the committed roster against its published contract
├── test_project.py              # root discovery from subdirs, state classification
├── test_extension.py            # manifest version scan, published-version fetch, delegation
├── test_agent_list.py           # grouping, installed marker, schema tolerance, failures
├── test_no_hardcoded_agents.py  # the roster is data, not code
├── test_check.py                # four states, four messages, the install offer
├── test_version_update.py       # three verdicts, exit-code contract, the update loop
├── test_uninstall.py            # delegation, idempotence, the tool left untouched
├── test_generator.py            # determinism, region isolation, every --check failure
└── test_cli_surface.py          # dispatch, exit codes, removed-flag messages, help panels

spectra/                         # the catalog channel
├── extension.yml                # EDITED — description only (1.3.0 → 1.3.1)
├── README.md                    # EDITED — Commands table becomes a generated region; PR agent retitled
└── CHANGELOG.md                 # EDITED — 1.3.1 entry

README.md                        # EDITED — Agents table becomes a generated region; flag docs updated
AGENTS_LIST.md                   # EDITED — two generated regions; prose blocks gain id anchors
CONTRIBUTING.md                  # EDITED — roster + generator in the add-an-agent procedure (FR-021)
CLAUDE.md                        # EDITED via /speckit.agent-context.update — managed region
catalog.json                     # EDITED — description, version
docs/index.html                  # EDITED — reads roster at load; description from catalog (FR-051/052)
docs/packages/spectra.zip        # REBUILT — Principle V
VERSION                          # EDITED — 4.0.0 → 5.0.0
.specify/memory/constitution.md  # AMENDED — Principle V (FR-022), 1.3.0 → 1.4.0
.github/workflows/ci.yml         # EDITED — new checks; `--version` assertion moves to `cli version`
```

**Structure Decision**: The existing three-way split at the repository root is preserved and extended
rather than reorganized — `spectra/` is the extension payload, `spectra_cli/` is the tool, `docs/` is the
published surface. The roster is placed at the repository root beside `catalog.json` because it is
published the same way, over the same raw-link mechanism, and FR-001 fixes the location. New CLI logic
goes into four small single-purpose modules instead of growing `cli.py`, which stays a dispatch and
presentation layer — matching how `install.py` and `version.py` are already separated from it. The
generator lives in a new `tools/` directory that `pyproject.toml`'s explicit package list keeps out of
the wheel, which is what makes FR-023 true by construction rather than by convention.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Principle V's "There is no build script" and "Agents table updated by hand" become false | The whole point of the feature is to stop maintaining the roster in three places (FR-011, FR-012). A generator is the mechanism; the constitution's current text forbids it. FR-022 puts the amendment in scope, and Governance requires it to land in the same change. | Keeping the table hand-maintained and adding `agents-list.json` alongside it was considered and rejected in the BRD's own problem statement: a fourth place to forget makes the drift worse, not better. Amending one clause of one principle is cheaper than institutionalizing the drift. |
| A new top-level `tools/` directory | The generator must exist somewhere, must be runnable as one command (FR-011), and must not ship to users (FR-023). | Putting it inside `spectra_cli/` would package it into the wheel and put maintainer tooling on every user's machine. Putting it inside `spectra/` would place non-command files in the extension payload, violating Principle II's fixed structure. |
| The roster records AI-DLC phase once per phase rather than once per agent | FR-003 requires each agent's AI-DLC phase to be recorded. The mapping is 1:1 from SDLC phase (Foundation→Inception, …, Deployment→Operation), so storing it per agent would create 44 opportunities for the exact class of drift this feature exists to eliminate. | Duplicating it per entry was rejected on those grounds. See research.md decision 2 — flagged explicitly because it is a literal-reading deviation from FR-003 and should be overruled here if that reading is intended strictly. |
