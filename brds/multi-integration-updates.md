# Business Requirements Document (BRD): Multi-Integration Stack Updates

## Document Control

| Field             | Value                                                                                                                                                                                                          |
| ----------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| BRD ID            | BRD-006                                                                                                                                                                                                        |
| Title             | Multi-Integration Stack Updates                                                                                                                                                                                |
| Author            | Spectra / TELUS Digital                                                                                                                                                                                        |
| Status            | Draft                                                                                                                                                                                                          |
| Version           | 0.1.0                                                                                                                                                                                                          |
| Created           | 2026-08-19                                                                                                                                                                                                     |
| Last updated      | 2026-08-19                                                                                                                                                                                                     |
| Related documents | `.specify/memory/constitution.md`, `specs/007-unified-version-update/spec.md`, `specs/007-unified-version-update/contracts/health-check.md`, `specs/007-unified-version-update/contracts/cli-surface.md`, `brds/agent-roster-and-cli-commands.md` (BRD-004), `README.md` § "Keeping everything up to date" |

## 1. Executive Summary

`spectra version` and `spectra update` report and refresh four components of the Spectra stack, and
today they get one of them wrong whenever a project has **more than one coding-agent integration
installed**. Only the project's default integration is ever considered or upgraded; the others drift
silently, and the signal Spectra reads cannot see that they have.

This feature makes "Core agents" plural-aware. `spectra version` tells the truth about **every**
installed integration, `spectra update` brings **all** of them current in one run, and where the
update would overwrite files the team has modified, the user is shown exactly what would be lost and
asked once before anything is discarded.

It is bounded by one rule: **Spectra brings versions current; it never changes which agent the
project targets.** Where the multi-install situation needs a change to project configuration to be
fully resolved, Spectra reports it with the exact command and its consequence, rather than making
that decision on the team's behalf.

## 2. Business Context & Problem Statement

Spec Kit supports installing several agent integrations into one project — a repository can carry both
`claude` and `kiro-cli`, with one of them marked as the default. This is a normal configuration for a
team where different developers use different agents, and it is the configuration Spectra's own
"works with every agent" positioning invites.

`spectra update` was designed around the premise that four things must be current for Spectra to
work, and that one command should make them so. For multi-install projects that premise is not being
met:

- **Only the default integration is upgraded.** The upgrade Spectra delegates to acts on the default
  integration when invoked without naming one. A project with two integrations gets one of them
  upgraded and no mention of the other.
- **The drift is then invisible.** The project-level record Spectra reads to decide whether "Core
  agents" is current is rewritten to the current tool version whenever *any* integration is upgraded.
  So after upgrading one of two, Spectra reports the row as up to date while the second integration
  is still on the old version. The stack is stale and the report is green.
- **The manual workaround is undocumented and fiddly.** Today the only way through is to switch the
  project default to each integration in turn, upgrade, and switch back — a multi-step sequence that
  mutates committed project configuration, that nobody is told about, and that is easy to abandon
  half-finished.
- **The update can dead-end entirely.** Where managed files have diverged from what was installed,
  the upgrade refuses to run by design. `spectra update` surfaces that as a plain failure with no
  path forward: the user is told the component failed, not what diverged or what their options are.
  In a real project measured for this BRD, that is the current state — the update cannot complete at
  all.
- **A second, quieter gap sits next to it.** Spectra's own commands are registered for the default
  integration only. A developer on the same repository using the non-default agent has no Spectra
  commands and nothing explains why.

The cost is trust in the one command whose entire job is to answer "is my stack current?". A wrong
"yes" is worse than a missing answer, and a failure with no remedy trains users to stop running the
command.

### 2.1 Verified findings

Observed 2026-08-19 against Spec Kit CLI 0.16.5 and two real projects — `willow` (drifted) and this
repository (clean). These are behaviours of the dependency and of recorded project state, not of
Spectra's internals, and they are what the requirements below are built on.

| # | Finding | How it was established | Consequence |
| - | ------- | ---------------------- | ----------- |
| F1 | The integration upgrade, invoked without naming an integration, resolves to the project's **default** integration only. | Dependency source inspection. | Non-default integrations are never upgraded by `spectra update`. |
| F2 | Upgrading **any** single integration rewrites the project-level version record to the current tool version. | Dependency source inspection. | The single field Spectra reads today cannot represent a stale second integration. Per-integration versions are recorded separately, one per integration. |
| F3 | The upgrade **accepts an explicit integration name**, and upgrading a non-default one is supported without changing the default. | Dependency command surface and source inspection. | All installed integrations can be brought current without touching project configuration. |
| F4 | Re-registration of extension and preset commands happens **only** when the integration being upgraded is the default. Inactive integrations are deliberately left until they are activated. | Dependency source inspection, upstream issue reference in that code. | Spectra commands exist for the default integration only; there is no supported way to scaffold a non-default one except by changing the default. |
| F5 | The upgrade is **blocked** when managed files for that integration diverge from what was installed, and the block is lifted only by an explicit overwrite. | Dependency source inspection and its own on-screen message. | Some projects cannot be updated at all today without an overwrite decision being made by a human. |
| F6 | The overwrite is **not scoped to the files that caused the block** — it also overwrites shared Spec Kit infrastructure, "including customizations". | Dependency source inspection and its own flag documentation. | Any disclosure to the user must include shared templates and scripts, not only the offending integration's files. |
| F7 | The integration **status report is read-only and always succeeds**, including when it reports a warning. Its machine-readable form lists modified files per integration. | Executed in both projects; exit status 0 in every case. | The warning is not the trigger to act on; per-integration modification lists are, and they are available without guesswork. |
| F8 | The shared-infrastructure record lives alongside the per-integration records but is **not an integration**. | Compared recorded installed integrations against the set of records present. | The set of integrations must be taken from the recorded installed list, never inferred from the records on disk. |
| F9 | There is **no way to see what diverged**. The dependency offers no comparison command, and in the measured project the divergence is already committed to version control, so ordinary version-control tooling shows nothing. | Dependency command surface; version-control inspection in `willow`. | "Review the changes first" is not actionable advice and must not be repeated to users as if it were. |

Measured state of the drifted project (`willow`): tool at 0.16.5, project recorded at 0.15.1, two
integrations installed with `kiro-cli` as default, **23 modified managed files** (10 for `kiro-cli`,
10 for `claude`, 3 shared templates — the spec, plan, and tasks templates). Spectra commands are
present for `kiro-cli` and absent for `claude`. The clean project shows the same two-integration
layout with both current and nothing modified, confirming that neither drift nor divergence is
inherent to multi-install.

## 3. Business Objectives & Goals

- **G1 — Never report a stale stack as current.** "Core agents" must reflect every installed
  integration, so a green row means every agent in the project is current.
- **G2 — One command, all integrations.** A single `spectra update` brings every installed
  integration current, with no manual switching sequence and no knowledge of the workaround required.
- **G3 — No silent loss of a team's work.** Where updating would overwrite modified files, the user
  sees exactly which files and decides. Consent is explicit, per run, and never inferred.
- **G4 — Keep project configuration under the team's control.** Spectra updates versions; it does not
  change which agent a project targets, and does not scaffold agents the team has not activated.
- **G5 — Turn a dead end into a decision.** A project that cannot be updated today must end up either
  updated or told, in plain terms, what the two real options are.
- **G6 — Cost the majority nothing.** Projects with a single integration must see no new output, no
  new prompts, and no new steps.
- **G7 — Surface the coverage gap honestly.** Where installed integrations lack Spectra commands, say
  so, name the remedy, and state its side effect — without performing it.

## 4. Stakeholders & Users

| Stakeholder / user                       | Role in this product | What they need from it                                                                                                        |
| ---------------------------------------- | -------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| Developer in a multi-agent project       | Primary user         | A truthful currency report and one command that makes every installed integration current, without learning a manual workaround. |
| Developer in a single-agent project      | Primary user         | Exactly today's behaviour and output — no new noise, prompts, or steps.                                                        |
| Team that has customized templates       | Affected party       | To be told precisely what would be overwritten, and to have the option to keep it, before anything is discarded.               |
| Automation / CI running the update       | Secondary consumer   | Deterministic, non-destructive behaviour with no prompt to answer, and an exit code that reflects only what was attempted.      |
| Engineering leads                        | Oversight            | Confidence that a green stack report is trustworthy and that a maintenance command cannot quietly destroy committed work.       |
| Spec Kit CLI and recorded project state  | Dependency (input and action) | The source of installed integrations, their recorded versions, and modification state; and the executor of every upgrade. |

## 5. Scope

### 5.1 In Scope

- **Per-integration currency.** Determine, for every installed integration, whether it is current,
  behind, ahead, or unestablished — rather than deriving one verdict from a single project-level
  record.
- **Truthful "Core agents" reporting.** The row is behind when any installed integration is behind,
  shows the oldest version found, and names the integrations that are behind.
- **Updating every behind integration** in one `spectra update`, skipping the ones already current.
- **Detection and disclosure of modified managed files** before anything is attempted, grouped by
  integration and, separately, shared Spec Kit infrastructure.
- **Explicit overwrite consent**: a prompt that defaults to *no*, an explicit flag for non-interactive
  use, and overwriting limited to the integrations that require it.
- **Graceful partial progress.** Integrations that need no overwrite are updated even when consent for
  the others is withheld or unavailable; the rest are reported as skipped with the exact remedy.
- **Per-integration outcome reporting**, with post-update verification that each integration's
  recorded version actually moved.
- **An advisory** when installed integrations have no Spectra commands, naming the command that would
  fix it and stating that it changes the project's default integration.

### 5.2 Out of Scope

- **Changing the project's default integration.** Not as an end state and not transiently. That
  setting is committed project configuration owned by the team.
- **Scaffolding or registering commands for non-default integrations.** The dependency deliberately
  defers this until an integration is activated (F4); Spectra reports the gap instead of working
  around it. A future opt-in capability may revisit this — it is not part of this feature.
- **Showing what diverged.** No comparison of modified files against their original content (F9).
  A separate capability could own this; today the honest position is that the divergence cannot be
  displayed.
- **Preset handling.** Presets follow the same activation model as extensions and are the
  dependency's responsibility.
- **Any new top-level Spectra command.** This is a behavioural change inside `spectra version` and
  `spectra update`.
- **Repairing the divergence itself.** Spectra offers overwrite-or-leave; it does not merge,
  reconcile, or back up the modified files beyond what the dependency already does.
- **The other three components** (Specify CLI, Spectra CLI, Spectra agents). Their detection and
  update paths are unchanged.

## 6. User Journeys *(feeds the spec's prioritized user stories)*

### Journey 1 — The report tells the truth about every integration (Priority: P1)

- **Actor:** Developer in a project with two integrations installed.
- **Trigger:** Runs `spectra version`.
- **Outcome / value:** Learns that a non-default integration is behind — information that is
  currently unobtainable. Valuable on its own: even with no change to updating, the silent drift ends
  and the manual remedy becomes possible.
- **Flow:**
  1. The developer runs `spectra version` in a project with `claude` and `kiro-cli` installed, one of
     them behind.
  2. The four-component report is rendered as today.
  3. The "Core agents" row reports "needs updating", shows the oldest version found and the target,
     and names the integrations that are behind.
  4. Where more than one integration is installed and their versions differ, the row is followed by a
     per-integration breakdown.
- **Acceptance:**
  - **Given** two integrations installed and only the default is current, **When** `spectra version`
    runs, **Then** "Core agents" reports needs-updating and names the behind integration.
  - **Given** two integrations installed and both current, **When** `spectra version` runs, **Then**
    "Core agents" reports up to date with no per-integration breakdown.
  - **Given** exactly one integration installed, **When** `spectra version` runs, **Then** the output
    is identical to today's, with no added lines.
  - **Given** the version of one installed integration cannot be established, **When** the report is
    rendered, **Then** the row reports unknown with the reason, and no verdict is guessed.
  - **Given** shared Spec Kit infrastructure has its own record alongside the integrations, **When**
    integrations are enumerated, **Then** it is not counted or reported as an integration.

### Journey 2 — One update brings every installed integration current (Priority: P1)

- **Actor:** Developer maintaining a multi-agent project.
- **Trigger:** Runs `spectra update` after `spectra version` reports "Core agents" behind.
- **Outcome / value:** Every installed integration is upgraded in one run, with no switching sequence
  and no residual stale agent. Replaces a multi-step manual workaround the user was never told about.
- **Flow:**
  1. The developer confirms the update plan, which names the integrations that will be upgraded.
  2. Each behind integration is upgraded; integrations already current are not touched.
  3. The project's default integration remains exactly as it was, before and after.
  4. Each integration's outcome is reported, and the recorded versions are re-read to confirm they
     moved.
  5. Re-running `spectra version` reports "Core agents" up to date.
- **Acceptance:**
  - **Given** two installed integrations both behind, **When** `spectra update` completes, **Then**
    both are current and the report confirms it.
  - **Given** one integration behind and one current, **When** `spectra update` runs, **Then** only
    the behind one is upgraded and the current one is reported as skipped.
  - **Given** any update run, **When** it finishes or is interrupted, **Then** the project's default
    integration is unchanged.
  - **Given** an upgrade of one integration fails, **When** the run continues, **Then** the remaining
    integrations are still attempted and the failure is reported against the integration that failed.
  - **Given** an upgrade reports success but the recorded version did not move, **When** results are
    rendered, **Then** that is stated plainly rather than reported as an update.
  - **Given** the user interrupts the run, **When** the interrupt is received, **Then** the run stops
    rather than proceeding to the next integration, and what completed is reported.
  - **Given** an update run completes, **When** shared project configuration is inspected, **Then** it
    remains aligned with the default integration.

### Journey 3 — Nothing is overwritten without an informed yes (Priority: P2)

- **Actor:** Developer in a project whose managed files have been modified.
- **Trigger:** Runs `spectra update` where the upgrade would be blocked by those modifications.
- **Outcome / value:** Instead of an unexplained failure, the developer sees exactly which files would
  be overwritten and decides. This is the difference between an update that dead-ends and one that
  completes on the user's terms.
- **Flow:**
  1. Before attempting anything, Spectra determines which integrations have modified managed files.
  2. The disclosure lists the files, grouped per integration and — separately — shared Spec Kit
     infrastructure, because the overwrite is not scoped to the files that caused the block (F6).
  3. One question is asked, covering everything disclosed, defaulting to no.
  4. On yes: overwriting is applied only to the integrations that require it; integrations that need
     no overwrite are upgraded normally.
  5. On no: integrations needing no overwrite are still upgraded; the others are reported as skipped,
     with the two real options stated plainly.
- **Acceptance:**
  - **Given** modified managed files, **When** `spectra update` runs interactively, **Then** the exact
    files are listed, grouped by integration and shared infrastructure, before any question is asked.
  - **Given** the disclosure is shown, **When** the user presses Enter without answering, **Then**
    nothing is overwritten.
  - **Given** the user declines, **When** the run continues, **Then** integrations that needed no
    overwrite are still updated, the others are reported as skipped, and the run is not reported as a
    failure.
  - **Given** one of two integrations has modified files, **When** the user consents, **Then**
    overwriting is applied only to that integration.
  - **Given** the user declines, **When** the outcome is reported, **Then** the message states the two
    available options and does not advise reviewing a difference that cannot be displayed (F9).
  - **Given** consent is given, **When** the run completes, **Then** the shared infrastructure files
    named in the disclosure are the only shared files that were overwritten.

### Journey 4 — Automation cannot destroy local work (Priority: P2)

- **Actor:** CI job or scripted maintenance run.
- **Trigger:** `spectra update --yes` with no terminal attached.
- **Outcome / value:** Predictable, non-destructive automation. Approving an update plan never doubles
  as approving the discarding of modified files.
- **Flow:**
  1. The run proceeds without prompting, as today.
  2. Integrations needing no overwrite are updated.
  3. Integrations that would require an overwrite are skipped, and the output names the explicit flag
     that would authorize it.
  4. The exit status reflects only what was attempted.
- **Acceptance:**
  - **Given** modified managed files and `--yes` with no terminal, **When** the run completes, **Then**
    no file was overwritten and the affected integrations are reported as skipped with the flag named.
  - **Given** the explicit overwrite flag is passed, **When** the run completes non-interactively,
    **Then** the overwrite proceeds and the disclosure is still printed for the record.
  - **Given** integrations were skipped for want of consent, **When** the process exits, **Then** the
    exit status does not indicate failure.
  - **Given** no terminal and no flags, **When** an overwrite would be required, **Then** the run does
    not hang waiting for input.

### Journey 5 — The agent-coverage gap is visible (Priority: P3)

- **Actor:** Developer using the non-default agent in a shared repository.
- **Trigger:** Runs `spectra version` (or joins a project and finds no Spectra commands in their
  agent).
- **Outcome / value:** An explanation and an exact remedy for a situation that is currently silent and
  baffling — Spectra commands present for one agent and absent for another in the same repository.
- **Flow:**
  1. Spectra compares the installed integrations against the integrations its commands are registered
     for.
  2. Where an installed integration has no Spectra commands, an advisory is printed below the report.
  3. The advisory names the command that would scaffold them and states that it changes the project's
     default integration for everyone.
  4. Spectra does not run that command.
- **Acceptance:**
  - **Given** two integrations installed and Spectra commands registered for one, **When**
    `spectra version` runs, **Then** an advisory names the uncovered integration, the remedy, and its
    side effect.
  - **Given** every installed integration has Spectra commands, **When** the report runs, **Then** no
    advisory appears.
  - **Given** the advisory is shown, **When** the run completes, **Then** no agent configuration was
    changed and the advisory did not affect the exit status.

## 7. Business Requirements

| ID    | Requirement                                                                                                                                                                        | Priority |
| ----- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| BR-01 | Currency for "Core agents" MUST be determined per installed integration, not from a single project-level version record.                                                            | P1       |
| BR-02 | The set of installed integrations MUST come from the project's recorded installed list; shared Spec Kit infrastructure MUST NOT be treated as an integration (F8).                  | P1       |
| BR-03 | "Core agents" MUST report as behind when any installed integration is behind, MUST show the oldest version found, and MUST name the integrations that are behind.                   | P1       |
| BR-04 | The report MUST keep its four-component shape, and output for a single-integration project MUST be unchanged.                                                                       | P1       |
| BR-05 | A per-integration breakdown MUST be shown only when more than one integration is installed and their versions differ.                                                               | P2       |
| BR-06 | `spectra update` MUST update every installed integration that is behind, and MUST NOT act on integrations already current.                                                          | P1       |
| BR-07 | Spectra MUST NOT change the project's default integration, or any other agent-targeting configuration, at any point in a run — including transiently.                               | P1       |
| BR-08 | After an update run, shared project configuration MUST remain aligned with the project's default integration.                                                                       | P2       |
| BR-09 | Before attempting any upgrade, Spectra MUST determine which integrations have modified managed files, and MUST disclose the exact files, grouped per integration and — separately — shared Spec Kit infrastructure (F6). | P2       |
| BR-10 | Overwriting modified files MUST require explicit consent, obtained once per run, defaulting to no.                                                                                  | P2       |
| BR-11 | Approving the update plan (`--yes`) MUST NOT be treated as consent to overwrite. A separate, explicitly named flag MUST be required.                                                | P2       |
| BR-12 | Overwriting MUST be limited to the integrations that require it; integrations that can be upgraded without it MUST NOT be overwritten.                                              | P2       |
| BR-13 | Where consent is withheld or unavailable, Spectra MUST still update the integrations that need no overwrite, MUST report the others as skipped with the available options, and MUST NOT report the run as failed. | P2       |
| BR-14 | A failed integration upgrade MUST NOT prevent the remaining integrations from being attempted; an explicit user interrupt MUST stop the run.                                        | P2       |
| BR-15 | Each integration's outcome MUST be reported individually, and each recorded version MUST be re-read afterwards so a success that changed nothing is reported as such.               | P2       |
| BR-16 | Spectra MUST NOT scaffold or register commands for integrations that are not the project's default.                                                                                 | P1       |
| BR-17 | Spectra SHOULD advise when an installed integration has no Spectra commands, naming the remedy and its side effect, without performing it.                                          | P3       |
| BR-18 | Any integration whose state cannot be established MUST be reported as unknown with a reason, MUST NOT be guessed at, and MUST NOT be acted on.                                      | P1       |
| BR-19 | User-facing messages MUST state the options actually available and MUST NOT advise reviewing a difference that cannot be displayed (F9).                                            | P3       |
| BR-20 | Machine decisions MUST be based on machine-readable dependency output and recorded project state; human-formatted output MUST NOT be parsed where a machine-readable form exists.    | P2       |

## 8. Success Metrics & Measurable Outcomes

- **SC-01** — In a project with any number of installed integrations, one `spectra update` (with
  consent given where required) leaves every installed integration current, confirmed by re-running
  `spectra version`.
- **SC-02** — `spectra version` never reports "Core agents" as current while an installed integration
  is behind. Zero occurrences.
- **SC-03** — Zero files are overwritten in any run without an explicit consent act recorded in that
  same run.
- **SC-04** — Manual steps required of a user to bring a two-integration project current drops from
  the current four-step switch-and-upgrade sequence to zero.
- **SC-05** — For single-integration projects, the output of `spectra version` and `spectra update` is
  unchanged, line for line.
- **SC-06** — In the measured drifted project, `spectra update` moves from "cannot complete" to either
  fully updated or updated-with-declared-skips, with no unexplained failure.
- **SC-07** — Non-interactive runs never overwrite a modified file, and their exit status reflects only
  work that was attempted.
- **SC-08** — Every installed integration lacking Spectra commands is named in the report, with a
  remedy the user can run verbatim.

## 9. Assumptions

- The project's recorded list of installed integrations is the authoritative membership set; a
  per-integration record on disk is not, by itself, evidence of an installed integration (F8).
- Each installed integration records its own version, so per-integration currency is determinable
  without network access.
- Machine-readable status, including per-integration modification lists, is available from the pinned
  Spec Kit version; where it is not, the state is treated as unestablished rather than inferred.
- Upgrading a named non-default integration is supported by the dependency and does not change the
  default (F3).
- Whether a modified managed file represents deliberate customization or accumulated drift is
  indistinguishable to Spectra, so both are treated as the team's property.
- Single-integration projects are the large majority today; multi-install is the minority case this
  feature serves, which is why it must add nothing to the majority's experience.
- Users who install a second integration intend to use both agents, which is why the coverage gap is
  worth reporting rather than ignoring.

## 10. Constraints

- **Spectra brings versions current; it never changes which agent the project targets.** This bounds
  the whole feature and is the reason the coverage gap is reported rather than fixed.
- The four-component report shape is an established contract across the existing spec, its tests, the
  README, and the docs site. A component that is now plural must be represented within those four
  rows rather than by adding a fifth.
- Overwrite granularity belongs to the dependency and is per upgrade action, not per file: authorizing
  an overwrite for one integration also overwrites shared Spec Kit infrastructure (F6). Disclosure
  must therefore be wider than the block that triggered it.
- The dependency's block on modified files exists to protect user content. Any override MUST be a
  deliberate, per-run human act; it MUST NOT be persisted as a setting, inferred from an unrelated
  flag, or defaulted on.
- Extension command registration scope is the dependency's decision (F4) and MUST NOT be worked around.
- No new top-level command; this changes the behaviour of `spectra version` and `spectra update` only.
- The minimum Spec Kit version this feature requires must be pinned, and behaviour on older versions
  defined rather than left to chance.
- No new network dependency: per-integration currency is determined from local state and the already
  established tool version.

## 11. Dependencies

- **Spec Kit CLI** — input: installed integrations, per-integration recorded versions, per-integration
  modification state, machine-readable status. Output: performs every integration upgrade. Spectra
  adds no upgrade mechanism of its own.
- **Recorded project state** (the project's integration record, per-integration records, and the
  extension registry) — input for currency, membership, and command-coverage detection.
- **`specs/007-unified-version-update`** — input: this feature amends that contract. Its stated
  decision that the overwrite flag is deliberately never passed is superseded here by a consent-gated
  path, and that supersession must be recorded rather than left contradictory.
- **The four-row report and its tests** — output: must continue to hold, extended rather than replaced.
- **`spectra check`** — potential consumer of the coverage advisory; see Open Questions.

## 12. Risks & Mitigations

| Risk                                                                                          | Impact | Likelihood | Mitigation                                                                                                                                     |
| --------------------------------------------------------------------------------------------- | ------ | ---------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| A team's customized templates are destroyed by an overwrite they did not understand.          | H      | M          | Mandatory file-level disclosure grouped by scope, one question defaulting to no, consent never inferred from `--yes`, overwrite scoped to the integrations that need it. |
| Users habituate to approving the overwrite prompt and lose work over time.                     | M      | H          | Shared infrastructure listed as its own group so customized templates are visible rather than buried; default answer is no; consent is per run, never remembered. |
| The dependency changes its status output, upgrade behaviour, or registration scope.            | M      | M          | Treat anything unestablished as unknown and act on nothing; pin the minimum Spec Kit version; keep machine decisions on machine-readable inputs. |
| Added output makes the report noisier for the single-integration majority.                      | M      | M          | Per-integration breakdown only when more than one integration is installed and versions differ; single-integration output unchanged, and asserted as such. |
| A declined overwrite leaves a project permanently mixed-version and the prompt recurs forever.  | M      | M          | Report the skipped integrations and their versions on every run, state the two real options, and keep the rest of the stack updatable meanwhile. |
| The coverage advisory is read as an error and erodes confidence in a healthy project.           | L      | M          | Advisory tone, placed outside the four rows, no effect on exit status, with the remedy and its side effect stated.                              |
| An interrupt part-way leaves some integrations upgraded and others not.                          | M      | L          | Per-integration outcomes reported; project default never changed, so the interrupted state is stale-but-consistent and the next run resumes it.  |
| The superseded "never overwrite" decision in the existing spec is left contradictory.           | L      | M          | Record the supersession explicitly as part of this feature's documentation output.                                                              |

## 13. Open Questions

- What minimum Spec Kit version should this feature require, and on an older version should
  "Core agents" fall back to today's single-integration behaviour or report unknown?
- Should the coverage advisory (Journey 5) also appear in `spectra check`, or only in
  `spectra version`? `check` currently answers a narrower question.
- What should the overwrite flag be called — reusing `--force` matches the dependency's vocabulary,
  while something like `--overwrite-modified` states the consequence. Reusing `--force` also risks
  confusion with `spectra uninstall --yes`, where force only suppresses a confirmation.
- Is the overwrite ever useful on its own, when no integration is behind — for example to reset
  modified files deliberately — or is it strictly a modifier of an update that is already needed?
- Should the disclosure cap the number of files listed for very large divergences, and if so what
  replaces the tail?
- If the default integration is current and only a non-default one is behind, is reporting
  "Core agents" as behind the desired behaviour, given that the agent the user is actively using is
  fine?
- Should a future capability display what diverged (F9), and does excluding it now leave the declined
  path acceptably actionable?

## 14. Glossary

| Term                            | Definition                                                                                                                            |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| Integration                     | A Spec Kit installation targeting one coding agent (for example `claude`, `kiro-cli`), providing that agent's core Spec Kit commands.  |
| Default integration             | The one installed integration a project is currently pointed at. Committed project configuration; determines which agent gets scaffolding and registration. |
| Multi-install                   | A project with more than one integration installed at the same time.                                                                  |
| Core agents                     | The Spectra stack component representing Spec Kit's integration installed in the project — the component this feature makes plural-aware. |
| Spectra agents                  | The Spectra extension installed in the project; a separate component with its own version and update path.                             |
| Managed file                    | A file installed and tracked by an integration, whose expected content is recorded at install time. A file that no longer matches is "modified". |
| Shared Spec Kit infrastructure  | Scripts and templates shared by all integrations in a project — including the spec, plan, and tasks templates. Tracked separately from any integration. |
| Modified managed file           | A managed file whose content diverges from what was recorded at install. Blocks an upgrade until an overwrite is authorized.            |
| Overwrite (force)               | Authorizing an upgrade to replace modified managed files and shared infrastructure with bundled content. Irreversible and not scoped to the files that caused the block. |
| Coverage gap                    | An installed integration that has no Spectra commands registered for it, because registration follows the default integration only.     |
| Currency                        | Whether a component is current, behind, ahead, or unestablished relative to the tool version installed on the machine.                  |
