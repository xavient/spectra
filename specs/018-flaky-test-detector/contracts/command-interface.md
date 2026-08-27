# Contract: Command Interface

**Feature**: `018-flaky-test-detector` | **Plan**: [../plan.md](../plan.md)

What the command is called, what it accepts, what it is permitted to do, and — stated as explicitly as
the permissions — what it must refuse.

## Registration

```yaml
# spectra/extension.yml → provides.commands[]
- name: "speckit.spectra.flaky-test-detector"
  file: "commands/flaky-test-detector.md"
  description: "Find the tests that pass and fail on the same code by reading the test source alone,
    report each with a confidence rating and a concrete fix, then — behind two explicit gates — write a
    resumable task list to .specify/memory/flaky-test-analysis.md and apply the fixes you approve."
```

| Property | Value |
|---|---|
| Command name | `speckit.spectra.flaky-test-detector` |
| Command file | `spectra/commands/flaky-test-detector.md` |
| Namespace segment | `spectra`, equal to the extension `id` — required by Spec Kit's `^speckit\.<extension-id>\.<command>$` pattern |
| Roster id | `flaky-test-detector`, phase `testing-quality`, type `add-on`, provider `spectra` |
| Effect | `read-write` — the extension already declares this; no manifest change |
| Front matter | YAML with a `description`, per Principle III |
| Runtime tool requirements | **None.** Not `git`, not `gh`. The command must not gate on any binary |
| Hooks | None registered (R-011) |
| Templates | None registered (R-002) |

## Arguments

`$ARGUMENTS` is optional and carries a scope.

| Form | Meaning |
|---|---|
| *(empty)* | Analyze the whole working tree |
| A project-relative path | Analyze only what is under it |
| A suite name as reported by a prior run | Analyze only that suite |

**Rules.**

- The scope actually analyzed MUST be stated in chat and recorded in the file header (FR-002, FR-023).
- An argument that resolves to nothing is reported as such; the command MUST NOT silently widen to the
  whole tree, because the developer would then get a plan they did not ask for.
- The scope is what the FR-029a comparison reads. A narrower scope than the file it would replace
  triggers disclosure before any write.

## The governing rule

> **Read anything, execute nothing, and change only test code the developer approved row by row.**

Every permission below is a narrowing of that sentence, and every refusal is a case where an agent
would otherwise be tempted to widen it.

## Permitted actions

| Action | Bounded by |
|---|---|
| Read any file in the working tree | — |
| Read the consumer project's `.specify/memory/constitution.md` | FR-033a; absence is reported, not assumed |
| Read `.specify/memory/flaky-test-analysis.md` | The first act of every run (FR-006) |
| Create or replace `.specify/memory/flaky-test-analysis.md` | Only after Gate 1 (FR-021), only wholesale (FR-029) |
| Edit test code and test-support files | Only after Gate 2, only rows surviving review (FR-030, FR-031) |
| Create a new test-support file | Only where a fix requires one (FR-032) |
| Rewrite a row's state marker and the progress count | After each applied fix, before the next (FR-034) |

## Refusals

These are not defaults. No argument, configuration, or instruction in the session enables them.

| Refusal | Requirement |
|---|---|
| Execute tests, builds, or package commands — including to verify a fix it just applied | FR-003 |
| Install a dependency or add a test library | FR-003, FR-032 |
| Reach the network | FR-003 |
| Commit, stage, push, create a branch, or open a pull request | FR-004 |
| Create or edit production source | FR-005, FR-032 |
| Edit project governance, including the constitution it reads | FR-005 |
| Write anywhere outside the project | FR-005 |
| Weaken a test to make it pass — delete or loosen an assertion, skip it, mark it expected-to-fail, wrap it in a retry, or lengthen a sleep | FR-033 |
| Open or edit a test whose row the developer deleted | FR-031 |
| Re-open a row already marked `[x]` | FR-038 |
| Overwrite an unparseable file without asking | FR-040 |
| Create a second analysis file, a dated variant, or append a second analysis | FR-008 |
| Create `.specify/memory/` unannounced | FR-007 |
| Report a candidate in a file it did not read | FR-017 |
| Lower its bar to avoid an empty result | FR-018 |

## Ordered flow and its gates

| Step | Action | Gate |
|---|---|---|
| 1 | State check — four branches (FR-006) | — |
| 2 | Suite discovery, reported before any candidate (FR-010) | — |
| 3 | Static analysis across the eight signal categories (FR-012) | — |
| 4 | Chat table plus coverage statement (FR-019, FR-020) | — |
| 5 | Ask to write the plan, stating this produces a plan and not a code change | **Gate 1** (FR-021) |
| 6 | Write the file; report the path, that it is waiting, and that rows may be deleted (FR-028) | — |
| 7 | Ask to apply the fixes | **Gate 2** (FR-030) |
| 8 | Re-read the file; work surviving rows in order, re-checking evidence per row (FR-031, FR-031a) | — |
| 9 | Closing report — fixed, left open and why, files changed, nothing committed (FR-037) | — |

**Gate semantics.** Each gate is a plain question that states what will happen and waits for an answer.
There is no bypass argument and no unattended mode (R-005). Declining at either gate leaves the working
tree and any existing file exactly as they were, and the command says so.

**A run may enter at step 7** when the state check found pending rows and the developer chose to continue
(FR-038). It never enters at step 8: the approval is always asked for.

## Exit paths

| Path | Wrote anything? | Reported |
|---|---|---|
| `.specify/memory/` missing | No | What is missing and where the file would go |
| No test suite found | No | Where it looked and by which conventions |
| Suites found, no candidates | No | Suites, coverage, zero candidates. Any existing file left unchanged |
| Gate 1 declined | No | That nothing was written |
| Gate 2 declined | File only | That no source was edited |
| No row survived review | File only | That there is nothing to fix |
| Fix run completed | File + test code | Fixed count, open count with reasons, files changed, uncommitted |
| Stopped at the state check | No | Nothing further read or changed |

## Reporting obligations

The command reports, without being asked:

- the scope it analyzed, and how it differed from the scope requested if it did;
- every suite found, with framework and file count, **before** any candidate;
- what it could not examine — skipped, unparseable, or beyond what it could read;
- whether the project declared a constitution, and when a guardrail blocked a fix, which rule;
- every file it created, and every change reaching tests beyond the row that authorized it;
- that its changes are uncommitted and awaiting review.
