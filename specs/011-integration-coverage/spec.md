# Feature Specification: Full Integration Coverage on Install and Update

**Feature Branch**: `011-integration-coverage`

**Created**: 2026-08-20

**Status**: Draft

**Input**: BRD-007 — `brds/full-integration-coverage.md` ("Full Integration Coverage on Install and Update")

## Clarifications

### Session 2026-08-20

- Q: When the coverage step runs but cannot cover one of the integrations, should `spectra install` still
  report overall success? → A: **A failed attempt exits non-zero; a step deliberately skipped for a
  stated reason exits zero.** The distinction is between "we tried and it broke", which is a real failure
  of the install's own promise and must be actionable, and "we deliberately did not try, and said why" —
  no default recorded, or coverage state unknown — which is a reported state rather than an error. This
  matches how the existing update walk already treats skips as inert and failures as failures, and it
  replaces the phrase "covered or explicitly accounted for", which could have meant either.
- Q: What should install and update do when the Spec Kit version present is too old to support the
  coverage mechanism this feature relies on? → A: **Never compare versions — degrade on absence of
  data.** When the state coverage depends on is absent or unreadable, coverage is unknown, the step is
  skipped, and the reason is stated. This mirrors the fallback rule the previous feature established, so a
  project on an older dependency keeps today's behaviour instead of having its default integration
  rotated for no gain, and there is no minimum-version constant to keep current as the dependency moves.
- Q: If restoring the original default leaves the project's configuration files textually different from
  how they started — same meaning, different bytes — what must the product do? → A: **Treat it as a
  defect found by testing before release; if it cannot be eliminated, disclose the affected files by name
  before the coverage step and let the user decline it.** Rewriting the files to match byte-for-byte was
  rejected because the product is forbidden from writing the dependency's records itself, and accepting
  the difference silently was rejected because committed configuration noise is precisely the objection
  the disclosure exists to prevent. Under this answer the install acquires a question **only** in the
  unresolved-difference case; otherwise it still discloses and proceeds.
- Q: When the extension step of `spectra install` fails for a real reason — the catalog is unreachable, or
  the download fails — should the coverage step still run? → A: **Conditionally.** Coverage runs when the
  extension is already present in the project from an earlier run, because coverage depends on an
  extension being present rather than on this run having installed it, and a failed download must not
  block a repair that would otherwise succeed. Where no extension is present, coverage is skipped as
  inapplicable rather than attempted and failed. The two outcomes are reported separately, and a
  successful coverage step never masks the extension failure or its non-zero exit status.
- Q: Should there be a way to run `spectra install` while skipping the coverage step — for a team that
  does not want its default integration moved even transiently? → A: **No flag and no environment
  variable.** Coverage is part of installing Spectra. The step is non-destructive, self-reversing, and
  disclosed before it acts, and the only skips are the stated ones: no default recorded, coverage state
  unknown, no extension present, or the unresolved-textual-difference case that FR-044 already makes
  declinable. A team that genuinely objects can still install the extension with the dependency's own
  command, so a flag would add permanent surface for an opt-out that is only meaningful in a case already
  handled.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Installing Spectra covers every agent in the project (Priority: P1)

A developer runs `spectra install` in a repository that has two coding-agent integrations installed —
one marked as the project default, one not. Today the install registers Spectra's commands for the
default integration only, reports complete success, and says nothing about the other agent, so a
colleague using it has no Spectra commands and no explanation. This story makes the install finish the
job for the whole project: every installed integration ends up carrying Spectra's commands, and the
project's default integration is exactly what it was when the run started.

**Why this priority**: This is the feature. It is the difference between "Spectra is installed here"
being true for the repository and true only for whoever happened to run the install. It is also the
foundation every other story builds on — the coverage step it introduces is what Story 2 preserves,
Story 3 re-runs, and Story 4 makes safe.

**Independent Test**: In a project with two integrations installed and Spectra's commands registered
for neither or one, run `spectra install` and confirm that both integrations end up with Spectra's
commands registered and their command files present, that the recorded default integration and active
agent are unchanged from before the run, and that the run stated up front that the default would move
and be restored.

**Acceptance Scenarios**:

1. **Given** two installed integrations and one of them uncovered, **When** `spectra install`
   completes successfully, **Then** both integrations are recorded as having Spectra's commands and
   both agents' command artifacts are present.
2. **Given** the same run, **When** it completes, **Then** the project's recorded default integration
   and recorded active agent are identical to their values immediately before the run.
3. **Given** coverage work is required, **When** the coverage step begins, **Then** the run states
   before acting that each uncovered integration will be activated in turn, that the default will be
   restored at the end, and names the default it will restore.
4. **Given** the coverage step ran, **When** the run finishes, **Then** it names every integration it
   covered and confirms the default was restored.
5. **Given** three or more installed integrations with two uncovered, **When** `spectra install`
   completes, **Then** all three are covered and the default is unchanged.
6. **Given** any coverage run, **When** it completes, **Then** no overwrite prompt was shown, no
   overwrite authorization was requested, and no locally modified managed file was overwritten.
7. **Given** the integration that is the project default is itself uncovered, **When** the coverage
   step runs, **Then** it is covered as part of the same step and remains the default.

---

### User Story 2 - Updating Spectra keeps every agent covered (Priority: P1)

A developer maintains a two-integration repository where both agents have Spectra's commands. They run
`spectra update`. Today updating the Spectra agents removes those commands from **every** agent and
re-registers them for the default only, so the non-default agent silently loses them — including when a
developer had previously fixed it by hand. This story makes the update re-establish coverage for every
installed integration, disclosing the transient default change and asking once before doing it.

**Why this priority**: Equal to Story 1, because without it Story 1 is undone by the next maintenance
run. It is also the only story that fixes an active regression: today's update destroys coverage that
already existed.

**Independent Test**: In a project with two integrations both covered, run `spectra update` through an
update of the Spectra agents, accept the coverage step, and confirm both integrations are still
covered afterwards and the default is unchanged. Then decline it on a second run and confirm nothing
was activated and the uncovered integrations are named with a remedy.

**Acceptance Scenarios**:

1. **Given** two integrations both covered and the Spectra agents behind, **When** `spectra update`
   runs and the coverage step is accepted, **Then** both integrations are covered after the run.
2. **Given** an interactive run where coverage work is needed, **When** the coverage step is reached,
   **Then** the user is asked exactly once, the question defaults to declining, and the disclosure
   names the integrations to be covered and the default to be restored.
3. **Given** the run carries the existing confirmation flag, **When** coverage work is needed,
   **Then** it proceeds without a prompt.
4. **Given** an interactive run where the user declines, **When** the run completes, **Then** no
   integration was activated, the default is unchanged, the uncovered integrations are named, and the
   remedy is stated.
5. **Given** a run with no terminal attached and no confirmation flag, **When** coverage work is
   needed, **Then** nothing is activated, the skip is reported together with the flag that would
   authorize it, and the run's exit status reflects only the work that was attempted.
6. **Given** every installed integration is already covered, **When** `spectra update` runs, **Then**
   no coverage question is asked and no coverage output appears.
7. **Given** coverage work was performed, **When** the run reports its outcomes, **Then** the coverage
   result appears alongside the four component results, with one line per integration.
8. **Given** the user declines coverage, **When** the run reports its exit status, **Then** declining
   is not treated as a failure.

---

### User Story 3 - A partially covered project is repaired by re-running the install (Priority: P2)

A developer joins a repository where Spectra is already installed but their agent has none of its
commands. The obvious thing to try — `spectra install` — currently fails outright, because the
underlying extension install refuses to run when the extension is already present. This story makes
the install treat "already installed" as a state rather than an error, so re-running it repairs
coverage and reports success.

**Why this priority**: It is the self-service repair path for every project that predates this feature,
and for any project where coverage was lost or interrupted. It is lower than P1 only because Stories 1
and 2 prevent the situation arising in the first place; this one cleans up the installed base.

**Independent Test**: In a project where Spectra is installed and one integration is uncovered, run
`spectra install` and confirm it exits successfully, reports the extension as already present rather
than as a failure, and covers the uncovered integration.

**Acceptance Scenarios**:

1. **Given** Spectra is already installed and one integration is uncovered, **When** `spectra install`
   runs, **Then** it exits successfully, reports the extension as already present, and covers the
   uncovered integration.
2. **Given** Spectra is already installed and every integration is covered, **When** `spectra install`
   runs, **Then** it exits successfully, says the project is already fully covered, and changes
   nothing.
3. **Given** the extension cannot be installed for any reason other than already being present,
   **When** `spectra install` runs, **Then** that is reported as a failure with a non-zero exit status
   and the existing remedy text.
4. **Given** the extension is already present, **When** the install reports what it did, **Then** it
   does not claim to have installed or downloaded anything.
5. **Given** an already-installed project, **When** `spectra install` runs, **Then** the installed
   extension is neither removed, re-downloaded, nor overwritten in order to achieve coverage.
6. **Given** Spectra is already present but this run's extension step fails, **When** the run continues,
   **Then** coverage is still attempted, its outcome is reported separately from the extension failure,
   and the run still exits non-zero because of that failure.
7. **Given** no extension is present and the extension step fails, **When** the run ends, **Then**
   coverage is skipped as inapplicable and only the extension failure is reported.

---

### User Story 4 - The project's default is never left changed (Priority: P2)

A coverage run is interrupted, or one activation fails part-way through. Because coverage is achieved
by activating each uncovered integration in turn, an abandoned run could leave the repository pointing
at an agent nobody chose — committed configuration that affects everyone who clones it. This story
makes the restoration unconditional: it is the last act of every run that moved the default, it is
attempted even after a failure or an interruption, and where it cannot be completed the run hands the
user the exact command that restores it.

**Why this priority**: It is the safeguard that makes Stories 1 and 2 acceptable at all. It is
separated from them because it is independently testable — by interrupting or failing a run — and
because the guarantee must hold even for code paths added later.

**Independent Test**: Interrupt a coverage run between two activations and confirm the original default
is restored, the integrations already covered stay covered, and the interruption is reported as an
interruption. Then force an activation to fail and confirm the run still restores the default, names
the failure with its integration, and reports the remaining integrations explicitly.

**Acceptance Scenarios**:

1. **Given** a coverage run in progress, **When** the user interrupts it between activations, **Then**
   no further integration is activated, the original default is restored, and the interruption is
   reported as an interruption rather than as a failed command.
2. **Given** an activation fails for one integration, **When** the run continues, **Then** the
   remaining uncovered integrations are still attempted, the original default is still restored, and
   the failure is reported naming the integration it belongs to.
3. **Given** the restoration itself fails, **When** the run exits, **Then** it names the integration
   the project is currently defaulted to, names the original default, prints the exact command that
   restores it, and exits non-zero.
4. **Given** the project records no default integration, **When** coverage is considered, **Then** no
   activation is attempted, the reason is reported, and the uncovered integrations are named.
5. **Given** every uncovered integration was covered successfully, **When** the run restores the
   default, **Then** the restoration is confirmed in the output.
6. **Given** a coverage run that had to activate at least one integration, **When** the run ends for
   any reason, **Then** the last integration activated is never left as the project default unless it
   already was.
7. **Given** coverage was attempted and failed for at least one integration, **When** the run exits,
   **Then** its exit status is non-zero.
8. **Given** the coverage step was skipped for a stated reason rather than attempted, **When** the run
   exits, **Then** its exit status is zero and the reason is in the output.

---

### User Story 5 - Single-integration projects notice nothing (Priority: P3)

The large majority of projects have exactly one integration installed. For them this feature must be
invisible: no new step in the install, no new question in the update, no new line of output.

**Why this priority**: It is a constraint on the other stories rather than new capability, but it is
independently testable and it protects the common case from noise introduced for the uncommon one.

**Independent Test**: In a project with one installed integration, run `spectra install` and
`spectra update` and confirm their output and prompts are unchanged from the release before this
feature.

**Acceptance Scenarios**:

1. **Given** one installed integration that is covered, **When** `spectra install` runs, **Then** its
   output is unchanged from the previous release and no activation occurs.
2. **Given** one installed integration that is covered, **When** `spectra update` runs, **Then** its
   output and prompts are unchanged from the previous release.
3. **Given** several installed integrations all already covered, **When** either command runs,
   **Then** no coverage step, question, or output appears.
4. **Given** one installed integration that is recorded as uncovered, **When** `spectra install` runs,
   **Then** coverage is established for it, and because it is already the default nothing about the
   project's configuration changes and no transient-default disclosure is made.

---

### User Story 6 - Where coverage cannot be completed, the report still explains it (Priority: P3)

A developer runs `spectra version` in a project whose recorded state cannot answer the coverage
question, or which declined the coverage step. The advisory introduced by the previous feature survives
for exactly these cases — but it currently points at a dependency command that permanently changes the
project's default integration for everyone, which is advice no careful developer should take. This
story repoints it at `spectra install`.

**Why this priority**: Informational, and reduced in importance precisely because the automatic path
now handles the common case. It matters because the remaining cases must still be diagnosable.

**Independent Test**: In a project with an uncovered integration, run `spectra version` and confirm the
advisory names the uncovered integration and gives `spectra install` as the remedy, and that nothing
was changed and the exit status is unaffected.

**Acceptance Scenarios**:

1. **Given** an installed integration with no Spectra commands, **When** `spectra version` runs,
   **Then** the advisory names it and gives `spectra install` as the remedy.
2. **Given** the advisory is shown, **When** the run completes, **Then** nothing in the project was
   changed and the exit status is unaffected.
3. **Given** coverage cannot be established from recorded state, **When** `spectra version` runs,
   **Then** no advisory is shown and coverage is not guessed at.
4. **Given** every installed integration is covered, **When** `spectra version` runs, **Then** no
   advisory appears.
5. **Given** the advisory is shown, **When** it names a remedy, **Then** it does not instruct the user
   to run a command that permanently changes the project's default integration.

---

### Edge Cases

- **One integration, uncovered**: coverage is established for the sole integration without any
  configuration change, because it is already the default — no rotation, no disclosure, one line of
  output.
- **No integrations recorded**: membership cannot be established → no coverage is attempted, and the
  install still reports its extension work normally.
- **No default recorded**: integrations may be enumerable but there is nothing to restore → no
  activation is attempted, the reason is reported, and the uncovered integrations are named.
- **Coverage state unreadable**: the record of which agents have Spectra's commands cannot be read →
  coverage is treated as unknown, nothing is activated, and no coverage claim is made in either
  direction.
- **Dependency too old to support coverage**: the state coverage depends on is absent → coverage is
  unknown, the step is skipped with its reason stated, and install and update otherwise behave exactly as
  they did before this feature. No version number is compared to reach that conclusion.
- **Registry names an agent that is not installed**: coverage for integrations outside the recorded
  installed list is ignored rather than reported as a problem; the question is only ever "is every
  *installed* integration covered?".
- **An integration recorded as installed but otherwise broken**: its activation fails; the failure is
  named, the remaining integrations are still attempted, and the default is still restored.
- **Interrupt during the restoration itself**: the run reports the current default, the original one,
  and the verbatim restoring command.
- **Modified managed files present**: coverage proceeds, the dependency preserves the modified files,
  and no overwrite is requested, offered, or performed.
- **Modified shared infrastructure warning**: the dependency's preservation warning may appear once per
  activation; it is not an error and does not fail the run.
- **Restored configuration differs only in bytes**: the default and every setting are back to their
  starting values but a file was rewritten differently → treated as a defect to be eliminated before
  release; if it cannot be, the affected files are named before the step and the step can be declined.
- **Activation succeeds but coverage does not appear in the record**: reported as not covered, not as
  covered — success is verified from recorded state rather than from an exit code.
- **Update where the Spectra agents were not updated**: coverage is still evaluated, because the damage
  may have been done by an earlier run.
- **Update where the Spectra agents failed to update**: coverage is still evaluated for the
  integrations that have the extension, and the two outcomes are reported separately.
- **`spectra check` accepting the offer to install**: it delegates to the install and therefore
  inherits the coverage step unchanged.
- **A project where the sole integration's commands were never registered because project options were
  unreadable**: coverage is unknown, not zero → nothing is attempted and nothing is claimed.
- **An integration installed after Spectra**: not detected automatically; re-running `spectra install`
  covers it.
- **Extension step fails in an already-installed project**: coverage is still attempted and reported
  separately; the run still exits non-zero for the extension failure.
- **Extension step fails with nothing installed**: coverage is skipped as inapplicable — there are no
  commands to register — and only the extension failure is reported.

## Requirements *(mandatory)*

### Functional Requirements

**Coverage detection**

- **FR-001**: The system MUST determine, for each installed integration, whether Spectra's commands are
  registered for it, using recorded project state as the source.
- **FR-002**: The system MUST take the set of installed integrations from the project's recorded
  installed list, MUST NOT infer it from files present on disk, and MUST NOT treat the shared
  infrastructure record as an integration.
- **FR-003**: The system MUST treat an unreadable, absent, or empty coverage record as **unknown** and
  MUST NOT interpret it as "no integration is covered". Support for coverage MUST be determined from the
  presence of the state it depends on, never from the dependency's version number.
- **FR-004**: When coverage is unknown, the system MUST attempt no coverage work, MUST make no claim
  about coverage in either direction, and MUST state why it did not act.
- **FR-005**: The system MUST ignore coverage recorded for agents that are not in the installed list.
- **FR-006**: The system MUST re-read coverage state after performing coverage work, and MUST report an
  integration as covered only when the record shows it.

**Covering an integration**

- **FR-007**: The system MUST establish coverage only through the dependency's own supported commands,
  and MUST NOT write agent command files, skill files, or registration records itself.
- **FR-008**: The system MUST cover an integration by making it the project's active integration, which
  is the only supported trigger for registering an installed extension's commands for that agent.
- **FR-009**: The system MUST NOT request, require, or accept an authorization to overwrite locally
  modified managed files as part of covering an integration.
- **FR-010**: The system MUST NOT remove, replace, or re-register coverage that an integration already
  has in order to cover another.
- **FR-011**: The system MUST attempt coverage only for integrations recorded as uncovered.
- **FR-012**: The system MUST attempt coverage only when a default integration is recorded, so that
  there is always a value to restore.
- **FR-013**: When the only uncovered integration is already the project default, the system MUST cover
  it without changing any project configuration, and MUST NOT make a transient-default disclosure.
- **FR-014**: When coverage requires activating an integration that is not the default, the system MUST
  disclose before the first activation: that the default will change transiently, the integrations it
  will activate, and the default it will restore.
- **FR-015**: The system MUST restore the project's original default integration as the final act of
  any run in which it changed the active integration.
- **FR-016**: The system MUST attempt the restoration even when an activation failed, when a later step
  failed, or when the run was interrupted.

**`spectra install`**

- **FR-017**: `spectra install` MUST perform the coverage step after its existing catalog and extension
  work, and its exit status MUST distinguish attempt from abstention: zero when the step covered every
  uncovered integration, zero when it deliberately skipped the step for a stated reason (no default
  recorded, or coverage state unknown), and non-zero when coverage was **attempted** and failed for any
  integration.
- **FR-018**: `spectra install` MUST perform the coverage step without asking for permission, and MUST
  make the disclosure required by FR-014 before acting. It MUST NOT offer a flag or environment variable
  that skips the step; the only permitted skips are those FR-004, FR-012, FR-022, and FR-044 define.
- **FR-019**: `spectra install` MUST perform the coverage step in non-interactive runs on the same
  terms as interactive ones, because the step is non-destructive and self-reversing.
- **FR-020**: `spectra install` MUST treat an extension that is already installed as a state rather
  than a failure: it MUST continue to the coverage step, MUST report the extension as already present,
  MUST NOT claim to have installed or downloaded it, and MUST exit successfully when coverage
  completes.
- **FR-021**: `spectra install` MUST distinguish "already installed" from other install failures by
  consulting recorded project state rather than by matching the dependency's message text.
- **FR-022**: `spectra install` MUST continue to report every other install failure as a failure, with a
  non-zero exit status and its existing remedy text. After such a failure the coverage step MUST still
  run when the extension is already present in the project from an earlier run, MUST be skipped as
  inapplicable when no extension is present, and its outcome MUST be reported separately from the install
  failure — a successful coverage step MUST NOT mask that failure or its exit status.
- **FR-023**: `spectra install` MUST NOT remove, re-download, or overwrite an installed extension in
  order to achieve coverage.

**`spectra update`**

- **FR-024**: `spectra update` MUST evaluate coverage after its component walk, whether or not the
  Spectra agents were updated in that run.
- **FR-025**: When coverage work is needed and the run is interactive, `spectra update` MUST ask
  exactly once, and the question MUST default to declining.
- **FR-026**: The disclosure accompanying that question MUST name the integrations that will be
  activated and the default that will be restored.
- **FR-027**: The run's existing confirmation flag MUST authorize the coverage step without a prompt.
- **FR-028**: A run with no terminal attached and no confirmation flag MUST attempt no activation, and
  MUST report the skip together with the flag that would authorize it.
- **FR-029**: Declining or skipping the coverage step MUST leave the project unchanged, MUST NOT be
  treated as a failure, and MUST NOT alter the run's exit status. A coverage step that was **attempted**
  and failed MUST affect the exit status on the same terms as any other attempted component.
- **FR-030**: When the coverage step is declined or skipped, `spectra update` MUST name the
  integrations left uncovered and the remedy.
- **FR-031**: `spectra update` MUST NOT change any behaviour of the four-component report, its
  verdicts, its overwrite authorization, or its per-integration version upgrades.

**Reporting**

- **FR-032**: The system MUST report a per-integration coverage outcome, distinguishing newly covered,
  already covered, failed, and skipped with a reason.
- **FR-033**: The system MUST confirm, after a run that activated any integration, that the original
  default was restored.
- **FR-034**: Where the restoration could not be completed, the system MUST name the current default,
  the original default, and the verbatim command that restores it.
- **FR-035**: A failure to cover one integration MUST be attributed to that integration by name, and the
  outcome report MUST still show the integrations that succeeded as covered; the run's exit status is
  governed by FR-017 for the install and FR-029 for the update.
- **FR-036**: An interruption during coverage MUST be reported as an interruption, consistent with the
  existing update walk, and MUST NOT be reported as a failure.
- **FR-037**: The system MUST add no step, question, or line of output when every installed integration
  is already covered, or when coverage is unknown.
- **FR-038**: The system MUST add no step, question, or line of output for a project with a single
  installed integration that is already covered.

**The coverage advisory in `spectra version`**

- **FR-039**: The advisory MUST name `spectra install` as the remedy for uncovered integrations.
- **FR-040**: The advisory MUST NOT direct the user at a command that permanently changes the project's
  default integration.
- **FR-041**: The advisory MUST remain silent when coverage is unknown, when every installed
  integration is covered, and when fewer than two integrations are installed.
- **FR-042**: The advisory MUST NOT change the run's exit status and MUST NOT change anything in the
  project.

**Boundaries**

- **FR-043**: The system MUST NOT leave the project's default integration, active agent, or per
  integration settings different from their values before the run.
- **FR-044**: A textual difference in committed configuration introduced by a coverage run — same
  meaning, different bytes — MUST be treated as a defect and eliminated before release. Where a
  difference cannot be eliminated, the affected files MUST be named in the disclosure before the coverage
  step and the step MUST be declinable, including in `spectra install`, which otherwise does not ask.
- **FR-045**: The system MUST NOT install, remove, enable, disable, or recommend an integration.
- **FR-046**: The system MUST NOT hard-code any integration key or agent name; the set of integrations
  and the default MUST be read from project state at run time.
- **FR-047**: The system MUST NOT add a new top-level command, and MUST NOT add a flag or environment
  variable for the coverage step; the capability lives inside `spectra install`, `spectra update`, and the
  advisory in `spectra version`, using the flags those commands already have.
- **FR-048**: The system MUST NOT introduce a new network call, credential, or telemetry of any kind.
- **FR-049**: The system MUST NOT reuse the overwrite authorization built for version upgrades, and
  that authorization MUST remain unreachable from the coverage path.
- **FR-050**: Documentation MUST state that install and update cover every installed integration, that
  the default is changed only transiently and restored, and how to recover a default left changed by an
  abandoned run.
- **FR-051**: The version of the dependency this behaviour was verified against MUST be recorded
  alongside the feature, and MUST NOT be consulted at run time as a gate on whether coverage is
  attempted.

### Key Entities

- **Installed integration**: A coding-agent integration the project records as installed. Identified by
  its key. Has a recorded version (owned by the previous feature) and, new here, a coverage state.
- **Default integration**: The single integration the project targets, recorded in committed project
  configuration. Both the value to be restored and, transiently, the mechanism by which coverage is
  achieved.
- **Coverage state**: For one integration, whether Spectra's commands are registered for it — covered,
  uncovered, or unknown. Unknown is a first-class value and never collapses into uncovered.
- **Coverage plan**: The ordered set of uncovered integrations a run intends to cover, plus the default
  it will restore. What the disclosure describes and what the outcome report is matched against.
- **Coverage outcome**: Per integration, one of newly covered, already covered, failed, or skipped with
  a reason; plus a whole-run statement about the restoration.
- **Restoration obligation**: The original default recorded at the start of a run that changes the
  active integration, and the run's commitment to return to it — including after failure or
  interruption.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In a project with any number of installed integrations, a successful `spectra install`
  leaves 100% of them covered, with zero manual steps and zero further commands to run.
- **SC-002**: Zero runs end with a default integration, active agent, or per-integration setting
  different from the value it had when the run started.
- **SC-003**: Coverage that exists before an update survives it in 100% of runs; the current behaviour
  of losing it for every non-default integration is eliminated.
- **SC-004**: A developer who lands in a partially covered project restores full coverage with one
  command, without consulting the dependency's documentation.
- **SC-005**: Zero locally modified managed files are overwritten by the coverage step, and zero
  overwrite prompts or flags originate from it.
- **SC-006**: Projects with a single covered integration see output identical to the release before
  this feature, for both install and update.
- **SC-007**: 100% of integrations that end a run uncovered are named in the output, each with a remedy
  the user can run verbatim.
- **SC-008**: Every run that changed the default and could not restore it prints the restoring command
  — measured as zero runs that end in a changed default without one.
- **SC-009**: A developer can determine which agents have Spectra's commands, and what to do about the
  ones that do not, from one command run without inspecting any project file by hand.
- **SC-010**: An interrupted coverage run leaves the project in a state that a subsequent
  `spectra install` fully repairs, in 100% of cases.
- **SC-011**: On the success path the coverage step adds at most one line of output per integration
  plus one disclosure and one restoration confirmation — so a three-integration project's install grows
  by no more than five lines.
- **SC-012**: Zero runs report success after an attempted coverage step left an installed integration
  uncovered, and every skipped step states its reason.
- **SC-013**: Zero coverage runs produce a textual change in the project's committed configuration; any
  difference that cannot be eliminated is named before the step runs and can be declined.

## Assumptions

- **Activation is the only mechanism.** The dependency offers no way to register an extension's
  commands for a named agent; making an integration active is the only supported trigger. If a direct
  per-agent registration is offered later, it replaces the rotation and the restoration obligation
  disappears with it.
- **Activation is non-destructive.** Activating an integration whose managed files have been modified
  locally preserves those files and succeeds with a warning. Coverage therefore needs no overwrite
  authorization, and the authorization built for version upgrades stays exclusive to that path.
- **Coverage accumulates.** Covering one integration does not remove coverage from another, so the
  order integrations are covered in affects only intermediate states — with the single exception that
  the original default is restored last.
- **The restored state must be textually identical, not merely equivalent.** Activating away from the
  default and back returns the recorded configuration to its starting values; whether it also returns the
  same bytes is verified during implementation, and a difference is a defect rather than an accepted side
  effect (FR-044). A spurious change to committed configuration is a cost borne by the whole team.
- **`spectra update` evaluates coverage every run**, not only when the Spectra agents were updated,
  because the loss may have been caused by an earlier run. This costs nothing when coverage is already
  complete, since no output is produced in that case.
- **Coverage in the update is a distinct question**, asked after the component walk rather than folded
  into the plan the run confirms up front. The plan is about versions; coverage is not a version
  verdict, and mixing them would make one answer cover two different kinds of change.
- **The install discloses and proceeds; the update discloses and asks.** A developer running
  `spectra install` has asked for Spectra to be set up in this project. A developer running
  `spectra update` is performing maintenance and has not asked for anything to be activated, so the
  transient default change is offered rather than taken.
- **Non-interactive installs still cover.** The step is non-destructive and self-reversing, and the
  exposure from an abandoned run is identical whether or not a terminal is attached, so withholding
  coverage from automated provisioning would cost the feature its main promise for no safety gain.
- **`spectra check`, when it offers to install, inherits the coverage step** unchanged, because it
  delegates to the install and the install's contract is now full coverage.
- **The number of installed integrations is small** (single digits), so a rotation costs seconds and
  needs no progress reporting beyond a line per integration.
- **No two Spectra runs execute concurrently in one project.** The product does not defend against a
  second run observing a transiently changed default.
- **The recorded installed list is authoritative membership**, unchanged from the previous feature.
- **Projects with one integration are the large majority**, which is why the feature must be invisible
  to them.
- **The dependency's behaviour is a dependency, not a guarantee.** Everything above rests on observed
  behaviour of a specific dependency version; that version is recorded, and an end-to-end scenario
  guards it so a change upstream is caught before release rather than by a user. Degradation on an older
  dependency is detected by the absence of the state coverage depends on, never by comparing version
  numbers — so no constant needs maintaining as the dependency moves.

## Dependencies

- **The previous feature's per-integration foundation** — the installed-integration enumeration, the
  default-integration reader, and the coverage detection introduced for the advisory. This feature
  builds directly on all three; it does not reuse the overwrite authorization gate.
- **The dependency CLI as input** — the source of the installed list, the recorded default, and the
  registration state that answers the coverage question.
- **The dependency CLI as action** — the executor of every activation, every registration, and the
  restoration of the original default.
- **The project's committed configuration as output** — written more than once during a rotation and
  restored at the end; the end state is the contract.
- **User-facing documentation and the changelog as output** — must state the new install and update
  behaviour and the recovery step for an abandoned run.
