# Copyright 2026 TELUS Digital
# SPDX-License-Identifier: Apache-2.0

"""Terminal presentation — colors, the splash banner, prompts, and subprocess helpers.

Everything user-facing lives here so the install flow reads as a sequence of steps rather than a
wall of escape codes. Color is suppressed when stdout is not a TTY or when NO_COLOR is set.
"""

from __future__ import annotations

import os
import platform
import re
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


def step(n: int, title: str, *, total: int = 3) -> None:
    """A numbered step header. `total` defaults to 3, which was the whole install before coverage existed.

    The total is passed in rather than hard-coded because the install has a fourth step only in projects
    with an agent that lacks Spectra's commands — and a run that printed `[1/4]` and then showed three
    steps would be worse than no count at all.
    """
    print()
    print(f"{BOLD}{PURPLE}[{n}/{total}]{RESET} {BOLD}{title}{RESET}")


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
# Help panels
# --------------------------------------------------------------------------- #

MAX_WIDTH = 88

_ANSI = re.compile(r"\033\[[0-9;]*m")


def visible_len(s: str) -> int:
    """Length of `s` as rendered — color escapes occupy no columns."""
    return len(_ANSI.sub("", s))


def _box_width() -> int:
    return min(shutil.get_terminal_size((80, 24)).columns, MAX_WIDTH)


def panel(title: str, rows) -> None:
    """Draw a rounded, titled box of label/description pairs, in Spectra's palette.

    `rows` is a sequence of `(label, description)`; labels arrive pre-colored, so widths are
    measured with `visible_len` rather than `len`. Descriptions wrap inside the box.
    """
    width = _box_width()
    inner = width - 4  # "│ " + content + " │"
    label_w = min(max((visible_len(lb) for lb, _ in rows), default=0), max(12, inner // 2))
    desc_w = max(inner - label_w - 2, 20)

    fill = max(width - 5 - len(title), 0)
    print(f"{PURPLE_DIM}╭─{RESET} {BOLD}{title}{RESET} {PURPLE_DIM}{'─' * fill}╮{RESET}")
    for label, desc in rows:
        for i, line in enumerate(textwrap.wrap(desc, width=desc_w) or [""]):
            left = label if i == 0 else ""
            content = f"{left}{' ' * max(label_w - visible_len(left), 0)}  {line}"
            gap = " " * max(inner - visible_len(content), 0)
            print(f"{PURPLE_DIM}│{RESET} {content}{gap} {PURPLE_DIM}│{RESET}")
    print(f"{PURPLE_DIM}╰{'─' * (width - 2)}╯{RESET}")


# --------------------------------------------------------------------------- #
# The agent roster
# --------------------------------------------------------------------------- #

AVAILABLE_GLYPH = "✅"
PLANNED_GLYPH = "🚧"

PROVIDER_LABELS = {"spectra": "Spectra", "speckit": "Spec Kit"}


def agent_list(roster, installed=None) -> None:
    """Print the roster grouped by SDLC phase, one line per agent.

    Grouping is what keeps forty-plus entries readable: a flat list of that length is a wall, while
    seven labelled groups of four to nine can be skimmed. Rows are aligned into columns rather than
    boxed, because a box would force the longest command to wrap on an 80-column terminal and the
    command is the part a user copies.

    Four things are unambiguous on every row — status, type, provider, and either the command or the
    fact that there is not one yet. `installed` is a tri-state: True or False inside a Spec Kit
    project, and None outside one, where the question does not apply and the column is omitted.
    """
    groups = roster.grouped()
    title_w = max((len(agent.title) for agent in roster.agents), default=0)
    type_w = max((len(agent.type) for agent in roster.agents), default=0)
    provider_w = max(len(label) for label in PROVIDER_LABELS.values())

    for phase, agents in groups:
        print()
        print(f"{BOLD}{PURPLE}{phase.title}{RESET} {PURPLE_DIM}· {phase.aidlc}{RESET}")
        for agent in agents:
            glyph = f"{GREEN}{AVAILABLE_GLYPH}{RESET}" if agent.available \
                else f"{YELLOW}{PLANNED_GLYPH}{RESET}"
            title = f"{agent.title}{' ' * (title_w - len(agent.title))}"
            kind = f"{PURPLE_DIM}{agent.type}{' ' * (type_w - len(agent.type))}{RESET}"
            provider_label = PROVIDER_LABELS.get(agent.provider, agent.provider)
            provider = (f"{PURPLE_DIM}{provider_label}"
                        f"{' ' * (provider_w - len(provider_label))}{RESET}")
            if agent.command:
                trailing = f"{CYAN}{agent.command}{RESET}"
            else:
                trailing = dim("under development")
            row = f"  {glyph} {title}  {kind}  {provider}  {trailing}"
            if installed and agent.shipped:
                row += f"  {GREEN}✓ installed here{RESET}"
            print(row)

    available = sum(1 for agent in roster.agents if agent.available)
    print()
    print(dim(f"  {len(roster.agents)} agents · {available} available today · "
              f"{len(roster.agents) - available} under development"))
    print(dim("  Spec Kit agents come with Spec Kit itself — Spectra builds on them but does not "
              "install or version them."))
    if installed is False:
        print(dim("  Spectra is not installed in this project. Add it with: spectra install"))
    print()



# --------------------------------------------------------------------------- #
# The stack health table
# --------------------------------------------------------------------------- #

# Status glyphs, reusing the vocabulary ok()/warn()/fail() already established so the CLI speaks one
# visual language.
GLYPH_OK = f"{GREEN}✓{RESET}"
GLYPH_WARN = f"{YELLOW}!{RESET}"
GLYPH_FAIL = f"{RED}✗{RESET}"
GLYPH_NONE = f"{PURPLE_DIM}–{RESET}"


def health_table(rows) -> None:
    """Print aligned `label: glyph phrase` rows, each optionally followed by indented children.

    `rows` is a sequence of `(label, glyph, phrase)` — or `(label, glyph, phrase, children)`, where
    `children` is a sequence of the same triples to render beneath that row. The glyph and phrase are
    already coloured and formatted by the caller.

    **One renderer, two callers**: the status table from `spectra version` and the outcome table from
    `spectra update` have the same shape, and letting them share this keeps them aligned by construction —
    they print adjacent in a single update run, which is exactly where two implementations would visibly
    drift. Children are aligned to their own width rather than the parent's, so a long component label
    cannot push a short integration key off to the right.

    Columns rather than a box: `panel()` would force the longest version transition to wrap on an
    80-column terminal, and the versions are the part a user reads most closely.
    """
    if not rows:
        return
    rows = [tuple(row) for row in rows]
    label_w = max(len(row[0]) for row in rows)
    child_w = max((len(child[0]) for row in rows for child in (row[3] if len(row) > 3 else ())),
                  default=0)
    for row in rows:
        label, glyph, phrase = row[0], row[1], row[2]
        pad = " " * (label_w - len(label))
        print(f"  {label}:{pad} {glyph} {phrase}")
        for child_label, child_glyph, child_phrase in (row[3] if len(row) > 3 else ()):
            child_pad = " " * (child_w - len(child_label))
            print(f"    {child_label}:{child_pad} {child_glyph} {child_phrase}")


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
