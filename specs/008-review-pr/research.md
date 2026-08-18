# Phase 0 Research: Review PR

**Feature**: `008-review-pr` | **Date**: 2026-08-17 | **Plan**: [plan.md](./plan.md)

All `gh` capabilities below were verified against **`gh` version 2.97.0 (2026-07-31)** on the
development machine, by reading `--help` output rather than relying on recollection. Where a claim
could not be verified without network access against a live pull request, it is marked as such and
carried into [quickstart.md](./quickstart.md) for validation during implementation.

The spec entered planning with no `NEEDS CLARIFICATION` markers — five were resolved during
`/speckit.clarify`. The research below therefore resolves *implementation* unknowns, not requirement
unknowns.

---

## R-001 — How the reviewer's target is resolved from an optional URL

**Decision**: Accept `$ARGUMENTS` as an optional PR reference and pass it straight through to `gh`.
`gh pr view`, `gh pr diff`, and `gh pr review` all accept `[<number> | <url> | <branch>]` as their
positional argument, so a URL, a bare number, and a branch name all work with no parsing on our side.
With no argument, use `gh pr status`/`gh pr list --head <current-branch>` to offer the current branch's
open PR first, then `gh pr list --state open` for the picker.

**Rationale**: Verified in `gh pr review --help` — `USAGE: gh pr review [<number> | <url> | <branch>]`.
Delegating reference parsing to `gh` removes an entire class of URL-parsing bugs and automatically
supports enterprise hosts. It also satisfies FR-004 without a bespoke parser.

**Alternatives considered**: Parsing the URL ourselves to extract owner/repo/number — rejected as
redundant work that `gh` already does, and a portability hazard on GitHub Enterprise hosts.

---

## R-002 — Pinning the review to one revision, and gathering all metadata in one call

**Decision**: A single `gh pr view <ref> --json` call supplies every metadata field the summary needs.
Confirmed available fields include `headRefOid`, `baseRefOid`, `baseRefName`, `headRefName`, `number`,
`title`, `url`, `author`, `isDraft`, `statusCheckRollup`, `changedFiles`, `additions`, `deletions`,
`files`, `commits`, `reviews`, `latestReviews`, `headRepository`, `headRepositoryOwner`, and
`maintainerCanModify`.

Mapping to requirements:

| Requirement | Field |
|---|---|
| FR-005 pin and report the head revision | `headRefOid` |
| FR-009 constitution in force on the **base** branch | `baseRefOid`, `baseRefName` |
| FR-013 diff size against the budget | `changedFiles`, `additions`, `deletions` |
| FR-021 CI status | `statusCheckRollup` |
| FR-029 self-review detection | `author` vs `gh api user` |
| FR-036 existing review by the same reviewer | `reviews`, `latestReviews` |
| Draft edge case | `isDraft` |
| Fork edge case | `headRepository`, `headRepositoryOwner` |

**Rationale**: One call, verified field list, no guessing. `headRefOid` is what makes FR-005's
revision pinning and FR-032's pre-publication re-check exact rather than approximate — the re-check is
simply a second `gh pr view --json headRefOid` compared against the first.

**Alternatives considered**: Deriving the SHA from `git ls-remote` — rejected because it requires the
PR's branch to be fetchable locally, which is false for fork PRs and violates FR-007's prohibition on
touching the working tree.

---

## R-003 — The declared review budget (resolves FR-013)

**Decision**: **40 changed files or 1,500 changed lines, whichever is reached first.** Within the
budget every file is reviewed at full fidelity. Beyond it, rank the remaining files by risk and review
the highest-risk files up to the same budget, then disclose the excluded remainder. The figures are
stated in the command file itself so they are assertable, as FR-013 requires.

Risk ranking, highest first: security-relevant paths (auth, crypto, secrets, permissions) → data and
migrations → public API and contract surfaces → application logic → configuration and infrastructure →
tests → documentation.

**Rationale**: The clarify session settled the *mechanism* (a declared budget, not runtime judgment and
not a reviewer prompt); this resolves the *figures*. 40 files / 1,500 lines is large enough that the
overwhelming majority of real pull requests are reviewed whole, and small enough to leave context for
the authorizing context — spec, plan, tasks, ADRs, and constitution — which FR-006 and FR-009 require
to be read *alongside* the diff, not instead of it. Two dimensions are needed because either can be hit
alone: 60 one-line renames and 3 files of 900 lines each are both "large".

**Alternatives considered**: A single line-count threshold — rejected because a wide, shallow diff
evades it. A token-count budget — rejected as unstable across agents and models, and unassertable in a
test. No budget with pure runtime judgment — rejected by the clarify decision, because it makes SC-013
untestable.

---

## R-004 — Excluding generated files (resolves FR-014)

**Decision**: Use `gh pr diff --exclude <patterns>` to drop generated files at fetch time, and name the
exclusions in the coverage statement. Verified present in `gh pr diff --help`:
`-e, --exclude patterns   Exclude files matching glob patterns from the diff`.

Default exclusions: lock files (`*.lock`, `package-lock.json`, `yarn.lock`, `Cargo.lock`, `poetry.lock`,
`go.sum`, `Gemfile.lock`, `composer.lock`), vendored trees (`vendor/**`, `node_modules/**`,
`third_party/**`), build output (`dist/**`, `build/**`, `out/**`, `target/**`), minified assets
(`*.min.js`, `*.min.css`, `*.map`), and binary/media types.

**Rationale**: Native exclusion at fetch time is strictly better than post-filtering: the excluded bytes
never enter the review at all, so they cannot consume budget or leak into a finding. Exclusion is
declared, not silent, which is what FR-014 and SC-003 require.

**Alternatives considered**: Fetching everything and filtering afterwards — rejected as wasteful of the
very budget R-003 is rationing. Honouring `.gitattributes linguist-generated` — attractive and more
principled, but not exposed through `gh`; recorded as a possible enhancement.

---

## R-005 — Two-pass diff retrieval

**Decision**: Fetch the file list first with `gh pr diff --name-only` (plus `--exclude`), rank and apply
the budget against that cheap list, then fetch the patch with `gh pr diff --patch` for the files that
made the cut. Both flags verified present in `gh pr diff --help`.

**Rationale**: Risk-ranking needs only paths, so paying for the full patch before deciding what to
review inverts the order of operations. On an oversized PR the two-pass approach means the excluded
remainder is never fetched, which is what makes R-003's budget real rather than cosmetic.

**Alternatives considered**: A single `--patch` fetch followed by in-memory subsetting — simpler, but it
consumes the budget before the budget can be applied.

---

## R-006 — Reading the authorizing context at the head revision (resolves FR-006a)

**Decision**: Resolve the governing spec through the three-tier chain the clarify session set, then read
each artifact at the pinned revision with
`gh api repos/$REPO/contents/<path>?ref=<headRefOid> --jq .content`, decoding the base64 payload, where
`$REPO` is derived from the pull request's own URL (see the correction below).

> **Correction — 2026-08-17, after implementation.** This decision originally specified
> `repos/{owner}/{repo}/...` and justified it by quoting `gh api --help` as *"placeholder values
> `{owner}`, `{repo}`, and `{branch}` get populated with values"*. **That quote was truncated.** The
> sentence ends **"…from the repository of the current directory."** Placeholders resolve from the
> reviewer's working directory, not from the pull request under review.
>
> The consequence was a real defect, found while validating a reviewer's question about not having the
> branch locally: for any PR outside the reviewer's current repository, `gh pr view <url>` correctly
> targets the PR while `gh api repos/{owner}/{repo}/...` targets the reviewer's own repo. Metadata and
> diff would be right; every artifact read would 404 with *"No commit found for the ref"*; and the agent
> would conclude "no spec found", drop the guardrail lens, and report that absence as an honest coverage
> statement. A false negative wearing the costume of a truthful report — the one output this command must
> never produce.
>
> **Fix**: derive the repository from the PR URL and pin every call to it —
> `REPO=$(gh pr view <ref> --json url --jq '.url | capture("github.com/(?<o>[^/]+)/(?<r>[^/]+)/pull") | "\(.o)/\(.r)"')`
> — then pass `--repo "$REPO"` to every `gh pr` call and use `repos/$REPO/...` in every `gh api`
> endpoint. Placeholders are now forbidden by
> [contracts/gh-operations.md](./contracts/gh-operations.md). Verified working against a live cross-repo
> PR. The lesson generalizes: quoting a tool's documentation up to the clause that would have
> contradicted you is not verification.

The chain:

1. **A spec in the PR's own diff** — detect a `specs/<dir>/spec.md` path in the `--name-only` output.
   This is evidence, not convention, and is the normal case for spec-driven work.
2. **The Spec Kit feature record at the head revision** — read `feature_directory` from
   `.specify/feature.json` at `headRefOid`. Covers the addendum case where the spec merged earlier.
3. **Neither** — treat as no-spec and follow FR-012 (Story 3).

The constitution and ADRs are read at **`baseRefOid`**, not the head, because FR-009 requires the rules
being merged *into*. When the PR itself modifies the constitution or an ADR, that difference is exactly
what surfaces the governance change.

**Rationale**: Reading at an explicit `ref` is the only approach that satisfies FR-006 and FR-007
together — it needs no checkout, no fetch, and no assumption that the PR's branch exists locally, so it
works unchanged on fork PRs. Branch-name inference was explicitly rejected during clarification as a
project convention rather than a guarantee.

**Alternatives considered**: `git show <sha>:<path>` — rejected; requires the object locally, which
fails for forks and unfetched branches. Checking out the PR branch — rejected outright by FR-007.

---

## R-007 — Publishing as a single review event (resolves FR-033)

**Decision**: One `gh pr review <ref>` call carrying both verdict and body, with the body supplied
through `--body-file -` on stdin. Verified flags: `-a/--approve`, `-r/--request-changes`,
`-c/--comment`, `-b/--body`, `-F/--body-file file (use "-" to read from standard input)`.

| Reviewer's choice | Invocation |
|---|---|
| Approve | `gh pr review <ref> --approve --body-file -` |
| Request changes | `gh pr review <ref> --request-changes --body-file -` |
| Comment only | `gh pr review <ref> --comment --body-file -` |

**Rationale**: GitHub's native three-state review model maps one-to-one onto the spec's closed verdict
set, so a single call satisfies FR-033's one-review-event guarantee with no translation — the entire
class of platform-mismapping risk that the BRD carried for GitLab is absent by construction.
`--body-file -` is preferred over `--body` because review bodies routinely exceed comfortable
command-line argument length and contain backticks, quotes, and newlines that shell-escaping would
mangle.

**Alternatives considered**: `gh api repos/$REPO/pulls/<n>/reviews` with a JSON payload —
strictly more capable (it is the only route to line-anchored inline comments, FR-037) but requires
hand-built JSON and diff-position arithmetic. Deferred with FR-037 rather than adopted now; the
single-body form ships first, exactly as the spec's constraints state.

**Not verified without network**: that `--request-changes` rejects an empty body, and that approving
one's own PR returns 422. Both are carried into quickstart as validation steps rather than asserted
here.

---

## R-008 — Recovering prior findings without persistence (resolves FR-039)

**Decision**: List the PR's reviews via `gh pr view --json reviews` (or
`gh api repos/$REPO/pulls/<n>/reviews --paginate`), filter to reviews authored by the
authenticated user whose body contains the FR-034 AI-assisted disclosure line, and parse the recorded
head revision out of that body.

This requires the published body to be **self-describing**, which turns FR-034's disclosure and FR-005's
revision statement from presentation details into load-bearing structure. The output contract therefore
fixes both as stable, greppable lines.

**Rationale**: The only source of prior findings that introduces no persistence is the pull request
itself, which is what the clarify session chose. It is also the most authoritative source, being
literally what was published. FR-026 stays intact and no local store appears.

**Alternatives considered**: A local cache keyed by PR and revision — rejected; violates FR-026 and the
constitution's no-telemetry posture. Asking the reviewer to paste prior findings — rejected as
tedious and error-prone when the data is already on the PR.

---

## R-009 — Manifest declaration of the `gh` dependency

**Decision**: Leave `requires.tools` in `spectra/extension.yml` with **`gh: required: false`**, and
enforce the hard gate inside the command at runtime per FR-001.

**Rationale**: This looks like a contradiction and is not. `requires.tools` describes the *extension*,
which contains five commands, three of which (`adr`, `brd`, `domain-analyzer`) never touch GitHub.
Marking `gh` as extension-level required would degrade or block installation for users who want only
those three. The hard gate belongs to the command that actually needs it, which is precisely where
FR-001 puts it. The existing comment in the manifest is updated to name both `create-pr` (degrades) and
`review-pr` (hard-gates), so the difference is documented rather than surprising.

**Alternatives considered**: `required: true` — rejected; punishes users of the three commands that have
no GitHub dependency. Splitting GitHub commands into a second extension — rejected outright by
Principle II.

---

## R-010 — Version bump and the publishing surface (Principles V and VI)

**Decision**: Catalog channel only. `spectra/extension.yml` and the `catalog.json` `spectra` entry both
go **`1.3.1` → `1.4.0`** (MINOR — a command is added, nothing breaks). `catalog.json`
`provides.commands` goes **4 → 5**, `updated_at` is refreshed, and `review` / `code-review` join `tags`.
Root `VERSION` is untouched, and no git tag or GitHub Release is cut.

Every artifact in the same commit:

| Artifact | Change | By hand or generated |
|---|---|---|
| `spectra/commands/review-pr.md` | new command file | hand-authored |
| `spectra/extension.yml` | 5th `provides.commands` entry; version `1.4.0` | hand-authored |
| `spectra/CHANGELOG.md` | `1.4.0` entry | hand-authored |
| `agents-list.json` | `review-pr` roster entry, `status: available` | hand-authored |
| `AGENTS_LIST.md` | `<!-- SPECTRA:AGENT id=review-pr -->` prose block | hand-authored |
| `docs/index.html` | command card for `review-pr` | hand-authored |
| `catalog.json` | version, command count, tags, `updated_at` | hand-authored |
| `README.md`, `AGENTS_LIST.md`, `spectra/README.md` | generated regions | `tools/generate_agent_docs.py` |
| `docs/packages/spectra.zip` | rebuilt | `tools/build_package.py` |

**Rationale**: Verified by reading `tools/generate_agent_docs.py`: `check_prose_anchors` fails when a
shipped agent has no prose block anchored by stable id, and `check_manifest_agreement` fails when the
roster and manifest disagree about the shipped set. So registering `review-pr` as `available` without
the prose block and the manifest entry breaks CI. Verified by reading `docs/index.html`: the extension
version, description, and agent roster are fetched live from `catalog.json` and `agents-list.json`, but
the per-command cards are hand-written prose — consistent with Principle V's rule that tables and lists
are generated while paragraphs are written. The card must therefore be authored by hand.

**Alternatives considered**: Splitting the publishing updates into a follow-up commit — rejected;
Principle V requires them in the same change, and CI would fail the intermediate state anyway.

---

## R-011 — No automatic hook

**Decision**: `review-pr` registers **no** hook. It is on-demand only.

**Rationale**: The obvious candidate would be offering it after `create-pr`, closing the loop from
implementation to review. But the spec's first assumption is that the reviewer is *not* the author, and
that the agent runs in a fresh session with no memory of the code being written — that absence is what
makes the review independent. A hook firing right after the author opens their own PR would invite
exactly the self-review the design excludes, and GitHub would reject the approval anyway (FR-029). The
BRD reached the same conclusion.

**Alternatives considered**: An `after_create-pr` hook prompting a *different* reviewer — there is no
mechanism to address a different person from the author's session, so this is not implementable.

---

## R-012 — Rate limits (deferred item from clarification, now closed)

**Decision**: No special handling. Fetch normally and surface any rate-limit error verbatim if it occurs.

**Rationale**: A single review's call budget is roughly one `pr view`, two `pr diff` passes, one `api user`,
and a handful of `api contents` reads for the authorizing context — on the order of 10 to 50 requests.
GitHub's documented authenticated REST limit is 5,000 requests per hour, so a reviewer would need to run
dozens of reviews per hour to approach it. Building caching or backoff for that margin is unwarranted
complexity, and R-005's two-pass fetch already avoids the largest avoidable payload.

**Alternatives considered**: Caching artifact reads per revision — rejected as premature, and it edges
toward the persistence FR-026 forbids.

---

## Summary of decisions

| ID | Decision | Requirement resolved |
|---|---|---|
| R-001 | Pass the PR reference straight to `gh`; no bespoke URL parsing | FR-004 |
| R-002 | One `gh pr view --json` call for all metadata; `headRefOid` pins the review | FR-005, FR-021, FR-032 |
| R-003 | Budget = 40 files or 1,500 lines; risk-ranked subsetting beyond | FR-013, SC-013 |
| R-004 | Native `--exclude` for generated files, declared in coverage | FR-014 |
| R-005 | Two-pass diff: `--name-only` to rank, `--patch` for the cut | FR-013 |
| R-006 | Read artifacts at `ref`; three-tier spec discovery; constitution at base | FR-006, FR-006a, FR-009 |
| R-007 | Single `gh pr review` with `--body-file -` | FR-033 |
| R-008 | Recover prior findings by reading our own review off the PR | FR-039 |
| R-009 | `gh` stays extension-optional; the command hard-gates | FR-001 |
| R-010 | Catalog channel only; `1.3.1` → `1.4.0`; nine artifacts in one commit | FR-042 |
| R-011 | No hook; on-demand only | Story 1 independence |
| R-012 | No rate-limit handling needed | (closed deferred item) |

**No unresolved unknowns remain.** Three behaviours could not be verified without a live pull request —
empty-body rejection on `--request-changes`, the 422 on self-approval, and end-to-end publication — and
each is an explicit validation step in [quickstart.md](./quickstart.md).
