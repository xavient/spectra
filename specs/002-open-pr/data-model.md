# Phase 1 Data Model: Open PR

This extension has no persistent data store. The "entities" below are the in-memory concepts the
command derives from real project/Git state to make its targeting and confirmation decisions. They map
directly to the Key Entities in [spec.md](./spec.md).

## Entity: SourceBranch

The branch whose changes the PR proposes — always the current spec branch (one-branch-per-spec).

| Field | Type | Derivation / Rule |
|-------|------|-------------------|
| `name` | string | `git rev-parse --abbrev-ref HEAD` |
| `is_spec_branch` | bool | `name` matches a directory under `specs/` (constitution: branch == spec-dir) |
| `is_detached` | bool | true if HEAD is detached → refuse (FR-005) |
| `is_base_branch` | bool | true if `name` is the default/base branch (e.g., `main`) → refuse (FR-005) |
| `exists_on_remote` | bool | `git ls-remote --heads origin <name>` non-empty |
| `has_uncommitted_changes` | bool | `git status --porcelain` non-empty → surface (FR-012) |
| `has_unpushed_commits` | bool | local ahead of `origin/<name>` → push flow (FR-014) |

**Validation**: A PR may only be opened when `is_spec_branch && !is_detached && !is_base_branch`.

## Entity: PromotionFlow

The ordered chain of branches changes are promoted through, if defined.

| Field | Type | Derivation / Rule |
|-------|------|-------------------|
| `stages` | ordered list of branch names | Parsed from constitution *Version Control & Branching Strategy* and/or `git-config.yml` |
| `defined_in_constitution` | bool | flow present in constitution section |
| `defined_in_config` | bool | flow present in `git-config.yml` |
| `has_conflict` | bool | both defined and `stages` disagree → surface & ask (FR-013) |
| `is_defined` | bool | at least one source defines a flow |

**State logic**:
- `has_conflict` → STOP and ask the user (FR-013).
- `is_defined && !has_conflict` → derive `TargetBranch` as the next stage (FR-003).
- `!is_defined` → propose repository default branch, confirm (FR-004).

## Entity: TargetBranch (base)

The branch the PR is opened against.

| Field | Type | Derivation / Rule |
|-------|------|-------------------|
| `name` | string | Next stage after source in `PromotionFlow`, else repository default branch |
| `source` | enum (`promotion-flow`, `default-branch`) | which rule produced it |
| `derivation_reason` | string | human-readable explanation stated to the user (FR-003) |
| `exists_on_remote` | bool | if a promotion-flow target doesn't exist → surface, never create (edge case) |
| `requires_confirmation` | bool | true when `source == default-branch` (FR-004) |

## Entity: Remote

The Git remote inspected to confirm GitHub and resolve owner/repo.

| Field | Type | Derivation / Rule |
|-------|------|-------------------|
| `url` | string | `git config --get remote.origin.url` |
| `is_github` | bool | URL matches `github.com` (HTTPS or SSH form); else degrade (FR-007) |
| `owner` | string | parsed from URL |
| `repo` | string | parsed from URL |
| `default_branch` | string | `gh repo view --json defaultBranchRef` or `origin/HEAD` |
| `multiple_remotes` | bool | more than one remote / `origin` is a fork → ask (R10) |

## Entity: PullRequest

The PR the command opens (or detects).

| Field | Type | Derivation / Rule |
|-------|------|-------------------|
| `base` | string | `TargetBranch.name` |
| `head` | string | `SourceBranch.name` |
| `title` | string | derived from spec name/summary (FR-011) |
| `body` | string | derived from spec summary + link to spec file (FR-011) |
| `is_draft` | bool | false by default; true only on explicit opt-in (FR-016) |
| `existing_url` | string \| null | from `gh pr list --head <head> --state open`; if set, return it, do not duplicate (FR-010) |
| `url` | string | returned to chat on success (FR-006, SC-004) |

## Entity: ToolingPreconditions

The probes that gate execution and drive graceful degradation (FR-007).

| Field | Type | Derivation / Rule |
|-------|------|-------------------|
| `gh_installed` | bool | `command -v gh` |
| `gh_authenticated` | bool | `gh auth status` |
| `network_ok` | bool | inferred from `gh`/remote calls succeeding |
| `fallback_message` | string | manual `git push` + `gh pr create` commands incl. derived target, shown when any precondition fails |
