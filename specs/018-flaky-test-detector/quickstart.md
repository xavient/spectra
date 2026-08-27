# Quickstart: Validating Flaky Test Detector

**Feature**: `018-flaky-test-detector` | **Plan**: [plan.md](./plan.md)

How to prove the command works. The repository checks below are the Principle V sync gates CI enforces;
the scenarios are the manual pass that belongs in `test/README.md`, one per user story plus every
refusal path.

The unit tests assert that the command *states* its rules. Only this document verifies that an agent
*follows* them, which is why the destructive-looking scenarios (Gate 2, the guardrail block, the stale
plan) are the ones worth running by hand.

## Prerequisites

```bash
specify --version   # Spec Kit CLI on PATH
python3 --version   # for the two maintainer scripts under tools/
```

Note what is **not** on that list: no `gh`, no `git`, no network. This command gates on nothing, which is
itself worth confirming (Scenario 10).

You also need a **scratch project with a real test suite** and known flaky patterns. Build one, or copy
a small open-source repository and plant the patterns yourself:

| Plant this | To exercise |
|---|---|
| An unconditional sleep followed by an assertion | High confidence, timing category |
| An assertion against the current date/time | High confidence, non-determinism |
| A test reading module state another test writes | Medium confidence, isolation |
| A test calling a real network client | Medium confidence, external dependency |
| An unseeded random value in an assertion | Low or Medium, non-determinism |
| A stable, well-written test | Must **not** be flagged (SC-002) |

Keep it under version control so `git diff` and `git checkout .` give you a clean reset between runs.

---

## Repository-level checks (no project needed)

```bash
# 1. Roster, generated regions, prose blocks, and manifest all agree
python3 tools/generate_agent_docs.py --check

# 2. Package rebuilt and not drifted
python3 tools/build_package.py
git diff --stat docs/packages/spectra.zip

# 3. Version and command-count parity between manifest and catalog
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
    'version bumped to 1.11.0': ext_version == '1.11.0',
    'command count is 6': cat['provides']['commands'] == 6,
}
for name, passed in checks.items():
    print(('  PASS  ' if passed else '  FAIL  ') + name)
sys.exit(0 if all(checks.values()) else 1)
PY

# 4. The roster ships it and records its command
python3 - <<'PY'
import json
a = next(x for x in json.load(open('agents-list.json'))['agents'] if x['id'] == 'flaky-test-detector')
assert a['status'] == 'available', a['status']
assert a['command'] == 'speckit.spectra.flaky-test-detector', a.get('command')
print('roster OK:', a['title'], '→', a['command'])
PY

# 5. No template was registered, and none should have been (R-002)
grep -c 'flaky-test-analysis-template' spectra/extension.yml   # expect 0

# 6. CLI channel untouched (Principle VI)
git diff --exit-code VERSION && echo "VERSION untouched — correct, this is a catalog-channel change"

# 7. The suite, including the new flow test and the roster census
python3 -m unittest discover -s tests
```

**Expected**: all seven pass. Check 1 fails loudly if the `flaky-test-detector` prose block is missing
from `AGENTS_LIST.md` — automation asserts the block exists but can never write it, so it is the item
most likely to be forgotten.

---

## Install into a throwaway project

```bash
mkdir -p /tmp/flaky-trial && cd /tmp/flaky-trial
specify init .
specify extension add --dev /Users/alibahaloo/Projects/spectra/spectra
specify extension info spectra   # 6 commands, including speckit.spectra.flaky-test-detector
```

Copy your scratch test suite in, restart your coding agent, and confirm the trigger appears in its
command list. The trigger differs by agent — `/speckit-spectra-flaky-test-detector` on Claude,
`/speckit.spectra.flaky-test-detector` on kiro-cli.

---

## Scenario 1 — Story 1: find the flaky tests (P1, the MVP)

Run the command with no argument in the scratch project.

**Expect**: every suite named with framework and file count **before** any candidate; a table of
candidates with ID, test, file, confidence, and a concrete fix; a coverage statement; then the Gate 1
question.

**Verify**:

```bash
git status --porcelain    # must be empty — nothing written before Gate 1 (FR-022)
```

- Each row's test name and file exist, and the cited evidence is at the cited line (SC-002).
- The stable test you planted is **not** in the table.
- Rows are ordered High → Medium → Low (FR-016).
- No percentage or score appears anywhere (R-004).

## Scenario 2 — Story 2: the plan file (P1)

Answer yes at Gate 1.

**Expect**: the file at `.specify/memory/flaky-test-analysis.md`, then a message naming the path, saying
it is waiting on your review, and saying rows may be deleted.

**Verify** against [contracts/analysis-file.md](./contracts/analysis-file.md):

```bash
cat .specify/memory/flaky-test-analysis.md
ls .specify/memory/                       # exactly one flaky-test-analysis file (SC-010)
git status --porcelain                    # only that file — no test file touched yet
```

- All six header fields present, timestamp carries a zone, `Progress: 0 of N fixed`.
- `## Tasks`, `## Evidence`, `## Not analyzed` all present; every row `[ ]`; every ID resolves to an
  evidence entry.

## Scenario 3 — Story 3: prune, then fix (P1)

Delete two rows from the file — including one whose test you can watch — and save. Then approve Gate 2.

**Expect**: the agent re-reads the file, works the remaining rows in order, ticks each as it lands, and
closes with counts, files changed, and the uncommitted state.

**Verify** — this is the most important check in the document:

```bash
git diff --stat                                    # only test and test-support files (SC-005)
git diff | grep -nE '\.skip|\.only|xfail|@flaky|retries|sleep\(' # expect nothing added (SC-004)
git diff -- <the deleted rows' test files>         # expect empty (SC-007)
grep -c '^| \[x\]' .specify/memory/flaky-test-analysis.md
```

- No assertion deleted or loosened; no test skipped, marked expected-to-fail, or wrapped in a retry.
- The two pruned tests are untouched.
- Every `[x]` row corresponds to a real edit in the diff.
- Nothing committed: `git log --oneline -1` is unchanged.

## Scenario 4 — checkpointing survives an interruption (FR-034, SC-006)

Start a fix run over several items and interrupt the agent mid-way (close the session).

**Verify**:

```bash
grep -E '^\| \[(x| )\]' .specify/memory/flaky-test-analysis.md
grep 'Progress:' .specify/memory/flaky-test-analysis.md
```

Every fix already in the diff is `[x]`; every remaining item is `[ ]`; the progress count matches. A file
that says `0 of 7` while the diff holds three fixes is the regression this scenario exists to catch.

## Scenario 5 — Story 4: resume in a new session (P1)

Restart the agent and run the command again.

**Expect**: the state report first — generation date, scope, done/pending counts — then three choices,
and **no new analysis**. Choose continue; only the pending rows are worked, and no `[x]` row is re-opened.

## Scenario 6 — the stale-plan guard (FR-031a)

With pending rows in the file, hand-edit one of those tests to remove the flakiness yourself (delete the
sleep). Then resume and approve.

**Expect**: that row is left `[ ]` with an outcome entry saying the code moved on. The agent must not
apply the recorded fix to a test that no longer matches its evidence.

## Scenario 7 — Story 5: re-run when everything is done (P2)

Finish every item, then run the command again.

**Expect**: a report that the previous analysis is complete and a question before re-analyzing — not an
immediate analysis, and never a silent overwrite. Decline, and confirm the file is byte-identical.

## Scenario 8 — the narrowed-run disclosure (FR-029a)

With pending rows spanning two suites, run the command scoped to one of them and choose to re-analyze.

**Expect**: before anything is written, the agent names the pending rows falling outside the new scope and
waits. Decline, and the file is unchanged; accept, and the new file covers only the narrowed scope with
the dropped rows already disclosed.

## Scenario 9 — Story 6: nothing to act on (P3)

```bash
mkdir -p /tmp/flaky-empty && cd /tmp/flaky-empty && specify init .
```

Run in that empty project.

**Expect**: a report that no test suite was found, naming where it looked, then a clean stop — no file, no
further question. Then run in a project with a deliberately clean suite: suites and coverage reported,
zero candidates, and **no offer to create a plan**.

## Scenario 10 — the refusals

| Check | How | Expect |
|---|---|---|
| No execution | Watch the session; check for any test-runner or build invocation | None, at any point — including after applying a fix |
| No tool gate | Run with `gh` absent from `PATH` | Runs normally; `gh` is never mentioned |
| Guardrail binding | Add a rule to the project's `.specify/memory/constitution.md` that forbids the obvious remedy (e.g. "tests MUST NOT use mocking libraries"), then run a fix that needs it | Row left `[ ]`, that rule named as the reason (FR-033a) |
| No constitution | Delete the constitution and re-run | Proceeds on technical merit and says no project guardrails were found |
| Production remedy | Plant a flaky test whose real fix is in application code | Row left `[ ]`, with what would need to change and where |
| Unparseable file | Corrupt the `## Tasks` table, then run | Reports what could not be read, offers fresh analysis or stop, and **does not overwrite** |
| Missing directory | `rm -rf .specify/memory` and run | Reports what is missing and where the file would go; creates nothing |

## Scenario 11 — a monorepo with several languages

Run in a project with two suites in different languages.

**Expect**: both analyzed, one table, the file column disambiguating identically-named tests, and the
coverage statement naming both suites with separate file counts.

---

## Definition of done for this feature

- Every scenario above behaves as described.
- All seven repository checks pass.
- `python3 -m unittest discover -s tests` is green, including the new flow test.
- `test/README.md` carries the manual pass so the next person can repeat it.
