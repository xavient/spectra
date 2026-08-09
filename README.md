<div align="center">

<img src="assets/TELUS_Digital_logo.png" alt="TELUS Digital" width="320">

# SPECTRA

**Agentic software engineering across the entire SDLC**

<sub>A curated catalog of [Spec Kit](https://github.com/github/spec-kit) extensions that enable full agentic development across the entire software development lifecycle.</sub>

</div>

---

Spectra **builds on top of** [![Spec Kit — GitHub stars](https://img.shields.io/github/stars/github/spec-kit?style=social&label=Spec%20Kit)](https://github.com/github/spec-kit) — it does not replace it.
Spec Kit gives you spec-driven development (`specify`, `plan`, `tasks`, `implement`); Spectra adds
focused, production-ready agents for the work that surrounds the code: architecture decisions, design,
quality gates, documentation, delivery, and more. These capabilities ship together as a single
self-contained Spec Kit extension, `spectra`, whose commands all live under the `speckit.spectra.*`
namespace. You install Spec Kit first, then add the Spectra extension onto any Spec Kit project.

Spectra is built and maintained by TELUS Digital.

> **Who this README is for — developers.** It covers two paths:
>
> - **Consumers** — engineers and teams who want to install and use the Spectra extension in their Spec
>   Kit projects. That's everything below.
> - **Contributors** — engineers adding or changing a command. Start at
>   [CONTRIBUTING.md](CONTRIBUTING.md); this README only points you there.

> 📚 **New to spec-driven development and Spec Kit?** We've built a course handbook for you:
> **[Spec-Driven Development — Course Handbook](https://expert-adventure-77nryn7.pages.github.io/e-learning/)**.

## AI-Assisted VS AI-Native
Vibe coding and plan mode — Claude Code, Cursor, and the rest — supercharge a single phase. But each phase runs in its own session: the agent rebuilds its understanding from scratch every time, and the spec, design, tests, and code drift apart at every hand-off. That's AI-assisted — a faster typist. True AI-native engineering keeps one context intact across the whole lifecycle, so every phase builds on the last instead of starting cold.

![AI-Native Engineering](assets/AI-Native.png)

SPECTRA makes spec-driven development truly AI-native. Every phase reads and writes one shared, durable context — the spec, plan, design, tasks, and code stay in lockstep through a tight, repeating loop, with a human owning the gate at each step. Because that context is shared, every agent stays in full compatibility with the standards and guardrails set for the system — nothing drifts out of policy from one phase to the next. Continuity is the design goal; speed and quality follow from it.

## Spec-Driven Development

Spec-Driven Development flips the script on traditional software development. For decades, code has
been king — specifications were just scaffolding we built and discarded once the "real work" of
coding began. Spec-Driven Development changes this: specifications become executable, directly
generating working implementations rather than just guiding them.

Spec Kit runs that loop in four core phases:

```text
spec  →  plan  →  tasks  →  implement
```

![Spec-Driven Development](assets/SDD.png)

Spec Kit ships the **skeleton** — the core spec-driven loop above. **Spectra builds on top of it**,
adding specialized agents across every phase of the SDLC: foundation and governance, requirements,
architecture, planning, implementation, testing, and delivery.

## AI-DLC

**AI-DLC** is AWS's [AI-Driven Development Life Cycle](https://aws.amazon.com/blogs/devops/ai-driven-development-life-cycle/)
— introduced to fix a structural limit of the traditional SDLC: it's built around **humans**, with AI
bolted on at the edges. AI-DLC inverts that and puts **AI at the centre** — AI drafts the plan and does
the heavy lifting, while humans review and approve at each gate. It collapses the classic SDLC phases
into three: **Inception → Construction → Operation**.

![SDLC to AI-DLC mapping](assets/SDLC-to-AIDLC.png)

That is exactly the Spectra model. Spectra already runs this way on a conventional SDLC, and it's
**ready for AI-DLC out of the box**: its loop, shared context, and human gates map straight onto
AI-DLC's three phases — so adopting Spectra is itself how a team makes the shift, without giving up
the discipline that keeps quality high. Inside every phase the same pattern repeats — **the team
validates at a gate, AI drafts and builds, the team reviews** — and the same agents from the
[roster below](#agents) slot straight into each phase:

## Agents

Every Spectra roster is built from two kinds of agents — a required **core** that runs the SDLC
end-to-end, plus optional **add-ons** you switch on as the domain demands. The roster spans the SDLC
phases below, each also mapped onto the [**AI-DLC**](#ai-dlc) phases (Inception → Construction → Operation).

**Status:** ✅ available today · 🚧 under development.

| Agent | SDLC phase | AI-DLC phase | Type | Status |
| ----- | ---------- | ------------ | ---- | ------ |
| Guardrails | Foundation | Inception | Core | ✅ available |
| Domain Analyzer | Foundation | Inception | Add-on | ✅ available |
| FDA 21 CFR Part 11 & IEC 62304 | Foundation | Inception | Add-on | 🚧 under dev |
| ISO 27001 / 27701 | Foundation | Inception | Add-on | 🚧 under dev |
| Requirements Analyst | Requirements & Discovery | Inception | Core | ✅ available |
| BRD Generator | Requirements & Discovery | Inception | Add-on | ✅ available |
| Clarifier | Requirements & Discovery | Inception | Add-on | ✅ available |
| Requirements Quality | Requirements & Discovery | Inception | Add-on | ✅ available |
| GDPR Compliance | Requirements & Discovery | Inception | Add-on | 🚧 under dev |
| Canadian Privacy — PIPEDA / PHIPA / Law 25 | Requirements & Discovery | Inception | Add-on | 🚧 under dev |
| EU AI Act & Responsible-AI Governance | Requirements & Discovery | Inception | Add-on | 🚧 under dev |
| Legal-Obligation Extraction | Requirements & Discovery | Inception | Add-on | 🚧 under dev |
| Architecture Planner | Architecture & Design | Construction | Core | ✅ available |
| Architecture Decision Records (ADR) | Architecture & Design | Construction | Add-on | ✅ available |
| Architecture Reviewer | Architecture & Design | Construction | Add-on | 🚧 under dev |
| HIPAA Compliance | Architecture & Design | Construction | Add-on | 🚧 under dev |
| PCI-DSS | Architecture & Design | Construction | Add-on | 🚧 under dev |
| Threat Modeling | Architecture & Design | Construction | Add-on | 🚧 under dev |
| Performance & Scalability | Architecture & Design | Construction | Add-on | 🚧 under dev |
| Data Governance & Privacy Engineering | Architecture & Design | Construction | Add-on | 🚧 under dev |
| API Design & Contract | Architecture & Design | Construction | Add-on | 🚧 under dev |
| Task Planner | Planning | Construction | Core | ✅ available |
| Consistency | Planning | Construction | Add-on | ✅ available |
| Implementation | Implementation | Construction | Core | ✅ available |
| Dependency & Supply-Chain | Implementation | Construction | Add-on | 🚧 under dev |
| Database & Data-Layer | Implementation | Construction | Add-on | 🚧 under dev |
| Documentation Quality | Implementation | Construction | Add-on | 🚧 under dev |
| Technical-Debt & Maintainability | Implementation | Construction | Add-on | 🚧 under dev |
| Testing | Testing & Quality | Construction | Core | ✅ available |
| Test Coverage Analyst | Testing & Quality | Construction | Add-on | 🚧 under dev |
| Test Automation Analyst | Testing & Quality | Construction | Add-on | 🚧 under dev |
| Security Analyst | Testing & Quality | Construction | Add-on | 🚧 under dev |
| Accessibility & WCAG Compliance | Testing & Quality | Construction | Add-on | 🚧 under dev |
| Carbon & Green-Software | Testing & Quality | Construction | Add-on | 🚧 under dev |
| Internationalization Readiness | Testing & Quality | Construction | Add-on | 🚧 under dev |
| Responsible-AI & Bias | Testing & Quality | Construction | Add-on | 🚧 under dev |
| GitHub (PR) | Deployment & Operations | Operation | Core | ✅ available |
| Operations Monitor | Deployment & Operations | Operation | Add-on | 🚧 under dev |
| Incident Responder | Deployment & Operations | Operation | Add-on | 🚧 under dev |
| SOC 2 | Deployment & Operations | Operation | Add-on | 🚧 under dev |
| SOX Change-Management | Deployment & Operations | Operation | Add-on | 🚧 under dev |
| Infrastructure-as-Code Analysis | Deployment & Operations | Operation | Add-on | 🚧 under dev |
| Cost & FinOps | Deployment & Operations | Operation | Add-on | 🚧 under dev |
| Observability Readiness | Deployment & Operations | Operation | Add-on | 🚧 under dev |

The agents marked ✅ that aren't shipped by Spectra (Guardrails, Requirements Analyst, Clarifier,
Requirements Quality, Architecture Planner, Task Planner, Consistency, Implementation, Testing) are
Spec Kit's own core commands — Spectra layers on top of them.

Full details for every agent — what it does, its arguments, and how to run it — live in
**[AGENTS_LIST.md](AGENTS_LIST.md)**.

## Installation

Spectra installs **into** a Spec Kit project, and its catalog is **public** — there's no GitHub login
or token involved either way. Pick one path: the **installer** does everything for you, or **manual
setup** walks you through it step by step.

### Spectra Installer

The recommended path — **you don't need to clone this repo, just the installer.** Spectra ships
`spectra-setup.py` as a versioned release asset, and that single file takes care of everything: it
installs the `specify` CLI if it's missing (via [`uv`](https://docs.astral.sh/uv/), at the latest Spec
Kit release), offers to run `specify init` if the current folder isn't a Spec Kit project yet, and
registers the Spectra catalog. It works on macOS, Linux, and Windows.

Head to the **[Spectra releases page](https://github.com/xavient/spectra/releases/)**, grab the latest
release, and follow its download-and-run instructions. When it finishes, **the catalog is already
registered** — skip ahead to [Install and use extensions](#install-and-use-extensions).

### Manual setup

Prefer to wire it up by hand (or the installer didn't work for you)? Because the catalog is public,
there's nothing to authenticate — no GitHub token, no `gh` login. Three steps:

**1. Install the `specify` CLI (Spec Kit).** Spectra installs into a Spec Kit project, so you need Spec
Kit first — follow the [Spec Kit installation guide](https://github.com/github/spec-kit#-get-started)
(it uses [`uv`](https://docs.astral.sh/uv/)), then verify it's on your `PATH`:

```bash
specify --version
```

**2. Initialize a Spec Kit project** (or use an existing one). This creates the `.specify/` directory
and registers Spec Kit's commands for your coding agent:

```bash
specify init               # in a new directory, or `specify init .` in an existing one
```

Run the next step — and every Spectra command — from **inside** that project (a folder containing
`.specify/`). New to spec-driven development? Read the [Spec Kit docs](https://github.github.io/spec-kit/)
first — Spectra assumes you're comfortable with the `specify → plan → tasks → implement` loop.

**3. Add the Spectra catalog.** Point Spec Kit at the public catalog so `search` / `add` / `update`
resolve against it:

```bash
specify extension catalog add \
  https://raw.githubusercontent.com/xavient/spectra/main/catalog.json \
  --name spectra --priority 5 --install-allowed
```

`--install-allowed` is required — catalogs are discovery-only by default, which blocks
`specify extension add` from installing anything in them. This writes the catalog into
`.specify/extension-catalogs.yml`:

```yaml
catalogs:
  - name: "spectra"
    url: "https://raw.githubusercontent.com/xavient/spectra/main/catalog.json"
    priority: 5
    install_allowed: true
```

**Commit `.specify/extension-catalogs.yml`** so everyone who clones the project inherits the catalog —
no per-developer setup. (Prefer not to touch project config? Set `SPECKIT_CATALOG_URL` to the same URL
to use Spectra everywhere.)

## Install and use extensions

Once the catalog is added:

```bash
specify extension search          # find the Spectra extension
specify extension add spectra     # install spectra and register all its commands with your agent
specify extension list            # show what's installed, with status and version
specify extension update spectra  # pull a newer version when we publish one
specify extension remove spectra  # uninstall (configs are backed up by default)
```

Spectra ships as a **single extension** — `specify extension add spectra` registers all of its
commands (`speckit.spectra.adr`, `speckit.spectra.domain-analyzer`, `speckit.spectra.create-pr`,
`speckit.spectra.brd`) at once. After installing, **restart your AI agent** so it picks up the new commands, then run one. On
Claude:

```
/speckit-spectra-adr We should standardize on PostgreSQL for all primary data stores
```

Spec Kit translates each command into your agent's native format at install time, so the extension
supports every agent — but the **trigger you type differs by agent**. Every Spectra command lives
under the unified `speckit.spectra.*` namespace (e.g. `speckit.spectra.adr` in the manifest), and how
you invoke it depends on how your agent registers it:

- **Claude** installs commands as *skills*, invoked with a leading slash and dashes: `/speckit-spectra-adr ...`.
- **Other agents** register it under a slightly different trigger — e.g. kiro-cli keeps the dots:
  `/speckit.spectra.adr ...`.

The examples in this README use Claude's form; adjust the trigger for your agent.

After install, the CLI prints the provided commands, and `specify extension info spectra` (or your
agent's own command/skill list) shows the exact triggers to use.

The extension has its own README with full per-command usage details — see [`spectra/`](spectra/README.md).

## Support and compatibility

- Spectra extensions are built and maintained by TELUS Digital.
- Each extension pins the Spec Kit version it was tested against (`requires.speckit_version`). If you
  upgrade Spec Kit and a command misbehaves, check that field and update the extension.
- Issues and requests: <https://github.com/xavient/spectra/issues>.

## Contributing

Want to add a new command or change an existing one? Everything you need — repository layout,
the `extension.yml` manifest reference, how to write agent-agnostic commands, local testing with
`--dev`, and how to publish the catalog and package — lives in [CONTRIBUTING.md](CONTRIBUTING.md). Use
the [`spectra/`](spectra/) extension as the reference model; new capabilities are added as commands
under it in the `speckit.spectra.*` namespace.

## License

Apache License 2.0 — see [LICENSE](LICENSE). The `spectra` extension carries its own copy of the
license too.

Spectra is free to use, modify, and redistribute, commercially or otherwise. Attribution is
required: if you redistribute Spectra or a derivative work, keep the copyright notice, the `LICENSE`,
and the [`NOTICE`](NOTICE) file, and state which files you changed. See sections 4(b)–4(d) of the
license.
