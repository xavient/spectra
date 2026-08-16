# Contract — the four-component health check

How each component's status is detected and how each is updated. This is the contract
`spectra_cli/health.py` implements and `tests/test_health.py` pins.

## Module surface

```python
# spectra_cli/health.py

UP_TO_DATE      = "up_to_date"
NEEDS_UPDATING  = "needs_updating"
AHEAD           = "ahead"
UNKNOWN         = "unknown"

SPECIFY_CLI       = "specify_cli"
INTEGRATION       = "integration"
SPECTRA_CLI       = "spectra_cli"
SPECTRA_EXTENSION = "spectra_extension"

class ComponentStatus:   # key, label, installed, latest, status, detail
class HealthReport:      # components; .outdated, .needs_update, .unknown

def parse_self_check(text) -> dict
def get_specify_cli_status(timeout=...) -> ComponentStatus
def read_integration_version(project_root) -> str | None
def get_integration_status(project_root, specify_status) -> ComponentStatus
def get_spectra_cli_status(*, skip_network=False) -> ComponentStatus
def get_spectra_extension_status(project_state) -> ComponentStatus
def check_all(project_state, *, skip_network=False, timeout=...) -> HealthReport
```

`parse_self_check` is separated from `get_specify_cli_status` on purpose: the parser is the risky part
and must be unit-testable against literal fixture strings without spawning a subprocess.

---

## 1 · Specify CLI

**Detect**: run `["specify", "self", "check"]` with captured text output and an explicit timeout, then
parse stdout.

**⚠ The exit code carries no information — it is 0 on every path.** Do not branch on it. (R1)

### Parse table

Applied in order; first match wins. Rich markup is stripped when stdout is not a TTY, so these are the
literal bytes received.

| Match on stdout | `installed` | `latest` | `status` |
| --- | --- | --- | --- |
| `Up to date: <v>` | `<v>` | `<v>` | `UP_TO_DATE` |
| `Update available: <a> → <b>` | `<a>` | `<b>` | `NEEDS_UPDATING` |
| `Installed: <v>` **and** (`Could not check latest release:` **or** `Could not validate latest release tag`) | `<v>` | `None` | `UNKNOWN` |
| `Current version could not be determined.` | `None` | `Latest release: <v>` if present | `UNKNOWN` |
| *no match* | `None` | `None` | `UNKNOWN` (detail = first non-empty line) |

The separator in `Update available` is U+2192 (`→`), not `->`.

### Failure mapping

| Condition | Result |
| --- | --- |
| `specify` not on `PATH` (`shutil.which` is `None`) | `UNKNOWN`, detail `specify is not on PATH` |
| `OSError` launching the process | `UNKNOWN`, detail names the OS error |
| `subprocess.TimeoutExpired` | `UNKNOWN`, detail says the check timed out |
| Unrecognized output | `UNKNOWN`, detail carries the first non-empty line |

Never raises. A component that cannot be checked is a status, not an exception — the same rule
`project.classify()` already follows.

**Update**: `specify self upgrade`, via `extension.delegate_self_upgrade()`.

---

## 2 · Core agents (integration)

**Detect**: `json.load` on `<project_root>/.specify/integration.json`, take the `version` key, then
apply the state table below. Takes the already-resolved Specify CLI `ComponentStatus` as input — it
cannot be evaluated independently (FR-025).

**⚠ `specify integration status` does not report a version** — it reports health only. The file read is
the sole source. (R2)

### State table

`I` = the integration file's `version`; `C` = the Specify CLI's installed version.

| Specify CLI status | `I` readable | `I` vs `C` | Result | `latest` |
| --- | --- | --- | --- | --- |
| `UNKNOWN` | either | — | `UNKNOWN` | `None` |
| `NEEDS_UPDATING` | no | — | `UNKNOWN` | `None` |
| `NEEDS_UPDATING` | yes | any | `NEEDS_UPDATING` | the CLI's `latest` |
| `UP_TO_DATE` | no | — | `UNKNOWN` | `None` |
| `UP_TO_DATE` | yes | `I == C` | `UP_TO_DATE` | `C` |
| `UP_TO_DATE` | yes | `I < C` | `NEEDS_UPDATING` | `C` |
| `UP_TO_DATE` | yes | `I > C` | `AHEAD` | `C` |

Row 3's `latest` is the CLI's *latest*, not its *installed* version: when the CLI is behind, the
upgrade will install the newer one and the integration will follow it there, so the row must read
`0.12.14 → 0.16.5` to match the outcome.

### "Readable" means

Unreadable — all collapsing to `UNKNOWN` (FR-018) — covers: file missing, `OSError` reading it, invalid
JSON, top level not an object, `version` key absent, `version` empty or not a string.

**Update**: `specify integration upgrade`, via `extension.delegate_integration_upgrade()`. Invoked
bare — the optional trailing key defaults to the current integration.

---

## 3 · Spectra CLI

**Detect**: reuse `version.check_update()` wholesale and translate its verdict.

| `check_update()["status"]` | Result |
| --- | --- |
| `up_to_date` | `UP_TO_DATE` |
| `update_available` | `NEEDS_UPDATING` |
| `ahead` | `AHEAD` |
| `latest_unknown` | `UNKNOWN`, detail says the latest release could not be fetched |

When `skip_network=True` (`--no-update-check` or `SPECTRA_NO_UPDATE_CHECK`), the release lookup is not
attempted: `installed` is read locally via `version.read_installed_version()`, `latest` is `None`, and
the status is `UNKNOWN` with detail `latest-release check skipped (--no-update-check)`. FR-016 requires
the flag suppress this call and no other.

**Update**: `version.perform_update(latest)` — the existing uv reinstall.

**⚠ This step replaces the running process's own code.** It is third in the update order for that
reason; moving it earlier would leave later steps running under a half-replaced install. (R6)

---

## 4 · Spectra agents (extension)

**Detect**: `installed` comes from the already-resolved `ProjectState.installed_version`; `latest` from
`extension.published_version()`; the verdict from `extension.compare()`, whose three return values map
one-to-one onto the status vocabulary.

| Condition | Result |
| --- | --- |
| `net.FetchError` from `published_version()` | `UNKNOWN`, detail says the published version could not be fetched; `installed` still reported (FR-026) |
| `ProjectState` is `INCOMPLETE` | `UNKNOWN`, detail says the install is incomplete and names `spectra update` as the repair |
| otherwise | `extension.compare()`'s verdict |

`project.classify()` is called **once** per command invocation and the result threaded through, so the
filesystem is not re-read per component.

**Update**: `extension.delegate_update()` — the existing `specify extension update spectra`.

---

## New delegation helpers

Added to `spectra_cli/extension.py`, both routed through the existing private `_delegate()` so they
inherit its PATH check, its `DelegationError`, its terminal attachment (Spec Kit's own prompts must
reach the user), and its `130` handling for Ctrl-C:

```python
def delegate_self_upgrade() -> int:
    """`specify self upgrade`. Returns its exit code."""
    return _delegate(["specify", "self", "upgrade"])

def delegate_integration_upgrade() -> int:
    """`specify integration upgrade`. Returns its exit code."""
    return _delegate(["specify", "integration", "upgrade"])
```

Neither passes `--force`. `specify integration upgrade` blocks on locally modified managed files by
design, and silently overriding that on the user's behalf would discard their edits — exactly the class
of destructive action that belongs behind Spec Kit's own gate rather than behind ours.

---

## The update walk

```text
for component in report.components:          # canonical order == update order
    if component.status != NEEDS_UPDATING:
        record SKIPPED (with the reason: already current / ahead / unknown)
        continue
    try:
        code = <the component's update action>
    except (DelegationError, UpdateError) as exc:
        record FAILED (detail = str(exc));  continue
    if code == 130:
        abort the whole walk, exit 130
    record UPDATED if code == 0 else FAILED (detail = f"exited with code {code}")
```

Three properties this shape guarantees:

- **Every component is visited.** A failure records and continues; it never breaks the loop (FR-009).
- **Skips are inert.** `SKIPPED` never contributes to the exit code, so an unknown component cannot
  turn a clean run into a failed one (FR-023).
- **Cancellation is not a failure.** Exit 130 stops the walk rather than recording a failure and
  pressing on. "Continue through partial failures" means failures, not an explicit interrupt — the user
  asked it to stop mutating their toolchain.

Exit code: `EXIT_DELEGATION` (4) if any result is `FAILED`, else `EXIT_OK` (0).

---

## Test fixtures this requires

`tests/helpers.py` gains two things, because the health check shells out and today nothing in the suite
does:

1. **A fake `specify` executable** placed on a temporary `PATH`, emitting any one of the five R1 output
   branches on demand — so the parser is exercised through the real subprocess path, not only through
   `parse_self_check()` directly.
2. **A way to remove `specify` from `PATH`** entirely, covering the "not on PATH" branch.

`temp_project()` already writes `.specify/`, so it gains an optional `integration_version` argument to
write (or deliberately corrupt) `integration.json` alongside the extension manifest.
