# Feature Specification: Agent Roster & Project-Scoped CLI Commands

**Feature Branch**: `006-agent-roster-cli`

**Created**: 2026-08-09

**Status**: Draft

**Input**: BRD-004 — `brds/agent-roster-and-cli-commands.md` (v0.3.0), "Agent Roster & Project-Scoped CLI Commands"

## Clarifications

### Session 2026-08-09

- Q: How is an agent identified in the roster, given that the generator, the prose-block check, and the roster↔manifest cross-check all need a handle on it? → A: Each entry carries a stable lowercase slug `id` distinct from `title`. The `id` keys prose blocks, manifest cross-checks, and generated anchors; `title` is display-only and free to change.
- Q: What does an installed CLI do when it fetches a roster whose schema version it does not recognize? → A: Degrade on a newer minor schema — render the fields it understands and print a notice that the roster is newer than this CLI, naming the CLI update command; refuse only on a newer major schema.
- Q: What bounds how long a command waits when fetching published data? → A: 10 seconds per fetch, then fail with the clear, actionable message required by FR-041.
- Q: What does "the roster and the extension manifest agree" mean for verification? → A: Set membership plus command names — every shipped roster entry's recorded command matches the manifest's registered command exactly. Descriptions are deliberately independent.
- Q: What exit status does the version command return when the agents are out of date? → A: Success. Reporting "out of date" is a successful report; only genuine errors (not installed, fetch failed) exit non-zero.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Discover what agents Spectra offers, from the terminal (Priority: P1)

A developer evaluating or already using Spectra wants to know what Spectra can do. They run one
`spectra` command and get a readable roster of every agent — its human title, what it does, whether it
is available today, and who provides it — without opening GitHub. The roster itself is published as a
public, machine-readable document so the listing is data rather than something baked into the tool.

**Why this priority**: This is the gap that makes everything else visible. Without a published roster
there is no source of truth for the other stories to read, generate from, or verify against.

**Independent Test**: Install the CLI, run the roster command from an arbitrary folder, and confirm the
published agents are listed with correct titles and statuses. Delivers value on its own: discovery
without a browser.

**Acceptance Scenarios**:

1. **Given** an internet connection, **When** the developer runs the roster command from any directory,
   **Then** the published roster is printed with human-readable titles, and the command succeeds whether
   or not the current folder is a Spec Kit project.
2. **Given** the roster contains both available and planned agents, **When** the list is printed,
   **Then** each agent's status is unambiguous and no planned agent is presented as runnable.
3. **Given** the roster contains agents provided by Spec Kit rather than by Spectra, **When** the list is
   printed, **Then** the provider of each agent is evident.
4. **Given** a newly published agent added to the roster, **When** a developer with an already-installed
   CLI runs the roster command, **Then** the new agent appears without the developer updating the CLI.
5. **Given** no network access, **When** the developer runs the roster command, **Then** the CLI explains
   that the roster could not be fetched rather than printing an empty or stale list silently.
6. **Given** a roster of forty or more agents, **When** the list is printed, **Then** the output is
   grouped so it remains readable rather than an undifferentiated wall of lines.
7. **Given** a roster whose minor schema version is newer than the CLI understands, **When** the developer
   runs the roster command, **Then** every agent is still listed from the recognized fields and a notice
   states the roster is newer than this CLI, naming the CLI update command.
8. **Given** a roster whose major schema version is newer than the CLI understands, **When** the developer
   runs the roster command, **Then** the CLI declines to present the roster, explains that a newer CLI is
   required, and names the CLI update command.

---

### User Story 2 - Confirm Spectra is installed in this project (Priority: P1)

A developer who has just cloned a teammate's project, or is unsure of its state, asks whether Spectra's
agents are available here. They get a definitive yes or no about the current project — and, when the
answer is no, an offer to fix it on the spot.

**Why this priority**: It is the first question a new team member asks, and today the only answers come
from a Spec Kit command or from inspecting hidden folders by hand.

**Independent Test**: Run the check command in a project with Spectra installed, in a Spec Kit project
without it, and in a folder that is not a Spec Kit project; confirm three distinguishable outcomes.

**Acceptance Scenarios**:

1. **Given** a project with Spectra installed, **When** the developer runs the check command, **Then**
   the CLI reports success and exits with a success status.
2. **Given** a Spec Kit project without Spectra installed, **When** the developer runs the check command,
   **Then** the CLI reports that Spectra is not installed, offers to install it, and exits with a failure
   status if the developer declines.
3. **Given** a Spec Kit project without Spectra installed, **When** the developer accepts the offer,
   **Then** the existing install flow runs and, on success, the project ends up with Spectra installed.
4. **Given** a folder that is not a Spec Kit project at all, **When** the developer runs the check
   command, **Then** the message distinguishes that case from "Spec Kit project without Spectra".
5. **Given** the developer runs the check command from a subdirectory of the project, **When** it
   executes, **Then** it reports on the enclosing project rather than failing.

---

### User Story 3 - Find out whether my agents are current, and update them (Priority: P1)

A developer using Spectra wants to know whether they are running the latest agents. They get a clear
verdict and, when behind, the single named command that fixes it — which they then run.

**Why this priority**: This is what makes the independent catalog channel worth having. New agents can
ship any day, and today nobody finds out.

**Independent Test**: In a project with a deliberately older extension installed, confirm the version
command reports both versions and names the update command; run the update and confirm a second version
check reports up to date.

**Acceptance Scenarios**:

1. **Given** an installed extension whose version matches the published one, **When** the developer runs
   the version command, **Then** the CLI reports that the agents are up to date.
2. **Given** an installed extension older than the published one, **When** the developer runs the version
   command, **Then** the CLI reports both versions, names the update command as the fix, and exits with a
   success status because it delivered a verdict.
3. **Given** an out-of-date extension, **When** the developer runs the update command, **Then** the
   extension is updated through Spec Kit and a subsequent version check reports the agents as up to date.
4. **Given** an installed extension already at the published version, **When** the developer runs the
   update command, **Then** the CLI reports that the agents are already current and makes no changes.
5. **Given** Spectra is not installed in the current project, **When** the developer runs the version or
   update command, **Then** the CLI says Spectra is not installed rather than reporting a misleading
   version or failing obscurely.
6. **Given** an installed extension newer than the published one, **When** the developer runs the version
   command, **Then** the CLI reports both versions, states that the installed agents are ahead of what is
   published, does not offer an update, and exits with a success status.
7. **Given** the published version cannot be retrieved, **When** the developer runs the version command,
   **Then** the CLI reports the installed version, explains that the published version could not be
   fetched rather than implying the agents are current, and exits with a failure status.

---

### User Story 4 - Add an agent once and have every listing update itself (Priority: P1)

A TELUS Digital maintainer shipping a new agent classifies it in exactly one place, runs one command, and
every structured listing of agents rewrites itself. They are left to write only the part that needs
judgement — the explanatory prose — and automation tells them if they forget.

**Why this priority**: The roster already disagrees with itself across three files with four agents
shipped and forty-plus planned. Publishing a machine-readable roster without making it the source would
add a fourth place to forget.

**Independent Test**: Add an entry to the roster, run the generator, and confirm every structured listing
contains the agent with an identical title; hand-edit a generated region and confirm verification fails.

**Acceptance Scenarios**:

1. **Given** a new agent added to the roster, **When** the maintainer runs the generator, **Then** every
   structured listing includes the agent, with the same title in each.
2. **Given** a new *shipped* agent added to the roster with no prose block written, **When** the automated
   verification runs, **Then** it fails and names the agent whose prose is missing.
3. **Given** a prose block that exists for an agent the roster does not list as shipped, **When** the
   automated verification runs, **Then** it fails and names that agent.
4. **Given** a repository where a generated region has been edited by hand, **When** the automated
   verification runs, **Then** it fails and identifies the document that no longer matches the roster.
5. **Given** hand-authored prose sitting outside the generated regions, **When** the generator runs,
   **Then** that prose is left byte-identical.
6. **Given** the generator is run twice against an unchanged roster, **When** the outputs are compared,
   **Then** they are byte-identical.
7. **Given** the roster and the extension manifest disagree about which agents the extension ships,
   **When** the automated verification runs, **Then** it fails and reports the disagreement.
8. **Given** a roster entry whose recorded command differs from the command the manifest registers for the
   same agent, **When** the automated verification runs, **Then** it fails and reports the mismatched
   command.
9. **Given** a roster description that differs in wording from the manifest description for the same
   agent, **When** the automated verification runs, **Then** it passes, because the two are intentionally
   independent.
10. **Given** a generated document whose region markers are missing or malformed, **When** the generator
    runs, **Then** it fails with a message naming the document and the missing marker rather than
    rewriting the file or silently skipping it.
11. **Given** the merged change, **When** any user with an already-installed CLI runs the roster command,
    **Then** the new agent is listed with no CLI update required.
12. **Given** the merged change, **When** a user with the previous extension version runs the version
    command, **Then** they are told an update is available and pointed at the update command.
13. **Given** an agent whose title is changed in the roster while its identifier stays the same, **When**
    the generator and the automated verification run, **Then** every listing shows the new title, the
    agent's prose block is still matched to it, and verification passes.
14. **Given** a hand-written heading in an artifact whose agent listing is not fully generated, and whose
    wording no longer matches the agent's canonical title, **When** the automated verification runs,
    **Then** it fails and names both the agent and the file.

---

### User Story 5 - Manage the tool itself, unambiguously (Priority: P2)

Any user of the `spectra` command wants to check, update, or remove the tool rather than the agents. Tool
operations live under a `cli` group so they read unambiguously and cannot be confused with agent
operations.

**Why this priority**: The confusion is real but survivable today; the value is realised only once the
project-scoped commands (P1) exist and compete for the same words.

**Independent Test**: Run each `cli` subcommand and confirm it acts on the tool; run each removed flag and
confirm it names its replacement.

**Acceptance Scenarios**:

1. **Given** an installed CLI, **When** the user asks for the CLI's own version, **Then** the CLI's version
   is reported, noting whether a newer release exists.
2. **Given** a newer CLI release exists, **When** the user runs the CLI self-update, **Then** the CLI
   updates itself and reports the new version.
3. **Given** an installed CLI, **When** the user runs the CLI self-uninstall and confirms, **Then** the
   `spectra` command is removed from the machine and any extension installed in a project is left
   untouched.
4. **Given** a user who runs the removed `--version`, `--update`, or `--uninstall` flag, **When** the
   command executes, **Then** it fails with a message naming the replacement command rather than a bare
   "unrecognized argument".
5. **Given** the help screen, **When** a first-time reader reads it, **Then** it is evident which commands
   act on the project's agents and which act on the tool.
6. **Given** the bare `spectra` command with no arguments, **When** it runs, **Then** it prints its
   existing informational output and does not touch the current folder.

---

### User Story 6 - Remove Spectra's agents from a project (Priority: P2)

A developer who no longer wants Spectra's agents in a given project cleans the project without removing
the tool from their machine.

**Why this priority**: Completes the project-scoped lifecycle, but is needed less often than discovery,
checking, and updating.

**Independent Test**: Run the project uninstall in a project with Spectra installed and confirm the
extension is gone while the `spectra` command still works; run it where Spectra is absent and confirm
nothing changes.

**Acceptance Scenarios**:

1. **Given** a project with Spectra installed, **When** the developer runs the project uninstall and
   confirms, **Then** the extension is removed from that project and the `spectra` command remains
   installed on the machine.
2. **Given** a project without Spectra installed, **When** the developer runs the project uninstall,
   **Then** the CLI reports that Spectra is not installed and makes no changes.
3. **Given** Spec Kit's own CLI is unavailable, **When** the developer runs the project uninstall or
   update, **Then** the CLI explains that Spec Kit is required and makes no changes.

---

### User Story 7 - Spectra is described the same way everywhere (Priority: P2)

A reader encountering Spectra through the catalog, the extension manifest, the packaged download, or the
landing page sees one positioning line and one title per agent, because those surfaces read from shared
sources rather than restating them.

**Why this priority**: Presentation drift is embarrassing rather than blocking, but it is cheap to fix
inside this change and expensive to fix later once more surfaces exist.

**Independent Test**: Compare the description string across every published surface and confirm they
match; load the landing page and confirm its agent information reflects a roster edit without an HTML
change.

**Acceptance Scenarios**:

1. **Given** the extension description, **When** every published copy is compared, **Then** all read
   "TELUS Digital - Agentic software engineering across the entire SDLC."
2. **Given** an agent renamed in the roster, **When** the generator is run and the landing page is
   loaded, **Then** every surface shows the new title and none shows the old one.
3. **Given** the landing page, **When** it is loaded, **Then** its agent information comes from the
   published roster rather than being hard-coded in the page.

---

### Edge Cases

- The published roster cannot be fetched — offline, behind a proxy, or rate-limited — for either the
  roster listing or the version comparison.
- The fetched roster declares a schema version newer than the installed CLI understands, in either its
  minor or its major component.
- The fetched roster is retrievable but malformed — not valid structured data, or missing the schema
  version entirely.
- The current folder is not a Spec Kit project at all, as distinct from being a Spec Kit project without
  Spectra installed; the two get different messages and different remedies.
- The installed extension is *newer* than the published one, as happens when a maintainer tests locally.
- The installed extension manifest is missing, unreadable, or records no version.
- The extension folder exists but is empty or partially written from an interrupted install.
- Spec Kit's own CLI is not installed or not on `PATH` when an update or removal is requested.
- A project-scoped command is run from a subdirectory of the project rather than its root.
- The roster and the extension manifest disagree about which agents the extension ships.
- A generated document's region markers are missing, malformed, or duplicated, so the generator cannot
  locate the region it owns.
- The roster grows well beyond today's forty-plus entries and the terminal listing becomes unwieldy.
- A maintainer edits a generated region by hand and commits it without running the generator.
- A user on Windows runs every command, where path handling and terminal rendering differ.

## Requirements *(mandatory)*

### Functional Requirements

#### The roster

- **FR-001**: Spectra MUST publish a machine-readable agent roster at `agents-list.json` in the
  repository root, publicly fetchable with no authentication over the same raw-link mechanism as
  `catalog.json`.
- **FR-002**: `agents-list.json` MUST be the single source of truth for which agents Spectra offers; no
  other artifact may independently declare the roster.
- **FR-002a**: "Artifact" in FR-002 means any committed document, published page, or packaged file that
  enumerates or names the agents Spectra offers — including the extension's own `README.md`, which ships
  inside the published package. Each such artifact MUST either derive its agent listing from the roster or
  contain no listing at all.
- **FR-003**: For each agent the roster MUST record a stable identifier, a human-readable title, a
  one-line description, an availability status, an SDLC phase, an AI-DLC phase, a type (core or add-on),
  and which product provides it.
- **FR-003a**: The stable identifier MUST be a lowercase slug, MUST be unique across the roster, and MUST
  be the handle every automated consumer keys off — prose-block matching, roster↔manifest cross-checking,
  and generated document anchors. The title MUST NOT be used as an identifier.
- **FR-003b**: Changing an agent's title MUST NOT require changing its identifier, and MUST NOT break
  prose-block matching, cross-checking, or any generated anchor.
- **FR-004**: The roster MUST NOT carry multi-paragraph or multi-line explanatory prose; descriptions are
  one line and anything longer belongs in hand-authored documentation.
- **FR-005**: The roster MUST include agents that are available today and agents under development, each
  distinguished by status, matching the coverage of `AGENTS_LIST.md` and the README Agents table as they
  stand today.
- **FR-006**: The roster MUST distinguish agents provided by the Spectra extension from agents provided by
  Spec Kit itself, since only the former are installed by Spectra.
- **FR-007**: For every available agent the roster MUST record the command that invokes it; for planned
  agents this MUST be absent rather than invented.
- **FR-008**: The roster MUST define the order in which agents are presented, so generated documents and
  the CLI listing agree.
- **FR-009**: The roster MUST carry a schema version expressed as major and minor components, where a
  backward-compatible addition bumps the minor component and a change that invalidates existing readers
  bumps the major component.
- **FR-009a**: When the roster's major schema version is newer than the one the CLI understands, the CLI
  MUST refuse to present the roster, explain that the roster requires a newer CLI, and name the CLI
  update command.
- **FR-009b**: When only the roster's minor schema version is newer than the one the CLI understands, the
  CLI MUST still present every agent using the fields it understands, and MUST print a notice that the
  roster is newer than this CLI, naming the CLI update command. Unrecognized fields MUST be ignored
  rather than treated as an error.
- **FR-010**: Each agent MUST have exactly one title, used identically in the roster, every generated
  document, the CLI, and every artifact in scope under FR-002a; the title is display text only. The
  existing disagreement over the PR agent's name MUST be resolved to a single title, across all four
  places it currently differs.

#### Generation and consistency

- **FR-011**: A generator MUST rewrite the structured agent listings from `agents-list.json`, and MUST be
  runnable by a maintainer as a single command.
- **FR-012**: The generator MUST own, at minimum and in full, the Agents table in `README.md`, the roadmap
  section of `AGENTS_LIST.md`, the Spec Kit core agents section of `AGENTS_LIST.md`, and the Commands table
  in `spectra/README.md`. Owning further structured listings is permitted; leaving any of these
  hand-authored is not.
- **FR-013**: Per-agent explanatory prose for shipped agents — arguments, when to use them, worked
  examples — MUST remain hand-authored and MUST NOT be generated.
- **FR-014**: The boundary between generated and hand-authored content MUST be explicit in the document
  itself, including a visible notice that the generated content must not be edited by hand.
- **FR-015**: The generator MUST rewrite only the regions it owns, leaving all surrounding hand-authored
  content byte-identical.
- **FR-016**: The generator MUST be deterministic: running it twice against an unchanged roster MUST
  produce byte-identical output.
- **FR-017**: Automated verification MUST fail when a generated region does not match what the roster
  would produce, and MUST identify which document is out of date.
- **FR-018**: Automated verification MUST fail, naming the agent, when a shipped agent in the roster has
  no hand-authored prose block, or when a prose block exists for an agent the roster does not list as
  shipped. Prose blocks MUST be matched to roster entries by the agent's stable identifier, not by its
  title.
- **FR-018a**: Automated verification MUST fail, naming the agent and the file, when a shipped agent's
  canonical title does not appear in an artifact in scope under FR-002a whose agent listing is not fully
  generated — the containment check that keeps hand-written headings from drifting away from the roster.
- **FR-019**: Automated verification MUST fail when the roster and the extension manifest disagree about
  which agents the extension ships, matching entries to manifest commands by the agent's stable
  identifier.
- **FR-019a**: That agreement check MUST cover exactly two things: that the set of agents the roster marks
  as shipped by Spectra is the same set the manifest registers commands for, and that each such entry's
  recorded command string matches the manifest's registered command exactly. Descriptions in the roster
  and the manifest MUST be allowed to differ, since they address different audiences.
- **FR-020**: The generator MUST fail with an actionable message, naming the document and the marker, when
  a generated document's region markers are missing or malformed, rather than rewriting the document or
  skipping it silently.
- **FR-021**: Adding, renaming, or removing an agent MUST require editing the roster and running the
  generator, and this MUST be documented in the contributor guide.
- **FR-022**: The constitution MUST be amended, since it currently states that there is no build script
  and that the README Agents table is maintained by hand — both untrue after this change.
- **FR-023**: The generator MUST be maintainer tooling only and MUST NOT add any runtime dependency to the
  `spectra` command, nor be required at install time or by end users.
- **FR-024**: Generated documents MUST remain committed to the repository, so someone reading the
  repository without ever running the generator sees correct documentation.

#### The command surface

- **FR-025**: The CLI MUST provide a command that prints the roster to the console in human-readable form,
  grouped so a list of forty or more agents remains readable.
- **FR-026**: The roster command MUST read the published roster at run time, so a newly published agent
  reaches existing installations without a CLI release.
- **FR-027**: The roster command MUST work outside a Spec Kit project.
- **FR-028**: The CLI MUST provide a command that reports whether the Spectra extension is installed in
  the current project, exiting with a success status when it is.
- **FR-029**: When the extension is not installed, that command MUST say so, MUST offer to install it
  reusing the existing install flow, and MUST exit with a failure status if the offer is declined.
- **FR-030**: The CLI MUST provide a command that compares the extension version installed in the current
  project against the published version and reports whether the agents are up to date.
- **FR-031**: The installed version MUST be read from the extension manifest inside the project; the
  published version MUST be read from the manifest published on the repository's default branch.
- **FR-032**: When the versions differ, the version command MUST report both and MUST name the update
  command as the remedy.
- **FR-032a**: The version command MUST exit with a success status whenever it can deliver a verdict —
  up to date, out of date, or installed-ahead-of-published — and MUST exit non-zero only when it cannot:
  Spectra is not installed, the project is not a Spec Kit project, the install is incomplete, or the
  published version could not be retrieved.
- **FR-033**: The CLI MUST provide a command that updates the installed extension to the published version
  by delegating to Spec Kit's own extension update, and MUST report success without making changes when
  the installed version is already current.
- **FR-034**: The CLI MUST provide a command that removes the extension from the current project by
  delegating to Spec Kit's own extension removal, MUST first confirm the extension is installed, and MUST
  say so and make no changes when it is not.
- **FR-035**: Removing the extension from a project MUST NOT remove or affect the installed `spectra`
  command itself.
- **FR-036**: Tool self-management — reporting the CLI's version, updating the CLI, and uninstalling the
  CLI — MUST be namespaced under a `cli` command group.
- **FR-037**: Top-level commands MUST act on the Spectra extension in the current project; only commands
  under the `cli` group may act on the tool itself.
- **FR-038**: The `--version`, `--update`, and `--uninstall` flags MUST be removed and MUST NOT be retained
  as aliases.
- **FR-039**: Invoking a removed flag MUST produce a message naming its replacement command rather than a
  generic unrecognized-argument error.
- **FR-040**: Every command that acts on the current project MUST behave correctly when run from a
  subdirectory of that project, not only from its root.
- **FR-041**: Commands that depend on fetching published data MUST fail clearly and explain why when that
  data cannot be retrieved, and MUST NOT report a misleading result.
- **FR-041a**: Each fetch of published data MUST time out after 10 seconds and then produce the failure
  message required by FR-041, so no command can appear to hang.
- **FR-042**: The CLI MUST NOT hard-code the list of agents; the roster is data, fetched at run time. (A
  specific, directly testable instance of FR-002.)
- **FR-043**: The help screen MUST make the distinction between project-scoped and tool-scoped commands
  evident to a first-time reader.
- **FR-044**: Project-scoped commands MUST distinguish "not a Spec Kit project" from "a Spec Kit project
  without Spectra installed", since the remedies differ.
- **FR-045**: Project-scoped commands MUST report an interrupted or partial installation — an extension
  folder present but without a readable manifest version — as an incomplete install rather than as either
  installed or absent.
- **FR-046**: Project-scoped commands that delegate to Spec Kit MUST explain that Spec Kit is required and
  make no changes when Spec Kit's CLI is unavailable.
- **FR-047**: The existing informational behaviour of the bare `spectra` command MUST be retained, and it
  MUST NOT act on the current folder.
- **FR-048**: The roster command SHOULD indicate which agents are currently installed in the project when
  run inside one.
- **FR-049**: Removing the flags and renaming the tool-management commands MUST be released as a MAJOR
  version of the CLI channel.
- **FR-050**: All command behaviour MUST hold on macOS, Linux, and Windows.

#### Presentation

- **FR-051**: The extension's description MUST be changed to "TELUS Digital - Agentic software engineering
  across the entire SDLC." wherever it is published, and every published copy MUST agree — the extension
  manifest, `catalog.json`, the rebuilt package, and the landing page.
- **FR-052**: The landing page MUST read agent information from `agents-list.json` at page load rather
  than hard-coding it, consistent with the existing rule that the page never hard-codes a version.

### Out of Scope

- Authoring or changing any agent. This work adds no new `speckit.spectra.*` command.
- Installing individual agents. Spectra ships as one self-contained extension; the roster is
  informational, not an à-la-carte install menu.
- Managing non-Spectra extensions. These commands are Spectra-scoped and delegate to Spec Kit where a
  Spec Kit operation exists.
- Generating explanatory prose. Per-agent detail for shipped agents stays hand-authored, as do the
  narrative sections of `README.md`.
- Replacing `spectra/extension.yml`. It remains the manifest Spec Kit validates and installs from.
- A registry of third-party or community agents.
- Automatic background update checks for agents; version comparison happens when the user asks.
- Filtering or searching the roster listing by status, phase, or provider.

### Key Entities

- **Agent**: A capability a user invokes through their coding agent, provided either by the Spectra
  extension or by Spec Kit itself. Identified by a stable lowercase slug; presented under exactly one
  human-readable title.
- **Roster**: The public, machine-readable list of agents (`agents-list.json`) — the single source of
  truth for what Spectra offers. Carries a schema version and a defined presentation order.
- **Roster entry**: One agent's classification — stable identifier, title, one-line description, status,
  SDLC phase, AI-DLC phase, type (core or add-on), provider, and, when available, the invoking command.
  The identifier is the machine handle; the title is display text.
- **Generated region**: A marked span within a hand-authored document that the generator owns and
  rewrites; everything outside it stays hand-written.
- **Prose block**: The hand-authored explanation of one shipped agent — arguments, when to use it, worked
  examples — associated with its agent by stable identifier. Its existence is enforced automatically; its
  wording is not.
- **Installed extension record**: The Spectra extension installed inside a project, whose manifest records
  the version currently in use.
- **Published extension manifest**: The extension manifest on the repository's default branch, which
  defines the currently published version.
- **Command scope**: Whether a command acts on the Spectra extension in the current project or on the
  `spectra` tool itself; the latter is namespaced under `cli`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer can answer "what agents exist?", "is Spectra installed here?", and "are my
  agents current?" using only the `spectra` command, with zero browser visits.
- **SC-002**: Agent classification is authored in exactly one artifact; the count of independent agent
  lists elsewhere — including in CLI code — is zero.
- **SC-003**: Adding an agent requires editing one file and running one command for every structured
  listing to be correct; the only remaining manual step is writing prose, and omitting it fails
  verification rather than shipping silently.
- **SC-004**: Publishing a new agent requires zero CLI releases for it to appear in the roster listing for
  every existing installation.
- **SC-005**: Every agent has exactly one title across the roster, the generated documents, the CLI, and
  every artifact in scope under FR-002a — verified automatically, with the count of disagreements at zero.
- **SC-006**: A hand-edit to a generated document is caught before merge, every time — verified by
  deliberately introducing one and observing the failure.
- **SC-007**: A user told their agents are out of date reaches an up-to-date state in one command, which
  was named in the message that told them.
- **SC-008**: For every command in the surface, a first-time reader of the help screen can correctly say
  whether it acts on the project's agents or on the tool.
- **SC-009**: Each project-scoped command gives a distinguishable, actionable message for each of:
  installed, not installed, incomplete install, and not a Spec Kit project.
- **SC-010**: Every published copy of the extension description matches the agreed line, verified before
  release, with zero mismatches.
- **SC-011**: Running the generator twice against an unchanged roster produces zero file differences.
- **SC-012**: Every project-scoped command produces identical outcomes when run from the project root and
  from a nested subdirectory.
- **SC-013**: No command that fetches published data stays silent for more than 10 seconds before either
  producing its result or explaining the failure.

## Assumptions

Where the source BRD left a question open, the following defaults were chosen and are recorded here
rather than blocking the spec.

- **Canonical PR agent title**: the PR agent is titled **GitHub (PR)** everywhere — the wording already
  public in the README Agents table — invoked by `speckit.spectra.create-pr`. The `AGENTS_LIST.md`
  heading form (`github` — GitHub) is retired.
- **Command names**: `spectra agent-list`, `spectra check`, `spectra version`, `spectra update`,
  `spectra uninstall` at the top level; `spectra cli version`, `spectra cli update`,
  `spectra cli uninstall` under the tool group; `spectra install` unchanged.
- **`spectra version` stays strictly about the agents.** It does not report the CLI's version, since
  mixing the two would undercut the whole point of separating the noun. The CLI's version is available
  from `spectra cli version`.
- **`spectra update` when already current** reports that the agents are current and makes no changes; it
  does not force a reinstall.
- **An installed extension newer than the published one** is reported as ahead of what is published, with
  both versions shown, no update offered, and a success exit status.
- **`spectra uninstall` asks for confirmation**, matching `spectra cli uninstall`, with a non-interactive
  bypass flag for scripted use.
- **`spectra check` treats the presence of the extension's installed folder as the signal**, and
  additionally reports an incomplete install when the folder is present but its manifest is unreadable or
  records no version. It does not verify that commands are registered with the user's agent.
- **Generated regions are delimited by HTML comment markers** in the Markdown, following the pattern
  already used for the managed region in `CLAUDE.md`. A document may contain more than one generated
  region, so the existing section order of `AGENTS_LIST.md` — with shipped-agent prose between generated
  sections — does not need to change.
- **The generator lives in the repository as a maintainer script, run on demand.** No pre-commit hook is
  mandated; CI is the backstop.
- **The roster listing is grouped by SDLC phase** and offers no filtering flags in this release.
- **Spec Kit core agents appear in the roster**, labelled by provider, because the README table lists them
  and the generator must produce that table. The listing makes clear that Spectra neither installs,
  updates, nor versions them.
- **The project root is located by walking up from the current directory** to the nearest folder
  containing `.specify/`.
- The roster is published from the repository's default branch over the same anonymous raw-link mechanism
  already used for the catalog and the package, so it is live on merge and needs no release.
- Because generated documents are committed, automated verification is a regenerate-and-compare check
  rather than a build step that produces artifacts in CI.
- `spectra/extension.yml` remains authoritative for what Spec Kit installs; the roster is authoritative
  for how agents are described and presented. Their overlap is verified automatically rather than one
  being derived from the other.
- Spec Kit remains the mechanism for updating and removing an installed extension; Spectra delegates
  rather than manipulating the project's extension files itself.
- Spectra continues to ship as exactly one extension, so project-scoped commands act on a single known
  extension rather than taking an extension argument.
- Spec Kit core agents listed in the roster are informational only.
- The shipped CLI remains free of third-party runtime dependencies, including for reading a version out
  of the YAML manifest and for fetching published data. The generator is maintainer tooling and is not
  bound by that rule, but must not change what the CLI depends on.
- The volume of hand-authored prose grows slowly — one block per newly shipped Spectra agent, four today
  — while the generated listings grow with every roadmap entry. That asymmetry is what justifies the
  split between generated and hand-written content.

## Dependencies

- **Spec Kit's `specify` CLI** — relied on to update and remove the installed extension.
- **`agents-list.json`** — output of the maintainer's authoring step; input to the generator, the CLI
  roster command, and the landing page.
- **The installed extension manifest inside the project** — the source of the installed version.
- **The published extension manifest on the default branch** — the source of the published version, and
  the reference the roster is checked against.
- **`AGENTS_LIST.md` and the README Agents table** — outputs of the generator; no longer hand-authored in
  their agent-listing regions.
- **`catalog.json` and the packaged extension** — sibling artifacts; the description change must be
  reflected in both.
- **The landing page** — publishes the extension description and agent information and must not drift.
- **CI** — extended to verify generated documents, prose-block presence, and roster/manifest agreement.
- **The constitution** — must be amended in the same change, since it currently forbids what this work
  requires.
