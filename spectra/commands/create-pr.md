---
description: "Open a correctly-targeted GitHub pull request for the current branch, optionally linked to an issue, with the body built from an overridable PR template and one final confirmation before anything is created."
---

# Open a Pull Request

You are closing the loop on a piece of work. Your job is to open a **correctly-targeted** pull request using
`gh`, with a body built from the project's **PR template**, optionally **linked to an issue**, with the user
in control at every outward step — and to return the PR link in chat.

`gh` is not optional. If it is missing or not authenticated, you **stop and say which** — you do not run
the flow anyway and hand back commands the user cannot execute. Once past that gate, a refusal from the
remote is different: there you degrade, hand over the exact manual commands, and say precisely what was
already mutated.

Work through the steps in order. Never skip the pre-flight gate, and never take an outward action —
committing, pushing, creating the PR — without explicit user confirmation.

## User Input

Optional arguments the user may pass:

$ARGUMENTS

Interpret them as follows (all optional — the command works with no arguments):

- **(no arguments)** — run the full default flow and open a **ready-for-review** PR.
- **`--draft`** — open the PR as a **draft** instead of ready-for-review.
- **`--base <branch>`** — use `<branch>` as the target. Still shown in the final summary (Step 11).
- **`--issue <url-or-number>`** — the issue this PR addresses, e.g. `--issue 42`,
  `--issue https://github.com/<owner>/<repo>/issues/42`. When supplied, do **not** ask for it again.

If the arguments contain anything you do not recognize, briefly note it and continue with the default
behavior rather than failing.

## The one rule that governs everything

Your allowed mutations are **only** the Git and remote actions required to open the PR: committing the
user's uncommitted work **when they ask you to** (Step 8), pushing the branch, and creating the PR. You MUST
NOT modify source code yourself, and you MUST NOT touch the spec, the plan, the tasks, or the constitution.
Every commit, every push, and the PR creation MUST be preceded by an explicit user go-ahead.

All pull request and issue interaction goes through `gh`. Do not use `curl`, direct REST calls, or any other
route. You hold **no credentials of your own**: every interaction with GitHub goes through the user's
existing `gh` authentication.

---

## Step 1 — Offer and await go-ahead

If you were triggered automatically after `implement` (via the `after_implement` hook), **offer** to
open a PR for the completed spec and then **stop and wait** for the user's response. Take no Git or
remote action until the user accepts.

- If the user **declines** (e.g. "no"), take no action: do not check anything, do not push, do not open
  a PR. Note that they can open the PR later at any time by invoking this command directly (see
  Step 13). Then stop.
- If the user **accepts**, or if the command was invoked directly on demand, continue to Step 2.

**The offer itself is never gated.** Do not check for `gh` before offering — a user who declines never
needed it, and an unsolicited tooling error after `implement` is noise they did not ask for.

---

## Step 2 — Pre-flight: `gh` must be installed and authenticated

**This is a hard stop, not a degradation.** Do this before anything else — before reading the
constitution or the branching config, before validating the branch, before any other `gh` or `git`
command:

```bash
command -v gh                            # installed?
gh auth status --hostname github.com     # authenticated on the host this version supports?
```

If either fails, **stop**. Say precisely which one failed, because the remedies are different and the
user needs to know which one applies:

- **`gh` not found** — the GitHub CLI is not installed. Point them at <https://cli.github.com> and stop.
- **`gh` present but not authenticated** — tell them to run `gh auth login` and stop. An expired or
  revoked token surfaces here too, and takes the same remedy.

Two rules for these messages:

- **When `gh` is absent, never print a `gh` command.** Telling someone without `gh` to run
  `gh pr create` is not a fallback. The only alternative route you may name is opening the PR through
  the GitHub web interface for `<owner>/<repo>`. You may read `git config --get remote.origin.url` to
  build that link — a single local read is not the analysis this gate exists to prevent.
- **Say that nothing was changed**, because nothing was: no push, no branch, no PR, no file written.

Do not derive a target branch, read the constitution, or analyze anything on the way to that message.
The value of this command is the pull request, and the pull request requires `gh` — a partial run wastes
the user's time when the fix is one command away.

> **Do not add `--json` to the auth check.** `gh auth status --help` states that with `--json` the
> command "will always exit with zero regardless of any authentication issues". That would turn a gate
> that can fail into a gate that cannot.

---

## Step 3 — The remote must exist and be on GitHub

Read the remote URL and confirm it points to **github.com**:

```bash
git config --get remote.origin.url
```

- HTTPS form: `https://github.com/<owner>/<repo>.git`
- SSH form: `git@github.com:<owner>/<repo>.git`

Extract `<owner>` and `<repo>`. ONLY treat the remote as GitHub if the host is actually `github.com`.

If there is **no remote**, or the host is **not** `github.com`, **stop** — this is a statement of scope,
not a tool failure. Name what you found (the host, or the absence of a remote) and say that this version
supports GitHub only. **Print no `gh` fallback command**: there is nothing `gh` can do with a
non-GitHub remote, so a command line here would only mislead.

**GitHub Enterprise is out of scope in this version.** A remote on any host other than `github.com`
stops here rather than being half-attempted.

---

## Step 4 — Read the repository's facts in one call

One structured query answers everything you need about the repository:

```bash
gh repo view --json nameWithOwner,isFork,parent,defaultBranchRef,viewerPermission
```

- **`defaultBranchRef`** — needed twice: as the base you propose when no promotion flow is defined
  (Step 7), and to decide whether an issue may carry a closing keyword (Step 9). Keep it.
- **`isFork`** and **`parent`** — fork status. Take it from here; do **not** infer a fork from the shape
  of the remote URL.
- **`viewerPermission`** — whether this user can act. `null` means *unknown*, not *denied*: continue,
  and let a refusal surface as a post-gate failure rather than refusing pre-emptively.

**If more than one remote is configured, or `origin` is a fork, do not guess** — ask the user which
remote and which base to use before proceeding.

Guessing is not merely impolite here, it is unsafe: `gh pr list --head` does **not** accept
`<owner>:<branch>` syntax, while `gh pr create --head` does. A fork flow that inferred the head would
therefore check for duplicates against one head and create the PR against another — which is exactly
how a duplicate pull request gets opened.

---

## Step 5 — Check the branch is one you can open a PR from

Derive the **source branch** (the branch the PR proposes) from the current branch:

```bash
git rev-parse --abbrev-ref HEAD
```

Refuse to proceed, with a clear explanation, in only two cases:

- HEAD is **detached** (the command returns `HEAD`) — there is no branch to propose.
- The current branch **is** the base you resolve in Step 7 — a branch cannot target itself.

**Any branch is otherwise fair game.** A bug fix on `fix/login-timeout`, a chore, a spike — all can open a
PR. What a spec branch changes is not permission but **material**: when the branch name matches a directory
under `specs/`, you have `spec.md`, `plan.md`, and `tasks.md` to draw the body from (Step 10). Without one you
use the commits and the diff instead.

These refusals are about the branch, not the tooling. Do not offer a `gh` remedy for them.

---

## Step 6 — Detect an existing open PR (no duplicates)

Before opening anything, check whether the source branch already has an open PR:

```bash
gh pr list --head <source-branch> --state open --json url,number
```

If an open PR already exists for this branch, **return its URL** to the user, note that no duplicate
was opened, and stop. Do not open a second PR.

On a fork, this check is only meaningful once Step 4's question has been answered — see the `--head`
limitation recorded there.

---

## Step 7 — Determine the target (base) branch

**Documented intent wins over anything you can infer.** Read the project's branching/promotion strategy from
both sources before deciding:

1. The constitution's **Version Control & Branching Strategy** section in
   `.specify/memory/constitution.md`.
2. The `git` extension's branching config, if present:
   `.specify/extensions/git/git-config.yml`.

Parse any **promotion flow** expressed as an ordered chain of branches (e.g. `feat → dev → main`). Then:

1. **`--base <branch>` was passed** — use it. It is the user's explicit instruction; it still appears in the
   final summary (Step 11).
2. **Both sources define a flow and they disagree** — surface the conflict and ask which applies. Do not
   apply a precedence and do not guess.
3. **A documented, unambiguous flow** — target the **next** branch in the flow after the source branch's
   stage, and record **the rule you used** so the summary can cite it. If that branch does not exist on the
   remote, surface it and stop: never silently retarget `main`, never create the missing branch.
4. **Nothing documented** — you must **propose** a base rather than settle one. In order of preference:
   - the branch this one appears to have been cut from, if you can establish it — compare the source branch
     against the remote's branches and take the nearest ancestor, e.g.
     `git merge-base HEAD origin/<candidate>` for the plausible candidates;
   - otherwise `defaultBranchRef` from Step 4.

   **Do not treat a proposal as agreed.** Carry it to the final summary (Step 11), which asks the user
   whether it is right and lets them redirect it in the same breath.

> **Why a proposal and not a decision.** Git records no parent branch. `@{upstream}` is the tracking branch,
> not the origin, and `git merge-base --fork-point` reads the reflog — so it yields nothing in a fresh clone
> or CI checkout, and nothing useful when two candidates point at the same commit or the branch has been
> rebased. Inference here is a good guess, and a good guess is exactly the kind of thing to have confirmed
> rather than acted on. Where a documented flow exists, it is a statement of intent and needs no guessing.

If a documented flow and the branch's apparent fork point disagree, use the **documented** one and mention the
divergence once in the summary, so the user can redirect if the branch really was cut from somewhere else.

---

## Step 8 — Make sure the branch is ready (commit & push)

Establish three facts first:

```bash
git status --porcelain                                   # uncommitted or untracked changes?
git ls-remote --heads origin <source-branch>             # does the branch exist on the remote?
git log --oneline origin/<source-branch>..HEAD           # unpushed commits? (skip if not on the remote)
```

**If the working tree is dirty**, list the affected files — grouped into modified, staged, and untracked — and
ask:

> There are uncommitted changes. Should I proceed with committing and pushing first?

- **Yes** — treat it exactly as an ordinary "commit and push" request:
  1. **Look at the list before staging.** Call out anything that looks like a credential or secret —
     `.env`, `*.pem`, `*.key`, `id_rsa`, `credentials*`, `*.p12` — and get a specific go-ahead for those files
     rather than sweeping them in with the rest.
  2. Stage the files you listed. Do not blind-`git add -A` beyond what you showed the user, and do not stage
     files that are clearly unrelated to this branch's work without saying so.
  3. Commit with a message that describes the work — a concise subject, and a body when the change warrants
     one. **Never pass `--no-verify`**: if a hook rejects the commit, report the hook's own message and stop
     rather than bypassing it.
  4. Push (`git push -u origin <source-branch>`), then say what you committed and pushed.
- **No** — continue, and state plainly that the PR will contain only what is already committed and that the
  listed changes are excluded. Do not commit anything.

**If the tree is clean but the branch is not on the remote, or has unpushed commits**, ask to push and, on
confirmation, run:

```bash
git push -u origin <source-branch>
```

**Never commit or push without that confirmation.** If the tree is clean and everything is already pushed,
say nothing and move on — there is no question to ask.

If a push is **refused**, go to *When an outward action is refused* below. Say exactly what reached the remote
and what did not: a commit that exists locally but was not pushed is a fact the user cannot recover by
guessing.

---

## Step 9 — Gather the linked issue (optional)

An issue link is **optional**. Ask for it, accept a refusal, and never invent one.

1. **`--issue` was passed** — use it and do not ask.
2. **Otherwise ask once**: *"Is there an issue this PR should be linked to? (number or URL — or skip)"*. An
   empty answer, "no", or "skip" means **no issue**: proceed without one and do not ask again.
3. **Validate what you were given** before using it:

   ```bash
   gh issue view <number-or-url> --json number,title,url,state
   ```

   If it does not resolve — wrong number, wrong repository, no access — say so plainly and **continue without
   the link**. A broken reference in the body is worse than no reference.

**How the issue is written depends on the base branch**, and this is not cosmetic:

- **Base is the repository's default branch** (`defaultBranchRef` from Step 4) — use a closing keyword, e.g.
  `Closes #42`. Merging will close the issue.
- **Base is any other branch** — use a **plain reference** (`#42`), and tell the user that GitHub will neither
  link nor auto-close the issue on this merge.
- **The issue lives in another repository** — reference it by **full URL**, never with a closing keyword.

> **Why.** GitHub's documentation is explicit: the closing keywords in a pull request description "are
> interpreted only when the pull request targets the repository's default branch. If the pull request targets
> any other branch, then these keywords are ignored, no links are created, and merging the PR has no effect on
> the issues." A `Closes #42` on a PR into `dev` therefore looks correct and does nothing at all — which is
> precisely the case a promotion flow produces. A plain mention still records a cross-reference on the issue,
> so it is the honest form there.

---

## Step 10 — Resolve the PR template and compose the body

The PR body's **structure** comes from a template, not from this file. Resolve `pr-template.md` through the
project's template stack and take the **first readable, non-empty** hit:

1. `.specify/templates/overrides/pr-template.md` — the project's own override. It wins outright.
2. `.specify/presets/<preset-id>/templates/pr-template.md` — any installed preset (in registry priority
   order, if a `.specify/presets/.registry` says so).
3. `.specify/extensions/spectra/templates/pr-template.md` — the template shipped with this extension.
4. `.specify/templates/pr-template.md` — a core template, if the project keeps one there.
5. The **inline skeleton** at the end of this command — last resort only, for a project with no `.specify/`
   at all.

Rules: stop at the first layer you can actually **use**, not the first that exists; if a layer is present but
empty or unreadable, say so in one line and continue. Never edit a template — they are input. **Report which
one you used**, by path, in the summary and again in the final report.

**Fill it from evidence, not from imagination.** Gather in this order:

- **The diff against the base** — always, and it is the source for **Changes**:

  ```bash
  git diff --name-status <target-branch>...HEAD
  git log --oneline <target-branch>..HEAD
  ```

  If the diff is **empty**, stop: there is nothing to review, and an empty PR wastes the reviewer's time.
- **Spec artifacts, when the branch has them** — a branch matching a directory under `specs/` gives you
  `spec.md` (Summary, How to Test), `plan.md` (design intent), and `tasks.md` (what was actually done). Link
  the spec file in the body.
- **Commits, when it does not** — a bug or chore branch has its commit messages and its diff; use them.

Filling rules:

- **Title** — a concise, self-describing subject line: the spec name on a spec branch, otherwise a summary of
  the change. It is the template's top heading; do not leave it as a placeholder.
- **Summary** — outcome first, in plain language, for a reviewer with no context on the ticket.
- **Related Issues** — where the reference from Step 9 goes. Three cases, and the first two are not optional:
  - **The template has a section for issues** — put it there, rendered per Step 9's base-branch rules. Judge
    that by intent rather than by heading text: a team's `## Ticket` or `## Linked work` is such a section,
    and appending a second one to a template that already handles issues would be noise.
  - **The template has no such section, and you have a resolved issue** — **append** a short
    `## Related Issues` section carrying the reference, and say once that you added it because the template
    had no place for it. The user can then move it where they want it in their own template.
  - **There is no issue** — remove the section entirely. No placeholder number, no empty heading.
- **Type of Change** — mark exactly one, based on what the diff actually does.
- **Changes** — from the diff, grouped when large; skip formatting-only noise.
- **How to Test** — the real commands, and what the reviewer should observe. Name the test suite when that is
  the fastest route to confidence.
- **Screenshots / Evidence** — paste the terminal output you actually produced (a test run, a build) where it
  helps; `N/A` when there is genuinely nothing visual or observable.
- **Breaking Changes** — leave the box unchecked unless the diff really breaks a contract; when it does, name
  what breaks and the migration path.
- **Notes for Reviewers** — trade-offs, deferred work, and anything you could not verify. Say plainly what you
  did not check.
- **Delete every guidance comment and `[PLACEHOLDER]` token.** None may survive into the posted body.
- **Honour the template; do not repair it.** If the resolved template drops sections, follow it as authored and
  mention the omission once. If it adds sections, fill them from the same evidence; where you have nothing to
  say, say so rather than inventing content. A project's override is a decision, not a suggestion.
- **One exception, and it is a matter of scope rather than an exception to the rule.** A resolved **issue
  reference is yours, not the template's.** A template governs how the body *reads*; it does not govern whether
  a pull request is linked to the issue the user passed. If the template has nowhere for it, append it — the
  alternative is that `--issue 42` silently produces an unlinked pull request that looks complete. `review-pr`
  draws the same line for its revision anchor, its AI-assisted disclosure, and its coverage statement: shape is
  the template's, functional obligations are the command's.
- **Do not tick a box that asserts something a human must vouch for.** If a project's override reintroduces a
  self-certification checklist ("I have self-reviewed the full diff"), leave those boxes unchecked and say you
  left them for the author.

---

## Step 11 — Final confirmation (one summary, one answer)

You now have everything. Show it in one place and ask once. **Create nothing before an affirmative answer.**

State:

- **Source → base**, and where the base came from: the promotion flow (cite the rule), `--base`, or a
  proposal. When it is a proposal, ask it as a question — *"This PR will be created to merge into `main`. Is
  that correct?"* — so the user can redirect with "no, use dev".
- **The linked issue**, or nothing. If there is no issue, leave the line blank or omit it — never fabricate.
  When the issue will not auto-close because the base is not the default branch, say so here.
- **Draft or ready-for-review.**
- **The template path** you resolved.
- **What has already happened** — a commit, a push — so the user knows the state they are in before answering.

Then ask a single yes/no, e.g. *"I have everything needed to open the PR. Continue?"*

- **The user corrects the base** — apply it, then **re-check two things** before proceeding: that the new
  target exists on the remote (`git ls-remote --heads origin <new-base>`), and whether the closing-keyword
  decision from Step 9 changes now that the base has changed. Re-diff against the new base if the Changes
  section would differ. Show the corrected summary and ask again.
- **The user declines** — create nothing. State what was already done (any commit, any push) and that the PR
  was not opened; they can run this command again later.

---

## Step 12 — Open the PR

Open the PR (ready-for-review by default; add `--draft` only if the user passed `--draft`):

```bash
printf '%s' "$BODY" | gh pr create \
  --base "<target-branch>" \
  --head "<source-branch>" \
  --title "<title>" \
  --body-file -
# add --draft when the user opted in
```

Two details in that call are deliberate:

- **`--body-file -` rather than `--body`.** The body is Markdown — headings, backticks, code fences, quotes,
  blank lines. As a shell argument that is a quoting hazard on every platform; on standard input it is just
  bytes.
- **`--head` is always passed explicitly.** `gh pr create` warns that without it, when the branch is
  not fully pushed, "a prompt will ask where to push the branch and offer an option to fork the base
  repository". An interactive prompt or an implicit fork is an unconfirmed mutation, which the one rule
  forbids.

If creation is **refused**, go to *When an outward action is refused* below — and remember that by this
point the branch is already on the remote, and possibly carries a commit you made.

---

## When an outward action is refused (after the gate)

You are past the pre-flight gate, so `gh` exists, is authenticated, and the target branch is derived.
**Degrade, do not discard** — and do not present the run as a success:

1. **Name what failed**, surfacing `gh`'s or `git`'s own message verbatim. A paraphrase loses the
   remedy GitHub itself supplied. The usual causes are a protected base branch, a token without push
   permission, and a fork restriction.
2. **State what was mutated, always** — even when the answer is nothing:
   - *nothing reached the remote* — the push itself was refused;
   - *the branch is on the remote, and no pull request exists* — the push landed and creation failed.

   This is the one fact the user cannot recover by guessing, so it is never left implicit.
3. **Hand over the commands that finish the job**, with the derived target branch substituted. Print the
   composed body in chat and have the user save it, so the command they run does not sit waiting on
   standard input:

   ```bash
   git push -u origin <source-branch>          # only if the branch is not on the remote yet
   gh pr create --base <target-branch> --head <source-branch> \
     --title "<title>" --body-file <path-to-the-saved-body>
   ```

   These run, because `gh` is present and authenticated here — which is exactly what makes this a
   useful hand-over rather than the empty one a missing `gh` would produce.

Read `gh`'s exit code before classifying the failure: **4** means the call requires authentication
(`gh help exit-codes`), so the remedy is `gh auth login` rather than a permission change; **2** means
the call was cancelled, so stop rather than retrying.

---

## Step 13 — Report in chat

On success, reply with:

- The **PR URL**.
- The **base branch** it targets, and where that came from — the promotion flow (name the rule), `--base`, or
  the proposal the user confirmed.
- The **template you used**, by path, so an override that was not picked up is obvious immediately.
- The **linked issue**, if any — and, when the base is not the default branch, the reminder that GitHub will
  not auto-close it on this merge.
- **What you changed on the way**: any commit you made and pushed, or the note that uncommitted changes were
  left out at the user's request.

If you returned an existing PR (Step 6), say so and include its URL. If you stopped at the pre-flight gate, at
the remote check, or at the branch check, leave the user with the specific reason and — for the gate — the one
remedy that applies.

### Opening the PR later (on demand)

This command is fully runnable **on demand**, not only via the post-`implement` offer. If the user
declined earlier, nothing was checked, committed, pushed, or opened, so invoking the command later on the same
branch runs this exact flow — gate, branch check, base, readiness, issue, template, summary, create.

---

## Edge cases

| Situation | What to do |
| --------- | ---------- |
| `gh` not installed | Hard stop before anything else; point at <https://cli.github.com>; print no `gh` command (Step 2) |
| `gh` present but not authenticated | Hard stop with `gh auth login` — a different message from the one above (Step 2) |
| Expired or revoked token | Same as unauthenticated, same remedy |
| Offer declined | Stop silently; the gate never runs and nothing is reported |
| No remote configured | Hard stop with the GitHub-only scope statement (Step 3) |
| Remote not on `github.com` | Hard stop naming the host; no `gh` fallback printed (Step 3) |
| GitHub Enterprise remote | Out of scope this version; stops as a non-GitHub remote |
| Several remotes, or `origin` is a fork | Ask which remote and base; never infer a fork from the URL (Step 4) |
| Detached HEAD | Refuse — there is no branch to propose (Step 5) |
| Already on the resolved base branch | Refuse — a branch cannot target itself (Step 5) |
| Branch has no matching `specs/` directory | Proceed; compose the body from commits and the diff instead (Step 5, Step 10) |
| Open PR already exists | Return its URL; open no duplicate (Step 6) |
| Promotion flow and branching config disagree | Surface the conflict and ask; apply no precedence (Step 7) |
| Documented flow disagrees with the apparent fork point | Use the documented flow; mention the divergence in the summary (Step 7) |
| Nothing documented, fork point undeterminable | Propose `defaultBranchRef` and say the proposal is a guess (Step 7) |
| Derived target branch missing on the remote | Surface and stop; never retarget `main`, never create it (Step 7) |
| Corrected base missing on the remote | Same — re-checked after the correction (Step 11) |
| Dirty working tree | List the files and ask whether to commit and push first (Step 8) |
| Credential-shaped file among the changes | Call it out and get a specific go-ahead before staging it (Step 8) |
| Commit rejected by a hook | Report the hook's message and stop; never `--no-verify` (Step 8) |
| User declines the commit offer | Open from committed work; state that the changes are excluded (Step 8) |
| No issue supplied or user skips | Proceed with no issue section; never fabricate one (Step 9) |
| Issue does not resolve via `gh issue view` | Say so and continue without the link (Step 9) |
| Issue in another repository | Reference by full URL; no closing keyword (Step 9) |
| Base is not the default branch | Plain reference, not a closing keyword; tell the user why (Step 9) |
| No template layer readable | Use the inline skeleton and say so (Step 10) |
| Resolved template omits a section | Follow it as authored; note the omission once (Step 10) |
| Override reintroduces a self-certification checklist | Leave those boxes unchecked; say you left them for the author (Step 10) |
| Empty diff against the base | Stop; there is nothing to review (Step 10) |
| User declines at the final gate | Create nothing; state any commit or push already made (Step 11) |
| Push refused | Degrade; state exactly what reached the remote and what did not |
| PR creation refused | Degrade; state that the branch is pushed and no PR exists |
| `gh` exits 4 after the gate | Report as authentication (`gh auth login`), not as a permission problem |

---

## Inline template skeleton (last resort for Step 10)

Use this **only** when no layer in Step 10 yielded a readable template — a project with no `.specify/`
directory at all. Its sections are identical to the shipped `pr-template.md`; fill it per Step 10 and delete
these guidance notes in the output.

```markdown
# <PR title>

## Summary

<!-- Outcome first, two to four sentences, for a reviewer with no context. -->

## Related Issues

<!-- `Closes #NNN` only when the base is the default branch; otherwise a plain `#NNN`. Delete the
     section when there is no issue. -->

## Type of Change

- [ ] Feature — new user-facing capability
- [ ] Bug fix — corrects broken behaviour
- [ ] Refactor — internal change, no behaviour change
- [ ] Documentation
- [ ] Build / CI / tooling
- [ ] Hotfix — urgent production fix

## Changes

<!-- From the real diff against the base; group when large; skip formatting noise. -->

## How to Test

<!-- The commands a reviewer runs, and what they should observe. -->

**Expected result:**

## Screenshots / Evidence

<!-- Terminal output, screenshots, or "N/A". -->

## Breaking Changes

- [ ] This PR contains breaking changes

<!-- If checked: what breaks, and the migration path. -->

## Notes for Reviewers

<!-- Trade-offs, deferred work, and anything you could not verify. -->
```
