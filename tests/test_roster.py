"""Roster parsing: ordering, the schema gate, and every field rule.

The schema gate is the load-bearing part. Principle VI promises a new agent reaches every installed
CLI with no CLI release, so an additive change to the roster must never break an older reader — hence
newer-minor renders and only newer-major refuses.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import helpers as h  # noqa: E402
from spectra_cli import net, roster  # noqa: E402


class Ordering(unittest.TestCase):
    def test_phase_order_follows_the_roster_not_the_alphabet(self):
        parsed = roster.parse(h.roster())
        self.assertEqual([p.id for p in parsed.phases],
                         ["foundation", "requirements-discovery", "deployment-operations"])

    def test_agents_keep_roster_order_within_a_phase(self):
        parsed = roster.parse(h.roster())
        grouped = dict((phase.id, [a.id for a in agents]) for phase, agents in parsed.grouped())
        self.assertEqual(grouped["foundation"], ["constitution", "domain-analyzer"])
        self.assertEqual(grouped["requirements-discovery"], ["brd", "gdpr"])

    def test_grouped_skips_phases_with_no_agents(self):
        data = h.roster()
        data["phases"].append({"id": "empty", "title": "Empty", "aidlc": "Operation"})
        parsed = roster.parse(data)
        self.assertNotIn("empty", [phase.id for phase, _ in parsed.grouped()])

    def test_grouping_is_stable_across_calls(self):
        parsed = roster.parse(h.roster())
        self.assertEqual([(p.id, [a.id for a in ag]) for p, ag in parsed.grouped()],
                         [(p.id, [a.id for a in ag]) for p, ag in parsed.grouped()])


class Derived(unittest.TestCase):
    def test_shipped_is_spectra_and_available_only(self):
        parsed = roster.parse(h.roster())
        self.assertEqual([a.id for a in parsed.shipped()], ["domain-analyzer", "brd", "create-pr"])

    def test_speckit_agents_are_not_shipped_by_spectra(self):
        parsed = roster.parse(h.roster())
        self.assertFalse(parsed.by_id("constitution").shipped)

    def test_planned_spectra_agents_are_not_shipped(self):
        parsed = roster.parse(h.roster())
        self.assertFalse(parsed.by_id("gdpr").shipped)

    def test_by_id_returns_none_for_an_unknown_agent(self):
        self.assertIsNone(roster.parse(h.roster()).by_id("no-such-agent"))


class SchemaGate(unittest.TestCase):
    def test_the_current_schema_parses_without_a_notice(self):
        parsed = roster.parse(h.roster(schema_version="1.0"))
        self.assertFalse(parsed.newer_minor)

    def test_a_newer_minor_parses_and_flags_itself(self):
        parsed = roster.parse(h.roster(schema_version="1.7"))
        self.assertTrue(parsed.newer_minor)
        self.assertEqual(len(parsed.agents), 5, "a newer minor must still render every agent")

    def test_a_newer_major_is_refused_and_names_the_remedy(self):
        with self.assertRaises(roster.RosterError) as caught:
            roster.parse(h.roster(schema_version="2.0"))
        message = str(caught.exception)
        self.assertIn("newer Spectra CLI", message)
        self.assertIn("spectra cli update", message)

    def test_unknown_fields_are_ignored_when_reading_published_data(self):
        data = h.roster()
        h.agent(data, "brd")["some_future_field"] = "ignored"
        self.assertEqual(roster.parse(data, strict=False).by_id("brd").title, "BRD Generator")

    def test_unknown_fields_are_rejected_when_loading_the_committed_roster(self):
        data = h.roster()
        h.agent(data, "brd")["typoed_field"] = "x"
        with self.assertRaises(roster.RosterError) as caught:
            roster.parse(data, strict=True)
        self.assertIn("typoed_field", str(caught.exception))

    def test_a_missing_schema_version_is_refused(self):
        data = h.roster()
        del data["schema_version"]
        with self.assertRaises(roster.RosterError):
            roster.parse(data)

    def test_an_unreadable_schema_version_is_refused(self):
        with self.assertRaises(roster.RosterError):
            roster.parse(h.roster(schema_version="not.a.version"))


class FieldRules(unittest.TestCase):
    def _rejects(self, mutate, expected_fragment):
        data = h.roster()
        mutate(data)
        with self.assertRaises(roster.RosterError) as caught:
            roster.parse(data)
        self.assertIn(expected_fragment, str(caught.exception))

    def test_an_available_agent_must_record_a_command(self):
        self._rejects(lambda d: h.agent(d, "brd").pop("command"), "records no command")

    def test_a_planned_agent_must_not_record_a_command(self):
        self._rejects(lambda d: h.agent(d, "gdpr").update(command="speckit.spectra.gdpr"),
                      "records a command")

    def test_descriptions_must_be_a_single_line(self):
        self._rejects(lambda d: h.agent(d, "brd").update(description="two\nlines"), "single-line")

    def test_descriptions_must_not_be_blank(self):
        self._rejects(lambda d: h.agent(d, "brd").update(description="   "), "brd")

    def test_ids_must_be_lowercase_slugs(self):
        self._rejects(lambda d: h.agent(d, "brd").update(id="Not_A_Slug"), "lowercase slug")

    def test_ids_must_be_unique(self):
        self._rejects(lambda d: d["agents"].append(dict(h.agent(d, "brd"))), "appears twice")

    def test_phase_must_resolve(self):
        self._rejects(lambda d: h.agent(d, "brd").update(phase="nowhere"), "unknown phase")

    def test_status_must_be_in_range(self):
        self._rejects(lambda d: h.agent(d, "brd").update(status="maybe"), "status")

    def test_type_must_be_in_range(self):
        self._rejects(lambda d: h.agent(d, "brd").update(type="middleware"), "type")

    def test_provider_must_be_in_range(self):
        self._rejects(lambda d: h.agent(d, "brd").update(provider="someone-else"), "provider")

    def test_a_roster_with_no_agents_is_refused(self):
        self._rejects(lambda d: d.update(agents=[]), "no agents")

    def test_a_roster_with_no_phases_is_refused(self):
        self._rejects(lambda d: d.update(phases=[]), "no phases")

    def test_a_non_object_roster_is_refused(self):
        with self.assertRaises(roster.RosterError):
            roster.parse(["not", "a", "roster"])


class Loading(unittest.TestCase):
    def test_load_reads_a_local_file(self):
        parsed = roster.load(h.repo_file("agents-list.json"))
        self.assertGreater(len(parsed.agents), 0)

    def test_load_reports_a_missing_file_rather_than_raising_oserror(self):
        with self.assertRaises(roster.RosterError) as caught:
            roster.load("/definitely/not/here/agents-list.json")
        self.assertIn("could not read", str(caught.exception))

    def test_load_reports_invalid_json(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "agents-list.json"
            path.write_text("{oops", encoding="utf-8")
            with self.assertRaises(roster.RosterError) as caught:
                roster.load(path)
        self.assertIn("not valid JSON", str(caught.exception))

    def test_fetch_reads_the_published_roster(self):
        with h.serve_roster() as base, h.raw_base(base):
            self.assertEqual(len(roster.fetch().agents), 5)

    def test_fetch_lets_a_network_failure_through_as_a_fetch_error(self):
        """Unreachable and unparseable are different problems and get different messages."""
        with h.raw_base(h.UNREACHABLE_BASE):
            with self.assertRaises(net.FetchError):
                roster.fetch()

    def test_fetch_raises_a_roster_error_for_a_document_it_cannot_understand(self):
        with h.serve({"agents-list.json": '{"schema_version": "1.0"}'}) as base, h.raw_base(base):
            with self.assertRaises(roster.RosterError):
                roster.fetch()


if __name__ == "__main__":
    unittest.main()
