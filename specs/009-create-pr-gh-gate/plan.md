# Implementation Plan: Create PR Gates on `gh`

**Branch**: `009-create-pr-gh-gate` | **Date**: 2026-08-19 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/009-create-pr-gh-gate/spec.md`

## Summary

Make `speckit.spectra.create-pr` treat an unusable `gh` the way `speckit.spectra.review-pr` does: a **hard
pre-flight gate** with two distinguishable remedies, taken before any project read or remote call, instead
of a graceful degradation that printed a manual fallback the user could not run. The manual fallback moves
to where it works — failures **after** the gate — and gains the one fact it never reported: whether the
source branch already reached the remote.

**Technical approach**: the whole behavioural deliverable is one Markdown instruction file,
`spectra/commands/create-pr.md`. Steps 2 and 2a are rewritten (gate + post-gate degradation), Step 7 moves
the body onto standard input and gains a failure path, the governing-rule section gains `gh`-exclusivity,
and a fork/default-branch heuristic collapses into one structured `gh repo view --json` call. Nothing is
added to `spectra_cli/`; no code executes. Everything else is Principle V synchronization — manifest
comment and version, changelog, extension README, roster prose, catalog, and a rebuilt package — plus
supersession notes on the earlier specs that recorded the old behaviour.

The work divides into three tracks: **(1)** rewrite the command file; **(2)** publish the change across the
manifest/catalog/package/docs set; **(3)** validate — the repository's own checks now, the runtime scenarios
against a live repository.

## Technical Context

**Language/Version**: Markdown with YAML front matter — Spec Kit generic command format. No programming
language; the coding agent is the runtime.

**Primary Dependencies**: `gh` (GitHub CLI) — **now hard-gated**, verified against **2.97.0 (2026-07-31)**;
`git` for branch and remote inspection. Both already declared in `spectra/extension.yml` under
`requires.tools`, both staying `required: false` (research R-009).

**Storage**: None. The command holds no state between runs; the only durable artifacts are the pushed
branch and the pull request.

**Testing**: Manual end-to-end execution of [quickstart.md](./quickstart.md) S1–S7 against a throwaway Spec
Kit project and a live GitHub repository, plus repository-level automation for the publication set —
`python tools/generate_agent_docs.py --check`, `python -m unittest discover -s tests`, and the CI `catalog`
job's version/description/zip-drift assertions reproduced locally (S8).

**Target Platform**: Any coding agent Spec Kit supports (Claude, Kiro, Gemini, Copilot, Cursor, …) on macOS,
Linux, or Windows. No agent-specific syntax; no shell-specific construct beyond what `gh` itself documents.

**Project Type**: Spec Kit extension command — a behavioural change to one Markdown instruction file inside
the existing single extension.

**Performance Goals**: Not latency-bound. The one measurable movement is call count: **4–7 `gh`/`git` calls**
per run versus 5–8 before, because one structured query replaces the fork heuristic and the separate
default-branch lookup (contracts/gh-operations.md, Call budget).

**Constraints**: Read-write effect with explicit confirmation before each of the two permitted mutations;
zero mutations on a failed gate; no credentials held; `gh` as the exclusive route to GitHub; GitHub-only
scope unchanged.

**Scale/Scope**: One command file modified (203 lines today; the rewrite touches roughly a third of it and
adds an edge-case table). 15 functional requirements, 7 success criteria, 3 prioritized user stories. No new
command, so the extension stays at **5 commands** and the roster is unchanged.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Evaluated against Spectra Constitution **v1.5.0** (ratified 2026-07-12, last amended 2026-08-16).

| Principle | Requirement | Assessment |
|---|---|---|
| **I. Spec-Driven Development** | Non-trivial work flows through `specify` → `plan` → `tasks` → `implement`; specs under `specs/` | **PASS** — `specs/009-create-pr-gh-gate/` created by the specify step on a branch made by the `before_specify` git hook; no file in `spectra/` is touched before `tasks.md` exists. The change reverses a published decision, which is precisely the kind of work that must not be an ad-hoc edit. |
| **II. A Single Self-Contained Extension** | Every capability is a command file under `spectra/commands/`, registered in the single `spectra/extension.yml` | **PASS** — modifies one existing command file. No new file, no new extension folder, no new dependency between extensions. |
| **III. Agent-Agnostic Commands** | `speckit.spectra.<command>` namespace, `$ARGUMENTS` input, front-matter `description`, registered in `provides.commands` | **PASS** — name, arguments, front matter, and registration are all unchanged (contracts/command-interface.md, Registration). The added instructions name `gh` flags, which is tool-specific, not agent-specific. |
| **IV. Context-Aware by Default** | Commands read real project context before acting | **PASS, and sharpened** — the command still reads the constitution's branching section and the `git` branching config to derive the target (002 FR-002). What changes is *ordering*: it no longer performs those reads on a run that provably cannot open a pull request. Reading context to produce a message the user cannot act on is not context-awareness. |
| **V. Catalog and Package in Sync** | The same change registers the roster entry, rebuilds the zip, updates `catalog.json` and `docs/index.html`, regenerates structured listings, and hand-writes prose | **PASS by plan** — FR-015 makes it binding; research R-010 and R-012 enumerate exactly which files move and which correctly do not (`agents-list.json` and `docs/index.html` describe the command without asserting degradation; the landing page fetches version and roster at load). The zip rebuild is mandatory — CI diffs it against the folder. |
| **VI. Two Independently-Versioned Release Channels** | A changed command bumps the extension/catalog version per SemVer; the CLI channel is untouched; the catalog is never tagged | **PASS** — `spectra/extension.yml` and the `catalog.json` mirror go `1.4.0` → **`1.5.0`** (MINOR; research R-012 records why not MAJOR). Root `VERSION` is **not** touched, no tag, no GitHub Release. |
| **Publishing & Distribution Standards** | A `spectra/CHANGELOG.md` entry under the new version; `requires.speckit_version` reflects what was tested | **PASS by plan** — 1.5.0 entry states the reversal explicitly and leaves the 1.4.0 entry as history. `requires.speckit_version: ">=0.11.0"` is unchanged and re-confirmed against the Spec Kit release used for validation (0.12.14 per `.specify/init-options.json`). |
| **Version Control & Branching Strategy** | One branch per spec; branch name equals the spec directory name; branch created before specifying | **PASS** — branch `009-create-pr-gh-gate` equals `specs/009-create-pr-gh-gate`, created by the `before_specify` hook before the spec was written. |

**Gate result: PASS — no violations.** Complexity Tracking is therefore empty and omitted.

### Re-check after Phase 1

Design artifacts introduce no new structure: two contracts, a data model of run-time concepts, and a
quickstart. No new file ships to users, no dependency is added, and the manifest's shape is unchanged.
**Still PASS.**

### The one constitutional point worth stating plainly

Principle V's sync obligation is what makes this feature bigger than its one behavioural edit. Six shipped
or spec documents assert that `create-pr` degrades (research R-010). Five are corrected in place; the sixth
is a changelog entry, which stays as written because a changelog records what was true at the time. If the
in-place five were deferred to a follow-up commit, the repository would ship a command whose documentation
contradicts it — the exact drift Principle V exists to prevent, and it would be visible to users on the
landing page and in `AGENTS_LIST.md`.

## Project Structure

### Documentation (this feature)

```text
specs/009-create-pr-gh-gate/
├── spec.md                        # Feature specification (specify step) — 15 FRs, Supersedes table
├── plan.md                        # This file
├── research.md                    # Phase 0 — 12 resolved decisions, gh 2.97.0 verified
├── data-model.md                  # Phase 1 — Preflight, GateFailure, MutationState, PostGateFailure
├── quickstart.md                  # Phase 1 — S1–S9 validation scenarios
├── contracts/
│   ├── command-interface.md       # Flow, gates, exit paths, the replacement degradation policy
│   └── gh-operations.md           # The closed set of gh calls, OP-1…OP-5
├── checklists/
│   └── requirements.md            # Spec quality checklist (16/16)
└── tasks.md                       # Phase 2 output (tasks step — NOT created here)
```

### Source Code (repository root)

This feature ships instructions, not code. Every file the implementation touches:

```text
spectra/
├── commands/
│   └── create-pr.md       # MODIFIED — the entire behavioural deliverable
├── extension.yml          # MODIFIED — requires.tools comment; version 1.4.0 → 1.5.0
├── CHANGELOG.md           # MODIFIED — 1.5.0 entry (1.4.0 left as history)
└── README.md              # MODIFIED — create-pr §1 + closing paragraph; review-pr's "unlike create-pr" line

catalog.json               # MODIFIED — version 1.5.0, updated_at; command count unchanged at 5
AGENTS_LIST.md             # MODIFIED — hand-written prose for id=create-pr and id=review-pr
docs/packages/spectra.zip  # REBUILT — python tools/build_package.py (CI diffs it against spectra/)

specs/002-open-pr/spec.md               # ANNOTATED — supersession note on FR-007 and SC-006
specs/002-open-pr/quickstart.md         # ANNOTATED — supersession note on S6
specs/008-review-pr/contracts/command-interface.md   # ANNOTATED — §Degradation policy
specs/008-review-pr/research.md         # ANNOTATED — R-009

agents-list.json           # UNCHANGED — its create-pr description never mentioned degradation
docs/index.html            # UNCHANGED — fetches version, description, and roster at page load
README.md                  # UNCHANGED — the generated Agents table depends on the roster, which is unchanged
VERSION                    # UNCHANGED — CLI channel (Principle VI)
```

**Structure Decision**: no structural change. The single self-contained `spectra/` extension is the only
shipped artifact, its command lives where Principle II requires, and the publication set is exactly the one
Principle V enumerates. The `specs/` annotations are documentation hygiene, not deliverables: the spec's
Supersedes table is the authoritative record, and each annotation is a one-line pointer to it so a reader
who lands on the old requirement is not misled.

## Phase 0 — Research

Complete. See [research.md](./research.md): 12 decisions, every `gh` behaviour verified against 2.97.0 by
reading `--help` output, with the two quickstart simulation mechanisms (restricted `PATH`, empty
`GH_CONFIG_DIR`) confirmed by execution.

Three findings changed the design rather than merely documenting it:

- **`gh auth status --json` always exits zero** even when authentication is broken, so the gate must not use
  it (R-003).
- **`gh pr list --head` rejects `owner:branch` while `gh pr create --head` accepts it** (R-008), which is
  why the fork case must ask rather than infer — a guessing implementation would dedup against one head and
  create against another.
- **The gate retires a fallback.** With `gh` guaranteed past Step 2, the `git symbolic-ref
  refs/remotes/origin/HEAD` default-branch fallback covers a state that can no longer occur (R-007). The
  change removes logic rather than adding it.

## Phase 1 — Design

Complete:

- **[data-model.md](./data-model.md)** — `Preflight` with a normative evaluation order, `GateFailure` with
  its four kinds and their single remedies, `MutationState` as the fact that separates "nothing happened"
  from "half of it happened", `PostGateFailure`, seven validation rules, and the closed set of six run
  outcomes.
- **[contracts/command-interface.md](./contracts/command-interface.md)** — the ten-step flow with the four
  changed rows marked, twelve enumerated exit paths, and the degradation policy that replaces 008's.
- **[contracts/gh-operations.md](./contracts/gh-operations.md)** — OP-1…OP-5 as the closed set, post-gate
  error interpretation including exit code 4, an explicit out-of-contract list, and the call budget.
- **[quickstart.md](./quickstart.md)** — S1–S9 with a coverage map to every FR and SC.

## Phase 2 — Task planning approach

The tasks step will produce a dependency-ordered `tasks.md` shaped by two facts:

1. **All behaviour lives in one file**, so the command-file tasks are strictly sequential — no `[P]` across
   them — and are ordered gate → scope → repository facts → post-gate degradation → body/stdin →
   edge-case table.
2. **The publication set is atomic.** Version, changelog, README, roster prose, catalog, and zip must land
   in the same change (Principle V), and the zip rebuild must come **after** every `spectra/` edit or CI's
   drift check fails. The generator check and the test suite run last, as gates rather than as steps.

Validation splits into what is verifiable in the repository now (S8, S9, plus reading the command file
against the `gh` contract) and what needs a live GitHub repository (S1–S7). The latter is explicitly marked
so the change is not reported as validated beyond what was actually run.
