# Feature Specification: A Templated, Issue-Linked `create-pr`

**Feature Branch**: `014-create-pr-template`

**Created**: 2026-08-21

**Status**: Implemented

**Input**: User description: "For `create-pr` to receive an optional argument: a linked issue (agents should ask for it,
but it's optional — if no issue URL is supplied, ignore it). The flow should look at the current working tree and create a
PR to merge into the branch it is off from. If the agent detects uncommitted and un-pushed code, notify the user and ask
'confirm and push to remote?'. The PR should follow a template, customizable like `adr` and `brd`. Once the agent has
everything, ask for final confirmation with a summary — 'now I have everything to build the PR, and it will be linked to
&lt;issue&gt;' — then create the PR and report back."

## Current State (verified)

`spectra/commands/create-pr.md` runs ten steps: offer → hard `gh` gate → GitHub-remote check → `gh repo view` →
source-branch validation → duplicate-PR check → base derivation → commit/push readiness → `gh pr create` → report.

| | Today | Wanted |
|---|---|---|
| Linked issue | no argument, never asked | optional `--issue`, asked once, silently skipped when declined |
| Base branch | promotion flow from constitution + `.specify/extensions/git/git-config.yml`, else `defaultBranchRef` | documented flow when documented; otherwise proposed and **confirmed at the final gate** |
| Dirty working tree | surfaced with a warning; line 218: *"do not commit on their behalf"* | offer to commit **and** push, on one confirmation |
| PR body | composed ad hoc from `specs/<dir>/spec.md` — no template | a registered, overridable `pr-template` (Principle VIII) |
| Confirmation | per-action (base in some paths, push) | one consolidated pre-flight summary before creating |
| Branch scope | refuses any branch not matching a `specs/` directory | works from any branch; spec branches merely have richer sources |

## Clarifications

- Q: Base precedence — documented flow, or the branch actually forked from?
  → A: **Documented wins when documented.** Read the constitution (and the `git` extension config); if a promotion flow
  is there, follow it. If nothing is documented, do not infer silently — propose a base and ask at the final gate
  ("This PR will be created to merge into `main`, is that correct?"), letting the user redirect it conversationally
  ("no, change it to dev").
- Q: Should the command commit uncommitted work?
  → A: Yes. Ask *"there are uncommitted changes, should I proceed with committing and pushing first?"* and on a yes
  behave exactly as a normal "commit and push" request. This reverses today's explicit refusal to commit.
- Q: Keep the Checklist section in the template?
  → A: No. Remove it. An agent cannot honestly tick "I have self-reviewed the full diff".
- Q: Restrict to spec branches?
  → A: No. A bug fix or chore branch must be able to open a PR. Only detached HEAD and "already on the base branch"
  remain refusals.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A PR that follows the project's template (Priority: P1)

A developer finishes work and runs the command. The PR body arrives structured — Summary, Related Issues, Type of Change,
Changes, How to Test, Evidence, Breaking Changes, Notes for Reviewers — filled from real evidence rather than a
paragraph of spec prose. A team that wants different sections drops
`.specify/templates/overrides/pr-template.md` into the repo, and every later PR follows theirs.

**Why this priority**: It is the substance of the request and the part reviewers see on every PR.

**Independent Test**: run the command on a branch with commits; confirm the PR body carries the template's sections in
order; add an override with an extra section and confirm the next PR follows it.

**Acceptance Scenarios**:

1. **Given** no override, **When** the PR is composed, **Then** it follows the shipped `pr-template.md` and the run
   reports which template path it used.
2. **Given** `.specify/templates/overrides/pr-template.md`, **When** the PR is composed, **Then** the override is used —
   resolved ahead of the extension copy — and named in the report.
3. **Given** a resolved template that drops or adds sections, **When** the PR is composed, **Then** its structure is
   followed as authored and any omission is noted once, never reinstated.
4. **Given** any template, **When** the body is written, **Then** no guidance comment or `[PLACEHOLDER]` token survives.
5. **Given** the **Changes** section, **When** it is filled, **Then** it reflects the actual diff
   (`git diff --name-status <base>...HEAD`), not a restatement of the spec.

---

### User Story 2 - An optional linked issue that actually links (Priority: P1)

The developer passes `--issue 42` (or a full URL), or is asked once and answers — or declines, and the PR is opened
without any issue section content. When the issue is linked, the body uses a form that *works for the base branch it is
targeting*.

**Why this priority**: Equal to Story 1 — it is the other half of the request, and the naive implementation silently
does nothing (see the closing-keyword finding below).

**Independent Test**: open a PR to the default branch with `--issue N` and confirm a closing keyword; open one to a
non-default branch and confirm a plain reference plus an explicit note that auto-close will not happen.

**Acceptance Scenarios**:

1. **Given** `--issue <number-or-URL>`, **When** the command runs, **Then** it does not ask again.
2. **Given** no `--issue`, **When** the command gathers, **Then** it asks once; a declined or empty answer proceeds with
   no issue link and no further prompting.
3. **Given** an issue reference that `gh issue view` cannot resolve, **When** validated, **Then** the command says so and
   continues **without** the link rather than writing a broken reference.
4. **Given** base **is** the repository default branch, **When** the body is composed, **Then** the issue appears with a
   closing keyword (`Closes #42`).
5. **Given** base is **not** the default branch, **When** the body is composed, **Then** the issue appears as a plain
   reference and the report states that GitHub will not auto-close it on this merge, and why.
6. **Given** no issue, **When** the final summary is shown, **Then** the issue line is blank/absent rather than
   fabricated.

---

### User Story 3 - Uncommitted work is not silently left behind (Priority: P1)

The developer has edits they forgot to commit. Instead of a warning that the PR excludes them, the command asks whether
to commit and push first, and on yes does exactly that before opening the PR.

**Why this priority**: It is the difference between a correct PR and one missing the work it was opened for.

**Independent Test**: leave a modified file uncommitted, run the command, answer yes, and confirm the commit exists on
the remote and the PR contains it.

**Acceptance Scenarios**:

1. **Given** a dirty working tree, **When** detected, **Then** the command lists the affected files and asks *"there are
   uncommitted changes, should I proceed with committing and pushing first?"*.
2. **Given** a yes, **When** it proceeds, **Then** it stages the listed files, commits with a message describing the
   work, pushes, and reports what it did.
3. **Given** a no, **When** it proceeds, **Then** it opens the PR from what is already committed and states plainly that
   the uncommitted changes are excluded.
4. **Given** files that look like credentials (`.env`, `*.pem`, `id_rsa`, `credentials*`), **When** staging is proposed,
   **Then** they are called out before anything is staged.
5. **Given** any commit it makes, **When** hooks exist, **Then** they run — `--no-verify` is never used.
6. **Given** unpushed commits and a clean tree, **When** detected, **Then** it asks to push only, as today.

---

### User Story 4 - One final gate, and the base is settled there (Priority: P2)

Before anything is created, the command summarizes: source → base, the issue (or nothing), draft or ready, and the
template it resolved. The user confirms once — or redirects the base in the same breath.

**Why this priority**: It consolidates confirmations that are scattered today, and it is where an undocumented base gets
settled.

**Independent Test**: run in a repository with no documented promotion flow and confirm the summary asks whether the
proposed base is correct; answer "no, use dev" and confirm the PR targets `dev`.

**Acceptance Scenarios**:

1. **Given** everything gathered, **When** the command is ready, **Then** it shows one summary and asks a single
   yes/no — and creates nothing before an affirmative.
2. **Given** a documented promotion flow, **When** the base is shown, **Then** the summary cites the rule it came from.
3. **Given** no documented flow, **When** the base is shown, **Then** the summary asks whether the proposed base is
   correct and accepts a correction without restarting the flow.
4. **Given** a corrected base, **When** it is applied, **Then** the target's existence on the remote is re-checked and
   the closing-keyword decision (Story 2) is recomputed for the new base.
5. **Given** a no, **When** the user declines, **Then** nothing is created, and what was already done (a push, a commit)
   is stated plainly.

---

### User Story 5 - Any branch, not just spec branches (Priority: P2)

A developer on `fix/login-timeout` opens a PR with the same command.

**Why this priority**: It removes a refusal rather than adding capability, but without it the feature is unusable for
bugs and chores.

**Independent Test**: on a branch with no matching `specs/` directory, run the command and confirm it proceeds.

**Acceptance Scenarios**:

1. **Given** a branch with no matching spec directory, **When** the command runs, **Then** it proceeds and composes the
   body from commits and the diff.
2. **Given** a spec branch, **When** the command runs, **Then** it additionally uses `spec.md`, `plan.md`, and
   `tasks.md` for Summary and How to Test.
3. **Given** detached HEAD, **When** detected, **Then** the command refuses — there is no branch to propose.
4. **Given** the current branch is the resolved base, **When** detected, **Then** the command refuses; a branch cannot
   target itself.

---

### Edge Cases

- **Closing keyword on a non-default base** — see FR-012. GitHub ignores the keyword entirely there, so the command must
  not write one.
- **Cross-repository issue** — a URL pointing at another repository is referenced by full URL, never with a closing
  keyword, and the user is told why.
- **A documented flow and the branch's actual fork point disagree** — the documented flow is used; the divergence is
  mentioned once in the summary so the user can redirect.
- **No documented flow and no determinable fork point** (fresh clone, no reflog, `dev` and `main` at the same commit) —
  propose the default branch and say the proposal is a guess.
- **Nothing to commit and nothing to push** — skip Story 3 entirely; no prompt.
- **The corrected base does not exist on the remote** — surface and stop; never create it.
- **Empty diff against the base** — say so and stop rather than opening an empty PR.
- **An existing open PR** — return its URL, as today; no duplicate.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The command MUST accept an optional `--issue <url-or-number>` argument.
- **FR-002**: When no issue is supplied, it MUST ask exactly once, and MUST proceed with no issue content when the answer
  is empty or declined.
- **FR-003**: It MUST validate the reference with `gh issue view` and, when it does not resolve, say so and continue
  without the link.
- **FR-004**: The PR body's structure MUST come from a `pr-template` resolved through Spec Kit's stack — project
  override → presets → extension → core → the command's inline skeleton — per Principle VIII.
- **FR-005**: `spectra/templates/pr-template.md` MUST ship and MUST be registered in `provides.templates`.
- **FR-006**: The template MUST contain Summary, Related Issues, Type of Change, Changes, How to Test, Screenshots /
  Evidence, Breaking Changes, and Notes for Reviewers — and MUST NOT contain a self-certification checklist.
- **FR-007**: The command MUST report the resolved template path.
- **FR-008**: It MUST follow the resolved template as authored, noting omissions rather than reinstating sections.
- **FR-009**: The **Changes** section MUST be derived from the real diff against the base.
- **FR-010**: A spec branch MUST additionally draw on `spec.md`, `plan.md`, and `tasks.md`; a non-spec branch MUST fall
  back to commit messages and the diff.
- **FR-011**: Base derivation MUST prefer a documented promotion flow (constitution, then the `git` extension config),
  and MUST cite the rule it used.
- **FR-012**: When no flow is documented, the command MUST propose a base and confirm it at the final gate, accepting a
  correction without restarting; it MUST NOT treat inference as settled.
- **FR-013**: An issue MUST be written with a closing keyword **only** when the base is the repository's default branch.
  Otherwise it MUST be a plain reference, and the command MUST state that GitHub will not link or auto-close it on this
  merge.
- **FR-014**: On a dirty working tree the command MUST list the files and ask whether to commit and push first.
- **FR-015**: On a yes it MUST stage those files, commit with a descriptive message, and push — with hooks intact
  (`--no-verify` MUST NOT be used).
- **FR-016**: It MUST call out files that look like credentials before staging anything.
- **FR-017**: On a no it MUST open the PR from committed work and state that the uncommitted changes are excluded.
- **FR-018**: Before creating the PR it MUST show one summary — source → base and its origin, the issue or nothing,
  draft/ready, and the template path — and MUST create nothing without an affirmative answer.
- **FR-019**: It MUST work from any branch, refusing only detached HEAD and a branch equal to the resolved base.
- **FR-020**: Every existing guarantee MUST survive: the hard `gh` gate, GitHub-only scope, the duplicate-PR check,
  `--head` always passed explicitly, `--body-file -` for the body, and post-gate degradation that states exactly what was
  mutated.
- **FR-021**: The command's one rule MUST be restated to permit a commit with explicit consent, while continuing to
  forbid touching the spec, the constitution, and unrelated source.
- **FR-022**: The extension version MUST bump to `1.8.0` with catalog, changelog, and zip in sync.
- **FR-023**: The constitution MUST make clear that Principle VIII covers documents a command **emits** (a PR body), not
  only files it writes to disk.
- **FR-024**: The test suite MUST cover `pr-template` in the existing template guard and MUST assert the new
  behaviors that are checkable as text: the `--issue` argument, the default-branch-only closing keyword, the
  confirm-before-commit rail, and the final summary gate.

### Key Entities

- **Linked issue** — a number or URL, optional, validated, rendered as a closing keyword or a plain reference depending
  on the base.
- **Base branch** — documented flow, else a proposal confirmed at the final gate.
- **PR template** — `pr-template`, resolved through the stack, overridable at
  `.specify/templates/overrides/pr-template.md`.
- **Final gate** — the single consolidated confirmation preceding creation.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A PR opened by the command carries every section of the resolved template, filled, with no leftover
  guidance comments or placeholders.
- **SC-002**: Overriding `pr-template.md` changes the shape of the next PR with no other configuration.
- **SC-003**: An issue passed on a default-branch PR closes on merge; on a non-default-branch PR the command warns
  instead of writing a keyword that GitHub ignores.
- **SC-004**: Uncommitted work either reaches the PR (on a yes) or is explicitly reported as excluded (on a no) — never
  silently dropped.
- **SC-005**: Nothing is created without exactly one affirmative answer to the final summary.
- **SC-006**: The command runs to completion from a non-spec branch.
- **SC-007**: `python -m unittest discover -s tests`, `tools/generate_agent_docs.py --check`, and a
  `tools/build_package.py` rebuild all pass.

## Assumptions

- Command files are prompts; the enforceable surface is their text plus the CI guard on it. Behavior needs the manual
  pass in `test/README.md`.
- `gh` remains the only route to GitHub, and the command holds no credentials of its own.
- Committing on the user's behalf is scoped to the files it listed. It is not a general-purpose commit tool and does not
  amend, rebase, or force-push.
- GitHub's closing-keyword behavior is as documented today: keywords are interpreted only when the PR targets the
  default branch. If that changes, FR-013 is the requirement to revisit.
- Fork-point inference is best-effort. It is never presented as authoritative, which is why FR-012 requires
  confirmation rather than silent use.
