# Testing Spectra

There are **two** independent things to test — the repo's two release channels — and they use
different tools:

1. **The CLI (`spectra_cli/` → the `spectra` command)** — end-to-end onboarding. Tested in a throwaway
   **container** (this folder's `run.sh`) because it must run against a *bare machine* and fetch
   everything from GitHub. This is the real "brand-new user's first five minutes" path. See
   [Section 1](#1-end-to-end-the-cli-container).
2. **The extension package (`docs/packages/spectra.zip`)** — the actual artifact users download from
   the catalog. Tested **locally**: install the zip into a Spec Kit project and exercise every
   command. This is the fast loop for verifying the extension itself — especially after changing its
   structure. See [Section 2](#2-the-extension-package-local-zip).

Rule of thumb: use the **CLI/container** track to prove onboarding works end to end; use the
**zip/local** track to prove the extension and its commands actually install and run.

---

# 1. End-to-end: the CLI (container)

A throwaway container for testing the `spectra` command the way a brand-new user experiences it: a
**bare machine** with `uv` and nothing else Spectra-related — no `specify` CLI, no `.specify/`
project, no registered catalog.

`uv` is the one thing pre-installed, and only because it is *how the CLI arrives* — a user about to
run `uv tool install` has already installed uv. Everything downstream of it the CLI is supposed to
bootstrap itself (install Spec Kit at the latest release → `specify init` → register the public
catalog → install the extensions), so the clean room sets up none of it.

Your laptop can't test this honestly — it passed setup long ago and stays "dirty". Each `docker run`
here is a fresh user's first five minutes; exit the shell and the machine is gone.

## Use it

```bash
test/run.sh                  # interactive shell, tests your LOCAL working copy
test/run.sh install          # installs the CLI, runs `spectra install`, then drops you in to look
test/run.sh run              # runs `spectra install` once, exits with its code

test/run.sh --published      # installs from git+https://github.com/xavient/spectra (main)
test/run.sh --published 3.0.0 run   # …or from that tag
```

The local mode mounts your repo read-only and runs `uv tool install spectra-cli --from /work/repo`,
so uv builds your working tree exactly as it would build the published source.

- **Before tagging:** run the default (local working copy) and walk the scenarios below.
- **After publishing:** run `--published <tag>` so you exercise exactly what users get — not the tree
  in your editor.

## No authentication needed

The Spectra catalog is **public**, so the CLI authenticates nothing — no `gh` login, no token, no SSO.
It bootstraps Spec Kit, offers `specify init`, registers the catalog, and installs the extensions the
catalog advertises.

## Scenario checklist

The logic that actually breaks between releases lives in a few spots. The container starts bare, so
the **full bootstrap is the default happy path** — no setup needed. Walk these in a `test/run.sh`
shell (`spectra install`, inspect, `exit`, re-launch for a fresh machine):

| # | Scenario | How to set it up | Expected |
|---|----------|------------------|----------|
| 1 | **Full bootstrap (happy path)** | bare container, run `spectra install`, answer `y` to install Spec Kit / `specify init` | Spec Kit installs at the latest release; `specify init` creates `.specify/`; catalog registered; the extension downloads anonymously (no token, no 404) and its commands are listed |
| 1b | **Version marker** | `spectra --version` | matches the repo's `VERSION` file (confirms `--published <tag>` pulled the right source) |
| 1c | **Catalog drives the install** | run `spectra install` and read step 3 | it installs the extensions **the catalog advertises**, not a hardcoded name — this is what lets a new agent ship without a CLI release |
| 2 | **Spec Kit bootstrap declined** | at step 1 answer `n` | dies at step 1 with manual install guidance |
| 2b | **`specify` already present (regression guard)** | pre-install `uv tool install specify-cli --from git+https://github.com/github/spec-kit.git`; re-run | step 1 finds `specify`, no prompt |
| 3 | **Project init declined** | at step 2 answer `n` | dies at step 2 with `specify init` guidance |
| 3b | **Already a Spec Kit project** | after step 1 installs `specify`, run `specify init --here --force`, then re-run | step 2 detects the project, no prompt |
| 4 | **Re-run idempotency** | complete a run, then run `spectra install` again | 2nd run: "already registered" for the catalog, no duplicate catalog entry |
| 5 | **Self-management** | `spectra --update`, then `spectra --uninstall` | update reports up-to-date/ahead against the latest Release; uninstall prompts, then `uv tool list` no longer shows `spectra-cli` |

## What this track does NOT cover

- Real cross-platform behavior (the Windows branches of `find_uv`, and the Windows file-lock path in
  `--update` / `--uninstall`). The container is Linux; Windows and macOS still need a human on those
  OSes.
- The extension and its commands **installing and working** — this track tests onboarding only, up to
  the extension being installed. That is exactly what
  [Section 2](#2-the-extension-package-local-zip) covers.

---

# 2. The extension package (local zip)

This track tests the **built package** — `docs/packages/spectra.zip`, the exact artifact the catalog
serves — without needing the container or the catalog. You unzip the package into a local folder and
install it into a throwaway Spec Kit project, then run every command. Use this whenever you change the
extension's structure, add or rename a command, or edit a command's prompt.

Spectra ships as a **single** extension (`id: spectra`); installing it registers all of its commands
at once under the `speckit.spectra.*` namespace:

- `speckit.spectra.adr`
- `speckit.spectra.domain-analyzer`
- `speckit.spectra.create-pr`
- `speckit.spectra.brd`

## Prerequisites

- The `specify` CLI on your PATH (`specify --version`).
- A coding agent to invoke the commands (examples below use Claude).
- No GitHub token or catalog needed — you install straight from the local zip.

## Steps

**1. (Re)build the package** if you've changed anything under `spectra/`. Run from the repo root so
the zip has a single top-level `spectra/` folder (the layout Spec Kit expects):

```bash
rm -f docs/packages/spectra.zip
zip -r -X docs/packages/spectra.zip spectra -x '*.DS_Store'
```

Sanity-check the layout — you should see `spectra/extension.yml`, `spectra/commands/*.md`, etc.:

```bash
unzip -l docs/packages/spectra.zip
```

**2. Create a throwaway Spec Kit project** to install into (keeps your real projects clean):

```bash
specify init /tmp/spectra-pkg-test --integration claude
cd /tmp/spectra-pkg-test
```

**3. Unzip the package to a local folder and install it** with `--dev` (point it at the unzipped
`spectra/` folder — the one containing `extension.yml`):

```bash
unzip -o /path/to/repo/docs/packages/spectra.zip -d /tmp/spectra-pkg
specify extension add --dev /tmp/spectra-pkg/spectra
```

You should see `✓ Extension installed successfully!` listing every provided command. (This
proves the *zip* is valid and complete — you're installing exactly what it unpacked to.)

**4. Verify registration:**

```bash
specify extension list          # spectra → Status: Enabled
specify extension info spectra  # shows every command and the exact triggers
```

**5. Run each command in your agent.** Restart the agent first so it picks up the new skills/commands.
On Claude the triggers are dash-form skills:

```
/speckit-spectra-adr We should standardize on PostgreSQL for all primary data stores
/speckit-spectra-domain-analyzer
/speckit-spectra-create-pr --draft
```

(Other agents keep the dots, e.g. kiro-cli: `/speckit.spectra.adr`.) Confirm each command runs, reads
real project context, and writes to the expected place — `Docs/ADR/` for `adr`,
`.specify/memory/domain-analysis.md` for `domain-analyzer`, and a PR/branch action for `create-pr`.

**6. Iterate and clean up.** After editing files under `spectra/`, rebuild the zip (step 1),
re-unzip, and reinstall with `--force`, then restart your agent:

```bash
specify extension add --dev /tmp/spectra-pkg/spectra --force
```

Remove it when done, or just delete the throwaway project:

```bash
specify extension remove spectra
rm -rf /tmp/spectra-pkg-test /tmp/spectra-pkg
```

## What this track does NOT cover

- The catalog/download path (`specify extension add spectra` from the registered catalog over
  `raw.githubusercontent.com`) — it's exercised by the [CLI track](#1-end-to-end-the-cli-container).
- Publishing/versioning correctness (catalog entry vs. `extension.yml` vs. zip). CI checks this on
  every push — see the `catalog` job in `.github/workflows/ci.yml` — and
  [CONTRIBUTING.md](../CONTRIBUTING.md#publish-the-catalog-and-package) documents the manual steps.
