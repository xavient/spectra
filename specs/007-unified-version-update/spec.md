# Feature Specification: Unified Version & Update Commands

**Feature Branch**: `007-unified-version-update`

**Created**: 2026-08-16

**Status**: Implemented

**Input**: GitHub Issue #10 — "Unify `spectra version` and `spectra update` to check all 4 components"

## Clarifications

### Session 2026-08-16

- Q: Should the unified `spectra version` still require a Spec Kit project with Spectra installed, given that two of the four components are machine-level? → A: Yes — require a Spec Kit project with Spectra installed, exiting EXIT_PROJECT_STATE otherwise. The precondition stays identical to today's command and to `spectra update`, so a user never has to reason about which subset of components a given folder can report on.
- Q: What should `spectra update` do with a component whose status is "unknown" (specify absent, network unreachable)? → A: Skip it. Report it as "skipped — status could not be determined" in the final summary, and do not let it affect the exit code. Attempting an update against an undeterminable state risks a pointless failure and would corrupt the "did anything fail?" signal the exit code carries.
- Q: What should the Core agents (integration) version be compared against, given that a behind Specify CLI makes an installed-CLI comparison ambiguous? → A: `specify self check` is the first step and the single source for both rows — it reports the installed CLI version and whether a newer one exists. Because the integration version tracks the CLI version, a behind CLI necessarily means a behind integration: both are reported as needing updating, and both are then updated. Independently, an integration whose version does not match an already-current CLI also needs updating (the user upgraded the CLI but never re-ran the integration upgrade).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Single command to check the health of all Spectra stack components (Priority: P1)

A developer using Spectra wants to know whether their entire stack is current — not just the extension agents, but also the Specify CLI, the core integration, and the Spectra CLI tool itself. They run `spectra version` and get a clear, 4-line summary showing the status of every component, without needing to know about or run multiple different commands.

**Why this priority**: This is the foundational change — the health check module powers both the new `version` and `update` commands. Without it, neither command can report on all four components.

**Independent Test**: In a project where one component is deliberately out of date, run `spectra version` and confirm all four components are listed with correct installed/latest versions and a clear status indicator for each.

**Acceptance Scenarios**:

1. **Given** a Spec Kit project with Spectra installed and all components up to date, **When** the developer runs `spectra version`, **Then** all four components (Specify CLI, Core agents, Spectra CLI, Spectra agents) are reported as up to date with their version numbers.
2. **Given** a project where the Spectra CLI is out of date but other components are current, **When** the developer runs `spectra version`, **Then** the Spectra CLI row shows "needs updating" with both installed and latest versions, and the other three rows show "up to date".
3. **Given** a project where multiple components need updating, **When** the developer runs `spectra version`, **Then** all out-of-date components are identified and the output ends with a hint to run `spectra update`.
4. **Given** no network access, **When** the developer runs `spectra version`, **Then** every component whose latest version cannot be resolved reports "unknown" rather than being guessed at, each still shows its locally-readable installed version where one exists, and the command reports what it could rather than failing outright.
5. **Given** `specify` is not on PATH, **When** the developer runs `spectra version`, **Then** the Specify CLI and Core agents rows report "unknown" rather than crashing, and the Spectra CLI and Spectra agents rows still report normally.
6. **Given** `.specify/integration.json` is missing or malformed, **When** the developer runs `spectra version`, **Then** the Core agents row reports "unknown" with an explanation, and all other components report normally.
7. **Given** the `--no-update-check` flag is passed, **When** the developer runs `spectra version`, **Then** the lookup of the latest Spectra CLI release is suppressed and that row reports "unknown" while still showing its installed version, and every other check — including the delegated `specify self check` — still runs.
8. **Given** a folder that is not a Spec Kit project, **When** the developer runs `spectra version`, **Then** no component table is printed, the message points at `specify init`, and the command exits EXIT_PROJECT_STATE (5).
9. **Given** a Spec Kit project without Spectra installed, **When** the developer runs `spectra version`, **Then** no component table is printed, the message points at `spectra install`, and the command exits EXIT_PROJECT_STATE (5).
10. **Given** `specify self check` reports the installed CLI is behind a newer release, **When** the developer runs `spectra version`, **Then** both the Specify CLI row and the Core agents row report "needs updating", because the integration version tracks the CLI version.
11. **Given** `specify self check` reports the CLI is current but `.specify/integration.json` records an older version than the installed CLI, **When** the developer runs `spectra version`, **Then** the Specify CLI row reports "up to date" and the Core agents row reports "needs updating".

---

### User Story 2 - Single command to update all out-of-date components (Priority: P1)

A developer who has confirmed (via `spectra version` or otherwise) that components need updating wants to bring everything current in one step. They run `spectra update`, see what needs updating, confirm once, and all updates execute in the correct order — continuing through partial failures so one broken update does not block the rest.

**Why this priority**: Equal to Story 1 — the update command is the other half of the feature. Together they replace the fragmented `spectra version` + `spectra update` + `spectra cli version` + `spectra cli update` surface with two unified commands.

**Independent Test**: In a project where the Spectra CLI and Spectra agents are both out of date, run `spectra update`, confirm, and verify both are updated and the final report shows success for each.

**Acceptance Scenarios**:

1. **Given** all components are up to date, **When** the developer runs `spectra update`, **Then** the command reports "everything is up to date" and exits 0 without prompting.
2. **Given** two components need updating, **When** the developer runs `spectra update`, **Then** the command lists the two out-of-date components with their version transitions and prompts for confirmation.
3. **Given** the developer confirms the update, **When** updates execute, **Then** they run in the correct order: Specify CLI → Core agents (integration) → Spectra CLI → Spectra agents (extension).
4. **Given** the Specify CLI update fails but the Spectra CLI update would succeed, **When** updates execute, **Then** the Spectra CLI update still runs (partial failure does not abort remaining updates), and the final report shows which succeeded and which failed.
5. **Given** the developer passes `--yes`, **When** `spectra update` runs, **Then** the confirmation prompt is skipped and updates proceed immediately.
6. **Given** the developer declines the confirmation prompt, **When** prompted, **Then** no updates are applied and the command exits with EXIT_DECLINED (1).
7. **Given** all updates succeed, **When** the final report is shown, **Then** the command exits 0.
8. **Given** any update fails, **When** the final report is shown, **Then** the command exits EXIT_DELEGATION (4) and the failure message includes actionable detail (exit code or error from the underlying command).
9. **Given** `specify` is not on PATH so the Specify CLI and Core agents statuses are unknown, **When** the developer runs `spectra update`, **Then** those two components are not attempted, are listed as skipped with the reason, and the exit code reflects only the components that were actually attempted.
10. **Given** every out-of-date component updates successfully while one other component's status is unknown, **When** the final report is shown, **Then** the command exits 0 — a skipped component does not make the run a failure.
11. **Given** a component's status is unknown, **When** the confirmation prompt lists what will be updated, **Then** that component does not appear in the list.
12. **Given** no component's status could be determined at all (offline and `specify` absent), **When** the developer runs `spectra update`, **Then** the output states that nothing could be checked and names the unknown components, does **not** claim everything is up to date, prompts for nothing, and exits 0.
13. **Given** some components are current and others are unknown, with none needing updating, **When** the developer runs `spectra update`, **Then** the output reports what is current *and* names the components that could not be checked, rather than implying the whole stack was verified.

---

### User Story 3 - Retired `spectra cli version` and `spectra cli update` produce clear errors (Priority: P2)

A developer who has muscle memory for the old commands runs `spectra cli version` or `spectra cli update`. Instead of an opaque error, they get a clear message naming the replacement command.

**Why this priority**: Important for a smooth transition, but secondary to the new functionality. Users who never learned the old commands are unaffected.

**Independent Test**: Run `spectra cli version` and confirm it prints the retirement message and exits 2; same for `spectra cli update`.

**Acceptance Scenarios**:

1. **Given** a developer runs `spectra cli version`, **When** the command executes, **Then** it prints "`spectra cli version` has been retired. Use `spectra version` instead." and exits with EXIT_USAGE (2).
2. **Given** a developer runs `spectra cli update`, **When** the command executes, **Then** it prints "`spectra cli update` has been retired. Use `spectra update` instead." and exits with EXIT_USAGE (2).
3. **Given** a developer runs `spectra cli uninstall`, **When** the command executes, **Then** it behaves exactly as before — unchanged.
4. **Given** a developer runs `spectra cli` with no subcommand, **When** the help is printed, **Then** only `uninstall` appears in the tool commands section.
5. **Given** a developer runs `spectra --help`, **When** the help is printed, **Then** the `cli version` and `cli update` entries are removed from the Tool commands panel, and the descriptions for `version` and `update` in the Project commands panel reflect the new unified behavior.

---

### User Story 4 - Update order respects component dependencies (Priority: P2)

Updates execute in a defined order that respects dependency relationships: the Specify CLI must be current before `specify integration upgrade` can run against it, and both must be settled before the Spectra extension update delegates back to `specify`.

**Why this priority**: Correctness constraint — wrong order could leave the stack in an inconsistent state. But this is an implementation invariant rather than a user-facing flow, so it ranks below the user-visible stories.

**Independent Test**: Mock all four update commands, trigger an update where all four are out of date, and verify the calls execute in the prescribed order.

**Acceptance Scenarios**:

1. **Given** all four components need updating, **When** the update runs, **Then** the order is: Specify CLI (`specify self upgrade`) → Core agents (`specify integration upgrade`) → Spectra CLI (`uv tool install …`) → Spectra agents (`specify extension update spectra`).
2. **Given** only the Spectra CLI and Spectra agents need updating, **When** the update runs, **Then** only those two are attempted and they execute in their relative order (Spectra CLI before Spectra agents).
3. **Given** the Specify CLI update fails, **When** the integration update would follow, **Then** the integration update is still attempted (no short-circuiting), and the final report documents both outcomes.

---

### Edge Cases

- What happens when `specify self check` output format changes? The parser should degrade gracefully, reporting "unknown" rather than crashing.
- How does the system handle a `.specify/integration.json` with a missing `version` field? Reports "unknown" for the Core agents component.
- What happens when the integration version is *ahead* of the installed Specify CLI version (e.g., a pre-release integration)? Reports "ahead" — same logic as the extension comparison — and is not offered for update.
- What happens when `specify self check` reports a newer CLI is available but `.specify/integration.json` already matches the newer version? The Specify CLI row still reports "needs updating"; the Core agents row is driven by the CLI being behind, so it also reports "needs updating" and is re-evaluated after the CLI upgrade.
- What happens when `spectra update` is run outside a Spec Kit project? Same behavior as today: exit EXIT_PROJECT_STATE with a message pointing at `specify init`.
- What happens when `spectra update` is run in a project without Spectra installed? Same behavior as today: exit EXIT_PROJECT_STATE pointing at `spectra install`.
- What happens when `spectra version` is run outside a Spec Kit project, or in one without Spectra installed? The command declines to report at all and exits EXIT_PROJECT_STATE, naming the remedy (`specify init` or `spectra install`) — it does not fall back to reporting only the two machine-level components.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST report the status of four components in a single `spectra version` invocation: Specify CLI, Core agents (integration), Spectra CLI, and Spectra agents (extension).
- **FR-002**: Each component status MUST include at minimum: component name, installed version, and a status indicator drawn from exactly four values — up to date, needs updating, ahead, or unknown. A component that could not be checked, for any reason, MUST report "unknown" together with an explanation; there is no separate "error" state, because reporting it and acting on it are identical to the unknown case.
- **FR-003**: When any component reports "needs updating", the output MUST end with a hint to run `spectra update`.
- **FR-004**: System MUST detect the Specify CLI status by running `specify self check` first, before any other component check, and parsing from its output both the installed CLI version and whether a newer one is available.
- **FR-005**: System MUST detect the Core agents status by reading the `version` field from `.specify/integration.json` and reporting it as needing updating when **either** the Specify CLI is itself behind (because the integration version tracks the CLI version, so a behind CLI implies a behind integration) **or** the integration version does not match the installed Specify CLI version (the CLI was upgraded but the integration upgrade was never re-run).
- **FR-006**: System MUST detect the Spectra CLI status by comparing the installed command's version against the newest published release, reusing the existing release-check behavior rather than introducing a second mechanism.
- **FR-007**: System MUST detect the Spectra agents status by comparing the version recorded in the project's installed extension against the version published in the catalog, reusing the existing comparison behavior.
- **FR-008**: `spectra update` MUST run the health check, list out-of-date components, prompt for confirmation, then execute updates in order: Specify CLI → Core agents → Spectra CLI → Spectra agents.
- **FR-009**: `spectra update` MUST continue through partial failures — a failed update for one component does not prevent attempts on remaining components.
- **FR-010**: `spectra update` MUST report the final status of each component after all update attempts complete: updated / failed / skipped (already current, or status could not be determined).
- **FR-011**: `spectra update --yes` MUST skip the confirmation prompt.
- **FR-012**: `spectra update` MUST exit 0 when every attempted update succeeded, counting skipped components as neither success nor failure; it MUST exit EXIT_DELEGATION (4) when any attempted update failed.
- **FR-013**: `spectra cli version` MUST print a retirement message naming `spectra version` as the replacement and exit EXIT_USAGE (2).
- **FR-014**: `spectra cli update` MUST print a retirement message naming `spectra update` as the replacement and exit EXIT_USAGE (2).
- **FR-015**: `spectra cli uninstall` MUST remain unchanged.
- **FR-016**: The `--no-update-check` flag MUST suppress the network call that resolves the latest Spectra CLI release, and MUST NOT suppress any other check. In particular it MUST NOT suppress reading `.specify/integration.json`, nor the delegated `specify self check` — which makes a GitHub request of its own that is Spec Kit's to manage, and which degrades to an "unknown" verdict by itself when offline.
- **FR-017**: When `specify` is not on PATH, the Specify CLI and Core agents checks MUST report "unknown" rather than causing a crash or preventing Spectra CLI and Spectra agents checks from running.
- **FR-018**: When `.specify/integration.json` is missing or malformed, the Core agents check MUST report "unknown" with a brief explanation rather than blocking other checks.
- **FR-019**: The help text describing `version` and `update` MUST reflect their new unified behavior rather than the old extension-only behavior.
- **FR-020**: The Tool commands panel in `--help` output MUST show only `cli uninstall`; `cli version` and `cli update` MUST be removed.
- **FR-021**: When all components are already up to date, `spectra update` MUST report the status table and exit 0 without prompting.
- **FR-022**: `spectra version` MUST require a Spec Kit project with Spectra installed. Outside a Spec Kit project it MUST exit EXIT_PROJECT_STATE (5) pointing at `specify init`; inside one without Spectra installed it MUST exit EXIT_PROJECT_STATE (5) pointing at `spectra install`. It MUST NOT report a partial subset of components in those states.
- **FR-023**: `spectra update` MUST NOT attempt to update a component whose status is "unknown". Such components MUST be reported as skipped with the reason the status could not be determined, and MUST NOT contribute to a non-zero exit code.
- **FR-024**: A component whose status is "unknown" MUST NOT appear in the list of components presented for confirmation, since it is not being updated.
- **FR-025**: The health check MUST resolve the Specify CLI status before the Core agents status, because the Core agents verdict depends on it. When the Specify CLI status is unknown, the Core agents status MUST also be reported as unknown rather than guessed from the integration file alone.
- **FR-026**: When a component's latest version cannot be resolved, the health check MUST still report that component's locally-readable installed version alongside the "unknown" status, and MUST NOT fail the whole command.
- **FR-027**: `spectra update` MUST distinguish "nothing to update because every component is current" from "nothing to update because no component's status could be determined". It MUST NOT report that everything is up to date when no component was successfully checked. When at least one component is unknown and none needs updating, it MUST name the unknown components and say that they could not be checked, while still exiting 0.

### Key Entities

- **Component Status**: Represents the health of one stack component — includes component name, installed version, latest version, comparison status (one of the four values in FR-002), and an explanatory detail, which is required whenever the status is "unknown".
- **Health Report**: An aggregate of exactly four Component Status objects in a fixed order, representing the full-stack health at a point in time. A component that could not be checked appears as "unknown" rather than being omitted, so the report always has four entries.
- **Update Result**: The outcome of attempting to update one component — updated, failed (with actionable detail), or skipped (already current, ahead, or status undeterminable).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer can determine the status of all four Spectra stack components in a single command invocation.
- **SC-002**: A developer can bring all out-of-date components current in a single command invocation with one confirmation prompt.
- **SC-003**: Partial failures during update do not prevent other components from being updated — the system always attempts every component whose status is known to be out of date, regardless of earlier outcomes.
- **SC-004**: Running a retired command (`spectra cli version` or `spectra cli update`) produces a clear, actionable error naming the replacement within one second.
- **SC-005**: All existing tests pass with modifications for the new behavior.
- **SC-006**: New test coverage covers the health check module, edge cases (missing specify, malformed integration.json, network failures), and partial failure scenarios.

## Assumptions

- `specify self check` exists, runs without requiring network credentials, and outputs parseable information covering both the installed CLI version and whether a newer release is available (this is a Spec Kit CLI feature available in the version pinned by this project).
- `specify integration upgrade` exists as a Spec Kit CLI command for updating the integration.
- `specify self upgrade` exists as a Spec Kit CLI command for updating the Specify CLI itself.
- The `version` field in `.specify/integration.json` records the Spec Kit version used to install/upgrade the integration, and it tracks the Specify CLI version — which is what makes "the CLI is behind" sufficient to conclude "the integration is behind".
- The existing behaviors this feature composes — resolving the newest published Spectra CLI release, reinstalling the CLI at a given release, reading the published extension version, comparing two versions, and delegating an extension update to Spec Kit — continue to work as they do today.
- The update order (Specify CLI → Integration → Spectra CLI → Spectra agents) is correct because later steps may depend on earlier ones being current.
- Zero third-party dependencies remain the constraint — no YAML parser or other libraries are introduced.
