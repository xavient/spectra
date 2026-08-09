# Phase 0 — Research & Decisions

Twelve decisions, each grounded in a file that already exists in this repository rather than in general
best practice. Nothing here was left as NEEDS CLARIFICATION.

---

## 1. Roster format and location

**Decision**: A single JSON object at `agents-list.json` in the repository root, with three top-level
keys: `schema_version`, `phases`, and `agents`. No `updated_at`.

**Rationale**: FR-001 fixes the filename and location, and JSON is the only format the CLI can read
without a dependency (`json` is stdlib; YAML is not). Placing it beside `catalog.json` means it is
published by the identical mechanism — raw links from `main`, live on merge, no release step — which is
what FR-001 and the Assumptions require. `updated_at` is omitted deliberately: `catalog.json` carries a
hand-maintained timestamp today and it is already stale (`2026-08-08`), which is a small demonstration of
exactly the drift this feature exists to remove. A field nobody can verify is a field that lies.

**Alternatives considered**: Extending `catalog.json` with an `agents` key — rejected because
`catalog.json` is a Spec Kit-defined document with its own schema, and adding non-standard keys to it
risks breaking Spec Kit's own parsing. A YAML roster — rejected outright: it would either need a
dependency or a hand-rolled parser for a format far more complex than the manifest's one line we already
scan.

---

## 2. AI-DLC phase is recorded on the phase, not on each agent

**Decision**: `phases[]` carries `id`, `title`, and `aidlc`. Each agent references a phase by id. The
generator expands the AI-DLC value into each table row.

**Rationale**: The mapping is a total function of SDLC phase — Foundation and Requirements & Discovery →
Inception; Architecture & Design, Planning, Implementation, Testing & Quality → Construction; Deployment
& Operations → Operation. Verified against all 44 rows of the current README table: there is no agent
whose AI-DLC phase differs from its phase-mates. Storing it 44 times creates 44 chances to disagree.

**Flagged**: FR-003 reads "For each agent the roster MUST record … its AI-DLC phase". This design records
it *for* each agent, unambiguously, but *once per phase*. If the strict per-entry reading is intended,
this is the one decision in this document that must be reversed; the cost is a redundant field and a
CI check to keep it consistent with the phase. Recorded in the plan's Complexity Tracking so the
`analyze` gate sees it rather than discovering it.

**Alternatives considered**: Per-agent `aidlc_phase` with a consistency check — rejected as strictly more
machinery for strictly less integrity. Dropping AI-DLC entirely — rejected: the README table publishes
the column and the generator must produce it.

---

## 3. A stable slug `id`, and what the ids are

**Decision**: Every entry carries a lowercase-slug `id`, unique across the roster, distinct from `title`.
Shipped Spectra agents use the slug already visible in their command and file name — `adr`,
`domain-analyzer`, `brd`, `create-pr`. Spec Kit core agents use their command's final segment —
`constitution`, `specify`, `clarify`, `checklist`, `plan`, `tasks`, `analyze`, `implement`, plus `testing`
for the one that has no command of its own. Planned agents get short deliberate slugs (full map in
`data-model.md`).

**Rationale**: Settled by the session's first clarification. `create-pr` is chosen over `github` or
`github-pr` because `spectra/commands/create-pr.md` and `speckit.spectra.create-pr` already use it, so the
id needs no separate act of remembering. The three-way name disagreement FR-010 must resolve
(`github` / GitHub / GitHub (PR)) collapses to `id: create-pr`, `title: GitHub (PR)`.

**Alternatives considered**: Title-derived slugs — rejected, because they would change when a title
changes, which is the failure FR-003b exists to prevent.

---

## 4. Schema version semantics and the CLI's tolerance

**Decision**: `schema_version` is `"MAJOR.MINOR"`, starting at `"1.0"`. The CLI holds a supported major
constant. Newer minor → render recognized fields, ignore unknown ones, print a notice naming
`spectra cli update`. Newer major → refuse, explain, name `spectra cli update`. Older or equal → silent.

**Rationale**: Settled by the session's second clarification. `catalog.json` already uses a
`"MAJOR.MINOR"` `schema_version` string, so the roster matches its sibling. The asymmetry is the point:
adding a field must never break an installed CLI, because Principle VI promises new agents reach existing
installs with no CLI release — a hard failure on any additive change would quietly convert that promise
into a lie.

**Alternatives considered**: Ignoring the field at runtime — rejected: it makes a genuinely incompatible
future roster render as garbage. Failing on any mismatch — rejected for the reason above.

---

## 5. Reading the installed and published versions without a YAML parser

**Decision**: Scan for the first line matching `^  version: "(.*)"$` inside the `extension:` block, the
same expression `.github/workflows/ci.yml` already uses via `sed`. Applied to
`<project>/.specify/extensions/spectra/extension.yml` for the installed version and to the raw URL of
`spectra/extension.yml` on `main` for the published one.

**Rationale**: Verified against real installed manifests in this repo — `.specify/extensions/git/extension.yml`
and `.specify/extensions/agent-context/extension.yml` both carry `  version: "1.0.0"` at exactly that
indentation, nested under `extension:`. The shape is fixed by Spec Kit's own manifest schema and already
load-bearing in CI, so a line scanner is not a shortcut here; it is the established approach in this
repository. FR-031 names the manifest as the source, and CI already guarantees `catalog.json` agrees, so
the two are interchangeable in practice — the manifest is used because the spec says so and because
Principle VI calls it authoritative.

**Alternatives considered**: `.specify/extensions/.registry` — a genuinely tempting JSON file that records
`version` per installed extension, discovered during research. Rejected: it is Spec Kit's private
bookkeeping, undocumented, and free to change shape without notice; FR-031 also names the manifest
explicitly. Vendoring a mini-YAML parser — rejected as far more code and far more failure modes than the
one line being read justifies.

---

## 6. Marker syntax for generated regions, and prose anchors

**Decision**: HTML comments, following the `<!-- SPECKIT START -->` / `<!-- SPECKIT END -->` pattern
already used in `CLAUDE.md`:

```markdown
<!-- SPECTRA:GENERATED START id=readme-agents-table -->
<!-- Generated from agents-list.json — do not edit by hand. Run tools/generate_agent_docs.py. -->
…generated content…
<!-- SPECTRA:GENERATED END id=readme-agents-table -->
```

Each hand-authored prose block is preceded by `<!-- SPECTRA:AGENT id=adr -->`.

**Rationale**: Invisible in rendered Markdown on GitHub, so FR-024 (the repo reads correctly for someone
who never runs the generator) is unaffected. Named ids let one file hold several regions, which is what
lets `AGENTS_LIST.md` keep its current section order — the spec's Assumptions rely on this. The visible
"do not edit" line inside the region satisfies FR-014. Anchoring prose blocks by id rather than by
heading text is what makes FR-003b true: the `### \`github\` — GitHub ✅` heading is about to be reworded,
and prose matching must survive it.

**Alternatives considered**: Whole-file generation with prose in separate include files — rejected as a
much larger change to how the documentation reads and is edited. Matching prose blocks by heading text —
rejected; it re-couples machinery to display text.

---

## 7. Generator location, invocation, and the check that backs it

**Decision**: One script, `tools/generate_agent_docs.py`, stdlib only. Default run rewrites the regions;
`--check` regenerates in memory and compares, additionally asserting prose-block presence and
roster↔manifest agreement. Non-zero exit with a named file or agent on any failure. CI runs `--check`. No
pre-commit hook.

**Rationale**: FR-011 wants one command; FR-017 through FR-019 want three checks, and folding them into
`--check` gives CI one step to run and a contributor one command to reproduce it. Stdlib-only means CI
adds no install step and `pyproject.toml`'s deliberate `dependencies = []` is untouched, which matters
because that emptiness is itself documented policy. `tools/` stays out of the wheel because
`[tool.setuptools] packages = ["spectra_cli"]` lists packages explicitly rather than auto-discovering —
so FR-023 holds by construction.

**Alternatives considered**: Two scripts (generate + verify) — rejected; they would duplicate the
rendering logic, and any divergence between them is a false pass. A pre-commit hook — rejected per the
spec's Assumptions: CI is the backstop, and a hook that rewrites files during commit surprises people.

---

## 8. What exactly the generator owns

**Decision**: Four regions — the README Agents table, the Spec Kit core agents section of
`AGENTS_LIST.md`, the Roadmap section of `AGENTS_LIST.md`, and the Commands table in `spectra/README.md`.
The README region is drawn slightly wider than a bare table: it also contains the sentence enumerating which
✅ agents come from Spec Kit rather than Spectra. Two adjacent counts are removed from hand-authored prose
instead of being generated — `AGENTS_LIST.md`'s "These four ship in the `spectra` extension today" and the
root README's inline list of the four command names are both reworded to drop the enumeration.

**Rationale**: That README sentence lists nine agent titles. It is classification wearing prose clothing,
and it would drift on the very first roster change while every table around it stayed correct — the exact
failure mode BR-09 documents. Rewording the "four" is cheaper than generating a count and reads better
than "These 4".

`spectra/README.md` was added to this list during cross-artifact analysis, not during planning. It
independently declared all four shipped agents in a Commands table, *and* named the PR agent a fourth way
("GitHub PR delivery") beyond the three the BRD identified — while shipping inside
`docs/packages/spectra.zip`, so a stale copy is republished to everyone who downloads the package. Its
Effect column is dropped rather than modelled in the roster, because `spectra/extension.yml` already
declares `effect: read-write` for the extension as a whole. Its four hand-written per-agent sections stay
hand-written, guarded by the weaker title-containment check (FR-018a) rather than by generation.

**Alternatives considered**: Leaving the README sentence hand-written — rejected; it is a known drift site
being walked past. Generating the count sentence — rejected as over-engineering for one word. Deleting
`spectra/README.md`'s Commands table outright instead of generating it — genuinely tempting, since the same
file repeats the same four agents in detail immediately below, but rejected because a summary index at the
top of the extension's own README earns its place, and generating it costs one more region in machinery we
are building anyway. Adding an `effect` field to the roster to preserve the dropped column — rejected: a
field exists to be a source of truth, and the manifest already is one for effect.

---

## 9. Project discovery and installation-state classification

**Decision**: Walk up from `Path.cwd()` through its parents to the nearest directory containing
`.specify/`. Then classify into exactly four states: `NOT_A_PROJECT`, `NOT_INSTALLED`, `INCOMPLETE`,
`INSTALLED`.

**Rationale**: `install.py`'s `check_in_specify_project()` already walks `[here, *here.parents]` looking
for `.specify/`, so FR-040 is satisfied by reusing an established pattern rather than inventing one.
`INCOMPLETE` exists because FR-045 demands it: the folder can be present with an unreadable or
version-less manifest after an interrupted install, and reporting that as either "installed" or "absent"
would be a lie in one direction or the other. Four states map exactly onto SC-009's four required
messages.

**Alternatives considered**: Presence of the folder alone as a boolean — rejected by FR-045. Asking
`specify extension list` and parsing it — rejected: it is slower, needs `specify` on PATH just to answer
"is it installed", and couples the answer to another tool's output formatting.

---

## 10. Delegation to Spec Kit, and who owns the confirmation prompt

**Decision**: `spectra update` runs `specify extension update spectra`. `spectra uninstall` runs
`specify extension remove spectra`, adding `--force` when the user passed `--yes`. Spectra does not add a
second confirmation prompt of its own.

**Rationale**: Verified by running `specify extension remove --help` — it already prompts and already
offers `--force` to skip. The spec's Assumption ("`spectra uninstall` asks for confirmation … with a
non-interactive bypass flag") is therefore satisfied by delegation; adding our own prompt would make the
user confirm twice for one action. `specify extension update --help` confirms `update` takes the
extension id and needs no flags. FR-034's "must first confirm the extension is installed" is a state
check, not a prompt, and is handled by decision 9 before either delegation runs.

**Alternatives considered**: Prompting in Spectra and always passing `--force` — rejected; it puts the
safety gate in the outer tool while the inner tool does the destructive work unguarded, which is worse if
anyone ever calls `specify` directly. Manipulating `.specify/extensions/` ourselves — rejected by the
spec's Assumptions and by Principle II's deference to Spec Kit.

---

## 11. The command surface, and how removed flags still help

**Decision**: `argparse` subparsers. Top level: `install`, `check`, `version`, `update`, `uninstall`,
`agent-list`. Group: `cli version`, `cli update`, `cli uninstall`. The three removed flags are detected
in `argv` *before* parsing and produce a message naming the replacement, exiting 2.

**Rationale**: FR-039 requires the replacement to be named, and argparse cannot do that for an argument
it no longer defines — it emits "unrecognized arguments" and stops. Pre-parse detection is the only way to
turn that into a useful sentence. Registering the flags as hidden aliases was the obvious alternative and
is forbidden outright by FR-038 ("MUST NOT be retained as aliases"), so the check must live outside the
parser. `cli.py` already owns a hand-rendered help surface built from an `OPTIONS`/`COMMANDS` list and
`ui.panel()`; that becomes three panels — Project commands, Tool commands, Options — which is how FR-043
gets satisfied without inventing a new presentation layer.

**Alternatives considered**: A separate `spectra-cli` executable for tool management — rejected: two
binaries for one tool is a worse answer to a naming problem than one namespace.

**Exit code map** (extends the codes `cli.py` already uses — 0/1/2/3/4/130):

| Code | Meaning |
| --- | --- |
| 0 | Success, including any delivered verdict (up to date, out of date, ahead) |
| 1 | The user declined an offered action |
| 2 | Usage error — bad flag, unknown command, or a removed flag |
| 3 | Published data could not be retrieved within the timeout |
| 4 | A delegated command (`specify` or `uv`) failed |
| 5 | The project is not in the required state — not a Spec Kit project, not installed, or incomplete |
| 130 | Interrupted |

FR-032a is satisfied by construction: `version` returns 0 for all three verdicts, 3 on fetch failure,
5 on any bad project state. `uninstall` when Spectra is absent returns **0**, not 5 — the requested end
state already holds, mirroring how `cmd_uninstall` already treats an absent uv tool as an idempotent
no-op. The spec leaves this open; the choice is recorded in `contracts/cli-surface.md`.

---

## 12. The landing page, and the description everywhere

**Decision**: `docs/index.html` fetches `agents-list.json` at load and renders the roster-derived content
from it — titles, statuses, phases, one-line descriptions, commands. Its hand-written per-command detail
(arguments, worked examples) stays in the HTML. The extension description is read from the already-fetched
`catalog.json` instead of being hard-coded in the page.

**Rationale**: FR-052 requires the page to read agent information from the roster, and the page already
does exactly this shape of thing twice — it fetches the newest GitHub Release for the CLI version and
`catalog.json` for the extension version, with a comment citing Principle VI's no-hard-coded-versions
rule. Extending that established pattern to the description and the roster costs a third fetch and
removes two more hand-typed strings. The split mirrors the Markdown split: generated classification,
hand-written prose. The roster carries only one-line descriptions (FR-004), so it *cannot* supply the
arguments and examples, which settles the boundary on its own.

**Alternatives considered**: Generating the HTML from the roster with the same script — rejected; the page
would need markers and the generator would grow an HTML renderer, when a `fetch` the page already knows
how to do is enough. Hard-coding the new description in the page — rejected by FR-051's "every published
copy MUST agree", which is only reliably true if there is one copy.

---

## Version bumps and the CI consequence

| Artifact | From | To | Why |
| --- | --- | --- | --- |
| `VERSION` (CLI channel) | 4.0.0 | 5.0.0 | MAJOR — three flags removed and tool commands renamed (FR-049). |
| `spectra/extension.yml` + `catalog.json` (catalog channel) | 1.3.0 | 1.3.1 | PATCH — description metadata only; no command added, changed, or removed. |
| `.specify/memory/constitution.md` | 1.3.0 | 1.4.0 | MINOR — materially changed guidance in Principle V (FR-022). |

**A CI assertion breaks and must move.** `.github/workflows/ci.yml` currently runs `spectra --version` and
fails the build unless its output equals `VERSION`. That flag is being removed, so the assertion moves to
`spectra cli version`. To keep it a one-line comparison, `cli version` prints the bare version on its
first line and any "newer release available" notice on subsequent lines — the format `cmd_version`
already uses. Three checks are added alongside it: `python tools/generate_agent_docs.py --check`,
`python -m unittest discover -s tests`, and a description-parity check asserting the agreed line appears
identically in `spectra/extension.yml` and `catalog.json`.
