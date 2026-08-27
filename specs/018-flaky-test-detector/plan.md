# Implementation Plan: Flaky Test Detector

**Branch**: `018-flaky-test-detector` | **Date**: 2026-08-26 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/018-flaky-test-detector/spec.md`

## Summary

A sixth Spectra command, `speckit.spectra.flaky-test-detector`, and the first that **edits the user's
source**. It reads the project's test code, reports the tests most likely to fail intermittently with a
confidence rating and a concrete fix for each, and — behind two explicit consent gates — writes a
resumable task list to `.specify/memory/flaky-test-analysis.md` and applies the approved fixes.

Three properties shape every design decision below. It **never executes anything** — no test run, no
build, no install, no network — so detection is a read of the working tree and nothing else. It **never
writes production source**, so the blast radius of a wrong answer is a test file in an uncommitted diff.
And its entire memory is **one Markdown file it wrote itself**, which means that file is a machine
contract, not just a report: the same command must re-read it next week and know exactly which of four
states it is in.

The command file is the deliverable. No script ships, no binary ships, and every rule below is expressed
as prompt instructions, because that is the only form that survives Principle III.

## Technical Context

**Language/Version**: Markdown command prompt in Spec Kit's generic format; Python 3.9+ (standard library
only) for the repository's own tools and tests

**Primary Dependencies**: Spec Kit `>=0.11.0`. **No runtime tool dependency** — unlike `create-pr` and
`review-pr`, this command needs neither `git` nor `gh`, and must not gate on either

**Storage**: exactly one file, `.specify/memory/flaky-test-analysis.md`, written by the command and read
back by its next run. No database, no cache, no cross-run history

**Testing**: `python -m unittest discover -s tests`; `python tools/generate_agent_docs.py --check`; a new
`tests/test_flaky_test_detector_flow.py`; the manual zip-install pass in `test/README.md`

**Target Platform**: every coding agent and OS Spec Kit supports. Suite discovery, analysis, gating, and
file parsing are all prompt-expressed, so nothing depends on a shell flavour

**Project Type**: Spec Kit extension command — a prompt file under `spectra/commands/`, plus the
publishing surface Principle V requires

**Performance Goals**: not latency-bound. The real limit is how much test code the agent can read in one
run, which is why FR-020 makes disclosing what was *not* reached mandatory rather than optional

**Constraints**: Markdown only — no scripts, binaries, or post-install hooks; agent-agnostic `$ARGUMENTS`;
no execution of any kind (FR-003); no commit, push, or branch (FR-004); no production-source edit
(FR-005, FR-032); two consent gates with no flag that removes either

**Scale/Scope**: 1 new command file; 1 manifest entry; 1 roster entry flipped planned → available; 1
catalog entry; 1 changelog entry; 1 rebuilt zip; ~4 documentation surfaces including a hand-authored
prose block; 1 new test module plus two census updates

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Note |
|---|---|---|
| I. Spec-Driven Development | ✅ | This spec/plan/tasks set on branch `018-flaky-test-detector`, clarified before planning. |
| II. A Single Self-Contained Extension | ✅ | One new file under the existing `spectra/commands/`. No new extension folder, no dependency on another extension. |
| III. Agent-Agnostic Commands | ✅ | Text only, `$ARGUMENTS` for the optional scope. Suite discovery and file parsing are stated in prose precisely because a detection script would break this. |
| IV. Context-Aware by Default | ✅ | The strongest application yet: the whole product is reading the project. Reads the working tree, the consumer project's constitution (FR-033a), and its own prior output before acting. |
| V. Catalog and Package in Sync | ✅ | Manifest, roster, catalog, changelog, zip, landing page, generated regions, and a new hand-authored prose block all move in the same change. |
| VI. Two Independently-Versioned Channels | ✅ | Extension channel only: 1.10.0 → 1.11.0. `VERSION` untouched, no tag, no Release. |
| VII. Documents Under One Declared Root | ✅ | Not engaged — see below. The output is `.specify/` context, the category the principle explicitly places outside its rule. |
| VIII. Shaped by Overridable Templates | ✅ | Not engaged — see below. Follows from VII: no deliverable, no template. |

**Amendment classification**: none. No principle is added, redefined, or loosened. VII and VIII are applied
as written, including the sentence in VII that already anticipates this case.

**Extension version classification**: MINOR — 1.10.0 → 1.11.0. A command is added; none is renamed or
removed, and no existing command's behaviour changes. `catalog.json` `provides.commands` goes 5 → 6.

### The two gates that need an argument, not a checkmark

**VII and VIII both turn on one question: is the analysis file a deliverable?** The answer decides where
it lives and whether it ships a template, so it is worth stating the reasoning rather than asserting the
conclusion.

Principle VII settles it directly:

> `.specify/` (constitution, memory, extension assets) and `specs/` belong to Spec Kit, and a command
> writing there — as `speckit.spectra.domain-analyzer` does with `.specify/memory/domain-analysis.md` —
> is writing **context** for another command to consume, not a deliverable for a human to read.

The analysis file is that, with the consuming command being *this same command's next run*. It is a task
list two parties hand back and forth — the agent ticks boxes, the developer deletes rows — and its value
is entirely in being re-read. Nobody files it, links it from a README, or ships it to a stakeholder.
`domain-analysis.md` is the exact precedent, and this file sits beside it.

That answer carries VIII with it: VIII shapes **deliverables**, and its 1.7.1 clarification widened
"deliverable" to cover emitted documents — a PR body, a review comment — not to cover working state.
`domain-analysis.md` has shipped since 1.1.0 with no registered template, and nothing here distinguishes
this file from it. So: no `spectra/templates/flaky-test-analysis-template.md`, no `provides.templates`
entry, and the structure lives in the command, pinned by
[contracts/analysis-file.md](./contracts/analysis-file.md).

**The counter-argument, stated fairly.** A human *does* read this file — that is the whole point of the
review gate — and a team might reasonably want to reshape it. If that argument wins later, the fix is
additive and cheap: ship the template, register it, resolve it through the stack. Nothing in this design
forecloses it. What decides it today is that the file's structure is a **parsing contract with the next
run**, and an override that removed the `## Tasks` heading or renamed a column would not restyle the
output — it would make the file unreadable to the command that wrote it, which is a failure mode
Principle VIII's "honour, do not repair" rule would then force the command to accept. That is a real
hazard, not a hypothetical, and it is the reason to keep the structure fixed until someone asks.

**The precedent this sets, named once.** This is the first Spectra command that modifies files it did not
create, in a project it did not author. The constitution has no principle about that today, and this plan
deliberately does not invent one — it constrains the behaviour inside the spec instead (FR-005, FR-032,
FR-033, FR-032a). If a second such agent appears, the shared rules should be lifted into the constitution
rather than copied.

## Project Structure

### Documentation (this feature)

```text
specs/018-flaky-test-detector/
├── plan.md                    # This file
├── spec.md                    # 48 requirements, 6 stories, 13 clarifications
├── research.md                # Phase 0 — the decisions behind the command's rules
├── data-model.md              # Phase 1 — entities and the session state machine
├── quickstart.md              # Phase 1 — how to prove it works
├── contracts/
│   ├── command-interface.md   # name, arguments, effect, gates, refusals
│   ├── analysis-file.md       # the file's exact shape and parse rules
│   └── chat-output.md         # what the developer sees at each step
├── checklists/requirements.md # spec quality checklist (16/16)
└── tasks.md                   # Phase 2 output — NOT created by this command
```

### Source Code (repository root)

```text
spectra/
├── commands/flaky-test-detector.md   # NEW — the whole runtime deliverable
├── extension.yml                     # + the command; version → 1.11.0; tags
├── CHANGELOG.md                      # [1.11.0]
└── README.md                         # generated commands table gains a row
agents-list.json                      # flaky-test-detector: planned → available, + command
catalog.json                          # version → 1.11.0, provides.commands 5 → 6, updated_at
docs/
├── index.html                        # the command's entry on the landing page
└── packages/spectra.zip              # rebuilt with tools/build_package.py
README.md                             # generated agents table row flips to ✅ available
AGENTS_LIST.md                        # NEW hand-authored prose block, anchored id=flaky-test-detector
test/README.md                        # manual pass for the two gates and the resume states
tests/
├── test_flaky_test_detector_flow.py  # NEW — the command's hard rules, asserted on the text
└── test_roster_data.py               # census: 14 → 15 available, 32 → 31 planned, shipped set 5 → 6
```

**Structure Decision**: no new top-level directory and no new module. The runtime artifact is a single
Markdown file under the existing `spectra/commands/`, exactly like the five commands already shipped;
everything else in the tree above is the publishing surface Principle V requires to move with it.

## Complexity Tracking

> Fill ONLY if Constitution Check has violations that must be justified

No violations. Every gate passes as written, and the two marked "not engaged" are argued above rather
than waved through.

One item is worth recording even though it is not a violation: this command's **write scope is wider than
any existing Spectra command's** — it edits files the user wrote. The design keeps that bounded by four
independent limits rather than one, so no single mistaken judgment is sufficient to cause damage: edits
are confined to test and test-support files (FR-032); the prohibited-remedy list closes the degenerate
"make it pass" solutions (FR-033); every edit requires a row the developer left in the file after review
(FR-031); and nothing is ever committed (FR-004), so the working-tree diff is always the last checkpoint
before anything becomes permanent.

## Post-Design Constitution Re-Check

Re-run after Phase 1. No status changed.

| Principle | Post-design finding |
|---|---|
| II | Phase 1 added three contract documents and no shipped asset. The extension is still one folder, one manifest, six command files. |
| III | The riskiest temptation in this design was a discovery or parsing script — suite detection and file re-reading both *look* like code problems. [R-003](./research.md) and [R-007](./research.md) keep both in prose, so the package stays Markdown-only and works wherever Spec Kit does. |
| IV | Strengthened by FR-033a: the constitution is not only read, it is binding on fix selection, and its absence is reported rather than assumed. |
| V | The publishing surface is enumerated in the tree above and again as tasks. The new prose block is the one item automation cannot generate — `--check` asserts only that it exists. |
| VII / VIII | Unchanged, and the design now depends on the reasoning: [contracts/analysis-file.md](./contracts/analysis-file.md) is a parse contract, which is what makes "context, not deliverable" true rather than convenient. |

### What the design deliberately did not add

- **No configuration file.** No thresholds, no ignore list, no severity weights. Confidence is a judgment
  (FR-015) and pruning is a human act; a config file would be a second policy surface competing with the
  constitution, which is the argument that settled the same question for `review-pr`.
- **No hook registration.** `create-pr` earns its `after_implement` hook because opening a PR is the next
  step after implementing. Flaky-test remediation is not part of any command's flow; it is something a
  team does when they decide to. An unprompted offer after every `implement` would be noise.
- **No cross-run history.** One file, replaced wholesale. Trends are the telemetry product the BRD
  explicitly deferred.
- **No candidate cap.** Ordering plus a mandatory coverage statement does the same work without silently
  deciding which flakiness matters.

## Phase Artifacts

| Phase | Artifact | Contents |
|---|---|---|
| 0 | [research.md](./research.md) | 12 decisions: output location, the no-template argument, prose-expressed discovery, the confidence rubric, gate mechanics, checkpointing cost, the parse contract, scope comparison, constitution binding, the version and publishing surface, the no-hook decision, and the test strategy |
| 1 | [data-model.md](./data-model.md) | 11 entities, the four-state session machine, and the file's state transitions |
| 1 | [contracts/command-interface.md](./contracts/command-interface.md) | Command name, arguments, effect, preconditions, the gates, and the refusal list |
| 1 | [contracts/analysis-file.md](./contracts/analysis-file.md) | Required headings, header fields, table columns, ID format, evidence and outcome entries, and what makes a file unparseable |
| 1 | [contracts/chat-output.md](./contracts/chat-output.md) | The seven things the developer can be shown, and which requirement each satisfies |
| 1 | [quickstart.md](./quickstart.md) | Repository checks, throwaway-project install, and one scenario per user story plus the refusal paths |
