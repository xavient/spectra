# Contract: Core Agents Detection & Update

**Feature**: `010-multi-integration-updates` | **Date**: 2026-08-20

The detection and update contract for the one component this feature makes plural. Everything here lives
in `spectra_cli/health.py` except the two delegation helpers, which live in `spectra_cli/extension.py`.

This contract **extends** `specs/007-unified-version-update/contracts/health-check.md`. The other three
components are unchanged by it (FR-042).

---

## 1 · Inputs

| Input | Path / command | Read by | Absent or unreadable → |
| --- | --- | --- | --- |
| Installed integrations | `.specify/integration.json` → `installed_integrations` | both commands | fall back to single-record mode (§ 6) |
| Default integration | `.specify/integration.json` → `default_integration`, then `integration` | both commands | no key is treated as default; walk order falls back to recorded order; coverage advisory suppressed |
| Per-integration version | `.specify/integrations/<key>.manifest.json` → `version` | both commands | that integration is `UNKNOWN` (§ 3) |
| Project-level version | `.specify/integration.json` → `version` | fallback only | see § 6 |
| Modification state | `specify integration status --json` | `spectra update` only | `ModificationReport.established = False` (§ 5) |
| Command coverage | `.specify/extensions/.registry` → `extensions.spectra.registered_commands` | `spectra version` only | no advisory (§ 7) |

**`spectra version` runs no child process for this component.** Every input it needs is a local file
read (research R1). This is what keeps FR-012 achievable.

---

## 2 · Enumeration

```python
read_installed_integrations(project_root) -> list[str] | None
```

- Returns the recorded `installed_integrations` list, order preserved.
- Returns `None` — meaning *fall back* — when the file is missing, unreadable, not an object, or has no
  usable list.
- MUST NOT infer membership from the presence of `.specify/integrations/*.manifest.json` files: that
  directory also holds `speckit.manifest.json`, which is shared infrastructure, not an integration
  (FR-002, finding F8).
- A recorded key with no corresponding manifest is still enumerated — it becomes an `UNKNOWN` child
  rather than disappearing, because a recorded-but-broken integration is exactly what a user needs told.

```python
read_integration_version(project_root, key) -> str | None
```

Missing file, unreadable file, invalid JSON, non-object top level, and an absent or empty `version` all
return `None`. To the caller they are one situation with one remedy — the same rule the current
project-level reader already follows.

---

## 3 · Per-integration verdict

| Specify CLI status | Recorded version vs the installed CLI | Verdict | `latest` |
| --- | --- | --- | --- |
| `UNKNOWN` | — | `UNKNOWN` | — |
| any | unreadable | `UNKNOWN` | — |
| `NEEDS_UPDATING` | any | `NEEDS_UPDATING` | the CLI's latest |
| `UP_TO_DATE` / `AHEAD` | recorded < installed | `NEEDS_UPDATING` | the CLI's installed |
| `UP_TO_DATE` / `AHEAD` | recorded > installed | `AHEAD` | the CLI's installed |
| `UP_TO_DATE` / `AHEAD` | equal | `UP_TO_DATE` | the CLI's installed |

Unchanged in substance from the 007 contract — the same two ways to be behind, evaluated once per
integration instead of once per project. Every `UNKNOWN` carries a reason (FR-005).

---

## 4 · Aggregation into one row

Evaluated top to bottom, first match wins (FR-006, FR-009, FR-010):

| # | Condition | Row status |
| - | --------- | ---------- |
| 1 | no integrations enumerated | `UNKNOWN` |
| 2 | any child `NEEDS_UPDATING` | `NEEDS_UPDATING` |
| 3 | any child `UNKNOWN` | `UNKNOWN` |
| 4 | every child `AHEAD` | `AHEAD` |
| 5 | otherwise | `UP_TO_DATE` |

- Row `installed` = the **oldest** readable child version (FR-007).
- Row `detail` names the behind children (rule 2) or the unestablished children (rule 3).
- The row is **always** present. There is never a fifth component and never zero rows (FR-011).

**Breakdown lines** are rendered only when more than one integration is enumerated **and** the children
are not uniform in version and status (FR-013).

---

## 5 · Modification report

```python
modification_report(timeout=...) -> ModificationReport
```

- Runs `specify integration status --json`, which is read-only and exits 0 in every state including its
  own warning (finding F7).
- Routes the `speckit` entry to `shared`; routes every other entry that is a recorded integration to
  `per_integration`; ignores anything else.
- Never raises. A missing `specify`, a timeout, a non-zero exit, or unparseable output all yield
  `established = False` with empty lists.
- MUST NOT be called by `spectra version` (FR-012), and MUST NOT be derived by parsing the
  human-readable status table (FR-041).

**Degradation (research R6)**: `established = False` means no overwrite may be authorized. The walk still
runs, unforced. The dependency then refuses exactly the integrations it must, and its refusal — which
names the files and the flag — reaches the user unaltered.

---

## 6 · Single-record fallback

Triggered when `read_installed_integrations` returns `None`, **or** when no enumerated key yields a
readable manifest version. Detected by absence of data, never by comparing `specify` version numbers
(research R8).

In this mode:

- Exactly one child is produced, with `key = None`, judged from `.specify/integration.json` → `version`
  by the § 3 table — which is today's behaviour, unchanged.
- No breakdown lines are rendered (there is one child).
- The update walk delegates **bare**: `specify integration upgrade`, with no key and no `--force`.
- No coverage advisory is computed.

This mode is what FR-012 and SC-005 assert against, so it must remain reachable and byte-identical.

---

## 7 · Command coverage

```python
registered_agents(project_root) -> set[str] | None
```

- Reads `extensions.spectra.registered_commands` from `.specify/extensions/.registry` and returns its
  keys — the agents Spectra's commands are registered for.
- Returns `None` when the registry is missing, unreadable, has no `spectra` entry, or records no command
  map. `None` means **do not report** (FR-039); it MUST NOT be treated as "no agents covered".
- The advisory names every enumerated integration absent from that set, gives
  `specify integration use <key>` as the remedy, and states that the remedy changes the project's
  default integration (FR-037).
- The advisory is rendered below the four rows, never as a row, and never affects the exit code
  (FR-038). It performs nothing (FR-040).

---

## 8 · Delegation

Both helpers stay in `spectra_cli/extension.py`, routed through the existing private `_delegate()` so
they inherit its PATH check, its `DelegationError`, its terminal attachment, and its `130` handling.

```python
def delegate_integration_upgrade(key: str | None = None, force: bool = False) -> int:
    argv = ["specify", "integration", "upgrade"]
    if key:
        argv.append(key)
    if force:
        argv.append("--force")
    return _delegate(argv)
```

- `key = None` reproduces today's bare invocation exactly, which is the fallback path (§ 6).
- `force = True` MUST be reachable **only** from an `OverwritePlan` whose `authorized` set contains that
  key (FR-026, FR-029, SC-003). No other caller may pass it.
- The docstring that currently records "`--force` is deliberately not passed" is replaced by one that
  records *why it is now reachable and what gates it* — the reasoning is preserved, the outcome changes.
  See `contracts/cli-surface.md` § Supersession.

---

## 9 · The walk

```text
for component in report.components:                 # canonical order, unchanged
    if component is Core agents and component.parts:
        targets = [child for child in parts if child.status == NEEDS_UPDATING]
        order targets: non-default first, default last          # R3
        for child in targets:
            force = child.key in authorized_keys                 # never inferred
            code = delegate_integration_upgrade(child.key, force=force)
            code == 130            -> raise Interrupted (abort the whole walk)
            code == 0              -> child UPDATED
            otherwise              -> child FAILED (detail = exit code); continue
        children not in targets    -> child SKIPPED (already current / ahead / unknown)
        children in candidates but not authorized -> child SKIPPED (overwrite not authorized)
        component outcome = worst(children)                      # FAILED > UPDATED > SKIPPED
    else:
        ... unchanged from the 007 contract ...
```

Invariants, each inherited or required:

- **Every component is visited**, and now every enumerated integration produces a child result (FR-021).
- **A failed integration does not stop the walk** (FR-019); a failed *component* still does not stop the
  other components.
- **Skips are inert** — neither a "already current" skip nor an "overwrite not authorized" skip reaches
  the exit code (FR-023, FR-030).
- **Cancellation stops everything** — `130` from any child aborts the whole walk, not just the
  integration loop (FR-020).
- **`authorized_keys` is an input.** `health.py` never prompts, never reads a TTY, and never consults
  `--force`; `cli.py` resolves authorization and passes the result in.

---

## 10 · Post-walk verification

Each attempted integration's manifest version is re-read after the walk (FR-022). A child recorded
`UPDATED` whose version did not move is rendered as "reported success, but the version is unchanged".

This matters more here than for the other components: a delegated upgrade that silently no-ops is
exactly how a stale sibling would become invisible again, which is the bug this feature exists to fix.
