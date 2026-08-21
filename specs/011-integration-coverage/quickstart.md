# Quickstart — validating Full Integration Coverage

**Feature**: `011-integration-coverage` | **Date**: 2026-08-20

How to prove the feature works. Every scenario maps to a user story and requirement and states its
expected output and exit code. Structure and mechanics live in [data-model.md](data-model.md),
[contracts/coverage.md](contracts/coverage.md), and
[contracts/cli-surface.md](contracts/cli-surface.md).

## Prerequisites

```bash
cd /Users/alibahaloo/Projects/spectra
pip install -e .                 # puts `spectra` on PATH from this working tree
specify --version                # Spec Kit CLI must be installed (0.16.5 when this was written)
```

On this machine the interpreter is `python3`; bare `python` is not on `PATH`. CI provides `python` via
`actions/setup-python`.

Check the exit code after every run — several scenarios differ only in exit status:

```bash
spectra install; echo "exit=$?"
```

## Automated suite

Baseline before any change: **455 tests, OK** (measured 2026-08-20).

```bash
python3 -m unittest discover -s tests             # everything
python3 -m unittest tests.test_coverage -v        # detection, plan, rotation, restoration (NEW)
python3 -m unittest tests.test_install -v         # install's step 4 and already-present path (NEW)
python3 -m unittest tests.test_version_update -v  # the update's coverage question and outcome row
python3 -m unittest tests.test_cli_surface -v     # no new flag; help output unchanged
python3 -m unittest tests.test_no_hardcoded_agents -v  # no integration key literals in coverage.py
```

A run that adds tests but leaves the total at 455 has not exercised anything new.

---

## Building a two-integration project by hand

Every manual scenario needs one. This is the fixture, and it is disposable:

```bash
WORK=$(mktemp -d) && cd "$WORK"
specify init probe --integration kiro-cli --script sh --non-interactive --ignore-agent-tools
cd probe
specify integration install claude --force        # second integration; default stays kiro-cli
python3 - <<'EOF'
import json
print("installed:", json.load(open('.specify/integration.json'))['installed_integrations'])
print("default:  ", json.load(open('.specify/integration.json'))['default_integration'])
EOF
```

Two helpers used throughout:

```bash
# who has Spectra's commands, per the registry
coverage() { python3 -c "import json;d=json.load(open('.specify/extensions/.registry'));\
print(sorted(d['extensions']['spectra']['registered_commands']))"; }

# the recorded default
default() { python3 -c "import json;print(json.load(open('.specify/integration.json'))['default_integration'])"; }
```

Remove the fixture when done: `rm -rf "$WORK"`.

---

## Scenario 1 — Install covers every agent (Story 1, FR-003/FR-014/FR-015)

In the two-integration project above:

```bash
spectra install; echo "exit=$?"
coverage; default
```

Expected:

- Step `[4/4] Registering Spectra with your other agents` appears.
- Before any activation, the output states that the default moves transiently and **names `kiro-cli`** as
  the default it will restore.
- One line per activation, then `✓ default restored to kiro-cli`.
- `coverage` prints `['claude', 'kiro-cli']`.
- `default` prints `kiro-cli`.
- `exit=0`.

Then check the files the whole team shares are untouched (FR-043, SC-013):

```bash
git -C . diff --stat .specify/integration.json .specify/init-options.json   # if the project is a repo
```

Expected: no output. A diff here is a defect, not a cosmetic difference (FR-044).

## Scenario 2 — Re-running install repairs a partially covered project (Story 3, FR-020/FR-021)

Break coverage the way the dependency does, then repair it:

```bash
specify extension remove spectra --force     # clears both agents
specify extension add spectra                # re-registers the default only
coverage                                     # ['kiro-cli']
spectra install; echo "exit=$?"
coverage                                      # ['claude', 'kiro-cli']
```

Expected:

- `✓ Spectra is already installed here (…) — nothing to download.`
- The extension folder's modification time is unchanged — nothing was re-downloaded (FR-023).
- `exit=0`. Under the previous release this run exited non-zero and covered nothing.

## Scenario 3 — Single-integration projects are untouched (Story 5, FR-038, SC-006)

```bash
cd "$WORK" && specify init solo --integration kiro-cli --script sh --non-interactive --ignore-agent-tools
cd solo && spectra install > after.txt; echo "exit=$?"
spectra install < /dev/null > noninteractive.txt; echo "exit=$?"
```

Expected: `after.txt` shows `[1/3]`…`[3/3]` and **no** step 4, no disclosure, no activation. Diff it
against the same run on the previous release; the only permitted differences are version numbers.
`noninteractive.txt` matches it — a run with no terminal attached behaves the same, and in a
*multi*-integration project it performs the coverage step rather than withholding it (FR-019).

## Scenario 4 — Update keeps coverage (Story 2, FR-024/FR-025/FR-027)

With both agents covered, force the extension to look behind, then update:

```bash
python3 - <<'EOF'
import re, pathlib
p = pathlib.Path('.specify/extensions/spectra/extension.yml')
p.write_text(re.sub(r'^  version: .*$', '  version: "0.0.1"', p.read_text(), count=1, flags=re.M))
EOF
spectra update            # answer y at the coverage question
coverage; default
```

Expected:

- The four component rows appear as today, then an `Agent coverage:` row group with one child line per
  integration.
- `coverage` still prints both agents — under the previous release the extension update deleted
  `claude`'s commands.
- `default` prints `kiro-cli`.

Repeat with `--yes` (no prompt, FR-027), and once answering `n`:

```bash
spectra update --yes; echo "exit=$?"
spectra update       # answer n
coverage; default; echo "exit=$?"
```

Expected for the declined run: nothing activated, `claude` named as left uncovered with `spectra install`
as the remedy, default unchanged, and the exit code **not** turned into a failure by the decline
(FR-029).

## Scenario 5 — Non-interactive update authorizes nothing (Story 2 scenario 5, FR-028)

```bash
spectra update < /dev/null; echo "exit=$?"
coverage
```

Expected: no activation, a skip line naming `--yes` as what would authorize it, and coverage unchanged.

## Scenario 6 — Interrupt mid-rotation still restores the default (Story 4, FR-016)

With three integrations installed and two uncovered, interrupt during the second activation:

```bash
specify integration install copilot --force
spectra install                     # press Ctrl-C while it works on the second agent
default; coverage; echo "exit=$?"
```

Expected: `default` prints `kiro-cli`, the integration covered before the interrupt is still covered,
the run reports an **interruption** rather than a failure, and `exit=130`.

Then prove the interrupted state is repairable, not merely tidy (SC-010):

```bash
spectra install; echo "exit=$?"
coverage; default
```

Expected: coverage completes for every integration, `default` still prints `kiro-cli`, and `exit=0`.

## Scenario 7 — A failed restore names the recovery command (Story 4 scenario 3, FR-034)

Simulated rather than provoked — make the restoring activation fail by putting a stub `specify` earlier on
`PATH` that fails only for `integration use kiro-cli`. Expected output:

```text
✗ Could not set the default integration back to kiro-cli.
  The project is currently defaulted to claude.
  Restore it with: specify integration use kiro-cli
```

with `exit=4`. This is the only place the dependency's `integration use` is printed as advice.

## Scenario 8 — The advisory now points at `spectra install` (Story 6, FR-039/FR-040)

```bash
specify extension remove spectra --force && specify extension add spectra
spectra version; echo "exit=$?"
```

Expected: the advisory below the four rows names `claude` and says `Add them with: spectra install`. The
old two lines about changing the project's default for everyone are **gone**. `exit=0` — the advisory
never affects the exit code (FR-042).

## Scenario 9 — Coverage is unknown, so nothing is claimed (FR-003/FR-004)

```bash
printf '{ not json' > .specify/extensions/.registry
spectra install; echo "exit=$?"
spectra version
```

Expected: no activation, no advisory, no claim in either direction; the install exits 0 having stated that
the registration state could not be read.

---

## Containerized end-to-end

The harness in [`test/`](../../test) builds a clean machine and installs the working copy exactly as `uv`
would. Two scenarios are added there (research R9, R10):

```bash
test/run.sh stack                  # ready project + scenario helpers
# inside: build a second integration, then
spectra install                    # coverage across both agents, real Spec Kit
```

The added scenario must assert:

1. both agents' command directories are populated after `spectra install`, and still populated after
   `spectra update`; and
2. `.specify/integration.json` and `.specify/init-options.json` are **byte-identical** to snapshots taken
   before the run (FR-044, SC-013).

Item 2 is the gate on the feature's central promise. If it cannot be made to pass, FR-044's fallback
applies and the coverage step becomes declinable in the install too.

---

## Requirement coverage map

| Scenario | Story | Requirements |
| --- | --- | --- |
| 1 | 1 | FR-001–FR-008, FR-014–FR-018, FR-033, FR-043 |
| 2 | 3 | FR-020–FR-023 |
| 3 | 5 | FR-019, FR-037, FR-038, SC-006, SC-011 |
| 4 | 2 | FR-024–FR-027, FR-029–FR-032 |
| 5 | 2 | FR-028 |
| 6 | 4 | FR-016, FR-036, SC-010 |
| 7 | 4 | FR-034, FR-015 |
| 8 | 6 | FR-039–FR-042 |
| 9 | — | FR-003, FR-004, FR-011 |
| container | 1, 2 | FR-006, FR-044, SC-013 |
