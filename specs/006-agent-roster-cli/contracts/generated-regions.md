# Contract — generated regions and prose anchors

The boundary between what the generator owns and what a human writes. Both sides are enforced: CI fails if
a generated region drifts, and CI fails if a shipped agent has no prose (FR-014, FR-017, FR-018).

## Region markers

```markdown
<!-- SPECTRA:GENERATED START id=readme-agents-table -->
<!-- Generated from agents-list.json — do not edit by hand. Run: python tools/generate_agent_docs.py -->

…generated content…

<!-- SPECTRA:GENERATED END id=readme-agents-table -->
```

Rules:

1. HTML comments, so nothing is visible in rendered Markdown and the documents still read correctly on
   GitHub for anyone who never runs the generator (FR-024).
2. Follows the `<!-- SPECKIT START -->` / `<!-- SPECKIT END -->` pattern already in `CLAUDE.md`, so the
   convention is recognizable rather than novel.
3. The `id=` is required on both markers and must match. Ids are fixed and known to the generator.
4. The second line — the human-readable "do not edit" notice — is regenerated as part of the region. It is
   what satisfies FR-014 for a reader who is not consulting this document.
5. A file may hold several regions. This is what lets `AGENTS_LIST.md` keep its current section order,
   with hand-written prose sitting between two generated sections.
6. Content outside any region is never read and never written (FR-015).

### Failure modes, all hard errors (FR-020)

| Condition | Generator behaviour |
| --- | --- |
| A known id's START marker is missing | Fail, naming the file and the missing marker id |
| END missing, or END id ≠ START id | Fail, naming the file and the mismatch |
| The same id appears twice in one file | Fail, naming the file and the duplicate id |
| A region in the file has an id the generator does not know | Fail, naming the unknown id |

The generator never guesses a region's extent, never appends a missing marker, and never skips a file it
cannot parse — silently skipping is how a "successful" run leaves documentation stale.

## The three regions

| Region id | File | Generated content |
| --- | --- | --- |
| `readme-agents-table` | `README.md` | The Agents table — one row per roster entry, columns Agent / SDLC phase / AI-DLC phase / Type / Status — plus the sentence naming which ✅ agents are Spec Kit's own rather than Spectra's. |
| `agents-list-speckit-core` | `AGENTS_LIST.md` | The Spec Kit core agents section body: one subsection per `provider: speckit` entry, with its title, command, one-line description, and how to run it. |
| `agents-list-roadmap` | `AGENTS_LIST.md` | The Roadmap section body: `status: planned` entries grouped under their phase title, in roster order. |

The `readme-agents-table` region is deliberately drawn a little wider than FR-012's letter, to include that
trailing sentence. It enumerates nine agent titles — classification in prose clothing — and it is the
sentence most likely to be correct today and wrong after the next roster change. Recorded in
`research.md` decision 8.

## Prose anchors

Each hand-authored prose block in `AGENTS_LIST.md` is preceded by an anchor:

```markdown
<!-- SPECTRA:AGENT id=adr -->
### Architecture Decision Records (ADR) ✅

**`speckit.spectra.adr`** — …hand-written explanation, arguments, worked examples…
```

Rules:

1. The anchor's `id` must equal a roster `agents[].id`.
2. One anchor per prose block; one prose block per shipped Spectra agent.
3. The generator **reads only the anchor**. It never parses, rewrites, reformats, or validates the prose
   itself — its wording is enforced by review, not by machine (FR-013).
4. Anchors live outside every generated region, in the hand-authored part of the file.

### Why anchors instead of headings

Because heading text is display text, and this change is about to reword one. `### \`github\` — GitHub ✅`
becomes the `GitHub (PR)` form; matching prose by heading would break on exactly that edit, and would keep
breaking every time an agent is renamed. The anchor is the stable slug, so FR-003b holds: a title can be
reworded freely and prose matching survives.

## What `--check` asserts

| Assertion | Failure message names | Requirement |
| --- | --- | --- |
| Each region matches what the roster would produce | the file, and the region id | FR-017 |
| Every `provider: spectra`, `status: available` id has an anchor | the agent id whose prose is missing | FR-018 |
| No anchor exists for an id outside that set | the offending anchor id | FR-018 |
| The roster's shipped-Spectra id set equals the manifest's command set | the ids present in one and not the other | FR-019 |
| Each shipped entry's `command` equals the manifest's registered command | the agent id and both command strings | FR-019a |
| Roster descriptions are single-line, ids unique and slug-shaped, `phase` resolves, `command` present iff available | the offending field and agent id | FR-004, FR-007, FR-003a |

Descriptions in the roster and the manifest are **not** compared. They address different audiences — the
manifest's are consumed by Spec Kit and the user's coding agent at install time, the roster's are one-liners
for a table — and forcing them equal would make one of the two worse (FR-019a, settled by clarification).

## Determinism

Running the generator twice against an unchanged roster produces byte-identical files (FR-016, SC-011).
Concretely: iteration follows roster array order only, never a dictionary iteration order or a sort by a
mutable field; no timestamps, no version strings, and no environment-derived values are written into a
region; and line endings are written `\n` regardless of platform, so a Windows checkout does not appear
drifted to CI (FR-050).
