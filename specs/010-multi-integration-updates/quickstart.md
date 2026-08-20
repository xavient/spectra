# Quickstart — validating Multi-Integration Stack Updates

**Feature**: `010-multi-integration-updates` | **Date**: 2026-08-20

How to prove the feature works. Every scenario maps to a user story and requirement, and states its
expected output and exit code. Structure and mechanics live in [data-model.md](data-model.md),
[contracts/core-agents.md](contracts/core-agents.md), and
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
spectra version; echo "exit=$?"
```

## Automated suite

Baseline before any change: **343 tests, OK** (measured 2026-08-20).

```bash
python3 -m unittest discover -s tests -v          # everything
python3 -m unittest tests.test_health -v          # enumeration, per-key reads, aggregation
python3 -m unittest tests.test_version_update -v  # report rows, walk, consent paths
python3 -m unittest tests.test_cli_surface -v     # --force placement and help text
```

Standard-library `unittest`, no third-party runner, green on Python 3.9 and 3.12 (the CI matrix).

---

## Fixtures

Everything below runs in a scratch directory. **Do not run the mutating scenarios against a real
project** — several of them deliberately overwrite managed files.

### F1 — a two-integration project

```bash
rm -rf /tmp/spectra-multi && mkdir -p /tmp/spectra-multi && cd /tmp/spectra-multi
specify init --here --integration kiro-cli --script sh --non-interactive
specify integration install claude
specify integration status --json | python3 -m json.tool | head -20
```

**Expect** `installed_integrations` containing both keys and `default_integration` at `kiro-cli`.

Then install Spectra so the four-row report is reachable:

```bash
specify extension catalog add \
  https://raw.githubusercontent.com/xavient/spectra/main/catalog.json \
  --name spectra --priority 5 --install-allowed
specify extension add spectra
```

### F2 — make one integration stale

The recorded per-integration version is what decides currency, so lowering one produces a behind
integration without touching any file the dependency will compare hashes against:

```bash
python3 - <<'PY'
import json, pathlib
p = pathlib.Path("/tmp/spectra-multi/.specify/integrations/claude.manifest.json")
d = json.loads(p.read_text())
d["version"] = "0.15.1"
p.write_text(json.dumps(d, indent=2) + "\n")
PY
```

### F3 — make managed files modified

```bash
printf '\n<!-- local edit -->\n' >> /tmp/spectra-multi/.specify/templates/spec-template.md
printf '\n<!-- local edit -->\n' >> /tmp/spectra-multi/.kiro/prompts/speckit.plan.md
specify integration status --json | python3 -c \
  'import json,sys; d=json.load(sys.stdin); print(d["status"], d["modified_managed_files"])'
```

**Expect** `warning 2`. Note the status command still **exits 0** — it is read-only and never gates
(finding F7):

```bash
specify integration status >/dev/null 2>&1; echo "exit=$?"    # expect exit=0
```

### F4 — a real drifted project, read-only

`~/Projects/willow` is the project the BRD measured: two integrations, recorded at `0.15.1` against a
`0.16.5` CLI, 23 modified managed files, Spectra commands registered for `kiro-cli` only. Use it for
**read-only** verification of Scenarios 1 and 9 — never for the mutating ones.

---

## Scenario 1 — the row tells the truth about every integration (US1, FR-001…FR-010)

```bash
cd /tmp/spectra-multi     # after F1 + F2
spectra version
```

**Expect** four rows, with `Core agents` behind, showing the **oldest** version and naming both keys:

```text
  Specify CLI:     ✓ up to date (0.16.5)
  Core agents:     ! needs updating (0.15.1 -> 0.16.5) — claude
                     kiro-cli:  ✓ up to date (0.16.5)
                     claude:    ! needs updating (0.15.1 -> 0.16.5)
  Spectra CLI:     ✓ up to date (6.1.0)
  Spectra agents:  ✓ up to date (1.3.1)
```

**Exit 0.** A verdict is a success, behind included.

The regression this scenario exists for: before the change, this same project reports
`Core agents: ✓ up to date`, because the project-level record is rewritten on any single upgrade
(finding F2).

## Scenario 2 — breakdown only when it earns its place (US1, FR-013, FR-012)

```bash
python3 - <<'PY'
import json, pathlib
p = pathlib.Path("/tmp/spectra-multi/.specify/integrations/claude.manifest.json")
d = json.loads(p.read_text()); d["version"] = "0.16.5"
p.write_text(json.dumps(d, indent=2) + "\n")
PY
spectra version
```

**Expect** a single `Core agents: ✓ up to date (0.16.5)` row and **no** child lines — the integrations
are uniform.

Then the single-integration guard (SC-005):

```bash
rm -rf /tmp/spectra-solo && mkdir -p /tmp/spectra-solo && cd /tmp/spectra-solo
specify init --here --integration kiro-cli --script sh --non-interactive
spectra version > /tmp/after.txt; echo "exit=$?"
```

**Expect** `/tmp/after.txt` to be byte-identical to the same command on the previous release. Capture the
before by installing the released CLI in a throwaway virtualenv:

```bash
python3 -m venv /tmp/prev && /tmp/prev/bin/pip -q install \
  "spectra-cli @ git+https://github.com/xavient/spectra@6.0.0"
(cd /tmp/spectra-solo && /tmp/prev/bin/spectra version > /tmp/before.txt)
diff /tmp/before.txt /tmp/after.txt && echo "IDENTICAL"
```

## Scenario 3 — unknown is never guessed (US1, FR-005, FR-010)

```bash
cd /tmp/spectra-multi
mv .specify/integrations/claude.manifest.json /tmp/claude.manifest.bak
spectra version
```

**Expect** `Core agents: – unknown (…)` naming `claude` as the integration that could not be
established, with `kiro-cli` still reported in the breakdown. **Not** `up to date` — rule 3 outranks
rule 5 (contracts/core-agents.md § 4).

```bash
mv /tmp/claude.manifest.bak .specify/integrations/claude.manifest.json
```

## Scenario 4 — one update, every integration (US2, FR-014…FR-018)

```bash
cd /tmp/spectra-multi     # after F2, clean managed files
python3 -c "import json;print(json.load(open('.specify/integration.json'))['default_integration'])"
spectra update --yes; echo "exit=$?"
```

**Expect** both integrations upgraded, each with its own outcome line, and the default **unchanged**:

```text
  Core agents:     ✓ updated (0.16.5)
                     claude:    ✓ updated (0.16.5)
```

```bash
python3 -c "import json;print(json.load(open('.specify/integration.json'))['default_integration'])"
```

**Expect** the same value printed before and after (FR-017). **Exit 0.**

Re-run `spectra version` and expect `Core agents: ✓ up to date` — the SC-001 round trip.

## Scenario 5 — informed consent before any overwrite (US3, FR-024…FR-029)

```bash
cd /tmp/spectra-multi     # after F2 + F3
spectra update
```

**Expect**, before any question: the affected files listed, grouped per integration and with shared
Spec Kit infrastructure as its own group; a closing sentence stating the two real options; and a prompt
whose default is **no**. Press Enter.

**Expect** nothing overwritten, the affected integrations reported
`– skipped (overwrite not authorized)`, and **exit 0** — a declined overwrite is not a failure (FR-030).

```bash
grep -c "local edit" .specify/templates/spec-template.md   # expect 1, still there
```

Then authorize:

```bash
spectra update --force --yes; echo "exit=$?"
grep -c "local edit" .specify/templates/spec-template.md   # expect 0, overwritten as disclosed
```

**Expect** the disclosure still printed even though nothing was asked (FR-032), the upgrade completed,
and **exit 0**.

## Scenario 6 — `--yes` is not consent (US4, FR-027, FR-031)

```bash
cd /tmp/spectra-multi     # re-apply F2 + F3 first
spectra update --yes < /dev/null; echo "exit=$?"
```

**Expect**: no file overwritten, the affected integrations skipped, the output naming `--force`, no hang
waiting for input, and **exit 0**.

```bash
grep -c "local edit" .specify/templates/spec-template.md   # expect 1
```

## Scenario 7 — an integration that needs nothing is left alone (US3, FR-034)

With only `claude` behind and only `kiro-cli`'s files modified:

```bash
spectra update --yes; echo "exit=$?"
```

**Expect** no disclosure and no prompt at all — `kiro-cli` is not being upgraded, so its modified files
are irrelevant to this run — and `claude` upgraded normally.

## Scenario 8 — flag placement (FR-028, contracts/cli-surface.md § 2)

```bash
spectra update --help | grep -A1 force        # expect the consequence-stating help line
spectra --force update; echo "exit=$?"        # expect the error path, exit=2
spectra uninstall --force; echo "exit=$?"     # expect exit=2 — --force is update-only
```

## Scenario 9 — the coverage advisory (US5, FR-036…FR-039)

```bash
cd /tmp/spectra-multi
python3 -c "
import json;d=json.load(open('.specify/extensions/.registry'))
print(list(d['extensions']['spectra']['registered_commands']))"
spectra version
```

**Expect** the advisory naming any installed integration missing from that list, the exact
`specify integration use <key>` remedy, the statement that it changes the project default, and **no
change** to any file. Exit code unaffected.

Then the silent case (FR-039):

```bash
mv .specify/extensions/.registry /tmp/registry.bak
spectra version          # expect no advisory at all, four rows unchanged
mv /tmp/registry.bak .specify/extensions/.registry
```

This is also the state of the Spectra repository itself — no `spectra` entry, because the repo is the
extension's source rather than a consumer — so `spectra version` here must never print an advisory.

## Scenario 10 — degradation and interruption (FR-019, FR-020, R6, R8)

```bash
# modification state unestablished: no `specify` on PATH for the probe
cd /tmp/spectra-multi
PATH=/usr/bin:/bin spectra update --yes; echo "exit=$?"
```

**Expect** `Specify CLI` and `Core agents` reported unknown and skipped rather than attempted, and
**exit 0** — nothing unknown is ever acted on (FR-018, FR-015).

```bash
# single-record fallback: an older project layout with no per-integration manifests
rm -rf /tmp/spectra-legacy && mkdir -p /tmp/spectra-legacy/.specify/memory
cat > /tmp/spectra-legacy/.specify/integration.json <<'JSON'
{ "version": "0.15.1", "integration": "kiro-cli" }
JSON
cd /tmp/spectra-legacy && spectra version
```

**Expect** one `Core agents` row judged from the project-level record, no breakdown, and no crash —
today's behaviour, preserved (R8).

Interruption: run `spectra update` on a two-integration project and press Ctrl-C while the **first**
integration is upgrading.

**Expect** the walk to stop, the completed integration reported, the second untouched, the default
unchanged, and **exit 130**.

---

## Cleanup

```bash
rm -rf /tmp/spectra-multi /tmp/spectra-solo /tmp/spectra-legacy /tmp/prev \
       /tmp/before.txt /tmp/after.txt
```

## Requirement coverage

| Scenario | Story | Requirements |
| --- | --- | --- |
| 1 | US1 | FR-001…FR-008, FR-010 |
| 2 | US1 | FR-012, FR-013, SC-005 |
| 3 | US1 | FR-005, FR-010 |
| 4 | US2 | FR-014…FR-018, FR-021, FR-022, SC-001 |
| 5 | US3 | FR-024…FR-030, FR-032, FR-035 |
| 6 | US4 | FR-027, FR-031, SC-007 |
| 7 | US3 | FR-034 |
| 8 | — | FR-028, FR-011 |
| 9 | US5 | FR-036…FR-040 |
| 10 | US2 | FR-015, FR-019, FR-020, FR-023, FR-041 |
