# Contract — the `spectra` command surface

The user-facing contract of the CLI channel after this change. Breaking, hence CLI **`6.0.0`**.

## Shape

```text
spectra                          informational only; touches nothing
spectra --help                   banner, then three panels
spectra <command> [options]      project-scoped: acts on this project and this machine's stack
spectra cli uninstall [options]  tool-scoped: the only surviving tool subcommand
```

The project/tool split established in 5.0.0 survives, but the tool side shrinks to a single verb.
`version` and `update` are now unambiguous *because* there is no competing `cli` form of either — which
is the point of the change, and the reason the split no longer needs two panels to explain itself.

## Project-scoped commands

| Command | Acts on | Network | Options |
| --- | --- | --- | --- |
| `spectra install` | the project | yes (catalog) | unchanged |
| `spectra check` | the project | no | `--yes` accepts the install offer |
| `spectra version` | **the whole stack** | yes (release API, published manifest, `specify self check`) | `--no-update-check` suppresses only the Spectra CLI release lookup |
| `spectra update` | **the whole stack** | yes (same three) | `--yes` skips the confirmation prompt |
| `spectra uninstall` | the project | no | `--yes` passes `--force` to Spec Kit |
| `spectra agent-list` | nothing | yes (roster) | — |

`version` and `update` are the two changed rows. Both previously acted on the extension alone.

## Tool-scoped commands

| Command | Behaviour |
| --- | --- |
| `spectra cli uninstall` | Unchanged. Removes the command from this machine; project extensions untouched. `--yes` skips the prompt. |

## Retired subcommands

`spectra cli version` and `spectra cli update` are **hard-removed**, following the same pattern as the
`--version` / `--update` / `--uninstall` flags removed in 5.0.0: the surface no longer accepts them, and
running one names its replacement rather than emitting a generic error.

```text
$ spectra cli version
✗ `spectra cli version` has been retired. Use `spectra version` instead.

$ spectra cli update
✗ `spectra cli update` has been retired. Use `spectra update` instead.
```

Both exit **2** (`EXIT_USAGE`). They are **not** aliases and do not perform the action.

Implementation note: unlike the removed *flags* — which had to be caught in `argv` before parsing,
because argparse cannot name a replacement for an argument it no longer defines — these are
*subcommands*, so the parser can keep accepting them and dispatch to a handler that reports the
retirement. Registering them keeps `spectra cli version` from degrading into a bare "invalid choice"
error.

## Help output

Two panels, not three. The **Tool commands** panel now holds one row:

```text
╭─ Project commands — act on the agents in this project ───────────────╮
│ install     Install Spectra into the Spec Kit project in this folder…│
│ check       Report whether Spectra is installed in this project…      │
│ version     Check every part of the Spectra stack — the Spec Kit CLI, │
│             core agents, the spectra command, and your agents.        │
│ update      Bring every out-of-date part of the Spectra stack current.│
│ uninstall   Remove Spectra's agents from this project…                │
│ agent-list  List every agent Spectra offers…                          │
╰──────────────────────────────────────────────────────────────────────╯
╭─ Tool commands — act on the spectra command itself ──────────────────╮
│ uninstall   Remove the spectra command from this machine…             │
╰──────────────────────────────────────────────────────────────────────╯
```

`spectra cli` with no subcommand keeps printing the group help and exiting 2, now listing only
`uninstall` and pointing at the top-level commands for everything else.

## `spectra version` output

Four rows, always, in canonical order. Label column padded to the longest label.

Everything current:

```text
Specify CLI:     ✓ up to date (0.16.4)
Core agents:     ✓ up to date (0.16.4)
Spectra CLI:     ✓ up to date (6.0.0)
Spectra agents:  ✓ up to date (1.3.1)
```

Something behind — the hint is appended only when at least one row needs updating (FR-003):

```text
Specify CLI:     ✓ up to date (0.16.4)
Core agents:     ! needs updating (0.12.14 → 0.16.4)
Spectra CLI:     ! needs updating (5.1.0 → 6.0.0)
Spectra agents:  ✓ up to date (1.3.1)

You can update by running: spectra update
```

Degraded — `specify` absent and the network unreachable, showing what is still known (FR-026):

```text
Specify CLI:     – unknown (specify is not on PATH)
Core agents:     – unknown (the Specify CLI version is unknown, so there is nothing to compare against)
Spectra CLI:     – unknown (installed 6.0.0; the latest release could not be fetched)
Spectra agents:  – unknown (installed 1.3.1; the published version could not be fetched)
```

Glyphs reuse the existing vocabulary: `✓` green, `!` yellow, `–` dimmed. Color is suppressed
automatically when stdout is not a TTY.

**Exit code is 0 for every one of the above.** A delivered verdict is a success, including an unknown
one. Only a project-state failure is non-zero:

```text
$ spectra version          # outside a Spec Kit project
✗ This is not a Spec Kit project — no .specify/ directory here or in any parent folder.
  Initialize one:   specify init
  Then add Spectra: spectra install
                                                                    exit 5
```

The 5.0.0 hint line `This is the extension version. For the tool's own: spectra cli version` is
**removed** — it named a retired command, and the table now covers both.

## `spectra update` output

Nothing to do (FR-021) — reports and exits 0 without prompting:

```text
Specify CLI:     ✓ up to date (0.16.4)
Core agents:     ✓ up to date (0.16.4)
Spectra CLI:     ✓ up to date (6.0.0)
Spectra agents:  ✓ up to date (1.3.1)

✓ Everything is up to date.
```

Nothing **checkable** (FR-027) — a different message for a different situation, because claiming
everything is current here would be false:

```text
Specify CLI:     – unknown (specify is not on PATH)
Core agents:     – unknown (the Specify CLI version is unknown, so there is nothing to compare against)
Spectra CLI:     – unknown (installed 6.0.0; the latest release could not be fetched)
Spectra agents:  – unknown (installed 1.3.1; the published version could not be fetched)

! Nothing could be checked, so nothing was updated.
  Unverified: Specify CLI, Core agents, Spectra CLI, Spectra agents
                                                                    exit 0
```

Partially checkable (FR-027) — what is known is stated, and what is not is named:

```text
Specify CLI:     ✓ up to date (0.16.4)
Core agents:     ✓ up to date (0.16.4)
Spectra CLI:     ✓ up to date (6.0.0)
Spectra agents:  – unknown (installed 1.3.1; the published version could not be fetched)

✓ Nothing needs updating among the components that could be checked.
  Unverified: Spectra agents
                                                                    exit 0
```

All three exit 0 — no update was needed or attempted in any of them. The distinction is in the message,
not the code, because the exit code answers "did anything I attempted go wrong?" and nothing was
attempted.

Work to do — only `needs_updating` rows are listed, and one prompt covers all of them:

```text
The following components need updating:
  • Specify CLI: 0.16.3 → 0.16.4
  • Spectra CLI: 5.1.0 → 6.0.0

Proceed? [Y/n]
```

`--yes` skips the prompt. Declining exits **1** (`EXIT_DECLINED`) having changed nothing.

Final report — four rows, matching the status table's shape, with each version **re-read after** the
walk rather than inferred from an exit code:

```text
Specify CLI:     ✓ updated (0.16.4)
Core agents:     ✓ updated (0.16.4)
Spectra CLI:     ✗ failed (uv exited with code 1)
Spectra agents:  – skipped (already up to date)
                                                                    exit 4
```

A `skipped` row never causes a non-zero exit; a `failed` row always does.

**A delegate reporting success is not proof anything moved.** Spec Kit records an extension's installed
version in its own registry, so a manifest that disagrees produces a cheerful exit 0 with nothing
changed. `spectra update` re-checks every component after the walk and says so plainly rather than
echoing the claim:

```text
Spectra agents:  ! reported success, but the version is unchanged (1.0.0)

! Reported success without changing anything: Spectra agents.
  The underlying command exited 0 but the version did not move. This usually means it
  disagrees with us about what is installed — check the component by hand.
                                                                    exit 4
```

**`--yes` is honoured all the way down.** `specify extension update` prompts for confirmation and offers
no flag to skip it, so a non-interactive run would otherwise abort on that step alone with exit 1. When
the user has already been shown exactly what will change and answered yes, that answer is fed to the
delegate rather than letting an invisible prompt fail the run.

## Exit codes

Unchanged constants; no new codes introduced.

| Code | Constant | Meaning here |
| --- | --- | --- |
| 0 | `EXIT_OK` | Any verdict from `version`; a fully successful or no-op `update` |
| 1 | `EXIT_DECLINED` | The user declined the update prompt |
| 2 | `EXIT_USAGE` | Bad flag, unknown command, or a retired `cli` subcommand |
| 3 | `EXIT_UNREACHABLE` | Reserved; **no longer reached by `version`**, which now reports unreachable data as `unknown` and exits 0 |
| 4 | `EXIT_DELEGATION` | At least one attempted update failed |
| 5 | `EXIT_PROJECT_STATE` | Not a Spec Kit project, or Spectra not installed |
| 130 | `EXIT_INTERRUPTED` | Ctrl-C during a delegated command |

Code 3's retreat is a deliberate behavior change: previously an unreachable published version made
`spectra version` exit 3, because with one component there was nothing left to report. With four
components there always is, so unreachability degrades one row instead of failing the command.

## CI contract

`.github/workflows/ci.yml` asserts that the installed distribution reports the committed `VERSION`. That
assertion currently reads `spectra cli version | head -1` and **must move** as part of this change,
because the command it depends on is being retired (R3):

```bash
REPORTED="$(python -c 'import importlib.metadata as m; print(m.version("spectra-cli"))')"
FILE_VERSION="$(tr -d '[:space:]' < VERSION)"
```

The adjacent "removed flags name their replacements" step gains `cli version` and `cli update` as two
new cases, asserting each exits non-zero and names its replacement.
