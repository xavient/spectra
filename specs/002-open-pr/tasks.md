---
description: "Task list for Open PR extension implementation"
---

# Tasks: Open PR

**Input**: Design documents from `/specs/002-open-pr/`

**Prerequisites**: [plan.md](./plan.md) (required), [spec.md](./spec.md) (required), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/](./contracts/)

**Tests**: No automated tests requested. This is a Spec Kit extension whose behavior is a Markdown command prompt; validation is manual end-to-end via [quickstart.md](./quickstart.md) (Constitution Principle I / Workflow step 4). No test tasks are generated.

**Organization**: Tasks are grouped by user story. NOTE: all runtime behavior lives in the single command-prompt file `github/commands/create-pr.md`. Story phases therefore build that one file incrementally and are **sequential** (same file = no cross-story `[P]`). Each story still yields an independently testable increment of the command's behavior.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Paths are repo-root-relative.

## Path Conventions

This project is a Spec Kit **extension catalog**, not application code. The deliverable is a self-contained folder `github/` at the repo root (modeled on `adr/` and `domain-analyzer/`), plus registration in `catalog.json` and regenerated `docs/`. There is no `src/` or `tests/` tree.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Scaffold the self-contained extension folder (Constitution Principle II).

- [X] T001 Create the `github/` folder with the standard extension layout (`commands/`, `README.md`, `CHANGELOG.md`, `LICENSE`, `extension.yml`) by copying the `adr/` extension as a starting template, then clearing `adr`-specific content
- [X] T002 [P] Author `github/extension.yml`: `schema_version: "1.0"`; `id: github`; name "GitHub"; `version: 1.0.0`; `category` (e.g. "delivery"); `effect: read-write` (research R9); `author: TELUS Digital`; `license: Apache-2.0`; `repository`/`homepage` per `adr/`; `requires.speckit_version: ">=0.11.0"`; `requires.tools` listing `gh` and `git` (required: false, for graceful degradation); `provides.commands` with `speckit.github.create-pr` → `commands/create-pr.md` and a one-line description; and a `hooks.after_implement` block (`command: speckit.github.create-pr`, `optional: true`, offer-style `prompt`, `description`) — per [contracts/hook-and-targeting.md](./contracts/hook-and-targeting.md) Part A
- [X] T003 [P] Add `github/LICENSE` (Apache-2.0, TELUS Digital — copy from `adr/LICENSE`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Create the command-prompt skeleton plus the shared precondition, remote-detection, and source-validation steps that every user story depends on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete (all stories edit `commands/create-pr.md`).

- [X] T004 Create `github/commands/create-pr.md` with YAML front matter (`description`) and an overall step outline; handle `$ARGUMENTS` as optional, supporting no-arg (default flow), `--draft`, and `--base <branch>` (FR-009, FR-016, Principle III) — per [contracts/command-interface.md](./contracts/command-interface.md)
- [X] T005 Add the "Preconditions & graceful degradation" step to `github/commands/create-pr.md`: probe `gh` installed (`command -v gh`), `gh` authenticated (`gh auth status`), and remote-is-GitHub via in-prompt remote detection (`git config --get remote.origin.url`, parse owner/repo, confirm `github.com` — re-implemented in-prompt, NOT a runtime dependency on the `git` extension); on any failure print a clear manual `git push` + `gh pr create` fallback that includes the target branch it would have used, never failing opaquely (FR-007, SC-006) — per [research.md](./research.md) R7 and [data-model.md](./data-model.md) (Remote, ToolingPreconditions)
- [X] T006 Add the "Source-branch validation" step to `github/commands/create-pr.md`: derive the source from `git rev-parse --abbrev-ref HEAD` and refuse (with explanation) if HEAD is detached, the branch is the base/default branch (e.g. `main`), or it does not match a directory under `specs/` (one-branch-per-spec); never open a PR from a non-spec branch (FR-005, SC-007) — per [research.md](./research.md) R3 and [data-model.md](./data-model.md) (SourceBranch)

**Checkpoint**: Command exists, refuses to run in unsafe contexts, and degrades gracefully — user stories can now be layered on.

---

## Phase 3: User Story 1 - Open a PR after implementation, confirming the target when none is defined (Priority: P1) 🎯 MVP

**Goal**: After `implement`, the command offers to open a PR; on acceptance and with no promotion flow defined, it proposes the default branch, confirms source → target, opens a ready-for-review PR (pushing first if needed), and returns the PR URL.

**Independent Test**: On a completed spec branch in a GitHub repo with no promotion flow, accept the offer (or invoke directly); verify the agent proposes `<spec-branch> → <default-branch>`, opens the PR only after explicit confirmation, and returns the PR URL in chat; declining opens nothing (quickstart S1, S4, S5).

- [X] T007 [US1] Add the "Offer & await go-ahead" framing to `github/commands/create-pr.md`: the command offers to open a PR and takes NO Git/remote action until the user responds; an explicit decline leaves the branch unpushed and no PR opened (FR-001) — per spec US1 acceptance #1 and #4
- [X] T008 [US1] Add the "Derive & confirm default target" step to `github/commands/create-pr.md`: when no promotion flow is defined, resolve the repository default branch (`gh repo view --json defaultBranchRef`, fallback `origin/HEAD`), propose `source → default`, and require explicit confirmation before proceeding (FR-004, SC-003) — per [research.md](./research.md) R1 step 4 and [contracts/hook-and-targeting.md](./contracts/hook-and-targeting.md) Part B
- [X] T009 [US1] Add the "Existing-PR detection" step to `github/commands/create-pr.md`: run `gh pr list --head <source> --state open --json url`; if an open PR exists, return its URL and stop without opening a duplicate (FR-010, SC-005) — per [research.md](./research.md) R4
- [X] T010 [US1] Add the "Commit & push" step to `github/commands/create-pr.md`: surface uncommitted changes (`git status --porcelain`) before opening (FR-012); detect whether the source branch is on the remote / has unpushed commits, ask to push, and on confirmation run `git push -u origin <source>`, never pushing without confirmation (FR-014) — per [research.md](./research.md) R5
- [X] T011 [US1] Add the "Open the PR" step to `github/commands/create-pr.md`: run `gh pr create --base <target> --head <source>` with a title and body derived from the spec name/summary plus a link to the spec file (FR-011), ready-for-review by default and `--draft` only on explicit opt-in (FR-016); explicitly forbid modifying source code, the spec, or the constitution — the only mutations are push + PR create (FR-008) — per [research.md](./research.md) R6 and [contracts/command-interface.md](./contracts/command-interface.md)
- [X] T012 [US1] Add the "Report in chat" step to `github/commands/create-pr.md`: return the PR URL and the chosen base branch in chat on success (FR-006, SC-004)

**Checkpoint**: MVP — on any GitHub project with no promotion flow, the command opens a correctly-targeted PR in a single confirmation and returns the link.

---

## Phase 4: User Story 2 - Honor the project's promotion strategy (Priority: P2)

**Goal**: When a promotion flow is defined, the command targets the correct next branch in the flow and states the rule it came from, instead of the default branch.

**Independent Test**: With a promotion flow `feat → dev → main` (constitution and/or `git-config.yml`) and `dev` present on the remote, run from a spec branch; verify the PR base is `dev`, the agent states it chose `dev` because of the flow, and it does not ask the user to re-pick (quickstart S2, S8).

- [X] T013 [US2] Add the "Promotion-flow target derivation" step to `github/commands/create-pr.md`: read the flow from BOTH the constitution's *Version Control & Branching Strategy* section and the `git` branching config (`.specify/extensions/git/git-config.yml`); when a single unambiguous flow exists, target the next stage after the source, state the derived target and the rule it came from, and do NOT ask the user to re-pick (FR-002, FR-003, SC-002) — per [contracts/hook-and-targeting.md](./contracts/hook-and-targeting.md) Part B and [research.md](./research.md) R1–R2
- [X] T014 [US2] Add the "Conflict & missing-target handling" to `github/commands/create-pr.md`: when the constitution and config define disagreeing flows, surface the conflict and ask rather than applying a precedence (FR-013); when a promotion-flow target branch does not exist on the remote, surface it and stop — never silently retarget `main` or create the branch (edge cases) — per [data-model.md](./data-model.md) (PromotionFlow, TargetBranch)

**Checkpoint**: Promotion strategy is enforced by construction; conflicts and missing branches are surfaced, not guessed.

---

## Phase 5: User Story 3 - Decline now, open later on demand (Priority: P3)

**Goal**: Declining the post-implement offer is safe and non-destructive, and the same command can open the PR later via direct invocation.

**Independent Test**: Decline the offer and confirm nothing is pushed or opened; later invoke `speckit.github.create-pr` directly on the same spec branch and verify it runs the identical targeting/confirmation flow and opens the PR (quickstart S3).

- [X] T015 [US3] Add an "On-demand invocation" note to `github/commands/create-pr.md` making explicit that the command is fully runnable on demand (not only via the `after_implement` offer) and that a prior decline leaves no Git/remote state, so a later direct invocation runs the same flow end to end (FR-015) — per spec US3 acceptance and [contracts/hook-and-targeting.md](./contracts/hook-and-targeting.md) Part A (`optional: true` offer)

**Checkpoint**: All three stories are independently functional within the single command.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, catalog registration, site regeneration, and end-to-end validation.

- [X] T016 [P] Complete `github/README.md` (modeled on `adr/README.md`): what it does, install (`--dev` and catalog), usage with per-agent trigger note (e.g. Claude `/speckit-github-create-pr`), the `after_implement` offer + on-demand invocation, GitHub/`gh`-only scope and graceful-degradation behavior, and the read-write effect note
- [X] T017 [P] Author `github/CHANGELOG.md` with a `## [1.0.0] - <date>` entry summarizing the initial release (modeled on `adr/CHANGELOG.md`)
- [X] T018 Register the extension in the canonical `catalog.json`: add an `github` entry mirroring the `adr`/`domain-analyzer` entries' fields (name, id, description, category, effect `read-write`, version 1.0.0, repository/homepage/documentation/changelog URLs, license, `requires.speckit_version` `>=0.11.0`, `provides.commands` count 1, tags) — do NOT set catalog/download URLs (generated)
- [X] T019 Run `python3 build_packages.py` from repo root and commit the regenerated `docs/` (index.html, catalog.json, packages/github.zip); resolve any `!` URL-drift warning before publishing (Constitution Principle V)
- [ ] T020 Execute the [quickstart.md](./quickstart.md) validation scenarios (S1–S8) by installing with `specify extension add --dev ./github` into a throwaway Spec Kit project; confirm the only mutations in the target project are the branch push and PR creation (no source/spec/constitution edits)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories.
- **User Stories (Phases 3–5)**: All depend on Foundational. Because every story edits the same file (`commands/create-pr.md`), they proceed **sequentially in priority order** (US1 → US2 → US3); they are not parallelizable against each other.
- **Polish (Phase 6)**: T018/T019/T020 depend on the command and docs being complete; T016/T017 (docs) can begin once US1 behavior is settled.

### User Story Dependencies

- **US1 (P1)**: Depends only on Foundational. The MVP — opens a correctly-targeted PR in the no-flow case.
- **US2 (P2)**: Adds promotion-flow targeting on top of US1's open-PR mechanics. Independently testable.
- **US3 (P3)**: Adds explicit on-demand semantics on top of the offer. Independently testable.

### Within Each User Story

- Steps are added to `commands/create-pr.md` in listed order; later steps assume earlier ones exist.

### Parallel Opportunities

- Setup: T002 and T003 run in parallel ([P]) — different files from T001's scaffold.
- Polish: T016 and T017 run in parallel ([P]) — different files.
- Cross-story parallelism is NOT available (single shared command file).

---

## Parallel Example: Setup

```bash
# After T001 scaffolds the folder, author these two files in parallel:
Task: "Author github/extension.yml manifest (command + after_implement hook)"
Task: "Add github/LICENSE (Apache-2.0, TELUS Digital)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1: Setup → 2. Phase 2: Foundational (CRITICAL) → 3. Phase 3: US1.
4. **STOP and VALIDATE**: quickstart S1 (+ S4 push, S5 dedup, S6 degradation, S7 refusal) — a single confirmation opens a correctly-targeted PR and returns the link.
5. The MVP already delivers the core value: closing the loop from "implementation done" to "PR open" for any GitHub project.

### Incremental Delivery

1. Setup + Foundational → command scaffold, preconditions, source validation ready.
2. US1 → no-flow open + return URL (MVP) → validate.
3. US2 → promotion-flow targeting + conflict handling → validate.
4. US3 → on-demand invocation semantics → validate.
5. Polish → README/CHANGELOG, register in `catalog.json`, rebuild `docs/`, run quickstart.

### Notes

- [P] = different files, no dependencies. The single command file makes most story work sequential.
- Each user story is an independently demoable behavior of the command.
- Per Constitution Principle V, the feature is not "done" until `docs/` is regenerated and committed.
- Commit after each task or logical group.
