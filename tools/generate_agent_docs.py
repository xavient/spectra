#!/usr/bin/env python3
"""Rewrite the structured agent listings from `agents-list.json`.

**Maintainer tooling. Not shipped.** `pyproject.toml` lists its packages explicitly
(`packages = ["spectra_cli"]`), so nothing under `tools/` reaches a user's machine, and the shipped
CLI gains no dependency from anything here.

Run it after editing the roster::

    python tools/generate_agent_docs.py            # rewrite the generated regions
    python tools/generate_agent_docs.py --check    # verify without writing (what CI runs)

Four regions are owned in full and rewritten on every run; everything outside them is hand-written
and left byte-identical. The division is by kind of content, not by file: **if it is a table or a
list, it is generated; if it is a paragraph, it is written.** Roughly forty of the forty-plus roster
entries are pure classification — title, phase, type, status — and those are exactly the entries that
rot silently. The handful of shipped agents carrying real explanatory prose keep it hand-authored,
with `--check` asserting only that the prose *exists*, never what it says.

The roster is loaded through :mod:`spectra_cli.roster`, the same parser the CLI uses, so the two can
never disagree about what a valid roster is. The dependency runs tools -> package, never the reverse.
"""

from __future__ import annotations

import argparse
import re
import sys
import textwrap
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from spectra_cli import roster as roster_module  # noqa: E402

ROSTER = REPO_ROOT / "agents-list.json"
MANIFEST = REPO_ROOT / "spectra" / "extension.yml"

# Hand-written documentation wraps at 100 columns; generated content matches so the diff between a
# hand-maintained table and its generated replacement is about content, not reflow.
WRAP = 100

START_MARKER = "<!-- SPECTRA:GENERATED START id={region} -->"
END_MARKER = "<!-- SPECTRA:GENERATED END id={region} -->"
NOTICE = ("<!-- Generated from agents-list.json — do not edit by hand. "
          "Run: python tools/generate_agent_docs.py -->")

ANCHOR = re.compile(r"<!--\s*SPECTRA:AGENT id=([a-z0-9-]+)\s*-->")
MANIFEST_COMMAND = re.compile(r'^    - name: "(speckit\.spectra\.[^"]+)"$', re.M)

TYPE_LABELS = {"core": "Core", "add-on": "Add-on"}
STATUS_LABELS = {"available": "✅ available", "planned": "🚧 under dev"}


class GeneratorError(Exception):
    """Something is wrong with the roster, a marker, or a document. Message names the culprit."""


# --------------------------------------------------------------------------- #
# Renderers
# --------------------------------------------------------------------------- #

def _claude_trigger(command: str) -> str:
    """`speckit.constitution` -> `/speckit-constitution`, the form Claude registers."""
    return "/" + command.replace(".", "-")


def _wrap(text: str, indent: str = "", subsequent: str = None) -> list:
    """Wrap to WRAP columns deterministically — no platform or locale input."""
    return textwrap.wrap(
        text,
        width=WRAP,
        initial_indent=indent,
        subsequent_indent=subsequent if subsequent is not None else indent,
        break_long_words=False,
        break_on_hyphens=False,
    ) or [indent.rstrip()]


def render_readme_table(roster) -> list:
    """The Agents table, plus the sentence naming which available agents are Spec Kit's own.

    That sentence enumerates nine agent titles. It is classification wearing prose clothing, and it
    would drift on the very first roster change while every table around it stayed correct — so the
    region is drawn wide enough to include it.
    """
    aidlc = {phase.id: phase.aidlc for phase in roster.phases}
    titles = {phase.id: phase.title for phase in roster.phases}

    lines = [
        "| Agent | SDLC phase | AI-DLC phase | Type | Status |",
        "| ----- | ---------- | ------------ | ---- | ------ |",
    ]
    for agent in roster.agents:
        lines.append(
            f"| {agent.title} | {titles[agent.phase]} | {aidlc[agent.phase]} "
            f"| {TYPE_LABELS[agent.type]} | {STATUS_LABELS[agent.status]} |"
        )

    speckit = [a.title for a in roster.agents if a.provider == "speckit" and a.available]
    sentence = (
        f"The agents marked ✅ that aren't shipped by Spectra ({', '.join(speckit)}) are "
        "Spec Kit's own core commands — Spectra layers on top of them."
    )
    return lines + [""] + _wrap(sentence)


def render_speckit_core(roster) -> list:
    """One subsection per Spec Kit-provided agent: title, command, description, how to run it."""
    lines = []
    for agent in roster.agents:
        if agent.provider != "speckit":
            continue
        if lines:
            lines.append("")
        lines.append(f"### {agent.title} — `{agent.command}` ✅")
        lines.append("")
        lines.extend(_wrap(agent.description))
        lines.append("")
        lines.append(f"- **Run it (Claude)** — `{_claude_trigger(agent.command)}`")
    return lines


def render_roadmap(roster) -> list:
    """Planned agents, grouped under their phase title, in roster order."""
    lines = []
    for phase, agents in roster.grouped():
        planned = [agent for agent in agents if not agent.available]
        if not planned:
            continue
        if lines:
            lines.append("")
        lines.append(f"### {phase.title}")
        lines.append("")
        for agent in planned:
            entry = f"**{agent.title}** ({TYPE_LABELS[agent.type]}) — {agent.description}"
            lines.extend(_wrap(entry, indent="- ", subsequent="  "))
    return lines


def render_spectra_commands(roster) -> list:
    """The extension README's Commands table.

    No Effect column: the roster does not model per-agent effect, and inventing a field to reproduce
    one column would be the wrong trade. `spectra/extension.yml` declares `effect: read-write` for
    the extension as a whole, and the prose around this table says so.
    """
    lines = [
        "| Command | What it does |",
        "| ------- | ------------ |",
    ]
    for agent in roster.shipped():
        lines.append(f"| `{agent.command}` | {agent.description} |")
    return lines


REGIONS = {
    "readme-agents-table": ("README.md", render_readme_table),
    "agents-list-speckit-core": ("AGENTS_LIST.md", render_speckit_core),
    "agents-list-roadmap": ("AGENTS_LIST.md", render_roadmap),
    "spectra-readme-commands": ("spectra/README.md", render_spectra_commands),
}


# --------------------------------------------------------------------------- #
# Marked regions
# --------------------------------------------------------------------------- #

def _locate(text: str, region: str, relative_path: str):
    """(start_of_body, end_of_body) for a region, or raise.

    Never guesses a region's extent, never appends a missing marker, and never skips a document it
    cannot parse — silently skipping is how a "successful" run leaves documentation stale.
    """
    start = START_MARKER.format(region=region)
    end = END_MARKER.format(region=region)

    if text.count(start) == 0:
        raise GeneratorError(f"{relative_path}: missing start marker for region {region!r}.")
    if text.count(start) > 1:
        raise GeneratorError(f"{relative_path}: start marker for region {region!r} appears "
                             f"{text.count(start)} times.")
    if text.count(end) == 0:
        raise GeneratorError(f"{relative_path}: missing end marker for region {region!r}.")
    if text.count(end) > 1:
        raise GeneratorError(f"{relative_path}: end marker for region {region!r} appears "
                             f"{text.count(end)} times.")

    body_start = text.index(start) + len(start)
    body_end = text.index(end)
    if body_end < body_start:
        raise GeneratorError(f"{relative_path}: end marker for region {region!r} precedes its start "
                             "marker.")
    return body_start, body_end


def _known_region_ids(text: str) -> set:
    return set(re.findall(r"<!--\s*SPECTRA:GENERATED START id=([a-z0-9-]+)\s*-->", text))


def render_region(region: str, roster) -> str:
    """The full body of a region, including its do-not-edit notice.

    Line endings are always `\\n`, whatever the platform, so a Windows checkout does not look drifted
    to CI.
    """
    _, renderer = REGIONS[region]
    lines = renderer(roster)
    return "\n" + NOTICE + "\n\n" + "\n".join(lines) + "\n"


def apply_regions(roster, *, write: bool):
    """Rewrite (or compare) every region. Returns the list of paths whose content differs."""
    by_file = {}
    for region, (relative_path, _) in REGIONS.items():
        by_file.setdefault(relative_path, []).append(region)

    stale = []
    for relative_path, regions in sorted(by_file.items()):
        path = REPO_ROOT / relative_path
        try:
            original = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise GeneratorError(f"{relative_path}: could not be read ({exc}).") from exc

        unknown = _known_region_ids(original) - set(REGIONS)
        if unknown:
            raise GeneratorError(f"{relative_path}: unknown generated region(s) "
                                 f"{', '.join(sorted(unknown))}.")

        updated = original
        for region in regions:
            body_start, body_end = _locate(updated, region, relative_path)
            updated = updated[:body_start] + render_region(region, roster) + updated[body_end:]

        if updated != original:
            stale.append(relative_path)
            if write:
                path.write_text(updated, encoding="utf-8", newline="\n")
    return stale


# --------------------------------------------------------------------------- #
# Verification
# --------------------------------------------------------------------------- #

def check_prose_anchors(roster) -> list:
    """Every shipped agent has a prose block, and no prose block exists for anything else.

    Matched by stable id, never by heading text: a title is display text and is free to change, so
    matching on it would break the moment an agent is renamed — which is exactly what this change
    does to the PR agent.
    """
    problems = []
    path = REPO_ROOT / "AGENTS_LIST.md"
    text = path.read_text(encoding="utf-8")
    anchored = ANCHOR.findall(text)

    duplicates = {value for value in anchored if anchored.count(value) > 1}
    for value in sorted(duplicates):
        problems.append(f"AGENTS_LIST.md: prose anchor for {value!r} appears more than once.")

    shipped = {agent.id for agent in roster.shipped()}
    for agent_id in sorted(shipped - set(anchored)):
        problems.append(
            f"AGENTS_LIST.md: no prose block for shipped agent {agent_id!r}. Write one, anchored "
            f"with <!-- SPECTRA:AGENT id={agent_id} -->.")
    for agent_id in sorted(set(anchored) - shipped):
        known = roster.by_id(agent_id)
        reason = "is not listed as shipped by Spectra" if known else "is not in the roster"
        problems.append(f"AGENTS_LIST.md: prose block for {agent_id!r}, which {reason}.")
    return problems


def check_title_containment(roster) -> list:
    """Each shipped agent's canonical title appears in `spectra/README.md`.

    Deliberately weak — substring presence, not structural equality. It exists to catch a
    hand-written heading drifting away from the roster, which is a real failure that already happened
    four times over for one agent. Anything stronger would mean generating the prose, and the whole
    point of the split is that we do not.
    """
    problems = []
    relative_path = "spectra/README.md"
    text = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
    for agent in roster.shipped():
        if agent.title not in text:
            problems.append(
                f"{relative_path}: does not mention the canonical title for {agent.id!r} "
                f"({agent.title!r}). A heading has drifted from the roster.")
    return problems


def check_manifest_agreement(roster) -> list:
    """The roster and the manifest agree on membership and on command strings — and only those.

    Descriptions are deliberately not compared. The manifest's are consumed by Spec Kit and the
    user's coding agent at install time; the roster's are one-liners for a table. Forcing them equal
    would make one of the two worse.
    """
    problems = []
    try:
        text = MANIFEST.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"spectra/extension.yml: could not be read ({exc})."]

    manifest_commands = set(MANIFEST_COMMAND.findall(text))
    roster_commands = {agent.command: agent.id for agent in roster.shipped()}

    for command in sorted(manifest_commands - set(roster_commands)):
        problems.append(f"spectra/extension.yml registers {command!r}, which the roster does not "
                        "list as a shipped Spectra agent.")
    for command in sorted(set(roster_commands) - manifest_commands):
        problems.append(f"agents-list.json lists {roster_commands[command]!r} with command "
                        f"{command!r}, which spectra/extension.yml does not register.")
    return problems


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #

def run(check: bool) -> int:
    try:
        roster = roster_module.load(ROSTER, strict=True)
    except roster_module.RosterError as exc:
        print(f"error: agents-list.json: {exc}", file=sys.stderr)
        return 1

    problems = []
    try:
        stale = apply_regions(roster, write=not check)
    except GeneratorError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if check:
        for relative_path in stale:
            problems.append(
                f"{relative_path}: a generated region does not match agents-list.json. "
                "Run: python tools/generate_agent_docs.py")
        problems += check_prose_anchors(roster)
        problems += check_title_containment(roster)
        problems += check_manifest_agreement(roster)

        if problems:
            print(f"error: {len(problems)} problem(s) found:", file=sys.stderr)
            for problem in problems:
                print(f"  - {problem}", file=sys.stderr)
            return 1
        print(f"agents-list.json ({len(roster.agents)} agents) matches every generated region; "
              f"{len(roster.shipped())} prose blocks present; roster and manifest agree.")
        return 0

    # Writing mode still runs the assertions that do not depend on generated content, so a
    # maintainer who forgets a prose block finds out now rather than in CI.
    problems += check_prose_anchors(roster)
    problems += check_manifest_agreement(roster)
    if stale:
        for relative_path in stale:
            print(f"rewrote {relative_path}")
    else:
        print("every generated region was already current")
    if problems:
        print(f"warning: {len(problems)} problem(s) remain:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="generate_agent_docs",
        description="Rewrite the structured agent listings from agents-list.json.",
    )
    parser.add_argument("--check", action="store_true",
                        help="verify without writing; exit non-zero on any mismatch")
    args = parser.parse_args(argv)
    return run(check=args.check)


if __name__ == "__main__":
    sys.exit(main())
