# Spectra — notes for coding agents

Read `.specify/memory/constitution.md` first — it governs how Spectra is built, and the
Constitution Check gate in every plan is binding.

Two independently-versioned things live in this repo. Know which one you are changing:

- **`spectra/`** — the Spec Kit extension (the agents). Markdown + YAML, no code. Versioned in
  `spectra/extension.yml`, mirrored into `catalog.json`, shipped from `main` over raw URLs. Never
  tagged. Adding or changing a command means updating `extension.yml`, `spectra/CHANGELOG.md`,
  `agents-list.json`, `catalog.json`, `docs/packages/spectra.zip`, and `docs/index.html` in the same
  change (Principle V).
- **`spectra_cli/`** — the `spectra` command that manages Spectra in a project. Python, stdlib
  only, installed as a `uv` tool. Versioned in the root `VERSION` file and released by pushing a bare
  semver git tag. Git tags and GitHub Releases belong to this channel exclusively (Principle VI).

Never bump one channel because the other moved.

## The roster is the source of truth

`agents-list.json` at the repository root declares which agents Spectra offers. Every **structured**
listing of agents is generated from it and must not be hand-edited:

| Generated region | File |
| --- | --- |
| `readme-agents-table` | `README.md` |
| `agents-list-speckit-core` | `AGENTS_LIST.md` |
| `agents-list-roadmap` | `AGENTS_LIST.md` |
| `spectra-readme-commands` | `spectra/README.md` |

```bash
python tools/generate_agent_docs.py            # rewrite the generated regions
python tools/generate_agent_docs.py --check    # what CI runs
python tools/build_package.py                  # rebuild docs/packages/spectra.zip
```

The division is by kind of content, not by file: **if it is a table or a list, it is generated; if it
is a paragraph, it is written.** Per-agent prose stays hand-authored, anchored by
`<!-- SPECTRA:AGENT id=… -->` so it is keyed to the agent's stable id rather than its title — a title
can be reworded without breaking anything. `--check` fails if a shipped agent has no prose block, if a
prose block exists for an agent the roster does not ship, if a hand-written heading has drifted from a
canonical title, or if the roster and the manifest disagree about the shipped set.

## The command surface

A top-level verb acts on the agents in the current project; only `spectra cli …` acts on the tool.
`--version`, `--update`, and `--uninstall` were removed in CLI 5.0.0.

## Tests

Standard-library `unittest`, not pytest — the zero-dependency constraint applies to the whole
repository, not just the shipped wheel.

```bash
python -m unittest discover -s tests
```

Contributor workflow, packaging, and release steps: `CONTRIBUTING.md`.
Per-feature design artifacts live under `specs/<NNN>-<name>/`; note that the older ones predate the
single-extension consolidation and describe a build script that no longer exists.

<!-- The block below is owned by the agent-context extension and is REPLACED WHOLESALE whenever
     `speckit.agent-context.update` runs — its script writes a fixed template rather than preserving
     what is inside the markers. Keep hand-written guidance above this line, never inside it. -->
<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan
at specs/006-agent-roster-cli/plan.md
<!-- SPECKIT END -->
