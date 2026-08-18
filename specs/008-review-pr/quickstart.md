# Quickstart: Validating Review PR

**Feature**: `008-review-pr` | **Plan**: [plan.md](./plan.md)

How to prove the command works before publishing it. This is a validation guide, not an implementation
guide — the command's behaviour lives in `spectra/commands/review-pr.md`, and the task breakdown lives in
`tasks.md`.

Constitution Development Workflow step 5 requires local testing via `specify extension add --dev` into a
throwaway project before publishing. That is what this guide covers.

---

## Prerequisites

```bash
gh --version        # 2.97.0 or later — the contract was verified against this
gh auth status      # must report an authenticated account
specify --version   # Spec Kit CLI on PATH
python3 --version   # for the two maintainer scripts under tools/
```

You also need:

- **A GitHub repository you can review pull requests in.** Not the Spectra repo itself for the
  destructive-ish checks — publishing a review is a real, visible action on a real PR.
- **A pull request authored by someone else**, for the scenarios that require not being the author.
  Several requirements (FR-029, and approval generally) cannot be exercised on your own PR.
- **A pull request that carries a spec** for Story 1, and one that does not for Story 3.

---

## Repository-level checks (no PR needed)

Run these first — they are fast and catch the Principle V sync failures that CI would reject.

```bash
# 1. Roster, generated regions, prose blocks, and manifest all agree
python3 tools/generate_agent_docs.py --check

# 2. Package rebuilt and not drifted
python3 tools/build_package.py
git diff --stat docs/packages/spectra.zip

# 3. Version and command count parity between manifest and catalog
#    Dependency-free on purpose: PyYAML is not in the system python3 on a default macOS install.
python3 - <<'PY'
import json, re, sys
ext_src = open('spectra/extension.yml').read()
ext_version = re.search(r'^extension:.*?^\s+version:\s*"?([0-9.]+)"?', ext_src, re.M | re.S).group(1)
ext_count = len(re.findall(r'^\s+-\s+name:\s*"speckit\.spectra\.', ext_src, re.M))
cat = json.load(open('catalog.json'))['extensions']['spectra']
print(f'extension.yml : version={ext_version} commands={ext_count}')
print(f'catalog.json  : version={cat["version"]} commands={cat["provides"]["commands"]}')
checks = {
    'manifest/catalog version parity': ext_version == cat['version'],
    'manifest/catalog command-count parity': ext_count == cat['provides']['commands'],
    'version bumped to 1.4.0': ext_version == '1.4.0',
    'command count is 5': cat['provides']['commands'] == 5,
}
for name, passed in checks.items():
    print(('  PASS  ' if passed else '  FAIL  ') + name)
sys.exit(0 if all(checks.values()) else 1)
PY

# 4. CLI channel untouched (Principle VI)
git diff --exit-code VERSION && echo "VERSION untouched — correct, this is a catalog-channel change"
```

**Expected**: all four pass. Check 1 fails loudly if the `review-pr` prose block is missing from
`AGENTS_LIST.md` or if the roster and manifest disagree — both are easy to forget and both break CI.
Before implementation, check 3 correctly reports parity at `1.3.1` with 4 commands and fails the last
two assertions; after implementation all four lines must read `PASS`.

---

## Install into a throwaway project

```bash
mkdir -p /tmp/review-pr-trial && cd /tmp/review-pr-trial
specify init .
specify extension add --dev /Users/alibahaloo/Projects/spectra/spectra
specify extension info spectra          # should list 5 commands, including speckit.spectra.review-pr
```

Restart your coding agent so it picks up the new command, then confirm the trigger appears in its
command or skill list. The trigger differs by agent — `/speckit-spectra-review-pr` on Claude,
`/speckit.spectra.review-pr` on kiro-cli.

---

## Scenario 1 — Story 1: review by URL and publish (P1, the MVP)

Run the command with a PR URL authored by someone else.

**Assert on the summary** (FR-021, FR-015, FR-016, FR-017):

- [ ] The head revision is named
- [ ] Every finding carries a file and line
- [ ] Every finding cites a source — a quoted clause, a requirement id, or a named principle
- [ ] Every finding carries a severity **and** a confidence
- [ ] No finding is a blocker at low confidence (FR-017)
- [ ] Findings are numbered in one flat sequence (FR-019)
- [ ] A coverage-and-limits statement is present, naming lenses that did not run and why (SC-003)
- [ ] A recommended verdict is present, marked as a recommendation
- [ ] Nothing is pre-selected in the selection prompt (FR-023)

**Then exercise the gates in this order:**

| Check | Input | Expected |
|---|---|---|
| Empty selection publishes nothing | press enter / `none` | Nothing posted; run ends as a success (FR-023) |
| Both lists stated | re-run, select `1,2` | Accepted **and** dropped both listed before proceeding (FR-025) |
| Agent does not choose the verdict | proceed to verdict | You are asked; no verdict pre-applied (FR-027) |
| Preview before posting | choose `comment` | Exact body shown; nothing posted yet (FR-031) |
| Abort at the final gate | decline | Nothing posted (FR-031) |
| Publish | accept | One review appears on the PR; URL returned (FR-033) |

**Then verify the published review on GitHub:**

- [ ] Exactly **one** review event was created, not several
- [ ] Only the selected findings appear — no dropped ones
- [ ] The disclosure line is present (FR-034)
- [ ] The machine anchor comment `<!-- spectra:review-pr revision=... -->` is present with the full SHA
- [ ] The coverage statement is present

---

## Scenario 2 — the blocker override path (FR-028, SC-009)

On a PR where the agent raised at least one blocker:

1. Select the blocker.
2. Choose **approve**.

**Expected**: the agent states the contradiction, requires a **typed** confirmation rather than accepting
a bare "yes", and — on confirmation — the published body contains the `## Acknowledged blocker — approved
over` section naming that finding.

- [ ] A bare `yes` is **not** accepted as the confirmation
- [ ] The choice is not refused outright (FR-028 forbids that too)
- [ ] The acknowledgement appears in the published body

This is the single highest-consequence path in the feature: an approval can satisfy branch protection
and unblock a merge.

---

## Scenario 3 — Story 2: discovery with no argument (P2)

```text
Run the command with no arguments.
```

- [ ] With an open PR on the current branch, that one is offered **first** rather than a full list
- [ ] Otherwise open PRs are listed with number, title, author, and target branch
- [ ] Nothing is reviewed until you choose explicitly (FR-004)
- [ ] In a repo with no open PRs, it says so and stops **without an error**

---

## Scenario 4 — Story 3: no spec (P3)

Point the command at a PR with no spec, in a repo that *does* have a constitution on the base branch.

- [ ] The summary states no spec was found and that the change was reviewed standalone
- [ ] Traceability is listed as **not run** — and never as passed (FR-012, SC-003)
- [ ] Guardrail findings are still produced, still quoting their clause (FR-012)
- [ ] No intent-class observation is rated blocker or major — all capped at Question

Then verify the three-tier discovery chain from FR-006a explicitly:

| Tier | Setup | Expected `discoverySource` |
|---|---|---|
| 1 | PR's diff contains `specs/<dir>/spec.md` | `diff` |
| 2 | No spec in diff, but `.specify/feature.json` present at head | `feature-record` |
| 3 | Neither | `none` → Story 3 behaviour |

- [ ] Which tier resolved is stated in the output
- [ ] Branch name is **not** used to locate the spec, even when it would have worked

---

## Scenario 5 — Story 4: delta re-review (P4)

1. Review a PR and publish.
2. Have new commits pushed to it.
3. Re-run with `--since <the earlier revision>`.

- [ ] Findings are scoped to the delta
- [ ] **Both** revisions are stated
- [ ] Previously published findings are sorted into apparently-resolved and still-open
- [ ] No resolution is asserted that cannot be evidenced
- [ ] The prior findings came from reading the earlier review off the PR — confirm no local file was
      written anywhere (FR-026, R-008)
- [ ] On a PR with no readable prior review, it says so and reports the delta alone

---

## Scenario 6 — the hard pre-flight gate (FR-001, SC-011)

Simulate each failure separately; they must produce **different** messages.

```bash
# (a) gh not on PATH — run in a shell with PATH stripped of gh
env PATH=/usr/bin:/bin <invoke the command>

# (b) gh present but unauthenticated
GH_TOKEN="" GITHUB_TOKEN="" gh auth logout   # then invoke; re-login afterwards
```

- [ ] Both stop **before any analysis** — no findings, no diff fetched
- [ ] (a) names the missing binary; (b) names the missing authentication and states `gh auth login`
- [ ] Neither degrades into a partial review — this is a hard stop, unlike `create-pr`

---

## Scenario 7 — degradation after pre-flight passed (FR-035)

Use a fork PR, or a repository where you lack review permission.

- [ ] The fork is noted **upfront**, before analysis, to set expectations
- [ ] The full review still runs
- [ ] On the publication failure, the rendered body is handed over for manual posting
- [ ] What failed is explained
- [ ] **No partial review is left on the PR**

---

## Scenario 8 — the remaining edge cases

| Edge case | Expected |
|---|---|
| Reviewer is the author | Explains self-approval is unavailable; offers the other two verdicts; does not attempt approve (FR-029) |
| New commits land mid-session | Revision re-checked before publishing; warns and offers re-analysis; does **not** publish (FR-032) |
| Own review already exists | Surfaces it; asks supersede or add (FR-036) |
| Oversized diff (>40 files or >1,500 lines) | Never refuses; risk-ranks; names what was skipped; may raise size as a finding (FR-013, SC-013) |
| PR modifies the constitution or an ADR | Surfaced as a governance change regardless of severity (FR-009) |
| Draft PR | Draft state reported; not declined |
| Generated files in the diff | Excluded and **named** as excluded (FR-014) |
| Empty or trivial diff | Reported as such; **no findings manufactured** |
| Local checkout on another branch | Context read at the PR's revision; working tree untouched (FR-006, FR-007) |

---

## Scenario 9 — Cross-repo review from an unrelated directory (regression guard)

**This is the scenario that caught the placeholder defect.** Run it first on any change to how artifacts
are fetched. A reviewer normally reviews someone else's PR, frequently in a project they have no clone
of, so this is the common path rather than an exotic one.

```bash
cd /some/completely/unrelated/git/repo      # NOT a clone of the reviewed project
# then invoke the command with a PR URL from a different repository that carries a spec
```

- [ ] The summary names the correct PR — number, title, author, branches — from the **target** repo
- [ ] The head revision reported matches the PR's actual `headRefOid`
- [ ] The spec is **found**, and the coverage statement names which discovery tier resolved it
- [ ] The constitution is read from the target repo's base branch, and guardrail findings are produced
- [ ] The coverage statement does **not** claim "no spec found"

That last box is the whole point. The failure mode is not a crash — it is a review that looks complete
while having silently lost its authorizing context, reporting the loss as an honest absence. If the
command reports "no spec found" for a PR you know carries one, the repository is being resolved from your
working directory instead of from the pull request.

Also confirm the fork case, which is **not** a defect but is worth re-checking after any fetch change:

- [ ] A fork PR's artifacts read successfully via the base repository — a fork's head revision resolves
      there because forks share an object store, so no fork-specific handling is needed

---

## Behaviours that could not be verified without a live PR

Carried forward from research R-007. Confirm these during implementation and record the outcome:

- [ ] `gh pr review --request-changes` with an empty body — does `gh` reject it, and how?
- [ ] `gh pr review --approve` on your own PR — confirm GitHub returns 422, and confirm the message the
      command shows is intelligible rather than a raw API error
- [ ] `--body-file -` handles a long body containing backticks, quotes, and newlines without mangling

---

## Determinism check (SC-004)

Run the command twice against the **same** revision, selecting nothing both times.

- [ ] The same findings are produced
- [ ] Each finding gets the **same severity** on both runs

Severity drift here means the FR-016 rubric is being applied loosely, which undermines SC-004 and the
whole trust model. It is the most important non-obvious check in this guide.

---

## Cleanup

```bash
cd /tmp && rm -rf /tmp/review-pr-trial
```

Also delete or dismiss any test reviews left on real pull requests — they are visible to the author and
may satisfy branch protection.
