# Phase 1 — Quickstart: proving `speckit.spectra.impact` works

**Feature**: [spec.md](./spec.md) · **Plan**: [plan.md](./plan.md) · **Date**: 2026-09-03

Two layers of validation. The **repository suite** runs in seconds and asserts the rules on the command's text.
The **manual passes** need a throwaway Spec Kit project and a real agent, because the only way to know the
prompt works is to run it.

---

## Prerequisites

```bash
python3 --version          # 3.9+
specify --version          # Spec Kit on PATH
```

For the manual passes, a scratch project with something to find:

```bash
mkdir /tmp/impact-probe && cd /tmp/impact-probe
specify init .
specify extension add --dev /Users/alibahaloo/Projects/spectra/spectra
# restart the agent so it picks up the new command
```

A useful probe repository has: a migration directory, at least one route handler, a config file naming a table,
one string-keyed handler registry, and a `.env.example`. Any small service will do.

---

## Layer 1 — repository suite

```bash
cd /Users/alibahaloo/Projects/spectra
python -m unittest discover -s tests
python tools/generate_agent_docs.py --check
```

Expected: green, with these specifically:

| Assertion | Module |
|---|---|
| `impact.md` writes to `docs/impact-analysis/`, resolves the declared root, checks the publication signal, uses no legacy or absolute path | `test_doc_output_paths.py` |
| `impact-analysis-template` is registered both ways, its headings match the command's inline skeleton, all four layers appear, no hard-coded template path | `test_document_templates.py` |
| 47 agents, 16 available, 31 planned, 9 from Spec Kit; `impact` has a `command` because it is available | `test_roster_data.py` |
| The hard rules appear in the command text: no network, no URL, no credential, no secret reproduction, no absence-of-impact claim, write-once, draft-only status, five-question cap, no `spec_refs` | `test_impact_flow.py` (new) |
| Manifest, catalog, and zip agree on version 1.12.0 and 7 commands | `.github/workflows/ci.yml` — the Principle V drift job |
| No script or binary in the package | `test_document_templates.py` |

```bash
# the two that catch the most likely regressions, run alone
python -m unittest tests.test_doc_output_paths tests.test_document_templates -v
```

---

## Layer 2 — manual passes

Run in order; each builds on the last. Every one of these is a scenario from the spec, named so a failure maps
back to a requirement.

### Pass 1 — the core loop (User Story 1)

```text
/speckit-spectra-impact We want to email customers who leave items in their cart for more than 24 hours
```

| Check | Requirement |
|---|---|
| Pre-flight asks about scope before any scanning | FR-012 |
| At most five questions, one at a time, each with options, `Other`, and a reasoned recommendation | FR-029 to FR-032 |
| Document appears at `docs/impact-analysis/001-<name>.md` | FR-049, FR-050 |
| Every Findings item has a `path:line` that resolves to real content | FR-042, SC-001 |
| Impact rating names the trigger that produced it | FR-047 |
| Sources consulted states files read of files present, the scan mode, and terms searched with no hits | FR-044, FR-010b, FR-048 |
| `status: draft`, and `generated` has a time of day | FR-053a, FR-052 |
| Inputs section carries the paragraph verbatim | FR-052a |
| Nowhere does it say there is no impact | FR-041, SC-003 |
| `git status` shows exactly two new files | FR-005 |

### Pass 2 — skip a question (User Story 2)

Re-run, press enter on one question.

| Check | Requirement |
|---|---|
| The recommendation was used and the run did not block | FR-033 |
| Clarifications row says `defaulted` | FR-035 |
| If it was scope, data lifecycle, or contract compatibility, it also appears in risks | FR-034 |

### Pass 3 — another system, two ways (User Story 3)

Answer "no" to the scope question. Declare one system by local path (clone anything nearby) and one by a
sentence.

| Check | Requirement |
|---|---|
| Three forms offered; none required | FR-013 |
| No URL, credential, or login requested anywhere | FR-014 |
| The local path is searched for contract identifiers only, capped at 20 files | FR-026 |
| `git -C <the local path> status` is clean and its mtimes are unchanged | FR-015 |
| The described system appears as `declared-not-scanned` with a handoff item naming the team | FR-013, FR-055 |
| Point it at a nonexistent path: reason is `path-not-found`, run continues | FR-018 |

### Pass 4 — re-run and supersede (User Story 4)

Run twice with the same paragraph and the same attachments.

| Check | Requirement |
|---|---|
| Two documents exist; the second is `002` | FR-050, FR-051 |
| The first is unchanged apart from `status: superseded` and `superseded_by` | FR-005, FR-011 |
| The index has both rows with the relationship | FR-056 |
| Nothing was diffed, deduplicated, or refused | FR-051 |
| Hand-edit `001` to `status: approved`, re-run: the index row for `001` now says `approved`, and `001` itself is otherwise untouched | FR-056 |
| Delete `002`, run again: the next id is `003`, not `002` | FR-050 |

### Pass 5 — interrupt it (FR-051a)

Start a run and Ctrl-C during the scan.

| Check | Requirement |
|---|---|
| `docs/impact-analysis/` is byte-identical to before | FR-051a |
| No number was consumed — the next successful run takes the id the interrupted one would have | FR-051a |

### Pass 6 — a secret in the blast radius (FR-042a)

Add a file the scan will reach, containing something like
`const STRIPE_KEY = "sk_live_EXAMPLE_NOT_A_REAL_KEY";`, and describe a feature that touches it.

| Check | Requirement |
|---|---|
| The finding gives the location and the kind of secret | FR-042a |
| It states the value was deliberately not reproduced | FR-042a |
| `grep -r "sk_live_EXAMPLE" docs/impact-analysis/` finds nothing | FR-042a, SC-009a |
| The security lens fired and routed rather than judging | FR-037, FR-038 |

### Pass 7 — the two scan modes (FR-010a to FR-010d)

Run once in a project with `specs/` and a constitution, once in a bare repository.

| Check | Requirement |
|---|---|
| The spec'd run says it oriented on the specs and constitution | FR-010b |
| Blast-radius claims still cite code, not a spec | FR-010c |
| The bare run says the understanding was reconstructed from source | FR-010b |
| Introduce a spec that contradicts the code: the disagreement appears as a finding | FR-010c |
| Neither document records a relationship to any spec, and there is no `spec_refs` key | FR-010d, FR-054 |

### Pass 8 — template override (Principle VIII)

```bash
mkdir -p .specify/templates/overrides
cp .specify/extensions/spectra/templates/impact-analysis-template.md \
   .specify/templates/overrides/impact-analysis-template.md
# delete the "Effort & sequencing" section from the override
```

| Check | Requirement |
|---|---|
| The run reports the override path, not the extension path | FR-059 |
| The deleted section is absent and its omission is noted, not reinstated | FR-060 |
| Citations, confidence levels, the rating, and the coverage statement still appear | plan, VIII |
| Empty the override file: the run says so and falls through to the extension layer | FR-057 |

### Pass 9 — unattended (User Story 6)

```bash
echo "" | <agent> /speckit-spectra-impact --non-interactive "Add a nickname field to accounts"
```

| Check | Requirement |
|---|---|
| No prompt of any kind, including pre-flight | FR-062 |
| `status: draft`, every answer `defaulted — not confirmed` | FR-064 |
| Banner at the top when three or more were defaulted | FR-066 |
| A prior matching analysis is recorded as superseded in the new document, and the prior file is untouched, and the run says so | FR-065 |
| Run without the switch in the same piped session: it announces the detection, names the switch, and behaves identically | FR-062a |

### Pass 10 — publication signal (FR-049)

```bash
touch mkdocs.yml     # in a project with no declared artifact root
```

| Check | Requirement |
|---|---|
| The signal is surfaced and `documents/` recommended before anything is written | FR-049 |
| The question does not count against the five | FR-049 |
| With no answer obtainable, `documents/impact-analysis/` is used and the run says so | FR-049 |
| The `Artifact root:` line is offered, and the constitution is not edited | FR-005 |

---

## Clean up

```bash
cd / && rm -rf /tmp/impact-probe
```

---

## What "done" means

- Layer 1 green, including the three existing modules that gain this command.
- Passes 1 through 10 observed on at least one agent, and Passes 1, 5, and 6 on a second — 5 and 6 are the two
  where a prompt-expressed rule is most likely to be quietly ignored.
- SC-004 and SC-005 are **not** provable here. They need the retroactive exercise: run the command against five
  features this repository has already shipped and compare its findings to what actually broke. That is
  post-merge work, and the numbers belong in the changelog entry for whichever release reports them.
