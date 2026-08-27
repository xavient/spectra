# Contract: Chat Output

**Feature**: `018-flaky-test-detector` | **Plan**: [../plan.md](../plan.md)

Everything the developer sees. Eight shapes, each tied to the requirement that makes it mandatory. The
wording below is illustrative; the *content* obligations are not.

## 1. Suite discovery — before any candidate (FR-010)

```text
Flaky Test Detector — scope: whole tree
Suites found:
  web/   Jest    148 test files   (from jest.config.ts)
  api/   pytest   63 test files   (from pyproject.toml)
  e2e/   —         0 test files   (directory matches convention, nothing under it)
```

Every suite named, with framework, file count, and how it was identified. A suite that yielded nothing is
listed rather than omitted: silence reads as "there was nothing there", which is a different claim.

## 2. The candidate table (FR-019)

Columns exactly as they will appear in the file: ID, Test, File, Confidence, Suggested fix. Ordered High
→ Medium → Low, then by path (FR-016). Presented **before anything is written**.

```text
7 candidates: 3 high · 3 medium · 1 low

| ID     | Test                                | File                              | Confidence | Suggested fix                                                        |
| ------ | ----------------------------------- | --------------------------------- | ---------- | -------------------------------------------------------------------- |
| FT-001 | applies the promo code to the total | web/src/checkout/promo.test.ts:88 | High       | Replace the 500 ms sleep with an explicit wait on the updated total. |
```

## 3. Coverage and limits (FR-020)

```text
Coverage: web/ (148 files), api/ (63 files) — 1,204 tests examined.
Not covered: e2e/ — no test files found.
Could not parse: 4 files, listed in the plan if you create one.
Project guardrails: .specify/memory/constitution.md read — 3 rules bear on test code.
```

Mandatory on every run, including runs that find nothing. A partial pass presented as complete is a
defect, not a degradation.

## 4. Gate 1 — the plan (FR-021)

States what will happen, that it is a plan and not a code change, and waits.

```text
Shall I write this as a plan? It goes to .specify/memory/flaky-test-analysis.md as a task
list you can review and prune. No code changes at this step.
```

Where a file already exists and the new plan's scope is narrower, the FR-029a disclosure comes **first**,
naming the pending rows that would be dropped, and waits on its own answer.

## 5. After writing (FR-028)

```text
Written to .specify/memory/flaky-test-analysis.md — 7 items, none started.
I am waiting on your review. Delete any row you do not want fixed; anything left is what I will work.
```

The path, the waiting state, and the pruning instruction. All three are required.

## 6. Gate 2 — the fixes (FR-030)

```text
Ready to work the 7 remaining items. I will fix them in file order, tick each one off as it
lands, and leave anything I cannot fix confidently open with a reason. Nothing gets committed.
Go ahead?
```

## 7. The closing report (FR-037)

```text
5 of 7 fixed.

Left open:
  FT-002  the evidence is gone — the assertion was rewritten since the plan was generated
  FT-006  the real fix is in src/billing/invoice.ts (production code, out of scope for me)

Files changed:
  web/src/checkout/promo.test.ts
  web/src/flags/cache.test.ts
  web/src/support/clock.ts          (created)
  api/tests/conftest.py             (shared — affects every test in api/)

Nothing committed. Review with your usual diff; run the suite when you are ready.
```

Fixed count, every open item with its reason, every file changed with created files marked and
suite-wide changes called out (FR-032a), and the uncommitted state.

## 8. The state-check reports (FR-038, FR-039, FR-040)

**Pending rows.** Date, scope, counts, then three choices — and no analysis unless asked:

```text
An analysis from 2026-08-26 14:32 -07:00 is already here (scope: whole tree).
7 items — 5 fixed, 2 still open.
  1  continue with the 2 open items
  2  discard it and analyze again
  3  stop
```

**All complete.** Reports completion and asks before re-analyzing — never analyzes first:

```text
The analysis from 2026-08-26 is complete: all 7 items fixed.
Run the analysis again? A new plan would replace this file.
```

**Unparseable.** Says what could not be read and never offers a silent overwrite:

```text
.specify/memory/flaky-test-analysis.md is here, but I cannot read it — the Tasks table has no
recognizable rows. I have not changed it.
  1  analyze again (this would replace the file)
  2  stop
```

## The refusal messages

| Situation | Must say |
|---|---|
| `.specify/memory/` absent | What is missing, and where the file would go. Nothing created (FR-007) |
| No suite found | Where it looked and by which conventions. Nothing written (FR-011) |
| No candidates | Suites and coverage, zero candidates, no offer to create a plan (FR-018) |
| Re-analysis found nothing, a file exists | That the existing file is unchanged and may be deleted if no longer wanted (FR-041) |
| Gate declined | That nothing was written, or that no source was edited |
| No row survived review | That there is nothing to fix; the file stands (FR-036) |
| A guardrail blocked a fix | Which rule, by name (FR-033a) |

## What is never shown

- A candidate the agent did not read the source for (FR-017).
- A confidence rating of anything but High, Medium, or Low.
- A flakiness percentage, score, or failure rate — there is no run history to compute one from (R-004).
- A claim of full coverage when the run did not reach everything (FR-020).
- A suggestion to skip, retry, or quarantine a test as the remedy (FR-033).
