# Copyright 2026 TELUS Digital
# SPDX-License-Identifier: Apache-2.0

"""The agent roster: one parser, two callers.

`agents-list.json` is the single source of truth for the agents Spectra offers. Two very different
things read it — the `spectra agent-list` command fetches it over the network, and the maintainer's
documentation generator loads it from disk — and they must agree exactly on what a valid roster is.
So both come through :func:`parse` here. A second parser in `tools/` would be a second opinion, and
the first time the two disagreed, one of them would be publishing something the other rejected.

**Schema tolerance is asymmetric on purpose.** A newer *minor* schema renders with a notice and
unknown fields are ignored; only a newer *major* schema is refused. Principle VI promises that a new
agent reaches every installed CLI with no CLI release — if any additive change to this file broke
`agent-list` for older installs, that promise would quietly become false.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from spectra_cli import net

ROSTER_PATH = "agents-list.json"

# The highest schema major this CLI understands. A roster at 1.x renders; 2.x is refused.
SUPPORTED_SCHEMA_MAJOR = 1

STATUSES = ("available", "planned")
TYPES = ("core", "add-on")
PROVIDERS = ("spectra", "speckit")

_SLUG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


class RosterError(Exception):
    """The roster could not be understood. The message is safe to show a user verbatim."""


class Agent:
    """One roster entry. `title` is display text; `id` is what machines key off."""

    __slots__ = ("id", "title", "description", "status", "phase", "type", "provider", "command")

    def __init__(self, data: dict):
        self.id = data["id"]
        self.title = data["title"]
        self.description = data["description"]
        self.status = data["status"]
        self.phase = data["phase"]
        self.type = data["type"]
        self.provider = data["provider"]
        self.command = data.get("command")

    @property
    def available(self) -> bool:
        return self.status == "available"

    @property
    def from_spectra(self) -> bool:
        return self.provider == "spectra"

    @property
    def shipped(self) -> bool:
        """Shipped in the Spectra extension today — the set the manifest must agree with."""
        return self.from_spectra and self.available

    def __repr__(self):  # pragma: no cover - diagnostics only
        return f"Agent({self.id!r}, {self.status!r}, {self.provider!r})"


class Phase:
    """An SDLC phase and the AI-DLC phase it belongs to."""

    __slots__ = ("id", "title", "aidlc", "agents")

    def __init__(self, data: dict):
        self.id = data["id"]
        self.title = data["title"]
        self.aidlc = data["aidlc"]
        self.agents = []

    def __repr__(self):  # pragma: no cover - diagnostics only
        return f"Phase({self.id!r}, {len(self.agents)} agents)"


class Roster:
    """A parsed roster: phases in order, each holding its agents in order."""

    __slots__ = ("schema_version", "schema_major", "schema_minor", "phases", "agents", "newer_minor")

    def __init__(self, schema_version, major, minor, phases, agents, newer_minor):
        self.schema_version = schema_version
        self.schema_major = major
        self.schema_minor = minor
        self.phases = phases
        self.agents = agents
        self.newer_minor = newer_minor

    def grouped(self):
        """(phase, agents) pairs in roster order, skipping phases with no agents."""
        return [(phase, phase.agents) for phase in self.phases if phase.agents]

    def shipped(self):
        """Agents the Spectra extension ships today, in roster order."""
        return [agent for agent in self.agents if agent.shipped]

    def by_id(self, agent_id):
        for agent in self.agents:
            if agent.id == agent_id:
                return agent
        return None


# --------------------------------------------------------------------------- #
# Parsing
# --------------------------------------------------------------------------- #

def _parse_schema_version(raw):
    if not isinstance(raw, str) or not raw.strip():
        raise RosterError("the roster is missing its schema_version.")
    parts = raw.strip().split(".")
    try:
        major = int(parts[0])
        minor = int(parts[1]) if len(parts) > 1 else 0
    except (ValueError, IndexError):
        raise RosterError(f"the roster declares an unreadable schema_version ({raw!r}).") from None
    return raw.strip(), major, minor


def parse(data, *, strict=False) -> Roster:
    """Validate and structure a roster document.

    `strict=False` — the CLI's mode — ignores unrecognized fields so a newer minor schema still
    renders. `strict=True` — the generator's mode — rejects them, because an unrecognized field in
    the committed roster means a typo or a schema bump nobody expanded the tooling for.

    Raises :class:`RosterError` for a malformed document, and for a schema major this CLI does not
    understand.
    """
    if not isinstance(data, dict):
        raise RosterError("the roster is not a JSON object.")

    schema_version, major, minor = _parse_schema_version(data.get("schema_version"))
    if major > SUPPORTED_SCHEMA_MAJOR:
        raise RosterError(
            f"the roster uses schema version {schema_version}, which needs a newer Spectra CLI.\n"
            "  Update it with: spectra update")
    newer_minor = major == SUPPORTED_SCHEMA_MAJOR and minor > _current_minor()

    raw_phases = data.get("phases")
    raw_agents = data.get("agents")
    if not isinstance(raw_phases, list) or not raw_phases:
        raise RosterError("the roster has no phases.")
    if not isinstance(raw_agents, list) or not raw_agents:
        raise RosterError("the roster has no agents.")

    phases, order = [], {}
    for entry in raw_phases:
        _require(entry, ("id", "title", "aidlc"), "phase")
        if not _SLUG.match(entry["id"]):
            raise RosterError(f"phase id {entry['id']!r} is not a lowercase slug.")
        if entry["id"] in order:
            raise RosterError(f"phase id {entry['id']!r} appears twice.")
        phase = Phase(entry)
        order[phase.id] = phase
        phases.append(phase)

    agents, seen = [], set()
    for entry in raw_agents:
        _require(entry, ("id", "title", "description", "status", "phase", "type", "provider"), "agent")
        agent = Agent(entry)
        if not _SLUG.match(agent.id):
            raise RosterError(f"agent id {agent.id!r} is not a lowercase slug.")
        if agent.id in seen:
            raise RosterError(f"agent id {agent.id!r} appears twice.")
        seen.add(agent.id)
        if agent.status not in STATUSES:
            raise RosterError(f"agent {agent.id!r} has status {agent.status!r}.")
        if agent.type not in TYPES:
            raise RosterError(f"agent {agent.id!r} has type {agent.type!r}.")
        if agent.provider not in PROVIDERS:
            raise RosterError(f"agent {agent.id!r} has provider {agent.provider!r}.")
        if agent.phase not in order:
            raise RosterError(f"agent {agent.id!r} names unknown phase {agent.phase!r}.")
        if not agent.description.strip() or "\n" in agent.description or "\r" in agent.description:
            raise RosterError(f"agent {agent.id!r} needs a single-line, non-empty description.")
        if agent.available and not agent.command:
            raise RosterError(f"agent {agent.id!r} is available but records no command.")
        if not agent.available and agent.command is not None:
            raise RosterError(f"agent {agent.id!r} is planned but records a command.")
        if strict:
            unknown = set(entry) - set(Agent.__slots__)
            if unknown:
                raise RosterError(
                    f"agent {agent.id!r} carries unrecognized field(s): {', '.join(sorted(unknown))}.")
        order[agent.phase].agents.append(agent)
        agents.append(agent)

    return Roster(schema_version, major, minor, phases, agents, newer_minor)


def _require(entry, keys, kind):
    if not isinstance(entry, dict):
        raise RosterError(f"a {kind} entry is not an object.")
    missing = [key for key in keys if not entry.get(key)]
    if missing:
        label = entry.get("id", "<no id>")
        raise RosterError(f"{kind} {label!r} is missing: {', '.join(missing)}.")


def _current_minor() -> int:
    """The minor schema this CLI was written against.

    Kept as a function so the supported version lives in one place next to the major, and so tests
    can reason about "newer minor" without hard-coding a number twice.
    """
    return 0


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #

def load(path=ROSTER_PATH, *, strict=True) -> Roster:
    """Parse a roster from a local file. The generator's entry point."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise RosterError(f"could not read {path} ({exc}).") from exc
    try:
        data = json.loads(text)
    except ValueError as exc:
        raise RosterError(f"{path} is not valid JSON ({exc}).") from exc
    return parse(data, strict=strict)


def fetch(timeout: int = net.TIMEOUT) -> Roster:
    """Parse the published roster. The CLI's entry point.

    Lets :class:`net.FetchError` through unchanged — "could not reach it" and "reached it but could
    not understand it" are different problems and deserve different messages.
    """
    return parse(net.fetch_json(ROSTER_PATH, timeout=timeout), strict=False)
