# Implementation Plan: Feature Impact Analysis

**Branch**: `019-impact-analysis` | **Date**: 2026-09-03 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/019-impact-analysis/spec.md`

## Summary

A seventh Spectra command, `speckit.spectra.impact`, and the **third document agent** — after `adr` and
`brd` — so the first one that inherits Principles VII and VIII rather than establishing them. It takes one
paragraph of feature intent, scans the project, and writes a numbered impact analysis into
`<artifact-root>/impact-analysis/` whose every finding cites a file and line, for a Business Analyst to take
to a stakeholder go / no-go gate before any specification work begins.

Four properties shape every decision below.

**It is read-mostly and writes in one act.** The only writes are the new document, the folder index, and — on
explicit confirmation — two front-matter fields of the analysis being superseded. Everything before that
final write is reading and asking, which is what lets FR-051a promise that an interrupted run leaves the
folder untouched and consumes no sequence number.

**It makes no network request and holds no credential.** The design spec's shallow-clone / API-read /
raw-URL-read matrix was removed during clarification: other systems are declared as free text, a document,
or a **local directory path** read in place. That keeps the command inside the promise the project README
makes on Spectra's behalf — that it opens no channel the host agent does not already use — and it deleted an
entire failure taxonomy from the design.

**Its trustworthiness rules are the product.** Five hard rules (FR-041 to FR-048) plus a three-level
confidence taxonomy are what separate this from a plausible-sounding summary: absence of evidence is never
reported as absence of impact, every finding carries a citation, external contract changes always escalate,
coverage is stated per system, and caps degrade loudly. A run that produces a confident report with a hole in
it has failed even if every sentence in it is true.

**It never quotes a secret.** FR-042a is the one rule with no precedent in the roster, and it exists because
the other rules created the hazard: a mandatory `path:line` citation, a security lens that fires exactly when
the scan touches secrets, and a default output folder that some projects publish.

The command file is the deliverable. No script ships and no binary ships — search, traversal, caps, template
resolution, and root resolution are all expressed as prompt instructions, because that is the only form that
survives Principle III and the Markdown-only supply-chain promise.

## Technical Context

**Language/Version**: Markdown command prompt in Spec Kit's generic format; Python 3.9+ (standard library
only) for this repository's own tools and tests

**Primary Dependencies**: Spec Kit `>=0.11.0`. **No runtime tool dependency and no network** — unlike
`create-pr` and `review-pr` this command must not gate on `git` or `gh`, and unlike every other command it
must state explicitly that it makes no outbound request (FR-014)

**Storage**: the target project's `<artifact-root>/impact-analysis/` — one numbered Markdown document per run
plus an index. Nothing under `.specify/`, no cache, no cross-run state beyond the documents themselves

**Testing**: `python -m unittest discover -s tests`; `python tools/generate_agent_docs.py --check`; a new
`tests/test_impact_flow.py`; three existing modules gain this command
(`test_doc_output_paths.py`, `test_document_templates.py`, `test_roster_data.py`); the manual zip-install pass
in `test/README.md`

**Target Platform**: every coding agent and OS Spec Kit supports. Search, expansion, capping, and file
reading are prompt-expressed, so nothing depends on a shell flavour or on ripgrep being present

**Project Type**: Spec Kit extension command — a prompt file under `spectra/commands/`, a registered template
under `spectra/templates/`, plus the publishing surface Principle V requires

**Performance Goals**: not latency-bound, but the **only Spectra command with a stated time target**:
SC-002 puts a BA from one paragraph to a document in under 15 minutes. Five caps enforce it — 30 seed files,
2 hops, 80 project files, 50 swept identifiers, 20 files per declared system — and FR-045 makes reaching any
of them a disclosure rather than a silent truncation

**Constraints**: Markdown only, no scripts or binaries; agent-agnostic `$ARGUMENTS`; no network request and no
credential (FR-014); no write outside the project and no modification of a declared local path (FR-015); no
spec created, referenced, or linked (FR-054); no commit, branch, or constitution edit (FR-005); no secret
value reproduced anywhere (FR-042a); write once at the end (FR-051a)

**Scale/Scope**: 1 new command file; 1 new shipped template; 2 manifest entries; 1 **new** roster entry; 1
catalog entry; 1 changelog entry; 1 rebuilt zip; ~4 documentation surfaces including a hand-authored prose
block; 1 new test module plus three census/registry updates

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Note |
|---|---|---|
| I. Spec-Driven Development | ✅ | This spec/plan/tasks set on branch `019-impact-analysis`, clarified before planning (5 of 5 questions). |
| II. A Single Self-Contained Extension | ✅ | One new file under the existing `spectra/commands/`, one under `spectra/templates/`. No new extension folder, no dependency on another extension. |
| III. Agent-Agnostic Commands | ✅ | Text only, `$ARGUMENTS` for intent, attachments, and cap flags. The design spec's ripgrep and `git clone --depth 1` are generalized to capability statements — see [research.md](./research.md) §1. |
| IV. Context-Aware by Default | ✅ | FR-009 reads the constitution, the project's own specs, source, ADRs, contracts, migrations, tests, and CI. FR-010a makes the *presence* of specs change the scan strategy, which is the strongest reading of this principle in the roster. |
| V. Catalog and Package in Sync | ✅ | Manifest, roster, catalog, changelog, zip, landing page, generated regions, and a new hand-authored prose block all move in the same change. |
| VI. Two Independently-Versioned Channels | ✅ | Extension channel only: 1.11.1 → 1.12.0. `VERSION` untouched, no tag, no Release. |
| VII. Documents Under One Declared Root | ✅ | **Engaged.** `<artifact-root>/impact-analysis/NNN-<name>.md`, declared root honoured, publication check before defaulting. Two sub-questions argued below. |
| VIII. Shaped by Overridable Templates | ✅ | **Engaged.** New registered `impact-analysis-template`, resolved through the four-layer stack, inline skeleton last, resolved path reported. |

**Amendment classification**: none. No principle is added, redefined, or loosened.

**Extension version classification**: MINOR — 1.11.1 → 1.12.0. A command is added; none is renamed or
removed, and no existing command's behaviour changes. `catalog.json` `provides.commands` goes 6 → 7 and
`provides.templates` gains a fifth entry.

### VII: two sub-questions that need an argument, not a checkmark

**Does an index file violate "exactly one artifact type per folder"?** No. Principle VII's rule is about
*artifacts* — numbered deliverables — and the index carries no sequence number, describes the folder rather
than a feature, and exists so that a BA can find the current analysis six months later. It is navigation, and
`<artifact-root>/impact-analysis/README.md` is where it goes. The distinction is worth stating because
FR-056's refresh rule makes the index the one file this command rewrites on every run, and a reader of the
principle could otherwise object.

**Is the superseded-status write inside the promised scope?** VII requires a superseded *location* to be read,
reported, and left alone. That clause is about the pre-1.6.0 folders, not about a sibling document in the
canonical folder, so it does not forbid this — but the write is still the one non-additive thing the command
does, so it is gated three ways: it happens only on an explicit confirmation that defaults to yes but must be
given (FR-011), it touches exactly two fields (FR-005), and in a non-interactive run it does not happen at all
and the run says so (FR-065). The new document records `supersedes:` regardless, so the relationship survives
even when the prior file is untouched.

**Numbering has no legacy folder to read.** VII's sequence-continuity clause requires reading superseded
locations so a cut-over cannot produce a duplicate `001`. This artifact type is new, so there is nothing to
read — but FR-050's rule is stated as *highest present plus one* rather than *count of files*, which is the
same defence against a gap that VII's clause provides against a split folder.

### VIII: what the template may and may not shape

The document is a durable Markdown deliverable a human reads, so VIII applies in full and the structure ships
as `spectra/templates/impact-analysis-template.md`. Two boundaries need recording, because "honour, do not
repair" has teeth here.

**A team may delete a section, including a lens.** If an override drops "Effort & sequencing", the command
notes the omission and does not reinstate it. That is VIII working as designed.

**The trustworthiness rules are not part of the template.** Citations, confidence levels, the coverage
statement, the impact rating and its trigger, the no-absence phrasing, and the secret prohibition stay with
the command, exactly as `review-pr` keeps its revision anchor, AI-disclosure, and coverage statement out of
`review-template`. An override that removed "Sources consulted" would remove the section; it cannot make the
command stop knowing what it did not read, and the command still reports coverage in the session. The
precedent is already in the manifest comment for `review-template`; this plan reuses it rather than inventing
a rule.

## Project Structure

### Documentation (this feature)

```text
specs/019-impact-analysis/
├── plan.md                       # This file
├── spec.md                       # 76 requirement definitions, 6 stories, 21 clarifications
├── research.md                   # Phase 0 — the decisions behind the command's rules
├── data-model.md                 # Phase 1 — entities, document schema, status lifecycle
├── quickstart.md                 # Phase 1 — how to prove it works
├── contracts/
│   ├── command-interface.md      # name, arguments, flags, effect, refusals, write scope
│   ├── document-contract.md      # front matter schema, section order, template resolution
│   ├── index-contract.md         # the folder index's shape and its refresh rule
│   └── chat-output.md            # pre-flight, questions, and the run report
├── checklists/requirements.md    # spec quality checklist (16/16)
└── tasks.md                      # Phase 2 output — NOT created by this command
```

### Source Code (repository root)

```text
spectra/
├── commands/impact.md                        # NEW — the whole runtime deliverable
├── templates/impact-analysis-template.md     # NEW — the document's section structure
├── extension.yml                             # + command, + template; version → 1.12.0; tags
├── CHANGELOG.md                              # [1.12.0]
└── README.md                                 # generated commands table gains a row
agents-list.json                              # NEW entry: impact (requirements-discovery, add-on, available)
catalog.json                                  # version → 1.12.0, provides.commands 6 → 7, updated_at
docs/
├── index.html                                # the command's entry on the landing page
└── packages/spectra.zip                      # rebuilt with tools/build_package.py
README.md                                     # generated agents table gains a ✅ available row
AGENTS_LIST.md                                # NEW hand-authored prose block, anchored id=impact
test/README.md                                # manual pass for pre-flight, caps, and the write-once rule
tests/
├── test_impact_flow.py                       # NEW — the command's hard rules, asserted on the text
├── test_doc_output_paths.py                  # CANONICAL gains impact.md → docs/impact-analysis/
├── test_document_templates.py                # COMMAND_TEMPLATE gains impact.md → impact-analysis-template
└── test_roster_data.py                       # census: 46 → 47 agents, 15 → 16 available, 31 planned
```

**Structure Decision**: no new top-level directory and no new module. The runtime artifacts are one Markdown
command and one Markdown template under the folders that already hold six commands and four templates;
everything else above is the publishing surface Principle V requires to move with them.

**The two existing enforcement modules are the point of this layout.** `test_doc_output_paths.py` derives
`DOCUMENT_COMMANDS` from its `CANONICAL` dict, and `test_document_templates.py` derives its checks from
`COMMAND_TEMPLATE`. Adding one entry to each is what converts Principles VII and VIII from reviewed to
enforced for this command — the declared-root resolution, the publication check, the lowercase project-relative
path, the four-layer resolution, the heading parity between shipped template and inline skeleton, and the
absence of a hard-coded template path all become assertions rather than intentions. This closes the one item
`/speckit.clarify` deferred to planning.

## Complexity Tracking

> Fill ONLY if Constitution Check has violations that must be justified

No violations. Every gate passes as written, and the VII and VIII sub-questions are argued above rather than
waved through.

Three items are recorded because they are new to the roster, not because they breach anything.

| Item | Why it is needed | Why the simpler option was rejected |
|---|---|---|
| **Reads a directory outside the project** (FR-013, FR-015) | Repository scope is not system scope. Without it, a consumer in a sibling service is invisible, and that is the most common missed impact. | Refusing to look outside the project would make the multi-system case useless; fetching it over the network would introduce the credential and egress path the whole design avoids. Reading a path the user hands over inherits their existing filesystem access and adds nothing. |
| **A stated time target with five caps** (SC-002, FR-021/022/024/026/028) | The output is a decision input for a meeting. An analysis that arrives tomorrow is not one. | An uncapped scan is unbounded on a large repository; a single global cap would starve whichever phase ran last. Five per-phase caps, each disclosed when reached, keep the trade visible instead of hidden. |
| **A rule forbidding output content** (FR-042a) | The citation rule plus the security trigger plus a publishable default folder is a live path from a hardcoded credential to a committed, possibly served file. | Relying on the publication check alone leaves the value copied into a second location and depends on getting the location right. Not citing secret-bearing lines at all would hide findings the BA needs. |

The write scope is **narrower** than the last command to ship. `flaky-test-detector` edits files the user
wrote; this one writes two new files and two fields of a third, and only after the run has finished
everything else.

## Phase 0 — Research

Complete. See [research.md](./research.md): nine decisions, each with rationale and rejected alternatives —
expressing repository-wide search without naming a tool, enforcing caps in prose, detecting a
non-interactive session from inside a prompt (the one honest limitation), the ranked identifier classes,
artifact-root and template resolution reuse, index refresh, secret recognition without execution, and the
confidence taxonomy's mapping onto evidence kinds.

## Phase 1 — Design & Contracts

Complete. [data-model.md](./data-model.md) fixes the entities and the document schema, including the status
lifecycle the command deliberately does not own. Four contracts pin the interface, the document, the index,
and what the user sees in the session. [quickstart.md](./quickstart.md) gives the runnable validation passes,
including the two that are easiest to get wrong: an interrupted run leaving nothing behind, and a
secret-bearing citation.

## Post-Design Constitution Re-Check

Re-run after Phase 1. No status changed.

| Principle | Post-design finding |
|---|---|
| II | Phase 1 added four contract documents and one shipped asset — the template VIII requires. The extension is still one folder, one manifest: seven commands, five templates. |
| III | The contracts are written as capability statements, not commands. `contracts/command-interface.md` names the arguments and flags in generic form; no invocation syntax and no shell appears in anything that ships. |
| IV | Design deepened it: `data-model.md` makes scan mode a first-class recorded field, so the project's own spec'd-ness is visible in the output rather than implicit. |
| V | The file list above is the sync obligation, enumerated. `tasks.md` will order it so the zip is rebuilt after the manifest, and the generated regions after the roster. |
| VI | Unchanged — extension channel only. Nothing in Phase 1 touched `VERSION` or `spectra_cli/`. |
| VII | Confirmed by design: `document-contract.md` states the write target as `<artifact-root>/impact-analysis/NNN-<name>.md`, and `index-contract.md` keeps the index unnumbered and folder-scoped. The `test_doc_output_paths.py` entry makes both assertions. |
| VIII | Confirmed by design: the template ships with the section structure only; the trustworthiness rules stay in the command, and `document-contract.md` records which sections an override may drop and what the command still does when it does. |
