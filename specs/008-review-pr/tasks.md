# Tasks: Review PR

**Input**: Design documents from `/specs/008-review-pr/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/](./contracts/), [quickstart.md](./quickstart.md)

**Tests**: No automated test tasks. The spec does not request TDD, and the deliverable is a Markdown
instruction file with no unit-test surface. Validation is real: the eight scenarios in
[quickstart.md](./quickstart.md) plus the repository-level enforcement scripts, all in Phase 8.

**Organization**: Grouped by user story so each is independently deliverable and testable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel — different files, no dependency on incomplete work
- **[Story]**: `[US1]`…`[US4]`, on user-story phases only
- Every task names its exact file path

## Path Conventions

This feature ships instructions, not code. There is no `src/` or `tests/`. Real paths:

- **The behavioural deliverable**: `spectra/commands/review-pr.md` (one new file)
- **The publishing surface**: `spectra/extension.yml`, `spectra/CHANGELOG.md`, `spectra/README.md`,
  `agents-list.json`, `AGENTS_LIST.md`, `README.md`, `catalog.json`, `docs/index.html`,
  `docs/packages/spectra.zip`
- **Tooling used, never modified**: `tools/generate_agent_docs.py`, `tools/build_package.py`

> ## ⚠️ Read this before parallelizing
>
> **Almost nothing here is parallelizable, and that is a property of the feature, not an oversight.**
>
> User stories 1 through 4 are not separate modules — they are sections of a **single Markdown file**,
> `spectra/commands/review-pr.md`. Two people editing it simultaneously conflict on every task. The
> `[P]` marker therefore appears only where tasks genuinely touch **different files**, which in practice
> means the publishing surface in Phase 7 and nothing else.
>
> The stories remain independently *testable* and *deliverable* — you can stop after US1 and ship a
> complete agent. They are not independently *assignable*.

---

## Phase 1: Setup

**Purpose**: Establish the baseline and the file skeleton.

- [X] T001 Record the pre-implementation baseline by running `python3 tools/generate_agent_docs.py --check` and `python3 tools/build_package.py` from the repository root; confirm the output reads **44 agents / 4 prose blocks / roster and manifest agree** and that `git diff --stat docs/packages/spectra.zip` is empty. Note these numbers — Phase 8 asserts they became 45 and 5.
- [X] T002 Create `spectra/commands/review-pr.md` with YAML front matter carrying a single `description` key, matching the style of `spectra/commands/create-pr.md`; add the H1 title and a one-paragraph statement of the agent's job (review a GitHub PR against the intent and standards it carries, publish only what the reviewer selects).
- [X] T003 Add the **User Input** section to `spectra/commands/review-pr.md` documenting the `$ARGUMENTS` surface per [contracts/command-interface.md](./contracts/command-interface.md): no argument, `<url>`, `<number>`, `--since <revision>`; unrecognized arguments are noted and ignored rather than fatal.
- [X] T004 Add the **governing rule** section to `spectra/commands/review-pr.md`: the only permitted mutation is publishing one review after explicit confirmation (FR-008); no edits to source, spec, plan, tasks, or constitution; no working-tree changes including branch checkout without explicit permission (FR-007).

**Checkpoint**: The file exists, declares its interface, and states its limits.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The cross-cutting machinery every user story depends on — pre-flight, platform access, artifact reading, and the finding model.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. All tasks edit the same file and are therefore strictly sequential.

- [X] T005 Add the **pre-flight gate** to `spectra/commands/review-pr.md` per [contracts/gh-operations.md](./contracts/gh-operations.md) OP-1: `command -v gh`, `gh auth status`, `gh api user --jq .login`. A failure of either of the first two is a **hard stop before any analysis** (FR-001), and the two must produce **distinct** messages — a missing binary needs an install, a failed auth needs `gh auth login` (SC-011).
- [X] T006 Add the **trust posture** statement to `spectra/commands/review-pr.md`: holds no credentials of its own and acts solely through the reviewer's existing `gh` authentication (FR-002); all PR interaction goes through `gh` exclusively (FR-003); nothing is persisted between runs (FR-026).
- [X] T007 Add **target resolution** to `spectra/commands/review-pr.md` per OP-2: pass the reference to `gh` unparsed (research R-001); with no argument offer the current branch's open PR first, then list open PRs for an explicit choice, and never auto-select from several (FR-004).
- [X] T008 Add **revision pinning** to `spectra/commands/review-pr.md` per OP-3: one `gh pr view --json` call retrieving the full verified field set from research R-002, capturing `headRefOid` as the pinned revision and `baseRefOid` for base-branch reads; the pinned revision is reported in both the summary and the published body (FR-005).
- [X] T009 Add **artifact retrieval at a revision** to `spectra/commands/review-pr.md` per OP-5: `gh api repos/$REPO/contents/<path>?ref=<sha>` with base64 decoding, using the repository derived from the PR URL rather than `{owner}`/`{repo}` placeholders; spec, plan, tasks, and the PR's own ADRs at `headRefOid` (FR-006); constitution and ADRs in force at `baseRefOid` (FR-009). Explicitly forbid `git show <sha>:<path>` and branch checkout — both fail on fork PRs and the latter violates FR-007.
- [X] T010 Add the **three-tier spec discovery chain** to `spectra/commands/review-pr.md` per FR-006a: (1) a spec in the PR's own diff, (2) the Spec Kit feature record at the head revision, (3) treat as no-spec. Branch-name inference is explicitly forbidden. The tier that resolved MUST be stated in the output.
- [X] T011 Add the **declared review budget** to `spectra/commands/review-pr.md` per research R-003: **40 changed files or 1,500 changed lines**, whichever is hit first, stated as an assertable figure; the seven-level risk ranking; and the two-pass diff from R-005 — `gh pr diff --name-only` to rank, `gh pr diff --patch` only for what made the cut. Size never causes a refusal, and the budget is never surfaced to the reviewer as a choice (FR-013).
- [X] T012 Add the **generated-file exclusion set** to `spectra/commands/review-pr.md` per research R-004: the `gh pr diff --exclude` pattern list (lock files, vendored trees, build output, minified assets), applied at fetch time and named in the coverage statement (FR-014).
- [X] T013 Add the **severity rubric** to `spectra/commands/review-pr.md` — the full five-level table from FR-016 with assignment criteria and merge effect, the display labels `S1`/`S2`/`S3`/`Nit`/`Q`, and both floors: an explicit constitution MUST violation never below Major, an explicit compliance or regulatory MUST violation never below Blocker.
- [X] T014 Add the **confidence axis** to `spectra/commands/review-pr.md`: `high`/`medium`/`low` on every finding, and the rule that a low-confidence finding MUST NOT be a blocker — it becomes a Question instead (FR-017).
- [X] T015 Add the **finding structure and its existence invariant** to `spectra/commands/review-pr.md` per [contracts/output-format.md](./contracts/output-format.md): the field order, and the hard rule that a finding lacking **both** a file/line anchor **and** a cited source MUST NOT be reported at all (FR-015). Add grouping by owner class — intent, guardrail, craft (FR-018) — flat sequential numbering in presentation order (FR-019), and collapsing of repeated instances into one entry with a count (FR-020).

**Checkpoint**: Foundation ready. Every story below builds on the pre-flight gate, the `gh` operation set, revision-pinned artifact reads, and the finding model.

---

## Phase 3: User Story 1 — Review by URL and publish a curated review (Priority: P1) 🎯 MVP

**Goal**: A reviewer points the command at a PR URL, receives ranked and anchored findings with a recommended verdict, selects what to raise, chooses the verdict, and publishes one review under their own name.

**Independent Test**: Run against a real PR authored by someone else that carries a spec. Verify every finding is anchored and sourced with a severity and confidence; verify an empty selection posts nothing; verify a curated selection posts exactly what was selected after a preview and a final go-ahead; verify the returned link resolves to a single review event.

**Why this is the MVP**: shipped alone it delivers the entire value of the agent — conformance review plus the human filter. Stories 2 through 4 are convenience, honesty, and efficiency layers on this same engine.

### Analysis passes

- [X] T016 [US1] Add **lens selection** to `spectra/commands/review-pr.md`: choose lenses from what the diff actually touches rather than running all of them, and report every lens as `run` or `not-run` with a reason for each omission (FR-011). A lens that did not run is never reported as passed.
- [X] T017 [US1] Add the **traceability lens** to `spectra/commands/review-pr.md`, running in both directions: work claimed complete but absent from the diff, and changes present in the diff that no task or requirement authorized (FR-010).
- [X] T018 [US1] Add the **guardrail lens** to `spectra/commands/review-pr.md`: evaluate against the constitution and ADRs in force at `baseRefOid`, quote the violated clause in the finding, and surface any PR that modifies the constitution or an ADR as a **governance change regardless of severity** (FR-009).
- [X] T019 [US1] Add the **craft lenses** to `spectra/commands/review-pr.md` — correctness, security, tests, data and migrations, API contract and compatibility, performance, operability, maintainability, docs, dependencies, accessibility, internationalization — each subject to the FR-015 anchor-and-source invariant.

### Presentation

- [X] T020 [US1] Add the **summary layout** to `spectra/commands/review-pr.md` in the fixed 11-element order from [contracts/output-format.md](./contracts/output-format.md) Surface 1, covering PR identity, branches, pinned revision, change size, spec status with its discovery tier, CI status, applicable draft/fork/self-review notices, recommended verdict, the agent's own reading of the change, the severity tally by class, the findings, coverage and limits, and next actions (FR-021).
- [X] T021 [US1] Add **verdict recommendation** to `spectra/commands/review-pr.md`: derived mechanically from the findings, drawn from the closed set of approve / request-changes / comment-only, presented as a recommendation only, and never recommending approval while required checks are failing (FR-022, spec Assumptions).
- [X] T022 [US1] Add the **coverage and limits statement** to `spectra/commands/review-pr.md`: revision reviewed, lenses run, lenses not run with reasons, files excluded and why, evidence unavailable, and overall confidence. Mandatory in every review with no exceptions (FR-011, FR-021, SC-003, SC-013).

### Selection and verdict — the human filter

- [X] T023 [US1] Add the **selection prompt and grammar** to `spectra/commands/review-pr.md` per [contracts/output-format.md](./contracts/output-format.md) Surface 2: numbers, comma lists, ranges, severity groups, `all`, `none`, `all except N`, combined forms, and the `N:severity` override form (FR-024, FR-030). Nothing is pre-selected; an empty or absent selection publishes nothing and ends the run as a success (FR-023). An unparseable selection re-prompts without advancing.
- [X] T024 [US1] Add the **accepted-and-dropped confirmation** to `spectra/commands/review-pr.md`: both lists stated in full before any outward action, with a note that the transcript is the only record since nothing is persisted (FR-025, FR-026).
- [X] T025 [US1] Add **verdict selection** to `spectra/commands/review-pr.md`: the reviewer chooses from the closed three-value set and the agent MUST NOT choose on their behalf (FR-027).
- [X] T026 [US1] Add the **blocker-override path** to `spectra/commands/review-pr.md`: when approve is chosen alongside an accepted blocker, state the contradiction, require a **typed** confirmation rather than a bare yes, record the acknowledged blocker in the published body, and do **not** refuse the reviewer's choice outright (FR-028, SC-009).
- [X] T027 [US1] Add **self-review handling** to `spectra/commands/review-pr.md`: when the authenticated user is the PR author, explain that self-approval is unavailable and offer the remaining two verdicts rather than attempting an action GitHub will reject (FR-029).

### Publication

- [X] T028 [US1] Add the **published body format** to `spectra/commands/review-pr.md` per [contracts/output-format.md](./contracts/output-format.md) Surface 3, including the two **load-bearing** lines: the `<!-- spectra:review-pr revision=<full-sha> -->` machine anchor and the AI-assisted-and-human-curated disclosure line (FR-034, FR-005). Add an explicit warning in the file that these formats are parsed by the re-review path and MUST NOT be changed casually. Only accepted findings appear; dropped findings never do.
- [X] T029 [US1] Add the **preview gate** to `spectra/commands/review-pr.md`: display the exact body that will be posted and obtain a final explicit go-ahead; without it, publish nothing (FR-031).
- [X] T030 [US1] Add the **freshness re-check** to `spectra/commands/review-pr.md` per OP-8: re-read `headRefOid` immediately before publishing and, if it moved, warn and offer re-analysis instead of publishing against stale code (FR-032).
- [X] T031 [US1] Add **publication** to `spectra/commands/review-pr.md` per OP-7: exactly one `gh pr review <ref>` call carrying both verdict and body, with the body on stdin via `--body-file -` to avoid shell-escaping long content; return the review URL on success (FR-033).
- [X] T032 [US1] Add **post-pre-flight degradation** to `spectra/commands/review-pr.md`: on a permission or fork restriction at publication time, present the review in chat, hand over the rendered body for manual posting, explain what failed, and leave **no partial review** behind (FR-035). Contrast this explicitly with the T005 hard stop so the two are not conflated.
- [X] T033 [US1] Add **duplicate own-review detection** to `spectra/commands/review-pr.md` per OP-6: detect an existing review by the same reviewer on the same PR and ask whether to supersede it or add another (FR-036).
- [X] T034 [US1] Add the remaining **edge cases** to `spectra/commands/review-pr.md`: fork noted upfront to set expectations, draft state reported without declining, empty or trivial diff reported as such with **no findings manufactured**, and the reviewer's local checkout never relied upon for the PR's context (spec Edge Cases; FR-006, FR-007).
- [X] T035 [US1] Add the **optional saved review** to `spectra/commands/review-pr.md` per [contracts/output-format.md](./contracts/output-format.md) Surface 4: at the end of a review, offer to save the **complete** review including the findings the reviewer dropped, defaulting to **not** saving, written to a reviewer-chosen path outside the spec directory, and never written without an explicit request (FR-038).

**Deliberately not implemented here**: FR-037, line-anchored inline comments. The spec's constraints
state the single-body form ships first, and research R-007 records why — inline anchoring requires the
`gh api .../reviews` POST route with hand-built JSON and diff-position arithmetic. It remains a
`SHOULD` for a follow-on release; no task in this plan implements it.

**Checkpoint**: US1 is complete. The agent is fully functional and shippable as-is — run quickstart Scenarios 1 and 2 before proceeding.

---

## Phase 4: User Story 2 — Discover and pick a PR to review (Priority: P2)

**Goal**: A reviewer with no URL starts a review without leaving the terminal, and cannot review the wrong PR by accident.

**Independent Test**: Run with no arguments in a repo with several open PRs; verify the current branch's PR is offered first when one exists, that the list appears otherwise, that nothing is reviewed until an explicit choice, and that a repo with no open PRs stops cleanly without an error.

- [X] T036 [US2] Extend the target-resolution section of `spectra/commands/review-pr.md` with the **no-argument discovery flow**: offer the current branch's open PR first via `gh pr list --head <branch> --state open`, then fall back to the full picker listing number, title, author, and target branch (FR-004).
- [X] T037 [US2] Add the **empty-repository path** to `spectra/commands/review-pr.md`: when no open PRs exist, say so and stop **without an error**, and when the reviewer declines the offered PR or picks nothing, stop cleanly (FR-004).

**Checkpoint**: US1 and US2 both work independently.

---

## Phase 5: User Story 3 — Review a PR that carries no spec (Priority: P3)

**Goal**: The agent is useful on repositories that are not spec-driven, and is honest that it is reviewing without an authorized baseline rather than implying conformance it cannot check.

**Independent Test**: Point at a PR with no spec in a repo that does have a constitution on the base branch. Verify the summary states the absence, traceability is listed as not run and never as passed, guardrail findings are still produced with their clause quoted, and no intent-class observation is rated blocker or major.

- [X] T038 [US3] Add the **no-spec path** to `spectra/commands/review-pr.md` for discovery tier 3 (FR-012): state in the summary header that no spec was found and the change was reviewed standalone; list the traceability lens as **not run** and never as passed; keep the guardrail lens at **full strength** because the constitution exists independently of any spec; and cap intent-class findings at **Question** severity.

**Checkpoint**: All three of US1, US2, US3 work independently.

---

## Phase 6: User Story 4 — Delta re-review after new commits (Priority: P4)

**Goal**: The second pass costs a fraction of the first.

**Independent Test**: Review a PR and publish, have new commits pushed, re-run with `--since <earlier revision>`. Verify findings are scoped to the delta, both revisions are stated, previously published findings are sorted into apparently-resolved and still-open with no unevidenced claims, and that no local file was written anywhere.

- [X] T039 [US4] Add the **delta review path** to `spectra/commands/review-pr.md` for `--since <revision>`: review only what changed between the named prior revision and the current head, and state **both** revisions in the summary (FR-039).
- [X] T040 [US4] Add **prior-findings readback** to `spectra/commands/review-pr.md` per OP-6 and research R-008: list the PR's reviews, filter to those authored by the authenticated user whose body carries the T028 machine anchor, parse the recorded revision, and sort previously published findings into apparently-resolved and still-open **without asserting a resolution that cannot be evidenced**. Introduce no stored history (FR-026). Where no prior review can be read, say so and report the delta alone.

**Checkpoint**: All four user stories work independently.

---

## Phase 7: Publishing Surface (Principle V)

**Purpose**: Register the agent everywhere the constitution requires.

**⚠️ This phase is MANDATORY, not optional polish.** Constitution Principle V requires every item here in
the **same change** as the command file. CI fails on any omission, and two items are hand-authored and
easy to forget: the `AGENTS_LIST.md` prose block and the `docs/index.html` command card.

- [X] T041 Register the command in `spectra/extension.yml`: add the fifth `provides.commands` entry with `name: "speckit.spectra.review-pr"`, `file: "commands/review-pr.md"`, and a description; bump `extension.version` from `1.3.1` to **`1.4.0`** (MINOR — a command is added); update the `requires.tools` comment to record that `create-pr` degrades without `gh` while `review-pr` hard-gates on it, keeping `gh` at `required: false` per research R-009 (FR-040, FR-041).
- [X] T042 [P] Add the roster entry to `agents-list.json`: `id: review-pr`, a one-sentence description, `status: available`, `phase: deployment-operations`, `type: core`, `provider: spectra`, `command: speckit.spectra.review-pr` (FR-042).
- [X] T043 [P] Write the hand-authored prose block in `AGENTS_LIST.md` anchored by `<!-- SPECTRA:AGENT id=review-pr -->`, covering what the agent does, its arguments, and how to run it — matching the depth of the existing `create-pr` block. Required by `check_prose_anchors`; its absence fails CI.
- [X] T044 [P] Add the hand-authored command card for `review-pr` to `docs/index.html` in the `<ul class="cmds">` list, following the existing card structure: `name`, `cdesc`, `args`, and a Claude-form example. Only the extension version, description, and agent roster are fetched live — this card is prose and must be written.
- [X] T045 [P] Add the `1.4.0` entry to `spectra/CHANGELOG.md` describing the new `review-pr` command, under a heading matching the new version exactly.
- [X] T046 Update the `spectra` entry in `catalog.json`: `version` to `1.4.0`, `provides.commands` from `4` to `5`, refresh `updated_at`, and add `review` and `code-review` to `tags`. Must agree exactly with T041 or CI's parity check fails.
- [X] T047 Regenerate every structured agent listing by running `python3 tools/generate_agent_docs.py` from the repository root, updating the generated regions in `README.md`, `AGENTS_LIST.md`, and `spectra/README.md`. Depends on T041 and T042 — the generator asserts roster and manifest agree (FR-042).
- [X] T048 Rebuild the published package by running `python3 tools/build_package.py`, producing an updated `docs/packages/spectra.zip` containing the new command file. Depends on T041.

**Checkpoint**: `python3 tools/generate_agent_docs.py --check` must now report **45 agents / 5 prose blocks / roster and manifest agree**, **and** `python3 -m unittest discover -s tests -q` must pass. The CLI's `tests/test_roster_data.py` asserts the roster's exact shape — total, available count, and shipped ids — so adding an agent necessarily changes it. Two of those tests encode the count in the method name. This second command was missing from the original plan and the failure was found by CI instead (research R-010 correction); the roster has **four** consumers, not three.

---

## Phase 8: Validation

**Purpose**: Prove it works before publishing. Executes [quickstart.md](./quickstart.md).

- [X] T049 Run the four repository-level checks from [quickstart.md](./quickstart.md): the generator `--check` reporting 45 agents and 5 prose blocks, a rebuilt-and-in-sync `docs/packages/spectra.zip`, the dependency-free manifest/catalog parity script reporting all four lines `PASS` at `1.4.0` with 5 commands, and `git diff --exit-code VERSION` confirming the CLI channel was untouched (Principle VI).
- [X] T050 Install the working copy into a throwaway project per [quickstart.md](./quickstart.md): `specify init .` in `/tmp/review-pr-trial`, then `specify extension add --dev <repo>/spectra`, then `specify extension info spectra` confirming 5 commands including `speckit.spectra.review-pr`; restart the agent and confirm the trigger appears in its command list.
- [ ] T051 [US1] Execute **Scenario 1** of `specs/008-review-pr/quickstart.md` against a real PR authored by someone else that carries a spec, asserting all nine summary properties and all six gate behaviours in order, then verify on GitHub that exactly **one** review event was created carrying only the selected findings, the disclosure line, and the machine anchor with the full SHA (SC-001, SC-002, SC-005, SC-008, SC-010).
- [ ] T052 [US1] Execute **Scenario 2** of `specs/008-review-pr/quickstart.md`, the blocker-override path: confirm a bare `yes` is rejected as the confirmation, the choice is not refused outright, and the `## Acknowledged blocker — approved over` section appears in the published body (FR-028, SC-009).
- [ ] T053 [US2] Execute **Scenario 3** of `specs/008-review-pr/quickstart.md`: current-branch PR offered first, picker otherwise, nothing reviewed without an explicit choice, and a clean non-error stop in a repo with no open PRs.
- [ ] T054 [US3] Execute **Scenario 4** of `specs/008-review-pr/quickstart.md` including the explicit three-tier discovery matrix: tier 1 with a spec in the diff, tier 2 with only the feature record, tier 3 with neither; confirm the resolved tier is stated and that branch name is not used even where it would have worked.
- [ ] T055 [US4] Execute **Scenario 5** of `specs/008-review-pr/quickstart.md`: delta scoping, both revisions stated, prior findings sorted into resolved and open, and confirmation that no local file was written anywhere (SC-006).
- [ ] T056 Execute **Scenario 6** of `specs/008-review-pr/quickstart.md`, the hard pre-flight gate: run once with `gh` off `PATH` and once authenticated-out; confirm both stop before any analysis, produce **distinct** messages, and neither degrades into a partial review (FR-001, SC-011).
- [ ] T057 Execute **Scenario 7** of `specs/008-review-pr/quickstart.md`, post-pre-flight degradation, against a fork PR or a repo lacking review permission: fork noted upfront, full review still runs, rendered body handed over on failure, and no partial review left on the PR (FR-035, SC-006).
- [ ] T058 Execute **Scenario 8** of `specs/008-review-pr/quickstart.md`, the remaining edge-case matrix: self-authored PR, mid-session revision move, existing own review, oversized diff exceeding 40 files or 1,500 lines, constitution-modifying PR, draft PR, generated files, empty diff, and a local checkout on a different branch.
- [ ] T059 Run the **determinism check** in `specs/008-review-pr/quickstart.md`: review the same revision twice, selecting nothing both times, and confirm identical findings with identical severities. Severity drift means the T013 rubric is being applied loosely, which breaks SC-004 and the trust model — treat any drift as a defect in the rubric's wording, not as acceptable variance.
- [ ] T060 Resolve the three behaviours research R-007 could not verify without a live PR, and record the outcomes in `specs/008-review-pr/research.md`: whether `gh pr review --request-changes` rejects an empty body, that self-approval returns 422 with an intelligible message rather than a raw API error, and that `--body-file -` handles a long body containing backticks, quotes, and newlines without mangling.
- [X] T061 Re-verify `requires.speckit_version` in `spectra/extension.yml` against the Spec Kit version actually used for T050 validation, and update the pin if it has moved (Publishing & Distribution Standards).
- [ ] T062 Execute **Scenario 9** of `specs/008-review-pr/quickstart.md` — the cross-repo regression guard. From a directory that is **not** a clone of the reviewed project, review a PR by URL from another repository that carries a spec, and confirm the spec is found, the constitution is read from the target repo's base branch, guardrail findings are produced, and the coverage statement does **not** claim "no spec found". Also confirm a fork PR's artifacts read successfully via the base repository. This scenario exists because the `{owner}`/`{repo}` placeholder defect it catches shipped past every other check (research R-006 correction).
- [ ] T063 Clean up: remove `/tmp/review-pr-trial`, and delete or dismiss every test review left on a real pull request — they are visible to the author and may satisfy branch protection.

---

## Phase 9: Publish (Constitution Development Workflow step 6)

**Purpose**: Make the agent actually available to users. Until this phase runs, all 62 preceding tasks
produce a validated but **unpublished** agent.

**⚠️ Required by the constitution, not optional.** Development Workflow step 6 defines publication as
part of completing the change: commit the `spectra/` folder, the `specs/` artifacts, `catalog.json`,
`docs/`, and `README.md`, then land them on `main` — at which point the catalog and package are live
immediately at their `raw.githubusercontent.com` links. Principle V's sync obligation is only discharged
once that has happened.

**Do not start this phase until every check in Phase 8 passes.** Publication is effectively immediate and
public: the raw catalog URL is what every consumer's `specify extension add spectra` resolves against, so
a broken commit on `main` is a broken install for everyone.

- [ ] T064 Land the change on `main` and confirm it is live. Stage the full Principle V set — `spectra/` (including the new `spectra/commands/review-pr.md`, `spectra/extension.yml`, `spectra/CHANGELOG.md`, `spectra/README.md`), `specs/008-review-pr/`, `agents-list.json`, `AGENTS_LIST.md`, `README.md`, `catalog.json`, `docs/index.html`, and `docs/packages/spectra.zip` — then open a pull request from `008-review-pr` (the `speckit.spectra.create-pr` command does this, and the `after_implement` hook offers it) and merge it. Per the Version Control & Branching Strategy, do **not** commit directly to `main`; the change reaches `main` by merging this spec's branch. After the merge, verify publication is live by fetching `https://raw.githubusercontent.com/xavient/spectra/main/catalog.json` and confirming it reports version `1.4.0` with 5 commands, and that `https://raw.githubusercontent.com/xavient/spectra/main/docs/packages/spectra.zip` downloads and contains `spectra/commands/review-pr.md`.

**Checkpoint**: `spectra agent-list` run from any project now shows the Review PR agent, because the CLI reads the published roster at run time — no CLI release was needed (Principle VI).

---

## Dependencies & Execution Order

### Phase dependencies

- **Phase 1 Setup** — no dependencies.
- **Phase 2 Foundational** — needs Phase 1. **Blocks every user story.**
- **Phase 3 US1** — needs Phase 2. Ships alone as the MVP.
- **Phase 4 US2** — needs Phase 2. T036 extends the section written in T007.
- **Phase 5 US3** — needs Phase 2, specifically T010's discovery chain (tier 3 is this story's trigger).
- **Phase 6 US4** — needs Phase 2 **and T028**, because prior-findings readback parses the machine anchor that T028 defines. This is the one genuine cross-story dependency.
- **Phase 7 Publishing** — needs the command file to exist and be final in content. Mandatory, not optional.
- **Phase 8 Validation** — needs Phase 7. Story-specific validation tasks additionally need their story.
- **Phase 9 Publish** — needs **all** of Phase 8 green. Required by the constitution; publication is immediate and public.

### User story dependencies

| Story | Depends on | Independently deliverable? |
|---|---|---|
| US1 (P1) | Phase 2 only | **Yes** — the MVP |
| US2 (P2) | Phase 2 only | Yes |
| US3 (P3) | Phase 2 (T010) | Yes |
| US4 (P4) | Phase 2 **+ T028** (US1) | No — needs US1's published body format |

### Within each phase

Every task in Phases 1 through 6 edits `spectra/commands/review-pr.md`, so within those phases tasks are
**strictly sequential**. Order them as listed.

### Parallel opportunities

Genuinely limited, and confined to Phase 7:

- **T042, T043, T044, T045** — four different files (`agents-list.json`, `AGENTS_LIST.md`,
  `docs/index.html`, `spectra/CHANGELOG.md`), no interdependencies. Safe to run together.
- **T041 must precede T047** (the generator asserts roster/manifest agreement) **and T048** (the zip
  packages the manifest).
- **T046 must match T041** exactly, so sequence rather than parallelize them.
- Phases 1–6: **no parallelism available** — single file.
- Phase 8: `T049` can run before the live-PR scenarios; the scenario tasks share a single test PR and a
  single `gh` session, so run them sequentially to keep results attributable.

---

## Parallel Example: Phase 7

```bash
# These four touch four different files — safe together, after T041:
Task: "Add the roster entry to agents-list.json"                      # T042
Task: "Write the prose block in AGENTS_LIST.md"                       # T043
Task: "Add the command card to docs/index.html"                       # T044
Task: "Add the 1.4.0 entry to spectra/CHANGELOG.md"                   # T045

# Then, strictly in order:
Task: "Update the spectra entry in catalog.json"                      # T046
Task: "python3 tools/generate_agent_docs.py"                          # T047
Task: "python3 tools/build_package.py"                                # T048
```

---

## Implementation Strategy

### MVP first (US1 only)

1. Phase 1 Setup — T001–T004
2. Phase 2 Foundational — T005–T015 (**blocks everything**)
3. Phase 3 US1 — T016–T034
4. **Stop and validate**: quickstart Scenarios 1, 2, and 6, plus the determinism check
5. Phase 7 Publishing + Phase 8 Validation + Phase 9 Publish → live

This is a complete, useful agent. Stories 2 through 4 are genuine improvements but nothing in US1
depends on them.

### Incremental delivery

1. Setup + Foundational → machinery in place
2. **+ US1 → validate → shippable MVP**
3. + US2 → terminal-native discovery
4. + US3 → useful on non-spec-driven repositories
5. + US4 → cheap re-reviews
6. Publishing surface + full validation + Phase 9 → live at the raw catalog URLs

Phase 7 must run in the same change as whatever set of stories you ship. It is not deferrable to a
follow-up commit — Principle V requires it in the same change, and CI rejects the intermediate state.

### Parallel team strategy

**Not applicable to Phases 1–6.** One Markdown file means one author; a second person on the same file
produces conflicts on every task. If you have two people, the effective split is:

- Person A: the command file, Phases 1–6
- Person B: Phase 7's four independent publishing files (T042–T045) and drafting the quickstart test
  fixtures — the PRs needed for Scenarios 1, 4, and 7

---

## Notes

- **The two load-bearing formats.** T028's machine anchor and disclosure line are parsed by T040. Change
  either casually and re-review breaks silently, with no test to catch it. The warning belongs in the
  command file itself, which is why T028 includes writing it there.
- **No-publish is a success path.** Four of the nine exit paths in
  [contracts/command-interface.md](./contracts/command-interface.md) deliberately publish nothing. Do not
  treat them as errors during validation.
- **The hard stop and the degradation are different behaviours** (T005 versus T032) and must not be
  collapsed into one. `create-pr` degrades on missing `gh`; `review-pr` stops. The justification is in
  the interface contract.
- **`[P]` only where files genuinely differ.** Marking same-file tasks parallel would guarantee conflicts.
- Commit after each task or logical group; stop at any checkpoint to validate.
- The extension version bump is catalog-channel only. Never touch root `VERSION`, never cut a tag
  (Principle VI).

## Task Summary

| Phase | Tasks | Count | Story |
|---|---|---|---|
| 1 Setup | T001–T004 | 4 | — |
| 2 Foundational | T005–T015 | 11 | — |
| 3 User Story 1 | T016–T035 | 20 | US1 (P1) 🎯 |
| 4 User Story 2 | T036–T037 | 2 | US2 (P2) |
| 5 User Story 3 | T038 | 1 | US3 (P3) |
| 6 User Story 4 | T039–T040 | 2 | US4 (P4) |
| 7 Publishing Surface | T041–T048 | 8 | — |
| 8 Validation | T049–T063 | 15 | mixed |
| 9 Publish | T064 | 1 | — |
| **Total** | | **64** | |

**Requirement coverage**: 42 of the 43 requirement lines (FR-001…FR-042 plus FR-006a) are implemented by
tasks above. The single exception is **FR-037** (line-anchored inline comments), deliberately deferred —
the spec's own constraints state the single-body form ships first, and research R-007 records why. Every
`MUST` is covered; FR-037 is a `SHOULD`.

The distribution is deliberately lopsided. US1 carries 20 tasks because the spec defines it as delivering
the entire value of the agent, while US3 needs one task because it is a documented degradation of
machinery Phase 2 already built.
