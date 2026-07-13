# Quickstart & Validation: Domain Analyzer

How to build, install, and validate the `domain-analyzer` extension end-to-end. There is no
automated test suite — validation is manual installation into a throwaway Spec Kit project
(Constitution Principle I / Workflow step 4). References: [plan.md](./plan.md),
[contracts/proposal-file.md](./contracts/proposal-file.md),
[contracts/command-interface.md](./contracts/command-interface.md),
[data-model.md](./data-model.md).

## Prerequisites

- This repo checked out on branch `001-domain-analyzer`.
- Python 3 (for `build_packages.py`).
- Spec Kit CLI (`specify`) installed, and a throwaway Spec Kit project to install into.

## Build & register

```bash
# from repo root
python3 build_packages.py            # regenerates docs/ incl. packages/domain-analyzer.zip
```

Expected: no `!` URL-drift warnings; `docs/catalog.json` and `docs/packages/domain-analyzer.zip`
now include the extension. (Commit `docs/` per Principle V.)

## Install into a throwaway project

```bash
cd /path/to/throwaway-speckit-project
specify extension add --dev /path/to/spectra_extensions/domain-analyzer
# restart your agent so it picks up the new command/skill
```

## Validation scenarios

Each maps to a user story / acceptance scenario in [spec.md](./spec.md).

### Scenario 1 — Fresh run produces an opt-in proposal file (US1)

1. In a throwaway project **with some code and docs but no proposal file**, run the command
   (Claude: `/speckit-domain-analyzer-analyze`).
2. **Expect**: `.specify/memory/domain-analysis.md` is created with ≥1 candidate; each has
   `id`, `section`, ≥1 `evidence` path, `confidence`, `status`.
3. **Expect**: every candidate checkbox is `- [ ]` (none pre-selected).
4. **Expect**: chat reports the file path, a one-line inferred domain, and the next steps
   (review → check → run `/speckit-constitution`).

### Scenario 2 — SME opt-in handoff (US2)

1. Edit the file: check `- [x]` two candidates, edit the wording of one checked item, leave
   the rest `- [ ]`.
2. Run `/speckit-constitution` referencing the file.
3. **Expect**: only the two checked items are incorporated; the edited wording is what lands;
   unchecked items are absent.
4. Re-do with **nothing** checked → **Expect**: zero guardrails added.

### Scenario 3 — Re-run preserves prior decisions (US3)

1. With the reviewed file from Scenario 2 in place, change the codebase (add a new
   characteristic), then re-run the command.
2. **Expect**: every prior candidate keeps its exact checkbox state, edited text, and order.
3. **Expect**: new candidates appear under `## New in this run (YYYY-MM-DD)`; chat states how
   many were appended.
4. Re-run again with **no** relevant change → **Expect**: no duplicate candidates added.

### Scenario 4 — Amend an existing constitution with deltas only (US4)

1. In a project whose `.specify/memory/constitution.md` already asserts a guardrail, run the
   command.
2. **Expect**: no candidate duplicates that already-ratified guardrail.
3. **Expect**: any overlapping-but-different candidate shows `status: amends: <Principle>`.

### Edge checks

- **Sparse project** (little code/docs): fewer candidates, `confidence: Low`, and the file/chat
  says evidence was thin — no invented rules.
- **No existing constitution**: candidates still produced; file notes the constitution will be
  created from the approved set.

## Done / acceptance

- [ ] Scenarios 1–4 pass in a throwaway project.
- [ ] Edge checks behave as described.
- [ ] `python3 build_packages.py` runs clean and regenerated `docs/` committed.
- [ ] No file other than `.specify/memory/domain-analysis.md` is written in the target project.
