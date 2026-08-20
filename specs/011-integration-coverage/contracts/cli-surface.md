# Contract — CLI surface: install, update, version

**Modules**: `spectra_cli/install.py`, `spectra_cli/cli.py`
**Data**: [data-model.md](../data-model.md) · **Behaviour**: [coverage.md](coverage.md)

Quoted output is the contract. Colour and glyphs follow `ui.py`'s existing vocabulary; nothing new is
introduced.

---

## 1 · `spectra install` — the step count changes from 3 to 4

Existing steps 1–3 are unchanged in wording and behaviour, with one exception in step 3 (§ 2).

```text
[4/4] Registering Spectra with your other agents
```

The step **is not printed at all** when the plan is empty (FR-037, FR-038, research R11) — including for
every single-integration project, which is the common case. Such a run's output is byte-identical to the
previous release (SC-006), and the earlier steps still say `[1/3]`…`[3/3]`.

> **Consequence to implement deliberately**: the step count is decided *after* the plan is computed, so
> the header text for steps 1–3 must not bake in the total. Compute the plan before printing step 1, or
> pass the total in. Either is acceptable; a run that prints `[1/4]` and then never shows a fourth step is
> not.

### Disclosure, when the plan moves the default

Printed before the first activation (FR-014):

```text
› Spectra's commands are registered for kiro-cli only.
  claude is installed here but has no Spectra commands.

  To add them, each agent has to be made the project's default for a moment.
  This run will do that for: claude
  Then it will set the default back to kiro-cli, where it is now.
```

Then one line per activation, and the restoration:

```text
  ✓ claude — Spectra's commands registered
  ✓ default restored to kiro-cli
```

`spectra install` **does not ask** (FR-018). There is no flag or environment variable to skip the step
(FR-018, FR-047).

### The FR-013 case — only the default is uncovered

One activation, of the key that is already default. **No transient-default disclosure**, because nothing
moves:

```text
› Registering Spectra's commands for kiro-cli…
  ✓ kiro-cli — Spectra's commands registered
```

No restoration line: `restoration == NOT_NEEDED`.

### Exit codes

| Case | Exit | Constant |
| --- | --- | --- |
| every uncovered integration covered | 0 | `EXIT_OK` |
| plan empty for a stated reason | 0 | `EXIT_OK` |
| coverage attempted, any activation failed | 4 | `EXIT_DELEGATION` |
| restoring activation failed (`NOT_RESTORED`) | 4 | `EXIT_DELEGATION` |
| interrupted during the rotation | 130 | `EXIT_INTERRUPTED` |
| extension step failed (pre-existing behaviour) | 1 | unchanged |

The clarified rule (spec § Clarifications): **an attempt that fails is non-zero; an abstention with a
stated reason is zero.** A successful coverage step never masks a failed extension step, and its exit code
does not override the extension failure's (FR-022).

### `NOT_RESTORED` output

```text
✗ Could not set the default integration back to kiro-cli.
  The project is currently defaulted to claude.
  Restore it with: specify integration use kiro-cli
```

This is the only place the dependency's `integration use` is printed as advice, and it is printed to undo
something this run did — not as a remedy for coverage (FR-034, FR-040).

---

## 2 · `spectra install` — already-installed is a state, not a failure

Before invoking `specify extension add <id>`, the run checks whether that extension is present in the
project (research R6, FR-021). If it is:

```text
› Installing the Spectra extension…
✓ Spectra is already installed here (1.5.0) — nothing to download.
  Update it with: spectra update
```

The extension is not removed, re-downloaded, or overwritten (FR-023). The run continues to step 4 and
exits 0 when coverage completes (FR-020).

If the extension is **absent**, the add is attempted exactly as today. A non-zero exit keeps its existing
message and exit code, and then:

| Project state | Coverage step |
| --- | --- |
| an extension is present from an earlier run | still attempted; reported separately (FR-022) |
| no extension present | skipped, `skip_reason` "Spectra is not installed in this project" |

An `INCOMPLETE` extension folder counts as **absent** for the pre-check, so the add is attempted; if the
dependency refuses, the existing failure path runs and points at `spectra update` (research R6).

---

## 3 · `spectra update` — coverage after the walk

Order inside `cmd_update`, with the new step marked:

```text
1. classify project, check_all, render health table          (unchanged)
2. confirm the update plan                                    (unchanged)
3. overwrite disclosure + authorization                       (unchanged)
4. apply_updates walk                                         (unchanged)
5. re-read state (`after = check_all(...)`)                   (unchanged)
6. ── coverage: plan, disclose, ask once, apply ──            (NEW)
7. render the outcome table, now with a coverage row group     (MODIFIED)
8. failure / stall reporting, unauthorized report, closing line (unchanged)
```

Coverage is evaluated **whether or not** the Spectra agents were updated in this run (FR-024): the loss
may have been caused by an earlier run.

### The question

Asked once, defaulting to **no** (FR-025, FR-026):

```text
Spectra's commands are missing for: claude
  Adding them means making each agent the project's default for a moment,
  then setting the default back to kiro-cli, where it is now.

Register Spectra's commands for these agents? [y/N]
```

| Condition | Behaviour |
| --- | --- |
| `--yes` present | proceeds with no prompt (FR-027) |
| interactive, answered no | nothing activated; child rows `SKIPPED`, detail `"declined"` (FR-029, FR-030) |
| no TTY, no `--yes` | nothing activated; detail `"declined (re-run with --yes to authorize)"` (FR-028) |
| plan empty | no question, no output at all (FR-037) |

`--force` is **not** consulted here and must never be (FR-009, FR-049). `--yes` is the only flag that
authorizes coverage, and it authorizes only the activation — not any overwrite.

### The outcome row

A fifth row group in the **outcome** table, using the existing child-row rendering:

```text
  Specify CLI:     – skipped (already up to date)
  Core agents:     ✓ updated (0.16.5)
                     kiro-cli: ✓ updated (0.16.5)
                     claude:   ✓ updated (0.16.5)
  Spectra CLI:     – skipped (already up to date)
  Spectra agents:  ✓ updated (1.5.0)
  Agent coverage:  ✓ registered for claude
                     kiro-cli: – already registered
                     claude:   ✓ registered
```

**No fifth row is added to the health table** that `spectra version` and step 1 render (research R7).
That table reports currency for four components; feature 010 deliberately kept coverage out of it, and
this contract keeps that boundary. The row above belongs to the *outcome* table, which reports work
performed.

### Exit codes

Unchanged vocabulary. A coverage child `FAILED` or `restoration == NOT_RESTORED` makes the run report a
failure and return `EXIT_DELEGATION`, on the same terms as any other attempted component. A declined or
skipped coverage step never changes the exit code (FR-029).

`_say_what_happened`'s closing line must not claim completeness when coverage was declined — the same rule
it already applies to a declined overwrite.

---

## 4 · `spectra version` — the advisory is repointed

The advisory stays exactly where feature 010 put it: **below** the four rows, never a fifth row, never
touching the exit code (FR-042). Two changes:

**Before** (current):

```text
! Spectra commands are registered for kiro-cli only.
  claude is installed here but has no Spectra commands.
  To scaffold them: specify integration use claude
  (this changes the project's default integration for everyone.)
```

**After**:

```text
! Spectra commands are registered for kiro-cli only.
  claude is installed here but has no Spectra commands.
  Add them with: spectra install
```

The two lines about changing the project's default for everyone are **removed**, because the remedy no
longer does that (FR-039, FR-040). Silence conditions are unchanged: unknown coverage, full coverage, or
fewer than two integrations (FR-041).

---

## 5 · `spectra check`

Unchanged in itself. When it accepts the offer to install it delegates to `cmd_install` and therefore
inherits the coverage step, including the step's exit-code contract (spec § Assumptions).

---

## 6 · The command surface does not grow

| Guarantee | Requirement |
| --- | --- |
| no new subcommand | FR-047 |
| no new flag, on any command | FR-018, FR-047 |
| no new environment variable | FR-018, FR-047 |
| `--force` gains no new meaning and no new call site | FR-009, FR-049 |
| `OPTIONS` in `cli.py` and the rendered help are unchanged | FR-047 |

A test asserts the help output is byte-identical to the previous release.

---

## 7 · Supersession

This contract **supersedes** two published statements, and the reversal is deliberate:

1. **BRD-006 § 5.2 / spec 010 § Out of scope** — "Changing the project's default integration. Not as an
   end state and not transiently." Narrowed here to: *transiently, within a run that discloses it, and
   restored as that run's final act* (FR-014–FR-016, FR-043). The end state is unchanged, which is what
   the original boundary was protecting.
2. **BRD-006 § 5.2** — "Scaffolding or registering commands for non-default integrations… Spectra reports
   the gap instead of working around it. A future opt-in capability may revisit this." This feature is
   that revisit, and it is not opt-in: coverage is part of installing (FR-018, and the fifth clarification
   in spec § Clarifications).

The reasoning behind the reversal is recorded in BRD-007 § 2.2 and rests on findings F2–F4, which did not
exist when BRD-006 was written.

**Implementation obligation**: add a cross-note to
`specs/010-multi-integration-updates/contracts/cli-surface.md` § Supersession pointing here, so a reader
of the older contract is not misled. Feature 010 did exactly this to feature 007's health-check contract;
the same courtesy applies.

What is **not** superseded: the overwrite authorization gate. It remains reachable from exactly one call
site — the version upgrade — and this feature adds no second route (FR-049, research R5).
