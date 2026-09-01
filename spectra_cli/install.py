# Copyright 2026 TELUS Digital
# SPDX-License-Identifier: Apache-2.0

"""The Spectra install flow — prerequisites, then catalog registration.

Three steps, run from inside the project the user wants Spectra in:

1. the `specify` CLI (Spec Kit) is present, installing it via uv when it is not;
2. the current folder is a Spec Kit project, offering `specify init` when it is not;
3. the public Spectra catalog is registered and every extension it advertises is installed.

Spectra is distributed from a **public** catalog, so there is no GitHub login, token, or `gh`
setup — Spec Kit fetches the catalog and extension packages over anonymous requests.
"""

from __future__ import annotations

import json
import os
import shutil
import textwrap
import urllib.request
from pathlib import Path

from spectra_cli import coverage, health, project, ui
from spectra_cli.exits import EXIT_DECLINED, EXIT_DELEGATION, EXIT_INTERRUPTED, EXIT_OK
from spectra_cli.version import find_uv

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

CATALOG_URL = "https://raw.githubusercontent.com/xavient/spectra/main/catalog.json"
SPECKIT_INSTALL_URL = "https://github.com/github/spec-kit"

# Spec Kit bootstrap (used when `specify` is missing).
SPECKIT_GIT = "https://github.com/github/spec-kit.git"
SPECKIT_LATEST_API = "https://api.github.com/repos/github/spec-kit/releases/latest"
UV_DOCS_URL = "https://docs.astral.sh/uv/getting-started/installation/"

# Used only when the catalog itself cannot be fetched, so a network blip still installs Spectra.
FALLBACK_EXTENSION_ID = "spectra"


# --------------------------------------------------------------------------- #
# Step 1 — the Spec Kit CLI
# --------------------------------------------------------------------------- #

def _specify_version_detail() -> str:
    version = ui.run(["specify", "--version"])
    return version.stdout.strip() or version.stderr.strip() or "found"


def _latest_speckit_tag():
    """Latest Spec Kit release tag (e.g. 'v0.11.9'), or None if unreachable.

    Uses the public GitHub API — no auth needed.
    """
    req = urllib.request.Request(
        SPECKIT_LATEST_API,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "spectra-cli"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            tag = json.load(resp).get("tag_name")
        return tag or None
    except Exception:
        return None


def _prepend_to_path(*dirs: Path) -> None:
    """Make freshly installed executables discoverable for the rest of this run."""
    extra = [str(d) for d in dirs if d.is_dir()]
    if extra:
        os.environ["PATH"] = os.pathsep.join(extra + [os.environ.get("PATH", "")])


def install_speckit(uv: str) -> bool:
    """Install the `specify` CLI at the latest Spec Kit release via uv."""
    tag = _latest_speckit_tag()
    if tag:
        ui.info(f"Latest Spec Kit release: {tag}")
        cmd = [uv, "tool", "install", "specify-cli",
               "--from", f"git+{SPECKIT_GIT}@{tag}", "--force"]
    else:
        ui.warn("Couldn't reach the GitHub releases API — installing the latest published version.")
        cmd = [uv, "tool", "install", "specify-cli", "--force"]

    ui.info("Installing the Spec Kit CLI with uv… (this can take a minute)")
    print()
    if ui.run_interactive(cmd) != 0:
        return False

    # Put uv's tool bin dir on PATH for the rest of this run, and (best effort)
    # wire it into new shells so `specify` is there next time too.
    bin_dir = ui.run([uv, "tool", "dir", "--bin"]).stdout.strip()
    _prepend_to_path(Path(bin_dir) if bin_dir else Path.home() / ".local" / "bin")
    ui.run([uv, "tool", "update-shell"])
    return shutil.which("specify") is not None


def ensure_specify_installed(*, total: int = 3) -> None:
    ui.step(1, "Checking for the Spec Kit CLI (specify)", total=total)
    if shutil.which("specify"):
        ui.ok(f"specify is installed ({_specify_version_detail()}).")
        return

    ui.warn("Spec Kit's `specify` CLI isn't installed or isn't on your PATH.")
    print("  Spectra extensions install into a Spec Kit project, so it's required.")
    print()
    if not ui.confirm("Install Spec Kit now?"):
        ui.die(
            "Spec Kit is required to continue.",
            f"Install it yourself: {SPECKIT_INSTALL_URL}",
            "Then re-run `spectra`.",
        )

    # uv is present by construction — it is what installed this command — but a source or pip
    # install can reach here without it, so probe rather than assume.
    uv = find_uv()
    if not uv:
        ui.die(
            "Couldn't find `uv`, which Spec Kit's installer uses.",
            f"Install uv: {UV_DOCS_URL}",
            f"Then: uv tool install specify-cli --from git+{SPECKIT_GIT}@<latest-tag>",
            f"Or install Spec Kit another way: {SPECKIT_INSTALL_URL}",
        )

    if not install_speckit(uv):
        ui.die(
            "Spec Kit installation didn't complete.",
            "If `specify` was installed but isn't found, open a new terminal and re-run,",
            "or ensure uv's tool bin directory is on PATH (`uv tool update-shell`).",
        )

    ui.ok(f"Spec Kit installed ({_specify_version_detail()}).")


# --------------------------------------------------------------------------- #
# Step 2 — a Spec Kit project
# --------------------------------------------------------------------------- #

def check_in_specify_project(*, total: int = 3) -> Path:
    ui.step(2, "Checking this is a Spec Kit project", total=total)
    here = Path.cwd()
    for candidate in [here, *here.parents]:
        if (candidate / ".specify").is_dir():
            ui.ok(f"Spec Kit project detected at {candidate}.")
            return candidate

    ui.warn("This folder isn't a Spec Kit project (no .specify/ directory found).")
    print("  Spectra installs extensions into a Spec Kit project, so this folder")
    print("  needs Spec Kit initialized first. I can do that here for you — it runs")
    print(f"  `specify init` in {ui.bold(str(here))} and won't touch anything outside it.")
    print()
    if not ui.confirm("Initialize Spec Kit in this folder now?"):
        ui.die(
            "A Spec Kit project is required to continue.",
            "Run `specify init` here (or cd into an existing project), then re-run `spectra`.",
            f"See {SPECKIT_INSTALL_URL}",
        )

    ui.info("Initializing Spec Kit — pick your coding agent if prompted…")
    print()
    code = ui.run_interactive(["specify", "init", "--here", "--force"])
    if code != 0 or not (here / ".specify").is_dir():
        ui.die(
            "Spec Kit initialization didn't complete.",
            "Try running `specify init --here` yourself, then re-run `spectra`.",
        )
    ui.ok(f"Spec Kit project initialized at {here}.")
    return here


# --------------------------------------------------------------------------- #
# Step 3 — the catalog and its extensions
# --------------------------------------------------------------------------- #

def catalog_extension_ids():
    """Extension ids advertised by the Spectra catalog.

    Read from the live catalog at run time rather than hardcoded, so adding an extension to
    `catalog.json` reaches users without a CLI release — the two channels version independently
    (constitution Principle VI). Falls back to the well-known id if the catalog is unreachable,
    since Spec Kit will resolve it against the catalog it just registered anyway.
    """
    req = urllib.request.Request(CATALOG_URL, headers={"User-Agent": "spectra-cli"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.load(resp)
        ids = sorted((data.get("extensions") or {}).keys())
        return ids or [FALLBACK_EXTENSION_ID]
    except Exception:
        return [FALLBACK_EXTENSION_ID]


def register_catalog() -> bool:
    """Register the Spectra catalog with Spec Kit. Returns True when it is registered."""
    ui.info("Adding the Spectra catalog…")
    add = ui.run(
        [
            "specify", "extension", "catalog", "add", CATALOG_URL,
            "--name", "spectra", "--priority", "5", "--install-allowed",
        ]
    )
    combined = (add.stdout + add.stderr).lower()
    if add.returncode == 0:
        ui.ok("Spectra catalog registered.")
        return True
    if "already" in combined or "exists" in combined:
        ui.ok("Spectra catalog was already registered.")
        return True
    ui.warn("Could not register the catalog automatically:")
    print(textwrap.indent((add.stdout + add.stderr).strip(), "  "))
    print("  You can retry the command shown in the README.")
    return False


def add_catalog(project_root=None, *, total_steps: int = 3) -> bool:
    """Register the Spectra catalog, then install every extension it advertises.

    Returns True once all of them are installed — where "installed" includes an extension that was
    **already** present. That is a state, not a failure: Spec Kit refuses to install over an existing
    extension, and a run that reported that refusal as an error was the reason a partially covered project
    could not be repaired by the obvious command (spec 011 FR-020).

    **The presence check happens before the attempt, never after a failure.** A classification taken
    afterwards cannot tell "refused because already installed" from "the download failed while an older copy
    sat on disk" — both leave the folder there. Deciding first removes the ambiguity, and removes any need
    to match the dependency's message text (FR-021, research R6).
    """
    ui.step(3, "Registering the Spectra catalog and installing Spectra", total=total_steps)
    if not register_catalog():
        return False

    extension_ids = catalog_extension_ids()
    present = [e for e in extension_ids if project.extension_present(project_root, e)
               and project.classify(project_root).is_installed]
    pending = [e for e in extension_ids if e not in present]

    print()
    if not pending:
        for extension_id in present:
            state = project.classify(project_root)
            version = state.installed_version or "unknown version"
            ui.ok(f"Spectra is already installed here ({ui.bold(version)}) — nothing to download.")
            print(f"  Update it with: {ui.bold('spectra update')}")
        return True

    if len(pending) == 1:
        ui.info("Installing the Spectra extension…")
    else:
        ui.info(f"Installing {len(pending)} Spectra extensions: "
                + ", ".join(ui.bold(e) for e in pending))

    installed_all = True
    for extension_id in pending:
        print()
        code = ui.run_interactive(["specify", "extension", "add", extension_id])
        if code != 0:
            print()
            ui.warn(f"Could not install the {extension_id} extension automatically.")
            print(f"  Install it yourself: {ui.bold('specify extension add ' + extension_id)}")
            installed_all = False
    return installed_all


# --------------------------------------------------------------------------- #
# Step 4 — the agents that are not the default
# --------------------------------------------------------------------------- #

def coverage_expected(project_root) -> bool:
    """Whether this run will have a coverage step, decided **before** step 1 prints.

    The step count has to be known up front, and coverage cannot be read up front: on a fresh install the
    extension does not exist yet, so there is no registration state to read. Hence a prediction, and it is
    exact rather than a guess:

    * **extension already present** — read the real plan. It cannot change between here and step 4, because
      nothing installs over an existing extension (`add_catalog`).
    * **extension absent** — it is about to be installed, and Spec Kit will register it for the *active*
      integration alone (BRD-007 F1). So every other installed integration will be uncovered, and a project
      with two or more of them will need the step.

    A project with one integration therefore predicts False and prints `[1/3]`…`[3/3]`, byte-identical to
    the release before this feature (FR-038, SC-006).
    """
    if project.classify(project_root).is_installed:
        return coverage.plan(project_root).needed
    return len(health.read_installed_integrations(project_root) or []) >= 2


def _disclose(plan) -> None:
    """Say what the step will do before it does it — including that the default moves (FR-014).

    Silent about the default when the plan does not move it: covering the integration that is *already*
    the default changes no configuration, and announcing a transient change that will not happen would be
    a small lie in the one place this feature asks for trust (FR-013).
    """
    covered = [state.key for state in plan.states if state.covered]
    uncovered = list(plan.uncovered_keys)
    if covered:
        ui.info(f"Spectra's commands are registered for {', '.join(covered)} only.")
    for key in uncovered:
        print(f"  {key} is installed here but has no Spectra commands.")
    print()
    if plan.moves_default:
        print("  To add them, each agent has to be made the project's default for a moment.")
        print(f"  This run will do that for: {ui.bold(', '.join(plan.targets))}")
        print(f"  Then it will set the default back to {ui.bold(plan.default_key)}, where it is now.")
    else:
        print(f"  Registering Spectra's commands for {ui.bold(plan.default_key)}…")
    print()


def _report(result) -> None:
    """One line per integration, then the restoration — the whole cost of the step (SC-011)."""
    for child in result.parts:
        if child.outcome == coverage.NEWLY_COVERED:
            ui.ok(f"{child.key} — Spectra's commands registered")
        elif child.outcome == coverage.FAILED:
            ui.fail(f"{child.key} — not registered ({child.detail})")
        elif child.outcome == coverage.SKIPPED:
            ui.warn(f"{child.key} — skipped ({child.detail})")

    if result.restoration == coverage.RESTORED:
        ui.ok(f"default restored to {ui.bold(result.original_default)}")
    elif result.restoration == coverage.NOT_RESTORED:
        print()
        ui.fail(f"Could not set the default integration back to {result.original_default}.")
        if result.current_default:
            print(f"  The project is currently defaulted to {ui.bold(result.current_default)}.")
        print("  Restore it with: "
              + ui.bold(f"specify integration use {result.original_default}"))


def cover_agents(project_root, *, extension_present: bool = True, step: int = 4,
                 total: int = 4) -> int:
    """Give Spectra's commands to every installed integration that lacks them. Returns an exit code.

    Prints nothing at all when there is nothing to do and nothing a user could act on — a single-integration
    project, or one where every agent is already covered (FR-037, FR-038). The step header appears only when
    the caller predicted it would, so `[1/4]` is never followed by a missing fourth step.

    Exit codes follow the clarified rule: an **attempt** that fails is non-zero, an abstention with a stated
    reason is zero (spec 011 § Clarifications, FR-017).
    """
    plan = coverage.plan(project_root, extension_present=extension_present)

    if not plan.needed:
        if plan.skip_reason in (coverage.REASON_ALL_COVERED, coverage.REASON_UNKNOWN):
            # Nothing happened and nothing is wrong — or nothing is knowable. Either way, say nothing.
            return EXIT_OK
        ui.step(step, "Registering Spectra with your other agents", total=total)
        ui.info(f"Skipped — {plan.skip_reason}.")
        if plan.skip_reason == coverage.REASON_NO_DEFAULT and plan.uncovered_keys:
            print(f"  Without Spectra's commands: {', '.join(plan.uncovered_keys)}")
        return EXIT_OK

    ui.step(step, "Registering Spectra with your other agents", total=total)
    _disclose(plan)

    def announce(key):
        ui.info(f"Registering Spectra's commands for {ui.bold(key)}…")

    try:
        result = coverage.apply(plan, announce=announce)
    except coverage.Interrupted as stopped:
        _report(stopped.args[0])
        print()
        ui.fail("Interrupted; the agents that were not reached were left alone.")
        return EXIT_INTERRUPTED
    except extension_delegation_error() as exc:
        ui.fail(f"Could not register Spectra's commands ({exc}).")
        return EXIT_DELEGATION

    _report(result)
    if result.failed:
        print()
        left = ", ".join(result.left_uncovered)
        ui.warn(f"Spectra's commands are still missing for: {left}")
        print(f"  Try again with: {ui.bold('spectra install')}")
        return EXIT_DELEGATION
    return EXIT_OK


def extension_delegation_error():
    """`extension.DelegationError`, imported lazily to keep this module's imports acyclic and small."""
    from spectra_cli.extension import DelegationError
    return DelegationError


# --------------------------------------------------------------------------- #
# The whole flow
# --------------------------------------------------------------------------- #

def run_install() -> int:
    """Run the install steps — three, or four when an agent here lacks Spectra's commands.

    Returns a process exit code, and the code distinguishes an **attempt** from an **abstention**: a coverage
    step that was tried and failed is non-zero, while one deliberately skipped for a stated reason is zero
    (spec 011 § Clarifications, FR-017). A failed extension install keeps its own code and is never masked by
    a coverage step that went well afterwards (FR-022).
    """
    ui.intro_note()

    # The step count has to be known before step 1 prints, and step 2 is what *reports* the project root
    # rather than what finds it — so resolve it quietly here and predict from that. A folder that is not a
    # project yet predicts three steps, which is right: `specify init` installs exactly one integration.
    total_steps = 4 if coverage_expected(project.find_project_root()) else 3

    ensure_specify_installed(total=total_steps)
    project_root = check_in_specify_project(total=total_steps)

    installed = add_catalog(project_root, total_steps=total_steps)

    # Coverage runs whether or not the extension work succeeded: in a project that already had Spectra from
    # an earlier run, a failed download does not make the coverage gap unrepairable (FR-022, clarification 4).
    extension_present = project.classify(project_root).is_installed
    coverage_code = EXIT_OK
    if total_steps == 4:
        coverage_code = cover_agents(project_root, extension_present=extension_present,
                                     step=4, total=total_steps)

    print()
    if not installed:
        print(
            f"{ui.YELLOW}{ui.BOLD}Almost there.{ui.RESET} The catalog is registered — finish with "
            f"{ui.bold('specify extension add <id>')} for whatever didn't install above."
        )
        print()
        return EXIT_DECLINED
    if coverage_code != EXIT_OK:
        print(f"{ui.YELLOW}{ui.BOLD}Partly done.{ui.RESET} Spectra is installed, but not every agent "
              "here has its commands.")
        print()
        return coverage_code

    print(f"{ui.GREEN}{ui.BOLD}All set!{ui.RESET} {ui.PURPLE}Spectra is ready to use.{ui.RESET}")
    print()
    print("Restart your AI agent to pick up the new commands.")
    return EXIT_OK
