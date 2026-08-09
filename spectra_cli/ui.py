"""Terminal presentation — colors, the splash banner, prompts, and subprocess helpers.

Everything user-facing lives here so the install flow reads as a sequence of steps rather than a
wall of escape codes. Color is suppressed when stdout is not a TTY or when NO_COLOR is set.
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
import textwrap

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


def bold(msg: str) -> str:
    return f"{BOLD}{msg}{RESET}"


def dim(msg: str) -> str:
    return f"{PURPLE_DIM}{msg}{RESET}"


def plain(msg: str = "") -> None:
    print(msg)


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


def splash(version: str) -> None:
    print()
    for line in _banner("SPECTRA").splitlines():
        print(f"{PURPLE}{line}{RESET}")
    print()
    width = min(shutil.get_terminal_size((80, 24)).columns, 88)
    for line in textwrap.wrap(TAGLINE, width=width):
        print(f"{PURPLE_DIM}{line}{RESET}")
    print(f"{PURPLE_DIM}cli v{version}{RESET}")
    print()


def intro_note() -> None:
    """Remind the user this runs inside the target project folder."""
    line = "─" * 72
    print(f"{PURPLE_DIM}┌{line}{RESET}")
    print(f"{PURPLE_DIM}│{RESET} {BOLD}Run this from inside the project you want Spectra in.{RESET}")
    print(f"{PURPLE_DIM}│{RESET} That means a Spec Kit project — a folder containing a {BOLD}.specify/{RESET} directory.")
    print(f"{PURPLE_DIM}│{RESET} Not initialized yet? Spectra can set it up for you (step 2).")
    print(f"{PURPLE_DIM}└{line}{RESET}")


# --------------------------------------------------------------------------- #
# Subprocess helpers
# --------------------------------------------------------------------------- #

def run(cmd, **kwargs) -> subprocess.CompletedProcess:
    """Run a command, capturing output as text."""
    return subprocess.run(cmd, text=True, capture_output=True, **kwargs)


def run_interactive(cmd) -> int:
    """Run a command attached to the terminal (for interactive flows)."""
    # Flush our own buffered output first so it appears before the child's,
    # even when stdout is piped (e.g. `| tee`) rather than a live terminal.
    sys.stdout.flush()
    try:
        return subprocess.call(cmd)
    except KeyboardInterrupt:
        return 130
