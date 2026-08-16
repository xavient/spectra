# Phase 0 Research — Unified Version & Update Commands

**Feature**: `007-unified-version-update` | **Date**: 2026-08-16

Everything below was verified against the Spec Kit CLI actually installed on this machine
(`specify-cli` 0.16.4, at `~/.local/share/uv/tools/specify-cli/`) rather than inferred from the issue.
Three findings changed the design; they are marked **⚠ Finding**.

---

## R1 — The `specify self check` output contract

**Decision**: Parse `specify self check` **stdout**, matching on line prefixes. Never branch on its
exit code.

**⚠ Finding — the exit code carries no information.** `specify self check` returns **0 on every
path**, including the network-failure and unparseable-tag paths. The issue's status logic ("If
`specify self check` says 'Up to date' → up to date; otherwise → needs updating") is therefore only
half-safe: `otherwise` silently folds three *unknown* outcomes into `needs updating`, which would make
`spectra update` attempt `specify self upgrade` against a CLI whose state was never established —
exactly what the clarified FR-023 forbids.

Verified source: `specify_cli/_version.py`, `self_check()` at line 1150. All five branches, with the
observed rendering (Rich markup is stripped when stdout is not a TTY, so these are the literal bytes a
subprocess sees):

| # | Condition | First line | Status to report |
| --- | --- | --- | --- |
| 1 | Latest release could not be fetched | `Installed: 0.16.4` + `Could not check latest release: <reason>` | `unknown` |
| 2 | Latest tag unparseable | `Installed: 0.16.4` + `Latest release: …` + `Could not validate latest release tag from GitHub.` | `unknown` |
| 3 | Installed version undetectable | `Current version could not be determined.` | `unknown` |
| 4 | Newer release exists | `Update available: 0.16.4 → v0.16.5` | `needs_updating` |
| 5 | Current | `Up to date: 0.16.4` | `up_to_date` |

Confirmed live on this machine:

```text
$ specify self check
Up to date: 0.16.4
$ specify self check >/dev/null 2>&1; echo $?
0
```

**Parsing rules adopted** (in order; first match wins):

1. `Up to date: <version>` → `up_to_date`, installed = `<version>`, latest = `<version>`
2. `Update available: <installed> → <latest>` → `needs_updating` (split on `→`, U+2192)
3. `Installed: <version>` present **and** any of `Could not check latest release:` /
   `Could not validate latest release tag` → `unknown`, installed = `<version>`, latest = None
4. `Current version could not be determined.` → `unknown`, installed = None
5. Nothing matched → `unknown` with the raw first line kept as the explanation

Rule 5 is what satisfies the spec's "degrade gracefully if the output format changes" edge case: an
unrecognized format is `unknown`, never a guess.

**Rationale**: There is no machine-readable alternative. `specify self check --help` advertises **no
options at all** — no `--json`, no `--quiet`. Stdout is the only channel, so the parser is the
contract, and it is pinned by the tests in `tests/test_health.py` using literal fixture strings copied
from the table above.

**Alternatives considered**:

- *Reimplement the check ourselves against the `github/spec-kit` releases API.* Rejected: duplicates
  Spec Kit's own resolution logic (including its tag-normalizing rules), and would disagree with
  `specify self upgrade` the moment either side changed.
- *Use `specify version`.* Rejected: reports installed version and system info only — it has no
  concept of a latest release, so it cannot answer "is this behind?".
- *Branch on exit code.* Rejected: always 0, as measured above.

**Robustness note**: Rich wraps output to 80 columns when not attached to a TTY. The four version
lines are short and do not wrap, but a long `<reason>` in branch 1 can. The parser therefore matches
on **line prefixes** and treats a wrapped continuation as part of the reason text, never as a new
directive.

---

## R2 — The integration version, and why it is coupled to the CLI

**Decision**: Read `.specify/integration.json` → `version` with `json.load`. Report `needs_updating`
when **either** the Specify CLI is itself behind **or** the recorded version differs from the
installed CLI version. Report `unknown` whenever the CLI status is `unknown` (FR-025).

**⚠ Finding — `specify integration status` does not expose a version.** The obvious candidate command
reports health, not version, so the file read the issue prescribed is in fact the only source:

```text
$ specify integration status
Integration status: OK
Default integration: kiro-cli
Installed integrations: claude, kiro-cli
Multi-install safe: yes
Modified managed files: 0
...
```

No version field anywhere. Confirmed.

**Rationale for the coupling** (the clarified decision in the spec): the `version` field records the
Spec Kit version that installed the integration, so it tracks the CLI. If the CLI is behind, the
integration necessarily is too, and reporting it as "up to date" because it matches a stale local CLI
would be true-but-misleading. Both rows go to `needs_updating`, and the prescribed update order fixes
both in one pass.

This repository is itself a live example of the second condition: `.specify/integration.json` records
`0.12.14` while the installed CLI is `0.16.4`. The integration is behind by four minor versions, and
today nothing tells the user that. This feature is what surfaces it.

**Edge handling**: missing file, unreadable file, invalid JSON, and absent/empty `version` key all
collapse to `unknown` with a short explanation — to the caller they are the same situation (the same
reasoning `extension.read_manifest_version` already applies to manifests).

**Alternatives considered**:

- *Parse `specify integration status`.* Rejected: no version in the output, as shown.
- *Compare against the latest *published* Spec Kit rather than the installed CLI.* Rejected by
  clarification: it would make the Core agents row a duplicate of the Specify CLI row and lose the
  "CLI upgraded but integration never re-run" case, which is a distinct, real, and locally-detectable
  fault.

---

## R3 — ⚠ Finding: retiring `spectra cli version` breaks CI

**Decision**: Hard-remove the command as the issue requires, **and** in the same change move the CI
assertion off it. `.github/workflows/ci.yml` must be edited; the issue's file list omits it.

The build currently depends on the command being alive. `.github/workflows/ci.yml`, step "The command
runs and reports the committed version":

```bash
REPORTED="$(spectra cli version | head -1)"
FILE_VERSION="$(tr -d '[:space:]' < VERSION)"
if [ "$REPORTED" != "$FILE_VERSION" ]; then …fail… fi
```

After retirement that captures the retirement message and exits 2, so the step fails and every build
goes red. `contracts/cli-surface.md` from feature 006 states the coupling explicitly: "`spectra cli
version` keeps the first-line-is-bare-version format on purpose: `.github/workflows/ci.yml` asserts
that output equals the committed `VERSION`."

The new `spectra version` cannot substitute for it. It requires a Spec Kit project with Spectra
installed (FR-022) and prints a four-row table; the CI job has neither a project nor a reason to
build one.

**Decision — assert on package metadata instead:**

```bash
REPORTED="$(python -c 'import importlib.metadata as m; print(m.version("spectra-cli"))')"
FILE_VERSION="$(tr -d '[:space:]' < VERSION)"
```

This preserves the assertion's actual intent — *the installed distribution reports the committed
version* — and in fact tests it closer to the source, since `importlib.metadata` is precisely what
`version.read_installed_version()` reads. It needs no project, no network, and no CLI surface.

The adjacent CI step that checks the removed `--version` / `--update` / `--uninstall` flags still
passes untouched, and gains two new cases for the retired subcommands.

**Alternatives considered**:

- *Keep `spectra cli version` as a hidden alias.* Rejected: the issue requires a hard removal, and a
  hidden command that CI depends on is the kind of drift the constitution's sync principle exists to
  prevent.
- *Give `spectra version` a `--json` / machine-readable mode for CI.* Rejected as scope creep for this
  feature. Worth revisiting on its own merits — see Deferred below.
- *Drop the assertion.* Rejected: it is what enforces Principle VI's single-sourcing of `VERSION`.

---

## R4 — Where the four checks run, and in what order

**Decision**: `check_all()` resolves the Specify CLI first, then the integration (which consumes the
CLI result), then the Spectra CLI, then the extension. Sequential, not parallel.

**Rationale**: The integration verdict is a function of the CLI verdict (FR-025), so those two are
genuinely ordered. The two Spectra checks are independent, but the whole report is bounded by roughly
one subprocess call plus two short HTTP GETs — `specify self check` measured **0.33 s** here, and
`net.TIMEOUT` already bounds the fetches. Threading four checks to save a fraction of a second would
add failure modes (interleaved output, harder-to-read tracebacks) for no user-visible gain.

**Timeout**: `specify self check` is invoked with `subprocess.run(..., capture_output=True, text=True,
timeout=…)`. A hung network call inside a child process must not hang `spectra version`; a timeout is
caught and reported as `unknown`.

---

## R5 — `--no-update-check` and the spec's wording

**Decision**: `--no-update-check` suppresses only the **Spectra CLI** GitHub release lookup, which is
the existing behavior of `_update_check_disabled()`. `specify self check` still runs.

**Correction to the spec — applied.** FR-016 described `specify self check` as a "local check". It is
not — it performs a GitHub round trip of its own. The *behavior* the spec prescribed was still right (we
do not suppress it, because it is Spec Kit's call to make and it degrades to `unknown` on its own via
branch 1 of R1); only the parenthetical label was inaccurate. FR-016 and User Story 1's scenario 7 have
been reworded to say what is and is not suppressed. No behavioral consequence.

**Rationale for not suppressing it**: the flag exists so Spectra never makes an unrequested call to
*its own* release API. Reaching into a delegated Spec Kit command to disable its network access would
be overreach, and offline runs already degrade correctly and quickly.

---

## R6 — Update delegation, and the meaning of "continue through partial failures"

**Decision**: Four update actions, each returning a per-component result, run unconditionally in
sequence for every component whose status is `needs_updating`:

| Order | Component | Action | Mechanism |
| --- | --- | --- | --- |
| 1 | Specify CLI | `specify self upgrade` | new `extension.delegate_self_upgrade()` |
| 2 | Core agents | `specify integration upgrade` | new `extension.delegate_integration_upgrade()` |
| 3 | Spectra CLI | `uv tool install … --force` | existing `version.perform_update(tag)` |
| 4 | Spectra agents | `specify extension update spectra` | existing `extension.delegate_update()` |

Both new delegates go through the existing private `extension._delegate()`, inheriting its
PATH check, its `DelegationError`, its terminal attachment (so Spec Kit's own prompts reach the user),
and its `130` handling for Ctrl-C. `specify integration upgrade` takes an optional trailing key and
defaults to the current integration, so it is invoked bare — verified via `--help`.

**A caught exception must not end the run.** Each step is wrapped individually; `DelegationError`,
`version.UpdateError`, and a non-zero exit code all become a recorded failure for that component and
execution proceeds to the next. This is the one place where a `try/except` per step is the *correct*
shape rather than defensive noise, because FR-009 makes "attempt everything" the requirement.

**⚠ Finding — updating the Spectra CLI replaces the running process's own code.** Step 3 reinstalls
the very tool that is mid-execution. `version.perform_update()` already documents the Windows
file-lock consequence. Ordering it **third**, ahead of only the extension update, is therefore
load-bearing: if it were first, steps 2–4 would run under a half-replaced installation. The issue's
prescribed order already has this property; this note records *why* it must not be reordered later.

**Ctrl-C**: an interrupt during any step propagates as exit `130` and stops the sequence. Continuing
to mutate a user's toolchain after they asked it to stop would be wrong; "continue through failures"
means *failures*, not *cancellation*.

---

## R7 — Rendering the four-row table

**Decision**: One new `ui.health_table(rows)`, aligned in columns rather than boxed, reusing the
existing glyph vocabulary — `✓` green for up to date or updated, `!` yellow for needs updating, `✗` red
for failed, `–` dimmed for unknown or skipped.

**One renderer, two callers.** The status table and the update final report have identical shape — four
labelled rows carrying a glyph, a phrase, and version information — so `health_table` takes
already-formatted cells and both callers feed it. A second renderer for the final report would drift
from the first the moment either changed, and the two tables sitting adjacent in one `spectra update`
run is exactly where drift would show.

Target shape (the issue's desired output, with the label column padded to the longest name):

```text
Specify CLI:     ✓ up to date (0.16.4)
Core agents:     ! needs updating (0.12.14 → 0.16.4)
Spectra CLI:     ✓ up to date (5.1.0)
Spectra agents:  – unknown (installed 1.3.1; published version unavailable)

You can update by running: spectra update
```

**Rationale**: `ui.panel()` would box the rows and force wrapping at 80 columns; `ui.agent_list()`
already establishes aligned columns as this codebase's answer for tabular data, and `ui.visible_len()`
exists so padding stays correct once color codes are present. Reusing `ok`/`warn`'s glyphs keeps one
visual vocabulary across the CLI.

Colors vanish automatically when piped (`USE_COLOR` is `sys.stdout.isatty()`-gated), so tests assert on
plain text without stripping escapes.

---

## R8 — Reading the CLI's version once `spectra cli version` is gone

**Decision**: Two replacements, no new CLI surface. CI asserts on `importlib.metadata` (R3); every
procedure that needs the version *from an arbitrary directory* reads the banner line printed by **bare
`spectra`**.

**Finding**: R3 caught CI's dependency, but two further procedures depend on the same retired command,
and neither was in scope:

| Procedure | Current step | Why `spectra version` cannot substitute |
| --- | --- | --- |
| `CONTRIBUTING.md:398-400` — release smoke test | `uv tool install … --force` then `spectra cli version` | Runs "from any directory"; `spectra version` exits 5 without a Spec Kit project |
| `test/README.md:79` — clean-room row 10 | `spectra uninstall`, then `spectra cli version` | The whole point is that the *tool* survives removing the *project's* extension — so by construction there is no project extension left for `spectra version` to accept |

Row 10 is the sharper case: its purpose is to prove the command still runs after the project's agents are
removed, which is exactly the state in which the new `spectra version` refuses to report.

**Resolution — bare `spectra` already does this.** `cmd_overview()` calls `ui.splash()`, which prints a
`cli vX.Y.Z` line, and bare `spectra` is documented as informational: it works anywhere and touches
nothing. Verified from an empty temporary directory:

```text
$ cd "$(mktemp -d)" && SPECTRA_NO_UPDATE_CHECK=1 spectra | grep -i 'cli v'
cli v5.0.0
$ ls -A | wc -l
0
```

So both procedures become:

- **Release smoke test** → `spectra | grep 'cli v<tag>'`, which additionally exercises the banner path a
  consumer sees first.
- **Clean-room row 10** → `spectra uninstall`, then bare `spectra`, asserting it still runs and reports
  its version. This tests the requirement *better* than before: "the command still runs" is now
  demonstrated by the command actually running rather than by a subcommand that only reported a number.

**Rationale for not adding a flag**: `--version` was deliberately removed in 5.0.0, and clarification 1
of this spec deliberately refused to let `spectra version` report a partial subset outside a project.
Re-introducing either would reverse a considered decision to serve two internal procedures that an
existing, already-supported command path already satisfies.

**Alternatives considered**:

- *Add `spectra version --json` now.* Rejected: unnecessary once bare `spectra` is recognized as the
  answer, and it would widen a breaking release. Still worth doing on its own merits for scripting users
  — see Deferred.
- *Let `spectra version` degrade outside a project.* Rejected: directly contradicts clarification 1.
- *Keep `spectra cli version` alive for internal use only.* Rejected: a hidden command that internal
  procedures depend on is precisely the drift the constitution's sync principle exists to prevent.

---

## Resolved unknowns

| Unknown from Technical Context | Resolution |
| --- | --- |
| `specify self check` output format and exit code | R1 — five branches, always exit 0, parse stdout |
| Whether a machine-readable mode exists | R1 — no; `--help` lists no options |
| Whether `specify integration status` gives a version | R2 — no; read `integration.json` |
| `specify integration upgrade` invocation | R6 — bare; optional key defaults to current integration |
| Whether `specify self upgrade` exists | R6 — yes, with `--dry-run` and `--tag` |
| Cost of running all four checks | R4 — ~0.33 s subprocess + two bounded GETs; stay sequential |
| How to render the table | R7 — new `ui.health_table()`, aligned columns |
| CI's dependency on the retired command | R3 — real; move the assertion to `importlib.metadata` |
| How other procedures read the CLI version | R8 — bare `spectra` prints `cli vX.Y.Z` from any directory |

## Deferred

- **A machine-readable `spectra version`.** R8 resolves every *internal* procedure that needed the
  retired command, so nothing in this repository is left without a path. What remains unserved is an
  external user scripting against Spectra who wants the four-component report as data rather than as a
  table — grepping a banner line is not an interface to build on. A `--json` mode would serve that
  properly. Out of scope here; worth its own issue.
