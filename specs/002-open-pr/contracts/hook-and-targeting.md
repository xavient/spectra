# Contract: `after_implement` Hook + Base-Branch Targeting

## Part A — Hook registration contract

`github/extension.yml` MUST declare an `after_implement` hook so the offer is surfaced at install
time, mirroring how the `git` extension contributes its hooks. Spec Kit merges this into the target
project's `.specify/extensions.yml` when the extension is installed.

```yaml
hooks:
  after_implement:
    command: speckit.github.create-pr
    optional: true
    prompt: "Open a pull request for this spec?"
    description: "Offer to open a PR after implementation completes"
```

Contract rules:

- `optional: true` — the hook **offers**; it MUST NOT auto-open a PR (FR-001).
- `command: speckit.github.create-pr` — the same command available for direct on-demand invocation (FR-015).
- When merged into a project that also installs the `git` extension, this hook coexists with `git`'s
  `after_implement` auto-commit hook (both are optional; order is non-binding).

## Part B — Base-branch targeting algorithm (normative)

Input: `SourceBranch`, `PromotionFlow`, `Remote` (see [data-model.md](../data-model.md)).
Output: `TargetBranch` (base) or a STOP with explanation.

```text
1. flow_const = parse promotion flow from constitution "Version Control & Branching Strategy"
   flow_cfg   = parse promotion flow from git-config.yml (if present)

2. IF flow_const AND flow_cfg AND flow_const != flow_cfg:
       STOP → surface the conflict, ask the user which applies         # FR-013

3. flow = flow_const OR flow_cfg                                       # whichever is defined

4. IF flow is defined:
       idx = index of SourceBranch.stage in flow
       target = flow[idx + 1]                                          # next stage
       IF target does not exist on remote:
           STOP → surface missing branch; never create/retarget        # edge case
       state "Targeting <target> because the promotion flow is <flow>"  # FR-003
       RETURN target (no user re-pick needed)                          # US2 acceptance #3

5. ELSE (no flow defined):
       target = repository default branch (gh repo view / origin HEAD)
       ASK user to confirm  SourceBranch → target                      # FR-004
       IF confirmed: RETURN target  ELSE: STOP
```

Guarantees:

- 100% of PRs target the promotion-flow branch when a flow is defined (SC-002).
- 100% of no-flow PRs are opened only after explicit target confirmation (SC-003).
- The agent never silently retargets `main` when an intermediate branch applies, and never creates a
  missing target branch.
