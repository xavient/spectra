"""The committed roster itself, against its published contract.

`tests/test_roster.py` proves the parser is right. This file proves the *data* is right — that
`agents-list.json` as committed satisfies every rule in
`specs/006-agent-roster-cli/contracts/agents-list.schema.json`, and that it still agrees with the
extension manifest it describes.
"""

from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import helpers as h  # noqa: E402
from spectra_cli import extension, roster  # noqa: E402

ROSTER_PATH = h.repo_file("agents-list.json")
MANIFEST_PATH = h.repo_file("spectra", "extension.yml")
SLUG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


class Shape(unittest.TestCase):
    """Rules the schema states, checked against the file as committed."""

    @classmethod
    def setUpClass(cls):
        cls.raw = json.loads(ROSTER_PATH.read_text(encoding="utf-8"))
        cls.parsed = roster.load(ROSTER_PATH)

    def test_it_parses_in_strict_mode(self):
        """Strict is the generator's mode: an unrecognized field means a typo nobody expanded for."""
        self.assertGreater(len(self.parsed.agents), 0)

    def test_the_schema_version_is_major_dot_minor(self):
        self.assertRegex(self.raw["schema_version"], r"^\d+\.\d+$")

    def test_only_the_contracted_top_level_keys_are_present(self):
        self.assertEqual(set(self.raw), {"schema_version", "phases", "agents"})

    def test_no_updated_at_field(self):
        """A hand-maintained timestamp nobody can verify is a field that lies."""
        self.assertNotIn("updated_at", self.raw)

    def test_every_agent_id_is_a_unique_slug(self):
        ids = [a["id"] for a in self.raw["agents"]]
        self.assertEqual(len(ids), len(set(ids)))
        for value in ids:
            self.assertRegex(value, SLUG)

    def test_every_phase_id_is_a_unique_slug(self):
        ids = [p["id"] for p in self.raw["phases"]]
        self.assertEqual(len(ids), len(set(ids)))
        for value in ids:
            self.assertRegex(value, SLUG)

    def test_every_aidlc_value_is_in_range(self):
        for phase in self.raw["phases"]:
            self.assertIn(phase["aidlc"], ("Inception", "Construction", "Operation"))

    def test_every_description_is_a_single_non_empty_line(self):
        for agent in self.raw["agents"]:
            self.assertTrue(agent["description"].strip(), agent["id"])
            self.assertNotIn("\n", agent["description"], agent["id"])
            self.assertNotIn("\r", agent["description"], agent["id"])

    def test_command_is_present_exactly_when_available(self):
        for agent in self.raw["agents"]:
            self.assertEqual("command" in agent, agent["status"] == "available", agent["id"])

    def test_no_agent_carries_an_unexpected_field(self):
        allowed = {"id", "title", "description", "status", "phase", "type", "provider", "command"}
        for agent in self.raw["agents"]:
            self.assertEqual(set(agent) - allowed, set(), agent["id"])

    def test_every_phase_resolves(self):
        known = {p["id"] for p in self.raw["phases"]}
        for agent in self.raw["agents"]:
            self.assertIn(agent["phase"], known, agent["id"])

    def test_agents_are_contiguous_by_phase_in_declared_phase_order(self):
        """The generator groups by walking the list once, so entries cannot be interleaved."""
        declared = [p["id"] for p in self.raw["phases"]]
        appeared = []
        for agent in self.raw["agents"]:
            if agent["phase"] not in appeared:
                appeared.append(agent["phase"])
        self.assertEqual(appeared, declared)

    def test_every_declared_phase_has_at_least_one_agent(self):
        used = {a["phase"] for a in self.raw["agents"]}
        self.assertEqual(used, {p["id"] for p in self.raw["phases"]})


class Content(unittest.TestCase):
    """The roster must cover what the documentation covered before it existed (FR-005)."""

    @classmethod
    def setUpClass(cls):
        cls.parsed = roster.load(ROSTER_PATH)

    def test_it_carries_the_full_published_roster(self):
        self.assertEqual(len(self.parsed.agents), 45)

    def test_it_splits_into_fourteen_available_and_thirty_one_planned(self):
        available = [a for a in self.parsed.agents if a.available]
        self.assertEqual(len(available), 14)
        self.assertEqual(len(self.parsed.agents) - len(available), 31)

    def test_spectra_ships_exactly_five_agents_today(self):
        self.assertEqual(sorted(a.id for a in self.parsed.shipped()),
                         ["adr", "brd", "create-pr", "domain-analyzer", "review-pr"])

    def test_nine_available_agents_come_from_spec_kit(self):
        speckit = [a for a in self.parsed.agents if a.provider == "speckit" and a.available]
        self.assertEqual(len(speckit), 9)

    def test_the_pr_agent_has_one_canonical_title(self):
        """FR-010: the name that used to differ in four places resolves here."""
        agent = self.parsed.by_id("create-pr")
        self.assertEqual(agent.title, "GitHub (PR)")
        self.assertEqual(agent.command, "speckit.spectra.create-pr")

    def test_titles_are_unique(self):
        titles = [a.title for a in self.parsed.agents]
        self.assertEqual(len(titles), len(set(titles)))

    def test_type_and_provider_are_independent(self):
        """`create-pr` is core *and* Spectra-provided, so the two fields cannot be collapsed."""
        agent = self.parsed.by_id("create-pr")
        self.assertEqual((agent.type, agent.provider), ("core", "spectra"))

    def test_seven_sdlc_phases_are_declared(self):
        self.assertEqual(len(self.parsed.phases), 7)


class ManifestAgreement(unittest.TestCase):
    """FR-019 and FR-019a, on the committed artifacts rather than on fixtures."""

    @classmethod
    def setUpClass(cls):
        cls.parsed = roster.load(ROSTER_PATH)
        cls.manifest = MANIFEST_PATH.read_text(encoding="utf-8")
        cls.manifest_commands = re.findall(r'^    - name: "(speckit\.spectra\.[^"]+)"$',
                                          cls.manifest, re.M)

    def test_the_shipped_set_matches_the_manifest(self):
        self.assertEqual(sorted(a.command for a in self.parsed.shipped()),
                         sorted(self.manifest_commands))

    def test_the_manifest_registers_no_command_the_roster_omits(self):
        roster_commands = {a.command for a in self.parsed.shipped()}
        for command in self.manifest_commands:
            self.assertIn(command, roster_commands)

    def test_every_shipped_command_uses_the_spectra_namespace(self):
        for agent in self.parsed.shipped():
            self.assertTrue(agent.command.startswith("speckit.spectra."), agent.id)

    def test_the_installed_manifest_version_is_readable(self):
        """The version scanner and the committed manifest must not drift apart."""
        self.assertIsNotNone(extension.read_manifest_version(MANIFEST_PATH))


if __name__ == "__main__":
    unittest.main()
