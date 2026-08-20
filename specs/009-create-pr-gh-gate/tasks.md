# Tasks: Create PR Gates on `gh`

**Input**: Design documents from `/specs/009-create-pr-gh-gate/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md),
[data-model.md](./data-model.md), [contracts/](./contracts/), [quickstart.md](./quickstart.md)

**Tests**: No automated test tasks. The deliverable is a Markdown instruction file with no unit-test
surface, and the spec does not request TDD. Validation is real and lives in Phase 6: the repository's own
enforcement scripts, which run here, plus the runtime scenarios in [quickstart.md](./quickstart.md), which
need a live GitHub repository and are marked as such.

**Organization**: Grouped by user story so each is independently deliverable and testable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel — different files, no dependency on incomplete work
- **[Story]**: `[US1]`…`[US3]`, on user-story phases only
- Every task names its exact file path

## Path Conventions

This feature ships instructions, not code. There is no `src/` or `tests/`. Real paths:

- **The behavioural deliverable**: `spectra/commands/create-pr.md` (one existing file, modified)
- **The publishing surface**: `spectra/extension.yml`, `spectra/CHANGELOG.md`, `spectra/README.md`,
  `AGENTS_LIST.md`, `catalog.json`, `docs/packages/spectra.zip`
- **Historical records annotated**: `specs/002-open-pr/`, `specs/008-review-pr/`
- **Tooling used, never modified**: `tools/generate_agent_docs.py`, `tools/build_package.py`

> ## ⚠️ Read this before parallelizing
>
> **Phases 1–4 are strictly sequential.** All three user stories are sections of a **single Markdown file**,
> `spectra/commands/create-pr.md`. Two people editing it simultaneously conflict on every task, so `[P]`
> appears only in Phase 5 (publishing, different files) and Phase 5b (spec annotations, different files).
>
> The stories remain independently *testable*: US1 alone delivers the feature — the gate — and can ship
> without US2 or US3. They are not independently *assignable*.
>
> **One ordering rule is non-negotiable**: the zip rebuild (T027) must be the **last** edit to anything
> under `spectra/`. CI diffs the packaged tree against the folder, so any later edit invalidates it.

---

## Phase 1: Setup and baseline

**Purpose**: Capture the pre-change state so Phase 6 can assert what moved.

- [X] T001 Record the baseline from the repository root: `python3 tools/generate_agent_docs.py --check` (expect a pass — the roster is unchanged by this feature, so this must also pass unchanged at the end), `python3 -m unittest discover -s tests` (expect a pass), and `git diff --stat docs/packages/spectra.zip` (expect empty). Note the current extension version — `1.4.0` in both `spectra/extension.yml` and `catalog.json` — so the Phase 5 bump is verifiable as a change of exactly that pair.
- [X] T002 Re-read `spectra/commands/create-pr.md` end to end against [contracts/command-interface.md](./contracts/command-interface.md) and mark the four sections this feature rewrites: **Step 2** (preconditions), **Step 2a** (manual fallback), **Step 5 item 3** (default-branch resolution), **Step 7** (open the PR). Everything else in the file is preserved verbatim per FR-013 — the diff should be readable as "four sections and one rule".

**Checkpoint**: Baseline recorded; the edit surface is bounded and known.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The two statements every user story depends on — the `gh`-exclusivity rule and the gate's
position in the flow.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. Both tasks edit the same file
and are strictly sequential.

- [X] T003 Extend the **"The one rule that governs everything"** section of `spectra/commands/create-pr.md` with the `gh`-exclusivity rule (FR-008): all pull-request interaction goes through `gh`; `curl`, direct REST calls, and any other route MUST NOT be used. Keep the existing mutation rule intact — the two rules now sit together, mirroring `review-pr.md`'s framing.
- [X] T004 Restructure the head of the flow in `spectra/commands/create-pr.md` so the ordering in [contracts/command-interface.md](./contracts/command-interface.md) §"Ordered flow" holds: Step 1 offer → **Step 2 `gh` pre-flight** → Step 3 remote scope → Step 4 repository facts → Step 5 source-branch validation. State explicitly that the pre-flight runs **before** any project read, any `git` command, and any other `gh` call (FR-001), and that it runs **after** the offer, never before it (FR-005).

**Checkpoint**: The file declares `gh` as the only route and puts the gate in front of everything else.

---

## Phase 3: User Story 1 — An unusable `gh` stops the command with the remedy that fits (Priority: P1) 🎯 MVP

**Goal**: `gh` missing or unauthenticated ends the run immediately, with two distinguishable messages, one
remedy each, and zero mutations.

**Independent Test**: quickstart [S2](./quickstart.md#s2--gh-is-not-installed-hard-stop-install-remedy) and
[S3](./quickstart.md#s3--gh-is-installed-but-not-authenticated-a-different-message) — run with `gh` off
`PATH`, then with an empty `GH_CONFIG_DIR`.

- [X] T005 [US1] Replace the body of **Step 2** in `spectra/commands/create-pr.md` with the two-probe gate from [contracts/gh-operations.md](./contracts/gh-operations.md) OP-1: `command -v gh`, then `gh auth status --hostname github.com`. State that a non-zero exit from either is a **hard stop, not a degradation** — the same phrasing `review-pr.md` uses, so the two commands read alike (FR-001).
- [X] T006 [US1] Add the explicit prohibition on `--json` in the auth probe to `spectra/commands/create-pr.md`, with its reason quoted from `gh auth status --help`: with `--json` the command "will always exit with zero regardless of any authentication issues" (research R-003). Without this note a future edit re-introduces a gate that cannot fail.
- [X] T007 [US1] Write the **two distinct failure messages** into `spectra/commands/create-pr.md` per [data-model.md](./data-model.md) `GateFailure`: `gh_missing` → the GitHub CLI is not installed, point at <https://cli.github.com>; `gh_unauthenticated` → run `gh auth login`. Require that the message names **which** check failed, because the remedies differ (FR-002, SC-002).
- [X] T008 [US1] Add the no-`gh`-command rule for the `gh_missing` case to `spectra/commands/create-pr.md` (FR-003, data-model V-1): when `gh` is absent the stop message MUST NOT print any `gh …` line; the only alternative route it may name is the GitHub web interface for `<owner>/<repo>` — resolvable from the remote URL without `gh`.
- [X] T009 [US1] State the zero-mutation guarantee in `spectra/commands/create-pr.md` (FR-004, data-model V-3): on a gate failure nothing is pushed, no branch is created, no pull request is opened, and no file is written — and the command says so rather than leaving it implied.
- [X] T010 [US1] Make the offer/gate boundary explicit in **Step 1** of `spectra/commands/create-pr.md` (FR-005): the offer is never gated, and a declined offer ends the run silently with no gate check and no gate error. Note why — a user who declines never needed `gh`.
- [X] T011 [US1] Delete the old degradation language from `spectra/commands/create-pr.md`: the heading "Check preconditions (and degrade gracefully)", the three "If absent, degrade" clauses, and any remaining instruction to derive Steps 3–5 in order to print a fallback. Verify by grepping the file for `degrade` — the only surviving hits must be in the post-gate section added in Phase 4.

**Checkpoint**: US1 is complete and shippable on its own. The two `gh` failures stop the run with the right
remedy and no mutations.

---

## Phase 4: User Story 2 — A failure after the gate hands over a runnable manual path (Priority: P2)

**Goal**: A refused push or a refused creation degrades — naming the cause, the derived base, the manual
commands, and whether the branch reached the remote.

**Independent Test**: quickstart [S5](./quickstart.md#s5--a-refusal-after-the-gate-degrade-and-say-what-was-mutated)
against a protected base branch or a token without push permission.

- [X] T012 [US2] Rewrite **Step 2a** of `spectra/commands/create-pr.md` from "Manual fallback (when a precondition fails)" into **post-gate degradation**: it now applies only to failures *after* the gate passed, and the section says so in its first line. Cross-reference the gate so the two are never conflated — this is the distinction [contracts/command-interface.md](./contracts/command-interface.md) §"Degradation policy" fixes (FR-010).
- [X] T013 [US2] Add the **mutation-state statement** to that section of `spectra/commands/create-pr.md` per [data-model.md](./data-model.md) `MutationState` (FR-011, V-6): report `none` ("nothing reached the remote") or `branch_pushed` ("the branch is on the remote; no pull request exists"), **always**, including when nothing was mutated.
- [X] T014 [US2] Specify the manual hand-over content in `spectra/commands/create-pr.md` (FR-010, V-5): the `git push -u origin <source-branch>` and `gh pr create --base <target-branch> --head <source-branch>` lines, with the **derived** target branch substituted and the body handed over as a saved file rather than `--body-file -` (a pasted command must not sit waiting on standard input), plus the instruction to surface `gh`'s or `git`'s own error verbatim rather than paraphrasing it.
- [X] T015 [US2] Add the failure path to **Step 7** of `spectra/commands/create-pr.md`: if `gh pr create` fails, do not report success, route to the post-gate section, and state that the branch is already on the remote. Include the exit-code reading from [contracts/gh-operations.md](./contracts/gh-operations.md) §"Post-gate error interpretation" — exit 4 is authentication (`gh auth login`), not permission (V-7); exit 2 is a cancellation.
- [X] T016 [US2] Add the push-failure path to **Step 6** of `spectra/commands/create-pr.md`: a refused `git push` routes to the same section with the mutation state reported as `none`, and the run is not presented as partially successful.

**Checkpoint**: No failure after the gate can leave the remote in a state the user was not told about.

---

## Phase 5: User Story 3 — A non-GitHub remote stops honestly (Priority: P3)

**Goal**: An absent or non-GitHub remote is a scope stop with no `gh` fallback; a fork or several remotes is
a question, answered from structured data.

**Independent Test**: quickstart [S4](./quickstart.md#s4--the-remote-is-not-github-or-absent-a-scope-statement)
and [S7](./quickstart.md#s7--fork-or-several-remotes-ask-never-guess).

- [X] T017 [US3] Rewrite the remote check as **Step 3** of `spectra/commands/create-pr.md`: keep the existing HTTPS/SSH parsing and the `github.com`-only rule, but make the outcome a **hard stop with a scope statement** naming the host found (FR-006). Add the explicit prohibition: no `gh` fallback command is printed, because none would help against a non-GitHub remote (V-4, SC-003).
- [X] T018 [US3] Name GitHub Enterprise as out of scope in that section of `spectra/commands/create-pr.md` (research R-004): a host other than `github.com` stops as non-GitHub rather than being half-attempted, even though `gh` can technically target other hosts.
- [X] T019 [US3] Replace the "if `origin` looks like a fork" heuristic in `spectra/commands/create-pr.md` with **Step 4**, the single structured query from [contracts/gh-operations.md](./contracts/gh-operations.md) OP-2: `gh repo view --json nameWithOwner,isFork,parent,defaultBranchRef,viewerPermission`. State that fork status comes from `isFork`, never from the URL shape (FR-007, FR-009).
- [X] T020 [US3] Specify the fork/multi-remote behaviour in `spectra/commands/create-pr.md`: **ask** which remote and base to use, and record why guessing is unsafe — `gh pr list --head` rejects `owner:branch` while `gh pr create --head` accepts it, so an inferred fork flow dedups against one head and creates against another (research R-008, FR-007).
- [X] T021 [US3] Update the default-branch resolution in the target-derivation step of `spectra/commands/create-pr.md` to consume `defaultBranchRef` from T019's query, and **delete the `git symbolic-ref refs/remotes/origin/HEAD` fallback** — past the gate it covers a state that can no longer occur (research R-007). Add the `viewerPermission` note: `null` means unknown, so proceed and let the post-gate path handle a refusal rather than pre-emptively refusing.

**Checkpoint**: All three stories are in the file. Every remote shape either proceeds, asks, or stops with a
scope statement.

---

## Phase 5a: Command-file hardening and consistency

**Purpose**: The cross-cutting requirements that are not tied to one story, plus a read-through so the file
reads as one document rather than a patched one.

- [X] T022 Change the PR creation call in **Step 7** of `spectra/commands/create-pr.md` to pass the body on standard input per [contracts/gh-operations.md](./contracts/gh-operations.md) OP-5: `printf '%s' "$BODY" | gh pr create --base … --head … --title … --body-file -`, with `--draft` added only on request. Record why (FR-012): spec-derived bodies carry backticks, code fences, quotes, and blank lines that shell escaping mangles.
- [X] T023 Add the `--head` rationale to `spectra/commands/create-pr.md` from OP-5: `--head` is always passed explicitly, because `gh pr create --help` documents that without it a prompt "will ask where to push the branch and offer an option to fork the base repository" — an unconfirmed mutation the governing rule forbids.
- [X] T024 Add an **Edge cases** table to `spectra/commands/create-pr.md`, matching the shape `review-pr.md` uses, covering: `gh` missing · `gh` unauthenticated · expired token · offer declined · no remote · non-GitHub remote · GitHub Enterprise · fork or several remotes · dirty tree · unpushed commits · existing open PR · derived target missing on the remote · promotion-flow conflict · push refused · creation refused · non-spec branch or detached HEAD. Each row names the outcome from [data-model.md](./data-model.md) §"Run outcome".
- [X] T025 Read `spectra/commands/create-pr.md` end to end and reconcile it with FR-013: confirm the offer-first flow, both confirmation gates, one-branch-per-spec refusal, existing-PR detection, target derivation with conflict surfacing, `--draft`/`--base`, and the reported URL are all still present and unweakened; confirm the "Opening the PR later (on demand)" section still reads correctly against the new step numbers; confirm every internal step reference points at the right step after the renumbering.

**Checkpoint**: The command file is complete, internally consistent, and contains no reference to the
superseded behaviour.

---

## Phase 5b: Publication (Constitution Principle V)

**Purpose**: Ship the change across every artifact that describes it. Different files, so genuinely
parallelizable — **except T027, which must run last**.

- [X] T026 [P] Update `spectra/extension.yml`: rewrite the `requires.tools` comment so it records that **both** GitHub commands hard-gate on `gh` (keeping `gh` and `git` at `required: false`, and keeping the reason — `adr`, `brd`, and `domain-analyzer` never touch GitHub), and bump `extension.version` from `1.4.0` to **`1.5.0`** (FR-014, research R-012). Leave `provides.commands` untouched — no command is added.
- [X] T027 [P] Add the `[1.5.0]` entry to `spectra/CHANGELOG.md` under **### Changed**: `create-pr` now hard-stops when `gh` is missing or unauthenticated instead of degrading, with the two remedies named; the manual fallback now applies to post-gate failures and reports whether the branch was pushed; the body is passed on stdin; fork detection is structured. State plainly that this **reverses** the difference recorded in the 1.4.0 entry, and leave that entry unedited — it was true when written. Explain the MINOR: a shipped command changed, no argument or output contract did.
- [X] T028 [P] Update `spectra/README.md`: in the `create-pr` section, replace item 1's "degrades gracefully with a manual fallback" with the hard gate and its two remedies, and rewrite the closing "GitHub only" paragraph so the fallback is described as post-gate. In the `review-pr` section, replace "Unlike `create-pr` this does **not** degrade" with a statement that both commands gate identically and that what differs is only what each hands over after the gate. Do not touch the generated Commands table region (research R-010).
- [X] T029 [P] Update `AGENTS_LIST.md`: rewrite the hand-authored `<!-- SPECTRA:AGENT id=create-pr -->` prose so the `gh` behaviour is the gate (dropping "degrading gracefully with a manual fallback when `gh`, the remote, or the network is unavailable"), and rewrite the `<!-- SPECTRA:AGENT id=review-pr -->` paragraph that says "Unlike `create-pr`, this command **hard-stops** … instead of degrading". Keep both headings and anchors exactly as they are — `tools/generate_agent_docs.py --check` matches on canonical title and id.
- [X] T030 [P] Update `catalog.json`: set the `spectra` entry's `version` to `1.5.0` and refresh both `updated_at` fields to the release date. Leave `provides.commands` at **5**, the description unchanged, and the tags unchanged (CI asserts version and command-count agreement with `spectra/extension.yml`, and description agreement across the manifest, catalog, and zip).
- [X] T031 Rebuild the package **after every `spectra/` edit is final**: `python3 tools/build_package.py`, then verify with `unzip -q -o docs/packages/spectra.zip -d /tmp/unzipped && diff -r /tmp/unzipped/spectra spectra` (expect empty) and confirm the packaged manifest reports `1.5.0`. **This task is the last write in the phase** — CI's `catalog` job fails on any drift between the zip and the folder.

**Checkpoint**: Nothing shipped to users claims the superseded behaviour, and the catalog, manifest, and
package agree.

---

## Phase 5c: Annotate the superseded records

**Purpose**: A reader who lands on the old requirement must be pointed at the new one. One line each; the
earlier text is **not** rewritten, because those specs are history.

- [X] T032 [P] Annotate `specs/002-open-pr/spec.md`: a one-line superseded-by note on **FR-007** and on **SC-006**, each naming `specs/009-create-pr-gh-gate` and stating that the gate replaced the degradation.
- [X] T033 [P] Annotate `specs/002-open-pr/quickstart.md` scenario **S6** ("Graceful degradation") as superseded by this feature's S2–S4.
- [X] T034 [P] Annotate `specs/008-review-pr/contracts/command-interface.md` §"Degradation policy" — the paragraph justifying `create-pr` degrading where `review-pr` stops — with a superseded-by note; and `specs/008-review-pr/research.md` **R-009**, noting that `gh` stays extension-optional but the difference in handling is gone.
- [X] T035 [P] Annotate `brds/open-pr.md` **BR-07** and **G5** with a one-line pointer recording that the business rule was superseded at the spec level by `009-create-pr-gh-gate`. Do not restructure the BRD.

**Checkpoint**: Every document that asserted the old behaviour either states the new one or points at it.

---

## Phase 6: Verification

**Purpose**: Prove what changed, and be explicit about what could not be proven here.

Runs in the repository:

- [X] T036 Run `python3 tools/generate_agent_docs.py --check` and confirm it still passes: the roster is unchanged by this feature, so the shipped-agent set, the prose anchors, and the canonical titles must all still agree after T029's rewrite.
- [X] T037 Run `python3 -m unittest discover -s tests` and confirm a pass. Note that `tests/test_extension.py` reads the real manifest but asserts only a semver shape, so the version bump is expected to be test-neutral — a failure here means something else moved.
- [X] T038 Reproduce CI's `catalog` job locally: assert `spectra/extension.yml` and `catalog.json` both read `1.5.0`; assert the manifest command count still equals the catalog's `provides.commands` (5); assert the description matches across manifest, catalog, and the zip; assert `diff -r /tmp/unzipped/spectra spectra` is empty.
- [X] T039 Execute quickstart [S9](./quickstart.md#s9--documentation-consistency): `grep -rn "degrad" spectra/ AGENTS_LIST.md README.md | grep -v CHANGELOG` returns no hit describing `create-pr` as degrading and no hit claiming the two commands differ on the gate (SC-006).
- [X] T040 Read `spectra/commands/create-pr.md` against [contracts/gh-operations.md](./contracts/gh-operations.md) and confirm the closed set holds: every `gh` call in the file appears in OP-1…OP-5, nothing from the out-of-contract list appears, and there is no `curl` or REST call anywhere (FR-008).

Needs a live GitHub repository — **run before publishing, and do not report the feature as validated
without them**. T001–T040 were executed on 2026-08-19; T041–T044 remain open because they require a live
GitHub repository and a push to `main`, neither of which this session performed:

- [ ] T041 Execute quickstart **S2** and **S3** in a throwaway Spec Kit project with the working copy installed via `specify extension add --dev`: `gh` off `PATH`, then an empty `GH_CONFIG_DIR`. Confirm both stop before any target derivation, produce distinct messages, print no `gh` command in the missing-binary case, and mutate nothing (FR-001–FR-004, SC-001–SC-003).
- [ ] T042 Execute quickstart **S1** (happy path regression), **S4** (non-GitHub and absent remote), **S6** (body fidelity, via `gh pr create --dry-run`), and **S7** (fork or several remotes) (FR-006, FR-007, FR-012, FR-013, SC-005, SC-007).
- [ ] T043 Execute quickstart **S5** against a repository that refuses the outward action, confirming the degradation names the cause, the derived base, the runnable commands, and the mutation state (FR-010, FR-011, SC-004).
- [ ] T044 Land the change on `main`: stage the full Principle V set — `spectra/` (command, manifest, changelog, README), `catalog.json`, `AGENTS_LIST.md`, `docs/packages/spectra.zip`, `specs/009-create-pr-gh-gate/`, and the Phase 5c annotations — then open a pull request from `009-create-pr-gh-gate` using `speckit.spectra.create-pr` itself. Opening this feature's pull request **with the command it changes** is the last check: if the gate is wrong, the change cannot ship itself.

---

## Dependencies

```text
Phase 1 (T001–T002)  ── baseline, no edits
        ↓
Phase 2 (T003–T004)  ── BLOCKING: rule + gate position
        ↓
Phase 3 (T005–T011)  ── US1, sequential, same file        ← MVP ends here
        ↓
Phase 4 (T012–T016)  ── US2, sequential, same file
        ↓
Phase 5 (T017–T021)  ── US3, sequential, same file
        ↓
Phase 5a (T022–T025) ── hardening + consistency read-through
        ↓
Phase 5b (T026–T030 [P]) ── publishing, parallel across files
        ↓
Phase 5b (T031)      ── zip rebuild, MUST be last write under spectra/
        ↓
Phase 5c (T032–T035 [P]) ── supersession annotations, parallel
        ↓
Phase 6 (T036–T040)  ── repository checks
        ↓
Phase 6 (T041–T043)  ── live-repository scenarios
        ↓
Phase 6 (T044)       ── publish, using the command itself
```

**The one trap**: T031 after every `spectra/` write. A zip built before T028's README edit passes locally
and fails CI.

---

## Implementation strategy

**MVP**: Phases 1 → 2 → 3. That is the feature — the gate — and it is coherent on its own: `gh` failures
stop cleanly with the right remedy. US2 and US3 close the paths around it.

**Do not ship the MVP alone, though.** Phase 5b is not optional for a partial delivery either: the moment
`spectra/commands/create-pr.md` changes behaviour, the shipped documentation describing the old behaviour is
wrong, and Principle V forbids landing that drift.

**Suggested single-session order**: Phases 1–5a in one pass through the command file (the diff stays
readable), then 5b and 5c as mechanical sync, then Phase 6 as the gate on reporting completion.

---

## Requirement traceability

| Requirement | Tasks |
|---|---|
| FR-001 gate first, hard stop | T004, T005 |
| FR-002 two distinguishable remedies | T007 |
| FR-003 no `gh` command when `gh` is absent | T008 |
| FR-004 zero mutations on a failed gate | T009 |
| FR-005 the offer is not gated | T010 |
| FR-006 non-GitHub / absent remote stops | T017, T018 |
| FR-007 fork and multi-remote ask, from structured data | T019, T020 |
| FR-008 `gh` exclusively | T003, T040 |
| FR-009 one structured repository query | T019, T021 |
| FR-010 post-gate degradation | T012, T014, T015, T016 |
| FR-011 mutation state always stated | T013, T015, T016 |
| FR-012 body over stdin | T022 |
| FR-013 everything else unchanged | T002, T025 |
| FR-014 `gh` stays optional; comment records both gates | T026 |
| FR-015 publication set moves together | T026–T031 |
| SC-001 / SC-002 | T041 |
| SC-003 | T008, T017, T041 |
| SC-004 | T043 |
| SC-005 | T042 |
| SC-006 | T028, T029, T039 |
| SC-007 | T025, T042 |
