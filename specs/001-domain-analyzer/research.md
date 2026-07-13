# Phase 0 Research: Domain Analyzer

All spec-level ambiguities were resolved in `/speckit-clarify` (see spec § Clarifications).
This document consolidates the remaining technology/pattern decisions needed to author the
extension. No `NEEDS CLARIFICATION` markers remain.

## D1 — Extension shape & packaging

- **Decision**: Author a single self-contained folder `domain-analyzer/` at the repo root,
  copying the structure of the reference `adr/` extension: `extension.yml`,
  `commands/analyze.md`, `README.md`, `CHANGELOG.md`, `LICENSE`.
- **Rationale**: Constitution Principle II mandates self-contained extensions whose folder
  name equals the `id`; `adr/` is the named reference model and already passes the build.
- **Alternatives considered**: Multi-command extension (rejected — only one verb, `analyze`,
  is in scope); shared helper library (rejected — Principle II forbids cross-extension state).

## D2 — Command namespace & verb

- **Decision**: `speckit.domain-analyzer.analyze`, file `commands/analyze.md`, registered in
  `provides.commands`. Front matter carries a `description`.
- **Rationale**: Principle III requires `speckit.<extension-id>.<verb>` with a clear verb;
  the spec/BRD confirm `analyze`. Per-agent triggers (e.g. Claude
  `/speckit-domain-analyzer-analyze`) are derived by Spec Kit at install time.
- **Alternatives considered**: `propose`, `infer` (rejected — `analyze` is the BRD-confirmed
  verb and best describes reading-then-proposing).

## D3 — Spec Kit compatibility pin

- **Decision**: `requires.speckit_version: ">=0.11.0"`.
- **Rationale**: The repo is initialized with Spec Kit `0.11.3` (`.specify/init-options.json`),
  which is what the extension will actually be tested against. Principle / Publishing standard
  requires pinning to the version actually tested.
- **Alternatives considered**: Mirror `adr`'s `>=0.9.0` (rejected — we do not test against
  0.9.x here; pin to the tested baseline).

## D4 — Output artifact location

- **Decision**: Write the proposal to `.specify/memory/domain-analysis.md` in the target
  project (beside the constitution). Create on first run.
- **Rationale**: Spec Assumptions fix this path; siting it beside `constitution.md` makes it
  a discoverable foundation-phase staging artifact and an obvious input to
  `/speckit-constitution`. It is the only file the command writes (FR-010).
- **Alternatives considered**: Under `specs/` or a new `guardrails/` dir (rejected — the BRD
  open question was resolved in favor of `.specify/memory/`).

## D5 — Candidate stable-ID scheme

- **Decision**: Content-derived ID = short slug/hash of the normalized guardrail statement
  plus its target section (e.g. `da-<section-slug>-<8-char-hash>`). The agent computes it
  deterministically from the statement text.
- **Rationale**: Resolves spec clarification Q1. Survives reordering and edits to surrounding
  fields, so re-run state preservation (FR-011, SC-005) is robust without a fragile counter.
- **Alternatives considered**: Sequential per-section counters (rejected — collide on append,
  not stable under reorder); pure random IDs (rejected — not reproducible across runs).
- **Note**: "Normalized" = trimmed, lowercased, whitespace-collapsed statement text. An SME
  editing the *statement itself* will change its ID; this is acceptable and documented — such
  an edit is treated as a new candidate while the original retains its reviewed state.

## D6 — Proposal-file format & handoff contract

- **Decision**: Each candidate is a GitHub task-list checkbox line bearing the guardrail
  statement, immediately followed by indented metadata fields (ID, target section, evidence,
  confidence, status: new|amends `<Principle>`). Candidates are grouped under `##` headings by
  target constitution section. The `- [x]` line is the canonical selection signal. Full
  format specified in [contracts/proposal-file.md](./contracts/proposal-file.md).
- **Rationale**: Resolves clarifications Q2/Q3. Checkbox-as-anchor keeps the selection signal
  unambiguous and parseable by `/speckit-constitution`, while staying human-editable in a
  plain Markdown editor / PR review (Assumption: `- [ ]`/`- [x]` is acceptable to SMEs).
- **Alternatives considered**: One-row-per-candidate table (rejected — multi-line evidence and
  editing wording are awkward in table cells); fenced YAML blocks (rejected — heavier for SMEs
  to edit and the checkbox is the natural opt-in affordance).

## D7 — Re-run merge strategy (preserve-and-append)

- **Decision**: On re-run, parse the existing file, index reviewed candidates by their D5 ID,
  and (a) leave every existing candidate — its checkbox state and any edits — byte-for-byte in
  place and order; (b) append only candidates whose ID is absent, into a clearly marked
  "New in this run (YYYY-MM-DD)" group.
- **Rationale**: Satisfies FR-011 / SC-005 (zero lost decisions, no reorder/overwrite) and the
  edge case "edited then re-run". Date stamp makes new items distinguishable (Journey 3).
- **Alternatives considered**: Regenerate-and-diff (rejected — risks clobbering edits);
  content-similarity matching (rejected — D5 ID match is deterministic and testable).

## D8 — Duplicate / amendment detection vs. an existing constitution

- **Decision**: Before proposing, read `.specify/memory/constitution.md`; for each candidate,
  perform a semantic/intent comparison against existing principles. Suppress candidates whose
  intent is already asserted; mark an overlapping-but-different candidate as
  `status: amends <Principle name/number>`.
- **Rationale**: Resolves clarification Q4 and satisfies FR-009 / Journey 4. Intent match (not
  exact text) is appropriate because the constitution is prose, not candidate blocks.
- **Alternatives considered**: Exact/normalized text match (rejected — prose won't match
  candidate phrasing, would produce duplicates); section-only match (rejected — too coarse).

## D9 — Compliance add-on recommendations (FR-014)

- **Decision**: Include in v1 as a recommendation-only note in the proposal file's domain
  summary when the inferred domain suggests a regulated area (e.g. health → HIPAA, EU PII →
  GDPR). It never enables or implements a framework.
- **Rationale**: Spec includes FR-014 in v1; keeping it advisory respects the Out-of-Scope
  boundary (no compliance execution).
- **Alternatives considered**: Defer to a later release (rejected — spec keeps it in v1).

## D10 — Distribution / build

- **Decision**: Register the extension in canonical `catalog.json`, then run
  `python3 build_packages.py` to regenerate `docs/` (index, hosted catalog, and
  `docs/packages/domain-analyzer.zip`); commit the regenerated `docs/`.
- **Rationale**: Principle V — `docs/` is generated, never hand-edited; URLs derive from
  `site.config.json`. This is the only supported publish path.
- **Alternatives considered**: Hand-edit `docs/` (rejected — violates Principle V and drifts).
