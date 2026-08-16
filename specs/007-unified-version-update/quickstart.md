# Quickstart — validating Unified Version & Update

**Feature**: `007-unified-version-update` | **Date**: 2026-08-16

How to prove the feature works. Every scenario maps to a spec requirement and states its expected
outcome and exit code. Details of the structures and per-component mechanics live in
[data-model.md](data-model.md) and [contracts/health-check.md](contracts/health-check.md).

## Prerequisites

```bash
cd /Users/alibahaloo/Projects/spectra
pip install -e .                 # puts `spectra` on PATH from this working tree
specify --version                # Spec Kit CLI must be installed
```

On this machine the interpreter is `python3`; bare `python` is not on `PATH`. CI provides `python` via
`actions/setup-python`, so workflow snippets use `python` while the local commands below use `python3`.

Check the exit code after each run — several scenarios differ only in exit status:

```bash
spectra version; echo "exit=$?"
```

## Automated suite

Baseline before any change: **259 tests, OK**.

```bash
python3 -m unittest discover -s tests -v          # everything
python3 -m unittest tests.test_health -v          # the new module
python3 -m unittest tests.test_version_update -v  # the two rewritten commands
python3 -m unittest tests.test_cli_surface -v     # retirements and help panels
```

The suite is standard-library `unittest` with no third-party runner, and must stay green on Python 3.9
and 3.12 (the CI matrix).

---

## Scenario 1 — the four-component report (US1, FR-001…FR-007)

```bash
spectra version
```

**Expect** four rows in canonical order, each with a glyph, a status phrase, and version(s):

```text
Specify CLI:     ✓ up to date (0.16.4)
Core agents:     ! needs updating (0.12.14 → 0.16.4)
Spectra CLI:     ✓ up to date (6.0.0)
Spectra agents:  ✓ up to date (1.3.1)

You can update by running: spectra update
```

**Exit 0.** A verdict is a success, out-of-date included.

> This repository is itself a live fixture for the Core agents row: `.specify/integration.json` records
> `0.12.14` while the installed CLI is `0.16.4`. The row should read `needs updating` — and nothing in
> Spectra told you that before this feature.

Verify the hint appears **only** when something is behind (FR-003): once everything is current, the
final two lines must be absent.

## Scenario 2 — project preconditions (FR-022, clarification 1)

```bash
cd "$(mktemp -d)" && spectra version; echo "exit=$?"
```

**Expect** no table at all, a message naming `specify init`, **exit 5**.

```bash
mkdir -p /tmp/sk-empty/.specify && cd /tmp/sk-empty && spectra version; echo "exit=$?"
```

**Expect** no table, a message naming `spectra install`, **exit 5**. The two states must read
differently — same exit code, different remedy.

## Scenario 3 — `specify` absent (US1 #5, FR-017, FR-025)

```bash
env PATH="/usr/bin:/bin" spectra version; echo "exit=$?"
```

**Expect** the first two rows `unknown` with explanations, the last two still reporting normally, and
**exit 0**. The Core agents detail must say the Specify CLI version is unknown rather than implying the
integration file was the problem.

## Scenario 4 — malformed integration file (US1 #6, FR-018)

```bash
cp .specify/integration.json /tmp/integration.bak
echo '{ not json' > .specify/integration.json
spectra version; echo "exit=$?"
cp /tmp/integration.bak .specify/integration.json    # restore
```

**Expect** Core agents `unknown`; the other three rows unaffected; **exit 0**. Repeat with the file
deleted, and with `version` removed from the JSON — all three degrade identically.

## Scenario 5 — offline (US1 #4, FR-026)

Disable networking, or point the published-data base at a closed port:

```bash
SPECTRA_RAW_BASE=http://127.0.0.1:9 spectra version; echo "exit=$?"
```

**Expect** rows whose latest cannot be resolved show `unknown` **but still print their locally-readable
installed version**, and **exit 0** — not exit 3. This is the deliberate behavior change from the old
single-component command, which failed outright when the published version was unreachable.

## Scenario 6 — `--no-update-check` (US1 #7, FR-016)

```bash
spectra version --no-update-check
SPECTRA_NO_UPDATE_CHECK=1 spectra version
```

**Expect** identical output from both. The Spectra CLI row reports `unknown` with a detail naming the
skipped check; the other three rows are unaffected — in particular `specify self check` still runs, so
the first two rows keep their verdicts.

## Scenario 7 — update with nothing to do (US2 #1, FR-021)

```bash
spectra update; echo "exit=$?"
```

With everything current: **expect** the status table, an "everything is up to date" line, **no prompt**,
and **exit 0**.

## Scenario 7b — update with nothing *checkable* (US2 #12, #13, FR-027)

```bash
env PATH="/usr/bin:/bin" SPECTRA_RAW_BASE=http://127.0.0.1:9 spectra update; echo "exit=$?"
```

With every component unknown: **expect** a message stating nothing could be checked, the unverified
components named, **no claim that everything is up to date**, no prompt, and **exit 0**.

Then the partial case — network up, `specify` absent:

```bash
env PATH="/usr/bin:/bin" spectra update; echo "exit=$?"
```

**Expect** the output to report what is current *and* name the components that could not be checked. The
distinction from Scenario 7 is the whole point: exit 0 must not be allowed to imply "verified current"
when nothing was verified.

## Scenario 8 — update with work to do (US2 #2…#6, FR-008, FR-011)

```bash
spectra update
```

**Expect** only `needs updating` components listed, one prompt covering all of them, and updates running
in order Specify CLI → Core agents → Spectra CLI → Spectra agents.

- Answer `n` → nothing changes, **exit 1**.
- Answer `y` → updates run, then a four-row final report.
- `spectra update --yes` → no prompt at all.

Confirm a component whose status is `unknown` does **not** appear in the prompt list (FR-024).

## Scenario 9 — partial failure (US2 #4, US4 #3, FR-009, FR-012)

Best exercised through the suite, which mocks each delegate independently:

```bash
python3 -m unittest tests.test_version_update -v -k partial
```

**Expect**: with an early component's update forced to fail, later components are **still attempted**;
the final report shows per-component outcomes; **exit 4**. The failure detail must carry the exit code
or error text, not just the word "failed".

## Scenario 10 — skips do not fail the run (FR-023, clarification 2)

```bash
python3 -m unittest tests.test_version_update -v -k skip
```

**Expect** a run where every attempted update succeeds but another component is `unknown` to exit **0**.
A skipped component is neither success nor failure.

## Scenario 11 — retired subcommands (US3, FR-013, FR-014)

```bash
spectra cli version; echo "exit=$?"
spectra cli update;  echo "exit=$?"
```

**Expect** each to print a retirement message naming its replacement and **exit 2**, without performing
the action. Then confirm the survivor is untouched (FR-015):

```bash
spectra cli uninstall --help
```

## Scenario 12 — help surface (US3 #4, #5, FR-019, FR-020)

```bash
spectra --help
spectra cli; echo "exit=$?"
```

**Expect** the Tool commands panel to list only `uninstall`; no `cli version` or `cli update` anywhere in
the output; and the `version` / `update` descriptions to describe the whole stack rather than "the agents
installed here". Bare `spectra cli` prints group help and **exits 2**.

## Scenario 13 — update order (US4 #1, #2)

```bash
python3 -m unittest tests.test_version_update -v -k order
```

**Expect** recorded call order to be exactly Specify CLI → Core agents → Spectra CLI → Spectra agents,
and, when only a subset is out of date, the relative order of that subset preserved.

## Scenario 14 — CI parity assertion still holds (R3)

The retirement removes the command CI used for this, so verify the replacement locally:

```bash
python3 -c 'import importlib.metadata as m; print(m.version("spectra-cli"))'
tr -d '[:space:]' < VERSION
```

**Expect** the two to match. Then confirm `.github/workflows/ci.yml` no longer references
`spectra cli version` anywhere:

```bash
grep -n "cli version" .github/workflows/ci.yml    # expect no matches
```

Finally confirm the R8 replacement works from an arbitrary directory, which is what the release
smoke-test and clean-room row 10 now depend on:

```bash
cd "$(mktemp -d)" && SPECTRA_NO_UPDATE_CHECK=1 spectra | grep -i 'cli v'
ls -A | wc -l          # expect 0 — bare spectra must still touch nothing
```

## Scenario 15 — interruption (contracts/health-check.md)

Run `spectra update` with work to do and press Ctrl-C during a delegated step.

**Expect** the walk to **stop** rather than continue to the next component, and **exit 130**.
Cancellation is not a partial failure.

---

## Definition of done

| # | Check | Requirement |
| --- | --- | --- |
| 1 | Four rows reported in one invocation | FR-001, SC-001 |
| 2 | Preconditions exit 5 with the right remedy | FR-022 |
| 3 | `specify` absent degrades two rows only | FR-017, FR-025 |
| 4 | Malformed/missing integration file degrades one row | FR-018 |
| 5 | Offline keeps installed versions and exits 0 | FR-026 |
| 6 | `--no-update-check` suppresses one lookup only | FR-016 |
| 7 | No-op update exits 0 without prompting | FR-021 |
| 7b | No-op-because-unverified reads differently from no-op-because-current | FR-027 |
| 8 | One prompt; `--yes` skips; decline exits 1 | FR-011, SC-002 |
| 9 | Partial failure continues and exits 4 | FR-009, FR-012, SC-003 |
| 10 | Skips never fail the run | FR-023 |
| 11 | Retired subcommands exit 2 naming replacements | FR-013, FR-014, SC-004 |
| 12 | Help shows only `cli uninstall` | FR-019, FR-020 |
| 13 | Update order preserved | FR-008 |
| 14 | CI parity assertion moved and passing | R3 |
| 15 | Ctrl-C stops the walk, exits 130 | — |
| 16 | Full suite green on 3.9 and 3.12 | SC-005, SC-006 |
| 17 | No stale references to the retired commands survive anywhere in the repo | R8, T076 |
