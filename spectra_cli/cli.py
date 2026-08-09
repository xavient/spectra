"""Command-line entry point for `spectra`.

Bare `spectra` is informational — it prints the banner and points at `--help`, the way the
`specify` CLI does. `spectra install` runs the install flow; `--version`, `--update`, and
`--uninstall` manage the tool itself, delegating to uv (see :mod:`spectra_cli.version`).

The parser is built from subcommands rather than one flat argument list, so project-scoped verbs and
tool-scoped ones can live in separate namespaces as they are added. Flags shared by more than one
subcommand are declared once and attached to each, with `SUPPRESS` defaults on the subcommand copies
so that `spectra --yes install` and `spectra install --yes` mean the same thing — without a
subcommand's default silently overwriting a value the top level already parsed.
"""

from __future__ import annotations

import argparse
import os
import sys

from spectra_cli import extension, install, net, project, roster, ui, version

# The help surface, rendered by `print_help()` into Spectra-purple panels rather than by
# argparse's plain formatter. Keeping the copy here (not in `add_argument(help=...)`) keeps the
# rendered table and the parser reading from one list.
OPTIONS = [
    ("--version", "-V", "Show the installed version and note if a newer one exists."),
    ("--update", "", "Update to the latest release via uv."),
    ("--uninstall", "", "Remove the spectra command from this machine."),
    ("--yes", "-y", "Skip the confirmation prompt (for --uninstall)."),
    ("--no-update-check", "", "Skip the check for a newer version."),
    ("--help", "-h", "Show this message and exit."),
]

COMMANDS = [
    ("install", "Install Spectra into the Spec Kit project in this folder. Installs the "
                "Spec Kit CLI and initializes the project first if needed."),
    ("check", "Report whether Spectra is installed in this project, and offer to install it "
              "when it is not."),
    ("version", "Compare the agents installed here against the published version."),
    ("update", "Update the agents installed here to the published version, via Spec Kit."),
    ("agent-list", "List every agent Spectra offers, grouped by SDLC phase. Reads the published "
                   "roster, so it works from anywhere."),
]

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
        description="Install and manage the Spectra catalog of Spec Kit extensions.",
        add_help=False,  # `--help` is handled in _dispatch so the banner prints above it.
    )
    _add_shared(ap)
    ap.add_argument("--version", "-V", action="store_true")
    ap.add_argument("--update", action="store_true")
    ap.add_argument("--uninstall", action="store_true")

    subcommands = ap.add_subparsers(dest="command", metavar="COMMAND")
    for name, _ in COMMANDS:
        sub = subcommands.add_parser(name, add_help=False)
        _add_shared(sub, suppress=True)
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
    """Render the help screen: usage line, then Options and Commands panels."""
    ui.plain(f"{ui.BOLD}Usage:{ui.RESET} {ui.BOLD}spectra{ui.RESET} [OPTIONS] COMMAND [ARGS]...")
    ui.plain()
    ui.plain("  Install and manage the Spectra catalog of Spec Kit extensions.")
    ui.plain()
    ui.panel("Options", [(_option_label(lo, sh), desc) for lo, sh, desc in OPTIONS])
    ui.panel("Commands", [(f"{ui.CYAN}{name}{ui.RESET}", desc) for name, desc in COMMANDS])
    ui.plain()
    ui.plain(ui.dim("  Run `spectra install` from inside the project you want Spectra in —"))
    ui.plain(ui.dim("  a folder containing .specify/. Not initialized yet? It offers to set one up."))


def _update_check_disabled(args) -> bool:
    """True when the user opted out of contacting GitHub for a version comparison.

    Honoured by both `--version` and the start-of-run nudge, so air-gapped and CI runs never
    pay for a network round trip they did not ask for.
    """
    return bool(args.no_update_check or os.environ.get("SPECTRA_NO_UPDATE_CHECK"))


# --------------------------------------------------------------------------- #
# cli version (the tool's own version)
# --------------------------------------------------------------------------- #
def cmd_cli_version(args) -> int:
    installed = version.read_installed_version() or "unknown"
    ui.plain(installed)
    if _update_check_disabled(args):
        return 0
    newer = version.passive_check(timeout=2)  # best-effort, ~2s bound
    if newer:
        ui.info(f"A newer version ({ui.bold(newer)}) is available. "
                "Update with: " + ui.bold("spectra --update"))
    return 0


# --------------------------------------------------------------------------- #
# cli update (the tool updates itself)
# --------------------------------------------------------------------------- #
def cmd_cli_update() -> int:
    result = version.check_update()
    installed = result["installed"] or "unknown"
    status = result["status"]

    if status == "latest_unknown":
        ui.fail("Could not determine the latest version (GitHub unreachable or rate-limited).")
        ui.plain(ui.dim(f"Check your connection/proxy and try again. Installed: {installed}"))
        return 3
    if status == "up_to_date":
        ui.ok(f"Already up to date ({installed}).")
        return 0
    if status == "ahead":
        ui.ok(f"Installed {installed} is ahead of latest {result['latest']}; nothing to do.")
        return 0

    tag = result["latest"]
    ui.info(f"Update available: {ui.bold(installed)} {ui.dim('->')} {ui.bold(tag)}")
    try:
        ui.info("Reinstalling via uv …")
        version.perform_update(tag)
    except version.UpdateError as e:
        ui.fail(f"Update failed: {e}")
        return 4
    ui.ok(f"Updated to {ui.bold(tag)}.")
    ui.plain(ui.dim(
        "This updates the spectra command only. Extensions update separately with "
        "`specify extension update spectra`."
    ))
    return 0


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
# version (the agents in this project)
# --------------------------------------------------------------------------- #
def cmd_version(args) -> int:
    """Compare the installed agents against the published ones.

    Every verdict — current, behind, or ahead — exits 0, because the command was asked a question and
    answered it. Non-zero is reserved for being unable to answer, so this is safe to drop into a
    shell without `|| true`.
    """
    state = project.classify()
    if state.state == project.NOT_A_PROJECT:
        return _say_not_a_project()
    if state.state == project.NOT_INSTALLED:
        return _say_not_installed(state)
    if state.state == project.INCOMPLETE:
        return _say_incomplete(state)

    installed = state.installed_version
    try:
        published = extension.published_version()
    except net.FetchError as e:
        ui.warn(f"Your agents are at {ui.bold(installed)}, but the published version could not be "
                "fetched, so there is nothing to compare against.")
        ui.plain(f"  {e}")
        return EXIT_UNREACHABLE

    verdict = extension.compare(installed, published)
    if verdict == extension.UP_TO_DATE:
        ui.ok(f"Your agents are up to date (extension {ui.bold(installed)}).")
    elif verdict == extension.OUT_OF_DATE:
        ui.warn(f"Your agents are out of date: installed {ui.bold(installed)}, "
                f"published {ui.bold(published)}.")
        ui.plain("  Update them with: " + ui.bold("spectra update"))
    else:
        ui.ok(f"Your agents are ahead of what is published: installed {ui.bold(installed)}, "
              f"published {ui.bold(published)}.")
        ui.plain(ui.dim("  Nothing to update — this is what a local or pre-release copy looks like."))
    ui.plain(ui.dim("  This is the extension version. For the tool's own: spectra cli version"))
    return EXIT_OK


# --------------------------------------------------------------------------- #
# update (the agents in this project)
# --------------------------------------------------------------------------- #
def cmd_update(args) -> int:
    """Bring the installed agents up to the published version, through Spec Kit."""
    state = project.classify()
    if state.state == project.NOT_A_PROJECT:
        return _say_not_a_project()
    if state.state == project.NOT_INSTALLED:
        return _say_not_installed(state)

    # An incomplete install is exactly what this command repairs, so it does not check versions
    # first — there is no readable version to check.
    if state.state != project.INCOMPLETE:
        try:
            published = extension.published_version()
        except net.FetchError as e:
            ui.fail("Could not fetch the published version, so nothing was changed.")
            ui.plain(f"  {e}")
            return EXIT_UNREACHABLE

        verdict = extension.compare(state.installed_version, published)
        if verdict == extension.UP_TO_DATE:
            ui.ok(f"Your agents are already up to date (extension {ui.bold(published)}).")
            return EXIT_OK
        if verdict == extension.AHEAD:
            ui.ok(f"Installed {ui.bold(state.installed_version)} is ahead of published "
                  f"{ui.bold(published)}; nothing to do.")
            return EXIT_OK
        ui.info(f"Updating agents: {ui.bold(state.installed_version)} {ui.dim('->')} "
                f"{ui.bold(published)}")
    else:
        ui.info("Repairing an incomplete Spectra install …")

    ui.plain()
    try:
        code = extension.delegate_update()
    except extension.DelegationError as e:
        ui.fail("Could not update the extension.")
        for line in str(e).splitlines():
            ui.plain(f"  {line}")
        return EXIT_DELEGATION
    if code == EXIT_INTERRUPTED:
        return EXIT_INTERRUPTED
    if code != 0:
        ui.plain()
        ui.fail(f"Spec Kit's extension update exited with code {code}; your agents are unchanged.")
        return EXIT_DELEGATION

    ui.plain()
    now = project.classify()
    if now.is_installed:
        ui.ok(f"Agents updated (extension {ui.bold(now.installed_version)}).")
    else:
        ui.ok("Agents updated.")
    ui.plain(ui.dim("  Restart your AI agent so it picks up any new commands."))
    return EXIT_OK


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
        ui.plain(ui.dim("  Update the command with: " + ui.bold("spectra cli update")))
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
def _dispatch(argv) -> int:
    args = build_parser().parse_args(argv)
    if getattr(args, "help", False):
        ui.splash(version.read_installed_version() or "unknown")
        print_help()
        return 0
    if args.version:
        return cmd_cli_version(args)
    if args.update:
        return cmd_cli_update()
    if args.uninstall:
        return cmd_cli_uninstall(args)
    dispatch = {
        "install": cmd_install,
        "check": cmd_check,
        "version": cmd_version,
        "update": cmd_update,
        "agent-list": cmd_agent_list,
    }
    handler = dispatch.get(args.command)
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
