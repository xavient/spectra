#!/usr/bin/env python3
"""Spectra onboarding — register the public Spectra catalog with Spec Kit.

Run this from inside a Spec Kit project. It makes sure the prerequisites are in
place (the `specify` CLI and a Spec Kit project), registers the Spectra catalog,
and installs the Spectra extension into the project.

Spectra is distributed from a **public** catalog, so there is no GitHub login,
token, or `gh` setup — Spec Kit fetches the catalog and extension packages over
anonymous requests.

Works on macOS, Linux, and Windows. Standard library only — no pip installs.

Prerequisites
-------------
* Python 3.8+                  — you're running it, so you have this
* The `specify` CLI on PATH    — if missing, this script offers to install it
                                 (via uv) at the latest Spec Kit release
* A Spec Kit project           — run this from your project folder; if it isn't
                                 initialized yet, the script offers to `specify init` it

Standard library only — no third-party imports. It shells out to `uv` and
`specify`, installing `uv`/`specify` on request when they are missing.

Usage
-----
    python3 spectra-setup.py          # use `python` on Windows
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

__version__ = "2.0.0"

CATALOG_URL = "https://raw.githubusercontent.com/xavient/spectra/main/catalog.json"
SPECKIT_INSTALL_URL = "https://github.com/github/spec-kit"

# Spec Kit bootstrap (used when `specify` is missing).
SPECKIT_GIT = "https://github.com/github/spec-kit.git"
SPECKIT_LATEST_API = "https://api.github.com/repos/github/spec-kit/releases/latest"
UV_INSTALL_SH = "https://astral.sh/uv/install.sh"
UV_INSTALL_PS1 = "https://astral.sh/uv/install.ps1"
UV_DOCS_URL = "https://docs.astral.sh/uv/getting-started/installation/"

TAGLINE = (
    "TELUS Digital - A curated catalog of Spec Kit extensions that enable "
    "full agentic development across the entire software development lifecycle (SDLC)"
)

# --------------------------------------------------------------------------- #
# Terminal / color setup
# --------------------------------------------------------------------------- #

if platform.system() == "Windows":
    # Enable ANSI escape processing on Windows 10+ consoles.
    os.system("")
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

USE_COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None


def _c(code: str) -> str:
    return code if USE_COLOR else ""


PURPLE = _c("\033[38;5;141m")
PURPLE_DIM = _c("\033[38;5;98m")
BOLD = _c("\033[1m")
GREEN = _c("\033[38;5;42m")
RED = _c("\033[38;5;203m")
YELLOW = _c("\033[38;5;221m")
CYAN = _c("\033[38;5;80m")
RESET = _c("\033[0m")


def info(msg: str) -> None:
    print(f"{CYAN}›{RESET} {msg}")


def ok(msg: str) -> None:
    print(f"{GREEN}✓{RESET} {msg}")


def warn(msg: str) -> None:
    print(f"{YELLOW}!{RESET} {msg}")


def fail(msg: str) -> None:
    print(f"{RED}✗ {msg}{RESET}")


def die(msg: str, *extra: str) -> "NoReturn":  # type: ignore[name-defined]
    print()
    fail(msg)
    for line in extra:
        print(f"  {line}")
    print()
    sys.exit(1)


def step(n: int, title: str) -> None:
    print()
    print(f"{BOLD}{PURPLE}[{n}/3]{RESET} {BOLD}{title}{RESET}")


def confirm(prompt: str, default_yes: bool = True) -> bool:
    suffix = "[Y/n]" if default_yes else "[y/N]"
    try:
        ans = input(f"{prompt} {suffix} ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return False
    if ans == "":
        return default_yes
    return ans in ("y", "yes")


# --------------------------------------------------------------------------- #
# Splash
# --------------------------------------------------------------------------- #

_FONT = {
    "S": ["█████", "█    ", "█████", "    █", "█████"],
    "P": ["█████", "█   █", "█████", "█    ", "█    "],
    "E": ["█████", "█    ", "████ ", "█    ", "█████"],
    "C": ["█████", "█    ", "█    ", "█    ", "█████"],
    "T": ["█████", "  █  ", "  █  ", "  █  ", "  █  "],
    "R": ["████ ", "█   █", "████ ", "█  █ ", "█   █"],
    "A": ["█████", "█   █", "█████", "█   █", "█   █"],
}


def _banner(word: str) -> str:
    rows = ["", "", "", "", ""]
    for ch in word:
        glyph = _FONT[ch]
        for i in range(5):
            rows[i] += glyph[i] + "  "
    return "\n".join(rows)


def splash() -> None:
    print()
    for line in _banner("SPECTRA").splitlines():
        print(f"{PURPLE}{line}{RESET}")
    print()
    width = min(shutil.get_terminal_size((80, 24)).columns, 88)
    for line in textwrap.wrap(TAGLINE, width=width):
        print(f"{PURPLE_DIM}{line}{RESET}")
    print(f"{PURPLE_DIM}installer v{__version__}{RESET}")
    print()


def intro_note() -> None:
    """Remind the user this runs inside the target project folder."""
    line = "─" * 72
    print(f"{PURPLE_DIM}┌{line}{RESET}")
    print(f"{PURPLE_DIM}│{RESET} {BOLD}Run this from inside the project you want Spectra in.{RESET}")
    print(f"{PURPLE_DIM}│{RESET} That means a Spec Kit project — a folder containing a {BOLD}.specify/{RESET} directory.")
    print(f"{PURPLE_DIM}│{RESET} Not initialized yet? This installer can set it up for you (step 2).")
    print(f"{PURPLE_DIM}└{line}{RESET}")


# --------------------------------------------------------------------------- #
# Subprocess helpers
# --------------------------------------------------------------------------- #

def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    """Run a command, capturing output as text."""
    return subprocess.run(cmd, text=True, capture_output=True, **kwargs)


def run_interactive(cmd: list[str]) -> int:
    """Run a command attached to the terminal (for interactive flows)."""
    # Flush our own buffered output first so it appears before the child's,
    # even when stdout is piped (e.g. `| tee`) rather than a live terminal.
    sys.stdout.flush()
    try:
        return subprocess.call(cmd)
    except KeyboardInterrupt:
        return 130


# --------------------------------------------------------------------------- #
# Steps
# --------------------------------------------------------------------------- #

def _specify_version_detail() -> str:
    version = run(["specify", "--version"])
    return version.stdout.strip() or version.stderr.strip() or "found"


def _latest_speckit_tag() -> str | None:
    """Latest Spec Kit release tag (e.g. 'v0.11.9'), or None if unreachable.

    Uses the public GitHub API — no auth needed.
    """
    import urllib.request

    req = urllib.request.Request(
        SPECKIT_LATEST_API,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "spectra-setup"},
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


def ensure_uv() -> str | None:
    """Return the path to `uv`, installing it (with consent) if missing."""
    uv = shutil.which("uv")
    if uv:
        return uv

    warn("`uv` — the installer Spec Kit recommends — isn't on your PATH.")
    if not confirm("Install uv now (from astral.sh)?"):
        return None

    if platform.system() == "Windows":
        ps = shutil.which("pwsh") or shutil.which("powershell")
        if not ps:
            warn("Couldn't find PowerShell to run the uv installer.")
            return None
        code = run_interactive(
            [ps, "-NoProfile", "-ExecutionPolicy", "ByPass", "-Command",
             f"irm {UV_INSTALL_PS1} | iex"]
        )
    elif shutil.which("curl"):
        code = run_interactive(["sh", "-c", f"curl -LsSf {UV_INSTALL_SH} | sh"])
    elif shutil.which("wget"):
        code = run_interactive(["sh", "-c", f"wget -qO- {UV_INSTALL_SH} | sh"])
    else:
        warn("Need `curl` or `wget` to install uv.")
        return None

    if code != 0:
        warn("uv installation did not complete.")
        return None

    home = Path.home()
    _prepend_to_path(home / ".local" / "bin", home / ".cargo" / "bin")
    return shutil.which("uv")


def install_speckit(uv: str) -> bool:
    """Install the `specify` CLI at the latest Spec Kit release via uv."""
    tag = _latest_speckit_tag()
    if tag:
        info(f"Latest Spec Kit release: {tag}")
        cmd = [uv, "tool", "install", "specify-cli",
               "--from", f"git+{SPECKIT_GIT}@{tag}", "--force"]
    else:
        warn("Couldn't reach the GitHub releases API — installing the latest published version.")
        cmd = [uv, "tool", "install", "specify-cli", "--force"]

    info("Installing the Spec Kit CLI with uv… (this can take a minute)")
    print()
    if run_interactive(cmd) != 0:
        return False

    # Put uv's tool bin dir on PATH for the rest of this run, and (best effort)
    # wire it into new shells so `specify` is there next time too.
    bin_dir = run([uv, "tool", "dir", "--bin"]).stdout.strip()
    _prepend_to_path(Path(bin_dir) if bin_dir else Path.home() / ".local" / "bin")
    run([uv, "tool", "update-shell"])
    return shutil.which("specify") is not None


def ensure_specify_installed() -> None:
    step(1, "Checking for the Spec Kit CLI (specify)")
    if shutil.which("specify"):
        ok(f"specify is installed ({_specify_version_detail()}).")
        return

    warn("Spec Kit's `specify` CLI isn't installed or isn't on your PATH.")
    print("  Spectra extensions install into a Spec Kit project, so it's required.")
    print()
    if not confirm("Install Spec Kit now?"):
        die(
            "Spec Kit is required to continue.",
            f"Install it yourself: {SPECKIT_INSTALL_URL}",
            "Then re-run this script.",
        )

    uv = ensure_uv()
    if not uv:
        die(
            "Couldn't set up `uv`, which Spec Kit's installer uses.",
            f"Install uv: {UV_DOCS_URL}",
            f"Then: uv tool install specify-cli --from git+{SPECKIT_GIT}@<latest-tag>",
            f"Or install Spec Kit another way: {SPECKIT_INSTALL_URL}",
        )

    if not install_speckit(uv):
        die(
            "Spec Kit installation didn't complete.",
            "If `specify` was installed but isn't found, open a new terminal and re-run,",
            "or ensure uv's tool bin directory is on PATH (`uv tool update-shell`).",
        )

    ok(f"Spec Kit installed ({_specify_version_detail()}).")


def check_in_specify_project() -> Path:
    step(2, "Checking this is a Spec Kit project")
    here = Path.cwd()
    for candidate in [here, *here.parents]:
        if (candidate / ".specify").is_dir():
            ok(f"Spec Kit project detected at {candidate}.")
            return candidate

    warn("This folder isn't a Spec Kit project (no .specify/ directory found).")
    print("  Spectra installs extensions into a Spec Kit project, so this folder")
    print("  needs Spec Kit initialized first. I can do that here for you — it runs")
    print(f"  `specify init` in {BOLD}{here}{RESET} and won't touch anything outside it.")
    print()
    if not confirm("Initialize Spec Kit in this folder now?"):
        die(
            "A Spec Kit project is required to continue.",
            "Run `specify init` here (or cd into an existing project), then re-run this script.",
            f"See {SPECKIT_INSTALL_URL}",
        )

    info("Initializing Spec Kit — pick your coding agent if prompted…")
    print()
    code = run_interactive(["specify", "init", "--here", "--force"])
    if code != 0 or not (here / ".specify").is_dir():
        die(
            "Spec Kit initialization didn't complete.",
            "Try running `specify init --here` yourself, then re-run this script.",
        )
    ok(f"Spec Kit project initialized at {here}.")
    return here


def add_catalog() -> bool:
    """Register the Spectra catalog, then install the extension into this project.

    Returns True once the extension is installed.
    """
    step(3, "Registering the Spectra catalog and installing Spectra")
    info("Adding the Spectra catalog…")
    add = run(
        [
            "specify", "extension", "catalog", "add", CATALOG_URL,
            "--name", "spectra", "--priority", "5", "--install-allowed",
        ]
    )
    combined = (add.stdout + add.stderr).lower()
    if add.returncode == 0:
        ok("Spectra catalog registered.")
    elif "already" in combined or "exists" in combined:
        ok("Spectra catalog was already registered.")
    else:
        warn("Could not register the catalog automatically:")
        print(textwrap.indent((add.stdout + add.stderr).strip(), "  "))
        print("  You can retry the command shown in the README.")
        return False

    print()
    info("Installing the Spectra extension…")
    print()
    code = run_interactive(["specify", "extension", "add", "spectra"])
    if code != 0:
        print()
        warn("Could not install the Spectra extension automatically.")
        print(f"  Install it yourself: {BOLD}specify extension add spectra{RESET}")
        return False
    return True


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def main() -> None:
    splash()
    intro_note()
    ensure_specify_installed()
    check_in_specify_project()
    installed = add_catalog()

    print()
    if installed:
        print(f"{GREEN}{BOLD}All set!{RESET} {PURPLE}Spectra is ready to use.{RESET}")
        print()
        print("Restart your AI agent to pick up the new commands.")
        print(f"{PURPLE_DIM}This installer has done its job — you can safely delete spectra-setup.py now.{RESET}")
    else:
        print(
            f"{YELLOW}{BOLD}Almost there.{RESET} The catalog is registered — finish with "
            f"{BOLD}specify extension add spectra{RESET}."
        )
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        fail("Interrupted.")
        sys.exit(130)
