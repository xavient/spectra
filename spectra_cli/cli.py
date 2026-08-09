"""Command-line entry point for `spectra`.

With no flags it runs the install flow. `--version`, `--update`, and `--uninstall` manage the
tool itself, delegating to uv (see :mod:`spectra_cli.version`).
"""

from __future__ import annotations

import argparse
import os
import sys

from spectra_cli import install, ui, version

EPILOG = """\
examples:
  spectra                 install Spectra into the Spec Kit project in this folder
  spectra --version       print the installed version, noting if a newer one exists
  spectra --update        update to the latest release via uv
  spectra --uninstall     remove the spectra command from this machine

Run `spectra` from inside the project you want Spectra in — a folder containing .specify/.
Not initialized yet? It offers to run `specify init` for you.
"""


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="spectra",
        description="Install and manage the Spectra catalog of Spec Kit extensions.",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--version", action="store_true",
                    help="Print the installed version and note if a newer one exists")
    ap.add_argument("--update", action="store_true",
                    help="Update to the latest release via uv")
    ap.add_argument("--uninstall", action="store_true",
                    help="Remove the uv-installed spectra command")
    ap.add_argument("--yes", "-y", dest="yes", action="store_true",
                    help="Skip the confirmation prompt (for --uninstall)")
    ap.add_argument("--no-update-check", dest="no_update_check", action="store_true",
                    help="Skip the start-of-run check for a newer version")
    return ap


def _update_check_disabled(args) -> bool:
    """True when the user opted out of contacting GitHub for a version comparison.

    Honoured by both `--version` and the start-of-run nudge, so air-gapped and CI runs never
    pay for a network round trip they did not ask for.
    """
    return bool(args.no_update_check or os.environ.get("SPECTRA_NO_UPDATE_CHECK"))


# --------------------------------------------------------------------------- #
# --version
# --------------------------------------------------------------------------- #
def cmd_version(args) -> int:
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
# --update
# --------------------------------------------------------------------------- #
def cmd_update() -> int:
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
# --uninstall
# --------------------------------------------------------------------------- #
def cmd_uninstall(args) -> int:
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
# Dispatch
# --------------------------------------------------------------------------- #
def _dispatch(argv) -> int:
    args = build_parser().parse_args(argv)
    if args.version:
        return cmd_version(args)
    if args.update:
        return cmd_update()
    if args.uninstall:
        return cmd_uninstall(args)
    return cmd_install(args)


def main(argv=None) -> int:
    try:
        return _dispatch(argv)
    except KeyboardInterrupt:
        print()
        ui.fail("Interrupted.")
        return 130


if __name__ == "__main__":
    sys.exit(main())
