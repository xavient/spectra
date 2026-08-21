# Feature Specification: Overridable Document Templates

**Feature Branch**: `013-overridable-templates`

**Created**: 2026-08-21

**Status**: Draft

**Input**: User observation: "`brd` command follows a template, but `adr` does not. That makes the produced BRDs consistent
while allowing end users to customize their templates depending on their project needs." Confirmed as half true — `adr`
does follow a template, but it is a literal block inside the command file, and the BRD template's customizability is
incidental rather than designed. This spec closes both gaps.

## Current State (verified)

| | ADR | BRD |
|---|---|---|
| Template exists | Yes — a fenced literal in `spectra/commands/adr.md` Step 4, introduced by "use **exactly** this template … do not add, rename, or reorder sections" | Yes — `spectra/templates/brd-template.md`, 14 sections |
| Shipped as an asset | **No** | Yes (inside `docs/packages/spectra.zip`) |
| Registered in `extension.yml` | No | **No** — the manifest declares only `provides.commands` |
| How the command finds it | n/a (inline) | Hard-coded read of `.specify/extensions/spectra/templates/brd-template.md` (`brd.md:65`) |
| Fallback | n/a | Inline section skeleton (`brd.md:207`) |
| Project can override it | **No** | Only by editing the installed copy |

Spec Kit already provides the mechanism this needs. `.specify/scripts/bash/common.sh` defines `resolve_template()` with a
four-layer priority stack:

1. `.specify/templates/overrides/<name>.md` — project override
2. `.specify/presets/<preset-id>/templates/<name>.md` — installed presets, by registry priority
3. `.specify/extensions/<ext-id>/templates/<name>.md` — extension-provided
4. `.specify/templates/<name>.md` — core

The BRD command reads layer 3 directly, so a project override at `.specify/templates/overrides/brd-template.md` is
silently ignored. And because upstream specifies that "extension-provided templates and scripts always resolve as
`replace`", the only customization path available today — editing the installed copy — is overwritten by
`specify extension update spectra`. `.specify/.gitignore` excludes only `feature.json` and
`extensions/*/local-config.yml`, so that edit *is* committed and looks durable right up until an update reverts it.

## Clarifications

- Q: Should the ADR template gain sections (Alternatives Considered, Drivers, …) while we are shipping it as an asset?
  → A: No. The shipped default MUST reproduce today's four-part structure verbatim, so no existing user's output changes.
  Teams that want more sections are exactly who the override is for.
- Q: Should the commands call `resolve_template()` from `common.sh`?
  → A: No. It is a Bash function in core Spec Kit's script tree, so depending on it would break agent-agnosticism
  (Principle III) on PowerShell-only setups, and shipping our own script would break the "Markdown only — no scripts, no
  binaries, no post-install hooks" supply-chain promise the README makes. The commands MUST implement the same priority
  order as prompt instructions instead.
- Q: What if a project's override is unreadable or empty?
  → A: Fall through to the next layer and say so. Never produce a document with no structure, and never silently "repair"
  a user's template.

### Phase 0 findings (measured against Spec Kit 0.16.5, `/tmp/tmpl-probe`)

- **OQ-1 — closed.** Registration changes nothing about placement. An **unregistered** template file is copied anyway —
  `specify extension add --dev` copies the whole extension tree, so `templates/brd-template.md` lands at
  `.specify/extensions/spectra/templates/brd-template.md`. A manifest **with** `provides.templates` validates, installs
  without complaint, and puts the files in the same place.

  But `specify extension info spectra` lists **commands only** — it does not surface templates, and
  `.specify/extensions.yml` records only the installed id and its hooks. **Registration buys no discoverability on
  0.16.5.** User Story 3 is revised accordingly: it is now about declaring what we ship in the schema-sanctioned field
  (and being ready for a Spec Kit release that does surface it), not about what `info` prints today.

- **Template resolution verified end to end.** With the extension installed and no override,
  `resolve_template brd-template` and `resolve_template adr-template` both return the extension copy. After adding
  `.specify/templates/overrides/{adr,brd}-template.md`, both return the override. The resolver finds extension templates
  by scanning the directory, so it works **with or without** registration — which is why FR-002 is a correctness and
  forward-compatibility requirement rather than a functional prerequisite for FR-003.

- **OQ-2 — closed, and it confirms the problem this spec exists to fix.** Project overrides survived every operation
  tried: a `--dev` install, a forced install from the published catalog, and `specify extension update spectra`.
  `specify extension remove spectra` enumerates only the extension directory and its config files before asking, so the
  overrides are outside its blast radius.

  Meanwhile a marker appended to the **installed** `.specify/extensions/spectra/templates/brd-template.md` survived a
  no-op update but was **destroyed by `specify extension add spectra --force`**, which is the same tree-replace a real
  version bump performs. Editing the installed copy is therefore not durable; an override is.

  Limit of the evidence: a genuine version-to-version update could not be observed, because 1.6.0 is the newest published
  version. A forced reinstall exercises the same replace path and left `.specify/templates/` untouched.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A project shapes its own ADRs (Priority: P1)

A team needs ADRs to carry two sections their governance requires — say **Alternatives Considered** and **Compliance
Impact**. They drop `.specify/templates/overrides/adr-template.md` into the repo, commit it, and every ADR the agent
writes from then on follows their structure, on every teammate's machine, surviving extension updates.

**Why this priority**: It is the capability the user asked for and the one that does not exist at all today — the ADR
structure is currently a literal in a file that gets replaced on update.

**Independent Test**: In a throwaway project, add an override with a distinctive extra section, run the ADR command, and
confirm the produced ADR follows the override; then run `specify extension update spectra` and confirm the override still
wins.

**Acceptance Scenarios**:

1. **Given** `.specify/templates/overrides/adr-template.md` exists, **When** the ADR command drafts, **Then** it follows
   that file's sections, in that order, and reports which template it used.
2. **Given** no override anywhere, **When** the ADR command drafts, **Then** it follows the shipped
   `adr-template.md`, whose structure is identical to the pre-1.7.0 inline template.
3. **Given** an override that is empty or unreadable, **When** the ADR command drafts, **Then** it reports the problem,
   falls through to the next layer, and still produces a complete ADR.
4. **Given** any run, **When** the ADR is written, **Then** the command's write footprint is unchanged — one ADR file,
   plus the existing approval-gated exceptions.

---

### User Story 2 - The same override works for BRDs, and survives updates (Priority: P1)

The same team overrides `brd-template.md` — dropping sections they never use, adding a Regulatory Impact section. It
takes effect for the whole team, and `spectra update` does not silently revert it.

**Why this priority**: Equal to Story 1. Today BRD customization appears to work and then breaks on update, which is
worse than not existing, because the revert lands as noise in an unrelated diff.

**Independent Test**: Override `brd-template.md`, generate a BRD, confirm the override drove it; run
`specify extension update spectra`; confirm the override is untouched and still wins.

**Acceptance Scenarios**:

1. **Given** `.specify/templates/overrides/brd-template.md` exists, **When** the BRD command drafts, **Then** it follows
   the override rather than the extension copy, and reports which template it used.
2. **Given** an installed preset providing `brd-template.md` and no project override, **When** the BRD command drafts,
   **Then** the preset's template is used.
3. **Given** no override and no preset, **When** the BRD command drafts, **Then** the extension copy is used — today's
   behavior, unchanged.
4. **Given** the extension is updated, **When** either command next runs, **Then** the project override still wins,
   because it lives outside the extension tree.

---

### User Story 3 - Both templates are declared, not just present (Priority: P2)

The extension manifest declares what it provides. `provides.templates` is Spec Kit's field for exactly this, and a
Spectra template that ships as an undeclared file is an undocumented one — a reader of `extension.yml` cannot tell a
template from an incidental asset.

**Why this priority**: Correctness and forward-compatibility rather than capability. Stories 1–2 work without it: Phase 0
measured that the resolver locates extension templates by scanning the directory, and that `specify extension info` on
0.16.5 prints commands only. So registration changes nothing a user sees **today** — it makes the manifest honest, and it
is what a future Spec Kit release that surfaces templates would read.

**Independent Test**: a manifest carrying `provides.templates` for both templates installs without validation error, and
the installed layout is byte-identical to the unregistered case.

**Acceptance Scenarios**:

1. **Given** the manifest, **When** Spec Kit validates it at install time, **Then** `provides.templates` declares both
   templates with `name`, `file`, and `description`, and installation succeeds.
2. **Given** the registered manifest, **When** the extension is installed, **Then** both templates land at
   `.specify/extensions/spectra/templates/` — the same place as before — so no resolution behavior depends on this story.
3. **Given** a template file under `spectra/templates/` with no manifest entry, or an entry whose file is missing,
   **When** the suite runs, **Then** it fails and names the discrepancy.

---

### User Story 4 - The two ADR structures cannot drift (Priority: P3)

A maintainer edits the shipped ADR template but forgets the inline last-resort fallback inside `adr.md`. CI fails and
names both files.

**Why this priority**: It protects a subtle invariant rather than delivering user value, but the same trap already exists
in `brd.md` (a 14-section asset and a 14-section inline skeleton, kept in step by hand today).

**Independent Test**: Change a section heading in `spectra/templates/adr-template.md` only, and confirm the suite fails.

**Acceptance Scenarios**:

1. **Given** the shipped template and the command's inline fallback, **When** the suite runs, **Then** it asserts the two
   declare the same section headings in the same order.
2. **Given** a shipped template that is not registered in `provides.templates`, or a registered template whose file is
   missing, **When** the suite runs, **Then** it fails and names the discrepancy.

---

### Edge Cases

- **An override exists for one template but not the other** — resolve each template independently; no coupling.
- **An override provides a heading structure the command's filling rules do not recognize** (e.g. no Consequences
  section). Honour the template: fill what is there, and note in chat which of the command's usual sections the template
  omitted rather than adding it back.
- **An override contains guidance comments and `[PLACEHOLDER]` tokens** — strip them in the output, exactly as the BRD
  command already does for the shipped template.
- **Multiple presets provide the same template name** — Spec Kit's registry priority decides; the command follows the
  first hit and does not merge layers. Composition strategies (`wrap`/`prepend`/`append`) are preset-only upstream and
  are out of scope here.
- **`.specify/` is absent entirely** (Spectra invoked outside a Spec Kit project) — fall through to the inline skeleton
  rather than failing.
- **A template name collides with a core Spec Kit template** — `adr-template` and `brd-template` do not; the check
  belongs in review, and the names are already namespaced by purpose.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The repository MUST ship `spectra/templates/adr-template.md`, whose section structure reproduces the
  pre-1.7.0 inline ADR template verbatim: an `# ADR-NNN: [Title]` heading, `**Date:**`, `**Status:**`, and the sections
  Context, Decision, Consequences, in that order.
- **FR-002**: `spectra/extension.yml` MUST declare both templates under `provides.templates`, each with `name`, `file`,
  and `description`, using the names `adr-template` and `brd-template`.
- **FR-003**: Both document commands MUST resolve their template through the same four-layer priority order Spec Kit
  defines: project override → presets → extension → core.
- **FR-004**: Neither command may hard-code a single template path.
- **FR-005**: Each command MUST retain an inline last-resort skeleton, used only when no layer yields a readable
  template.
- **FR-006**: Each command MUST report which template it used, naming the resolved path, so an override is verifiable
  without guesswork.
- **FR-007**: When a layer's template exists but is empty or unreadable, a command MUST say so and fall through to the
  next layer.
- **FR-008**: A command MUST follow the resolved template's sections, in the template's order, and MUST NOT add,
  rename, or reorder them. Where the resolved template omits a section the command would normally fill, it MUST note
  the omission rather than reinstating the section.
- **FR-009**: Commands MUST strip guidance comments and `[PLACEHOLDER]` tokens from the output, whichever layer the
  template came from.
- **FR-010**: The `adr` command's "use **exactly** this template" wording MUST be restated so the *resolved* template is
  authoritative rather than the literal in the command file.
- **FR-011**: No script, binary, or post-install hook may be added to the extension; template resolution MUST be
  expressed as prompt instructions.
- **FR-012**: Every write scope MUST be unchanged: `brd` writes exactly one BRD; `adr` writes one ADR plus its existing
  approval-gated exceptions.
- **FR-013**: The published `docs/packages/spectra.zip` MUST contain both templates.
- **FR-014**: `catalog.json` MUST stay in sync with the manifest. The catalog schema carries a command count only, so no
  template count is added; the version and `updated_at` move.
- **FR-015**: The test suite MUST fail when a shipped template's section headings drift from the corresponding command's
  inline fallback.
- **FR-016**: The test suite MUST fail when a template file exists but is unregistered, or is registered but missing.
- **FR-017**: The test suite MUST fail when a document command stops naming all four resolution layers.
- **FR-018**: User-facing documentation — `spectra/README.md`, `AGENTS_LIST.md`, `docs/index.html`, `README.md` where
  relevant, and `test/README.md` — MUST document `.specify/templates/overrides/<name>.md` as the supported
  customization point, and MUST state that overrides survive extension updates.
- **FR-019**: The extension version MUST bump to `1.7.0` with a matching `spectra/CHANGELOG.md` entry, so the capability
  reaches installs through `spectra update`.
- **FR-020**: The constitution MUST record the rule so future document agents inherit it: a document command's structure
  comes from a registered, overridable template resolved through the stack, with an inline fallback — never from a path
  baked into the command.

### Key Entities

- **Template asset**: a Markdown file under `spectra/templates/`, shipped in the zip and installed to
  `.specify/extensions/spectra/templates/`.
- **Template name**: the resolver key — lowercase, alphanumeric, hyphens. `adr-template`, `brd-template`.
- **Resolution stack**: the four layers above, highest priority first.
- **Project override**: `.specify/templates/overrides/<name>.md`. Committed, team-wide, outside the extension tree and
  therefore untouched by `specify extension update`.
- **Inline skeleton**: the last-resort structure carried in the command file itself.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A project can change the structure of produced ADRs and BRDs by adding one file each, with no edit to any
  installed extension file.
- **SC-002**: An override survives `specify extension update spectra` — verified by running the update and regenerating.
- **SC-003**: With no override present, the output of both commands is structurally identical to 1.6.0.
- **SC-004**: Each command names the resolved template path in its report, so which layer won is never ambiguous.
- **SC-005**: `python -m unittest discover -s tests`, `python tools/generate_agent_docs.py --check`, and a
  `tools/build_package.py` rebuild all pass; the zip contains both templates.
- **SC-006**: The published extension remains Markdown-only: zero scripts, binaries, or hooks added.

## Assumptions

- Command files are prompts: the enforceable surface is their text plus the CI guard on that text. End-to-end behavior
  needs the manual pass in `test/README.md`.
- Presets are in the stack for completeness. Spectra ships none, and preset-only composition strategies stay out of
  scope.
- The ADR template's *content* is unchanged in this release. Enriching it is a separate, opt-in decision now that every
  project can do it themselves.
- A genuine version-to-version extension update behaves like the forced reinstall measured in Phase 0 — it replaces the
  extension tree and leaves `.specify/templates/` alone. This could not be observed directly because 1.6.0 is the newest
  published version; re-check when 1.7.0 is live.

## Open Questions

All three are closed. OQ-1 and OQ-2 were answered by measurement (see Phase 0 findings above); OQ-3 was decided by the
maintainer.

- **OQ-1 — closed.** Registration does not change placement or behavior, and `specify extension info` does not surface
  templates on 0.16.5. User Story 3 was rewritten to claim only what is true.
- **OQ-2 — closed.** Overrides live outside the extension tree and survived install, forced reinstall, and update; the
  installed copy did not survive a forced reinstall.
- **OQ-3 — closed.** The rule becomes **Principle VIII — Documents Are Shaped by Overridable Templates**, not a clause
  in VII. VII governs where a document goes; VIII governs how it is shaped.
