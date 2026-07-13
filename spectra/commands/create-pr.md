---
description: "Offer to open a correctly-targeted GitHub pull request for the current spec branch after implementation, deriving the base branch from the project's promotion strategy and returning the PR link."
---

# Open a Pull Request for the Current Spec

You are closing the loop on spec-driven development. The implementation for a spec is finished and you
are **offering** to open a pull request for it. Your job is to open a **correctly-targeted** PR using
`gh`, with the user in control at every outward step, and to return the PR link in chat — or, if you
cannot, to explain the exact manual fallback.

Work through the steps in order. Never skip the preconditions or the source-branch validation, and
never take an outward action (pushing a branch, creating a PR) without explicit user confirmation.

## User Input

Optional arguments the user may pass:

$ARGUMENTS

Interpret them as follows (all optional — the command works with no arguments):

- **(no arguments)** — run the full default flow and open a **ready-for-review** PR.
- **`--draft`** — open the PR as a **draft** instead of ready-for-review.
- **`--base <branch>`** — override the derived target/base branch with `<branch>`. The override is
  still confirmed with the user before the PR is opened.

If the arguments contain anything you do not recognize, briefly note it and continue with the default
behavior rather than failing.

## The one rule that governs everything

Your **only** allowed mutations are the Git/remote actions required to open the PR — pushing the
source branch and creating the PR. You MUST NOT modify source code, the spec, or the constitution.
Every push and every PR creation MUST be preceded by an explicit user go-ahead.

---

## Step 1 — Offer and await go-ahead

If you were triggered automatically after `implement` (via the `after_implement` hook), **offer** to
open a PR for the completed spec and then **stop and wait** for the user's response. Take no Git or
remote action until the user accepts.

- If the user **declines** (e.g. "no"), take no action: do not push, do not open a PR. Note that they
  can open the PR later at any time by invoking this command directly (see Step 8). Then stop.
- If the user **accepts**, or if the command was invoked directly on demand, continue to Step 2.

---

## Step 2 — Check preconditions (and degrade gracefully)

Before doing anything else, verify the tools and remote are usable. If any check fails, **do not fail
opaquely and do not guess** — explain the situation and print the manual fallback (Step 2a), then stop.

1. **`gh` installed?** — `command -v gh`. If absent, degrade.
2. **`gh` authenticated?** — `gh auth status`. If not authenticated, degrade.
3. **Remote configured and on GitHub?** — read the remote URL with
   `git config --get remote.origin.url` and confirm it points to **github.com**:
   - HTTPS form: `https://github.com/<owner>/<repo>.git`
   - SSH form: `git@github.com:<owner>/<repo>.git`
   - Extract `<owner>` and `<repo>` from the URL. ONLY treat the remote as GitHub if the host is
     actually `github.com`. Do **not** assume GitHub when the URL doesn't match — degrade instead.
4. **Multiple remotes / fork?** — if more than one remote exists or `origin` looks like a fork, do not
   guess: ask the user which remote and base to use before proceeding.

### Step 2a — Manual fallback (when a precondition fails)

Explain which check failed, and give the user the exact commands they can run by hand, **including the
target branch you would have used** (derive it via Steps 3–5 even if you cannot open the PR):

```bash
git push -u origin <source-branch>
gh pr create --base <target-branch> --head <source-branch> --title "<title>" --body "<body>"
```

If `gh` is unavailable entirely, also mention opening the PR via the GitHub web UI for
`<owner>/<repo>`. Then stop.

---

## Step 3 — Validate the source branch (one-branch-per-spec)

Derive the **source branch** (the branch the PR proposes) from the current branch:

```bash
git rev-parse --abbrev-ref HEAD
```

Refuse to proceed, with a clear explanation, if any of the following is true:

- HEAD is **detached** (the command returns `HEAD`).
- The current branch is the repository's **base/default branch** (e.g. `main`).
- The current branch does **not** match a spec directory under `specs/` (per the constitution's
  one-branch-per-spec rule, a spec branch name equals its `specs/<dir>` name).

In any of these cases there is nothing to propose a PR for — explain why (one-branch-per-spec; PRs are
opened *from* a spec branch, never from `main` or a detached HEAD) and stop. Never open a PR from a
non-spec branch.

---

## Step 4 — Detect an existing open PR (no duplicates)

Before opening anything, check whether the source branch already has an open PR:

```bash
gh pr list --head <source-branch> --state open --json url,number
```

If an open PR already exists for this branch, **return its URL** to the user, note that no duplicate
was opened, and stop. Do not open a second PR.

---

## Step 5 — Determine the target (base) branch

Read the project's branching/promotion strategy from **both** sources before deciding:

1. The constitution's **Version Control & Branching Strategy** section in
   `.specify/memory/constitution.md`.
2. The `git` extension's branching config, if present:
   `.specify/extensions/git/git-config.yml`.

Parse any **promotion flow** expressed as an ordered chain of branches (e.g. `feat → dev → main`).
Then apply this algorithm:

1. **Conflict** — if *both* sources define a promotion flow and they **disagree**, surface the
   conflict and ask the user which flow applies. Do not apply a precedence and do not guess.
2. **Defined, unambiguous flow** — target the **next** branch in the flow after the source branch's
   stage. **State the target you derived and the rule it came from** (cite the promotion flow), so the
   user can catch a wrong inference. Do not ask the user to re-pick a base you have unambiguously
   derived.
   - If that next target branch **does not exist** on the remote, surface this and stop. Never
     silently retarget `main`, and never create the missing branch.
3. **No flow defined** — propose the repository's **default branch** as the target. Resolve it via
   `gh repo view --json defaultBranchRef` (fallback: `git symbolic-ref refs/remotes/origin/HEAD`).
   Ask the user to **confirm** `source → target` and proceed only after explicit confirmation.

If the user passed `--base <branch>`, use it as the target but still confirm `source → target` before
opening.

---

## Step 6 — Make sure the source branch is ready (commit & push)

1. **Uncommitted changes** — run `git status --porcelain`. If the working tree is dirty, surface the
   uncommitted/untracked changes and warn that the PR would not include them. Let the user decide
   before continuing; do not commit on their behalf.
2. **Branch on the remote?** — determine whether the source branch exists on the remote and whether
   there are unpushed commits:
   - `git ls-remote --heads origin <source-branch>` (does it exist remotely?)
   - compare local `HEAD` with `origin/<source-branch>` for unpushed commits.
3. If the branch is **not on the remote** or has **unpushed commits**, ask the user to push, and on
   confirmation run:

   ```bash
   git push -u origin <source-branch>
   ```

   **Never push without that confirmation.**

---

## Step 7 — Open the PR

Derive a self-describing **title** and **body** from the spec so reviewers see what was built:

- Locate the spec via `.specify/feature.json` (`feature_directory`) → `specs/<dir>/spec.md`.
- **Title** — the feature/spec name (and, if helpful, the spec number), e.g. `Open PR`.
- **Body** — a short summary drawn from the spec's summary/overview plus a link to the spec file
  (e.g. `specs/<dir>/spec.md`).

Open the PR (ready-for-review by default; add `--draft` only if the user passed `--draft`):

```bash
gh pr create --base <target-branch> --head <source-branch> --title "<title>" --body "<body>"
# add --draft when the user opted in
```

Remember the one rule: the only mutations are this push and PR creation — do not touch source code,
the spec, or the constitution.

---

## Step 8 — Report in chat

On success, reply with:

- The **PR URL**.
- The **base branch** the PR targets, and — when it came from a promotion flow — the **rule** you used
  to derive it.

If you returned an existing PR (Step 4), say so and include its URL. If you stopped at a precondition
or validation step, make sure the user is left with a clear explanation and, where relevant, the
manual fallback from Step 2a.

### Opening the PR later (on demand)

This command is fully runnable **on demand**, not only via the post-`implement` offer. If the user
declined earlier, nothing was pushed or opened, so invoking the command later on the same spec branch
runs this exact flow — determine the target, confirm, push if needed, and open the PR — just as it
would have immediately after `implement`.
