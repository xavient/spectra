# Testing Spectra

There are **two** independent things to test, and they use different tools:

1. **The installer (`spectra-setup.py`)** — end-to-end onboarding. Tested in a throwaway
   **container** (this folder's `run.sh`) because it must run against a *bare machine* and fetch
   everything from GitHub. This is the real "brand-new user's first five minutes" path. See
   [Section 1](#1-end-to-end-the-installer-container).
2. **The extension package (`docs/packages/spectra.zip`)** — the actual artifact users download from
   the catalog. Tested **locally**: install the zip into a Spec Kit project and exercise every
   command. This is the fast loop for verifying the extension itself — especially after changing its
   structure. See [Section 2](#2-the-extension-package-local-zip).

Rule of thumb: use the **installer/container** track to prove onboarding works end to end; use the
**zip/local** track to prove the extension and its commands actually install and run.

---

# 1. End-to-end: the installer (container)

A throwaway container for testing `spectra-setup.py` the way a brand-new user experiences it: a
**bare machine** with only the unavoidable basics (`python3`, `git`, `curl`) and **nothing else** —
no `uv`, no `specify` CLI, no `.specify/` project, no registered catalog.

That's deliberate: the installer is supposed to bootstrap all of it (install `uv` → install Spec Kit
at the latest release → `specify init` → register the public catalog), so the clean room sets up
nothing and lets the installer prove it works end to end.

Your laptop can't test this honestly — it passed setup long ago and stays "dirty". Each `docker run`
here is a fresh user's first five minutes; exit the shell and the machine is gone.

## Use it

```bash
test/run.sh                  # interactive shell, tests your LOCAL working copy
test/run.sh install          # auto-runs the installer, then drops you in to look
test/run.sh run              # runs the installer once, exits with its code

test/run.sh --release v1.2.0 # downloads + tests the PUBLISHED release artifact
test/run.sh --release v1.2.0 run
```

- **Before tagging:** run the default (local working copy) and walk the scenarios below.
- **After publishing:** run `--release <tag>` so you exercise the exact file users download — not the
  one in your tree.

## No authentication needed

The Spectra catalog is **public**, so the installer authenticates nothing — no `gh` login, no token,
no SSO. It just bootstraps Spec Kit, offers `specify init`, registers the catalog, and lists the
extensions. `--release` mode downloads the published artifact on the *host* with `gh` (a public repo
needs no login for that either), then mounts it in.

## Scenario checklist

The installer's logic that actually breaks between releases lives in a few spots. The container
starts bare, so the **full bootstrap is the default happy path** — no setup needed. Walk these in a
`test/run.sh` shell (`python3 spectra-setup.py`, inspect, `exit`, re-launch for a fresh machine):

| # | Scenario | How to set it up | Expected |
|---|----------|------------------|----------|
| 1 | **Full bootstrap (happy path)** | bare container, run installer, answer `y` to install Spec Kit / `uv` / `specify init`, then `specify extension add spectra` | installs `uv` (astral.sh) then Spec Kit at the latest release; `specify init` creates `.specify/`; catalog registered; `add` downloads the extension anonymously (no token, no 404) |
| 1c | **Version marker** | run installer | splash shows the current `installer vX.Y.Z` (confirms `--release` pulled the right artifact) |
| 2 | **CLI bootstrap declined** | at step 1 answer `n` | dies at step 1 with manual install guidance (uv + git command) |
| 2b | **`specify` already present (regression guard)** | pre-install first: `sh -c "curl -LsSf https://astral.sh/uv/install.sh \| sh"` then `uv tool install specify-cli`; re-run | step 1 finds `specify`, no prompt |
| 3 | **Project init declined** | at step 2 answer `n` | dies at step 2 with `specify init` guidance |
| 3b | **Already a Spec Kit project** | after step 1 installs `specify`, run `specify init --here --force`, then re-run | step 2 detects the project, no prompt |
| 4 | **Re-run idempotency** | complete the installer once, then run it again | 2nd run: "already registered" for the catalog, no duplicate catalog entry |

## What this track does NOT cover

- Real cross-platform behavior (the Windows PowerShell branch of the `uv` bootstrap). The container is
  Linux; the Windows/macOS branches still need a human on those OSes.
- The extension and its commands **installing and working** — this track tests onboarding only, up to
  `specify extension search`. That is exactly what [Section 2](#2-the-extension-package-local-zip)
  covers.

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

You should see `✓ Extension installed successfully!` listing all three provided commands. (This
proves the *zip* is valid and complete — you're installing exactly what it unpacked to.)

**4. Verify registration:**

```bash
specify extension list          # spectra → Status: Enabled
specify extension info spectra  # shows all three commands and the exact triggers
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
  `raw.githubusercontent.com`) — it's exercised by the
  [installer track](#1-end-to-end-the-installer-container).
- Publishing/versioning correctness (catalog entry vs. `extension.yml` vs. zip). Verify those by hand
  per [CONTRIBUTING.md](../CONTRIBUTING.md#publish-the-catalog-and-package).
