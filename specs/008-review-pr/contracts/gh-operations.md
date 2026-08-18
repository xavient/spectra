# Contract: `gh` Operations

**Feature**: `008-review-pr` | **Verified against**: `gh` version 2.97.0 (2026-07-31)

The **closed set** of `gh` invocations the command may use. FR-003 requires all pull request interaction
to go through `gh` exclusively; this contract fixes exactly which calls that means. Any interaction not
listed here is outside the contract.

Every flag below was verified by reading `gh --help` output on the development machine. Behaviours that
require a live pull request to confirm are marked **[verify in quickstart]**.

---

## OP-1 — Pre-flight: is `gh` usable?

```bash
command -v gh                 # installed?
gh auth status                # authenticated?
gh api user --jq .login       # who am I? (for self-review and own-review detection)
```

**Gate**: a non-zero exit from either of the first two is a **hard stop** (FR-001). The two failures must
be distinguished in the message — a missing binary needs an install, a failed `auth status` needs
`gh auth login`.

---

## OP-2 — Resolve the target

```bash
# With an argument: passed through unparsed — gh accepts <number> | <url> | <branch>
# With no argument, offer the current branch's PR first:
gh pr list --head "$(git rev-parse --abbrev-ref HEAD)" --state open --json number,title,url

# Then the picker:
gh pr list --state open --json number,title,author,headRefName,baseRefName,isDraft
```

**Rule**: with several candidates the reviewer chooses explicitly. The agent MUST NOT auto-select
(FR-004).

---

## OP-3 — Derive the repository, then fetch metadata and pin the revision

**Derive the PR's repository first.** Every later call must be pinned to it:

```bash
REPO=$(gh pr view <ref> --json url \
  --jq '.url | capture("github.com/(?<o>[^/]+)/(?<r>[^/]+)/pull") | "\(.o)/\(.r)"')
```

`gh pr view` honours a full URL, so this works from any directory — including one that is not a clone
of the reviewed project, which is the common case for a reviewer.

**`{owner}`/`{repo}` placeholders are forbidden in this contract.** `gh api --help` states they "get
populated with values **from the repository of the current directory**" — not from the pull request. A
cross-repo review would therefore fetch correct metadata and diff while every artifact read hit the
reviewer's own repository, 404ing on a revision that does not exist there, and the agent would report
"no spec found" and silently drop the guardrail lens.

```bash
gh pr view <ref> --repo "$REPO" --json \
  number,title,url,author,isDraft,\
headRefName,headRefOid,baseRefName,baseRefOid,\
changedFiles,additions,deletions,files,commits,\
statusCheckRollup,reviews,latestReviews,\
headRepository,headRepositoryOwner,maintainerCanModify
```

All fields verified present in `gh pr view --json` on v2.97.0. One call populates the entire
[Review target](../data-model.md#review-target) entity.

`headRefOid` is the pinned revision for FR-005 and the value re-checked at OP-8.

---

## OP-4 — Fetch the diff (two passes, research R-005)

```bash
# Pass 1 — cheap file list for risk ranking and budget evaluation
gh pr diff <ref> --repo "$REPO" --name-only \
  --exclude '*.lock' --exclude 'package-lock.json' --exclude 'yarn.lock' \
  --exclude 'Cargo.lock' --exclude 'poetry.lock' --exclude 'go.sum' \
  --exclude 'Gemfile.lock' --exclude 'composer.lock' \
  --exclude 'vendor/**' --exclude 'node_modules/**' --exclude 'third_party/**' \
  --exclude 'dist/**' --exclude 'build/**' --exclude 'out/**' --exclude 'target/**' \
  --exclude '*.min.js' --exclude '*.min.css' --exclude '*.map'

# Pass 2 — the patch, only after the budget has decided what is in scope
gh pr diff <ref> --repo "$REPO" --patch [same --exclude set]
```

`--name-only`, `--patch`, and `-e/--exclude patterns` all verified present in `gh pr diff --help`.

**Rules**: exclusions MUST be named in the coverage statement (FR-014). Pass 2 MUST NOT run before the
budget has been applied, or the budget is meaningless (R-005).

---

## OP-5 — Read a file at a revision

```bash
gh api "repos/$REPO/contents/<path>?ref=<sha>" --jq .content   # base64, then decode
```

`{owner}` and `{repo}` placeholder substitution and `-q/--jq` are verified in `gh api --help`.

Which revision, and why it matters:

| Artifact | Revision | Requirement |
|---|---|---|
| Spec, plan, tasks | `headRefOid` | FR-006 — what this change was authorized to do |
| The PR's own ADRs | `headRefOid` | FR-006 |
| Constitution | `baseRefOid` | FR-009 — the rules being merged *into* |
| ADRs in force | `baseRefOid` | FR-009 |
| `.specify/feature.json` | `headRefOid` | FR-006a tier 2 |

Reading at an explicit `ref` is what lets the command satisfy FR-006 and FR-007 simultaneously: no
checkout, no fetch, no working-tree contact, and it works unchanged for fork PRs.

**Never**: `git show <sha>:<path>` or a branch checkout. Both fail on forks and FR-007 forbids the latter.

---

## OP-6 — Detect an existing review by this reviewer

```bash
gh api "repos/$REPO/pulls/<number>/reviews" --paginate \
  --jq '.[] | select(.user.login == "<me>") | {id, state, submitted_at, body}'
```

Serves two requirements:

- **FR-036** — surface a prior review and ask whether to supersede or add another.
- **FR-039** — recover previously published findings by filtering to bodies containing the
  [disclosure line](./output-format.md#required-structural-lines) and parsing the recorded revision.

This is the *only* mechanism for prior findings; no local store exists (FR-026, research R-008).

---

## OP-7 — Publish the review

```bash
# Exactly one of the three, body always on stdin:
printf '%s' "$BODY" | gh pr review <ref> --repo "$REPO" --approve         --body-file -
printf '%s' "$BODY" | gh pr review <ref> --repo "$REPO" --request-changes --body-file -
printf '%s' "$BODY" | gh pr review <ref> --repo "$REPO" --comment         --body-file -
```

`--approve`, `--request-changes`, `--comment`, and `--body-file file (use "-" to read from standard
input)` all verified in `gh pr review --help`.

**Why `--body-file -` and not `--body`**: review bodies routinely exceed comfortable argument length and
contain backticks, quotes, and newlines. Passing on stdin removes shell-escaping as a failure mode
entirely.

**One call = one review event**, satisfying FR-033 with no translation, because GitHub's native
three-state model maps one-to-one onto the spec's closed verdict set.

**[verify in quickstart]**: that `--request-changes` rejects an empty body, and that approving one's own
PR returns 422.

---

## OP-8 — Freshness re-check before publishing

```bash
gh pr view <ref> --repo "$REPO" --json headRefOid --jq .headRefOid   # compare against the pinned value
```

If it differs, **warn and offer re-analysis; do not publish** (FR-032). This runs after the final
go-ahead and before OP-7 — it is the last gate, guarding against a review of code that is no longer
current.

---

## Explicitly outside the contract

| Not used | Why |
|---|---|
| `gh pr merge` | Merging is out of scope; it belongs to the author and branch protection |
| `gh pr checkout` | FR-007 forbids altering the working tree |
| `gh pr edit`, `gh pr comment` | Would produce mutations beyond the single permitted review event |
| `gh pr close` / `reopen` | Not a review action |
| `gh api ... /pulls/<n>/reviews` **POST** | The route to inline comments (FR-037), deferred; OP-7 ships first |
| Any direct `curl` or REST call | FR-003 requires `gh` exclusively |
| Any `git push`, `commit`, `checkout` | FR-007, FR-008 |

---

## Call budget

A single review issues roughly:

| Operation | Calls |
|---|---|
| OP-1 pre-flight | 3 |
| OP-2 resolve | 0–2 |
| OP-3 metadata | 1 |
| OP-4 diff | 2 |
| OP-5 artifacts | 3–10 |
| OP-6 existing reviews | 1 |
| OP-7 publish | 0–1 |
| OP-8 freshness | 1 |
| **Total** | **~11–21** |

Against GitHub's documented authenticated limit of 5,000 requests per hour, no caching or backoff is
warranted (research R-012). A rate-limit error, if one somehow occurs, is surfaced verbatim.
