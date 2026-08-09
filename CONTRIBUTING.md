# Contributing to Spectra

This guide is for developers building and maintaining the **Spectra** extension. If you just want to
install and use Spectra, see the [README](README.md).

Spectra is a **single self-contained** [Spec Kit](https://github.com/github/spec-kit) extension,
`spectra/`, at the repo root. Every Spectra capability is a **command** under it, registered in one
`spectra/extension.yml` and named in the unified `speckit.spectra.<command>` namespace — Spec Kit
validates command names against `^speckit\.<extension-id>\.<command>$`, so the middle segment must be
the extension id (`spectra`). Spectra is distributed straight from the **public** `xavient/spectra`
repo over direct `raw.githubusercontent.com` links — a root `catalog.json` lists the extension, and
anyone installs it by name with **no authentication** (the catalog is public, so the raw URLs resolve
anonymously). Read the
[Spec Kit Extension Development Guide](https://github.com/github/spec-kit/blob/main/extensions/EXTENSION-DEVELOPMENT-GUIDE.md)
for the authoritative manifest and command-naming rules.

## Repository layout

```
spectra/
├── catalog.json                   # THE catalog — single source of truth; install points here
├── VERSION                        # THE CLI version — single source of truth; the release tag must match
├── pyproject.toml                 # packaging for the `spectra-cli` uv tool
├── spectra_cli/                   # THE CLI (installed as `spectra`; NOT the extension)
│   ├── cli.py                     #   argparse entry point: install / --version / --update / --uninstall
│   ├── install.py                 #   the 3-step flow: specify CLI → project → catalog + extensions
│   ├── version.py                 #   version reporting and uv-delegated update/uninstall
│   └── ui.py                      #   colors, splash, prompts, subprocess helpers
├── .github/workflows/             # CI + the tag-triggered CLI release
├── assets/                         # shared images (committed)
│   ├── TELUS_Digital_logo.png      #   the one logo (used by the README + landing page)
│   ├── SDD.png                     #   Spec-Driven Development diagram
│   ├── SDLC-to-AIDLC.png           #   SDLC → AI-DLC mapping diagram
│   └── AIDLC-mapping.png           #   per-phase AI-DLC mapping diagram
├── docs/                          # downloadable package + static landing assets (committed)
│   ├── index.html                 #   landing page: the extension + its install command
│   ├── onePager.html              #   static one-pager
│   ├── packages/spectra.zip       #   the one downloadable package (top-level spectra/ folder)
│   └── .nojekyll                  #   serve files as-is (no Jekyll processing)
├── README.md                      # user-facing: what Spectra is + how to install
├── CONTRIBUTING.md                # this file
├── LICENSE                        # Apache License 2.0
├── NOTICE                         # required attribution notice (Apache 2.0 §4(d))
└── spectra/                       # THE extension (folder name == extension id `spectra`)
    ├── extension.yml              #   the extension manifest (registers every command)
    ├── commands/                  #   one Markdown file per command
    │   ├── adr.md                 #     speckit.spectra.adr
    │   ├── domain-analyzer.md     #     speckit.spectra.domain-analyzer
    │   └── create-pr.md           #     speckit.spectra.create-pr
    ├── README.md                  #   extension docs (ships inside the zip)
    ├── CHANGELOG.md               #   extension changelog
    ├── LICENSE                    #   Apache License 2.0
    └── NOTICE                     #   attribution notice (ships inside the zip)
```

Two things live here, and it matters which one you are touching. [`spectra/`](spectra/) is **the
extension** — the agents, shipped over raw links and versioned in `extension.yml`. `spectra_cli/` is
**the CLI** — the `spectra` command that sets a project up, shipped as a uv tool and versioned in
`VERSION`. They release independently; see [Two release channels](#release-the-cli-spectra-cli).

New capabilities are added as command files under `spectra/commands/`, not as new top-level folders
and not as CLI code. The repo is **public**; clients fetch the catalog and package over **direct
`raw.githubusercontent.com` links** to `xavient/spectra`, so anyone installs by name with no
authentication. There is no build script: when you add or change a command you update `catalog.json`
and `docs/packages/spectra.zip` by hand (see [Publish](#publish-the-catalog-and-package)).
`catalog.json` is the single source of truth for the catalog.

## Anatomy of an extension

### `extension.yml`

The manifest. Field reference:

| Field | Required | Notes |
| ----- | -------- | ----- |
| `schema_version` | yes | Manifest schema version (currently `"1.0"`). |
| `extension.id` | yes | Unique id. **Must match the folder name.** Lowercase, kebab-case. |
| `extension.name` | yes | Human-readable name. |
| `extension.version` | yes | Semantic version (e.g. `1.0.0`). Must match the latest `CHANGELOG.md` entry. |
| `extension.description` | yes | One-line summary (shown on the site's landing page). |
| `extension.category` | yes | Grouping, e.g. `docs`, `quality`, `security`. |
| `extension.effect` | yes | `read-only` or `read-write` — what the commands do to the project. |
| `extension.author` | yes | `TELUS Digital`. |
| `extension.repository` | yes | `https://github.com/xavient/spectra`. |
| `extension.license` | yes | `Apache-2.0`. |
| `extension.homepage` | no | Link to the extension folder. |
| `requires.speckit_version` | yes | The Spec Kit version range you actually tested against — see [Compatibility](#compatibility). |
| `provides.commands[]` | yes | List of commands; each has `name`, `file`, `description`. |
| `tags` | no | Search keywords. |

Example (`spectra/extension.yml`) — one manifest registers every command:

```yaml
schema_version: "1.0"

extension:
  id: "spectra"
  name: "Spectra"
  version: "1.1.0"
  description: "Spectra's agentic SDLC commands for Spec Kit, bundled as a single extension."
  category: "workflow"
  effect: "read-write"
  author: "TELUS Digital"
  repository: "https://github.com/xavient/spectra"
  license: "Apache-2.0"
  homepage: "https://github.com/xavient/spectra/tree/main/spectra"

requires:
  speckit_version: ">=0.11.0"

provides:
  commands:
    - name: "speckit.spectra.adr"
      file: "commands/adr.md"
      description: "Create a new Architecture Decision Record from a short description."
    - name: "speckit.spectra.domain-analyzer"
      file: "commands/domain-analyzer.md"
      description: "Infer the project's domain and propose opt-in constitution guardrails."
    - name: "speckit.spectra.create-pr"
      file: "commands/create-pr.md"
      description: "Open a correctly-targeted GitHub PR for the current spec branch."

tags: ["documentation", "architecture", "adr", "governance", "delivery", "workflow"]
```

### Command files

Each entry in `provides.commands` points at a Markdown file under `commands/`. That file is the prompt
the agent runs.

- **Naming.** The command `name` is namespaced `speckit.spectra.<command>` — a fixed `spectra`
  segment followed by a clear, descriptive command name, e.g. `speckit.spectra.adr`. The leading
  `speckit.spectra.` is required for every Spectra command. The `file` is the path relative to
  the extension folder (e.g. `commands/adr.md`).
- **Front matter.** Start the file with a YAML front-matter block containing a `description`.
- **Generic format.** Write commands in Spec Kit's generic format and use `$ARGUMENTS` for user input.
  Spec Kit translates the file into each agent's native command format at install time, so a single
  source file supports every agent (both slash-command and skills-mode). Don't hard-code one agent's
  syntax.
- **Be context-aware.** Good Spectra commands read real project context (the constitution under
  `.specify/memory/`, specs under `specs/`, existing artifacts, and source code) before acting, rather
  than blindly filling a template. See [`spectra/commands/adr.md`](spectra/commands/adr.md) for the pattern.

Minimal skeleton:

```markdown
---
description: "One-line summary shown in the agent's command list."
---

# <What this command does>

$ARGUMENTS

<Step-by-step instructions for the agent...>
```

## Add a new command (use the Spec Kit workflow)

**Do not hand-create the files.** Spectra dogfoods Spec Kit (Constitution
[Principle I](.specify/memory/constitution.md)): every new command is built by running the
spec-driven workflow on a feature branch, not by copying files and editing them. Running the workflow
is itself how we exercise the extension we publish. A new capability is a **new command file under
`spectra/commands/`** registered in `spectra/extension.yml` — never a new top-level extension folder.

Run these Spec Kit commands in order from your agent (Claude triggers shown in parentheses; the
generic Spec Kit form is `/speckit.<step>`):

1. **Specify** — `/speckit.specify` (`/speckit-specify`). Describe the command you want in plain
   language: what it does, and `read-only` vs `read-write` effect. This creates a
   feature branch and `specs/<NNN>-<name>/spec.md`. Optionally run `/speckit.clarify`
   (`/speckit-clarify`) to resolve open questions before planning.
2. **Plan** — `/speckit.plan` (`/speckit-plan`). Generates the design artifacts and runs the
   Constitution Check gate, which enforces the single self-contained `spectra/` extension, a new
   command file under `spectra/commands/` registered in `spectra/extension.yml`, agent-agnostic
   `$ARGUMENTS` commands, and the `speckit.spectra.<command>` namespace.
3. **Tasks** — `/speckit.tasks` (`/speckit-tasks`). Produces the dependency-ordered `tasks.md`.
4. **Implement** — `/speckit.implement` (`/speckit-implement`). Executes the tasks: it adds the
   command file under `spectra/commands/`, registers it in `spectra/extension.yml`, bumps the
   extension `version` with a matching `spectra/CHANGELOG.md` entry, rebuilds `docs/packages/spectra.zip`
   (a single top-level `spectra/` folder), updates the `spectra` entry's `version` and command count in
   `catalog.json`, updates `docs/index.html`, and — if the command introduces a new agent — adds a row
   to the Agents table in [README.md](README.md).
5. **Test locally.** Install your working copy with `--dev` and exercise it end to end — see
   [Test the extension locally](#test-the-extension-locally). Iterate by re-running `/speckit.implement`
   or editing the generated files directly.
6. **Publish.** Commit the updated `spectra/` folder, the updated `catalog.json`, **and** `docs/` (plus
   the `specs/` artifacts), then push to `main`. The catalog and package are live immediately over their
   `raw.githubusercontent.com` links — no Pages build to wait on.

The [Anatomy of an extension](#anatomy-of-an-extension) section above documents the structure the
workflow produces — read it so you can review and refine the generated output, not so you can build
the files by hand.

## Test the extension locally

You don't need to publish to try the extension — install it straight from your working copy with
`--dev`. (The raw `--from` URL only works after you commit and push `catalog.json` and `docs/`; use
`--dev` before that.)

1. **Spin up a throwaway Spec Kit project:**
   ```bash
   specify init /tmp/spectra-test --integration claude
   cd /tmp/spectra-test
   ```
2. **Install your working copy** — point `--dev` at the `spectra/` extension folder (the one containing
   `extension.yml`) and run it from inside the test project:
   ```bash
   specify extension add --dev /path/to/repo/spectra
   ```
   You should see `✓ Extension installed successfully!` listing all provided commands.
3. **Verify registration:**
   ```bash
   specify extension list        # spectra → Status: Enabled
   specify extension info spectra   # details + provided commands
   ```
4. **Run it in your agent.** Start your agent in the test project and invoke a command. On Claude,
   commands install as skills, so the trigger is `/speckit-spectra-<command>` (e.g. `/speckit-spectra-adr`) —
   note the dashes, not dots. `specify extension info spectra` shows the exact triggers.
5. **Iterate.** After editing files in the `spectra/` folder, reinstall and restart your agent so it
   reloads the changes:
   ```bash
   specify extension add --dev /path/to/repo/spectra --force
   ```
   Uninstall with `specify extension remove spectra`.

## Publish the catalog and package

The extension is distributed from the `xavient/spectra` repo itself, fetched over direct
`raw.githubusercontent.com` links. The repo is **public**, so clients fetch the catalog and download
packages with **no authentication** — the raw URLs resolve anonymously. There is no catalog server;
only the raw links. (The `spectra` CLI is the other channel, published as a GitHub Release; see
[Release the CLI](#release-the-cli-spectra-cli).)

> Clients reach the catalog at `https://raw.githubusercontent.com/xavient/spectra/main/catalog.json`
> and the package at `https://raw.githubusercontent.com/xavient/spectra/main/docs/packages/spectra.zip`
> — **raw links, not Pages**. GitHub Pages *is* enabled (serving `main` `/docs` at
> <https://xavient.github.io/spectra/>), but it publishes the landing page only; nothing in the install
> path depends on it. If the repo is ever renamed or moved, update those URLs (and the links in this
> file and the README) together.

### What ships

There is **no build script** — the catalog and package are maintained by hand and committed:

- `catalog.json` (repo root) — **the** catalog Spec Kit fetches and the single source of truth. The
  `spectra` entry carries the full metadata (name, description, version, tags, author, license, …) plus
  the `catalog_url` and the `download_url` pointing at the raw link above.
- `docs/packages/spectra.zip` — the one package (a single top-level `spectra/` folder, the layout
  Spec Kit expects). Rebuilt whenever the extension changes or is released (see the
  [Spec Kit workflow](#add-a-new-command-use-the-spec-kit-workflow)).
- `docs/index.html` — the landing page that walks users through adding the catalog, then installing
  the extension by name.
- `assets/TELUS_Digital_logo.png` — the one logo, used by the README and the landing page.

The `catalog_url` and every `download_url` in `catalog.json`, and the literal URLs in this file and
the README, must all use the `raw.githubusercontent.com/xavient/spectra/main/...` form.

### Test, then publish

1. **Test** the built extension locally with `--dev` (see [above](#test-the-extension-locally)) — the
   raw `--from` URLs are not live until you push.
2. **Commit `catalog.json` and `docs/`** (plus any extension changes) and push to `main`.
3. The catalog and packages are live immediately at their raw URLs.

Nothing is reachable until you push — build and test freely first.

### How users install

The landing page shows the flow. They register the catalog once per project — this marks it
install-allowed, so installs resolve by name with no untrusted-source prompt (and no authentication,
since the catalog is public):

```bash
specify extension catalog add https://raw.githubusercontent.com/xavient/spectra/main/catalog.json \
  --name spectra --install-allowed
```

Then they install the extension by name and restart their agent:

```bash
specify extension add spectra
```

A one-off or offline install can still go straight from a zip with
`specify extension add spectra --from https://raw.githubusercontent.com/xavient/spectra/main/docs/packages/spectra.zip` —
that path shows the untrusted-source prompt (*"Continue with installation? [y/N]"*), which they answer `y`.

**Shipping updates.** Because users install from a registered catalog, `specify extension update spectra`
works against it. To release an update: bump `version` in `spectra/extension.yml`, add a
`spectra/CHANGELOG.md` entry, rebuild `docs/packages/spectra.zip`, bump the entry's `version` in
`catalog.json`, and commit. Users run `specify extension update spectra` (or re-install with
`--force`) to pull the new version.

## Release the CLI (`spectra-cli`)

The catalog and packages are one channel (raw links, above). The **CLI** is a *separate* channel:
the `spectra_cli/` package, installed by consumers as a [`uv`](https://docs.astral.sh/uv/) tool
straight from this repo's git URL.

```bash
uv tool install spectra-cli --from git+https://github.com/xavient/spectra
```

There is **no build artifact and no release asset** — uv builds the wheel from source at install time.
A GitHub Release is still published for every version, because that Release object is what
`spectra --version` / `spectra --update` and the landing page's version pill read via
`/releases/latest`.

### Tags and Releases belong to the CLI

Git tags and GitHub Releases on this repo mean **the CLI, and only the CLI**. The extension channel
has nothing to tag — merging to `main` *is* its release, since clients fetch `catalog.json` and the
zip from `main` over raw links.

Keeping tags single-purpose is what makes `/releases/latest` a reliable answer to *"what is the newest
`spectra` command"*. If the extension also cut releases, the CLI's update check would sometimes
resolve to an extension release and try to install it as a version of itself.

So that a reader can never mistake one for the other:

- name Releases **"Spectra CLI X.Y.Z"**, never "Spectra X.Y.Z" — `release.yml` does this automatically;
- tag with **bare semver** (`3.0.0`), not `vX.Y.Z`. The legacy `v1.0.0`…`v2.0.0` tags are the retired
  `spectra-setup.py` installer channel; the release workflow's tag filter deliberately does not match
  them, so they can never trigger a CLI release.

### VERSION is the single source of truth

[`VERSION`](VERSION) at the repo root holds the CLI version. `pyproject.toml` reads it
(`[tool.setuptools.dynamic] version = { file = "VERSION" }`) and the tool reports it at runtime via
`importlib.metadata`, so the committed version, the git tag, and the installed version cannot drift.
`release.yml` **fails the release** if the pushed tag and `VERSION` disagree.

### When to cut a release

Cut one **whenever the `spectra_cli/` package changes** in a way consumers should pick up (new
prompts, changed steps, a fixed flow). Bump per SemVer:

- **patch** (`3.0.1`) — bug fix, wording, no behavior change to the flow.
- **minor** (`3.1.0`) — new optional step, flag, or capability, backward-compatible.
- **major** (`4.0.0`) — the install flow, the command surface, or the prerequisites change in a
  breaking way.

**Adding or changing an agent is not a CLI release.** The command reads `catalog.json` at run time and
installs whatever it advertises, so a new extension reaches every existing install with no CLI change
at all. Bump the extension, not this. See [Publish the catalog and package](#publish-the-catalog-and-package).

### How to cut a release

1. **Bump `VERSION` in a PR** and land it on `main`, together with the code change it describes.
2. **Tag the merge commit and push the tag:**
   ```bash
   git checkout main && git pull
   git tag 3.0.0 && git push origin 3.0.0
   ```
3. **`release.yml` does the rest** — it verifies the tag matches `VERSION`, then publishes
   "Spectra CLI 3.0.0" with auto-generated notes, explicitly marked **Latest**. Watch it with
   `gh run watch`.

   > **Never publish or re-publish an old release without re-checking `/releases/latest`.** Left to
   > GitHub's default, "Latest" is resolved by `created_at` with `published_at` as the tie-breaker, so
   > touching an older release can steal the slot and point `spectra --update` and the landing page's
   > version pill at an ancient version. `make_latest: true` in the workflow protects new releases;
   > for anything done by hand, verify afterwards:
   > ```bash
   > gh api repos/xavient/spectra/releases/latest --jq '{tag: .tag_name, name: .name}'
   > ```
   > and fix with `gh release edit <newest-tag> -R xavient/spectra --latest`.
4. **Smoke-test what a consumer gets**, from any directory:
   ```bash
   uv tool install spectra-cli --from git+https://github.com/xavient/spectra --force
   spectra --version
   ```
   For a full clean-room run (no uv, no `specify`, no `.specify/`), use [`test/run.sh`](test/run.sh).

### How consumers get it

```bash
uv tool install spectra-cli --from git+https://github.com/xavient/spectra
spectra
```

Unpinned, so new installs track `main`. Keep `main` releasable. A specific version is pinned by
appending the tag (`--from git+https://github.com/xavient/spectra@3.0.0`), which is exactly what
`spectra --update` does. Keep the README's [Installation](README.md#installation) section and the
landing page in sync if the install command ever changes.

> **Heads-up:** the `download_url`s inside `catalog.json` point at `raw.githubusercontent.com/.../main/...`,
> **not** at release assets — extension packages are distributed over raw links and are unaffected by
> CLI releases. The two channels version independently.

## Conventions

- **Versioning.** [Semantic Versioning](https://semver.org/), **per channel**. The extension's version
  lives in `spectra/extension.yml` (mirrored into `catalog.json`) and gets a `spectra/CHANGELOG.md`
  entry; the CLI's lives in `VERSION` and is released by tag. The two are independent — never bump one
  just because the other moved.
- **Command namespace.** Always `speckit.spectra.<command>` — a fixed `spectra` segment followed by
  a clear, descriptive command name (e.g. `adr`, `domain-analyzer`, `create-pr`).
- **One source file, all agents.** Generic format plus `$ARGUMENTS`. Never hard-code an agent's syntax.
- **Author / copyright.** `TELUS Digital`, Apache-2.0 licensed. Keep `LICENSE` and `NOTICE` shipping
  with the extension — attribution is a license condition, not a courtesy.
- **The catalog and `docs/` are published by hand — keep them in sync.** `catalog.json` (repo root) is
  the single catalog (no second copy elsewhere) and `assets/TELUS_Digital_logo.png` is the one logo. When
  you add or release an extension, update the zip, catalog entry, and landing page together, then commit.

## Compatibility

Spec Kit does not review or support extension code — we own it. Pin a realistic
`requires.speckit_version` in each `extension.yml` based on the version you actually tested against,
and re-test extensions when you upgrade Spec Kit.
