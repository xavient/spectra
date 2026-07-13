# Changelog

All notable changes to the `spectra` extension are documented here. This project follows
[Semantic Versioning](https://semver.org/).

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
