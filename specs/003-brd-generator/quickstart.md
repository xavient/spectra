# Quickstart: Validating `speckit.spectra.brd`

Manual end-to-end validation for the BRD Generator command (per Constitution Principle I / Development
Workflow step 5). There is no automated test framework for a prompt artifact — these scenarios are the
acceptance gate before publishing.

## Prerequisites

- A throwaway Spec Kit project (a directory with `.specify/` initialized) on your coding agent.
- The working copy of this extension installed with:
  ```bash
  specify extension add --dev /path/to/spectra
  ```
  Restart the agent so it picks up the new `speckit.spectra.brd` command.
- Confirm the bundled template installed at
  `.specify/extensions/spectra/templates/brd-template.md`.
- Triggers below use Claude's form (`/speckit-spectra-brd`); on kiro-cli use `/speckit.spectra.brd`.

## Scenario 1 — Plain-text requirement → BRD (User Story 1, P1)

1. Run: `/speckit-spectra-brd We need a way for support agents to merge duplicate customer tickets so
   history is preserved.`
2. Answer any clarifying questions (or decline).

**Expected**:
- A file `/brds/001-<kebab-title>.md` is created (folder created if it didn't exist).
- It follows the template's 14 sections + Document Control; **no** `[PLACEHOLDER]` tokens or HTML
  guidance comments remain.
- Section 6 has prioritized journeys (P1, P2…) each with Given/When/Then acceptance.
- The chat reports the file path and says you can now run `/speckit-specify` with it.
- Anything the requirement didn't state appears under Assumptions or Open Questions — not invented.

## Scenario 2 — Document input → BRD (User Story 2, P2)

1. Place a requirement doc in the project (e.g. `reqs/idea.md` or a `.txt`/`.docx`/`.pdf` with text).
2. Run: `/speckit-spectra-brd reqs/idea.md`

**Expected**:
- The command extracts the document's text and produces `/brds/00N-<kebab-title>.md` from it.
- Same structural guarantees as Scenario 1.

## Scenario 3 — Unreadable / image-only document (graceful degradation, FR-002)

1. Run the command against an image-only PDF or an unsupported/corrupt file.

**Expected**:
- The command reports it cannot extract text and lists the formats it can read.
- **No** BRD file is written; nothing is fabricated.

## Scenario 4 — Thin requirement triggers clarifying questions (FR-005)

1. Run: `/speckit-spectra-brd make it better`

**Expected**:
- The command asks up to five targeted clarifying questions before writing.
- If you answer, the answers shape the BRD; if you decline, a best-effort BRD is written with explicit
  Assumptions and Open Questions.

## Scenario 5 — No input prompts for it (FR-014)

1. Run: `/speckit-spectra-brd` (no arguments).

**Expected**:
- The command asks for a requirement (text) or a document path. No file is written.

## Scenario 6 — Re-run never overwrites (FR-009)

1. Run Scenario 1 again with a different requirement.

**Expected**:
- A new file with the **next** `NNN` is created (e.g. `/brds/002-...md`); the earlier BRD is untouched.

## Scenario 7 — Handoff to `/speckit-specify` (User Story 3, P3)

1. Take a BRD produced above and run: `/speckit-specify` referencing it.

**Expected**:
- A spec is generated whose prioritized user stories correspond one-to-one to the BRD's Section 6
  journeys (same priorities, same acceptance intent).

## Scenario 8 — Context-aware grounding (FR-017)

1. In a project with a constitution and an existing BRD, run a new requirement that overlaps.

**Expected**:
- Terminology aligns with the constitution; the command flags overlap/tension with the existing BRD as
  an Open Question rather than duplicating it or contradicting a ratified guardrail — without adding
  requirements the input didn't state.

## Publish gate (Principle V) — verify before release

- `spectra/extension.yml` registers `speckit.spectra.brd`; version bumped to `1.2.0`.
- `spectra/CHANGELOG.md` has a `1.2.0` entry.
- `catalog.json` `provides.commands` = 4; tags/version/`updated_at` updated.
- `docs/index.html` lists the new command; `docs/packages/spectra.zip` rebuilt (single top-level
  `spectra/` folder including `templates/brd-template.md`).
- Agents tables updated in `README.md` and `AGENTS_LIST.md`.
- All of the above agree with the `spectra/` folder and use raw
  `raw.githubusercontent.com/xavient/spectra/main/...` URLs.
