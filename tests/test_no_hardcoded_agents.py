"""The roster is data, not code (FR-042, SC-002).

Principle VI's promise — that a new agent reaches every installed CLI with no CLI release — only holds
if the CLI never carries its own copy of the roster. `spectra_cli/install.py` already refuses to
hard-code the set of extensions it installs, reading `catalog.json` at run time; these tests hold the
same line for agents.

The checks are deliberately structural rather than keyword-based. Single words like "Testing" and
"Implementation" are ordinary English and appear in docstrings; what would signal a hard-coded roster
is a *listing* — several agents named together, a command string, or a description copied across.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import helpers as h  # noqa: E402
from spectra_cli import roster  # noqa: E402

PACKAGE = h.repo_file("spectra_cli")


def package_sources():
    """Every shipped Python source file, as (name, text)."""
    return [(path.name, path.read_text(encoding="utf-8")) for path in sorted(PACKAGE.glob("*.py"))]


class RosterIsNotInTheCode(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parsed = roster.load(h.repo_file("agents-list.json"))
        cls.sources = package_sources()

    def test_no_agent_description_is_copied_into_the_package(self):
        """A description in the code is a second source of truth by definition."""
        for name, text in self.sources:
            for agent in self.parsed.agents:
                self.assertNotIn(agent.description, text,
                                 f"{name} carries the description of {agent.id!r}")

    def test_no_agent_command_string_is_hard_coded(self):
        for name, text in self.sources:
            for agent in self.parsed.agents:
                if agent.command:
                    self.assertNotIn(agent.command, text,
                                     f"{name} hard-codes the command for {agent.id!r}")

    def test_no_module_enumerates_several_agents(self):
        """One generic word is prose; three agent titles in one file is a list."""
        titles = [agent.title for agent in self.parsed.agents]
        for name, text in self.sources:
            found = [title for title in titles if title in text]
            self.assertLess(len(found), 3, f"{name} appears to enumerate agents: {found}")

    def test_no_module_hard_codes_the_agent_count(self):
        """The count is derived from the fetched roster, never asserted in the code."""
        total = str(len(self.parsed.agents))
        for name, text in self.sources:
            for phrase in (f"{total} agents", f"= {total}  #", f"AGENT_COUNT = {total}"):
                self.assertNotIn(phrase, text, f"{name} hard-codes the agent count")

    def test_no_module_hard_codes_an_agent_id_list(self):
        ids = [agent.id for agent in self.parsed.agents]
        for name, text in self.sources:
            found = [value for value in ids if f'"{value}"' in text or f"'{value}'" in text]
            self.assertLess(len(found), 3, f"{name} appears to hard-code agent ids: {found}")


class TheRosterIsReadAtRunTime(unittest.TestCase):
    def test_the_roster_path_is_a_published_location_not_a_bundled_file(self):
        self.assertEqual(roster.ROSTER_PATH, "agents-list.json")

    def test_no_copy_of_the_roster_ships_inside_the_package(self):
        self.assertEqual(list(PACKAGE.glob("*.json")), [],
                         "the package must not carry a bundled roster")

    def test_the_command_reads_the_roster_over_the_network(self):
        """If `agent-list` ever stopped fetching, this fails: the served roster is the only source."""
        import contextlib
        import io

        from spectra_cli import cli

        served = h.roster()
        h.agent(served, "brd")["title"] = "Invented By The Test Only"
        buffer = io.StringIO()
        with h.serve_roster(served) as base, h.raw_base(base), \
             h.temp_project(is_project=False) as path, h.cwd(path):
            with contextlib.redirect_stdout(buffer):
                code = cli.main(["agent-list"])
        self.assertEqual(code, 0)
        self.assertIn("Invented By The Test Only", buffer.getvalue())


if __name__ == "__main__":
    unittest.main()
