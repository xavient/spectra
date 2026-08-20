# Phase 0 Research: Create PR Gates on `gh`

**Feature**: `009-create-pr-gh-gate` | **Date**: 2026-08-19

Every decision below was settled before Phase 1. `gh` behaviours are **verified against `gh` version
2.97.0 (2026-07-31)** — the same version `008-review-pr` pinned — by reading `--help` output on the
development machine. Verified strings are quoted.

---

## R-001 — A hard gate, not a graceful degradation

**Decision**: When `gh` is missing or unauthenticated, `create-pr` **stops**. It does not derive a target
branch, does not touch the remote, and does not print a manual `gh` fallback.

**Rationale**: The published justification for the old behaviour was that `create-pr` could still print a
useful manual path where `review-pr` could not. Three facts undercut it:

1. **The printed path was unusable.** The fallback told the user to run `gh pr create` — the command they
   demonstrably do not have.
2. **The dedup check cannot run without `gh`.** `create-pr`'s existing-PR detection (002 FR-010) is a
   `gh pr list` call. A "fallback" that skips it can walk the user into a second pull request for a
   branch that already has one, which is a worse outcome than stopping.
3. **The value of the command is the pull request.** `review-pr` hard-gates because its value is the
   analysis and the analysis needs `gh`. The identical argument applies here with the object swapped: the
   product is the PR, and the PR needs `gh`. The two commands were never really different — the earlier
   reasoning mistook "we can print something" for "we can deliver something".

**Alternatives rejected**:

- *Keep degrading, but fix the fallback text* (print the web-UI route instead of `gh pr create`).
  Rejected: it still performs constitution reads and target derivation whose only consumer is a message,
  and it still leaves the dedup gap. The user's remedy is one command; the honest answer is to name it.
- *Gate only on presence, and let an unauthenticated `gh` fail naturally at `gh pr create`.* Rejected: it
  fails **after** the push, manufacturing exactly the partial state FR-011 exists to prevent.

---

## R-002 — The gate sits after the go-ahead, not before the offer

**Decision**: The pre-flight runs as the first action **after** the user accepts the offer (or invokes the
command directly). The `after_implement` offer itself is never gated.

**Rationale**: The offer is free and reversible; `gh` is only needed once the user says yes. Gating
earlier would turn every `implement` on a machine without `gh` into an unsolicited error, punishing users
who never intended to open a pull request. This ordering is also what `review-pr` does in substance — its
Step 1 is the first thing that happens *once the command is running*, and `review-pr` has no offer to
precede it.

**Consequence for the command file**: the gate becomes Step 2, immediately after Step 1's offer, which is
where the precondition block already lives. The change is to its semantics and message set, not its
position.

---

## R-003 — Distinguishing the two failures mechanically

**Decision**:

```bash
command -v gh                              # presence
gh auth status --hostname github.com       # authentication, on the host that matters
```

**Rationale and verified facts**:

- `gh auth status --help` states: "If an account on any host (or only the one given via `--hostname`) has
  authentication issues, the command will **exit with 1** and output to stderr." Exit status is therefore
  a reliable signal, and `--hostname github.com` scopes the check to the only host this release supports.
- The same help text warns: "when using the `--json` option, the command will **always exit with zero**
  regardless of any authentication issues". **`--json` is therefore forbidden in the gate** — it would
  silently convert a failure into a pass.
- `gh help exit-codes` documents exit **4** as "If a command requires authentication". Useful *after* the
  gate to recognise an auth failure in any later call, and recorded in the contract for that purpose.

**Message set** (FR-002): missing binary → the GitHub CLI is not installed, point at <https://cli.github.com>.
Present but unauthenticated → run `gh auth login`. Two failures, two messages, one remedy each. An expired
or revoked token surfaces as the second case and takes the same remedy, which is why the spec folds it in
rather than adding a third kind.

---

## R-004 — A non-GitHub remote stops too, and names its scope

**Decision**: No remote, or a remote whose host is not `github.com`, ends the run with a statement that
this version supports GitHub only and what was found. No `gh` fallback line is printed.

**Rationale**: A `gh pr create` command is meaningless against a GitLab remote, so printing one is worse
than printing nothing. This is a scope statement, not a tool failure, and the message should read like
one.

**GitHub Enterprise**: `gh` can target other hosts via `GH_HOST`, so Enterprise support is technically
reachable — and deliberately **out of scope** here. The remote check stays `github.com`-only (unchanged
from 002), and Enterprise is named as unsupported rather than half-attempted. Widening it is a separate
feature with its own auth-host handling.

---

## R-005 — What survives of the manual fallback: post-gate degradation

**Decision**: The manual-fallback text moves to failures that occur **after** the gate has passed — a
refused push, a protected base branch, an insufficient token, a fork restriction, a lost network. There it
reports what failed, hands over the runnable command including the derived base branch, and states the
**mutation state**: whether the source branch reached the remote.

**Rationale**: This is the gap the old design actually left open. `create-pr` had no instructions for a
post-gate failure even though, by that point, it may already have pushed. `review-pr` Step 11 is the
model — "Degrade, do not discard … leave no partial review behind" — and the analogue here is stronger,
because `review-pr`'s worst partial state is a half-posted review while `create-pr`'s is a branch on the
remote with no pull request pointing at it.

**Why the fallback is genuinely usable here**: past the gate, `gh` exists and is authenticated. The
printed command runs.

---

## R-006 — The body goes over standard input

**Decision**: `printf '%s' "$BODY" | gh pr create … --body-file -` replaces `--body "<body>"`.

**Verified**: `gh pr create --help` lists `-F, --body-file file   Read body text from file (use "-" to
read from standard input)`.

**Rationale**: The body is assembled from spec prose — headings, backticks, code fences, quotes, blank
lines. As a shell argument that is a quoting hazard on every platform the extension supports; on stdin it
is bytes. `review-pr` already made this choice for review bodies (its OP-7) for the same reason, so this
is parity rather than novelty. The title stays on `--title`: it is one short line with no newlines.

---

## R-007 — One structured repository query replaces two ad-hoc probes

**Decision**:

```bash
gh repo view --json nameWithOwner,isFork,parent,defaultBranchRef,viewerPermission
```

**Verified**: all five fields appear in `gh repo view --json` field list on 2.97.0.

**Rationale**: The current command detects a fork by whether `origin` "looks like a fork" — a URL-shape
guess — and resolves the default branch in a separate call with a `git symbolic-ref` fallback. One
structured call answers both questions from GitHub's own data, and `viewerPermission` additionally lets
the command warn before attempting an action the token cannot perform.

**A pleasant consequence of the gate**: because `gh` is guaranteed present and authenticated past Step 2,
the `git symbolic-ref refs/remotes/origin/HEAD` fallback for the default branch is no longer needed. The
hard gate does not just change failure behaviour — it removes a branch of logic that existed only to cover
a `gh`-less world.

---

## R-008 — The fork case: `gh pr list --head` will not take `owner:branch`

**Decision**: Several remotes, or an `origin` that is a fork, is resolved by **asking the user** which
remote and base to use. The command does not silently dedup or create across repositories.

**Verified**, and the reason this is not merely conservative:

- `gh pr list --help`: `-H, --head string   Filter by head branch ("<owner>:<branch>" syntax **not
  supported**)`.
- `gh pr create --help`: "`--head` supports `<user>:<branch>` syntax to select a head repo owned by
  `<user>`."

The two calls disagree about what a fork head looks like, so a fork flow that guessed would dedup against
the wrong head while creating against the right one — the precise shape of bug that produces a duplicate
pull request. Asking is not politeness here; it is the only correct behaviour available from the tool.

---

## R-009 — `gh` stays extension-optional; both commands hard-gate

**Decision**: `requires.tools` keeps `gh` at `required: false`. The manifest comment is rewritten to say
that **both** GitHub commands hard-gate on it.

**Rationale**: Unchanged from 008 R-009 — `adr`, `brd`, and `domain-analyzer` never touch GitHub, and
marking `gh` required would degrade installation for users who only want those. What changes is the second
half of that comment, which currently records a difference between the two commands that this feature
eliminates.

---

## R-010 — The documentation surface that asserts the old behaviour

**Decision**: Six places state or imply that `create-pr` degrades, and all six move in this change
(FR-015, Principle V). Enumerated here so the task list can be mechanical rather than exploratory:

| File | What it says now |
|---|---|
| `spectra/extension.yml` (`requires.tools` comment) | "create-pr degrades gracefully and prints a manual fallback, while review-pr hard-stops" |
| `spectra/README.md` (create-pr §1 and its closing paragraph) | "**degrades gracefully** with a manual fallback"; "prints the manual `git push` + `gh pr create` commands" |
| `spectra/README.md` (review-pr §1) | "Unlike `create-pr` this does **not** degrade" |
| `AGENTS_LIST.md` (`id=create-pr` prose) | "degrading gracefully with a manual fallback when `gh`, the remote, or the network is unavailable" |
| `AGENTS_LIST.md` (`id=review-pr` prose) | "Unlike `create-pr`, this command **hard-stops** … instead of degrading" |
| `spectra/CHANGELOG.md` (1.4.0 entry) | "Two behaviours differ from `create-pr` on purpose" |

**Handling**: the first five are corrected in place. The changelog entry for 1.4.0 is **history and stays
as written** — the 1.5.0 entry states the reversal, which is how a changelog is supposed to work. Nothing
else in the repository asserts the behaviour: `agents-list.json` and `docs/index.html` describe the
command without mentioning degradation, and no test asserts the old text.

---

## R-011 — Parity items deliberately *not* adopted from `review-pr`

Recorded so a future reader does not mistake their absence for an oversight:

| `review-pr` behaviour | Adopted? | Why |
|---|---|---|
| `gh api user --jq .login` in the pre-flight | **No** | It exists to detect self-review and the reviewer's own prior reviews. `create-pr` has no such concept. `viewerPermission` from R-007 covers the only useful part — can this user act? |
| `--repo "$REPO"` on every call | **Partially** | `review-pr` reviews pull requests in repositories it is not standing in; `create-pr` always operates on the current repository's branch. `--repo` is used only where the fork question makes the target explicit. |
| A declared work budget | **No** | Nothing here scales with diff size. |
| Pinning a revision | **No** | A pull request is opened *from* a branch tip; there is no analysis to pin. |

---

## R-012 — Version bump and the publication set

**Decision**: `1.4.0` → **`1.5.0`** (MINOR) in `spectra/extension.yml` and the `catalog.json` mirror, with
a matching `spectra/CHANGELOG.md` entry.

**Rationale**: Constitution Principle VI requires a SemVer bump whenever a command is "added, changed, or
removed". A shipped command's failure behaviour changes; no argument, no output contract, and no command
name changes, and nothing that previously succeeded now fails. House precedent supports the level: 1.4.0
was MINOR for an added command, 1.3.1 was PATCH for wording only. A MAJOR was considered — documented
behaviour is being removed — and rejected because the removed behaviour is a failure path that produced
unusable output, not an interface consumers can depend on.

**Publication set** (Principle V, all in this change): `spectra/extension.yml`, `spectra/CHANGELOG.md`,
`spectra/README.md`, `AGENTS_LIST.md`, `catalog.json` (version + `updated_at`), and a rebuilt
`docs/packages/spectra.zip`. `agents-list.json` needs no edit (its `create-pr` description does not mention
degradation), `docs/index.html` needs no edit (it fetches version, description, and roster at page load),
and `README.md`'s generated table is unaffected because the roster is unchanged. **The zip rebuild is not
optional**: CI's `catalog` job diffs the packaged `spectra/` tree against the folder and fails on drift.

---

## Resolved-decision index

| ID | Decision | Requirements served |
|---|---|---|
| R-001 | Hard gate replaces graceful degradation | FR-001, FR-004 |
| R-002 | Gate runs after the go-ahead, not before the offer | FR-005 |
| R-003 | `command -v gh` + `gh auth status --hostname github.com`; no `--json`; exit 4 recognised later | FR-001, FR-002 |
| R-004 | Non-GitHub / absent remote stops, naming scope | FR-006 |
| R-005 | Fallback survives only post-gate, with mutation state | FR-010, FR-011 |
| R-006 | Body over stdin via `--body-file -` | FR-012 |
| R-007 | One `gh repo view --json` call; `git symbolic-ref` fallback retired | FR-007, FR-009 |
| R-008 | Fork/multi-remote asks, because `pr list --head` rejects `owner:branch` | FR-007 |
| R-009 | `gh` stays extension-optional; comment records both gates | FR-014 |
| R-010 | Six documentation sites, five corrected in place | FR-015 |
| R-011 | Parity items deliberately not adopted | — |
| R-012 | MINOR bump to 1.5.0; full Principle V set including the zip | FR-015 |
