# Business Requirements Document (BRD): Full Integration Coverage on Install and Update

## Document Control

| Field             | Value                                                                                                                                                                                                                                                                    |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| BRD ID            | BRD-007                                                                                                                                                                                                                                                                  |
| Title             | Full Integration Coverage on Install and Update                                                                                                                                                                                                                          |
| Author            | Spectra / TELUS Digital                                                                                                                                                                                                                                                  |
| Status            | Draft                                                                                                                                                                                                                                                                    |
| Version           | 0.1.0                                                                                                                                                                                                                                                                    |
| Created           | 2026-08-20                                                                                                                                                                                                                                                               |
| Last updated      | 2026-08-20                                                                                                                                                                                                                                                               |
| Related documents | `.specify/memory/constitution.md`, `brds/multi-integration-updates.md` (BRD-006), `specs/010-multi-integration-updates/spec.md`, `specs/010-multi-integration-updates/contracts/cli-surface.md`, `specs/007-unified-version-update/contracts/health-check.md`, `README.md` § "Projects with more than one agent installed" |

## 1. Executive Summary

`spectra install` installs Spectra's agents for **one** coding-agent integration — the project's
default — even when the project has several installed. Every other agent in the repository gets
nothing, and the developer using it has no Spectra commands and no explanation. BRD-006 made
`spectra version` *report* that gap; this feature **closes** it.

After this feature, `spectra install` leaves every installed integration in the project carrying
Spectra's commands, and `spectra update` keeps them there — today an update actively deletes them
from every agent but the default. Both do so without leaving the project pointed at a different agent
than it was before: coverage is achieved by activating each integration in turn and restoring the
original default as the last act of the run, which is disclosed before it happens.

This BRD deliberately reopens a boundary BRD-006 set (§ 2.2). It does not change what "current"
means, adds no new command, and costs single-integration projects nothing.

## 2. Business Context & Problem Statement

A Spec Kit project can have several agent integrations installed at once — `claude` and `kiro-cli`,
say — with one marked as the default. Spectra's entire positioning is that it works with whichever
agent a team has approved, so a repository carrying two of them is not an edge case; it is the
configuration the product invites.

BRD-006 fixed the *version* half of that story: `spectra version` now reports every installed
integration and `spectra update` brings every one of them current. It explicitly left the *coverage*
half alone — whether Spectra's own commands exist for each agent — and added an advisory that names
the gap and the manual remedy. Field use has shown that the advisory is where the problem starts, not
where it ends:

- **Install covers one agent.** Installing Spectra into a two-integration project registers its
  commands for the default integration only. Nothing is said about the other one during the install;
  the install reports complete success.
- **The user is then sent somewhere alarming.** The advisory's remedy permanently changes the
  project's default integration for everyone, so the correct thing for a careful developer to do with
  it is nothing. A remedy nobody should run is not a remedy.
- **Update makes it worse, silently.** Updating the Spectra extension removes its commands from
  **every** agent and reinstalls them for the default only. A project a developer had fixed by hand
  loses that work on the next `spectra update`, with no message and no failure.
- **Re-running the install cannot fix it.** In a project where Spectra is already installed, the
  install step fails outright, so the obvious self-service repair — run `spectra install` again —
  reports an error and changes nothing.
- **Nothing else can fix it either.** The per-integration upgrade introduced by BRD-006 re-registers
  commands only for the default integration, by the dependency's design.

The cost lands on exactly the teams Spectra most wants: multi-agent teams, where a developer on the
non-default agent concludes Spectra "doesn't work" while a colleague two desks away has all of it.
The gap is invisible from their side, the fix is undocumented, and the one command that appears to
offer a fix warns them off using it.

### 2.1 Verified findings

Observed 2026-08-20 against Spec Kit CLI 0.16.5, in a disposable two-integration project (`kiro-cli`
default, `claude` second) and by inspection of the dependency's source. These are behaviours of the
dependency, not of Spectra's internals, and the requirements below are built on them.

| #  | Finding | How it was established | Consequence |
| -- | ------- | ---------------------- | ----------- |
| F1 | Installing an extension registers its commands for the **active integration only**. The dependency records this as deliberate and defers the others until one is activated. | Source inspection; reproduced in the probe project — the recorded registration named `kiro-cli` alone, the default agent's command directory held all five Spectra commands and the second agent's held none. | `spectra install` cannot cover a second integration by installing harder. Coverage requires a separate act. |
| F2 | **Activating** an integration registers every installed extension's commands for it, and the record **accumulates** rather than replaces — the previously covered agent keeps its commands and its files. | Source inspection; reproduced — after activating the second agent, both agents were recorded as covered and both agents' command files were present. | Coverage can be added one integration at a time without taking it away from another. |
| F3 | Re-activating the original default afterwards restores it, leaving **both** agents covered and the project's recorded default and active-agent settings back to their original values. | Reproduced — default returned to `kiro-cli`, the setting the second agent had added was removed again, and both agents' command files remained intact. | A rotation through the integrations can end with the project configured exactly as it started. |
| F4 | Activation with **locally modified** shared infrastructure does **not** fail: the modified file is preserved, a warning names it, and the command succeeds. | Reproduced — a deliberately edited shared script was reported as preserved and the activation exited successfully. | Coverage needs no overwrite authorization and cannot discard a team's edits. This is materially safer than the upgrade path BRD-006 had to gate. |
| F5 | Updating an extension **removes it first** — which unregisters and deletes its command files for **every** agent — and then reinstalls, which registers the active agent only (F1). | Source inspection; the removal half reproduced — removing the extension deleted all five command files from **both** agents. | `spectra update` destroys coverage for every non-default integration. Fixing install alone would be undone by the next update. |
| F6 | There is **no** command that registers an extension for a named agent. Activation (and project initialization) is the only trigger. | Dependency command surface: the extension install offers no agent selector; the per-integration upgrade re-registers only for the default. | Rotating the active integration is not a preference — it is the only supported mechanism. |
| F7 | Installing an extension that is **already installed** exits with a failure and a message telling the user to remove it first or force an overwrite. | Reproduced — non-zero exit in the probe project. | Today `spectra install` reports failure in an already-installed project, so it cannot be the repair path until "already installed" is treated as a state rather than an error. |
| F8 | Upgrading a **non-default** integration deliberately skips extension re-registration. | Source inspection, with an upstream issue cited in that code. | The BRD-006 update path cannot repair coverage as a side effect; coverage must be an explicit step. |
| F9 | The set of installed integrations is the project's **recorded list**; a per-integration record on disk is not by itself membership, and the shared-infrastructure record is not an integration. | Inherited from BRD-006 F8, unchanged. | Enumeration must read the recorded list, never the directory. |

### 2.2 A boundary this BRD deliberately moves

BRD-006 § 5.2 placed two things out of scope: *"Changing the project's default integration — not as an
end state and not transiently"*, and *"Scaffolding or registering commands for non-default
integrations"*, noting that a future opt-in capability might revisit the latter. **This BRD is that
revisit, and it also reopens the first.**

What has changed is the evidence. BRD-006 recorded that no supported path existed (its F4); F2–F4
above establish that one does, that it is non-destructive, and that it can be undone within the same
run. What has not changed is the underlying commitment: **the project ends every run configured
exactly as it started.** The default integration is a means during the run, never an outcome of it.

Two properties keep that promise honest, and both are requirements rather than intentions: the
restoration is the last act of the run and is attempted even when an earlier step fails, and any run
that cannot complete the restoration tells the user the exact command that will.

## 3. Business Objectives & Goals

- **G1 — Installing Spectra means installing it for the whole project.** Every installed integration
  carries Spectra's commands when the install reports success.
- **G2 — Updating never takes coverage away.** A project covered before an update is covered after it.
- **G3 — The project's configuration is returned untouched.** No run ends with a different default
  integration, a different active agent, or a coverage gap it created.
- **G4 — Self-service repair.** A developer who lands in a partially covered project can fix it with a
  Spectra command that reads as safe, rather than a dependency command that warns it will change a
  team-wide setting.
- **G5 — Disclose before acting.** The transient change to the default is stated before it happens, in
  terms of what it is and how it ends.
- **G6 — Never lose a team's work to gain coverage.** Coverage must not overwrite modified files, and
  must not require anyone to authorize an overwrite.
- **G7 — Cost the majority nothing.** Single-integration projects see no new output, no new prompts,
  and no new steps.
- **G8 — Leave no undiagnosable state.** Where coverage cannot be established or completed, say which
  integrations are affected and what the user can run.

## 4. Stakeholders & Users

| Stakeholder / user                          | Role in this product          | What they need from it                                                                                                             |
| ------------------------------------------- | ----------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| Developer on a non-default agent            | Primary beneficiary           | Spectra's commands to exist in their agent after a colleague — or they themselves — ran `spectra install`, with no manual steps.     |
| Developer running the install               | Primary user                  | One command that finishes the job for the whole project, and tells them plainly what it did to get there.                            |
| Developer in a single-agent project         | Primary user                  | Exactly today's behaviour and output.                                                                                              |
| Team that owns the project configuration    | Affected party                | Certainty that a maintenance command does not change which agent the project targets, and does not overwrite customized files.       |
| Automation / CI running install or update   | Secondary consumer            | Deterministic, non-interactive behaviour with no prompt to answer and an exit code that reflects only what was attempted.            |
| Engineering leads                           | Oversight                     | Confidence that adopting Spectra across a mixed-agent team needs no per-developer setup and no undocumented workaround.             |
| Spec Kit CLI and recorded project state     | Dependency (input and action) | The source of installed integrations, the default, and coverage state; and the executor of every activation and registration.        |

## 5. Scope

### 5.1 In Scope

- **Coverage detection.** Determine which installed integrations have Spectra's commands registered
  and which do not, from recorded state rather than inference.
- **Coverage completion during `spectra install`.** Bring every uncovered integration into coverage as
  a disclosed step of the install, ending with the project's original default restored.
- **Coverage preservation during `spectra update`.** After the Spectra agents are updated, restore
  coverage for every integration that had it and complete it for those that did not — asked once, or
  taken as authorized by the run's existing confirmation flag.
- **Idempotent install.** An install run in a project where Spectra is already present completes
  successfully and repairs coverage, rather than reporting a failure.
- **Restoration guarantees.** The original default is restored as the run's final act, is attempted
  even after a failure, and any run that cannot restore it names the command that will.
- **Per-integration outcome reporting** for the coverage step: which integrations were newly covered,
  which were already covered, and which were skipped and why.
- **Silence for single-integration projects.** No step, prompt, or line of output is added when a
  project has one integration, or when every integration is already covered.
- **Rewording the coverage advisory** so that it points at the Spectra command that now fixes the gap,
  and remains only for the cases the automatic path declines.

### 5.2 Out of Scope

- **Changing which agent the project targets as an outcome.** The default integration is restored in
  every run. Only a transient, disclosed, self-reversing change is in scope (§ 2.2).
- **Installing integrations.** Spectra covers the integrations a project already has; it never adds,
  removes, or suggests one.
- **A new top-level command.** This is behaviour inside `spectra install` and `spectra update`, plus a
  reworded advisory in `spectra version`.
- **Changing what "current" means.** The four-component report, its verdicts, and the per-integration
  version work delivered by BRD-006 are unchanged.
- **Overwriting modified managed files.** Coverage takes the non-destructive path (F4) and never
  requests, requires, or accepts an overwrite authorization; BRD-006's gate stays exclusive to the
  version upgrade.
- **Reconciling divergence, or showing what diverged.** Unchanged from BRD-006.
- **Preset coverage.** Presets follow the same activation model and remain the dependency's
  responsibility.
- **Guaranteeing coverage for an integration installed *after* Spectra.** Re-running `spectra install`
  is the supported answer; watching for new integrations is not in scope.

## 6. User Journeys *(feeds the spec's prioritized user stories)*

### Journey 1 — Installing Spectra covers every agent in the project (Priority: P1)

- **Actor:** Developer installing Spectra into a repository with two integrations installed.
- **Trigger:** Runs `spectra install`.
- **Outcome / value:** Both agents carry Spectra's commands when the run finishes, the project's
  default integration is what it was before, and the developer was told how that was achieved.
- **Flow:**
  1. The install completes its existing steps: prerequisite check, project check, catalog and
     extension install.
  2. It determines which installed integrations lack Spectra's commands.
  3. Finding one or more, it states — before acting — that it will activate each in turn to register
     the commands and will restore the current default at the end, naming that default.
  4. It covers each uncovered integration, then restores the original default.
  5. It reports which integrations are now covered and confirms the default is unchanged.
- **Acceptance:**
  - **Given** two integrations installed and one uncovered, **When** `spectra install` completes,
    **Then** both integrations have Spectra's commands registered and their command files present.
  - **Given** the same run, **When** it completes, **Then** the project's recorded default integration
    and active-agent setting are identical to their values before the run.
  - **Given** the coverage step is about to run, **When** it starts, **Then** the output states that
    the default will change transiently and be restored, and names the default it will restore.
  - **Given** the run completes, **Then** the summary names every integration that was covered.
  - **Given** a project where coverage did not require any overwrite decision, **Then** no overwrite
    prompt or flag is involved at any point.

### Journey 2 — Updating Spectra keeps every agent covered (Priority: P1)

- **Actor:** Developer maintaining a two-integration repository where both agents have Spectra.
- **Trigger:** Runs `spectra update`.
- **Outcome / value:** Both agents still have Spectra's commands after the update, instead of the
  non-default agent silently losing them.
- **Flow:**
  1. The update performs its existing four-component walk, including updating the Spectra agents.
  2. Where the Spectra agents were updated, it determines coverage afresh.
  3. Finding integrations uncovered, it discloses the transient default change and asks once —
     defaulting to *no* — unless the run already carries the confirmation flag, which authorizes it.
  4. On agreement it covers each uncovered integration and restores the original default; on refusal
     it changes nothing and reports which integrations are left uncovered and how to fix them.
  5. Its outcome table gains a line per integration for the coverage work.
- **Acceptance:**
  - **Given** two integrations, both covered, **When** `spectra update` updates the Spectra agents and
    the coverage step is accepted, **Then** both integrations are covered afterwards.
  - **Given** the run is started with the confirmation flag, **When** coverage is needed, **Then** it
    proceeds without a prompt.
  - **Given** an interactive run where the user declines, **When** it completes, **Then** no
    activation occurred, the default is unchanged, and the uncovered integrations and the remedy are
    named.
  - **Given** a non-interactive run with no confirmation flag, **When** coverage is needed, **Then**
    nothing is activated, the skip is reported with the flag that would authorize it, and the exit
    status reflects only the work attempted.
  - **Given** the Spectra agents were already current and nothing was updated, **When** coverage is
    already complete, **Then** the coverage step adds no output.

### Journey 3 — A partially covered project is repaired by re-running the install (Priority: P2)

- **Actor:** Developer who joins a repository where Spectra is installed but their agent has none of
  its commands.
- **Trigger:** Runs `spectra install`.
- **Outcome / value:** Their agent gains Spectra's commands, and the run reports success rather than
  an error about the extension already being installed.
- **Flow:**
  1. The install recognizes that Spectra is already present in the project and treats that as a state,
     not a failure.
  2. It proceeds to the coverage step and covers the uncovered integrations.
  3. It reports what it repaired and exits successfully.
- **Acceptance:**
  - **Given** Spectra is already installed and one integration is uncovered, **When** `spectra install`
    runs, **Then** it exits successfully, reports the extension as already present, and covers the
    uncovered integration.
  - **Given** Spectra is already installed and every integration is covered, **When**
    `spectra install` runs, **Then** it exits successfully, says so, and changes nothing.
  - **Given** the install genuinely cannot install the extension for another reason, **Then** that is
    still reported as a failure with a non-zero exit status.

### Journey 4 — The project's default is never left changed (Priority: P2)

- **Actor:** Any developer running a coverage step, and the team that shares the repository.
- **Trigger:** The run is interrupted, or an activation fails, part-way through the rotation.
- **Outcome / value:** The project is never left pointing at an agent nobody chose, and if it cannot
  be restored automatically the user is handed the exact command that restores it.
- **Flow:**
  1. The rotation is interrupted or an activation fails.
  2. The run stops attempting further coverage and immediately restores the original default.
  3. If the restoration itself cannot be performed, the run reports the current default, the original
     one, and the verbatim command that restores it.
- **Acceptance:**
  - **Given** the run is interrupted mid-rotation, **When** it exits, **Then** the original default is
    restored, integrations already covered stay covered, and the interruption is reported rather than
    treated as a failure of the whole command.
  - **Given** an activation fails for one integration, **When** the run continues, **Then** the
    original default is still restored, the failure is named with the integration it belongs to, and
    the remaining integrations are reported as covered or skipped explicitly.
  - **Given** the restoration cannot be completed, **When** the run exits, **Then** it names the
    original default and prints the exact command to restore it, and the run's exit status reflects
    the failure.
  - **Given** no default integration is recorded for the project, **When** coverage is considered,
    **Then** no activation is attempted, because there would be nothing to restore, and the situation
    is reported.

### Journey 5 — Single-integration projects notice nothing (Priority: P3)

- **Actor:** Developer in the common case: one integration installed.
- **Trigger:** Runs `spectra install` or `spectra update`.
- **Outcome / value:** Identical experience to today — no new step, no new question, no new line.
- **Acceptance:**
  - **Given** one integration installed, **When** `spectra install` runs, **Then** its output is
    unchanged from today and no activation occurs.
  - **Given** one integration installed, **When** `spectra update` runs, **Then** its output and
    prompts are unchanged from today.
  - **Given** several integrations, all already covered, **When** either command runs, **Then** no
    coverage output appears.

### Journey 6 — When coverage cannot be completed, the report still explains it (Priority: P3)

- **Actor:** Developer in a project whose recorded state cannot answer the coverage question.
- **Trigger:** Runs `spectra version`.
- **Outcome / value:** The advisory BRD-006 introduced survives for the cases the automatic path
  declines, and now points at a Spectra command that is safe to run.
- **Flow:**
  1. `spectra version` reports the four components as it does today.
  2. Where installed integrations lack Spectra's commands, the advisory names them.
  3. The remedy it names is `spectra install`, not the dependency command that permanently changes the
     project's default.
- **Acceptance:**
  - **Given** an uncovered integration, **When** `spectra version` runs, **Then** the advisory names
    it and gives `spectra install` as the remedy.
  - **Given** coverage cannot be established from recorded state, **When** `spectra version` runs,
    **Then** no advisory is shown and coverage is not guessed at.
  - **Given** the advisory is shown, **When** the run completes, **Then** nothing was changed and the
    exit status is unaffected.

## 7. Business Requirements

| ID    | Requirement                                                                                                                                                          | Priority |
| ----- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| BR-01 | The product MUST determine, from recorded project state, which installed integrations have Spectra's commands registered and which do not.                            | P1       |
| BR-02 | The product MUST NOT infer installed integrations from files on disk, and MUST NOT treat the shared-infrastructure record as an integration.                          | P1       |
| BR-03 | `spectra install` MUST leave every installed integration covered when it reports success.                                                                             | P1       |
| BR-04 | Every run that changes the active integration MUST restore the project's original default as its final act, including after a failure or an interruption.              | P1       |
| BR-05 | The product MUST disclose, before the first activation, that the default will change transiently, and MUST name the default it will restore.                          | P1       |
| BR-06 | `spectra update` MUST re-establish coverage for every installed integration after the Spectra agents are updated.                                                     | P1       |
| BR-07 | The coverage step MUST NOT overwrite modified managed files, and MUST NOT request or accept an overwrite authorization.                                               | P1       |
| BR-08 | Coverage MUST NOT remove or replace coverage an integration already has.                                                                                              | P1       |
| BR-09 | The product MUST NOT attempt coverage when no default integration is recorded, and MUST report why.                                                                   | P1       |
| BR-10 | `spectra install` MUST treat an already-installed Spectra extension as a state, complete successfully, and proceed to the coverage step.                              | P1       |
| BR-11 | `spectra install` MUST still report a genuine install failure as a failure, with a non-zero exit status.                                                              | P1       |
| BR-12 | In `spectra update`, coverage MUST be confirmed once — defaulting to *no* — unless the run's existing confirmation flag is present, which authorizes it.              | P1       |
| BR-13 | A non-interactive `spectra update` without that flag MUST attempt no activation and MUST report the skip and the flag that would authorize it.                        | P1       |
| BR-14 | The product MUST report a per-integration coverage outcome: newly covered, already covered, or skipped with a reason.                                                 | P2       |
| BR-15 | A failure to cover one integration MUST NOT prevent the remaining integrations from being attempted, nor the default from being restored.                             | P2       |
| BR-16 | Where the original default cannot be restored, the product MUST name the current default, the original one, and the verbatim command that restores it.                | P2       |
| BR-17 | The product MUST add no step, prompt, or output for projects with a single installed integration, or where every integration is already covered.                      | P1       |
| BR-18 | The coverage advisory in `spectra version` MUST name `spectra install` as the remedy, and MUST NOT direct users at a command that permanently changes the default.    | P2       |
| BR-19 | The coverage advisory MUST remain silent when coverage cannot be established from recorded state.                                                                     | P2       |
| BR-20 | The product MUST NOT install, remove, or recommend an integration.                                                                                                   | P1       |
| BR-21 | The product MUST NOT hard-code any integration key or agent name; the set of integrations MUST come from project state at run time.                                   | P1       |
| BR-22 | Coverage MUST be performed only through the dependency's supported commands; the product MUST NOT write agent command files or registration records itself.           | P1       |
| BR-23 | An interruption during coverage MUST be reported as an interruption, not as a failed command, consistent with the existing update walk.                               | P2       |
| BR-24 | The four-component report, its verdicts, and the per-integration version behaviour delivered by BRD-006 MUST be unchanged.                                           | P1       |
| BR-25 | Documentation MUST state that install and update cover every installed integration and that the project's default is never changed as an outcome.                     | P2       |

## 8. Success Metrics & Measurable Outcomes

- **SC-01** — In a project with any number of installed integrations, a successful `spectra install`
  leaves 100% of them covered, with zero manual steps.
- **SC-02** — Zero runs end with a default integration different from the one they started with.
- **SC-03** — Coverage established before an update survives it 100% of the time; the current
  behaviour of losing it for every non-default integration is eliminated.
- **SC-04** — A developer landing in a partially covered project restores full coverage with one
  command, without reading the dependency's documentation.
- **SC-05** — Zero files modified by the team are overwritten by the coverage step, and zero overwrite
  prompts originate from it.
- **SC-06** — Single-integration projects show a byte-identical install and update experience to the
  release before this feature.
- **SC-07** — Every integration that ends a run uncovered is named in the output together with a
  remedy the user can run verbatim.
- **SC-08** — Zero runs leave the project in a state that requires manual inspection of project files
  to understand or repair.

## 9. Assumptions

- Activation is the only supported way to register an extension's commands for an agent (F6); if the
  dependency later offers a direct per-agent registration, that becomes the preferred mechanism and
  the rotation is removed.
- Activation is non-destructive to modified managed files (F4), so coverage never needs the overwrite
  gate BRD-006 built for version upgrades.
- Activating an integration and then restoring the original default leaves the project's recorded
  configuration semantically identical to its starting state (F3); verifying that the restored state
  is also textually identical is a task for the spec, not an assumption to rely on.
- Coverage accumulates rather than replaces (F2), so the order integrations are covered in affects
  only the intermediate states, never the outcome — with the single exception that the original
  default must be covered last so it is also the restored one.
- The recorded installed list is authoritative membership, unchanged from BRD-006.
- Projects with one integration are the large majority, which is why the feature must be invisible to
  them.
- A developer running `spectra install` has consented to Spectra changing this project's agent
  configuration; a developer running `spectra update` is performing maintenance, which is why the
  first discloses and proceeds while the second discloses and asks.
- The number of installed integrations in real projects is small (single digits), so a rotation costs
  seconds and needs no progress machinery beyond a line per integration.
- No two Spectra runs execute concurrently in the same project; the product does not defend against a
  second run observing a transiently changed default.

## 10. Constraints

- **The default integration is the team's, not Spectra's.** It may be changed only transiently, only
  within a run that discloses it, and it must be restored before the run ends. This is the condition
  under which BRD-006's boundary is reopened (§ 2.2).
- **All work is delegated.** Every activation and registration is performed by the dependency's own
  commands; Spectra never writes an agent's command files or the dependency's registration records.
- **No new trust boundary, no new credentials, no telemetry** — the product's standing constraints are
  unchanged, and this feature adds no network call of its own.
- **No hard-coded agents.** The roster and integration keys are data read at run time, never constants
  in the product.
- **Non-interactive runs are never destructive** and never hang waiting for input.
- **The extension's own version and release channel are unaffected**: this is a change to the Spectra
  command, not to the agents it installs.
- **Compatibility with the version of Spec Kit this feature is tested against** must be recorded, since
  the behaviour it builds on (F1–F8) is the dependency's, not the product's.

## 11. Dependencies

- **Spec Kit CLI — input.** The source of the installed-integration list, the recorded default, and
  the registration state that answers the coverage question.
- **Spec Kit CLI — action.** The executor of every activation and every registration, including the
  restoration of the original default.
- **BRD-006 / spec 010 — input.** Per-integration enumeration, the default-integration reader, and the
  coverage detection introduced for the advisory are the foundation this feature builds on; its
  overwrite-authorization gate is explicitly not reused.
- **`spectra version`'s advisory — output.** Reworded by this feature to point at the new remedy.
- **The project's committed configuration — output.** Written twice per covered integration during a
  rotation and restored at the end; the end state is the contract.
- **README and the extension's changelog — output.** Must state the new install and update behaviour.

## 12. Risks & Mitigations

| Risk                                                                                                                   | Impact | Likelihood | Mitigation |
| ---------------------------------------------------------------------------------------------------------------------- | ------ | ---------- | ---------- |
| A run is killed mid-rotation (`SIGKILL`, terminal closed, machine sleeps) and the default is left changed.              | H      | L          | Restore on interrupt and on failure; on any run that cannot restore, print the verbatim restoring command. Document the one-line recovery in the README so the state is diagnosable without support. |
| The restored configuration differs textually from the original, producing spurious version-control noise for the team.   | M      | M          | Verify the restored state against the pre-run state in testing, on every integration combination exercised; treat any difference as a defect, not an acceptable side effect. |
| Activating an integration changes a per-agent mode the team had set deliberately (for example, how commands are surfaced). | M      | L          | Rely on the dependency reproducing each integration's own recorded settings on activation; assert the per-integration settings are unchanged after a rotation, and abandon the automatic path for any integration where they are not. |
| The dependency changes activation semantics in a later release, breaking coverage or the restoration.                    | H      | M          | Pin and record the tested dependency version; cover the behaviour with an end-to-end scenario in the existing containerized test harness so a regression is caught before release, not by a user. |
| Users perceive the transient default change as Spectra taking liberties with project configuration.                     | M      | M          | Disclose before acting, name the default being restored, confirm the restoration in the summary, and ask rather than proceed in `spectra update`. |
| The coverage step lengthens the install noticeably in a project with several integrations.                               | L      | M          | Cover only integrations that need it, report progress one line per integration, and skip the step entirely when nothing is uncovered. |
| Treating "already installed" as success masks a genuinely failed install.                                               | M      | L          | Distinguish the two by project state rather than by message text, and keep a non-zero exit status for every other failure. |
| Two developers, or a developer and CI, run Spectra concurrently in one project and one observes a transient default.     | M      | L          | Documented as an assumption rather than defended against; the window is seconds and the end state is unchanged. |

## 13. Open Questions

- Should `spectra update` treat coverage as part of its update plan — counted in the plan it confirms
  up front — or as a distinct question asked after the components are updated?
- Should the coverage step also run when `spectra update` finds the Spectra agents already current but
  an integration uncovered, or is that strictly `spectra install`'s job?
- Does `spectra check --yes`, which delegates to the install, inherit the coverage step unchanged, or
  should it stay a pure "is Spectra here?" question as BRD-006 assumed for the advisory?
- Should the summary state the coverage outcome per integration in the install as well as the update,
  or is a single "covered: a, b" line sufficient there?
- When exactly one integration is installed but it is *not* covered — possible after a failed run —
  should coverage engage, given that Journey 5 promises silence for single-integration projects?
- Should the product verify coverage after the rotation by re-reading recorded state, in the same way
  BRD-006 verifies that an upgraded integration's version actually moved?

## 14. Glossary

| Term                      | Definition                                                                                                                                    |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| Integration               | A coding-agent integration installed into a Spec Kit project (for example `claude`, `kiro-cli`). A project may have several.                   |
| Default integration       | The one integration a project targets by default; committed project configuration shared by everyone who clones the repository.                |
| Active integration        | The integration the dependency currently treats as the project's own for registration purposes; in practice, the default.                      |
| Coverage                  | Whether Spectra's commands are registered, and their files present, for a given integration.                                                   |
| Activation                | Making an integration the project's default, which as a side effect registers installed extensions' commands for it.                           |
| Rotation                  | Activating each uncovered integration in turn and restoring the original default last, so coverage is completed without changing the outcome.   |
| Core agents               | The Spec Kit integration installed into the project — one of the four components `spectra version` reports.                                     |
| Spectra agents            | The Spectra extension installed into the project — another of the four components.                                                              |
| Managed file              | A project file the dependency installs and tracks, and which a team may have modified locally.                                                  |
