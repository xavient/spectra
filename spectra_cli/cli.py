"""Command-line entry point for `spectra`.

The command surface has one organizing rule: **a top-level verb acts on the stack you are standing in;
only `spectra cli …` acts on the machine's copy of the tool.**

    spectra install | check | version | update | uninstall | agent-list   the project's stack
    spectra cli uninstall                                                 the spectra command

Bare `spectra` stays informational — it prints the banner and points at `--help`, the way the
`specify` CLI does, and never touches the current folder. Because the banner carries the CLI's own
version, it is also the way to read that version from a directory that is not a Spec Kit project.

`--version`, `--update`, and `--uninstall` were removed in 5.0.0. They reported on the *tool*, which
is the number a user is least likely to care about, and they left the two independently-versioned
channels competing for the same three words. They are detected before parsing so the error can name
the replacement, which argparse cannot do for an argument it no longer defines.

`spectra cli version` and `spectra cli update` were retired in 6.0.0 for the same reason, one level
down: `spectra version` and `spectra update` now cover all four parts of the stack — Spec Kit's CLI, the
core agents, this command, and Spectra's agents — so a separate tool-scoped pair had nothing left to
mean. Both remain registered so typing one names its replacement.

Flags shared by more than one subcommand are declared once and attached to each, with `SUPPRESS`
defaults on the subcommand copies so that `spectra --yes install` and `spectra install --yes` mean the
same thing — without a subcommand's default silently overwriting a value the top level already parsed.
"""

from __future__ import annotations

import argparse
import os
import sys

from spectra_cli import extension, health, install, net, project, roster, ui, version

# The help surface, rendered by `print_help()` into Spectra-purple panels rather than by argparse's
# plain formatter. Keeping the copy here (not in `add_argument(help=...)`) keeps the rendered table and
# the parser reading from one list — and the two panel titles are what make the project/tool split
# evident to a first-time reader instead of something they have to infer from the verbs.
OPTIONS = [
    ("--yes", "-y", "Answer yes to prompts (installing, uninstalling)."),
    ("--force", "", "Overwrite managed files that have been modified locally (spectra update)."),
    ("--no-update-check", "", "Skip the check for a newer spectra command."),
    ("--help", "-h", "Show this message and exit."),
]

PROJECT_COMMANDS = [
    ("install", "Install Spectra into the Spec Kit project in this folder. Installs the "
                "Spec Kit CLI and initializes the project first if needed."),
    ("check", "Report whether Spectra is installed in this project, and offer to install it "
              "when it is not."),
    ("version", "Check every part of the Spectra stack: the Spec Kit CLI, the core agents, the "
                "spectra command, and the agents installed here."),
    ("update", "Bring every out-of-date part of the Spectra stack current, after one "
               "confirmation."),
    ("uninstall", "Remove Spectra's agents from this project. Leaves the spectra command "
                  "installed on this machine."),
    ("agent-list", "List every agent Spectra offers, grouped by SDLC phase. Reads the published "
                   "roster, so it works from anywhere."),
]

TOOL_COMMANDS = [
    ("cli uninstall", "Remove the spectra command from this machine. Extensions in your projects "
                      "are left untouched."),
]

# Registered with the parser but retired: dispatching to a handler that names the replacement is more
# useful than argparse's "invalid choice". Kept out of TOOL_COMMANDS so they vanish from help.
RETIRED_TOOL_SUBCOMMAND_NAMES = ("version", "update")

# Removed in 5.0.0. argparse cannot name a replacement for an argument it no longer defines — it emits
# "unrecognized arguments" and stops — so these are matched in argv before parsing.
#
# In 5.0.0 each named *two* candidates, because the ambiguity between a tool-scoped and a project-scoped
# reading was precisely why the flags went. 6.0.0 resolved that ambiguity by retiring the tool-scoped
# pair, so `--version` and `--update` now have exactly one answer each. `--uninstall` still has two,
# because removing the agents from a project and removing the command from the machine remain genuinely
# different actions.
REMOVED_FLAGS = {
    "--version": ("spectra version",),
    "-V": ("spectra version",),
    "--update": ("spectra update",),
    "--uninstall": ("spectra uninstall", "spectra cli uninstall"),
}

COMMANDS = PROJECT_COMMANDS  # kept for the subparser loop below

# Exit codes. 0-4 and 130 are already the tool's conventions; 5 is new, and exists so a caller can
# tell "I could not answer" from "the answer is no".
EXIT_OK = 0
EXIT_DECLINED = 1        # the user declined an offered action
EXIT_USAGE = 2           # bad flag or unknown command (argparse's convention)
EXIT_UNREACHABLE = 3     # published data could not be retrieved
EXIT_DELEGATION = 4      # a delegated `specify` or `uv` command failed
EXIT_PROJECT_STATE = 5   # the project is not in the required state
EXIT_INTERRUPTED = 130


class _Parser(argparse.ArgumentParser):
    """Parser whose argument errors are reported in Spectra's palette, not argparse's.

    On a bad flag or an unknown command, show the error and then the same panels `--help`
    prints — argparse's terse `usage:` synopsis is less useful here than the full table.
    Exit code stays 2, argparse's convention, so scripts still read it correctly.
    """

    def error(self, message):
        ui.plain()
        ui.fail(f"{self.prog}: {message}")
        ui.plain()
        print_help()
        raise SystemExit(2)


def _add_shared(parser, *, suppress: bool = False) -> None:
    """Attach the flags that are meaningful both before and after a subcommand.

    On a subcommand the defaults are suppressed rather than set. argparse writes a subparser's
    defaults into the same namespace *after* the top level has parsed, so a plain `default=False`
    here would make `spectra --yes install` lose its `--yes`.
    """
    default = argparse.SUPPRESS if suppress else False
    parser.add_argument("--yes", "-y", dest="yes", action="store_true", default=default)
    parser.add_argument("--no-update-check", dest="no_update_check", action="store_true",
                        default=default)
    parser.add_argument("--help", "-h", dest="help", action="store_true", default=default)


def build_parser() -> argparse.ArgumentParser:
    ap = _Parser(
        prog="spectra",
        description="Install and manage Spectra's agents in this project.",
        add_help=False,  # `--help` is handled in _dispatch so the banner prints above it.
    )
    _add_shared(ap)

    subcommands = ap.add_subparsers(dest="command", metavar="COMMAND")
    for name, _ in PROJECT_COMMANDS:
        parser = subcommands.add_parser(name, add_help=False)
        _add_shared(parser, suppress=True)
        if name == "update":
            # Registered here rather than in `_add_shared` on purpose. `--force` authorizes overwriting a
            # team's modified files, and it is meaningful for exactly one command; putting it in the
            # shared set would make `spectra uninstall --force` parse, where "force" already means
            # something far weaker (skip a confirmation). One word, two weights, is how a destructive
            # flag gets typed by accident.
            parser.add_argument("--force", dest="force", action="store_true",
                                default=argparse.SUPPRESS)

    # The tool's own management lives one level down, so no top-level verb can be mistaken for it.
    group = subcommands.add_parser("cli", add_help=False)
    _add_shared(group, suppress=True)
    tool = group.add_subparsers(dest="cli_command", metavar="SUBCOMMAND")
    for label, _ in TOOL_COMMANDS:
        _add_shared(tool.add_parser(label.split()[1], add_help=False), suppress=True)
    # Retired, but still registered: a named replacement beats "invalid choice".
    for name in RETIRED_TOOL_SUBCOMMAND_NAMES:
        _add_shared(tool.add_parser(name, add_help=False), suppress=True)
    return ap


# --------------------------------------------------------------------------- #
# Help
# --------------------------------------------------------------------------- #
def _option_label(long: str, short: str) -> str:
    """A padded, colored `--long  -s` label, aligned across every option row."""
    long_w = max(len(lo) for lo, _, _ in OPTIONS)
    pad = " " * (long_w - len(long))
    short_cell = f"{ui.GREEN}{short}{ui.RESET}" if short else "  "
    return f"{ui.PURPLE}{long}{ui.RESET}{pad}  {short_cell}"


def print_help() -> None:
    """Render the help screen: usage line, then three panels.

    The panels are the contract: **Project commands** act on the agents installed in the current
    project, **Tool commands** act on the `spectra` command itself. Two panels rather than one is what
    lets a first-time reader tell which is which without reading the descriptions.
    """
    ui.plain(f"{ui.BOLD}Usage:{ui.RESET} {ui.BOLD}spectra{ui.RESET} [OPTIONS] COMMAND [ARGS]...")
    ui.plain()
    ui.plain("  Install and manage Spectra's agents in this project.")
    ui.plain()
    ui.panel("Project commands — act on the Spectra stack you are standing in",
             [(f"{ui.CYAN}{name}{ui.RESET}", desc) for name, desc in PROJECT_COMMANDS])
    ui.panel("Tool commands — act on the spectra command itself",
             [(f"{ui.CYAN}{name}{ui.RESET}", desc) for name, desc in TOOL_COMMANDS])
    ui.panel("Options", [(_option_label(lo, sh), desc) for lo, sh, desc in OPTIONS])
    ui.plain()
    ui.plain(ui.dim("  Run project commands from inside the project — a folder containing .specify/."))
    ui.plain(ui.dim("  Not initialized yet? `spectra install` offers to set one up."))


def print_cli_group_help() -> None:
    """`spectra cli` with no subcommand: say what lives here, and what does not.

    One row now. `version` and `update` moved up to the top level in 6.0.0, where they cover the whole
    stack instead of just the tool — so this group is down to the one action that is genuinely about the
    machine's copy of the command rather than about any project.
    """
    ui.plain(f"{ui.BOLD}Usage:{ui.RESET} {ui.BOLD}spectra cli{ui.RESET} SUBCOMMAND")
    ui.plain()
    ui.plain("  Manage the spectra command itself. To check or update your stack — including this")
    ui.plain("  command's own version — use the top-level commands instead (see `spectra --help`).")
    ui.plain()
    ui.panel("Tool commands",
             [(f"{ui.CYAN}{label.split()[1]}{ui.RESET}", desc) for label, desc in TOOL_COMMANDS])
    ui.plain()


def _report_removed_flag(flag: str) -> int:
    """Name the replacement rather than emitting a bare unrecognized-argument error."""
    replacements = REMOVED_FLAGS[flag]
    ui.plain()
    ui.fail(f"spectra: {flag} was removed in 5.0.0.")
    if len(replacements) == 1:
        ui.plain(f"  Use instead:             {ui.bold(replacements[0])}")
    else:
        ui.plain(f"  For your agents:         {ui.bold(replacements[0])}")
        ui.plain(f"  For the command itself:  {ui.bold(replacements[1])}")
    ui.plain()
    ui.plain(ui.dim("  Top-level commands act on the stack you are standing in; "
                    "`spectra cli …` acts on the tool."))
    ui.plain()
    return EXIT_USAGE


def _update_check_disabled(args) -> bool:
    """True when the user opted out of contacting GitHub for a version comparison.

    Honoured by both `--version` and the start-of-run nudge, so air-gapped and CI runs never
    pay for a network round trip they did not ask for.
    """
    return bool(args.no_update_check or os.environ.get("SPECTRA_NO_UPDATE_CHECK"))


# --------------------------------------------------------------------------- #
# Retired tool subcommands
# --------------------------------------------------------------------------- #
# Retired in 6.0.0. Their jobs were absorbed by the top-level commands: `spectra version` now reports
# the CLI's own version alongside the other three components, and `spectra update` updates it alongside
# them. Unlike the *flags* removed in 5.0.0 — which had to be caught in argv, because argparse cannot
# name a replacement for an argument it no longer defines — these stay registered with the parser so
# that typing one gets a message naming its replacement rather than a bare "invalid choice".
RETIRED_TOOL_SUBCOMMANDS = {
    "version": "spectra version",
    "update": "spectra update",
}


def _report_retired_subcommand(subcommand: str) -> int:
    replacement = RETIRED_TOOL_SUBCOMMANDS[subcommand]
    ui.plain()
    ui.fail(f"`spectra cli {subcommand}` has been retired. Use `{replacement}` instead.")
    ui.plain()
    ui.plain(ui.dim(f"  {replacement} now covers the whole stack — the Spec Kit CLI, the core agents,"))
    ui.plain(ui.dim("  the spectra command itself, and your agents."))
    ui.plain()
    return EXIT_USAGE


def cmd_cli_version(args=None) -> int:
    """Retired in 6.0.0; absorbed into `spectra version`."""
    return _report_retired_subcommand("version")


def cmd_cli_update(args=None) -> int:
    """Retired in 6.0.0; absorbed into `spectra update`."""
    return _report_retired_subcommand("update")


# --------------------------------------------------------------------------- #
# cli uninstall (the tool removes itself)
# --------------------------------------------------------------------------- #
def cmd_cli_uninstall(args) -> int:
    """Remove the uv-installed tool.

    Exit 0 iff spectra ends up not installed as a uv tool (removed, or already absent);
    non-zero when action is still needed (declined, uv missing, or removal failed). Nothing
    inside the user's project is touched — installed extensions stay where they are.
    """
    kind = version.classify_uninstall()

    # Not a uv tool -> idempotent no-op (source checkout or pip install).
    if kind in (version.NOT_INSTALLED, version.PIP_OR_SOURCE):
        ui.info("spectra is not installed as a uv tool, so there is nothing to uninstall.")
        if kind == version.PIP_OR_SOURCE:
            ui.plain(ui.dim("This looks like a source or pip install; remove it with the Python "
                            "tooling you installed it with."))
        else:
            ui.plain(ui.dim("You appear to be running from a source checkout."))
        return 0

    # Installed as a distribution but uv cannot be located -> manual step required.
    if kind == version.UNKNOWN_UV_ABSENT:
        ui.fail("uv was not found on PATH, so spectra cannot uninstall itself automatically.")
        ui.plain("Remove it manually with:\n    "
                 + ui.bold(f"uv tool uninstall {version.DIST_NAME}"))
        return 4

    # kind == UV_MANAGED: gate on confirmation, then remove.
    if not args.yes:
        if not sys.stdin.isatty():
            ui.fail("Refusing to uninstall without confirmation in a non-interactive session.")
            ui.plain("Re-run with " + ui.bold("--yes") + " to skip the prompt.")
            return 2
        ui.warn("This will remove the spectra command from this machine.")
        ui.plain(ui.dim("Extensions already installed into your projects are left untouched."))
        if not ui.confirm("Uninstall spectra now?", default_yes=False):
            ui.info("Cancelled. Nothing was removed.")
            return 1

    ui.info("Removing spectra via uv …")
    try:
        version.perform_uninstall()
    except version.UninstallError as e:
        ui.fail(f"Uninstall failed: {e}")
        return 4
    ui.ok("spectra has been uninstalled.")
    return 0


# --------------------------------------------------------------------------- #
# Install (no mode flag)
# --------------------------------------------------------------------------- #
def _start_of_run_update_nudge(args) -> None:
    """Best-effort, non-blocking update offer at the start of an interactive run.

    Skipped when --no-update-check / SPECTRA_NO_UPDATE_CHECK is set, or when not attached to a
    TTY. Answering yes updates and exits (the running process is the old code); answering no
    continues on the current version.
    """
    if _update_check_disabled(args):
        return
    if not sys.stdin.isatty():
        return
    newer = version.passive_check(timeout=2)
    if not newer:
        return
    installed = version.read_installed_version() or "unknown"
    ui.info(f"A new version {ui.bold(newer)} is available (you have {installed}).")
    if not ui.confirm("Do you want to update now?", default_yes=False):
        return
    try:
        version.perform_update(newer)
    except version.UpdateError as e:
        ui.fail(f"Update failed: {e}")
        ui.warn("Continuing with the current version.")
        return
    ui.ok(f"Updated to {ui.bold(newer)}. "
          "Please re-run " + ui.bold("spectra") + " to use the new version.")
    raise SystemExit(0)


def cmd_install(args) -> int:
    ui.splash(version.read_installed_version() or "unknown")
    _start_of_run_update_nudge(args)
    return install.run_install()


# --------------------------------------------------------------------------- #
# Project state, reported the same way by every project-scoped command
# --------------------------------------------------------------------------- #
def _say_not_a_project() -> int:
    """Not a Spec Kit project at all — a different problem, with a different remedy, from
    "a Spec Kit project without Spectra". Conflating the two would send the user to the wrong fix.
    """
    ui.fail("This is not a Spec Kit project — no .specify/ directory here or in any parent folder.")
    ui.plain("  Initialize one:   " + ui.bold("specify init"))
    ui.plain("  Then add Spectra: " + ui.bold("spectra install"))
    return EXIT_PROJECT_STATE


def _say_not_installed(state) -> int:
    ui.warn(f"Spectra is not installed in this project ({state.project_root}).")
    ui.plain("  Install it with: " + ui.bold("spectra install"))
    return EXIT_PROJECT_STATE


def _say_incomplete(state) -> int:
    """The folder is present but tells us nothing — an interrupted or partially written install."""
    ui.fail("Spectra's extension folder is here but unusable — this looks like an interrupted "
            "install.")
    ui.plain(ui.dim(f"  Folder: {state.extension_dir}"))
    ui.plain("  Repair it with: " + ui.bold("spectra update"))
    return EXIT_PROJECT_STATE


# --------------------------------------------------------------------------- #
# check
# --------------------------------------------------------------------------- #
def cmd_check(args) -> int:
    """Answer "is Spectra available here?" definitively, and offer the fix when it is not."""
    state = project.classify()

    if state.state == project.NOT_A_PROJECT:
        return _say_not_a_project()
    if state.state == project.INCOMPLETE:
        return _say_incomplete(state)
    if state.state == project.INSTALLED:
        ui.ok(f"Spectra is installed here (extension {ui.bold(state.installed_version)}).")
        ui.plain(ui.dim(f"  Project: {state.project_root}"))
        ui.plain(ui.dim("  Check whether the agents are current with: spectra version"))
        return EXIT_OK

    # NOT_INSTALLED — the one state this command can fix, so offer rather than just report.
    ui.warn(f"Spectra is not installed in this project ({state.project_root}).")
    ui.plain()
    if not args.yes:
        if not sys.stdin.isatty():
            ui.plain("  Install it with: " + ui.bold("spectra install"))
            ui.plain(ui.dim("  Re-run with --yes to install without being asked."))
            return EXIT_DECLINED
        if not ui.confirm("Install Spectra into this project now?"):
            ui.info("Nothing was changed.")
            ui.plain("  Install it later with: " + ui.bold("spectra install"))
            return EXIT_DECLINED

    code = cmd_install(args)
    return EXIT_OK if code == 0 else EXIT_DELEGATION


# --------------------------------------------------------------------------- #
# Presenting stack health
# --------------------------------------------------------------------------- #
def _transition(component) -> str:
    """`0.12.14 -> 0.16.4`, or just the one version when there is only one to show."""
    if component.installed and component.latest:
        return f"{ui.bold(component.installed)} {ui.dim('->')} {ui.bold(component.latest)}"
    return ui.bold(component.installed or component.latest or "unknown")


def _detail_phrase(component) -> str:
    """The component's explanation, trimmed to sit inside parentheses.

    Details are written as sentences so they read well on their own, but they get embedded in
    `unknown (…)` here — so the trailing full stop would otherwise produce `(reason.)`.
    """
    detail = (component.detail or "status could not be determined").strip()
    return detail[:-1] if detail.endswith(".") else detail


def _behind_names(component) -> str:
    """`" — kiro-cli, claude"` when a plural row is behind, else `""`.

    The row has to name the integrations that are behind (FR-008), and it cannot delegate that to the
    breakdown: when every integration is behind at the *same* version the children are uniform and the
    breakdown is correctly suppressed — which is exactly the state a drifted project is usually in. Names
    on the row are therefore the only place that information is guaranteed to appear.

    Empty for the three singular components and for the single-record fallback, whose one child has no
    key to name.
    """
    names = [part.key for part in component.parts
             if part.key and part.status == health.NEEDS_UPDATING]
    return f" — {', '.join(names)}" if names else ""


def _integration_child_rows(component):
    """One `(label, glyph, phrase)` per integration beneath the `Core agents` row.

    Reuses `_status_row`'s phrasing by construction — a child is rendered by the same function as its
    parent, with the integration's key as the label — so the wording of a child and a row cannot drift
    apart as one of them is reworded.

    Returns `()` unless the breakdown has earned its place: more than one integration **and** children
    that are not uniform in version and status (FR-013). A single-integration project therefore renders
    exactly what it rendered before this feature existed, and a two-integration project that is uniformly
    current says so in one line instead of three.
    """
    parts = component.parts
    if len(parts) < 2:
        return ()
    uniform = len({(part.status, part.installed) for part in parts}) == 1
    if uniform:
        return ()
    return tuple(_status_row(part) for part in parts)


def _status_row(component):
    """One `(label, glyph, phrase)` row describing a component's health."""
    behind_names = _behind_names(component) if isinstance(component, health.ComponentStatus) else ""
    if component.status == health.UP_TO_DATE:
        return (component.label, ui.GLYPH_OK, f"up to date ({ui.bold(component.installed)})")
    if component.status == health.NEEDS_UPDATING:
        return (component.label, ui.GLYPH_WARN,
                f"needs updating ({_transition(component)}){behind_names}")
    if component.status == health.AHEAD:
        return (component.label, ui.GLYPH_OK,
                f"ahead of published ({_transition(component)})")
    # UNKNOWN always carries a detail, and keeps the installed version when it has one (FR-026).
    detail = _detail_phrase(component)
    if component.installed:
        return (component.label, ui.GLYPH_NONE,
                f"unknown (installed {ui.bold(component.installed)}; {detail})")
    return (component.label, ui.GLYPH_NONE, f"unknown ({detail})")


def _show_health(report) -> None:
    ui.plain()
    ui.health_table([_status_row(c) + (_integration_child_rows(c),) for c in report.components])
    ui.plain()


def _skip_network(args) -> bool:
    return _update_check_disabled(args)


# --------------------------------------------------------------------------- #
# version (the whole stack)
# --------------------------------------------------------------------------- #
def _show_coverage_advisory(state, report) -> None:
    """Name any installed integration that has no Spectra commands, and the remedy — without running it.

    Spec Kit registers an extension's commands for the **active** integration only, and defers the others
    until one is activated. So in a project with two integrations, a developer on the non-default one has
    no Spectra commands and nothing explains why. This says why, in the one place they are already looking.

    Three deliberate restraints: it sits **below** the four rows rather than becoming a fifth; it never
    touches the exit code, because coverage is not a currency verdict; and it stops at naming
    `specify integration use` instead of running it, because that command changes which agent the whole
    project targets — a decision that belongs to the team, not to a maintenance command.

    Silent whenever coverage cannot be established (`registered_agents` returning None), and whenever
    every installed integration is already covered.
    """
    core = report.get(health.INTEGRATION)
    if core is None or len(core.parts) < 2:
        return
    covered = extension.registered_agents(state.project_root)
    if covered is None:
        return
    missing = [part.key for part in core.parts if part.key and part.key not in covered]
    if not missing:
        return

    have = ", ".join(sorted(covered)) or "no agent"
    ui.warn(f"Spectra commands are registered for {have} only.")
    for key in missing:
        ui.plain(ui.dim(f"  {key} is installed here but has no Spectra commands."))
    ui.plain(ui.dim(f"  To scaffold them: specify integration use {missing[0]}"))
    ui.plain(ui.dim("  (this changes the project's default integration for everyone.)"))
    ui.plain()


def cmd_version(args) -> int:
    """Report the status of all four components of the Spectra stack.

    Every delivered verdict exits 0 — current, behind, ahead, or unknown — because the command was asked
    a question and answered it. That includes an unknown: with four components there is always something
    to report, so unreachable data degrades one row rather than failing the command. Non-zero is reserved
    for a project state in which the question cannot be asked at all, which keeps this safe to drop into
    a shell without `|| true`.
    """
    state = project.classify()
    if state.state == project.NOT_A_PROJECT:
        return _say_not_a_project()
    if state.state == project.NOT_INSTALLED:
        return _say_not_installed(state)
    if state.state == project.INCOMPLETE:
        return _say_incomplete(state)

    report = health.check_all(state, skip_network=_skip_network(args))
    _show_health(report)

    if report.needs_update:
        ui.plain("  You can update by running: " + ui.bold("spectra update"))
        ui.plain()
    elif report.all_unknown:
        ui.warn("Nothing could be checked, so the stack could not be verified.")
        ui.plain()
    elif report.unknown:
        names = ", ".join(c.label for c in report.unknown)
        ui.ok("Nothing needs updating among the components that could be checked.")
        ui.plain(ui.dim(f"  Unverified: {names}"))
        ui.plain()
    else:
        ui.ok("Your whole Spectra stack is up to date.")
        ui.plain()
    _show_coverage_advisory(state, report)
    return EXIT_OK


# --------------------------------------------------------------------------- #
# update (the whole stack)
# --------------------------------------------------------------------------- #
def _outcome_row(result, before=None, after=None):
    """One `(label, glyph, phrase)` row describing what an update attempt did.

    `before` and `after` are the component's status from the checks either side of the walk. A
    delegated command reporting success is **not** proof that anything moved: Spec Kit tracks an
    extension's installed version in its own registry, so a manifest that disagrees can produce a
    cheerful exit 0 with nothing changed. Reporting the re-read version — and saying so plainly when it
    did not move — is the difference between telling the user what happened and telling them what we
    asked for.
    """
    if result.outcome == health.UPDATED:
        now = after.installed if after is not None else None
        was = before.installed if before is not None else None
        if now and was and now == was:
            return (result.label, ui.GLYPH_WARN,
                    f"reported success, but the version is unchanged ({ui.bold(now)})")
        if now:
            return (result.label, ui.GLYPH_OK, f"updated ({ui.bold(now)})")
        return (result.label, ui.GLYPH_OK, "updated")
    if result.outcome == health.FAILED:
        return (result.label, ui.GLYPH_FAIL, f"failed ({result.detail})")
    return (result.label, ui.GLYPH_NONE, f"skipped ({result.detail})")


def _outcome_child_rows(result, before=None, after=None):
    """One row per attempted integration beneath the `Core agents` outcome row.

    Each child is verified against **its own** manifest rather than the component's aggregate, so one
    integration moving cannot vouch for a sibling that stalled (FR-022). Rendered whenever the component
    has children, unlike the status breakdown: after a run the user is asking "what happened to each
    one?", and collapsing that to a single line would hide a skip they need to act on.
    """
    if not result.parts:
        return ()
    was = {state.key: state.installed for state in (before.parts if before else ())}
    now = {state.key: state.installed for state in (after.parts if after else ())}
    rows = []
    for child in result.parts:
        rows.append(_outcome_row(
            child,
            before=health.IntegrationState(child.key, health.UNKNOWN,
                                           installed=was.get(child.key)),
            after=health.IntegrationState(child.key, health.UNKNOWN,
                                          installed=now.get(child.key))))
    return tuple(rows)


def _confirm_updates(args, outdated) -> bool:
    """List what will change and get one confirmation covering all of it.

    Only components established as behind are listed — an unknown one is not going to be touched, so
    naming it here would invite the user to approve something that will not happen. A plural component
    also names its behind integrations, because those are what will actually be acted on.
    """
    ui.plain("The following components need updating:")
    for component in outdated:
        ui.plain(f"  • {component.label}: {_transition(component)}{_behind_names(component)}")
    ui.plain()

    if args.yes:
        return True
    if not sys.stdin.isatty():
        ui.plain("  Re-run with " + ui.bold("--yes") + " to update without being asked.")
        return False
    return ui.confirm("Proceed?")


class OverwritePlan:
    """The overwrite decision for one run: what is at risk, and what the user authorized.

    Exists so "no file is overwritten without an authorization act in the same run" is *inspectable*
    rather than implicit. `candidates` holds only integrations the walk is **about to upgrade** that have
    modified files — an integration nobody is touching can never appear here, so it can never be part of
    what a prompt covers. `authorized` starts empty and is filled by exactly one of the paths in
    :func:`_resolve_overwrite`; nothing about it is written to disk, so a later run asks again.
    """

    __slots__ = ("candidates", "shared", "authorized", "source")

    def __init__(self, candidates=None, shared=None):
        self.candidates = dict(candidates or {})
        self.shared = list(shared or [])
        self.authorized = set()
        self.source = "none"

    @property
    def needed(self) -> bool:
        return bool(self.candidates)


def _overwrite_plan(report, modifications) -> OverwritePlan:
    """Reduce a modification report to the integrations this run is about to upgrade (FR-034).

    An unestablished report yields an empty plan: with nothing known about what would be overwritten,
    there is nothing to disclose and nothing that may be authorized (research R6). The walk then runs
    unforced and Spec Kit refuses exactly the integrations it must, in its own words.
    """
    core = report.get(health.INTEGRATION)
    if core is None or not modifications.established:
        return OverwritePlan()
    behind = [state.key for state in core.parts
              if state.status == health.NEEDS_UPDATING and state.key]
    candidates = {key: modifications.files_for(key) for key in behind
                  if modifications.files_for(key)}
    return OverwritePlan(candidates, modifications.shared if candidates else [])


def _disclose_overwrite(plan) -> None:
    """List every file the overwrite would replace, grouped, before anything is asked.

    Shared Spec Kit infrastructure is its own group even though it is never what blocked the upgrade: the
    dependency's overwrite is not scoped to the files that caused the block, so authorizing it for one
    integration also replaces customized templates and scripts. A disclosure that hid that would be a lie
    in the one place a lie is most expensive.

    Every affected file is listed rather than summarised. The counts observed in real projects are in the
    tens, and "and 18 more" is not something a user can consent to.
    """
    ui.plain()
    ui.warn("Modified files detected. Upgrading will overwrite them with the bundled versions.")
    ui.plain()
    for key, files in plan.candidates.items():
        ui.plain(f"  {ui.bold(key)} — {len(files)} managed file(s)")
        for path in files:
            ui.plain(ui.dim(f"    {path}"))
        ui.plain()
    if plan.shared:
        ui.plain(f"  {ui.bold('Shared Spec Kit infrastructure')} — {len(plan.shared)} file(s)")
        for path in plan.shared:
            ui.plain(ui.dim(f"    {path}"))
        ui.plain()
    ui.plain(ui.dim("  There is no way to show what changed in these files, so the choice is to "
                    "overwrite"))
    ui.plain(ui.dim("  them or leave these integrations as they are."))
    ui.plain()


def _resolve_overwrite(args, plan) -> OverwritePlan:
    """Obtain — or decline to obtain — authorization to overwrite the disclosed files.

    Four paths, and only two of them authorize anything:

    * `--force` -> authorized, and the disclosure is still printed for the record.
    * a terminal, answered yes -> authorized.
    * a terminal, answered no -> nothing.
    * no terminal and no `--force` -> nothing, and the flag is named. Never blocks on input.

    `--yes` deliberately does **not** appear in that list. It approves the update plan the user was just
    shown; discarding their edits is a different act and needs its own.
    """
    if not plan.needed:
        return plan
    _disclose_overwrite(plan)

    if bool(getattr(args, "force", False)):
        plan.authorized = set(plan.candidates)
        plan.source = "flag"
        ui.info("Overwriting as requested by " + ui.bold("--force") + ".")
        ui.plain()
        return plan

    if not sys.stdin.isatty():
        ui.plain("  Nothing was overwritten. Re-run with " + ui.bold("--force")
                 + " to overwrite these files.")
        ui.plain()
        return plan

    if ui.confirm("Overwrite these files?", default_yes=False):
        plan.authorized = set(plan.candidates)
        plan.source = "prompt"
    ui.plain()
    return plan


def _report_unauthorized(plan, report) -> None:
    """Name each integration left behind, its version, and both of the options that remain.

    Printed on every exit path, not only the happy one: an integration left at an old version is the most
    consequential thing a run can leave behind, and burying it under a failure summary is how it gets
    missed. The version comes from the *post-run* report so it states where the integration actually is
    now, not where it was when the plan was drawn up.
    """
    left = [key for key in plan.candidates if key not in plan.authorized]
    if not left:
        return
    core = report.get(health.INTEGRATION)
    versions = {state.key: state.installed for state in (core.parts if core else ())}
    for key in left:
        at = versions.get(key)
        where = f" was left at {ui.bold(at)}" if at else " was left as it was"
        ui.warn(f"{ui.bold(key)}{where}.")
    ui.plain(ui.dim("  To upgrade it, re-run with --force to overwrite the modified files, or restore "
                    "them"))
    ui.plain(ui.dim("  and run spectra update again."))
    ui.plain()


def _mark_modified(report, plan) -> None:
    """Record on each integration which of its files are modified, so the walk can skip the blocked ones.

    The walk needs to know two things it cannot ask for itself: which integrations have modified files, and
    which of those the user authorized. The first is written here; the second is passed in separately. That
    keeps `health.apply_updates` free of prompting, a TTY, and the flag.
    """
    core = report.get(health.INTEGRATION)
    if core is None:
        return
    for state in core.parts:
        if state.key in plan.candidates:
            state.modified = list(plan.candidates[state.key])


def _reported_success_without_moving(result, report, after) -> bool:
    """Whether `result` claims an update that the re-read version does not support.

    **A plural component is judged on its children, never on its own version.** The row's version is the
    *oldest* of its integrations, so it cannot move while any of them is still behind — including one the
    user deliberately declined to overwrite. Judging the aggregate would turn a correct partial success
    into a reported failure, which is the opposite of what this check is for.
    """
    if result.outcome != health.UPDATED:
        return False
    before, now = report.get(result.key), after.get(result.key)
    if result.parts:
        return _stalled_children(result, before, now)
    if before is None or now is None:
        return False
    return bool(before.installed and now.installed and before.installed == now.installed)


def _stalled_children(result, before, after) -> bool:
    """Whether any child reported success while its own recorded version stayed put.

    Checked per integration rather than on the component, because the component's version is the *oldest*
    of its children — so one integration moving forward can change the aggregate while another silently
    stalls. That is precisely how a stale sibling would become invisible again.
    """
    was = {state.key: state.installed for state in (before.parts if before else ())}
    now = {state.key: state.installed for state in (after.parts if after else ())}
    for child in result.parts:
        if child.outcome != health.UPDATED:
            continue
        old, new = was.get(child.key), now.get(child.key)
        if old and new and old == new:
            return True
    return False


def _say_what_happened(results, plan) -> None:
    """Close a successful run with a sentence that is true of *this* run.

    "Everything that needed updating was updated" is the right line only when nothing was left behind. A
    declined overwrite exits 0 — correctly, because a skip is neither success nor failure — but claiming a
    complete update in that state would be the same overstatement this feature exists to remove from the
    report.
    """
    updated = [r for r in results if r.outcome == health.UPDATED]
    updated += [child for r in results for child in r.parts if child.outcome == health.UPDATED]
    left_behind = [key for key in plan.candidates if key not in plan.authorized]

    if left_behind and not updated:
        ui.warn("Nothing was updated.")
        ui.plain()
        return
    if left_behind:
        ui.ok("Everything else was updated.")
    else:
        ui.ok("Everything that needed updating was updated.")
    ui.plain(ui.dim("  Restart your AI agent so it picks up any new commands."))
    ui.plain()


def cmd_update(args) -> int:
    """Bring every out-of-date part of the Spectra stack current, after one confirmation.

    Runs the same check `spectra version` renders, so the command never acts on a state it did not first
    report. Updates run in canonical order and continue past failures; anything whose status could not be
    established is skipped rather than attempted, and skipping never turns a clean run into a failed one.
    """
    state = project.classify()
    if state.state == project.NOT_A_PROJECT:
        return _say_not_a_project()
    if state.state == project.NOT_INSTALLED:
        return _say_not_installed(state)
    # An INCOMPLETE install deliberately falls through: the extension check reports it as needing an
    # update, and the walk repairs it. That is the one component this command can fix outright.

    report = health.check_all(state, skip_network=_skip_network(args))
    _show_health(report)

    if not report.needs_update:
        if report.all_unknown:
            # Not the same as "everything is current", and must not read like it.
            ui.warn("Nothing could be checked, so nothing was updated.")
            ui.plain(ui.dim("  Unverified: "
                            + ", ".join(c.label for c in report.unknown)))
        elif report.unknown:
            ui.ok("Nothing needs updating among the components that could be checked.")
            ui.plain(ui.dim("  Unverified: "
                            + ", ".join(c.label for c in report.unknown)))
        else:
            ui.ok("Everything is up to date.")
        ui.plain()
        return EXIT_OK

    if not _confirm_updates(args, report.outdated):
        ui.info("Nothing was changed.")
        return EXIT_DECLINED

    # Between the approved plan and the first write: find out what would be destroyed, show it, and ask
    # once. This ordering is the only one that can disclose real files while the run is still free to stop
    # at no cost — after the walk starts, some integrations may already have been upgraded.
    plan = _resolve_overwrite(args, _overwrite_plan(report, health.modification_report(
        state.project_root)))
    _mark_modified(report, plan)

    def announce(component):
        ui.plain()
        ui.info(f"Updating {component.label} …")

    try:
        results = health.apply_updates(report, announce=announce, assume_yes=bool(args.yes),
                                       authorized_keys=plan.authorized)
    except health.Interrupted:
        ui.plain()
        ui.fail("Interrupted; the remaining components were left alone.")
        return EXIT_INTERRUPTED

    ui.plain()
    # Re-check rather than trust the walk's exit codes. A delegated command can report success without
    # changing anything — Spec Kit keeps an extension's installed version in its own registry, so a
    # manifest that disagrees yields a cheerful no-op. Re-reading is what turns "we ran the update" into
    # "here is what you now have".
    after = health.check_all(project.classify(), skip_network=_skip_network(args))
    ui.health_table([
        _outcome_row(result, before=report.get(result.key), after=after.get(result.key))
        + (_outcome_child_rows(result, before=report.get(result.key),
                               after=after.get(result.key)),)
        for result in results
    ])
    ui.plain()

    failed = [r for r in results if r.failed]
    stalled = [r for r in results if _reported_success_without_moving(r, report, after)]

    if failed:
        ui.fail(f"{len(failed)} of {len(report.outdated)} updates failed.")
        ui.plain(ui.dim("  The components that succeeded were still updated."))
        ui.plain()
        _report_unauthorized(plan, after)
        return EXIT_DELEGATION

    if stalled:
        names = ", ".join(r.label for r in stalled)
        ui.warn(f"Reported success without changing anything: {names}.")
        ui.plain(ui.dim("  The underlying command exited 0 but the version did not move. This usually "
                        "means it"))
        ui.plain(ui.dim("  disagrees with us about what is installed — check the component by hand."))
        ui.plain()
        _report_unauthorized(plan, after)
        return EXIT_DELEGATION

    _report_unauthorized(plan, after)
    _say_what_happened(results, plan)
    return EXIT_OK


# --------------------------------------------------------------------------- #
# uninstall (the agents in this project)
# --------------------------------------------------------------------------- #
def cmd_uninstall(args) -> int:
    """Remove Spectra's agents from this project, leaving the machine's `spectra` command alone.

    The confirmation prompt is **Spec Kit's**, not ours. `specify extension remove` already prompts and
    already accepts `--force`, so adding a second gate would make the user confirm one action twice —
    and would put the safety check in the outer tool while the inner one stayed unguarded for anyone
    calling it directly. `--yes` passes `--force` through.

    Exits 0 when Spectra is already absent: the requested end state holds, and `spectra cli uninstall`
    already treats an absent tool the same way.
    """
    state = project.classify()
    if state.state == project.NOT_A_PROJECT:
        return _say_not_a_project()
    if state.state == project.NOT_INSTALLED:
        ui.info(f"Spectra is not installed in this project ({state.project_root}), so there is "
                "nothing to remove.")
        return EXIT_OK

    if state.state == project.INCOMPLETE:
        ui.warn("Spectra's extension folder is here but unusable; removing it anyway.")
    else:
        ui.info(f"Removing Spectra's agents from {state.project_root} "
                f"(extension {ui.bold(state.installed_version)}).")
    ui.plain(ui.dim("  The spectra command stays installed on this machine."))
    ui.plain()

    try:
        code = extension.delegate_remove(force=bool(args.yes))
    except extension.DelegationError as e:
        ui.fail("Could not remove the extension.")
        for line in str(e).splitlines():
            ui.plain(f"  {line}")
        return EXIT_DELEGATION
    if code == EXIT_INTERRUPTED:
        return EXIT_INTERRUPTED

    ui.plain()
    after = project.classify()
    if after.state == project.NOT_INSTALLED:
        ui.ok("Spectra's agents were removed from this project.")
        ui.plain(ui.dim("  Restart your AI agent so it drops the commands."))
        return EXIT_OK
    if code != 0:
        ui.info(f"Spec Kit's extension removal exited with code {code}; nothing was removed.")
        return EXIT_DECLINED if code == 1 else EXIT_DELEGATION
    ui.fail("Spec Kit reported success, but the extension folder is still present.")
    ui.plain(ui.dim(f"  Folder: {after.extension_dir}"))
    return EXIT_DELEGATION


# --------------------------------------------------------------------------- #
# agent-list
# --------------------------------------------------------------------------- #
def cmd_agent_list(args) -> int:
    """Print the published roster.

    Deliberately works outside a Spec Kit project: discovering what Spectra offers should not
    require having installed it. Inside one, each shipped agent additionally shows whether it is
    installed here — the one part of the output that depends on the current folder.
    """
    try:
        published = roster.fetch()
    except net.FetchError as e:
        ui.fail("Could not read the published agent roster.")
        ui.plain(f"  {e}")
        ui.plain(ui.dim("  Nothing is listed above rather than a stale or partial roster."))
        return 3
    except roster.RosterError as e:
        ui.fail("The published agent roster could not be understood.")
        for line in str(e).splitlines():
            ui.plain(f"  {line}")
        return 3

    state = project.classify()
    installed = state.is_installed if state.is_project else None
    ui.agent_list(published, installed=installed)

    if published.newer_minor:
        ui.info(f"This roster (schema {published.schema_version}) is newer than your Spectra CLI, "
                "so some details may not be shown.")
        ui.plain(ui.dim("  Update the command with: " + ui.bold("spectra update")))
    return 0


# --------------------------------------------------------------------------- #
# No command — the overview
# --------------------------------------------------------------------------- #
def cmd_overview() -> int:
    """Bare `spectra`: say what this is and where to go next, and change nothing.

    Running with no arguments is an orientation step, not a request to modify the current
    folder — so it prints and exits rather than starting the install. `spectra install` is the
    verb, mirroring how `specify` separates its banner from `specify init`.
    """
    ui.splash(version.read_installed_version() or "unknown")
    ui.intro_note()
    ui.plain()
    ui.plain(ui.dim(f"Run '{ui.BOLD}spectra --help{ui.RESET}"
                    f"{ui.PURPLE_DIM}' for usage information"))
    ui.plain()
    return 0


# --------------------------------------------------------------------------- #
# Dispatch
# --------------------------------------------------------------------------- #
PROJECT_DISPATCH = {
    "install": cmd_install,
    "check": cmd_check,
    "version": cmd_version,
    "update": cmd_update,
    "uninstall": cmd_uninstall,
    "agent-list": cmd_agent_list,
}

# Handlers are looked up here rather than branched on, so adding a subcommand means adding a row.
# `version` and `update` point at retirement handlers rather than being absent, so that typing one gets
# a named replacement instead of argparse's "invalid choice".
TOOL_DISPATCH = {
    "version": cmd_cli_version,
    "update": cmd_cli_update,
    "uninstall": cmd_cli_uninstall,
}


def _dispatch(argv) -> int:
    if argv is None:
        argv = sys.argv[1:]

    # Before parsing: argparse would report a removed flag as "unrecognized arguments", which tells
    # the user what is wrong but not what to do instead.
    for token in argv:
        if token in REMOVED_FLAGS:
            return _report_removed_flag(token)

    args = build_parser().parse_args(argv)
    if getattr(args, "help", False):
        ui.splash(version.read_installed_version() or "unknown")
        if args.command == "cli":
            print_cli_group_help()
        else:
            print_help()
        return EXIT_OK

    if args.command == "cli":
        subcommand = getattr(args, "cli_command", None)
        if subcommand is None:
            print_cli_group_help()
            return EXIT_USAGE
        return TOOL_DISPATCH[subcommand](args)

    handler = PROJECT_DISPATCH.get(args.command)
    if handler is not None:
        return handler(args)
    return cmd_overview()


def main(argv=None) -> int:
    try:
        return _dispatch(argv)
    except KeyboardInterrupt:
        print()
        ui.fail("Interrupted.")
        return 130


if __name__ == "__main__":
    sys.exit(main())
