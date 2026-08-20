# Contract — Coverage: detection, rotation, restoration, verification

**Module**: `spectra_cli/coverage.py` (new)
**Consumers**: `spectra_cli/install.py`, `spectra_cli/cli.py`
**Data**: [data-model.md](../data-model.md)

This contract is binding on the module's behaviour, not on its private helpers. Where it quotes output,
the wording is the contract — the tests assert on it.

---

## 1 · Detection

```python
def plan(project_root) -> CoveragePlan
```

Pure. No subprocess, no terminal, no writes. Reads exactly three things:

| Read | Source | Via |
| --- | --- | --- |
| installed integration keys | `.specify/integration.json` → `installed_integrations` | `health.read_installed_integrations` |
| the default key | `.specify/integration.json` → `default_integration`, else `integration` | `health.read_default_integration` |
| covered agents | `.specify/extensions/.registry` → `extensions.spectra.registered_commands` | `extension.registered_agents` |

Rules:

1. The installed list is membership. A per-integration manifest on disk is **not** membership, and the
   shared-infrastructure record (`speckit`) is not an integration (FR-002).
2. `registered_agents` returning `None` means **unknown** — absent, unreadable, no `spectra` entry, or an
   empty command map. Unknown yields an empty plan with `skip_reason` "the registration state could not be
   read" (FR-003, FR-004). It is never read as "nothing is covered".
3. Agents named in the registry but not in the installed list are ignored (FR-005).
4. Support is decided by the **presence of this state**, never by the dependency's version number
   (FR-051). There is no minimum-version constant anywhere in the module.
5. `targets` excludes the default; the default is covered by the restoring activation (research R3).

**Empty-plan table**: see [data-model.md](../data-model.md) § `CoveragePlan`. Five reasons, each with
fixed wording.

---

## 2 · The rotation

```python
def apply(plan, *, announce=None) -> CoverageResult
```

Preconditions: `plan.needed` is `True`. Callers must not invoke `apply` on an empty plan; doing so is a
programming error, not a supported no-op.

Algorithm, exactly:

```text
1. record original_default = plan.default_key
2. moved = False
3. try:
4.     for key in plan.targets:                  # non-default, uncovered, recorded order
5.         announce(key)
6.         code = extension.delegate_integration_use(key)
7.         moved = True                          # set even on failure: the default may have changed
8.         if code == 130: raise Interrupted
9.         record per-key outcome from `code`
10. finally:
11.     if moved or plan.default_uncovered:
12.         code = extension.delegate_integration_use(original_default)
13.         restoration = RESTORED if code == 0 else NOT_RESTORED
14.     else:
15.         restoration = NOT_NEEDED
16. re-read state; verify; build CoverageResult
```

Binding points:

- **Line 7 before line 8.** `moved` is set immediately after the call returns, whatever it returned,
  because a failed activation may still have changed the default. Setting it only on success would create
  a path where the default moved and the restore was skipped.
- **Line 11–13 runs in `finally`.** It executes after a failed activation, after `Interrupted`, and after
  any unexpected exception (FR-016). The restoring activation is attempted **once**; a failure there is
  `NOT_RESTORED`, never a retry loop.
- **`plan.default_uncovered` alone triggers the single activation** at line 12 with no targets — the
  FR-013 case. `moved` stays `False`, so `restoration` is reported as `NOT_NEEDED` even though an
  activation occurred, because the default never changed. The output says nothing about restoration in
  this case.
- **No call in this module passes a force or overwrite flag.** `delegate_integration_use` does not accept
  one (research R5), so this is enforced by signature (FR-009, FR-049).
- **`announce` is optional and presentation-free.** It receives the integration key only. The module
  never prints.

### Interruption

`KeyboardInterrupt` from a delegated call, and exit code 130 from it, both raise `coverage.Interrupted`
after the `finally` has restored the default. The caller reports an interruption, not a failure (FR-036,
FR-023 of the reporting group). Integrations already covered stay covered.

---

## 3 · Verification

After the rotation, detection runs again against the re-read registry.

| Post-state | Reported |
| --- | --- |
| a target now named in the registry | `NEWLY_COVERED` |
| a target still absent, activation exited 0 | `FAILED`, detail: `"the activation reported success but no commands were registered"` |
| a target still absent, activation exited non-zero | `FAILED`, detail: `"exited with code <n>"` |
| a target never reached (interrupt) | `SKIPPED`, detail: `"not reached"` |
| an integration that was already covered | `ALREADY_COVERED` |

`current_default` is re-read from `.specify/integration.json` and is only reported when it differs from
`original_default` — which can only happen under `NOT_RESTORED`.

**An exit code alone never produces `NEWLY_COVERED`** (FR-006). This mirrors feature 010's rule that a
delegated success is not evidence a version moved.

---

## 4 · Aggregate outcome

| Condition | `CoverageResult.outcome` |
| --- | --- |
| any child `FAILED`, or `restoration == NOT_RESTORED` | `FAILED` |
| else any child `NEWLY_COVERED` | `COVERED` |
| else | `SKIPPED`, with `detail` from the plan's `skip_reason` or `"nothing needed covering"` |

`FAILED` on one child does not stop the loop: every target is attempted (FR-015 of the reporting group,
Story 4 scenario 2).

---

## 5 · What this module must never do

| Prohibition | Requirement |
| --- | --- |
| write an agent's command or skill files | FR-007 |
| write the dependency's registration record | FR-007 |
| write `.specify/integration.json` or `.specify/init-options.json` directly | FR-007, FR-043 |
| pass a force/overwrite flag to any delegated command | FR-009, FR-049 |
| prompt, read a TTY, or consult a CLI flag | R2 (design), FR-025 (prompting is the caller's) |
| hard-code an integration key or agent name | FR-046 |
| consult the dependency's version | FR-051 |
| leave the default changed on any path it can observe | FR-015, FR-016, FR-043 |
| remove or re-register coverage an integration already has | FR-010 |
| make a network call | FR-048 |

---

## 6 · Delegation surface added to `extension.py`

```python
def delegate_integration_use(key: str) -> int:
    """`specify integration use <key>`. Returns its exit code."""
```

- Requires a non-empty `key`; there is no bare form, because a bare invocation has no meaning here.
- Takes **no** `force` parameter, by design (research R5).
- Raises `DelegationError` when `specify` is absent, consistent with the other delegations.
- Returns 130 on `KeyboardInterrupt`, consistent with `_delegate`.

Its docstring must state, in the same terms `delegate_integration_upgrade` uses, that the overwrite flag
is deliberately not expressible here and why — F4 in BRD-007 § 2.1 established that activation preserves
locally modified files.

---

## 7 · Test obligations

| Obligation | Kind |
| --- | --- |
| every empty-plan reason produces `needed == False` and the exact wording above | unit, no stub |
| `targets` excludes the default and every covered key | unit |
| `activations` always ends with the default | unit |
| the default-only case performs one activation and reports `NOT_NEEDED` | unit |
| a failed activation still restores the default | stub with argv log |
| an interrupt mid-rotation still restores the default and raises `Interrupted` | stub |
| a restore failure yields `NOT_RESTORED` and `current_default != original_default` | stub with side effect |
| an activation that exits 0 without registering yields `FAILED` with the verification wording | stub with side effect disabled for one key |
| the argv log shows exactly `targets + [default]`, in order | stub with argv log |
| no integration key appears as a literal in `coverage.py` | source assertion, extends `test_no_hardcoded_agents.py` |
| `.specify/integration.json` and `.specify/init-options.json` are byte-identical after a real rotation | container scenario (research R9) |
