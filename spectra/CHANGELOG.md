# Changelog

All notable changes to the `spectra` extension are documented here. This project follows
[Semantic Versioning](https://semver.org/).

## [1.3.1] - 2026-08-09

### Changed
- **The extension description is now the positioning line used everywhere else:** "TELUS Digital -
  Agentic software engineering across the entire SDLC." It previously enumerated the four shipped
  commands, which meant it needed editing every time an agent was added and disagreed with the
  wording on the landing page and in the README. One line, one place, no drift.
- **The Commands table in `README.md` is generated** from the new root `agents-list.json` roster
  rather than maintained by hand. The region is marked with
  `<!-- SPECTRA:GENERATED START id=spectra-readme-commands -->`; everything around it, including the
  four per-agent sections, stays hand-written. Its Effect column is dropped — `effect: read-write` is
  declared once for the extension in `extension.yml`.
- **The PR agent is titled "GitHub (PR)" everywhere.** It previously appeared as `github`, GitHub,
  GitHub (PR), and "GitHub PR delivery" across four documents. Its command is unchanged:
  `speckit.spectra.create-pr`.

No command was added, changed, or removed, which is why this is a PATCH.

## [1.3.0] - 2026-08-08

### Changed
- **Relicensed from MIT to the Apache License 2.0.** Spectra stays free to use, modify, and
  redistribute for any purpose, including commercially. Apache-2.0 adds an explicit patent grant and
  makes attribution enforceable: redistributions and derivative works must retain the copyright
  notice, ship the `LICENSE` and `NOTICE` files, and state which files were changed
  (§4(b)–4(d)).

### Added
- `NOTICE` — the attribution notice that downstream redistributors are required to carry forward
  under Apache-2.0 §4(d). It now ships inside the extension package.

## [1.2.0] - 2026-07-14

### Added
- **`speckit.spectra.brd`** — a Requirements & Discovery-phase command that transforms a raw business
  requirement (inline text or a `.docx`/`.pdf`/`.md`/`.txt` document) into a structured,
  specify-ready BRD written under `/brds`. It reads project context to ground the document, asks up to
  five clarifying questions only when the requirement has material gaps, never invents requirements
  (genuine unknowns become Open Questions), and hands off to the Spec Kit **specify** command. Its only
  write is the BRD file.
- Bundled the canonical BRD template as `templates/brd-template.md` so the command produces the same
  structure in any installed project.

## [1.1.0] - 2026-07-09

### Changed
- Consolidated the previously separate `adr`, `domain-analyzer`, and `github` extensions into a
  single `spectra` extension. Every capability is now a command under the unified `speckit.spectra.*`
  namespace, matching Spec Kit's `speckit.<extension-id>.<command>` rule (the extension `id` is
  `spectra`):
  - `speckit.adr.new` → `speckit.spectra.adr`
  - `speckit.domain-analyzer.analyze` → `speckit.spectra.domain-analyzer`
  - `speckit.github.create-pr` → `speckit.spectra.create-pr`
- Install once with `specify extension add spectra` to get all three commands. The `after_implement`
  hook now invokes `speckit.spectra.create-pr`.

### Commands
- **`speckit.spectra.adr`** — Create a context-aware Architecture Decision Record grounded in the
  codebase, prior ADRs, and the project constitution; asks up to five clarifying questions and writes
  the ADR under `Docs/ADR/`.
- **`speckit.spectra.domain-analyzer`** — Infer the project's business domain and write an opt-in
  proposal of evidence-backed candidate guardrails to `.specify/memory/domain-analysis.md` for SME
  review and handoff to `/speckit-constitution`. Never edits the constitution or source.
- **`speckit.spectra.create-pr`** — Offer to open a correctly-targeted GitHub PR for the current spec
  branch after `implement`, deriving the base branch from the promotion strategy, confirming before
  any push, and returning the PR URL — with a graceful manual fallback when `gh`, the remote, or the
  network is unavailable.
