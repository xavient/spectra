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
| 1b | **Version marker** | bare `spectra` (works anywhere, touches nothing) | the banner's `cli vX.Y.Z` line matches the repo's `VERSION` file (confirms `--published <tag>` pulled the right source) |
| 1c | **Catalog drives the install** | run `spectra install` and read step 3 | it installs the extensions **the catalog advertises**, not a hardcoded name — this is what lets a new agent ship without a CLI release |
| 2 | **Spec Kit bootstrap declined** | at step 1 answer `n` | dies at step 1 with manual install guidance |
| 2b | **`specify` already present (regression guard)** | pre-install `uv tool install specify-cli --from git+https://github.com/github/spec-kit.git`; re-run | step 1 finds `specify`, no prompt |
| 3 | **Project init declined** | at step 2 answer `n` | dies at step 2 with `specify init` guidance |
| 3b | **Already a Spec Kit project** | after step 1 installs `specify`, run `specify init --here --force`, then re-run | step 2 detects the project, no prompt |
| 4 | **Re-run idempotency** | complete a run, then run `spectra install` again | 2nd run: "already registered" for the catalog, no duplicate catalog entry |
| 5 | **Self-management** | `spectra update` inside an installed project, then `spectra cli uninstall` | the Spectra CLI row reports up to date/ahead against the latest Release; uninstall prompts, then `uv tool list` no longer shows `spectra-cli` |
| 6 | **Removed flags name their replacements** | `spectra --version`, `--update`, `--uninstall` | each exits 2 and names a live replacement — never a bare "unrecognized arguments" |
| 6b | **Retired subcommands name their replacements** | `spectra cli version`, `spectra cli update` | each exits 2 and points at `spectra version` / `spectra update`; neither performs the old action |
| 7 | **The roster is data** | `spectra agent-list` from `/tmp` (not a Spec Kit project) | lists every agent grouped by SDLC phase, exit 0; no planned agent shows a command |
| 8 | **Project state is distinguishable** | `spectra check` in `/tmp`, then in a fresh `specify init` project, then after `spectra install` | three different sentences: not a Spec Kit project (exit 5), not installed + offer, installed (exit 0) |
| 9 | **The whole stack is reported** | `spectra version` after a successful install | four rows — Specify CLI, Core agents, Spectra CLI, Spectra agents; hand-edit `.specify/extensions/spectra/extension.yml` to an older version and that row reports both versions and the output names `spectra update`. Then hand-edit `.specify/integration.json` to an older version and the Core agents row flags it too |
| 10 | **Project uninstall leaves the tool** | `spectra uninstall`, then bare `spectra` | the extension is gone from the project; the command still runs and still reports its version. (`spectra version` cannot be used here: with the project's extension removed it correctly exits 5, which is the state being set up) |

## What this track does NOT cover

- Real cross-platform behavior (the Windows branches of `find_uv`, and the Windows file-lock path in
  `spectra update` / `cli uninstall`). The container is Linux; Windows and macOS still need a human on those
  OSes.
- The extension and its commands **installing and working** — this track tests onboarding only, up to
  the extension being installed. That is exactly what
  [Section 2](#2-the-extension-package-local-zip) covers.

---

## 1a. The stack: `spectra version` / `spectra update` against stale components

`test/run.sh stack` is a different starting point from the bootstrap track above. Instead of a bare
machine, it hands you a **working project** — Spec Kit installed, `specify init` run, Spectra agents
installed — and a set of helpers for putting each component genuinely out of date.

```bash
test/run.sh stack              # ready project + helpers, then a shell
test/run.sh stack --as 4.0.0   # same, but the CLI starts out reporting itself behind
```

Type `scenarios` in the container for the menu.

**Nothing here is mocked.** Each helper creates a real out-of-date state, so the same detection paths
run as would in front of a user:

| Helper | What it really does | Expected report |
|---|---|---|
| `stale_specify [tag]` | installs an older `specify-cli` (default `v0.16.0`) | **two** rows stale — the integration version tracks the CLI, so a behind CLI drags Core agents with it |
| `stale_integration [ver]` | rewrites `version` in `.specify/integration.json` | Core agents stale; other three unchanged |
| `stale_agents [ver]` | rewrites the version in **both** the extension manifest and Spec Kit's `.registry` | Spectra agents stale, and `spectra update` genuinely repairs it |
| `stale_cli [ver]` | rebuilds your working copy carrying a lower `VERSION` | Spectra CLI stale against the live release feed |
| `stack_reset` | restores all four to current | everything up to date |
| `stack_show` | `spectra version` plus its exit code | — |
| `stack_truth` | reads each version from source, bypassing the CLI | lets you check the CLI's verdict against ground truth |

### Two things worth understanding before you start

**Why `stale_cli` rebuilds instead of installing an old release.** You cannot test "my CLI is behind" by
installing an old Spectra CLI, because an old CLI has no four-component report to test. So the helper
installs *your* code with a lower version number; the comparison it then makes against the real GitHub
release feed is genuine.

Related: on an unreleased working copy, the baseline reads
`Spectra CLI: ✓ ahead of published (6.0.0 -> 5.0.0)`. That is correct — your tree is ahead of the newest
published release — and it is why `stale_cli` exists.

**Why `stale_agents` edits two files.** Spec Kit records an extension's installed version in
`.specify/extensions/.registry`; Spectra scans the manifest. Editing only the manifest creates a state
Spectra calls stale and Spec Kit calls current, so its updater exits 0 having changed nothing. Both are
rewritten by default so the state is one `spectra update` can repair.

Pass `--manifest-only` to reproduce that disagreement deliberately:

```bash
stale_agents --manifest-only 1.0.0
spectra update --yes     # must NOT claim success
```

Expected: `! reported success, but the version is unchanged (1.0.0)` and **exit 4**. `spectra update`
re-reads every component after the walk rather than trusting exit codes, so a delegate that reports a
win without moving anything is caught rather than echoed.

### Degraded environments

| Command | Expected |
|---|---|
| `no_specify spectra version` | first two rows `unknown`, other two normal, **exit 0** |
| `no_specify spectra update` | those two skipped, never attempted; exit reflects only what was tried |
| `no_network spectra version` | four `unknown` rows, installed versions still shown, **exit 0** |
| `no_network spectra update` | "Nothing could be checked, so nothing was updated" — never a currency claim |
| `spectra version --no-update-check` | suppresses **only** the Spectra CLI release lookup |
| `rm .specify/integration.json` then `spectra version` | one row `unknown`, rest fine |

`no_specify` moves the `specify` shim aside rather than editing `PATH`, because uv installs `specify`
and `spectra` into the same directory — dropping it from `PATH` would take the command under test with
it.

### The surface, after 6.0.0

| Command | Expected |
|---|---|
| `spectra cli version` | exit 2, names `spectra version` |
| `spectra cli update` | exit 2, names `spectra update` |
| `spectra cli uninstall` | unchanged |
| `spectra --help` | Tool commands panel has **one** row |
| `cd /tmp && spectra version` | exit 5 — it needs a project, by design |
| `cd /tmp && spectra` | the banner's `cli vX.Y.Z`, from anywhere, touching nothing |

That last row is a constitutional requirement (Principle VI), not a nicety: CI's `VERSION` parity check,
the release smoke test, and clean-room row 10 all read it.

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
