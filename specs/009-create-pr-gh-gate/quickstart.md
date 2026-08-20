# Quickstart: Validating the `create-pr` `gh` Gate

**Feature**: `009-create-pr-gh-gate` | **Date**: 2026-08-19

The deliverable is instructions, so validation is **executing the command and reading what it does**. Each
scenario below is a run, its expected observable behaviour, and the requirements it evidences.

Scenarios S2–S4 replace `specs/002-open-pr/quickstart.md` **S6** ("Graceful degradation"), which asserted
the superseded behaviour.

---

## Setup

```bash
# 1. A throwaway Spec Kit project with the working copy installed
specify init /tmp/spectra-gate --integration claude
cd /tmp/spectra-gate
specify extension add --dev /Users/alibahaloo/Projects/spectra/spectra

# 2. A spec branch to open a pull request from (one branch per spec)
mkdir -p specs/001-probe && printf '# Feature Specification: Probe\n' > specs/001-probe/spec.md
printf '{\n  "feature_directory": "specs/001-probe"\n}\n' > .specify/feature.json
git checkout -b 001-probe && git add -A && git commit -m "probe spec"

# 3. Restart the agent so it reloads the command, then run it as your agent registers it
#    Claude: /speckit-spectra-create-pr   ·   kiro-cli: /speckit.spectra.create-pr
```

**Two environment tricks are used below, both verified on `gh` 2.97.0 and both fully reversible** — neither
touches your real `gh` configuration:

| Simulation | Mechanism | Verified result |
|---|---|---|
| `gh` not installed | Start the agent with a `PATH` that excludes `gh` but keeps `git`: `mkdir -p /tmp/nogh/bin && ln -sf "$(command -v git)" /tmp/nogh/bin/git` then `env -i PATH=/tmp/nogh/bin:/usr/bin:/bin <agent>` | `command -v gh` exits 1; `git` still resolves |
| `gh` not authenticated | `GH_CONFIG_DIR=$(mktemp -d) GH_TOKEN= GITHUB_TOKEN= <agent>` | `gh auth status --hostname github.com` exits **1** with "You are not logged into any GitHub hosts. To log in, run: `gh auth login`" |

---

## S1 — Regression: the happy path is untouched

**Run** with `gh` installed and authenticated, on the spec branch, in a GitHub repository.

**Expect**: identical behaviour to before the change — the offer, the derived target with the rule that
produced it, confirmation before the push, confirmation before creation, and the pull-request URL in the
reply. The gate is invisible.

**Evidences**: FR-013, SC-007.

---

## S2 — `gh` is not installed: hard stop, install remedy

**Run** the command with `gh` off `PATH`, and accept the offer.

**Expect**:

1. The command stops **immediately after the go-ahead**.
2. The message says the GitHub CLI is not installed and points at <https://cli.github.com>.
3. It has **not** read the constitution or branching config, **not** derived a target branch, **not** run
   `git push`, and **not** opened anything.
4. The output contains **no `gh …` command line** — the only alternative route named is the GitHub web
   interface for the repository.

**Fail if**: a target branch is stated, a `gh pr create` line appears, or the run reads project context
before stopping.

**Evidences**: FR-001, FR-002, FR-003, FR-004, SC-001, SC-002, SC-003.

---

## S3 — `gh` is installed but not authenticated: a *different* message

**Run** with `GH_CONFIG_DIR` pointed at an empty directory and both token variables cleared.

**Expect**:

1. The same immediate stop, with no mutations.
2. The remedy is `gh auth login`, and the text is **visibly different** from S2 — a reader can tell which
   of the two failed without being told.
3. No target derivation, no push.

**Fail if**: the two runs produce interchangeable messages, or the command suggests installing `gh` that is
already installed.

**Evidences**: FR-001, FR-002, FR-004, SC-001, SC-002.

---

## S4 — The remote is not GitHub, or absent: a scope statement

**Run** twice: once with `git remote set-url origin https://gitlab.com/acme/api.git`, once with
`git remote remove origin`.

**Expect**:

1. Both stop.
2. Both state that this version supports GitHub only, and name what was found — the host, or the absence of
   a remote.
3. Neither prints a `gh` command, because none would help.
4. GitHub Enterprise, if mentioned, is named as unsupported rather than attempted.

**Evidences**: FR-006, SC-003.

---

## S5 — A refusal after the gate: degrade, and say what was mutated

**Run** against a repository where the outward action will be refused — a protected base branch, or an
account without push permission. Confirm the push and the creation.

**Expect**:

1. The run does **not** present itself as successful.
2. It names what failed, surfacing `gh`'s or `git`'s own message rather than a paraphrase.
3. It hands over the manual commands **including the derived base branch**.
4. It states the mutation state explicitly: "the branch is on the remote, no pull request exists" when the
   push landed and creation failed; "nothing reached the remote" when the push itself was refused.

**Fail if**: the failure is reported without saying whether the branch was pushed, or the manual command
omits the base branch.

**Evidences**: FR-010, FR-011, SC-004.

---

## S6 — Body fidelity: backticks, quotes, and newlines survive

**Prepare** a spec whose summary contains a code fence, inline backticks, a double quote, an apostrophe,
and a blank line. **Run** the command through to creation.

**Expect** the pull-request body to match the composed text exactly — no dropped fences, no shell-mangled
quotes, no collapsed newlines.

**Shortcut**: `gh pr create --dry-run` prints the details instead of creating the pull request (its help
notes it "May still push git changes"), which is enough to inspect the body without opening anything.

**Evidences**: FR-012, SC-005.

---

## S7 — Fork or several remotes: ask, never guess

**Run** in a fork with both `origin` and `upstream` configured.

**Expect**:

1. The command asks which remote and base to use rather than choosing.
2. The fork determination is stated as read from the repository (`isFork`), not deduced from the URL.
3. Nothing is deduped or created until the user answers.

**Evidences**: FR-007, FR-009.

---

## S8 — The repository's own checks

Run in the Spectra repository, not the throwaway project:

```bash
python tools/generate_agent_docs.py --check     # roster ↔ manifest ↔ prose agreement
python -m unittest discover -s tests            # full suite
# CI's catalog job, locally:
sed -n 's/^  version: "\(.*\)"$/\1/p' spectra/extension.yml | head -1
python3 -c 'import json;print(json.load(open("catalog.json"))["extensions"]["spectra"]["version"])'
python3 tools/build_package.py && unzip -q -o docs/packages/spectra.zip -d /tmp/unzipped && diff -r /tmp/unzipped/spectra spectra
```

**Expect**: the generator check passes, the suite passes, the two versions read `1.5.0`, and the zip diff is
empty.

**Evidences**: FR-014, FR-015, SC-006.

---

## S9 — Documentation consistency

Grep the shipped surface for the superseded claim:

```bash
grep -rn "degrad" spectra/ AGENTS_LIST.md README.md | grep -v CHANGELOG
```

**Expect**: no hit describing `create-pr`, and no hit claiming `review-pr` differs from it on the `gh` gate.
Hits inside `spectra/CHANGELOG.md` are expected and correct — the 1.4.0 entry is history.

**Evidences**: SC-006.

---

## Coverage map

| Scenario | Requirements | Success criteria |
|---|---|---|
| S1 | FR-013 | SC-007 |
| S2 | FR-001, FR-002, FR-003, FR-004 | SC-001, SC-002, SC-003 |
| S3 | FR-001, FR-002, FR-004 | SC-001, SC-002 |
| S4 | FR-006 | SC-003 |
| S5 | FR-010, FR-011 | SC-004 |
| S6 | FR-012 | SC-005 |
| S7 | FR-007, FR-009 | — |
| S8 | FR-014, FR-015 | SC-006 |
| S9 | FR-015 | SC-006 |

FR-005 (the offer itself is not gated) is covered by declining the offer in S2's environment: the run ends
silently with no gate error.

FR-008 (`gh` exclusively) is verified by inspection of the command file against
[contracts/gh-operations.md](./contracts/gh-operations.md) — no `curl` or REST call appears in it.
