# Contract: Command Interface — `speckit.domain-analyzer.analyze`

The interface this extension exposes to the host coding agent and the user. As an
agent-agnostic Spec Kit command, the "contract" is the command file's front matter,
the inputs it reads, the artifact it writes, and the chat report it must produce.

## Manifest registration (`extension.yml`)

```yaml
provides:
  commands:
    - name: "speckit.domain-analyzer.analyze"
      file: "commands/analyze.md"
      description: "<one-line description>"
```

- `id: domain-analyzer`, `effect: read-write`, `requires.speckit_version: ">=0.11.0"`.
- Command file begins with YAML front matter containing a `description` (Principle III).

## Invocation

- Trigger differs per agent (Spec Kit rewrites at install). Claude: `/speckit-domain-analyzer-analyze`.
- Uses `$ARGUMENTS` for any optional user input; the command MUST function with empty input
  (no required arguments — it analyzes the current project).

## Inputs READ (never written)

| Input | Path | Required | Purpose |
|-------|------|----------|---------|
| Codebase | project source files | yes | Infer domain; ground candidates (FR-001/FR-002) |
| Documentation | docs/READMEs/etc. | if present | Domain evidence |
| Existing constitution | `.specify/memory/constitution.md` | if present | Dedup / amendment marking (FR-009) |
| Existing proposal file | `.specify/memory/domain-analysis.md` | if present | Preserve-and-append on re-run (FR-011) |

## Output WRITTEN

| Output | Path | Rule |
|--------|------|------|
| Proposal file | `.specify/memory/domain-analysis.md` | The ONLY write (FR-010). Format per [proposal-file.md](./proposal-file.md). |

- MUST NOT write/modify source code, the constitution, or any other file (FR-010).

## Chat report (post-run, FR-007)

After writing, the command MUST report in chat:
1. The proposal file path.
2. A one-line summary of the inferred domain.
3. The exact next steps: *review the file → check the items to adopt → run
   `/speckit-constitution` referencing the file*.
4. On re-run: how many new candidates were appended (FR-011 / Journey 3).

## Behavioral guarantees (acceptance-aligned)

| Guarantee | Spec ref |
|-----------|----------|
| Produces ≥1 candidate with id, statement, target section, evidence, confidence | FR-003/FR-004, US1 |
| No candidate pre-selected on a fresh file | FR-005, US1, SC-006 |
| Re-run preserves every prior candidate's state, edits, and order | FR-011, US3, SC-005 |
| No duplicate of an already-ratified guardrail; amendments marked | FR-009, US4 |
| 100% of candidates carry ≥1 file-path evidence reference | SC-002 |
| Sparse project → fewer, lower-confidence candidates (no invented rules) | Edge cases |
| Runs on any coding agent | FR-015, Principle III |

## Handoff to `/speckit-constitution`

The downstream consumer reads only candidates whose checkbox is `- [x]`. See the
selection-signal rules in [proposal-file.md](./proposal-file.md). The Domain Analyzer
does not invoke the constitution agent; the operator runs it separately.
