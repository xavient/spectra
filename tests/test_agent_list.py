"""`spectra agent-list` — the discovery command (User Story 1).

Exercised through `cli.main()` rather than the renderer directly, because the behaviour that matters
is what a user sees and what the shell gets back.
"""

from __future__ import annotations

import contextlib
import io
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import helpers as h  # noqa: E402
from spectra_cli import cli  # noqa: E402


def run(argv):
    """Run the CLI, returning (exit code, captured stdout)."""
    buffer = io.StringIO()
    try:
        with contextlib.redirect_stdout(buffer):
            code = cli.main(argv)
    except SystemExit as exc:  # pragma: no cover - argparse paths
        code = exc.code
    return code, buffer.getvalue()


class Listing(unittest.TestCase):
    def test_it_lists_every_agent_grouped_by_phase(self):
        with h.serve_roster() as base, h.raw_base(base), \
             h.temp_project(is_project=False) as path, h.cwd(path):
            code, out = run(["agent-list"])
        self.assertEqual(code, 0)
        for title in ("Guardrails", "Domain Analyzer", "BRD Generator",
                      "GDPR Compliance", "GitHub (PR)"):
            self.assertIn(title, out)
        for phase in ("Foundation", "Requirements & Discovery", "Deployment & Operations"):
            self.assertIn(phase, out)

    def test_phases_appear_in_roster_order(self):
        with h.serve_roster() as base, h.raw_base(base), \
             h.temp_project(is_project=False) as path, h.cwd(path):
            _, out = run(["agent-list"])
        positions = [out.index(p) for p in
                     ("Foundation", "Requirements & Discovery", "Deployment & Operations")]
        self.assertEqual(positions, sorted(positions))

    def test_each_phase_shows_its_aidlc_phase(self):
        with h.serve_roster() as base, h.raw_base(base), \
             h.temp_project(is_project=False) as path, h.cwd(path):
            _, out = run(["agent-list"])
        self.assertIn("Inception", out)
        self.assertIn("Operation", out)

    def test_provider_is_evident_per_agent(self):
        with h.serve_roster() as base, h.raw_base(base), \
             h.temp_project(is_project=False) as path, h.cwd(path):
            _, out = run(["agent-list"])
        self.assertIn("Spec Kit", out)
        self.assertIn("Spectra", out)

    def test_type_is_evident_per_agent(self):
        with h.serve_roster() as base, h.raw_base(base), \
             h.temp_project(is_project=False) as path, h.cwd(path):
            _, out = run(["agent-list"])
        self.assertIn("core", out)
        self.assertIn("add-on", out)

    def test_a_planned_agent_shows_no_command(self):
        """FR-007: nothing planned may look runnable."""
        with h.serve_roster() as base, h.raw_base(base), \
             h.temp_project(is_project=False) as path, h.cwd(path):
            _, out = run(["agent-list"])
        planned_line = next(line for line in out.splitlines() if "GDPR Compliance" in line)
        self.assertIn("under development", planned_line)
        self.assertNotIn("speckit.", planned_line)

    def test_an_available_agent_shows_its_command(self):
        with h.serve_roster() as base, h.raw_base(base), \
             h.temp_project(is_project=False) as path, h.cwd(path):
            _, out = run(["agent-list"])
        line = next(line for line in out.splitlines() if "BRD Generator" in line)
        self.assertIn("speckit.spectra.brd", line)

    def test_the_summary_counts_available_and_planned(self):
        with h.serve_roster() as base, h.raw_base(base), \
             h.temp_project(is_project=False) as path, h.cwd(path):
            _, out = run(["agent-list"])
        self.assertIn("5 agents", out)
        self.assertIn("4 available today", out)
        self.assertIn("1 under development", out)

    def test_it_says_spec_kit_agents_are_not_spectras_to_manage(self):
        with h.serve_roster() as base, h.raw_base(base), \
             h.temp_project(is_project=False) as path, h.cwd(path):
            _, out = run(["agent-list"])
        self.assertIn("does not install or version them", out)


class WorksAnywhere(unittest.TestCase):
    def test_it_succeeds_outside_a_spec_kit_project(self):
        """FR-027: discovering what Spectra offers must not require having installed it."""
        with h.serve_roster() as base, h.raw_base(base), \
             h.temp_project(is_project=False) as path, h.cwd(path):
            code, out = run(["agent-list"])
        self.assertEqual(code, 0)
        self.assertIn("Guardrails", out)

    def test_it_does_not_mention_installation_state_outside_a_project(self):
        with h.serve_roster() as base, h.raw_base(base), \
             h.temp_project(is_project=False) as path, h.cwd(path):
            _, out = run(["agent-list"])
        self.assertNotIn("installed here", out)
        self.assertNotIn("not installed in this project", out)


class InstalledMarker(unittest.TestCase):
    """FR-048 — the one part of the output that depends on the current folder."""

    def test_shipped_agents_are_marked_when_installed_here(self):
        with h.serve_roster() as base, h.raw_base(base), \
             h.temp_project("1.3.1") as path, h.cwd(path):
            _, out = run(["agent-list"])
        line = next(line for line in out.splitlines() if "Domain Analyzer" in line)
        self.assertIn("installed here", line)

    def test_spec_kit_agents_are_never_marked_installed_by_spectra(self):
        with h.serve_roster() as base, h.raw_base(base), \
             h.temp_project("1.3.1") as path, h.cwd(path):
            _, out = run(["agent-list"])
        line = next(line for line in out.splitlines() if "Guardrails" in line)
        self.assertNotIn("installed here", line)

    def test_planned_spectra_agents_are_never_marked_installed(self):
        with h.serve_roster() as base, h.raw_base(base), \
             h.temp_project("1.3.1") as path, h.cwd(path):
            _, out = run(["agent-list"])
        line = next(line for line in out.splitlines() if "GDPR Compliance" in line)
        self.assertNotIn("installed here", line)

    def test_a_project_without_spectra_is_told_how_to_add_it(self):
        with h.serve_roster() as base, h.raw_base(base), \
             h.temp_project(installed_version=None) as path, h.cwd(path):
            _, out = run(["agent-list"])
        self.assertIn("spectra install", out)
        self.assertNotIn("installed here", out)

    def test_an_incomplete_install_is_not_reported_as_installed(self):
        with h.serve_roster() as base, h.raw_base(base), \
             h.temp_project(incomplete=True) as path, h.cwd(path):
            _, out = run(["agent-list"])
        self.assertNotIn("installed here", out)


class SchemaTolerance(unittest.TestCase):
    def test_a_newer_minor_schema_still_lists_everything_and_warns(self):
        data = h.roster(schema_version="1.9")
        with h.serve_roster(data) as base, h.raw_base(base), \
             h.temp_project(is_project=False) as path, h.cwd(path):
            code, out = run(["agent-list"])
        self.assertEqual(code, 0)
        self.assertIn("Guardrails", out)
        self.assertIn("newer than your Spectra CLI", out)
        self.assertIn("spectra cli update", out)

    def test_a_newer_major_schema_lists_nothing_and_names_the_remedy(self):
        data = h.roster(schema_version="2.0")
        with h.serve_roster(data) as base, h.raw_base(base), \
             h.temp_project(is_project=False) as path, h.cwd(path):
            code, out = run(["agent-list"])
        self.assertEqual(code, 3)
        self.assertNotIn("Guardrails", out)
        self.assertIn("spectra cli update", out)


class Failures(unittest.TestCase):
    def test_an_unreachable_roster_explains_itself_and_exits_three(self):
        with h.raw_base(h.UNREACHABLE_BASE), \
             h.temp_project(is_project=False) as path, h.cwd(path):
            code, out = run(["agent-list"])
        self.assertEqual(code, 3)
        self.assertIn("Could not read the published agent roster", out)

    def test_nothing_partial_is_printed_when_the_roster_cannot_be_read(self):
        """FR-041: never present an empty or stale list as authoritative."""
        with h.raw_base(h.UNREACHABLE_BASE), \
             h.temp_project(is_project=False) as path, h.cwd(path):
            _, out = run(["agent-list"])
        self.assertNotIn("agents ·", out)
        self.assertNotIn("Foundation", out)

    def test_a_malformed_roster_is_reported_as_not_understood(self):
        with h.serve({"agents-list.json": '{"schema_version": "1.0", "phases": []}'}) as base, \
             h.raw_base(base), h.temp_project(is_project=False) as path, h.cwd(path):
            code, out = run(["agent-list"])
        self.assertEqual(code, 3)
        self.assertIn("could not be understood", out)


if __name__ == "__main__":
    unittest.main()
