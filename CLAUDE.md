<!-- SPECKIT START -->
Read `.specify/memory/constitution.md` first — it governs how Spectra is built, and the
Constitution Check gate in every plan is binding.

Two independently-versioned things live in this repo. Know which one you are changing:

- **`spectra/`** — the Spec Kit extension (the agents). Markdown + YAML, no code. Versioned in
  `spectra/extension.yml`, mirrored into `catalog.json`, shipped from `main` over raw URLs. Never
  tagged. Adding or changing a command means updating `extension.yml`, `spectra/CHANGELOG.md`,
  `catalog.json`, `docs/packages/spectra.zip`, and `docs/index.html` in the same change
  (Principle V).
- **`spectra_cli/`** — the `spectra` command that installs Spectra into a project. Python, stdlib
  only, installed as a `uv` tool. Versioned in the root `VERSION` file and released by pushing a bare
  semver git tag. Git tags and GitHub Releases belong to this channel exclusively (Principle VI).

Never bump one channel because the other moved.

Contributor workflow, packaging, and release steps: `CONTRIBUTING.md`.
Per-feature design artifacts live under `specs/<NNN>-<name>/`; note that the older ones predate the
single-extension consolidation and describe a build script that no longer exists.
<!-- SPECKIT END -->
