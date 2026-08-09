# Contract — the `spectra` command surface

The user-facing contract of the CLI channel after this change. Breaking, hence CLI `5.0.0`.

## Shape

```text
spectra                          informational only; touches nothing
spectra --help                   banner, then three panels
spectra <command> [options]      project-scoped: acts on the extension in this project
spectra cli <command> [options]  tool-scoped: acts on the spectra command itself
```

The split is the contract: **a top-level verb never acts on the tool, and `cli` never acts on the
project.** Nothing else in this document matters more (FR-037, G4).

## Project-scoped commands

| Command | Acts on | Network | Options |
| --- | --- | --- | --- |
| `spectra install` | the project | yes (catalog) | unchanged from today |
| `spectra check` | the project | no | `--yes` skips the install offer's prompt by accepting it |
| `spectra version` | the project | yes (published manifest) | — |
| `spectra update` | the project | yes (published manifest) | — |
| `spectra uninstall` | the project | no | `--yes` passes `--force` to Spec Kit |
| `spectra agent-list` | nothing | yes (roster) | — |

## Tool-scoped commands

| Command | Replaces | Behaviour |
| --- | --- | --- |
| `spectra cli version` | `--version` / `-V` | Bare version on the first line, then a notice if a newer release exists. |
| `spectra cli update` | `--update` | Self-update via uv. |
| `spectra cli uninstall` | `--uninstall` | Removes the command from the machine; project extensions untouched. `--yes` skips the prompt. |

`spectra cli version` keeps the first-line-is-bare-version format on purpose: `.github/workflows/ci.yml`
asserts that output equals the committed `VERSION`, and that assertion is moving here from `--version`.

## Removed flags

`--version` / `-V`, `--update`, and `--uninstall` are removed and are **not** aliases (FR-038). Detected
in `argv` before parsing, because argparse cannot name a replacement for an argument it does not define:

```text
$ spectra --version
✗ spectra: --version was removed in 5.0.0.
  For the tool's own version:    spectra cli version
  For your agents' version:      spectra version
```

Exit 2. Each message names the replacement and, where the old flag was ambiguous, both candidates
(FR-039). `--yes` and `--no-update-check` survive.

## Exit codes

| Code | Meaning |
| --- | --- |
| 0 | Success, including any delivered verdict |
| 1 | The user declined an offered action |
| 2 | Usage error — bad flag, unknown command, or a removed flag |
| 3 | Published data could not be retrieved within 10 seconds |
| 4 | A delegated command (`specify` or `uv`) failed |
| 5 | The project is not in the required state |
| 130 | Interrupted |

Codes 0–4 and 130 are already in use by `cli.py`; only 5 is new.

## Behaviour matrix

Rows are the four installation states from [`../data-model.md`](../data-model.md#3-installation-state).

### `spectra check`

| State | Message | Exit |
| --- | --- | --- |
| `INSTALLED` | Spectra is installed here, with the version | 0 |
| `NOT_INSTALLED` | Not installed in this Spec Kit project; offers to install | 0 if accepted and install succeeds, 1 if declined, 4 if the install fails |
| `INCOMPLETE` | Installed folder present but unusable — names it an interrupted install and points at `spectra update` | 5 |
| `NOT_A_PROJECT` | Not a Spec Kit project; names `specify init` and `spectra install` | 5 |

### `spectra version`

| Condition | Message | Exit |
| --- | --- | --- |
| Installed == published | Agents are up to date, with the version | 0 |
| Installed < published | Both versions, names `spectra update` as the fix | 0 |
| Installed > published | Both versions, states the installed agents are ahead of what is published, offers no update | 0 |
| Published unreachable | Installed version, plus why the published one could not be fetched; never implies currency | 3 |
| `NOT_INSTALLED` | Spectra is not installed here; names `spectra install` | 5 |
| `INCOMPLETE` | Interrupted install; names `spectra update` | 5 |
| `NOT_A_PROJECT` | Not a Spec Kit project | 5 |

Every verdict exits 0; only an inability to reach a verdict is non-zero (FR-032a).

### `spectra update`

| Condition | Behaviour | Exit |
| --- | --- | --- |
| Out of date | `specify extension update spectra`, then report the new version | 0, or 4 if Spec Kit fails |
| Already current | Reports current, changes nothing — no forced reinstall | 0 |
| Ahead of published | Reports ahead, changes nothing | 0 |
| Published unreachable | Explains; makes no changes | 3 |
| `NOT_INSTALLED` / `NOT_A_PROJECT` | Says so; makes no changes | 5 |
| `INCOMPLETE` | Proceeds with the update — this is the documented repair path | 0, or 4 |
| `specify` not on PATH | Explains Spec Kit is required; makes no changes | 4 |

### `spectra uninstall`

| Condition | Behaviour | Exit |
| --- | --- | --- |
| `INSTALLED` or `INCOMPLETE` | `specify extension remove spectra` (plus `--force` with `--yes`); Spec Kit owns the prompt | 0, 1 if declined at Spec Kit's prompt, 4 if it fails |
| `NOT_INSTALLED` | Reports not installed, changes nothing | **0** |
| `NOT_A_PROJECT` | Reports not a Spec Kit project | 5 |
| `specify` not on PATH | Explains Spec Kit is required; makes no changes | 4 |

Two choices here are worth stating plainly because the spec leaves them open.

**Confirmation is Spec Kit's, not ours.** `specify extension remove` already prompts and already accepts
`--force`. Adding a second prompt would make the user confirm one action twice, and would put the safety
gate in the outer tool while the inner tool stays unguarded for anyone calling it directly.

**Uninstalling when nothing is installed exits 0, not 5.** The requested end state already holds, and
`spectra cli uninstall` already treats an absent uv tool as an idempotent success. Consistency inside one
tool beats consistency with the other rows of this table.

### `spectra agent-list`

| Condition | Behaviour | Exit |
| --- | --- | --- |
| Roster fetched, understood | Prints all agents grouped by SDLC phase | 0 |
| Run outside a project | Identical output — discovery does not require an install (FR-027) | 0 |
| Run inside a project | Additionally marks which Spectra-provided agents are installed here (FR-048) | 0 |
| Roster newer MINOR | Full listing from recognized fields, plus a notice naming `spectra cli update` | 0 |
| Roster newer MAJOR | Refuses to present it, names `spectra cli update` | 3 |
| Unreachable or malformed | Explains; prints no partial or stale list | 3 |

## Output shape for `agent-list`

Grouped by phase in roster order, rendered through the existing `ui.panel()` so the output matches the
help screen rather than introducing a second visual language:

```text
Foundation                                                   Inception
  ✅ Guardrails                       core     Spec Kit   speckit.constitution
  ✅ Domain Analyzer                  add-on   Spectra    speckit.spectra.domain-analyzer   (installed)
  🚧 FDA 21 CFR Part 11 & IEC 62304   add-on   Spectra    under development
```

Four things are unambiguous per row, which is what FR-025 and Journey 1's acceptance require: status,
type, provider, and either the command or the fact that there is none. Planned agents show no command
(FR-007), so no planned agent can be mistaken for something runnable.

## Help screen

Three panels: **Project commands**, **Tool commands** (`cli …`), **Options** — built from the same
module-level lists `cli.py` already uses to keep the rendered table and the parser reading from one
source. The panel titles carry the distinction FR-043 requires; a first-time reader does not have to
infer it from the verbs.

## Network contract

| Data | URL | Timeout |
| --- | --- | --- |
| Roster | `https://raw.githubusercontent.com/xavient/spectra/main/agents-list.json` | 10s |
| Published extension version | `https://raw.githubusercontent.com/xavient/spectra/main/spectra/extension.yml` | 10s |
| Catalog (install flow) | unchanged | unchanged (10s) |
| Newest CLI release | unchanged — GitHub Releases, `cli` group only | unchanged (2s passive / 10s explicit) |

Every fetch is anonymous. Failure never degrades to a stale or empty result presented as authoritative
(FR-041); it reports the reason and exits 3. `SPECTRA_NO_UPDATE_CHECK` continues to suppress only the CLI
channel's release check — it does not disable the roster or the published-manifest read, which are the
whole point of the commands that fetch them.

One new environment variable, `SPECTRA_RAW_BASE`, overrides the
`https://raw.githubusercontent.com/xavient/spectra/main` prefix for the roster and published-manifest
reads. It exists so fetch failure, timeout behaviour, and schema-version tolerance can be exercised against
a local server without publishing anything — see `quickstart.md` steps 8 and 9. It mirrors the existing
`SPECTRA_UPDATE_REPO` seam in `version.py`, is undocumented in user-facing help, and defaults to the real
URL.
