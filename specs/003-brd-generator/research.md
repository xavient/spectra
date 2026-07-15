# Phase 0 Research: BRD Generator (`speckit.spectra.brd`)

All Technical Context items were resolvable from the spec (with its four recorded clarifications) and
the constitution. No `NEEDS CLARIFICATION` markers remain. This document records the design decisions
that shape the command prompt and the bundled asset.

## D1 — How the BRD template is shipped and used

- **Decision**: Ship the canonical template as a bundled asset `spectra/templates/brd-template.md` (a
  verbatim copy of the repo's `brds/template.md`). The command reads the shipped template from the
  installed extension location and reproduces its section structure exactly. As a resilience fallback,
  the command also embeds the template's **section skeleton** (the headings and the Document Control /
  User-Journey field shapes) inline, used only if the shipped file cannot be located at runtime.
- **Rationale**: Satisfies FR-004 literally ("a BRD template shipped with it") and Principle II
  (self-contained; no dependency on the Spectra repo at runtime). Reading the shipped file keeps a
  single authoritative template; the inline skeleton guarantees the command still produces the correct
  structure even where the installed asset path cannot be resolved, so "the same structure in any
  installed project" holds. The `git` extension already ships non-command assets
  (`config-template.yml`), so a `templates/` directory is an established, valid layout.
- **Alternatives considered**:
  - *Inline-only (embed the full template in the command, ship no file)* — matches `adr`/
    `domain-analyzer` exactly and is dependency-free, but does **not** ship the template as a
    first-class file, which the user explicitly asked for ("copied and shipped with spectra").
  - *File-only (ship the file, no inline fallback)* — cleanest single source, but a runtime failure to
    locate the installed asset would break generation with no recovery.
  - *Duplicate the full template inline AND in the file* — guarantees operation but invites drift
    between two full copies. The skeleton-only fallback avoids meaningful drift (headings change rarely).

## D2 — BRD identifier and filename scheme

- **Decision**: `/brds/NNN-<kebab-title>.md`, where `NNN` is a zero-padded, three-digit sequential
  number one greater than the highest existing `NNN` under `/brds` (starting at `001`), and
  `<kebab-title>` is the BRD title lowercased with spaces replaced by hyphens. The internal Document
  Control identifier is `BRD-NNN` using the same number. Never overwrite an existing file.
- **Rationale**: Confirmed by clarification Q1 (option A). Mirrors the `specs/` directory convention
  (`003-brd-generator`), guarantees uniqueness/ordering as BRDs accumulate, avoids collisions when two
  requirements share a title, and keeps BRD ↔ spec traceability obvious. The numbering algorithm reuses
  the exact pattern `adr` uses for `ADR-NNN`.
- **Alternatives considered**: title-only `<title>.md` (matches this repo's small curated `brds/` set
  but collides and loses ordering at scale); `BRD-NNN-<title>.md` (redundant prefix — the folder already
  says "brd").

## D3 — Requirement input modes and document text extraction

- **Decision**: Accept the requirement as (a) inline text via `$ARGUMENTS`, and/or (b) a filesystem
  path to a document. When a path is given, instruct the host agent to read/extract the document's
  **text content**. Supported-format baseline: `.md` and `.txt` are always supported (plain text);
  `.docx` and `.pdf` are supported when the host agent can extract their text. When both inline text and
  a file are supplied, the file is the primary requirement and the inline text is additional guidance
  (clarification Q3). When no input is supplied, prompt for text or a path (FR-014).
- **Rationale**: Matches FR-001/FR-002/FR-014 and clarification Q3. Text extraction is inherently a host
  capability (there is no bundled parser and none is desired — Principle II keeps the command a pure
  prompt), so the command declares the baseline and **degrades gracefully**: if a document's text cannot
  be extracted (unsupported, corrupt, image-only with no text layer), it reports the problem and the
  formats it can read, and does not fabricate a BRD.
- **Alternatives considered**: bundling a document-parsing dependency (rejected — turns a prompt artifact
  into runtime software, violates Principle II and the "no runtime libraries" constraint); OCR of scanned
  PDFs (rejected — explicitly out of scope in the spec).

## D4 — Degree of project-context reading (Principle IV)

- **Decision**: Before drafting, read available context when present — the constitution
  (`.specify/memory/constitution.md`), existing BRDs under `/brds`, and prior specs under `specs/` — and
  use it to ground and deconflict (align terminology, avoid contradicting ratified guardrails, avoid
  duplicating an existing BRD, and pick the next `NNN`). The supplied requirement and clarifying answers
  remain the sole source of truth for **what to build**; context never introduces requirements. On a
  greenfield/empty project, proceed from the requirement alone.
- **Rationale**: Confirmed by clarification Q4 and FR-017; satisfies Principle IV while honoring FR-006
  ("never invent"). This is the same context-first discipline `adr` and `domain-analyzer` use.
- **Alternatives considered**: requirement-only (violates Principle IV); deep codebase inference like
  `domain-analyzer` (rejected — risks inventing requirements not in the input and is too heavy for a
  front-of-SDLC authoring tool).

## D5 — Interaction model (clarifying questions)

- **Decision**: Interactive, in the spirit of `speckit.spectra.adr`: gather context, then ask **up to
  five** targeted clarifying questions **only when the requirement has material gaps or ambiguities**;
  skip questioning when the requirement is already complete. Present questions, wait for answers, fold
  them in; if the user declines, proceed best-effort and record remaining gaps as Open Questions.
- **Rationale**: Confirmed by clarifications Q2 (trigger) and the earlier user direction ("interactive
  like adr", cap of five). Reuses `adr`'s Step 2 pattern almost verbatim.
- **Alternatives considered**: always-ask (nags on well-specified requirements); never-ask (loses the
  interactive strengthening the user explicitly requested).

## D6 — Handoff to `/speckit-specify`

- **Decision**: After writing, report the output file path and instruct the user they can now run
  `/speckit-specify` with the constructed BRD. The command does **not** invoke `specify` itself.
- **Rationale**: FR-012. Keeps the command's effect bounded to writing BRD files; `specify` is a
  separate core command with its own hooks (branch creation, etc.). Matches how `adr` ends with a
  suggested (not executed) next step.
- **Alternatives considered**: auto-invoking `specify` (rejected — surprising outward action; couples two
  commands and bypasses `specify`'s own pre-hooks).

## D7 — Manifest, versioning, and distribution sync (Principle V)

- **Decision**: Register `speckit.spectra.brd` (file `commands/brd.md`) in `spectra/extension.yml`
  `provides.commands`; bump `extension.version` `1.1.0` → `1.2.0` (a new command is a MINOR change) with
  a matching `spectra/CHANGELOG.md` entry. Keep `requires.speckit_version: ">=0.11.0"` (no new host
  requirement; re-test before publish). Update `catalog.json` (`provides.commands` 3 → 4, add tags such
  as `brd` and `requirements`, bump `version`/`updated_at`), `docs/index.html`, the Agents tables in
  `README.md` and `AGENTS_LIST.md`, and rebuild `docs/packages/spectra.zip` by hand (single top-level
  `spectra/` folder). `effect` stays `read-write`.
- **Rationale**: Directly required by the constitution's Principle V and Publishing & Distribution
  Standards. MINOR bump per SemVer (additive, backward-compatible).
- **Alternatives considered**: none — these are prescribed obligations, not choices.

## Open item intentionally deferred

- The *guaranteed* document-format matrix beyond the D3 baseline (e.g. `.rtf`, `.odt`, or specific PDF
  variants) is host-agent-capability-dependent and is documented as a baseline plus graceful degradation
  rather than an exhaustive guarantee. This does not block implementation and is captured in the command
  prompt's degradation behavior; it can be revisited if a target agent's extraction capability is known.
