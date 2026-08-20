---
description: "Offer to open a correctly-targeted GitHub pull request for the current spec branch after implementation, deriving the base branch from the project's promotion strategy and returning the PR link."
---

# Open a Pull Request for the Current Spec

You are closing the loop on spec-driven development. The implementation for a spec is finished and you
are **offering** to open a pull request for it. Your job is to open a **correctly-targeted** PR using
`gh`, with the user in control at every outward step, and to return the PR link in chat.

`gh` is not optional. If it is missing or not authenticated, you **stop and say which** — you do not run
the flow anyway and hand back commands the user cannot execute. Once past that gate, a refusal from the
remote is different: there you degrade, hand over the exact manual commands, and say precisely what was
already mutated.

Work through the steps in order. Never skip the pre-flight gate or the source-branch validation, and
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

All pull request interaction goes through `gh`. Do not use `curl`, direct REST calls, or any other
route. You hold **no credentials of your own**: every interaction with GitHub goes through the user's
existing `gh` authentication.

---

## Step 1 — Offer and await go-ahead

If you were triggered automatically after `implement` (via the `after_implement` hook), **offer** to
open a PR for the completed spec and then **stop and wait** for the user's response. Take no Git or
remote action until the user accepts.

- If the user **declines** (e.g. "no"), take no action: do not check anything, do not push, do not open
  a PR. Note that they can open the PR later at any time by invoking this command directly (see
  Step 10). Then stop.
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

- **`defaultBranchRef`** — the target you propose when no promotion flow is defined (Step 7).
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

## Step 5 — Validate the source branch (one-branch-per-spec)

Derive the **source branch** (the branch the PR proposes) from the current branch:

```bash
git rev-parse --abbrev-ref HEAD
```

Refuse to proceed, with a clear explanation, if any of the following is true:

- HEAD is **detached** (the command returns `HEAD`).
- The current branch is the repository's **base/default branch** (`defaultBranchRef` from Step 4).
- The current branch does **not** match a spec directory under `specs/` (per the constitution's
  one-branch-per-spec rule, a spec branch name equals its `specs/<dir>` name).

In any of these cases there is nothing to propose a PR for — explain why (one-branch-per-spec; PRs are
opened *from* a spec branch, never from `main` or a detached HEAD) and stop. Never open a PR from a
non-spec branch.

This is a refusal, not a gate failure: the user's problem is the branch they are on, not their tooling.
Do not offer a `gh` remedy for it.

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
3. **No flow defined** — propose `defaultBranchRef` from Step 4 as the target. Ask the user to
   **confirm** `source → target` and proceed only after explicit confirmation.

If the user passed `--base <branch>`, use it as the target but still confirm `source → target` before
opening.

---

## Step 8 — Make sure the source branch is ready (commit & push)

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

If the push is **refused**, go to *When an outward action is refused* below. Nothing reached the remote,
and you must say so.

---

## Step 9 — Open the PR

Derive a self-describing **title** and **body** from the spec so reviewers see what was built:

- Locate the spec via `.specify/feature.json` (`feature_directory`) → `specs/<dir>/spec.md`.
- **Title** — the feature/spec name (and, if helpful, the spec number), e.g. `Open PR`.
- **Body** — a short summary drawn from the spec's summary/overview plus a link to the spec file
  (e.g. `specs/<dir>/spec.md`).

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

- **`--body-file -` rather than `--body`.** The body comes from spec prose — headings, backticks, code
  fences, quotes, blank lines. As a shell argument that is a quoting hazard on every platform; on
  standard input it is just bytes.
- **`--head` is always passed explicitly.** `gh pr create` warns that without it, when the branch is
  not fully pushed, "a prompt will ask where to push the branch and offer an option to fork the base
  repository". An interactive prompt or an implicit fork is an unconfirmed mutation, which the one rule
  forbids.

If creation is **refused**, go to *When an outward action is refused* below — and remember that by this
point the branch is already on the remote.

Remember the one rule: the only mutations are this push and PR creation — do not touch source code,
the spec, or the constitution.

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

## Step 10 — Report in chat

On success, reply with:

- The **PR URL**.
- The **base branch** the PR targets, and — when it came from a promotion flow — the **rule** you used
  to derive it.

If you returned an existing PR (Step 6), say so and include its URL. If you stopped at the pre-flight
gate, at the remote check, or at source-branch validation, make sure the user is left with the specific
reason and — for the gate — the one remedy that applies.

### Opening the PR later (on demand)

This command is fully runnable **on demand**, not only via the post-`implement` offer. If the user
declined earlier, nothing was checked, pushed, or opened, so invoking the command later on the same spec
branch runs this exact flow — gate, determine the target, confirm, push if needed, and open the PR —
just as it would have immediately after `implement`.

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
| `main`, detached HEAD, or non-spec branch | Refuse and explain one-branch-per-spec; this is not a tooling problem (Step 5) |
| Open PR already exists | Return its URL; open no duplicate (Step 6) |
| Promotion flow and branching config disagree | Surface the conflict and ask; apply no precedence (Step 7) |
| Derived target branch missing on the remote | Surface and stop; never retarget `main`, never create it (Step 7) |
| Dirty working tree | Surface the changes and warn the PR excludes them; do not commit for the user (Step 8) |
| Push refused | Degrade; state that nothing reached the remote |
| PR creation refused | Degrade; state that the branch is pushed and no PR exists |
| `gh` exits 4 after the gate | Report as authentication (`gh auth login`), not as a permission problem |
