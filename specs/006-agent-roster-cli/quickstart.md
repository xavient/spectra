# Quickstart — validating this feature

Runnable checks that prove the feature works end to end. Each maps to the user story or requirement it
proves. Run from the repository root on branch `006-agent-roster-cli` unless stated otherwise.

## Prerequisites

```bash
python3 --version          # >= 3.9
specify --version          # Spec Kit CLI on PATH
uv --version               # only needed for the `cli` group checks
```

No dependencies to install — everything here is standard library. That is itself a check: if a step asks
you to `pip install` something, the zero-dependency constraint has been broken.

---

## 1. The generator is deterministic and stays in its lane

Proves FR-011, FR-015, FR-016, SC-011, and User Story 4 scenarios 5 and 6.

```bash
python tools/generate_agent_docs.py
git diff --exit-code README.md AGENTS_LIST.md    # committed output is current: no diff

python tools/generate_agent_docs.py              # run it a second time
git diff --exit-code README.md AGENTS_LIST.md    # still no diff: deterministic
```

Then prove it leaves prose alone:

```bash
python - <<'PY'
import pathlib, re
p = pathlib.Path("AGENTS_LIST.md"); t = p.read_text()
# everything outside generated regions must survive a run untouched
outside = re.sub(r"<!-- SPECTRA:GENERATED START.*?<!-- SPECTRA:GENERATED END id=[^>]+ -->", "", t, flags=re.S)
pathlib.Path("/tmp/outside-before.txt").write_text(outside)
PY
python tools/generate_agent_docs.py
# regenerate the same extract and compare
diff /tmp/outside-before.txt <(python - <<'PY'
import pathlib, re
t = pathlib.Path("AGENTS_LIST.md").read_text()
print(re.sub(r"<!-- SPECTRA:GENERATED START.*?<!-- SPECTRA:GENERATED END id=[^>]+ -->", "", t, flags=re.S), end="")
PY
)
```

Expected: no output from `diff`.

## 2. Every verification failure is caught, and names the culprit

Proves FR-017, FR-018, FR-019, FR-019a, FR-020, SC-006, and User Story 4 scenarios 2, 3, 4, 7, 8, 9.
Each step ends by restoring the file, so run them one at a time.

```bash
# a) a hand-edit to a generated region
python - <<'PY'
import pathlib
p = pathlib.Path("README.md"); t = p.read_text()
p.write_text(t.replace("| Guardrails |", "| Guardrails EDITED |", 1))
PY
python tools/generate_agent_docs.py --check   # must FAIL and name README.md
git checkout README.md

# b) a shipped agent with no prose block
python - <<'PY'
import pathlib
p = pathlib.Path("AGENTS_LIST.md"); t = p.read_text()
p.write_text(t.replace("<!-- SPECTRA:AGENT id=adr -->", "", 1))
PY
python tools/generate_agent_docs.py --check   # must FAIL and name `adr`
git checkout AGENTS_LIST.md

# c) an orphan prose anchor
python - <<'PY'
import pathlib
p = pathlib.Path("AGENTS_LIST.md")
p.write_text(p.read_text() + "\n<!-- SPECTRA:AGENT id=not-a-real-agent -->\n### Ghost\n")
PY
python tools/generate_agent_docs.py --check   # must FAIL and name `not-a-real-agent`
git checkout AGENTS_LIST.md

# d) roster and manifest disagree on the command
python - <<'PY'
import json, pathlib
p = pathlib.Path("agents-list.json"); d = json.loads(p.read_text())
for a in d["agents"]:
    if a["id"] == "adr": a["command"] = "speckit.spectra.wrong"
p.write_text(json.dumps(d, indent=2) + "\n")
PY
python tools/generate_agent_docs.py --check   # must FAIL naming `adr` and both command strings
git checkout agents-list.json

# e) a malformed marker
python - <<'PY'
import pathlib
p = pathlib.Path("README.md")
p.write_text(p.read_text().replace(
    "<!-- SPECTRA:GENERATED END id=readme-agents-table -->", "", 1))
PY
python tools/generate_agent_docs.py           # must FAIL naming README.md and the marker
git diff --stat README.md                     # and must NOT have rewritten the file
git checkout README.md
```

Then prove the deliberate non-check:

```bash
# f) a description that differs from the manifest's must PASS
python - <<'PY'
import json, pathlib
p = pathlib.Path("agents-list.json"); d = json.loads(p.read_text())
for a in d["agents"]:
    if a["id"] == "adr": a["description"] = "Completely different wording, deliberately."
p.write_text(json.dumps(d, indent=2) + "\n")
PY
python tools/generate_agent_docs.py --check   # must PASS (FR-019a)
git checkout agents-list.json
```

## 3. Renaming a title breaks nothing

Proves FR-003b, FR-010, SC-005, and User Story 4 scenario 13.

```bash
python - <<'PY'
import json, pathlib
p = pathlib.Path("agents-list.json"); d = json.loads(p.read_text())
for a in d["agents"]:
    if a["id"] == "create-pr": a["title"] = "GitHub Pull Requests"
p.write_text(json.dumps(d, indent=2) + "\n")
PY
python tools/generate_agent_docs.py
grep -c "GitHub Pull Requests" README.md AGENTS_LIST.md   # both non-zero
grep -c "GitHub (PR)" README.md AGENTS_LIST.md            # both zero
python tools/generate_agent_docs.py --check               # still PASSES: prose matched by id
git checkout agents-list.json README.md AGENTS_LIST.md
```

## 4. Unit tests

Proves the module-level behaviour behind every FR, including the cases that are impractical to reach by
hand — timeouts, malformed manifests, schema-version gates.

```bash
python -m unittest discover -s tests -v
```

## 5. Discovery works with nothing installed

Proves User Story 1, FR-025, FR-026, FR-027, FR-042.

```bash
pip install .                      # or `uv tool install . --force`
cd /tmp && mkdir -p not-a-project && cd not-a-project
spectra agent-list                 # full roster; exit 0 outside any Spec Kit project
echo "exit=$?"
```

Confirm by eye: 44 agents grouped by SDLC phase; every row shows status, type, provider, and either a
command or "under development"; no planned agent shows a command.

Then prove the list is data, not code:

```bash
grep -rn "Domain Analyzer\|Threat Modeling\|Observability" spectra_cli/    # must find nothing
```

## 6. The four project states are distinguishable

Proves User Story 2, FR-028, FR-029, FR-044, FR-045, SC-009.

```bash
cd /tmp && rm -rf qs && mkdir qs && cd qs

# not a Spec Kit project
spectra check; echo "exit=$?"                 # expect 5, message names `specify init`

# a Spec Kit project without Spectra
specify init --here --force >/dev/null
spectra check; echo "exit=$?"                 # expect the install offer; decline -> 1

# incomplete install
mkdir -p .specify/extensions/spectra
spectra check; echo "exit=$?"                 # expect 5, message says interrupted install
rm -rf .specify/extensions/spectra

# installed
spectra install                               # accept the prompts
spectra check; echo "exit=$?"                 # expect 0
```

All four messages must be different sentences, not one sentence with a different noun.

## 7. Subdirectory behaviour

Proves FR-040, SC-012.

```bash
cd /tmp/qs && mkdir -p a/b/c && cd a/b/c
spectra check   && echo "check ok"
spectra version && echo "version ok"
```

Both must report on `/tmp/qs`, identically to running them at its root.

## 8. Staleness and the one-command fix

Proves User Story 3, FR-030, FR-031, FR-032, FR-032a, and SC-007.

```bash
cd /tmp/qs
# force a stale install
python - <<'PY'
import pathlib, re
p = pathlib.Path(".specify/extensions/spectra/extension.yml")
p.write_text(re.sub(r'^(  version: ")[^"]+(")', r'\g<1>0.0.1\g<2>', p.read_text(), count=1, flags=re.M))
PY
spectra version; echo "exit=$?"     # reports both versions, names `spectra update`, exit 0
spectra update                      # delegates to Spec Kit
spectra version; echo "exit=$?"     # up to date, exit 0
spectra update                      # already current: no changes, exit 0
```

Then the ahead case and the offline case:

```bash
python - <<'PY'
import pathlib, re
p = pathlib.Path(".specify/extensions/spectra/extension.yml")
p.write_text(re.sub(r'^(  version: ")[^"]+(")', r'\g<1>99.0.0\g<2>', p.read_text(), count=1, flags=re.M))
PY
spectra version; echo "exit=$?"     # "ahead of published", no update offered, exit 0

# offline: point the fetch at an unroutable host
SPECTRA_RAW_BASE=http://127.0.0.1:9 spectra version; echo "exit=$?"
```

The offline run must return within ~10 seconds, explain that the published version could not be fetched,
and exit 3 — never imply the agents are current (FR-041a, SC-013). Time it:

```bash
time SPECTRA_RAW_BASE=http://127.0.0.1:9 spectra agent-list
```

## 9. Schema tolerance

Proves FR-009a, FR-009b, and User Story 1 scenarios 7 and 8. Served locally rather than published:

```bash
mkdir -p /tmp/roster && cp agents-list.json /tmp/roster/
python - <<'PY'
import json, pathlib
p = pathlib.Path("/tmp/roster/agents-list.json"); d = json.loads(p.read_text())
d["schema_version"] = "1.99"
d["agents"][0]["some_future_field"] = "ignored"
p.write_text(json.dumps(d, indent=2))
PY
(cd /tmp/roster && python -m http.server 8931 >/dev/null 2>&1 &) ; sleep 1
SPECTRA_RAW_BASE=http://127.0.0.1:8931 spectra agent-list   # full list + "newer than this CLI" notice, exit 0

python - <<'PY'
import json, pathlib
p = pathlib.Path("/tmp/roster/agents-list.json"); d = json.loads(p.read_text())
d["schema_version"] = "2.0"; p.write_text(json.dumps(d, indent=2))
PY
SPECTRA_RAW_BASE=http://127.0.0.1:8931 spectra agent-list; echo "exit=$?"   # refuses, names `spectra cli update`, exit 3
```

## 10. The command surface reads correctly, and removed flags help

Proves User Story 5, FR-036, FR-038, FR-039, FR-043, FR-047, SC-008.

```bash
spectra --help                 # three panels: Project commands, Tool commands, Options
spectra cli version            # first line is the bare version
[ "$(spectra cli version | head -1)" = "$(tr -d '[:space:]' < VERSION)" ] && echo "parity ok"

for f in --version --update --uninstall; do
  spectra "$f"; echo "$f -> exit=$?"     # each: exit 2, message naming the replacement
done

cd /tmp && rm -rf bare && mkdir bare && cd bare
spectra > out.txt; echo "exit=$?"        # exit 0
grep -q "spectra --help" out.txt && echo "points at help"
[ -z "$(ls -A . | grep -v out.txt)" ] && echo "touched nothing"
```

## 11. Removing the agents leaves the tool alone

Proves User Story 6, FR-034, FR-035.

```bash
cd /tmp/qs
spectra uninstall              # Spec Kit prompts; confirm
spectra check; echo "exit=$?"  # not installed
spectra cli version            # the command itself still works
spectra uninstall; echo "exit=$?"   # idempotent: reports not installed, exit 0
```

## 12. Presentation agrees everywhere

Proves User Story 7, FR-051, FR-052, SC-010.

```bash
LINE="TELUS Digital - Agentic software engineering across the entire SDLC."
grep -c "$LINE" spectra/extension.yml catalog.json          # both 1
unzip -p docs/packages/spectra.zip spectra/extension.yml | grep -c "$LINE"   # 1
grep -c "$LINE" docs/index.html                             # 0 — the page fetches it
```

Then load the page and confirm the roster drives it:

```bash
(cd docs && python -m http.server 8932 >/dev/null 2>&1 &) ; sleep 1
open http://127.0.0.1:8932/     # or xdg-open
```

The Agents section must list agents fetched from `agents-list.json`, and the extension description must
match the line above without that line appearing in the HTML source.

## 13. Cross-platform and version floor

Proves FR-050. CI covers Python 3.9 and 3.12 on Linux; the container track covers a bare machine.

```bash
test/run.sh run        # bare-machine onboarding, exits with the install flow's code
```

Windows is verified by running steps 5–11 in PowerShell. Watch two things specifically: generated files
must not appear drifted (`git diff --exit-code` after a generator run — line endings are written `\n`), and
`spectra check` must resolve the project root from a nested path.

---

## Coverage map

| Step | Proves |
| --- | --- |
| 1 | US4 · FR-011, FR-015, FR-016 · SC-011 |
| 2 | US4 · FR-017, FR-018, FR-019, FR-019a, FR-020 · SC-006 |
| 3 | FR-003b, FR-010 · SC-005 |
| 4 | every module-level FR |
| 5 | US1 · FR-025, FR-026, FR-027, FR-042 |
| 6 | US2 · FR-028, FR-029, FR-044, FR-045 · SC-009 |
| 7 | FR-040 · SC-012 |
| 8 | US3 · FR-030–FR-032a, FR-041a · SC-007, SC-013 |
| 9 | US1 · FR-009a, FR-009b |
| 10 | US5 · FR-036, FR-038, FR-039, FR-043, FR-047 · SC-008 |
| 11 | US6 · FR-034, FR-035 |
| 12 | US7 · FR-051, FR-052 · SC-010 |
| 13 | FR-050 |

`SPECTRA_RAW_BASE` appears in steps 8 and 9 as the override that makes network failure and schema
tolerance testable without publishing anything. It is a test seam, and the only new environment variable
this feature introduces.
