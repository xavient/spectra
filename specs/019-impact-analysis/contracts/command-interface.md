# Contract — Command Interface

**Command**: `speckit.spectra.impact` · **File**: `spectra/commands/impact.md` · **Effect**: read-write

The command's public surface. Anything not listed here is not part of the contract.

## Name and invocation

| | |
|---|---|
| Manifest name | `speckit.spectra.impact` |
| Namespace rule | `speckit.<extension-id>.<command>`, so the middle segment is `spectra` (Principle III) |
| Argument form | Generic `$ARGUMENTS` — never an agent's invocation syntax |
| Trigger | Differs per agent; the extension's own README and the agent's command list show the exact form |

## Arguments

Everything arrives in one argument string. Order is free; the intent is whatever is left after the flags and
paths are taken out.

| Argument | Required | Meaning |
|---|---|---|
| Feature intent | **Yes** | One paragraph: what should be true after this ships that is not true today (FR-006) |
| Document paths | No | `.md`, `.txt`, `.pdf`, `.docx` — feature request, brief, epic, external-system description, prior analysis (FR-008) |
| `--non-interactive` | No | No prompt of any kind, including pre-flight (FR-062) |
| `--seed-cap N` | No | Seed set size. Default 30 |
| `--hops N` | No | Graph expansion depth. Default 2 |
| `--max-files N` | No | Total project files read. Default 80 |
| `--identifier-cap N` | No | Contract identifiers swept. Default 50 |
| `--per-system-cap N` | No | Files read per declared local system. Default 20 |

**Not accepted, by design**: a repository URL, a credential, a token, a login, or any instruction to clone or
download (FR-014). Offered one, the command explains it reads only local directories and records the system as
described.

**The five-question cap is not configurable** (FR-029).

## Refusals and degradations

| Condition | Behaviour |
|---|---|
| No feature intent | Stop, name what to supply, scan nothing (FR-007) |
| No project-wide text search available | Continue on what can be traversed, state the limitation, report reduced coverage (FR-027) |
| Attachment unreadable, missing, or unsupported | Record by name with the reason, continue (FR-008) |
| Declared path unreadable | Record the distinguishing reason, drop to `declared-not-scanned`, continue (FR-018) |
| A cap reached | Report the cap and what was left out (FR-045) |
| Cannot obtain an answer, no switch passed | Announce once, name the switch, proceed as if passed (FR-062a) |
| Declared artifact root unusable | Say why, fall back to the default (FR-049) |

**The command never fails a run over an input it can describe.** The only stop is a missing intent.

## Interaction order

```text
pre-flight  ──▶ supersede detection (if a candidate exists)
            ──▶ "is this the only repository?"           ─┐
            ──▶ per system: form and value               ─┴─ do not count against the five
scan        ──▶ structural map · expansion · seeds · 2-hop · dynamic sweep
            ──▶ ranked identifier sweep · per-system consumer detection
questions   ──▶ at most five, one at a time, each with options, Other, and a reasoned recommendation
write       ──▶ document · index · (confirmed) two fields of the superseded document
```

Pre-flight precedes the scan; questions follow it, because a question is only worth asking about something the
scan found ambiguous (FR-030).

## Write scope

Three writes, all at the end (FR-051a):

1. `<artifact-root>/impact-analysis/NNN-<name>.md`
2. `<artifact-root>/impact-analysis/README.md`
3. `status` and `superseded_by` of one prior analysis — on explicit confirmation only

**Never**: the constitution, a spec, a branch, a commit, anything under `specs/`, anything outside the project,
anything inside a declared local path (FR-005, FR-015, FR-054).

## Guarantees a caller can rely on

- No network request, no credential, no login (FR-014).
- No secret value reproduced, in the document or in the session (FR-042a).
- An interrupted run leaves the folder byte-identical and consumes no sequence number (FR-051a).
- No existing analysis is overwritten, amended, diffed, or deduplicated — identical input twice yields two
  reports (FR-051).
- `status` is `draft` on every run (FR-053a).
- No compliance verdict, certification claim, or reproduction of a routed agent's analysis (FR-038).
- No statement that there is no impact; at most, that none was found in what was scanned (FR-041).
