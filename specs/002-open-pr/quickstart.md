# Quickstart & Validation: Open PR

This guide proves the `github` extension works end to end. It is a validation/run guide — actual
behavior is defined by `commands/create-pr.md` and the contracts under [contracts/](./contracts/).

## Prerequisites

- A throwaway Spec Kit-initialized project (`.specify/` present) with a **GitHub remote**.
- `git` and the `gh` CLI installed; `gh auth status` authenticated (for the happy-path scenarios).
- The working copy of this extension at `./github`.

## Setup — install the working copy

```bash
specify extension add --dev ./github
```

Confirm the command is registered (e.g., Claude exposes `/speckit-github-create-pr`) and that an
`after_implement` hook now appears in the project's `.specify/extensions.yml` (offer-style, optional).

## Validation scenarios

Run each on a project whose current branch is a real spec branch (e.g., `003-some-feature`).

### S1 — No promotion flow → confirm default branch (P1, MVP)

1. Ensure the constitution defines no promotion flow.
2. Invoke the command (or accept the post-`implement` offer).
3. **Expect**: the agent proposes `<spec-branch> → <default-branch>`, asks for confirmation, and opens
   the PR only after you confirm; the chat reply contains the PR URL. (FR-001, FR-004, SC-001, SC-004)

### S2 — Defined promotion flow → auto-target next stage (P2)

1. Add a promotion flow `feat → dev → main` (constitution section and/or `git-config.yml`); ensure
   `dev` exists on the remote.
2. Invoke the command from the spec branch.
3. **Expect**: PR base is `dev` (not `main`); the agent states it chose `dev` because of the promotion
   flow, and does not ask you to re-pick the base. (FR-003, SC-002)

### S3 — Decline now, open later on demand (P3)

1. At the post-`implement` offer, decline.
2. **Expect**: nothing is pushed and no PR is opened.
3. Later, invoke `speckit.github.create-pr` directly on the same spec branch.
4. **Expect**: it runs the same targeting/confirmation flow and opens the PR. (FR-015)

### S4 — Push flow

1. On a spec branch with local commits not yet on the remote, invoke the command.
2. **Expect**: the agent surfaces the unpushed state, asks to push, pushes on confirmation, then opens
   the PR. It never pushes without confirmation. (FR-012, FR-014)

### S5 — Existing PR → no duplicate

1. With an open PR already on the source branch, invoke the command.
2. **Expect**: the agent returns the existing PR URL and opens no duplicate. (FR-010, SC-005)

### S6 — Graceful degradation (no `gh` / non-GitHub remote)

1. Temporarily make `gh` unavailable (or point the remote at a non-GitHub URL) and invoke the command.
2. **Expect**: a clear explanation plus the manual `git push` + `gh pr create` (or web) fallback,
   including the target branch it would have used — no opaque failure. (FR-007, SC-006)

### S7 — Non-spec branch refusal

1. Check out `main` (or a detached HEAD) and invoke the command.
2. **Expect**: the agent refuses with an explanation (one-branch-per-spec); no PR is opened.
   (FR-005, SC-007)

### S8 — Conflicting strategy

1. Define different promotion flows in the constitution and `git-config.yml`.
2. **Expect**: the agent surfaces the conflict and asks which applies rather than guessing. (FR-013)

## Publishing check (build-time, Principle V)

After authoring/changing the extension:

```bash
python3 build_packages.py
```

**Expect**: `docs/index.html`, `docs/catalog.json`, and `docs/packages/github.zip` are regenerated
with no `!` URL-drift warnings; commit the regenerated `docs/` alongside the `github/` folder and the
updated root `catalog.json`.
