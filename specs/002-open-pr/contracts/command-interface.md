# Contract: Command Interface — `speckit.github.create-pr`

The extension's user-facing contract. The command is interpreted by the host coding agent; this
defines its name, inputs, decisions, side effects, and chat output.

## Identity

- **Command name**: `speckit.github.create-pr` (registered in `provides.commands`, file `commands/create-pr.md`)
- **Agent trigger (example, Claude)**: `/speckit-github-create-pr`
- **Effect**: `read-write` (outward Git/remote actions, gated by explicit confirmation)

## Arguments (`$ARGUMENTS`)

All optional; the command works with no arguments in the default flow.

| Argument | Meaning |
|----------|---------|
| (none) | Run the full targeting + confirmation flow and open a ready-for-review PR |
| `--draft` | Open the PR as a draft instead of ready-for-review (FR-016) |
| `--base <branch>` | Override the derived target branch (still confirmed before opening) |

## Inputs read (no mutation)

1. Current branch and working-tree state (`git`) → `SourceBranch`.
2. `.specify/memory/constitution.md` *Version Control & Branching Strategy* section → `PromotionFlow`.
3. `.specify/extensions/git/git-config.yml` (if present) → `PromotionFlow`.
4. Remote config (`git config --get remote.origin.url`) → `Remote`.
5. The active spec (`.specify/feature.json` → `specs/<dir>/spec.md`) → PR title/body.

## Decision flow (MUST)

1. **Preconditions** (FR-007): probe `gh` installed, `gh` authenticated, remote is GitHub. On any
   failure → print manual fallback (incl. derived target) and stop. Do not fail opaquely.
2. **Source validation** (FR-005): refuse if detached HEAD, base branch, or non-spec branch; explain.
3. **Existing PR** (FR-010): if an open PR exists for the head branch → return its URL; stop.
4. **Target derivation** (FR-002/003/004/013):
   - conflict between constitution and config → surface, ask;
   - unambiguous promotion flow → next stage, state the rule (no re-pick);
   - no flow → propose default branch, require confirmation of source → target.
5. **Push** (FR-012/014): surface uncommitted changes; if branch not on remote / has unpushed commits,
   ask to push and push on confirmation.
6. **Open PR** (FR-006/011/016): `gh pr create --base <target> --head <source> --title <derived>
   --body <derived>` (`--draft` only on opt-in).
7. **Report** (FR-006/SC-004): return the PR URL in chat.

## Side effects (the ONLY mutations — FR-008)

- `git push -u origin <source-branch>` (only after confirmation).
- `gh pr create ...` (only after confirmation/derivation).
- MUST NOT modify source code, the spec, or the constitution.

## Chat output

- **Success**: a message containing the PR URL, the chosen base branch, and (when derived from a flow)
  the rule it came from.
- **Existing PR**: the existing PR URL with a note that no duplicate was opened.
- **Refusal / degradation**: a clear explanation plus the manual fallback commands.
