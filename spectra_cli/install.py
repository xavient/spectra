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

from spectra_cli import ui
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


def ensure_specify_installed() -> None:
    ui.step(1, "Checking for the Spec Kit CLI (specify)")
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

def check_in_specify_project() -> Path:
    ui.step(2, "Checking this is a Spec Kit project")
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


def add_catalog() -> bool:
    """Register the Spectra catalog, then install every extension it advertises.

    Returns True once all of them are installed.
    """
    ui.step(3, "Registering the Spectra catalog and installing Spectra")
    if not register_catalog():
        return False

    extension_ids = catalog_extension_ids()
    print()
    if len(extension_ids) == 1:
        ui.info("Installing the Spectra extension…")
    else:
        ui.info(f"Installing {len(extension_ids)} Spectra extensions: "
                + ", ".join(ui.bold(e) for e in extension_ids))

    installed_all = True
    for extension_id in extension_ids:
        print()
        code = ui.run_interactive(["specify", "extension", "add", extension_id])
        if code != 0:
            print()
            ui.warn(f"Could not install the {extension_id} extension automatically.")
            print(f"  Install it yourself: {ui.bold('specify extension add ' + extension_id)}")
            installed_all = False
    return installed_all


# --------------------------------------------------------------------------- #
# The whole flow
# --------------------------------------------------------------------------- #

def run_install() -> int:
    """Run the three install steps. Returns a process exit code."""
    ui.intro_note()
    ensure_specify_installed()
    check_in_specify_project()
    installed = add_catalog()

    print()
    if installed:
        print(f"{ui.GREEN}{ui.BOLD}All set!{ui.RESET} {ui.PURPLE}Spectra is ready to use.{ui.RESET}")
        print()
        print("Restart your AI agent to pick up the new commands.")
        return 0

    print(
        f"{ui.YELLOW}{ui.BOLD}Almost there.{ui.RESET} The catalog is registered — finish with "
        f"{ui.bold('specify extension add <id>')} for whatever didn't install above."
    )
    print()
    return 1
