# Feature Specification: Multi-Integration Stack Updates

**Feature Branch**: `010-multi-integration-updates`

**Created**: 2026-08-19

**Status**: Draft

**Input**: BRD-006 — `brds/multi-integration-updates.md` ("Multi-Integration Stack Updates")

## Clarifications

### Session 2026-08-19

- Q: What should the flag that authorizes overwriting modified managed files be called? → A: **`--force`**,
  matching the dependency's own vocabulary — a user who has seen Spec Kit's "use `--force` to overwrite
  modified files" message reaches for the same word. The known cost is that `spectra uninstall` already
  uses force to mean "suppress a confirmation", so one word now carries two weights across the CLI. That
  is mitigated rather than accepted silently: the flag's help text and the disclosure it accompanies MUST
  state that it overwrites modified files (FR-028), so its meaning is never inferred from the name alone.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The report tells the truth about every installed integration (Priority: P1)

A developer works in a project that has two coding-agent integrations installed — one marked as the
project default, one not. They run `spectra version`. Today the "Core agents" row is decided from a
single project-level record that is rewritten whenever *any* integration is upgraded, so the row can
report "up to date" while the non-default integration is still on an older version. This story makes
the row reflect every installed integration, so a green row means every agent in the project is
current, and a behind row names which integrations are behind.

**Why this priority**: This is the foundational change and the one that ends the silent drift. It is
independently valuable: even with no change to how updates run, the developer can see the true state
and act on it manually. Every other story in this feature depends on this detection being right.

**Independent Test**: In a project with two integrations installed where only the default is current,
run `spectra version` and confirm "Core agents" reports needs-updating, shows the oldest version
found, and names the behind integration. Then bring both current and confirm the row reports up to
date with no extra output.

**Acceptance Scenarios**:

1. **Given** two integrations installed and only the default is current, **When** the developer runs `spectra version`, **Then** "Core agents" reports "needs updating", shows the oldest installed version and the target version, and names the integration that is behind.
2. **Given** two integrations installed and both current, **When** the developer runs `spectra version`, **Then** "Core agents" reports "up to date" and no per-integration breakdown is printed.
3. **Given** exactly one integration installed, **When** the developer runs `spectra version`, **Then** the output is identical to the previous release's output, with no added lines.
4. **Given** two integrations installed at different versions, **When** the report is rendered, **Then** the "Core agents" row is followed by one line per integration showing its own version and status.
5. **Given** the shared Spec Kit infrastructure has its own record stored alongside the per-integration records, **When** integrations are enumerated, **Then** it is not counted, named, or reported as an integration.
6. **Given** one installed integration's version cannot be established, **When** the report is rendered, **Then** that integration is reported as unknown with the reason, and no verdict is guessed for it.
7. **Given** no installed integration's version can be established, **When** the report is rendered, **Then** "Core agents" reports unknown with a reason and does **not** report up to date.
8. **Given** one integration is ahead of the installed tool version and another is behind it, **When** the report is rendered, **Then** "Core agents" reports needs-updating rather than ahead.
9. **Given** the project records no installed integrations at all, **When** the report is rendered, **Then** "Core agents" reports unknown with a reason rather than up to date.
10. **Given** the whole stack is current, **When** the report is rendered, **Then** the report still presents exactly four components.

---

### User Story 2 - One update brings every installed integration current (Priority: P1)

A developer whose report shows "Core agents" behind runs `spectra update`. Today only the project's
default integration is upgraded and the others are left stale with no mention. This story upgrades
every installed integration that is behind, in one run, and reports the outcome for each — without
changing which agent the project targets. It replaces a four-step manual sequence (switch the default,
upgrade, switch back, upgrade) that users were never told about.

**Why this priority**: Equal to Story 1 — together they are the feature. Story 1 makes the state
visible; this makes it fixable in one command, which is the promise `spectra update` already makes for
the other three components.

**Independent Test**: In a project with two integrations installed and both behind, run
`spectra update`, confirm once, and verify both integrations are current afterwards, that each is
reported individually, and that the project's default integration is unchanged.

**Acceptance Scenarios**:

1. **Given** two installed integrations both behind, **When** `spectra update` completes, **Then** both are current and re-running `spectra version` reports "Core agents" up to date.
2. **Given** one integration behind and one current, **When** `spectra update` runs, **Then** only the behind integration is upgraded and the current one is reported as skipped with the reason.
3. **Given** integrations that will be upgraded, **When** the confirmation plan is listed, **Then** it names each integration to be upgraded and its version transition.
4. **Given** any update run, **When** it completes, fails, or is interrupted, **Then** the project's recorded default integration is unchanged from what it was before the run.
5. **Given** the upgrade of one integration fails, **When** the run continues, **Then** the remaining integrations are still attempted, and the failure is reported against the integration that failed with actionable detail.
6. **Given** every attempted integration upgrade succeeds, **When** the run finishes, **Then** the command exits 0.
7. **Given** any attempted integration upgrade fails, **When** the run finishes, **Then** the command exits EXIT_DELEGATION (4).
8. **Given** an integration upgrade reports success but that integration's recorded version did not move, **When** results are rendered, **Then** it is reported as "reported success, but the version is unchanged" rather than as an update.
9. **Given** the developer interrupts the run while a second integration is being upgraded, **When** the interrupt is received, **Then** no further integration is attempted, what completed is reported, and the command exits 130.
10. **Given** an integration whose state is unknown, **When** the run executes, **Then** it is not attempted, is reported as skipped, and does not affect the exit code.
11. **Given** an update run completes, **When** the project's shared configuration is inspected, **Then** it remains aligned with the project's default integration.
12. **Given** three installed integrations of which two are behind, **When** the run completes, **Then** both behind integrations were upgraded and each of the three has its own reported outcome.

---

### User Story 3 - Nothing is overwritten without an informed yes (Priority: P2)

A developer runs `spectra update` in a project whose managed files have diverged from what was
installed — for example customized spec, plan, or tasks templates. The upgrade is blocked by design in
that situation, and today the developer sees only "failed" with no explanation and no way forward.
This story detects the divergence first, shows exactly which files would be overwritten, asks once,
and proceeds only for the integrations the developer authorized.

**Why this priority**: It converts the current dead end into a decision, and it is the safeguard that
makes Story 2 safe to run in real projects. It ranks below Stories 1 and 2 because it applies only to
projects that have modified managed files — but for those projects nothing works without it.

**Independent Test**: In a project with modified managed files, run `spectra update`, confirm the exact
files are listed grouped by integration and shared infrastructure, decline, and verify nothing was
overwritten and the run was not reported as a failure. Repeat, consent, and verify the upgrade
completes.

**Acceptance Scenarios**:

1. **Given** an integration that is behind and has modified managed files, **When** `spectra update` runs interactively, **Then** the exact file paths are listed before any question is asked, grouped per integration and — separately — as shared Spec Kit infrastructure.
2. **Given** the disclosure is shown, **When** the developer accepts the default answer without typing, **Then** nothing is overwritten.
3. **Given** the disclosure is shown, **When** the developer declines, **Then** integrations that needed no overwrite are still upgraded, the others are reported as skipped, and the run is not reported as a failure on that account.
4. **Given** one of two behind integrations has modified files, **When** the developer consents, **Then** the overwrite is applied only to that integration and the other is upgraded without it.
5. **Given** the developer declines, **When** the outcome is reported, **Then** the message states the options actually available and does not advise reviewing a difference the command cannot display.
6. **Given** consent is given, **When** the run completes, **Then** the only shared infrastructure files overwritten are ones that were named in the disclosure.
7. **Given** an integration that is already current but has modified managed files, **When** `spectra update` runs, **Then** no disclosure is shown and no question is asked, because that integration is not being upgraded.
8. **Given** shared Spec Kit infrastructure is modified while every installed integration is current, **When** `spectra update` runs, **Then** nothing is overwritten and no question is asked.
9. **Given** a project where no managed files are modified, **When** `spectra update` runs, **Then** no disclosure and no additional question appear, and the run behaves as it does today.
10. **Given** consent was given in a previous run, **When** a later run needs an overwrite again, **Then** the developer is asked again — the authorization is never remembered.
11. **Given** consent is given and the upgrade still fails for another reason, **When** results are rendered, **Then** the failure is reported against that integration and the remaining integrations are still attempted.

---

### User Story 4 - Automation cannot destroy local work (Priority: P2)

A CI job or scripted maintenance run executes `spectra update --yes` with no terminal attached.
Approving the update plan must never double as approving the discarding of a team's modified files, so
the run updates what it can, skips what would require an overwrite, and names `--force` as the flag
that would authorize it.

**Why this priority**: It protects the case where nobody is watching, and it keeps the existing
non-interactive contract intact. Lower than Stories 1–2 because it is a constrained variant of Story 3
rather than new capability.

**Independent Test**: With no terminal attached and modified managed files present, run
`spectra update --yes` and verify no file was overwritten, the affected integrations are reported as
skipped, `--force` is named, and the process did not wait for input.

**Acceptance Scenarios**:

1. **Given** modified managed files and `--yes` with no terminal attached, **When** the run completes, **Then** no file was overwritten, the affected integrations are reported as skipped, and the output names `--force` as the flag that would authorize the overwrite.
2. **Given** `--force` is passed with no terminal attached, **When** the run completes, **Then** the overwrite proceeds and the disclosure of affected files is still printed.
3. **Given** integrations were skipped for want of overwrite authorization, **When** the process exits, **Then** the exit status does not indicate failure.
4. **Given** no terminal attached and an overwrite would be required, **When** the run executes, **Then** it does not block waiting for input.
5. **Given** `--force` is passed while no integration requires an overwrite, **When** the run completes, **Then** the flag changes nothing and no additional files are written.

---

### User Story 5 - The agent-coverage gap is visible (Priority: P3)

A developer joins a shared repository, uses the non-default agent, and finds no Spectra commands in it
while a colleague on the default agent has them all. This is silent today. This story reports the gap
below the four-component report, names the exact command that would fix it, and states that the
command changes the project's default integration for everyone — without running it.

**Why this priority**: Purely informational and lower value than making the stack current, but it
explains a genuinely baffling situation at almost no cost. It is independently testable and shippable
after the detection work in Story 1.

**Independent Test**: In a project with two integrations installed where Spectra commands are
registered for only one, run `spectra version` and confirm the advisory names the uncovered
integration, the remedy, and the side effect, and that nothing was changed.

**Acceptance Scenarios**:

1. **Given** two integrations installed and Spectra commands registered for one, **When** `spectra version` runs, **Then** an advisory below the report names the uncovered integration, gives the exact remedy command, and states that it changes the project's default integration.
2. **Given** every installed integration has Spectra commands registered, **When** `spectra version` runs, **Then** no advisory appears.
3. **Given** the advisory is shown, **When** the run completes, **Then** no agent configuration was changed and the exit code is unaffected.
4. **Given** the registration state cannot be read, **When** `spectra version` runs, **Then** no advisory is shown and no coverage is guessed at.
5. **Given** exactly one integration is installed, **When** `spectra version` runs, **Then** no advisory appears.

---

### Edge Cases

- **No integrations recorded**: the project records an empty installed list, or the record is missing or unreadable → "Core agents" reports unknown with a reason; nothing is attempted.
- **Recorded but unverifiable**: an integration appears in the installed list but has no readable version record → that integration reports unknown; other integrations still report normally.
- **Shared record only**: the shared Spec Kit infrastructure record exists but no integration records do → it is not mistaken for an integration; "Core agents" reports unknown.
- **Mixed verdicts**: one integration ahead, one behind, one unknown → the row reports needs-updating, names only the behind one as needing an update, and the unknown one is never attempted.
- **No default recorded**: the project records installed integrations but no default → integrations are still reported; the run does not invent a default, and the coverage advisory is suppressed.
- **Modified files on a current integration**: divergence exists but no upgrade is needed → no disclosure, no question, no overwrite.
- **Very large divergence**: every managed file in the project is modified → all affected files are still disclosed before the question is asked.
- **Older dependency**: the machine-readable status or per-integration records are unavailable → behaviour falls back to the previous single-integration reporting rather than reporting unknown, so no capability is lost.
- **Interrupt mid-run**: the developer interrupts between two integration upgrades → the completed one stays upgraded, the other is untouched, the default is unchanged, and the next run resumes from the reported state.
- **Success without movement**: an upgrade exits successfully but the integration's recorded version does not change → reported as unchanged, not as an update.
- **Registration state unreadable**: the record of which integrations have Spectra commands cannot be read → the coverage advisory is omitted entirely.
- **Consent declined every run**: a project stays mixed-version indefinitely → each run still reports the skipped integrations and their versions, and still updates everything else.

## Requirements *(mandatory)*

### Functional Requirements

**Enumeration and per-integration currency**

- **FR-001**: System MUST enumerate the project's installed integrations from the recorded installed-integrations list.
- **FR-002**: System MUST NOT treat the shared Spec Kit infrastructure record as an installed integration, and MUST NOT infer integration membership from the set of records present on disk.
- **FR-003**: System MUST determine each installed integration's recorded version individually.
- **FR-004**: System MUST NOT determine "Core agents" currency from the single project-level version record while per-integration records are readable; that record MAY be used only as a fallback when no per-integration record can be read.
- **FR-005**: System MUST report an integration whose version cannot be established as unknown, with a reason, and MUST NOT act on it.

**Reporting**

- **FR-006**: "Core agents" MUST report "needs updating" when any installed integration is behind, and MUST report "up to date" only when every installed integration is current.
- **FR-007**: The "Core agents" row MUST show the oldest **readable** version among the installed integrations, alongside the target version. An integration whose version cannot be read contributes no version to that comparison; it is reported through FR-005 instead.
- **FR-008**: The "Core agents" row MUST name the integrations that are behind.
- **FR-009**: "Core agents" MUST report "ahead" only when every installed integration is ahead of the installed tool version.
- **FR-010**: "Core agents" MUST report unknown when no installed integration's state can be established, and MUST NOT report up to date in that case.
- **FR-011**: The report MUST continue to present exactly four components.
- **FR-012**: For a project with exactly one installed integration, the output of `spectra version` and `spectra update` MUST be unchanged from the previous release.
- **FR-013**: A per-integration breakdown MUST be shown only when more than one integration is installed and their versions or statuses differ.

**Updating**

- **FR-014**: `spectra update` MUST upgrade every installed integration that is behind, within a single run.
- **FR-015**: `spectra update` MUST NOT act on an integration that is already current, ahead, or unknown, and MUST report each as skipped with the reason.
- **FR-016**: The confirmation plan MUST name every integration that will be upgraded, with its version transition.
- **FR-017**: System MUST NOT change the project's default integration, or any other agent-targeting project configuration, at any point during a run — including transiently.
- **FR-018**: After a run, the project's shared configuration MUST remain aligned with the project's default integration.
- **FR-019**: A failed integration upgrade MUST NOT prevent the remaining integrations from being attempted.
- **FR-020**: An explicit user interrupt MUST stop the run without attempting further integrations, MUST report what completed, and MUST exit 130.
- **FR-021**: Each integration MUST have its own reported outcome — updated, failed with actionable detail, or skipped with a reason.
- **FR-022**: After updating, each upgraded integration's recorded version MUST be re-read, and an upgrade that reported success without moving the version MUST be reported as unchanged rather than as an update.
- **FR-023**: The command MUST exit EXIT_DELEGATION (4) when any attempted integration upgrade failed, and skipped integrations MUST NOT contribute to the exit code.

**Overwrite consent**

- **FR-024**: Before attempting any upgrade, System MUST determine which integrations have modified managed files.
- **FR-025**: System MUST disclose the exact file paths that would be overwritten, grouped per integration and — separately — as shared Spec Kit infrastructure, because authorizing the overwrite for one integration also overwrites shared infrastructure.
- **FR-026**: Overwriting MUST require explicit authorization, obtained once per run, and the interactive prompt MUST default to declining.
- **FR-027**: Approving the update plan (`--yes`) MUST NOT be treated as authorization to overwrite modified files.
- **FR-028**: The overwrite MUST be authorized by an explicit `--force` flag on `spectra update`, which MUST work in non-interactive runs. Because `--force` means "suppress a confirmation" elsewhere in the CLI, its help text and the disclosure it accompanies MUST state that it overwrites modified files.
- **FR-029**: The overwrite MUST be applied only to the integrations that require it; an integration that can be upgraded without it MUST NOT be overwritten.
- **FR-030**: Where authorization is declined or unavailable, System MUST still upgrade the integrations that need no overwrite, MUST report the others as skipped with the options available, and MUST NOT report the run as failed on that account.
- **FR-031**: A non-interactive run MUST NOT block waiting for input when an overwrite would be required.
- **FR-032**: When the overwrite is authorized by `--force` in a non-interactive run, the disclosure MUST still be printed.
- **FR-033**: Authorization MUST NOT be persisted as a setting or remembered between runs.
- **FR-034**: An integration that is not being upgraded MUST NOT trigger a disclosure or a prompt, even when it has modified managed files.
- **FR-035**: User-facing messages MUST state the options actually available, and MUST NOT advise reviewing a difference that the command cannot display.

**Coverage advisory**

- **FR-036**: System SHOULD detect installed integrations that have no Spectra commands registered for them.
- **FR-037**: When an advisory is shown, it MUST name the uncovered integration, give the exact remedy command, and state that the remedy changes the project's default integration.
- **FR-038**: When an advisory is shown, it MUST be rendered outside the four component rows and MUST NOT affect the exit code. No advisory MUST be shown when every installed integration is covered.
- **FR-039**: When the registration state cannot be read, no advisory MUST be shown and coverage MUST NOT be guessed.

**Boundaries**

- **FR-040**: System MUST NOT scaffold or register commands for integrations that are not the project's default.
- **FR-041**: Machine decisions MUST be based on machine-readable dependency output and recorded project state; human-formatted output MUST NOT be parsed where a machine-readable form exists.
- **FR-042**: The detection and update behaviour of the other three components — Specify CLI, Spectra CLI, and Spectra agents — MUST remain unchanged.

### Key Entities

- **Installed integration**: One coding-agent integration recorded as installed in the project. Has a key, a recorded version, a modification state, and a flag for whether it is the project default.
- **Integration currency**: The verdict for a single installed integration — current, behind, ahead, or unknown — with the reason when unknown.
- **Core agents status**: The aggregate presented in the report's third row: one verdict derived from every installed integration's currency, the oldest version found, the target version, and the names of the integrations that are behind.
- **Modification report**: For each integration, and separately for shared Spec Kit infrastructure, the list of managed files that diverge from what was installed.
- **Overwrite authorization**: A single per-run decision, obtained interactively or by `--force`, recording that overwriting the disclosed files is permitted. Never persisted.
- **Integration update outcome**: Per integration — updated, failed with detail, or skipped with a reason — plus the version re-read after the attempt.
- **Coverage gap**: An installed integration for which no Spectra commands are registered.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In a project with any number of installed integrations, a single `spectra update` (with authorization given where required) leaves every installed integration current, confirmed by re-running `spectra version`.
- **SC-002**: Zero occurrences of "Core agents" reporting up to date while an installed integration is behind.
- **SC-003**: Zero files are overwritten in any run without an explicit authorization act performed in that same run.
- **SC-004**: The number of commands a developer must run to bring a two-integration project current drops from four to one.
- **SC-005**: For projects with a single installed integration, the output of `spectra version` and `spectra update` is unchanged line for line from the previous release.
- **SC-006**: A project that cannot be updated at all today ends every run either fully updated or updated with explicitly declared skips — zero unexplained failures.
- **SC-007**: Non-interactive runs overwrite zero files unless `--force` is passed, and their exit status reflects only work that was attempted.
- **SC-008**: 100% of installed integrations lacking Spectra commands are named in the report, each with a remedy the developer can run verbatim.
- **SC-009**: A developer can determine which integrations are behind, and by how much, from one command run without inspecting any project file by hand.

## Assumptions

- The project's recorded installed-integrations list is the authoritative membership set; a per-integration record existing on disk is not by itself evidence that an integration is installed.
- Each installed integration records its own version locally, so per-integration currency is determinable without network access.
- Where the dependency cannot supply per-integration state (an older version than this feature targets), behaviour falls back to the previous single-integration reporting rather than reporting unknown — losing capability that exists today would be worse than reporting less detail.
- Whether a modified managed file is a deliberate customization or accumulated drift is indistinguishable to Spectra, so both are treated as the team's property and protected identically.
- The coverage advisory is added to `spectra version` only. `spectra check` answers a narrower question — whether Spectra is installed here — and is left unchanged.
- The overwrite authorization is strictly a modifier of an update that is already needed; it never triggers work on its own, so passing it when nothing is behind does nothing.
- All disclosed files are listed in full rather than truncated; observed divergences are in the tens of files, which is readable.
- Reporting "Core agents" as behind when only a non-default integration is stale is intended, even though the agent the developer is actively using is current — a green row must mean the whole project is current. The alternative (report only on the default) was considered and rejected as reintroducing the silent drift this feature exists to remove.
- Single-integration projects are the large majority, which is why the feature must add no output, prompts, or steps for them.
- Presets follow the same activation model as extension commands and remain the dependency's responsibility.
