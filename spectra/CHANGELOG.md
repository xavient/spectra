# Changelog

All notable changes to the `spectra` extension are documented here. This project follows
[Semantic Versioning](https://semver.org/).

## [1.11.0] - 2026-08-26

### Added
- **`speckit.spectra.flaky-test-detector` — find the tests that pass and fail on the same code, then fix
  the ones you approve.** The conventional way to find a flaky test is to instrument CI, collect hundreds
  of runs, and compute a score: pipeline changes, a results store, and weeks of waiting before the first
  answer. This agent needs none of it. The causes are visible in the source — an unconditional sleep
  before an assertion, an un-awaited async call, state one test leaves for another, a live network call,
  an unseeded random value, an assertion against the real clock — so it reads the test suite and names
  them, on the day you install it.

  **It never runs anything.** Not the suite, not a build, not an install, and not to verify a fix it just
  applied. That last exclusion is deliberate: an agent that can run the tests it edited is an agent that
  can iterate until green, and iterating until green is how tests get weakened. Verification stays with
  you and your CI.

  **A fix removes the cause.** Deleting an assertion, loosening one until it always passes, skipping the
  test, marking it expected-to-fail, adding a retry wrapper, or lengthening a sleep are all forbidden as
  remedies. Edits are confined to test and test-support files; where the real fix belongs in application
  code, the item is left open with a note saying what would need to change and where.

  **Two gates, and pruning in between.** The run reports a ranked table — test, file, confidence, and a
  concrete fix — and stops. On your go-ahead it writes `.specify/memory/flaky-test-analysis.md`: a run
  summary, one `[ ]` row per candidate, the evidence behind each, and what it could not examine. You
  delete the rows you disagree with. On a second go-ahead it works what is left, one item at a time,
  ticking each `[x]` on disk as it lands — so an interrupted session leaves a file that is exactly true.
  Nothing is ever committed.

  **The list outlives the session.** Every run reads that file first and branches on its state: unfinished
  work resumes without re-analysing and without discarding your pruning; a completed list asks before it
  is replaced; a file it cannot parse is never overwritten silently. There is exactly one analysis file at
  any time. Before a run scoped to one suite replaces a broader plan, it names the pending items that
  would be dropped and waits.

  Confidence is High, Medium, or Low, and it rates the strength of the evidence rather than a failure
  rate — with no run history there is no denominator, so the agent emits no percentage or score. Your
  project's own constitution binds the choice of fix: where a guardrail rules out the only remedy, the
  item is left open with that rule named.

## [1.10.0] - 2026-08-22

### Changed
- **`speckit.spectra.review-pr` no longer looks for a spec in `.specify/feature.json`.** Spec Kit now gitignores
  that file — its own CLI writes the rule, describing it as "per-checkout state rather than something to share" —
  so the second tier of the spec-discovery chain read a path that, at a pull request's head revision, is either
  missing or stale. Missing was the common case and cost nothing but a wasted call. Stale was the dangerous one: a
  project that committed the file before Spec Kit began ignoring it still carries whatever feature its last
  committer happened to be on, so the review would check the diff against **someone else's spec** and report full
  traceability while doing it. That is the exact failure the chain's ban on branch-name guessing exists to prevent.

  The tier is now **a spec you name**. When the diff carries no spec, the command asks for one and reads the path
  at the pinned head revision, falling through to the standalone review if it does not resolve there. The addendum
  case — the spec merged in an earlier pull request — stays covered, on evidence a human vouched for rather than on
  a machine-local pointer. Both forbidden guesses are now named in the command, with the reason recorded, so
  neither comes back by accident.

  **The run still asks at most one question.** When neither a spec nor an issue was found, the existing single
  context question asks for both together; `--issue` answers only its own half, so a run with no spec in the diff
  still asks for the spec. Tier 1 is untouched: a PR that ships its spec behaves exactly as in 1.9.1, and a PR with
  no spec anywhere is still reviewed standalone — traceability reported as not run, guardrails at full strength,
  intent findings capped at Question.

## [1.9.1] - 2026-08-21

### Fixed
- **An issue passed to `speckit.spectra.create-pr` now always reaches the pull request.** The rendering was
  already right — `Closes #42` when the base is the repository's default branch, a plain `#42` reference
  elsewhere, since GitHub ignores closing keywords outside the default branch — but the reference was treated
  as *presentation*. Combined with the honour-the-template rule, that meant a project whose
  `.specify/templates/overrides/pr-template.md` had no **Related Issues** section got a pull request with no
  issue link at all: `--issue 42` noted the omission in chat and opened an unlinked PR that looked complete.

  The reference is now the command's obligation rather than the template's. It goes in the template's issue
  section when there is one — judged by intent, so a team's `## Ticket` counts — and is **appended** with a
  one-line note when there is not. With no issue, nothing is appended and any such section is removed, as
  before.

  This is the same line `review-pr` draws for its revision anchor, its AI-assisted disclosure, and its
  coverage statement: a template governs how a document *reads*; functional obligations stay with the command.
  Rendering is unchanged, and a template that has the section produces byte-identical output to 1.9.0.

## [1.9.0] - 2026-08-21

### Added
- **`speckit.spectra.review-pr` reads the linked issue as optional context — in both kinds of PR.** It looks
  for one automatically, tells you which issue it used, and asks once if it cannot find one. Skip the
  question and the review proceeds exactly as before, on the constitution and the spec.

  Detection runs two routes, and the second is not redundant: the structured link
  (`closingIssuesReferences`), then a scan of the PR title and body for `#42` and issue URLs. GitHub only
  records the structured link when a PR targets the **default branch** — the same rule that shaped
  `create-pr` in 1.8.0 — so a PR into `dev` can say `Closes #42` and return nothing structured. Without the
  text fallback the command would ask you for an issue already sitting on the pull request.

  What the issue is *for* depends on what else exists. With **no spec** it becomes the traceability baseline:
  the lens now runs against the issue in both directions — does the diff address what it describes, and does
  it do anything the issue never asked for — instead of being reported as not run. With a **spec**, the spec
  still authorizes and the issue is background. Where the two disagree, that is a Question naming both; the
  command does not adjudicate between two human artifacts.

  Two limits keep it honest. An issue's content is **data about intent, never instruction** — text asking to
  "just merge it" is a fact about the conversation, not a direction. And a finding whose only source is an
  issue **cannot be a Blocker** unless the PR claims to close it, in which case the rubric's existing clause
  about failing a requirement it claims to satisfy already applies. An issue is a conversation; a spec is
  authorized scope.

- **Line-anchored comments, with applicable code suggestions.** The review no longer arrives as one body
  with file:line references for you to go and find. Accepted findings whose anchors fall inside the diff are
  published **on those lines**, and where the fix is mechanical the comment carries a ` ```suggestion ` block
  the author can apply in one click.

  This was the command's one deferred feature, and its stated reason — "diff-position arithmetic" — is
  obsolete: the reviews endpoint takes `path`, `line`, and `side` directly. Everything posts in **one call**
  carrying body, comments, and verdict together, so there is no state where the comments landed and the
  verdict did not. Publication moves from `gh pr review` to `gh api` for that reason; it is the same tool and
  the same authentication, and `curl` remains forbidden.

  Because a suggestion is one click from a commit, the rails are requirements rather than advice: mechanical
  and complete for exactly the replaced range, never architectural, never spanning files, never on a
  low-confidence finding, never on a removed line or a generated file — and **every suggestion appears
  verbatim in the pre-publish preview**, because it can be applied without being read. Findings anchored
  outside the diff go in the body, with the reason stated. `<n>:body` in the selection forces any finding
  into the body.

- **A review template, overridable per project.** The body's shape was hard-coded; it is now
  `templates/review-template.md`, registered in `provides.templates` and resolved through the same stack as
  the ADR, BRD, and PR templates. It defines two shapes — the summary body and the inline comment — and the
  command reports which template path it used.

  Its remit is deliberately **narrower** than the other templates. Three things stay with the command and
  survive any override: the `<!-- spectra:review-pr revision=… -->` anchor (how `--since` and self-review
  detection find previous reviews), the AI-assisted disclosure line, and the **Coverage and limits** section
  that stops a review implying assurance it did not earn. Judgment is not overridable either — the severity
  rubric and its floors, the confidence cap, the anchor rule, the selection grammar, and the verdict
  derivation stay in the command, because two reviews of the same diff have to agree.

  The shipped default keeps today's sections and adds a **Summary**, with `- [ ]` task items on Blockers and
  Majors only. Ticking a Question means nothing, so Minor, Nits, and Questions stay plain bullets.

### Changed
- **Coverage now says how much of the constitution applied**, not merely that the guardrail lens ran. A
  review reporting "guardrails: run" against three vague principles looks thorough and is not. It states how
  many principles were read and how many bore on this diff, says so plainly when none did, and names the
  domain-analyzer and constitution commands as the way to close that gap. An absent constitution is stated
  rather than implied.
- Coverage also records **which context authorized the review** — spec and discovery tier, issue with number,
  title and state, constitution, or the absence of each — and **what could not be placed inline**.
- The summary gained an **Issue status** line: the issue, its state, and how it was obtained.

## [1.8.0] - 2026-08-21

### Added
- **`speckit.spectra.create-pr` takes an optional `--issue`.** Pass a number or a URL (`--issue 42`,
  `--issue https://github.com/owner/repo/issues/42`) and the PR links to it. Omit it and the command asks once;
  skip the question and the PR is opened with no issue section at all. A reference that `gh issue view` cannot
  resolve is reported and dropped rather than written into the body broken.

  **The link is written differently depending on the base branch, and that is not cosmetic.** GitHub interprets
  closing keywords *only* when a PR targets the repository's default branch — on any other base the keywords are
  ignored, no link is created, and merging closes nothing. So a `Closes #42` on a PR into `dev` would look
  correct and do nothing. The command writes a closing keyword only when the base is the default branch;
  otherwise it writes a plain `#42` reference, which still records a cross-reference on the issue, and tells you
  auto-close will not happen on this merge. An issue in another repository is referenced by full URL, never with
  a keyword.

- **The PR body now comes from an overridable template.** `templates/pr-template.md` ships with the extension,
  is registered in `provides.templates`, and resolves through the same stack as the ADR and BRD templates:
  project override → presets → extension → core → an inline skeleton. Drop
  `.specify/templates/overrides/pr-template.md` into your project and every PR follows your structure —
  committed, team-wide, and surviving extension updates.

  Sections: Summary, Related Issues, Type of Change, Changes, How to Test, Screenshots / Evidence, Breaking
  Changes, Notes for Reviewers. **Deliberately no self-certification checklist** — an agent cannot honestly tick
  "I have self-reviewed the full diff". If your override reintroduces one, the command leaves those boxes
  unchecked and says it left them for you.

- **One final confirmation before anything is created.** The command summarizes source → base and where the base
  came from, the linked issue or nothing, draft or ready, the resolved template path, and anything it has
  already done — then asks once. Confirmations that used to be scattered now happen in one place.

### Changed
- **Uncommitted work is offered a commit instead of a warning.** Previously the command surfaced a dirty tree,
  warned that the PR would exclude it, and explicitly would not commit. It now lists the files and asks *"there
  are uncommitted changes, should I proceed with committing and pushing first?"* — and on a yes behaves like any
  ordinary commit-and-push request. Rails: the file list is shown before staging, credential-shaped names
  (`.env`, `*.pem`, `id_rsa`, `credentials*`) are called out for a specific go-ahead, nothing is blind-`git
  add -A`'d beyond what you saw, and `--no-verify` is never used — a hook that rejects the commit stops the run
  with the hook's own message. Answer no and the PR is opened from committed work with the exclusion stated
  plainly.

  This widens the command's write scope, which is worth saying out loud: it may now create a commit on your
  behalf, with your explicit consent, in addition to pushing and opening the PR. It still never edits source,
  the spec, the plan, the tasks, or the constitution.

- **The base branch: documented intent wins, and a guess is confirmed rather than assumed.** A promotion flow in
  the constitution or `.specify/extensions/git/git-config.yml` is used and cited, as before. With nothing
  documented, the command proposes a base — the branch this one appears to have been cut from, else the default
  branch — and asks at the final gate: *"This PR will be created to merge into `main`. Is that correct?"* You can
  redirect it in the same breath, and the corrected base is re-checked on the remote before use.

  The reason it asks rather than decides: **Git records no parent branch.** `@{upstream}` is the tracking branch,
  and `git merge-base --fork-point` reads the reflog, so it yields nothing in a fresh clone or CI checkout and
  nothing useful when two candidates share a commit.

- **It works from any branch now.** The one-branch-per-spec refusal is gone: a `fix/…` or chore branch can open a
  PR. Only two refusals remain — detached HEAD, and a branch that is already the resolved base. A spec branch is
  still better served: it contributes `spec.md`, `plan.md`, and `tasks.md` to the body, where other branches
  contribute their commits. Either way the **Changes** section comes from the real diff
  (`git diff --name-status <base>...HEAD`), not from a restatement of the plan.

- Constitution **1.7.1** clarifies Principle VIII: a deliverable is the document, not the destination, so a PR
  body a command emits is shaped by a template exactly as a file written to disk is. Only Principle VII's
  *location* rules are limited to files.

Every earlier guarantee is intact: the hard `gh` gate before anything else, GitHub-only scope, the duplicate-PR
check, `--head` always explicit, `--body-file -` for the body, and post-gate degradation that states exactly what
was mutated.

## [1.7.0] - 2026-08-21

### Added
- **Both document agents are now driven by an overridable template.** `speckit.spectra.adr` used to carry its
  structure as a literal block inside the command file — there was no file to change. It now ships as
  `templates/adr-template.md`, alongside the BRD template, and both are declared in `extension.yml` under
  `provides.templates`.

- **`.specify/templates/overrides/<name>.md` is the supported way to customize them.** Drop
  `.specify/templates/overrides/adr-template.md` (or `brd-template.md`) into your project, edit it, commit it —
  every document produced from then on follows your structure, on every teammate's machine. Add the sections
  your governance needs, or delete ones you don't want.

  Both commands now resolve their template through Spec Kit's stack, first usable layer wins: project override
  → installed presets → this extension → core `.specify/templates/` → the command's inline skeleton as a last
  resort. A layer that exists but is empty or unreadable is reported and skipped rather than being fatal.

  **This is the part that was broken before.** `brd` read the extension's copy at a hard-coded path, so an
  override was silently ignored, which left editing the installed copy as the only lever — and that edit does
  not survive: extension files are replaced wholesale when the extension updates. Because the path is tracked
  by Git, the edit looks durable and then reverts later inside an unrelated diff. An override lives outside the
  extension tree and survives.

- **Each command reports which template it used**, by path. An override that silently failed to apply
  otherwise looks exactly like one that worked, and the first clue would be a wrongly-shaped document.

### Changed
- **A resolved template is honoured, not repaired.** If your override renames, renumbers, drops, or adds
  sections, the command follows *your* structure and mentions once what it left out, instead of quietly
  reinstating it. Where your template adds sections, they are filled from the same gathered context; where
  there is genuinely nothing to say, the command says so rather than inventing content.

- **The ADR's section list is unchanged**: Context, Decision, Consequences, with the same `Date` and `Status`
  header. With no override in place, output is structurally identical to 1.6.0. Enriching the default was
  deliberately left out of this release — now that every project can add sections itself, changing the shipped
  default would have altered everyone's output while claiming to be additive.

- Constitution **Principle VIII — Documents Are Shaped by Overridable Templates** (constitution 1.7.0) records
  the rule so future document agents inherit it: the structure comes from a registered template resolved
  through the stack, with an inline fallback and never a hard-coded path; the resolved template is honoured as
  authored; the command names the template it used. Resolution stays prompt-expressed, because calling Spec
  Kit's Bash `resolve_template()` would break agent-agnosticism and shipping a resolver of our own would break
  the Markdown-only guarantee — the package still contains no scripts, no binaries, and no hooks.

## [1.6.0] - 2026-08-21

### Changed
- **ADRs and BRDs now go to one place: `docs/adr/` and `docs/brd/`.** `speckit.spectra.adr` used to write
  `Docs/ADR/ADR-NNN-*.md` and `speckit.spectra.brd` used to write `/brds/NNN-*.md` — two different parent
  folders, two different capitalizations, and one path that named the filesystem root rather than the
  project. Both now write under a single root, project-relative and lowercase, one subfolder per artifact
  type. Filenames are unchanged: `docs/adr/ADR-NNN-<title>.md` and `docs/brd/NNN-<title>.md`. The root
  itself is a project setting — see **Added** below.

  The lowercasing is a fix, not a preference. `Docs/ADR/` is a distinct directory on Linux but silently
  aliases into an existing `docs/` folder on a case-insensitive macOS filesystem, so the same command
  produced different layouts on different machines.

- **Existing projects keep their numbering, and their old folder.** Both commands still read the earlier
  locations — `Docs/ADR/` (matched case-insensitively), `brds/`, and `docs/<artifact>/` when a project
  declares a different root — for context and for the next number, so the sequence after this update
  continues from the highest artifact found across old and new instead of restarting at `001`. Those folders
  are read-only to the agent: it reports them once, offers a `git mv` you can run, and moves nothing itself.
  If a new ADR supersedes one that still lives in an earlier folder, the supersession is recorded in the new
  ADR and reported to you rather than written into the old file.

- **Every write scope is unchanged in size.** `brd` still writes exactly one file; `adr` still writes one
  ADR plus, only with your agreement, the superseded-status line and a constitution edit.

### Added
- **A project can move the artifact root with one line.** `docs/` is the default, not a hard-coded path.
  Put this in `.specify/memory/constitution.md` and every Spectra document agent — these two and every one
  we ship later — writes there instead:

  ```text
  Artifact root: documents/
  ```

  The commands offer that line but never write it themselves: producing a document is not a licence to edit
  governance.

- **A publication check before defaulting into `docs/`.** `docs/` is GitHub Pages' only non-root branch
  source and the default source directory for MkDocs and Docusaurus, so on some projects writing there
  publishes the document or breaks a docs build. Both commands now look for that signal — `mkdocs.yml`,
  `docusaurus.config.*`, `docs/_config.yml`, `docs/.nojekyll`, `docs/index.html`, `docs/conf.py`, or a Pages
  configuration pointing at `docs` — and when they find one with no declared root, they say so before
  writing, recommend `documents/`, and ask. Unanswered, they take the non-publishing option: a misplaced
  private file is one `git mv` away, while a BRD served on the public web cannot be recalled from caches or
  forks. The question does not count against either command's five-question limit, because it is about
  where to write rather than what to record.

- **Constitution Principle VII — Document Artifacts Live Under One Declared Root** (constitution 1.6.0).
  Every command producing a durable Markdown deliverable writes it to `<artifact-root>/<artifact>/` with a
  lowercase kebab-case slug, one artifact type per folder, three-digit numbering. Spec Kit's own
  `.specify/` and `specs/` are carved out, so `speckit.spectra.domain-analyzer` writing
  `.specify/memory/domain-analysis.md` stays compliant — that is context for another command, not a
  deliverable. The point is forward-looking: the roster has a dozen more document producers under
  development, and each one now inherits its output location instead of choosing a new top-level folder.

## [1.5.0] - 2026-08-19

### Changed
- **`speckit.spectra.create-pr` now hard-stops when `gh` is missing or unauthenticated**, instead of
  degrading to a printed manual fallback. The check runs as the first thing after you accept the offer —
  before the constitution is read, before a target branch is derived, before any `git` command — and it
  names which of the two failed, because the remedies differ: install the GitHub CLI, or run
  `gh auth login`. Nothing is mutated on that path, and when `gh` is absent the message no longer prints
  a `gh` command line; the only alternative it names is the GitHub web interface.

  This **reverses the difference recorded in 1.4.0**, where `create-pr` degrading was described as a
  deliberate contrast with `review-pr`. That justification does not survive contact with the two
  failures it was meant to serve. The printed fallback told the user to run `gh pr create` — the command
  they demonstrably did not have — and the duplicate-PR check is itself a `gh` call, so a run without
  `gh` could walk them into a second pull request for a branch that already had one. Both GitHub
  commands now gate identically. What differs is only what each hands over *after* the gate.

- **A refusal after the gate now degrades properly, and says what it changed.** A protected base branch,
  a token without push permission, or a fork restriction is reported with the underlying `git`/`gh`
  message, the manual commands including the derived base branch — runnable, because `gh` is present
  here — and, critically, the mutation state: *nothing reached the remote*, or *the branch is on the
  remote and no pull request exists*. The command previously had no instructions for this case at all,
  even though by then it may already have pushed.

- **A remote that is absent or not on `github.com` is now a stop with a scope statement**, not a
  degradation, and prints no `gh` fallback — there is nothing `gh` can do with a GitLab remote. GitHub
  Enterprise is named as out of scope rather than half-attempted.

- **The pull request body is passed on standard input** (`--body-file -`) rather than as a
  command-line argument, so spec prose carrying backticks, code fences, quotes, and blank lines reaches
  the pull request unaltered. `review-pr` already published review bodies this way.

- **Fork detection is read from the repository, not guessed from the URL.** One
  `gh repo view --json nameWithOwner,isFork,parent,defaultBranchRef,viewerPermission` call replaces the
  previous "if `origin` looks like a fork" heuristic *and* the separate default-branch lookup. Forks and
  multi-remote setups are still resolved by asking, and now for a stated reason: `gh pr list --head`
  rejects `<owner>:<branch>` while `gh pr create --head` accepts it, so an inferred fork flow would
  check for duplicates against one head and open against another.

- **`gh` is declared as the only route to GitHub** in the command's governing rule — no `curl`, no
  direct REST calls — matching `review-pr`.

`gh` remains **optional at the extension level**: `adr`, `brd`, and `domain-analyzer` never touch
GitHub, so requiring it would block installation for users who only want those.

A command changed behaviour, no argument or output contract did, which is why this is a MINOR.

## [1.4.0] - 2026-08-17

### Added
- **`speckit.spectra.review-pr` — a reviewing agent for the last manual gate in the lifecycle.** It
  reviews a GitHub pull request against **the intent and standards the PR carries**: the spec, plan,
  tasks, and ADRs read at the PR's own head revision, plus the constitution and ADRs in force on the
  **base** branch. That is what lets it report a task marked complete but absent from the diff, scope
  no requirement authorized, or a pattern an ADR forbids — none of which a diff-only reviewer can see.

  Two properties define it:

  - **Every finding is anchored and sourced.** A file, a line, and the clause, requirement id, or named
    principle it rests on. A finding that cannot be anchored and sourced is not reported at all.
  - **The human is the filter.** Nothing is pre-selected. The reviewer chooses which findings are
    published and which verdict to submit, sees the exact body first, and gives a final go-ahead before
    anything is posted. An empty selection posts nothing and is a normal outcome. Approving over a
    blocker the reviewer accepted requires a typed confirmation and is recorded in the published review.

  Findings are graded Blocker / Major / Minor / Nit / Question from a fixed rubric so repeated reviews of
  one revision agree, with floors that keep an explicit constitution violation at Major or above and an
  explicit compliance violation at Blocker. Low confidence cannot be a Blocker — it becomes a Question.

  Publication is a single review event through the reviewer's own `gh` authentication. The agent holds no
  credentials, adds no data path, and stores nothing between runs.

  Two behaviours differ from `create-pr` on purpose:

  - **It hard-stops when `gh` is missing or unauthenticated** rather than degrading, because a review's
    value is the analysis and the analysis needs the PR. Failures *after* that gate — a fork
    restriction, insufficient permission — still degrade gracefully to a rendered body for manual
    posting.
  - **It registers no hook.** Review is on demand only, since the reviewer should not be the author.

  GitHub only in this release, and single-body reviews only — line-anchored inline comments are a
  follow-on.

A command was added, which is why this is a MINOR.

## [1.3.1] - 2026-08-09

### Changed
- **The extension description is now the positioning line used everywhere else:** "TELUS Digital -
  Agentic software engineering across the entire SDLC." It previously enumerated the four shipped
  commands, which meant it needed editing every time an agent was added and disagreed with the
  wording on the landing page and in the README. One line, one place, no drift.
- **The Commands table in `README.md` is generated** from the new root `agents-list.json` roster
  rather than maintained by hand. The region is marked with
  `<!-- SPECTRA:GENERATED START id=spectra-readme-commands -->`; everything around it, including the
  four per-agent sections, stays hand-written. Its Effect column is dropped — `effect: read-write` is
  declared once for the extension in `extension.yml`.
- **The PR agent is titled "GitHub (PR)" everywhere.** It previously appeared as `github`, GitHub,
  GitHub (PR), and "GitHub PR delivery" across four documents. Its command is unchanged:
  `speckit.spectra.create-pr`.

No command was added, changed, or removed, which is why this is a PATCH.

## [1.3.0] - 2026-08-08

### Changed
- **Relicensed from MIT to the Apache License 2.0.** Spectra stays free to use, modify, and
  redistribute for any purpose, including commercially. Apache-2.0 adds an explicit patent grant and
  makes attribution enforceable: redistributions and derivative works must retain the copyright
  notice, ship the `LICENSE` and `NOTICE` files, and state which files were changed
  (§4(b)–4(d)).

### Added
- `NOTICE` — the attribution notice that downstream redistributors are required to carry forward
  under Apache-2.0 §4(d). It now ships inside the extension package.

## [1.2.0] - 2026-07-14

### Added
- **`speckit.spectra.brd`** — a Requirements & Discovery-phase command that transforms a raw business
  requirement (inline text or a `.docx`/`.pdf`/`.md`/`.txt` document) into a structured,
  specify-ready BRD written under `/brds`. It reads project context to ground the document, asks up to
  five clarifying questions only when the requirement has material gaps, never invents requirements
  (genuine unknowns become Open Questions), and hands off to the Spec Kit **specify** command. Its only
  write is the BRD file.
- Bundled the canonical BRD template as `templates/brd-template.md` so the command produces the same
  structure in any installed project.

## [1.1.0] - 2026-07-09

### Changed
- Consolidated the previously separate `adr`, `domain-analyzer`, and `github` extensions into a
  single `spectra` extension. Every capability is now a command under the unified `speckit.spectra.*`
  namespace, matching Spec Kit's `speckit.<extension-id>.<command>` rule (the extension `id` is
  `spectra`):
  - `speckit.adr.new` → `speckit.spectra.adr`
  - `speckit.domain-analyzer.analyze` → `speckit.spectra.domain-analyzer`
  - `speckit.github.create-pr` → `speckit.spectra.create-pr`
- Install once with `specify extension add spectra` to get all three commands. The `after_implement`
  hook now invokes `speckit.spectra.create-pr`.

### Commands
- **`speckit.spectra.adr`** — Create a context-aware Architecture Decision Record grounded in the
  codebase, prior ADRs, and the project constitution; asks up to five clarifying questions and writes
  the ADR under `Docs/ADR/`.
- **`speckit.spectra.domain-analyzer`** — Infer the project's business domain and write an opt-in
  proposal of evidence-backed candidate guardrails to `.specify/memory/domain-analysis.md` for SME
  review and handoff to `/speckit-constitution`. Never edits the constitution or source.
- **`speckit.spectra.create-pr`** — Offer to open a correctly-targeted GitHub PR for the current spec
  branch after `implement`, deriving the base branch from the promotion strategy, confirming before
  any push, and returning the PR URL — with a graceful manual fallback when `gh`, the remote, or the
  network is unavailable.
