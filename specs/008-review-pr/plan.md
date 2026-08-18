# Implementation Plan: Review PR

**Branch**: `008-review-pr` | **Date**: 2026-08-17 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/008-review-pr/spec.md`

## Summary

Add `speckit.spectra.review-pr` — a fifth command in the existing self-contained `spectra` extension —
that reviews a GitHub pull request against the spec, plan, tasks, ADRs, and constitution it carries,
presents ranked and anchored findings, and publishes a single review containing only what the reviewer
individually selected, under the reviewer's own `gh` credentials.

**Technical approach**: the deliverable is one Markdown instruction file, `spectra/commands/review-pr.md`,
written in Spec Kit's agent-agnostic format. There is no compiled code and no new runtime. The command
composes a small, fixed set of `gh` invocations for every outward and inward interaction, and encodes the
severity rubric, the review budget, the selection grammar, and the confirmation gates as instructions the
coding agent executes. Publication is a single `gh pr review` call carrying both verdict and body.

The work divides into three tracks: (1) author the command file; (2) register it across the manifest,
roster, catalog, and package per Principle V; (3) validate end-to-end against a real pull request via a
throwaway Spec Kit project.

## Technical Context

**Language/Version**: Markdown with YAML front matter — Spec Kit generic command format. No programming
language; the agent is the runtime.

**Primary Dependencies**: `gh` (GitHub CLI) for all pull request interaction — hard-gated at start per
FR-001; `git` for local branch and remote inspection. Both already declared in `spectra/extension.yml`
under `requires.tools`.

**Storage**: None. FR-026 forbids persistence; the agent holds no state between runs. The only optional
write is the reviewer-initiated review file in FR-038.

**Testing**: Manual end-to-end validation through `specify extension add --dev` into a throwaway Spec Kit
project, exercised against real pull requests (see [quickstart.md](./quickstart.md)). Automated
enforcement is repository-level: `tools/generate_agent_docs.py --check` for roster/doc agreement, plus
CI's catalog-version, command-count, and zip-drift assertions.

**Target Platform**: Any coding agent Spec Kit supports (Claude, Kiro, Gemini, Copilot, Cursor, …) on
macOS, Linux, or Windows. The command must not assume a specific agent's invocation syntax.

**Project Type**: Spec Kit extension command — a single Markdown instruction file inside an existing
extension.

**Performance Goals**: Not latency-bound. The operative budget is review breadth, not speed: full-fidelity
review within the declared budget of **40 changed files or 1,500 changed lines**, whichever is reached
first, with risk-ranked subsetting beyond it, disclosed whenever exceeded (FR-013, SC-013; resolved in [research.md](./research.md) R-003).

**Constraints**: Read-write effect with an explicit confirmation gate before every outward action; no
credentials of its own; no telemetry; no new trust boundary; single review event per publication;
GitHub-only.

**Scale/Scope**: One new command file (~250–350 lines, consistent with `create-pr.md` at 203 lines).
43 requirement lines (FR-001…FR-042 plus FR-006a), 13 success criteria, 4 prioritized user stories.
Extension goes from 4 commands to 5.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Evaluated against Spectra Constitution v1.5.0.

| Principle | Requirement | Assessment |
|---|---|---|
| **I. Spec-Driven Development** | Non-trivial work flows through `specify` → `plan` → `tasks` → `implement`; specs under `specs/` | **PASS** — `specs/008-review-pr/` created by `/speckit.specify`, clarified through `/speckit.clarify` (5 questions), now planning. No ad-hoc edits to `spectra/`. |
| **II. A Single Self-Contained Extension** | Every capability is a command file under `spectra/commands/`, registered in the single `spectra/extension.yml`; no new top-level extension folders | **PASS** — one new file `spectra/commands/review-pr.md` registered in the existing manifest. No new extension. FR-040 makes this binding. |
| **III. Agent-Agnostic Commands** | `speckit.spectra.<command>` namespace, `$ARGUMENTS` for input, YAML front matter `description`, registered in `provides.commands` | **PASS** — `speckit.spectra.review-pr` matches `^speckit\.spectra\.<command>$`. Input via `$ARGUMENTS` (optional PR URL). FR-041 makes this binding. |
| **IV. Context-Aware by Default** | Commands read real project context before acting | **PASS** — context-awareness *is* the feature. FR-006/FR-006a read spec, plan, tasks, and ADRs at the PR's head revision; FR-009 reads the constitution and ADRs in force on the base branch. |
| **V. Catalog and Package in Sync** | Same change must register the agent in `agents-list.json`, rebuild the zip, update `catalog.json` and `docs/index.html`, regenerate structured listings, hand-write the prose block | **PASS by plan** — enumerated as a single atomic track below and in [research.md](./research.md) R-007. FR-042 makes it binding. Nothing is deferred to a follow-up commit. |
| **VI. Two Independently-Versioned Release Channels** | Adding a command bumps the extension/catalog version per SemVer; the CLI channel is untouched; the catalog is never tagged | **PASS** — `spectra/extension.yml` and the `catalog.json` entry go `1.3.1` → **`1.4.0`** (MINOR: a command is added). Root `VERSION` (CLI channel) is **not** touched. No git tag, no GitHub Release. |
| **Publishing & Distribution Standards** | `spectra/CHANGELOG.md` entry under the new version; `requires.speckit_version` reflects what was tested; all manifest fields present | **PASS by plan** — CHANGELOG entry under `1.4.0`; `requires.speckit_version` re-verified against the Spec Kit release actually used for validation. |
| **Version Control & Branching Strategy** | One branch per spec; branch name equals spec directory name; branch created before specifying | **PASS** — branch `008-review-pr` equals `specs/008-review-pr`, created by the `before_specify` git hook prior to specification. |

**Gate result: PASS — no violations.** Complexity Tracking is therefore empty and omitted.

### Two constitutional points that shaped the design

- **Principle V's generated/hand-authored split.** `tools/generate_agent_docs.py --check` asserts that
  every *shipped* agent has a hand-written prose block in `AGENTS_LIST.md` anchored by stable id, and
  that the roster and manifest agree on the shipped set. Registering `review-pr` as `available` in
  `agents-list.json` therefore *requires* the `<!-- SPECTRA:AGENT id=review-pr -->` prose block and the
  manifest entry in the same commit, or CI fails. The `docs/index.html` command card is likewise
  hand-authored prose — only the extension version, description, and agent roster are fetched live.
- **Principle VI's channel independence.** This change is catalog-channel only. Touching root `VERSION`
  or cutting a tag would break `/releases/latest` as an unambiguous answer for the CLI's update check.

## Project Structure

### Documentation (this feature)

```text
specs/008-review-pr/
├── spec.md              # Feature specification (/speckit.specify + /speckit.clarify)
├── plan.md              # This file (/speckit.plan)
├── research.md          # Phase 0 output — 8 resolved decisions
├── data-model.md        # Phase 1 output — entities, states, validation rules
├── quickstart.md        # Phase 1 output — end-to-end validation guide
├── contracts/
│   ├── command-interface.md   # Arguments, exit paths, confirmation gates
│   ├── gh-operations.md       # The closed set of gh invocations
│   └── output-format.md       # Summary shape, selection grammar, published body
├── checklists/
│   └── requirements.md  # Spec quality checklist (16/16)
└── tasks.md             # Phase 2 output (/speckit.tasks — NOT created here)
```

### Source Code (repository root)

This feature ships instructions, not code. The tree below lists every file the implementation touches.

```text
spectra/                          # the single self-contained extension (Principle II)
├── commands/
│   └── review-pr.md              # NEW — the entire behavioural deliverable
├── extension.yml                 # MODIFIED — 5th command registered; version 1.3.1 → 1.4.0
├── CHANGELOG.md                  # MODIFIED — 1.4.0 entry
└── README.md                     # MODIFIED — generated Commands table region

agents-list.json                  # MODIFIED — review-pr roster entry (single source of truth)
catalog.json                      # MODIFIED — version 1.4.0, provides.commands 4 → 5, tags, updated_at
AGENTS_LIST.md                    # MODIFIED — hand-written prose block + generated regions
README.md                         # MODIFIED — generated Agents table region
docs/
├── index.html                    # MODIFIED — hand-authored command card for review-pr
└── packages/
    └── spectra.zip               # REBUILT — tools/build_package.py

tools/                            # UNCHANGED — used, not modified
├── build_package.py              # rebuilds the zip
└── generate_agent_docs.py        # rewrites generated regions; --check gates CI
```

**Structure Decision**: No new directories and no new extension. The behavioural change is confined to
one new file, `spectra/commands/review-pr.md`; everything else is the publishing surface that
Principle V requires to move in the same commit. This mirrors how `create-pr.md` — the closest sibling,
being GitHub-facing, read-write, and `gh`-dependent — is structured and registered, so the new command
is consistent by construction rather than by review.

## Complexity Tracking

No constitutional violations. Section intentionally empty.

## Post-Design Constitution Re-Check

*Re-evaluated after Phase 1, as the workflow requires. Verified against the repository, not assumed.*

**Result: PASS — still no violations. No new complexity was introduced by the design.**

Baseline established by running the enforcement tooling before implementation:

```text
$ python3 tools/generate_agent_docs.py --check
agents-list.json (44 agents) matches every generated region; 4 prose blocks present;
roster and manifest agree.                                                      exit: 0

$ python3 tools/build_package.py
wrote docs/packages/spectra.zip (10 files, 29622 bytes)                         exit: 0
(git diff on the zip is empty — already in sync)
```

After implementation the same commands must report **45 agents** and **5 prose blocks**. That single
number is the cheapest possible check that Principle V was honoured.

| Principle | Post-design finding |
|---|---|
| **II. Single extension** | Design adds exactly one file under `spectra/commands/`. No new directories, no new extension, no dependency on another extension. |
| **III. Agent-agnostic** | [command-interface.md](./contracts/command-interface.md) fixes `$ARGUMENTS` as the only input mechanism and forbids the command file from naming any agent's trigger syntax. |
| **IV. Context-aware** | Strengthened during design: [gh-operations.md](./contracts/gh-operations.md) OP-5 pins *which revision* each artifact is read at — spec/plan/tasks at head, constitution/ADRs at base — which is what makes the governance-change detection in FR-009 work at all. |
| **V. Catalog/package sync** | Nine artifacts enumerated in research R-010 and reduced to an executable check in [quickstart.md](./quickstart.md). Two hand-authored items are easy to miss and both fail CI: the `AGENTS_LIST.md` prose block and the `docs/index.html` command card. |
| **VI. Channel independence** | Catalog channel only: `1.3.1` → `1.4.0`. Root `VERSION` untouched, verified by a `git diff --exit-code VERSION` step in quickstart. No tag, no Release. |

### Design decisions that reduced rather than added complexity

Three findings from Phase 0 removed work the spec had implied:

- **GitHub's native three-state review model maps one-to-one onto the spec's verdict set**, so
  publication is a single verified `gh pr review` call with no translation layer. The entire class of
  platform-mismapping risk that BRD-005 carried for GitLab is absent by construction, not by mitigation.
- **`gh pr diff --exclude` handles generated-file exclusion natively**, so FR-014 needs no
  post-filtering — excluded bytes never enter the review and cannot consume the budget.
- **`gh pr view --json` returns every metadata field the summary needs in one call**, including
  `headRefOid` for revision pinning and `statusCheckRollup` for CI status, so there is no
  multi-call metadata assembly to design.

### The one structural constraint the design added

`FR-034`'s disclosure line and `FR-005`'s revision statement became **load-bearing** rather than
presentational: FR-039's prior-findings readback locates the agent's own earlier review by exactly those
two lines (research R-008), since FR-026 forbids any local store. Their format is therefore fixed in
[output-format.md](./contracts/output-format.md), including a machine-readable HTML-comment anchor
carrying the full SHA. Changing either format later silently breaks re-review — a constraint worth
carrying into `tasks.md` as an explicit note rather than discovering by regression.

## Phase Artifacts

| Artifact | Phase | Contents |
|---|---|---|
| [research.md](./research.md) | 0 | 12 decisions (R-001…R-012), all `gh` claims verified against v2.97.0 |
| [data-model.md](./data-model.md) | 1 | 11 entities, validation rules, selection and session state machines |
| [contracts/command-interface.md](./contracts/command-interface.md) | 1 | Arguments, 12-step flow, 5 hard gates, 9 exit paths |
| [contracts/gh-operations.md](./contracts/gh-operations.md) | 1 | The closed set: OP-1…OP-8, plus what is explicitly excluded |
| [contracts/output-format.md](./contracts/output-format.md) | 1 | Summary shape, selection grammar, published body, saved file |
| [quickstart.md](./quickstart.md) | 1 | 8 scenarios, repository-level checks, determinism check |

**Next**: `/speckit.tasks` to produce the dependency-ordered task list.
