# Business Requirements Document (BRD): Agent Roster & Project-Scoped CLI Commands

## Document Control

| Field             | Value                                                                                                                                                                                              |
| ----------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| BRD ID            | BRD-004                                                                                                                                                                                            |
| Title             | Agent Roster & Project-Scoped CLI Commands                                                                                                                                                         |
| Author            | Spectra / TELUS Digital                                                                                                                                                                            |
| Status            | Draft                                                                                                                                                                                              |
| Version           | 0.3.0                                                                                                                                                                                              |
| Created           | 2026-08-09                                                                                                                                                                                         |
| Last updated      | 2026-08-09                                                                                                                                                                                         |
| Related documents | `.specify/memory/constitution.md` (Principles V and VI), `CONTRIBUTING.md`, `AGENTS_LIST.md`, `README.md` (Agents table), `catalog.json`, `spectra/extension.yml`, `docs/index.html`, `spectra_cli/` |

## 1. Executive Summary

Spectra ships **two** things a user can hold: the `spectra` command (the tool) and the `spectra`
extension (the agents). Today the CLI can only manage the tool — a user standing in their own project
has no way to ask *"what agents exist?"*, *"do I have them here?"*, or *"are mine current?"* without
leaving the terminal for GitHub.

This work introduces **`agents-list.json`** at the repository root: a public, machine-readable roster
that becomes the **single source of truth** for what Spectra offers. A **generator** run by maintainers
rewrites the *structured* agent listings — the Agents table in `README.md`, and the roadmap and Spec
Kit core sections of `AGENTS_LIST.md` — from that file, so the roster is authored once and published
everywhere.

The division is by kind of content, not by file: **if it is a table or a list, it is generated; if it
is a paragraph, it is written.** Roughly forty of the forty-plus roster entries are pure classification
— title, phase, type, status — and those are exactly the entries that rot silently today. The handful
of shipped agents that carry real explanatory prose (arguments, when to use them, worked examples) keep
that prose hand-authored, with automation asserting only that a prose block exists for every shipped
agent and no others.

The CLI is reorganized around the same distinction: **top-level commands act on the agents in your
project** (`check`, `version`, `update`, `uninstall`, `agent-list`), while **tool self-management moves
under `spectra cli`** (`cli version`, `cli update`, `cli uninstall`). The existing `--version`,
`--update`, and `--uninstall` flags are removed.

## 2. Business Context & Problem Statement

Four gaps. The first three are felt by developers using Spectra; the fourth is felt by the maintainers
who publish it.

**They cannot see what Spectra offers.** The roster of agents lives in prose — `AGENTS_LIST.md` and a
table in `README.md` — which is fine for a human browsing GitHub and useless to anyone at a terminal or
to any tool that wants to consume it. `spectra/extension.yml` *is* machine-readable, but it carries
namespaced command names (`speckit.spectra.domain-analyzer`) rather than the human titles the
documentation uses ("Domain Analyzer"), and it lists only what ships today with no phase, type, or
status.

**They cannot tell whether Spectra is installed here.** The only way to check is
`specify extension list` — a Spec Kit command, not a Spectra one — or looking for
`.specify/extensions/spectra/` by hand. A developer who has cloned a teammate's project has no direct
way to ask.

**They cannot tell whether their agents are stale.** The extension version is recorded in
`.specify/extensions/spectra/extension.yml`; the published version is in the same file on `main`.
Comparing them is a manual, two-tab exercise, so in practice nobody does it and teams silently run old
agents. This directly undercuts the value of the independent catalog channel: we can ship a new agent
any day, but users have no signal that we did.

**The roster is maintained three times and already disagrees with itself.** Every new agent must be
hand-written into `AGENTS_LIST.md`, the README table, and the extension manifest. That has already
produced drift: the PR agent is titled **`github` — GitHub** in `AGENTS_LIST.md` and **GitHub (PR)** in
the README table, while its command is `speckit.spectra.create-pr`. Three names for one agent, in two
files, today — with four agents shipped and forty-plus on the roadmap. Adding a machine-readable roster
*without* making it the source would make this worse, not better: a fourth place to forget.

Underneath the CLI gaps is a **naming collision the current command surface makes worse**.
`spectra --version` reports the *tool's* version, which is the number a user is least likely to care
about — they want to know about their *agents*. The same is true of `--update` and `--uninstall`. The
two channels the constitution deliberately keeps independent (Principle VI) compete for the same three
words at the command line.

## 3. Business Objectives & Goals

- **G1 — One source of truth for the roster.** `agents-list.json` declares what agents Spectra offers.
  Every other agent listing is derived from it, never authored alongside it.
- **G2 — Author once, publish everywhere.** A maintainer adding an agent edits the roster and runs one
  command; every structured listing of agents updates itself.
- **G2a — Automate the mechanical, keep the editorial.** Classification data is generated because it is
  repetitive and rots silently; explanatory prose stays hand-written because it is judgement, not data.
  Automation guarantees the prose *exists*, never what it says.
- **G3 — Answer "what, whether, and how current" from the terminal.** A developer can discover the
  roster, confirm whether Spectra is installed in the current project, and learn whether their agents
  are current — without opening a browser.
- **G4 — Make the noun obvious in every command.** Top-level commands act on the agents in the current
  project; tool self-management is namespaced under `cli`. A user should never have to wonder which of
  two things `spectra version` means.
- **G5 — Keep the channels independent in practice, not just in principle.** A newly added agent must
  reach every existing installation with no CLI release.
- **G6 — Close the update loop.** A user told their agents are out of date must be able to fix it with
  the command they were just shown, in one step.
- **G7 — Present Spectra consistently.** The extension's description matches the positioning used on the
  landing page and in the README, and each agent has exactly one title everywhere.

## 4. Stakeholders & Users

| Stakeholder / user                     | Role in this product | What they need from it                                                                                              |
| -------------------------------------- | -------------------- | --------------------------------------------------------------------------------------------------------------------- |
| Developer using Spectra in a project    | primary              | To see what agents exist, confirm they're installed here, know if they're stale, and update or remove them.               |
| Team lead / onboarding developer        | primary              | To verify a cloned project has Spectra set up correctly, without knowing Spec Kit's own commands.                         |
| TELUS Digital maintainer (agent author) | primary              | One obvious place to register a new agent, and one command that propagates it to every document.                          |
| TELUS Digital maintainer (CLI author)   | reviewer             | A command surface that stays small and predictable as agents are added.                                                   |
| Reader of the GitHub repo / landing page | downstream           | Agent documentation that is accurate and internally consistent, because it is generated rather than retyped.              |
| Downstream tools / integrations         | downstream           | A stable, public, machine-readable roster to consume, rather than scraping Markdown.                                      |

## 5. Scope

### 5.1 In Scope

- **`agents-list.json`** at the repository root — a public, anonymously fetchable roster that is the
  single source of truth for the agents Spectra offers, covering shipped Spectra agents, the Spec Kit
  core agents Spectra builds on, and planned agents, each with a human-readable title, a status, and a
  one-line description.
- A **generator** that maintainers run to rewrite the structured agent listings from `agents-list.json`:
  the Agents table in `README.md`, and the roadmap and Spec Kit core sections of `AGENTS_LIST.md`.
- **Automated verification** that the generated listings match the roster, so a hand-edit cannot
  silently reintroduce drift.
- **Automated verification that a hand-written prose block exists for every shipped agent** and for no
  agent that is not shipped — the safety net that lets the prose stay hand-authored.
- A CLI command that **prints the roster** to the console.
- A CLI command that **reports whether the Spectra extension is installed** in the current project, and
  offers to install it when it is not.
- A CLI command that **compares the installed extension version against the published one**.
- A CLI command that **updates the installed extension**.
- A CLI command that **removes the extension** from the current project.
- **Relocating tool self-management** under a `cli` command group, and **removing** the `--version`,
  `--update`, and `--uninstall` flags.
- Changing the **extension's description** to the agreed positioning line, everywhere it is published.
- **Amending the constitution** — Principle V currently states there is no build script and that the
  README Agents table is updated by hand. Both become untrue with this change.
- Updating `CONTRIBUTING.md` so the "add an agent" procedure names the roster and the generator.

### 5.2 Out of Scope

- **Authoring or changing any agent.** This work makes the roster visible and the extension manageable;
  it adds no new `speckit.spectra.*` command.
- **Installing individual agents.** Spectra ships as one self-contained extension (constitution
  Principle II); the roster is informational, not an à-la-carte install menu.
- **Managing non-Spectra extensions.** Spec Kit owns `specify extension` for the general case; these
  commands are Spectra-scoped and delegate to Spec Kit where a Spec Kit operation exists.
- **Generating explanatory prose.** The per-agent detail for shipped agents — arguments, when to use
  them, worked examples — stays hand-authored, as do the narrative sections of `README.md` (AI-Native,
  Spec-Driven Development, AI-DLC, Installation). The roster carries a one-line description per agent
  and nothing longer; it is not a content management system.
- **Replacing `spectra/extension.yml`.** It remains the manifest Spec Kit validates and installs from;
  the roster describes agents, the manifest declares installable commands.
- **A registry of third-party or community agents.** The roster describes what TELUS Digital publishes
  plus the Spec Kit agents Spectra builds on.
- **Automatic background update checks for agents.** Version comparison happens when the user asks.

## 6. User Journeys *(feeds the spec's prioritized user stories)*

### Journey 1 — Discover what agents Spectra offers (Priority: P1)

- **Actor:** A developer evaluating or already using Spectra.
- **Trigger:** They want to know what Spectra can do, from the terminal.
- **Outcome / value:** A readable roster of agents with their human titles, what each does, whether it
  is available today, and who provides it — without opening GitHub.
- **Flow:**
  1. The developer runs `spectra agent-list`.
  2. The CLI fetches the published roster.
  3. It prints the agents, grouped so a long list stays readable, each with its title, status, and the
     command that invokes it where one exists.
- **Acceptance:**
  - **Given** an internet connection, **When** the developer runs `spectra agent-list` from any
    directory, **Then** the published roster is printed with human-readable titles, and the command
    succeeds whether or not the current folder is a Spec Kit project.
  - **Given** the roster contains available and planned agents, **When** the list is printed, **Then**
    each agent's status is unambiguous, and no planned agent is presented as runnable.
  - **Given** a newly published agent added to the roster, **When** a developer with an
    already-installed CLI runs `spectra agent-list`, **Then** the new agent appears without the
    developer updating the CLI.
  - **Given** no network access, **When** the developer runs `spectra agent-list`, **Then** the CLI
    explains that the roster could not be fetched rather than printing an empty or stale list silently.

### Journey 2 — Confirm Spectra is installed in this project (Priority: P1)

- **Actor:** A developer who has just cloned a project, or is unsure of its state.
- **Trigger:** They want to know whether Spectra's agents are available here before trying to use one.
- **Outcome / value:** A definitive yes/no about the current project, and a way forward when the answer
  is no.
- **Flow:**
  1. The developer runs `spectra check` in the project folder.
  2. The CLI looks for the installed Spectra extension in the project.
  3. If present, it reports success. If absent, it reports that Spectra is not installed and offers to
     install it.
- **Acceptance:**
  - **Given** a project with Spectra installed, **When** the developer runs `spectra check`, **Then**
    the CLI reports success and exits with a success status.
  - **Given** a project without Spectra installed, **When** the developer runs `spectra check`, **Then**
    the CLI reports that Spectra is not installed, offers to install it, and exits with a failure status
    if the developer declines.
  - **Given** a project without Spectra installed, **When** the developer accepts the offer, **Then** the
    existing install flow runs and, on success, the project ends up with Spectra installed.
  - **Given** a folder that is not a Spec Kit project at all, **When** the developer runs
    `spectra check`, **Then** the message distinguishes that case from "Spec Kit project without
    Spectra".

### Journey 3 — Find out whether my agents are current, and update them (Priority: P1)

- **Actor:** A developer using Spectra in a project.
- **Trigger:** They want to know whether they are running the latest agents.
- **Outcome / value:** A clear verdict, and — when behind — a single named command that fixes it.
- **Flow:**
  1. The developer runs `spectra version` in the project folder.
  2. The CLI reads the version of the extension installed in the project.
  3. It fetches the published version.
  4. If they match, it reports that the agents are up to date. If not, it reports both versions and tells
     the developer to run `spectra update`.
  5. The developer runs `spectra update`, and the extension is updated in place.
- **Acceptance:**
  - **Given** an installed extension whose version matches the published one, **When** the developer runs
    `spectra version`, **Then** the CLI reports that the agents are up to date.
  - **Given** an installed extension older than the published one, **When** the developer runs
    `spectra version`, **Then** the CLI reports both versions and names `spectra update` as the fix.
  - **Given** an out-of-date extension, **When** the developer runs `spectra update`, **Then** the
    extension is updated via Spec Kit and a subsequent `spectra version` reports the agents as up to
    date.
  - **Given** Spectra is not installed in the current project, **When** the developer runs
    `spectra version` or `spectra update`, **Then** the CLI says Spectra is not installed rather than
    reporting a misleading version or failing obscurely.

### Journey 4 — Manage the tool itself, unambiguously (Priority: P2)

- **Actor:** Any user of the `spectra` command.
- **Trigger:** They want to check, update, or remove the CLI itself rather than the agents.
- **Outcome / value:** Tool operations that read unambiguously and cannot be confused with agent
  operations.
- **Flow:**
  1. The user runs `spectra cli version`, `spectra cli update`, or `spectra cli uninstall`.
  2. The CLI performs the corresponding operation on itself.
- **Acceptance:**
  - **Given** an installed CLI, **When** the user runs `spectra cli version`, **Then** the CLI's own
    version is reported, noting whether a newer release exists.
  - **Given** a newer CLI release exists, **When** the user runs `spectra cli update`, **Then** the CLI
    updates itself and reports the new version.
  - **Given** an installed CLI, **When** the user runs `spectra cli uninstall` and confirms, **Then** the
    `spectra` command is removed from the machine and any extension installed in a project is left
    untouched.
  - **Given** a user who runs the removed `--version`, `--update`, or `--uninstall` flag, **When** the
    command executes, **Then** it fails with a message naming the replacement command rather than a bare
    "unrecognized argument".
  - **Given** the help screen, **When** a user reads it, **Then** it is evident which commands act on the
    project's agents and which act on the tool.

### Journey 5 — Remove Spectra's agents from a project (Priority: P2)

- **Actor:** A developer who no longer wants Spectra's agents in a given project.
- **Trigger:** They want to clean the project without removing the tool from their machine.
- **Outcome / value:** The project is left without Spectra's commands; the CLI remains installed.
- **Flow:**
  1. The developer runs `spectra uninstall` in the project folder.
  2. The CLI confirms Spectra is actually installed there.
  3. If it is, the extension is removed via Spec Kit. If it is not, the CLI says so and does nothing.
- **Acceptance:**
  - **Given** a project with Spectra installed, **When** the developer runs `spectra uninstall`, **Then**
    the extension is removed from that project and the `spectra` command remains installed on the
    machine.
  - **Given** a project without Spectra installed, **When** the developer runs `spectra uninstall`,
    **Then** the CLI reports that Spectra is not installed and makes no changes.

### Journey 6 — Add an agent once and have it appear everywhere (Priority: P1)

- **Actor:** A TELUS Digital maintainer adding an agent.
- **Trigger:** A new `speckit.spectra.*` command is ready to ship.
- **Outcome / value:** The agent is classified in exactly one place, every structured listing updates
  itself, and the maintainer is left to write only the part that needs judgement.
- **Flow:**
  1. The maintainer adds the agent to `agents-list.json` and registers its command in the extension
     manifest, as part of the same change that adds the command file.
  2. They run the generator.
  3. The README Agents table and the generated sections of `AGENTS_LIST.md` are rewritten from the
     roster.
  4. Verification tells them a prose block is still missing for the new shipped agent; they write it.
  5. They commit the roster, the regenerated listings, the new prose, and the rest of the change
     together.
- **Acceptance:**
  - **Given** a new agent added to `agents-list.json`, **When** the maintainer runs the generator,
    **Then** every structured listing includes the agent, with the same title in each.
  - **Given** a new *shipped* agent added to the roster with no prose block written, **When** the
    automated verification runs, **Then** it fails and names the agent whose prose is missing.
  - **Given** a repository where a generated region has been edited by hand, **When** the automated
    verification runs, **Then** it fails and identifies the file that no longer matches the roster.
  - **Given** hand-authored prose sitting outside the generated regions, **When** the generator runs,
    **Then** that prose is left byte-identical.
  - **Given** the generator is run twice with no roster change, **When** the outputs are compared,
    **Then** they are byte-identical.
  - **Given** the merged change, **When** any user with an already-installed CLI runs
    `spectra agent-list`, **Then** the new agent is listed with no CLI update required.
  - **Given** the merged change, **When** a user with the previous extension version runs
    `spectra version`, **Then** they are told an update is available and pointed at `spectra update`.

### Edge Cases

- The roster cannot be fetched (offline, proxy, rate limit) for `agent-list` or `version`.
- The current folder is not a Spec Kit project at all, as distinct from being a Spec Kit project without
  Spectra installed — the two deserve different messages.
- The installed extension is *newer* than the published one (a maintainer testing locally).
- The installed manifest is missing, unreadable, or has no version recorded.
- The extension folder exists but is empty or partially written from an interrupted install.
- Spec Kit's own CLI is not installed or not on `PATH` when an update or removal is requested.
- A user runs a project-scoped command from a subdirectory of the project rather than its root.
- The roster and the extension manifest disagree about the shipped agents.
- A generated document's markers are missing or malformed, so the generator cannot find its region.
- The roster grows well beyond today's forty-plus entries and the terminal listing becomes unwieldy.

## 7. Business Requirements

### The roster

| ID    | Requirement                                                                                                                                                                                                  | Priority |
| ----- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| BR-01 | Spectra MUST publish a machine-readable agent roster at `agents-list.json` in the repository root, publicly fetchable with no authentication over the same raw-link mechanism as `catalog.json`.                | P1       |
| BR-02 | `agents-list.json` MUST be the single source of truth for which agents Spectra offers. No other artifact may independently declare the roster.                                                                  | P1       |
| BR-03 | For each agent the roster MUST record: a human-readable title, a one-line description, its availability status, its SDLC phase, its AI-DLC phase, its type (core or add-on), and which product provides it.     | P1       |
| BR-03a | The roster MUST NOT carry multi-paragraph or multi-line explanatory prose. Descriptions are one line; anything longer belongs in hand-authored documentation.                                                  | P1       |
| BR-04 | The roster MUST include agents that are available today **and** agents under development, each distinguished by status — matching the coverage of `AGENTS_LIST.md` and the README table today.                  | P1       |
| BR-05 | The roster MUST distinguish agents provided by the Spectra extension from agents provided by Spec Kit itself, since only the former are installed by Spectra.                                                    | P1       |
| BR-06 | For every agent that is available, the roster MUST record the command that invokes it; for planned agents this MUST be absent rather than invented.                                                             | P1       |
| BR-07 | The roster MUST define the order in which agents are presented, so generated documents and the CLI listing agree.                                                                                               | P2       |
| BR-08 | The roster MUST carry a schema version, so consumers can detect an incompatible format.                                                                                                                         | P2       |
| BR-09 | Each agent MUST have exactly one title, used identically in the roster, every generated document, and the CLI. Existing disagreements (for example `github` / GitHub / GitHub (PR)) MUST be resolved.            | P1       |

### Generation and consistency

| ID    | Requirement                                                                                                                                                                              | Priority |
| ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------- |
| BR-10 | A generator MUST rewrite the structured agent listings from `agents-list.json`, and MUST be runnable by a maintainer as a single command.                                                   | P1       |
| BR-10a | The generator MUST own, in full: the Agents table in `README.md`, the roadmap section of `AGENTS_LIST.md`, and the Spec Kit core agents section of `AGENTS_LIST.md`.                       | P1       |
| BR-10b | The per-agent explanatory prose for shipped agents — arguments, when to use them, worked examples — MUST remain hand-authored and MUST NOT be generated.                                   | P1       |
| BR-10c | The boundary between generated and hand-authored content MUST be explicit in the document itself, so a reader or editor can tell at a glance which is which.                               | P1       |
| BR-11 | The generator MUST only rewrite the regions it owns, leaving all surrounding hand-authored content byte-identical.                                                                          | P1       |
| BR-12 | The generator MUST be deterministic: running it twice against an unchanged roster MUST produce byte-identical output.                                                                       | P1       |
| BR-13 | Automated verification MUST fail when a generated region does not match what the roster would produce, and MUST identify which document is out of date.                                     | P1       |
| BR-13a | Automated verification MUST fail when a shipped agent in the roster has no hand-authored prose block, or when a prose block exists for an agent the roster does not list as shipped.       | P1       |
| BR-14 | Adding, renaming, or removing an agent MUST require editing the roster and running the generator, and this MUST be documented in the contributor guide and reflected in the constitution.   | P1       |
| BR-15 | Automated verification MUST fail when the roster and the extension manifest disagree about the agents the extension ships.                                                                  | P1       |
| BR-16 | The constitution MUST be amended, since it currently states that there is no build script and that the README Agents table is maintained by hand — both untrue after this change.           | P1       |
| BR-17 | The generator is a maintainer tool, not part of the shipped CLI, and MUST NOT add any runtime dependency to the `spectra` command.                                                          | P1       |

### The command surface

| ID    | Requirement                                                                                                                                                                                            | Priority |
| ----- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| BR-18 | The CLI MUST provide a command that prints the roster to the console in a human-readable form, grouped so that a list of forty or more agents remains readable.                                            | P1       |
| BR-19 | The roster command MUST read the published roster at run time, so a newly published agent reaches existing installations without a CLI release.                                                            | P1       |
| BR-20 | The roster command MUST work outside a Spec Kit project, since discovering what Spectra offers does not require having installed it.                                                                       | P1       |
| BR-21 | The CLI MUST provide a command that reports whether the Spectra extension is installed in the current project, determined by the presence of the extension's installed folder.                             | P1       |
| BR-22 | When the extension is not installed, the check command MUST say so and MUST offer to install it, reusing the existing install flow.                                                                         | P1       |
| BR-23 | The CLI MUST provide a command that compares the extension version installed in the current project against the published version and reports whether the agents are up to date.                            | P1       |
| BR-24 | The installed version MUST be read from the extension manifest inside the project; the published version MUST be read from the manifest published on the repository's default branch.                       | P1       |
| BR-25 | When the versions differ, the version command MUST report both and MUST name the update command as the remedy.                                                                                              | P1       |
| BR-26 | The CLI MUST provide a command that updates the installed extension to the published version by delegating to Spec Kit's own extension update.                                                              | P1       |
| BR-27 | The CLI MUST provide a command that removes the extension from the current project by delegating to Spec Kit's own extension removal, and MUST first confirm the extension is installed; if it is not, it MUST say so and make no changes. | P1       |
| BR-28 | Removing the extension from a project MUST NOT remove or affect the installed `spectra` command itself.                                                                                                     | P1       |
| BR-29 | Tool self-management — reporting the CLI's version, updating the CLI, and uninstalling the CLI — MUST be namespaced under a `cli` command group, distinct from the project-scoped commands.                 | P1       |
| BR-30 | Top-level commands MUST act on the Spectra extension in the current project; only commands under the `cli` group may act on the tool itself.                                                                | P1       |
| BR-31 | The `--version`, `--update`, and `--uninstall` flags MUST be removed, not retained as aliases.                                                                                                              | P1       |
| BR-32 | Invoking a removed flag MUST produce a message naming its replacement command, rather than a generic unrecognized-argument error.                                                                           | P2       |
| BR-33 | Every command that acts on the current project MUST behave correctly when run from a subdirectory of that project, not only from its root.                                                                  | P1       |
| BR-34 | Commands that depend on fetching published data MUST fail clearly and explain why when that data cannot be retrieved, and MUST NOT report a misleading result.                                              | P1       |
| BR-35 | The CLI MUST NOT hard-code the list of agents; the roster is data, fetched at run time.                                                                                                                     | P1       |
| BR-36 | The help screen MUST make the distinction between project-scoped and tool-scoped commands evident to a first-time reader.                                                                                    | P2       |
| BR-37 | The version command SHOULD distinguish "not a Spec Kit project" from "a Spec Kit project without Spectra installed", since the remedies differ.                                                              | P2       |
| BR-38 | The roster command SHOULD indicate which agents are currently installed in the project when run inside one.                                                                                                  | P3       |
| BR-39 | Removing the flags and renaming the tool-management commands is a breaking change to the command surface and MUST be released as a MAJOR version of the CLI channel.                                         | P1       |

### Presentation

| ID    | Requirement                                                                                                                                                                    | Priority |
| ----- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| BR-40 | The extension's description MUST be changed to "TELUS Digital - Agentic software engineering across the entire SDLC." wherever it is published, and every published copy MUST agree — including the extension manifest, `catalog.json`, the rebuilt package, and the landing page. | P1       |
| BR-41 | The landing page MUST read agent information from `agents-list.json` at page load rather than hard-coding it, consistent with the existing rule that the page never hard-codes a version. | P2       |

## 8. Success Metrics & Measurable Outcomes

- **SC-01** — A developer can answer "what agents exist?", "is Spectra installed here?", and "are my
  agents current?" using only the `spectra` command, without opening a browser.
- **SC-02** — Agent *classification* is authored in exactly **one** artifact; every structured listing is
  generated or fetched from it, and no agent list is duplicated in CLI code.
- **SC-03** — Adding an agent requires editing **one** file and running **one** command for every
  structured listing to be correct; the only remaining manual step is writing prose, and forgetting it
  fails the build rather than shipping silently.
- **SC-04** — Publishing a new agent requires **zero** CLI releases for it to appear in
  `spectra agent-list` for every existing installation.
- **SC-05** — Every agent has exactly one title across the roster, the generated documents, and the CLI —
  verified automatically, with the count of disagreements at zero.
- **SC-06** — A hand-edit to a generated document is caught before merge, every time.
- **SC-07** — A user told their agents are out of date reaches an up-to-date state in **one** command,
  which was named in the message that told them.
- **SC-08** — For every command in the surface, a first-time reader of `--help` can correctly say whether
  it acts on the project's agents or on the tool.
- **SC-09** — Each project-scoped command gives a distinguishable, actionable message for each of:
  installed, not installed, and not a Spec Kit project.
- **SC-10** — Every published copy of the extension description matches the agreed line, verified before
  release.

## 9. Assumptions

- `agents-list.json` is published from the repository's default branch over the same anonymous raw-link
  mechanism already used for the catalog and the extension package, so it is live on merge and needs no
  release.
- The generator is run by a maintainer as part of preparing a change, and its output is committed. It is
  not run at install time or by end users.
- Because generated documents are committed, automated verification is a regeneration-and-compare check
  rather than a build step that produces artifacts in CI.
- Generated regions in `AGENTS_LIST.md` and `README.md` are delimited by markers, following the pattern
  already used for the managed region in `CLAUDE.md`.
- The volume of hand-authored prose grows slowly — one block per newly shipped Spectra agent (four
  today) — while the generated listings grow with every roadmap entry. That asymmetry is what makes the
  split worth its complexity.
- `spectra/extension.yml` remains authoritative for what Spec Kit installs; the roster is authoritative
  for how agents are described and presented. Their overlap is verified automatically rather than one
  being derived from the other.
- Presence of the extension's installed folder inside the project is a sufficient signal that Spectra is
  installed; the version recorded in the manifest inside that folder is authoritative for what is
  installed.
- Spec Kit remains the mechanism for updating and removing an installed extension; Spectra delegates
  rather than manipulating the project's extension files itself.
- Spectra continues to ship as exactly one extension (Principle II), so project-scoped commands act on a
  single known extension rather than taking an extension argument.
- The existing informational behaviour of the bare `spectra` command is retained.
- Spec Kit core agents listed in the roster are informational; Spectra does not install, update, or
  version them.

## 10. Constraints

- **Zero third-party runtime dependencies.** The shipped CLI is standard-library only; this must remain
  true, including for reading a version out of a YAML manifest and for fetching published data. The
  generator is a maintainer tool and is not bound by this, but must not change what the CLI depends on.
- **The constitution currently forbids what this work requires.** Principle V states there is no build
  script and that the README Agents table is updated by hand. Amending it is part of this work, not a
  side effect of it.
- **Two independently-versioned channels** (Principle VI). The command surface must reinforce that split,
  and agent changes must not require CLI releases.
- **One self-contained extension** (Principle II). The roster informs; it does not become an à-la-carte
  installer.
- **Generated files are committed, not built on demand.** The repository must remain usable by someone
  who never runs the generator — reading GitHub must show correct documentation.
- **Agent-agnostic and cross-platform.** Behaviour must hold on macOS, Linux, and Windows.
- **Breaking changes must be versioned honestly.** Removing flags and renaming commands requires a MAJOR
  CLI release.

## 11. Dependencies

- **Spec Kit's `specify` CLI** — input and executor: relied on to update and remove the installed
  extension.
- **`agents-list.json`** — output of the maintainer's authoring step; input to the generator, the CLI
  roster command, and potentially the landing page.
- **The installed extension manifest inside the project** — input: the source of the installed version.
- **The published extension manifest on the default branch** — input: the source of the published
  version, and the reference the roster is checked against.
- **`AGENTS_LIST.md` and the README Agents table** — outputs of the generator; no longer hand-authored in
  their agent-listing regions.
- **`catalog.json`** — sibling artifact; the extension description change must be reflected here too.
- **The landing page** — publishes the extension description and agent information and must not drift.
- **CI** — extended to verify generated documents and roster/manifest agreement.

## 12. Risks & Mitigations

| Risk                                                                                                              | Impact | Likelihood | Mitigation                                                                                                                                    |
| ------------------------------------------------------------------------------------------------------------------- | ------ | ---------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| A maintainer edits a generated region by hand and their change is silently lost on the next generation            | M      | H          | Explicit generated-region boundaries, a visible "do not edit" notice, and CI that fails on any mismatch.                                         |
| A new shipped agent gets a table row but nobody writes its prose, so the docs look complete but explain nothing    | M      | M          | Verification fails when a shipped agent has no prose block, naming the agent (BR-13a).                                                           |
| The generated/hand-written boundary is unclear, so contributors write prose inside a generated region             | M      | M          | Make the boundary visible in the document (BR-10c) and cover it in the contributor guide.                                                        |
| The roster and the extension manifest drift, so the CLI advertises agents the extension does not ship              | H      | M          | Automated agreement check between roster and manifest, extending the existing catalog/manifest check.                                            |
| A generator is introduced but the landing page's agent section stays hand-written, leaving one drift site unfixed  | M      | M          | Bring the landing page into the same mechanism — generated or fetched at load (BR-41).                                                           |
| Two "version" commands confuse users about which thing they just checked                                           | M      | M          | Distinct wording per command ("agents are up to date" vs. the CLI's own version), and a help screen that groups them separately.                  |
| A second breaking command-surface change lands soon after the previous one, churning users                         | M      | H          | Ship removals and renames together as one MAJOR release, and make removed flags name their replacement.                                          |
| Network-dependent commands fail in restricted corporate environments                                               | M      | M          | Fail with an explicit, actionable message; never present a stale or empty result as authoritative.                                               |
| Reading a version out of YAML without a YAML library misparses an edge case                                        | M      | L          | Constrain to the known manifest shape and cover malformed/missing manifests as explicit behaviours.                                              |
| Printing forty-plus agents overwhelms the terminal                                                                 | L      | H          | Group the output and consider filtering (see Open Questions).                                                                                    |

## 13. Open Questions

- **How should the generated/hand-authored boundary be expressed?** Markers in the Markdown (following
  the `<!-- SPECKIT START -->` pattern already used in `CLAUDE.md`) are the obvious option, but the
  shipped-agent prose sits *between* generated sections in `AGENTS_LIST.md` today, so the document's
  section order may need to change to keep generated and hand-written content in contiguous blocks.
- **Should `spectra agent-list` support filtering** — by status, phase, or provider — given the roster is
  already forty-plus entries and mostly planned agents?
- **Should the roster include the Spec Kit core agents at all?** The README table does, which is why the
  roster must if it is to generate that table. But `spectra agent-list` then shows agents Spectra neither
  ships nor updates, which may mislead.
- **What is the canonical title for the PR agent** — `github`, GitHub, or GitHub (PR)? The roster forces a
  single answer, and today's three names must collapse to one.
- **Where should the generator live and how is it invoked** — a script under a tools directory run
  directly, or wrapped in a documented one-liner? Should it run automatically in a pre-commit hook, or
  only on demand with CI as the backstop?
- **Should `spectra version` also report the CLI version for context**, or stay strictly about the agents?
- **What should `spectra update` do when the extension is already current** — a no-op with a message, or a
  forced reinstall?
- **What is the expected behaviour when the installed extension is newer than the published one?**
- **Should `spectra check` verify more than the folder's existence** — for example that the manifest is
  readable and the commands are registered — or is presence sufficient?
- **Does `spectra uninstall` require confirmation before removing the extension**, given
  `spectra cli uninstall` does?

## 14. Glossary

| Term                     | Definition                                                                                                                                     |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| Agent                    | A capability a user invokes through their coding agent — provided either by the Spectra extension or by Spec Kit itself.                          |
| Roster                   | `agents-list.json` — the public, machine-readable list of agents; the single source of truth for what Spectra offers.                             |
| Generator                | The maintainer-run tool that rewrites the agent-listing regions of the human-facing documentation from the roster.                                |
| Generated region         | A marked span within a hand-authored document that the generator owns and rewrites; everything outside it stays hand-written.                     |
| Structured listing       | Agent content that is pure classification — title, phase, type, status, command — and is therefore generated.                                     |
| Prose block              | The hand-authored explanation of one shipped agent: its arguments, when to use it, and worked examples. Its existence is enforced; its wording is not. |
| Spectra agent            | An agent shipped in the `spectra` extension, invoked as a `speckit.spectra.*` command.                                                            |
| Spec Kit core agent      | An agent shipped by Spec Kit itself, which Spectra builds on but does not install, update, or version.                                            |
| Planned agent            | An agent listed on the roster as under development, with no invocable command yet.                                                                |
| Extension                | The single self-contained Spec Kit extension (`spectra`) that ships every Spectra agent; installed into a project.                                |
| CLI / the tool           | The `spectra` command installed on a developer's machine as a uv tool.                                                                            |
| Catalog channel          | The release channel that publishes the extension from the default branch over raw links; versioned in the extension manifest.                     |
| CLI channel              | The release channel that publishes the `spectra` command; versioned in `VERSION` and released by git tag.                                         |
| Project-scoped command   | A command that acts on the Spectra extension installed in the current working project.                                                            |
| Tool-scoped command      | A command that acts on the `spectra` command itself, namespaced under `cli`.                                                                      |
| Spec Kit project         | A folder containing a `.specify/` directory.                                                                                                      |
