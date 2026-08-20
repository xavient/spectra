# Contract: `gh` Operations

**Feature**: `009-create-pr-gh-gate` | **Verified against**: `gh` version 2.97.0 (2026-07-31)

The **closed set** of `gh` invocations `speckit.spectra.create-pr` may use. FR-008 requires all
pull-request interaction to go through `gh` exclusively; this contract fixes exactly which calls that
means. Anything not listed here is outside the contract.

Every flag below was verified by reading `gh --help` output on the development machine, and the verified
wording is quoted where the behaviour turns on it. Behaviours that need a live repository to confirm are
marked **[verify in quickstart]**.

---

## OP-1 — Pre-flight: is `gh` usable?

```bash
command -v gh                            # installed?
gh auth status --hostname github.com     # authenticated on the host this release supports?
```

**Gate**: a non-zero exit from either is a **hard stop** (FR-001). The two MUST be distinguished, because
the remedies differ: a missing binary needs an install, a failed `auth status` needs `gh auth login`
(FR-002).

Two verified facts make this the correct formulation:

- `gh auth status --help`: "If an account on any host (or only the one given via `--hostname`) has
  authentication issues, the command will **exit with 1** and output to stderr."
- The same text: "when using the `--json` option, the command will **always exit with zero** regardless of
  any authentication issues". **`--json` is forbidden in this call** — it would turn a failure into a pass.

`-h, --hostname string` is verified present in `gh auth status --help`.

**Nothing else runs before this.** No `git config`, no constitution read, no `gh repo view`.

---

## OP-2 — Repository facts, in one query

```bash
gh repo view --json nameWithOwner,isFork,parent,defaultBranchRef,viewerPermission
```

All five fields are verified present in the `gh repo view --json` field list on 2.97.0.

Serves four requirements at once:

| Field | Used for | Requirement |
|---|---|---|
| `nameWithOwner` | Naming the repository in messages and the web-UI route | FR-003 |
| `isFork`, `parent` | Fork detection — **never** inferred from the remote URL | FR-007 |
| `defaultBranchRef` | The proposed target when no promotion flow is defined | 002 FR-004 |
| `viewerPermission` | Warning before attempting an action the token cannot perform | FR-010 |

**Rules**:

- This call runs **after** OP-1, never before (FR-001).
- `viewerPermission` of `null` means *unknown*, not *denied*: proceed and let OP-4/OP-5 fail into the
  post-gate degradation rather than pre-emptively refusing.
- The `git symbolic-ref refs/remotes/origin/HEAD` fallback that 002 used for the default branch is
  **retired**. Past OP-1, `gh` is guaranteed usable, so the fallback covered a state that can no longer
  occur (research R-007).

---

## OP-3 — Existing-PR detection

```bash
gh pr list --head <source-branch> --state open --json url,number
```

`--head`, `--state`, and `--json` are verified in `gh pr list --help`.

**Constraint that shapes the fork rule**: `gh pr list --help` documents `-H, --head string   Filter by head
branch ("<owner>:<branch>" syntax **not supported**)`, while `gh pr create --help` states "`--head`
supports `<user>:<branch>` syntax to select a head repo owned by `<user>`". The two calls therefore
disagree about how a fork head is expressed. A fork flow that guessed would dedup against one head and
create against another — the exact path to a duplicate pull request. Hence FR-007: **ask**, do not infer
(research R-008).

---

## OP-4 — Push the source branch

```bash
git ls-remote --heads origin <source-branch>    # does it exist remotely?
git push -u origin <source-branch>             # only after explicit confirmation
```

Not a `gh` call, listed here because it is the first mutation and the one that sets `MutationState` to
`branch_pushed`. A refusal here is a **post-gate degradation** with the mutation state reported as `none`
(FR-010, FR-011).

---

## OP-5 — Create the pull request

```bash
printf '%s' "$BODY" | gh pr create \
  --base "<target-branch>" \
  --head "<source-branch>" \
  --title "<title>" \
  --body-file -
# add --draft only when the user asked for it
```

Verified in `gh pr create --help`: `-B, --base branch`, `-H, --head branch`, `-t, --title string`,
`-d, --draft`, and `-F, --body-file file   Read body text from file (use "-" to read from standard
input)`. `-R, --repo [HOST/]OWNER/REPO` is verified in the same command's INHERITED FLAGS.

**Why `--body-file -` and not `--body`** (FR-012): the body is assembled from spec prose containing
headings, backticks, code fences, quotes, and blank lines. As an argument that is a quoting hazard on every
supported platform; on stdin it is bytes. `review-pr` made the same choice for review bodies.

**`--head` is always passed explicitly.** `gh pr create --help` warns that without it, "When the current
branch isn't fully pushed to a git remote, a prompt will ask where to push the branch and offer an option
to fork the base repository … Use `--head` to explicitly skip any forking or pushing behavior." An
interactive prompt or an implicit fork is exactly the unconfirmed mutation the governing rule forbids.

**`--repo` is passed when the fork question made the target repository explicit** (FR-007); otherwise the
current repository is correct and adding it buys nothing.

**[verify in quickstart]**: that a body containing backticks and newlines arrives unaltered, and that
`--draft` is absent unless requested.

---

## Post-gate error interpretation

| Signal | Meaning | Response |
|---|---|---|
| Exit 4 from any call | `gh help exit-codes`: "If a command requires authentication, the exit code will be 4" | Report as authentication, remedy `gh auth login` — not as a permission problem (data-model V-7) |
| Exit 1 with a permission message | Token or branch protection refused the action | Post-gate degradation, cause surfaced verbatim |
| Exit 2 | "a command is running but gets cancelled" | Report as cancelled; mutate nothing further |

Surfacing `gh`'s own message verbatim is deliberate: a paraphrase loses the remedy GitHub itself supplied.

---

## Explicitly outside the contract

| Not used | Why |
|---|---|
| `gh pr create --web` | Opens a browser flow, bypassing the confirmation and the derived base |
| `gh pr create --fill` / `--fill-first` | Title and body come from the spec, not from commit messages (002 FR-011) |
| `gh pr create --editor` | Interactive editor breaks the agent-driven flow |
| `gh pr merge`, `gh pr review`, `gh pr edit`, `gh pr close` | Beyond the two permitted mutations |
| `gh auth login` / `gh auth refresh` executed by the command | The remedy is **named**, never run on the user's behalf — it is interactive and credential-bearing |
| `gh api` with `{owner}`/`{repo}` placeholders | Not needed here; and per 008's contract they resolve from the current directory, which is a silent-failure hazard |
| Any direct `curl` or REST call | FR-008 requires `gh` exclusively |
| `git commit`, `git checkout`, `git reset` | Only pushing is permitted (002 FR-008) |

---

## Call budget

| Operation | Calls |
|---|---|
| OP-1 pre-flight | 2 |
| OP-2 repository facts | 1 |
| OP-3 dedup | 1 |
| OP-4 push | 0–2 |
| OP-5 create | 0–1 |
| **Total** | **4–7** |

One call fewer than the pre-change flow in the common case, because OP-2 replaces both the fork heuristic
and the separate default-branch lookup. No caching or rate-limit handling is warranted at this volume.
