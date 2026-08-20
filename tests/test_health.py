"""The stack health check: parsing, reading, comparing, and the ordered update walk.

Split from `test_version_update.py` because the module under test is worth exercising directly. The
`specify self check` parser and the update walk are the two places this feature can go quietly wrong,
and both are reachable here without argparse, a prompt, or a terminal.
"""

from __future__ import annotations

import unittest
from unittest import mock

from spectra_cli import extension, health, project, version as cli_version
from tests import helpers


def _status(key, status, installed=None, latest=None, detail=None):
    return health.ComponentStatus(key, status, installed=installed, latest=latest, detail=detail)


class _Completed:
    """A stand-in for `subprocess.CompletedProcess`, so the probe's failure paths are reachable."""

    def __init__(self, stdout="", returncode=0):
        self.stdout = stdout
        self.stderr = ""
        self.returncode = returncode


def _completed(stdout="", code=0):
    return _Completed(stdout, code)


# --------------------------------------------------------------------------- #
# The `specify self check` parser
# --------------------------------------------------------------------------- #

class SelfCheckParsing(unittest.TestCase):
    """Every branch `specify self check` can print, against its literal output.

    The fixtures are copied from Spec Kit's source rather than derived from the parser, because a
    fixture generated from the thing under test would prove nothing about the real command.
    """

    def test_up_to_date_reports_the_installed_version_as_both(self):
        result = health.parse_self_check(helpers.SELF_CHECK_UP_TO_DATE)
        self.assertEqual(result["status"], health.UP_TO_DATE)
        self.assertEqual(result["installed"], "0.16.4")
        self.assertEqual(result["latest"], "0.16.4")

    def test_an_available_update_splits_on_the_unicode_arrow(self):
        result = health.parse_self_check(helpers.SELF_CHECK_UPDATE_AVAILABLE)
        self.assertEqual(result["status"], health.NEEDS_UPDATING)
        self.assertEqual(result["installed"], "0.16.4")
        self.assertEqual(result["latest"], "v0.16.5")

    def test_an_ascii_arrow_is_not_mistaken_for_the_real_separator(self):
        # Spec Kit prints U+2192. If it ever printed `->` we would want to notice, not guess.
        result = health.parse_self_check("Update available: 0.16.4 -> v0.16.5\n")
        self.assertEqual(result["status"], health.UNKNOWN)

    def test_an_unreachable_release_check_is_unknown_but_keeps_the_local_version(self):
        result = health.parse_self_check(helpers.SELF_CHECK_FETCH_FAILED)
        self.assertEqual(result["status"], health.UNKNOWN)
        self.assertEqual(result["installed"], "0.16.4")
        self.assertIsNone(result["latest"])
        self.assertIn("network unreachable", result["detail"])

    def test_an_unvalidatable_tag_is_unknown_but_keeps_the_local_version(self):
        result = health.parse_self_check(helpers.SELF_CHECK_TAG_INVALID)
        self.assertEqual(result["status"], health.UNKNOWN)
        self.assertEqual(result["installed"], "0.16.4")
        self.assertIsNone(result["latest"])

    def test_an_undeterminable_local_version_is_unknown(self):
        result = health.parse_self_check(helpers.SELF_CHECK_NO_LOCAL_VERSION)
        self.assertEqual(result["status"], health.UNKNOWN)
        self.assertIsNone(result["installed"])
        self.assertEqual(result["latest"], "v0.16.5")

    def test_unrecognized_output_is_unknown_and_quotes_what_arrived(self):
        result = health.parse_self_check(helpers.SELF_CHECK_GIBBERISH)
        self.assertEqual(result["status"], health.UNKNOWN)
        self.assertIn("something entirely unexpected", result["detail"])

    def test_empty_output_is_unknown_rather_than_a_crash(self):
        for text in ("", "\n", None):
            with self.subTest(text=text):
                self.assertEqual(health.parse_self_check(text)["status"], health.UNKNOWN)

    def test_a_wrapped_failure_reason_does_not_become_a_verdict(self):
        # Rich wraps to 80 columns when piped; a continuation line must stay part of the reason.
        wrapped = ("Installed: 0.16.4\n"
                   "Could not check latest release: the proxy refused the connection after\n"
                   "several attempts\n")
        result = health.parse_self_check(wrapped)
        self.assertEqual(result["status"], health.UNKNOWN)
        self.assertEqual(result["installed"], "0.16.4")

    def test_no_branch_depends_on_an_exit_code(self):
        # The real command exits 0 on every path, so a stub that also exits 0 must still be classified
        # correctly from its text alone.
        cases = {
            helpers.SELF_CHECK_UP_TO_DATE: health.UP_TO_DATE,
            helpers.SELF_CHECK_UPDATE_AVAILABLE: health.NEEDS_UPDATING,
            helpers.SELF_CHECK_FETCH_FAILED: health.UNKNOWN,
        }
        for output, expected in cases.items():
            with self.subTest(expected=expected):
                with helpers.fake_specify(output, exit_code=0):
                    self.assertEqual(health.get_specify_cli_status().status, expected)


class SpecifyAbsent(unittest.TestCase):
    """`specify` off PATH degrades two components and leaves the other two alone."""

    def test_the_specify_cli_is_unknown_and_says_why(self):
        with helpers.without_specify():
            status = health.get_specify_cli_status()
        self.assertEqual(status.status, health.UNKNOWN)
        self.assertIn("not on PATH", status.detail)

    def test_it_never_raises(self):
        with helpers.without_specify():
            health.get_specify_cli_status()  # must not raise

    def test_the_other_two_components_still_resolve(self):
        with helpers.temp_project("1.3.1") as path, helpers.cwd(path):
            state = project.classify()
            with helpers.without_specify():
                report = health.check_all(state, skip_network=True)
        self.assertEqual(report.get(health.SPECIFY_CLI).status, health.UNKNOWN)
        self.assertEqual(report.get(health.INTEGRATION).status, health.UNKNOWN)
        # The Spectra CLI row still knows what is installed locally even with the check skipped.
        self.assertIsNotNone(report.get(health.SPECTRA_CLI).installed)


# --------------------------------------------------------------------------- #
# The integration file
# --------------------------------------------------------------------------- #

class IntegrationVersion(unittest.TestCase):
    """Every way `.specify/integration.json` can fail to yield a version is the same answer: None."""

    def test_a_well_formed_file_yields_its_version(self):
        with helpers.temp_project("1.3.1", integration_version="0.16.4") as path:
            root = project.find_project_root(path)
            self.assertEqual(health.read_integration_version(root), "0.16.4")

    def test_a_missing_file_yields_none(self):
        with helpers.temp_project("1.3.1") as path:
            root = project.find_project_root(path)
            self.assertIsNone(health.read_integration_version(root))

    def test_malformed_json_yields_none(self):
        with helpers.temp_project("1.3.1", integration_version=helpers.BAD_JSON) as path:
            root = project.find_project_root(path)
            self.assertIsNone(health.read_integration_version(root))

    def test_a_missing_version_key_yields_none(self):
        with helpers.temp_project("1.3.1", integration_version=helpers.NO_VERSION) as path:
            root = project.find_project_root(path)
            self.assertIsNone(health.read_integration_version(root))

    def test_an_empty_version_yields_none(self):
        with helpers.temp_project("1.3.1", integration_version="   ") as path:
            root = project.find_project_root(path)
            self.assertIsNone(health.read_integration_version(root))

    def test_no_project_root_yields_none(self):
        self.assertIsNone(health.read_integration_version(None))


class ModificationReportReading(unittest.TestCase):
    """What the probe reports, and what it does when it cannot report at all."""

    def test_the_shared_record_is_routed_to_shared_not_to_an_integration(self):
        with helpers.temp_project("1.3.1", integration_version="0.16.5",
                                  integrations={"claude": "0.16.5"}) as path:
            with helpers.fake_specify(installed=("claude",),
                                      modified={"claude": [".claude/x.md"],
                                                "speckit": [".specify/templates/spec-template.md"]}):
                with helpers.cwd(path):
                    report = health.modification_report(project.find_project_root(path))
        self.assertTrue(report.established)
        self.assertEqual(report.files_for("claude"), [".claude/x.md"])
        self.assertEqual(report.shared, [".specify/templates/spec-template.md"])
        self.assertNotIn(health.SHARED_KEY, report.per_integration)

    def test_keys_that_are_not_installed_integrations_are_ignored(self):
        with helpers.temp_project("1.3.1", integration_version="0.16.5",
                                  integrations={"claude": "0.16.5"}) as path:
            with helpers.fake_specify(installed=("claude", "gemini"),
                                      modified={"gemini": [".gemini/x.md"]}):
                with helpers.cwd(path):
                    report = health.modification_report(project.find_project_root(path))
        self.assertEqual(report.files_for("gemini"), [])

    def test_a_clean_project_is_established_and_empty(self):
        with helpers.temp_project("1.3.1", integration_version="0.16.5",
                                  integrations={"claude": "0.16.5"}) as path:
            with helpers.fake_specify(installed=("claude",)):
                with helpers.cwd(path):
                    report = health.modification_report(project.find_project_root(path))
        self.assertTrue(report.established)
        self.assertEqual(report.per_integration, {})
        self.assertEqual(report.shared, [])

    def test_only_json_output_is_ever_read(self):
        """FR-041: the human-formatted table is never parsed."""
        argv = []
        with mock.patch.object(health, "specify_available", return_value=True), \
             mock.patch("subprocess.run",
                        side_effect=lambda a, **k: argv.append(a) or _completed("{}")):
            health.modification_report(None)
        self.assertEqual(argv, [["specify", "integration", "status", "--json"]])

    def test_an_absent_specify_is_not_established(self):
        with helpers.without_specify():
            report = health.modification_report(None)
        self.assertFalse(report.established)
        self.assertEqual(report.per_integration, {})
        self.assertEqual(report.shared, [])

    def test_a_timeout_is_not_established(self):
        import subprocess as sp
        with mock.patch.object(health, "specify_available", return_value=True), \
             mock.patch("subprocess.run", side_effect=sp.TimeoutExpired("specify", 5)):
            report = health.modification_report(None)
        self.assertFalse(report.established)

    def test_a_non_zero_exit_is_not_established(self):
        with mock.patch.object(health, "specify_available", return_value=True), \
             mock.patch("subprocess.run", return_value=_completed("", code=1)):
            report = health.modification_report(None)
        self.assertFalse(report.established)

    def test_unparseable_output_is_not_established(self):
        with mock.patch.object(health, "specify_available", return_value=True), \
             mock.patch("subprocess.run", return_value=_completed("not json at all")):
            report = health.modification_report(None)
        self.assertFalse(report.established)

    def test_an_os_error_is_not_established(self):
        with mock.patch.object(health, "specify_available", return_value=True), \
             mock.patch("subprocess.run", side_effect=OSError("boom")):
            report = health.modification_report(None)
        self.assertFalse(report.established)


class InstalledIntegrations(unittest.TestCase):
    """Membership comes from the recorded list, and never from what happens to be on disk."""

    def _read(self, path):
        return health.read_installed_integrations(project.find_project_root(path))

    def test_a_recorded_list_is_returned_in_order(self):
        with helpers.temp_project("1.3.1", integration_version="0.16.5",
                                  integrations={"kiro-cli": "0.16.5", "claude": "0.16.5"}) as path:
            self.assertEqual(self._read(path), ["kiro-cli", "claude"])

    def test_the_shared_infrastructure_record_is_not_an_integration(self):
        # `speckit.manifest.json` sits in the same directory as the integration manifests but is shared
        # infrastructure. A reader that enumerated the directory would find three; the recorded list has
        # two, and the recorded list is the truth (FR-002).
        with helpers.temp_project("1.3.1", integration_version="0.16.5",
                                  integrations={"kiro-cli": "0.16.5", "claude": "0.16.5"}) as path:
            root = project.find_project_root(path)
            on_disk = sorted(p.name for p in (root / ".specify" / "integrations").iterdir())
            self.assertIn("speckit.manifest.json", on_disk)
            self.assertNotIn("speckit", self._read(path))

    def test_a_missing_file_yields_none_meaning_fall_back(self):
        with helpers.temp_project("1.3.1") as path:
            self.assertIsNone(self._read(path))

    def test_malformed_json_yields_none(self):
        with helpers.temp_project("1.3.1", integration_version=helpers.BAD_JSON) as path:
            self.assertIsNone(self._read(path))

    def test_a_file_without_the_key_yields_none(self):
        with helpers.temp_project("1.3.1", integration_version=helpers.NO_VERSION) as path:
            self.assertIsNone(self._read(path))

    def test_an_empty_list_yields_none(self):
        with helpers.temp_project("1.3.1", integration_version="0.16.5") as path:
            root = project.find_project_root(path)
            (root / ".specify" / "integration.json").write_text(
                '{"version": "0.16.5", "installed_integrations": []}', encoding="utf-8")
            self.assertIsNone(health.read_installed_integrations(root))

    def test_no_project_root_yields_none(self):
        self.assertIsNone(health.read_installed_integrations(None))

    def test_the_default_integration_is_read_from_either_key(self):
        with helpers.temp_project("1.3.1", integration_version="0.16.5",
                                  integrations={"kiro-cli": "0.16.5", "claude": "0.16.5"},
                                  default_integration="claude") as path:
            root = project.find_project_root(path)
            self.assertEqual(health.read_default_integration(root), "claude")

    def test_an_absent_default_is_none_rather_than_invented(self):
        with helpers.temp_project("1.3.1", integration_version="0.16.5") as path:
            root = project.find_project_root(path)
            (root / ".specify" / "integration.json").write_text(
                '{"version": "0.16.5", "installed_integrations": ["claude"]}', encoding="utf-8")
            self.assertIsNone(health.read_default_integration(root))


class PerIntegrationVersion(unittest.TestCase):
    """Every way one integration's manifest can fail to yield a version is the same answer: None."""

    def _read(self, path, key):
        return health.read_integration_version(project.find_project_root(path), key)

    def test_a_well_formed_manifest_yields_its_version(self):
        with helpers.temp_project("1.3.1", integration_version="0.16.5",
                                  integrations={"kiro-cli": "0.16.5", "claude": "0.15.1"}) as path:
            self.assertEqual(self._read(path, "kiro-cli"), "0.16.5")
            self.assertEqual(self._read(path, "claude"), "0.15.1")

    def test_a_missing_manifest_yields_none(self):
        with helpers.temp_project("1.3.1", integration_version="0.16.5",
                                  integrations={"kiro-cli": "0.16.5",
                                                "claude": helpers.MISSING_MANIFEST}) as path:
            self.assertIsNone(self._read(path, "claude"))

    def test_malformed_json_yields_none(self):
        with helpers.temp_project("1.3.1", integration_version="0.16.5",
                                  integrations={"claude": "0.16.5"}) as path:
            root = project.find_project_root(path)
            (root / ".specify" / "integrations" / "claude.manifest.json").write_text(
                "{ not json", encoding="utf-8")
            self.assertIsNone(health.read_integration_version(root, "claude"))

    def test_a_non_object_top_level_yields_none(self):
        with helpers.temp_project("1.3.1", integration_version="0.16.5",
                                  integrations={"claude": "0.16.5"}) as path:
            root = project.find_project_root(path)
            (root / ".specify" / "integrations" / "claude.manifest.json").write_text(
                '["not", "an", "object"]', encoding="utf-8")
            self.assertIsNone(health.read_integration_version(root, "claude"))

    def test_an_absent_or_empty_version_yields_none(self):
        with helpers.temp_project("1.3.1", integration_version="0.16.5",
                                  integrations={"claude": "0.16.5"}) as path:
            root = project.find_project_root(path)
            manifest = root / ".specify" / "integrations" / "claude.manifest.json"
            manifest.write_text('{"integration": "claude"}', encoding="utf-8")
            self.assertIsNone(health.read_integration_version(root, "claude"))
            manifest.write_text('{"integration": "claude", "version": "  "}', encoding="utf-8")
            self.assertIsNone(health.read_integration_version(root, "claude"))


class PerIntegrationVerdict(unittest.TestCase):
    """The per-integration state table, evaluated once per key instead of once per project."""

    CURRENT = None  # set in setUp; a Specify CLI that is current at 0.16.5

    def setUp(self):
        self.CURRENT = _status(health.SPECIFY_CLI, health.UP_TO_DATE,
                               installed="0.16.5", latest="0.16.5")
        self.BEHIND = _status(health.SPECIFY_CLI, health.NEEDS_UPDATING,
                              installed="0.16.4", latest="0.16.5")
        self.UNKNOWN = _status(health.SPECIFY_CLI, health.UNKNOWN, detail="no specify")

    def _states(self, integrations, specify_status, default=None):
        with helpers.temp_project("1.3.1", integration_version="0.16.5",
                                  integrations=integrations,
                                  default_integration=default) as path:
            root = project.find_project_root(path)
            return {s.key: s for s in health.get_integration_states(root, specify_status)}

    def test_an_unknown_specify_cli_forces_every_integration_unknown(self):
        states = self._states({"kiro-cli": "0.16.5", "claude": "0.15.1"}, self.UNKNOWN)
        self.assertEqual({s.status for s in states.values()}, {health.UNKNOWN})
        for state in states.values():
            self.assertIn("nothing to compare against", state.detail)

    def test_every_unknown_carries_a_reason(self):
        states = self._states({"kiro-cli": "0.16.5", "claude": helpers.MISSING_MANIFEST},
                              self.CURRENT)
        self.assertEqual(states["claude"].status, health.UNKNOWN)
        self.assertTrue(states["claude"].detail)

    def test_a_behind_cli_makes_every_integration_behind_and_targets_its_latest(self):
        states = self._states({"kiro-cli": "0.16.4", "claude": "0.16.4"}, self.BEHIND)
        for state in states.values():
            self.assertEqual(state.status, health.NEEDS_UPDATING)
            self.assertEqual(state.latest, "0.16.5")
            self.assertIn("tracks it", state.detail)

    def test_a_stale_manifest_against_a_current_cli_needs_updating(self):
        states = self._states({"kiro-cli": "0.16.5", "claude": "0.15.1"}, self.CURRENT)
        self.assertEqual(states["kiro-cli"].status, health.UP_TO_DATE)
        self.assertEqual(states["claude"].status, health.NEEDS_UPDATING)
        self.assertEqual(states["claude"].latest, "0.16.5")
        # The two ways of being behind are distinguishable by their reason.
        self.assertIn("was upgraded but", states["claude"].detail)

    def test_a_newer_manifest_is_ahead(self):
        states = self._states({"claude": "0.17.0"}, self.CURRENT)
        self.assertEqual(states["claude"].status, health.AHEAD)

    def test_the_default_integration_is_marked(self):
        states = self._states({"kiro-cli": "0.16.5", "claude": "0.16.5"}, self.CURRENT,
                              default="claude")
        self.assertTrue(states["claude"].is_default)
        self.assertFalse(states["kiro-cli"].is_default)

    def test_modified_is_unset_until_the_update_path_asks(self):
        states = self._states({"claude": "0.16.5"}, self.CURRENT)
        self.assertIsNone(states["claude"].modified)


class Aggregation(unittest.TestCase):
    """One row from many integrations: the five precedence rules, in order."""

    CURRENT = _status(health.SPECIFY_CLI, health.UP_TO_DATE, installed="0.16.5", latest="0.16.5")

    def _row(self, *states):
        return health.aggregate_integration_status(list(states), self.CURRENT)

    def _state(self, key, status, installed=None):
        return health.IntegrationState(key, status, installed=installed,
                                       detail="reason" if status == health.UNKNOWN else None)

    def test_rule_1_no_integrations_is_unknown(self):
        row = self._row()
        self.assertEqual(row.status, health.UNKNOWN)
        self.assertIn("no installed integrations", row.detail)

    def test_rule_2_any_behind_makes_the_row_behind(self):
        row = self._row(self._state("a", health.UP_TO_DATE, "0.16.5"),
                        self._state("b", health.NEEDS_UPDATING, "0.15.1"))
        self.assertEqual(row.status, health.NEEDS_UPDATING)

    def test_rule_2_outranks_rule_3_so_an_unreadable_sibling_cannot_hide_work(self):
        row = self._row(self._state("a", health.UNKNOWN),
                        self._state("b", health.NEEDS_UPDATING, "0.15.1"))
        self.assertEqual(row.status, health.NEEDS_UPDATING)

    def test_rule_3_any_unknown_outranks_a_claim_of_currency(self):
        row = self._row(self._state("a", health.UP_TO_DATE, "0.16.5"),
                        self._state("b", health.UNKNOWN))
        self.assertEqual(row.status, health.UNKNOWN)
        self.assertIn("b", row.detail)

    def test_rule_3_covers_every_integration_being_unknown(self):
        row = self._row(self._state("a", health.UNKNOWN), self._state("b", health.UNKNOWN))
        self.assertEqual(row.status, health.UNKNOWN)

    def test_rule_4_ahead_only_when_every_integration_is_ahead(self):
        row = self._row(self._state("a", health.AHEAD, "0.17.0"),
                        self._state("b", health.AHEAD, "0.17.0"))
        self.assertEqual(row.status, health.AHEAD)

    def test_rule_5_a_mix_of_ahead_and_current_is_up_to_date(self):
        # "Ahead" is a flavour of not-behind, and the row answers "is anything stale here?".
        row = self._row(self._state("a", health.AHEAD, "0.17.0"),
                        self._state("b", health.UP_TO_DATE, "0.16.5"))
        self.assertEqual(row.status, health.UP_TO_DATE)

    def test_rule_5_all_current_is_up_to_date(self):
        row = self._row(self._state("a", health.UP_TO_DATE, "0.16.5"),
                        self._state("b", health.UP_TO_DATE, "0.16.5"))
        self.assertEqual(row.status, health.UP_TO_DATE)

    def test_the_children_are_carried_on_the_row(self):
        row = self._row(self._state("a", health.UP_TO_DATE, "0.16.5"),
                        self._state("b", health.NEEDS_UPDATING, "0.15.1"))
        self.assertEqual([part.key for part in row.parts], ["a", "b"])
        self.assertTrue(row.has_parts)


class DerivedRowFields(unittest.TestCase):
    """The row's version and reason are derived from its children, never set independently."""

    CURRENT = _status(health.SPECIFY_CLI, health.UP_TO_DATE, installed="0.16.5", latest="0.16.5")

    def _row(self, *states):
        return health.aggregate_integration_status(list(states), self.CURRENT)

    def test_the_row_shows_the_oldest_readable_version(self):
        row = self._row(health.IntegrationState("a", health.UP_TO_DATE, installed="0.16.5"),
                        health.IntegrationState("b", health.NEEDS_UPDATING, installed="0.15.1",
                                                latest="0.16.5"))
        self.assertEqual(row.installed, "0.15.1")

    def test_an_unreadable_child_contributes_no_version_to_the_comparison(self):
        row = self._row(health.IntegrationState("a", health.UP_TO_DATE, installed="0.16.5"),
                        health.IntegrationState("b", health.UNKNOWN, detail="unreadable"))
        self.assertEqual(row.installed, "0.16.5")

    def test_the_row_names_the_behind_integrations(self):
        row = self._row(health.IntegrationState("kiro-cli", health.UP_TO_DATE, installed="0.16.5"),
                        health.IntegrationState("claude", health.NEEDS_UPDATING, installed="0.15.1",
                                                latest="0.16.5"))
        self.assertIn("claude", row.detail)
        self.assertNotIn("kiro-cli", row.detail)

    def test_the_row_targets_what_the_behind_children_target(self):
        row = self._row(health.IntegrationState("claude", health.NEEDS_UPDATING, installed="0.15.1",
                                                latest="0.16.5"))
        self.assertEqual(row.latest, "0.16.5")


class RecordPrecedence(unittest.TestCase):
    """The regression this feature exists for.

    Spec Kit rewrites the project-level `version` in `.specify/integration.json` to the current CLI
    version whenever **any** integration is upgraded (BRD-006 finding F2). So after upgrading one of two,
    that field reads current while the other integration's own manifest is still stale. A check that
    reads the project-level field first reports a green row over a stale stack — which is the bug.
    """

    CURRENT = _status(health.SPECIFY_CLI, health.UP_TO_DATE, installed="0.16.5", latest="0.16.5")

    def test_a_current_project_record_cannot_mask_a_stale_manifest(self):
        with helpers.temp_project("1.3.1", integration_version="0.16.5",
                                  integrations={"kiro-cli": "0.16.5", "claude": "0.15.1"},
                                  default_integration="kiro-cli") as path:
            root = project.find_project_root(path)
            # The project-level field says everything is current...
            self.assertEqual(health.read_integration_version(root), "0.16.5")
            # ...but the row must not believe it.
            row = health.get_integration_status(root, self.CURRENT)
        self.assertEqual(row.status, health.NEEDS_UPDATING)
        self.assertEqual(row.installed, "0.15.1")
        self.assertIn("claude", row.detail)

    def test_the_project_level_field_is_not_consulted_while_manifests_read(self):
        with helpers.temp_project("1.3.1", integration_version="0.11.0",
                                  integrations={"kiro-cli": "0.16.5"}) as path:
            root = project.find_project_root(path)
            row = health.get_integration_status(root, self.CURRENT)
        # A wildly stale project-level field is irrelevant when the manifest is readable and current.
        self.assertEqual(row.status, health.UP_TO_DATE)
        self.assertEqual(row.installed, "0.16.5")


class Fallback(unittest.TestCase):
    """Older layouts keep working: one unnamed integration, judged by the project-level record."""

    CURRENT = _status(health.SPECIFY_CLI, health.UP_TO_DATE, installed="0.16.5", latest="0.16.5")

    def test_no_recorded_list_falls_back_to_the_project_level_record(self):
        with helpers.temp_project("1.3.1", integration_version="0.15.1") as path:
            root = project.find_project_root(path)
            row = health.get_integration_status(root, self.CURRENT)
        self.assertEqual(row.status, health.NEEDS_UPDATING)
        self.assertEqual(row.installed, "0.15.1")
        self.assertEqual([part.key for part in row.parts], [None])

    def test_a_recorded_list_whose_manifests_are_all_unreadable_falls_back(self):
        with helpers.temp_project("1.3.1", integration_version="0.15.1",
                                  integrations={"kiro-cli": helpers.MISSING_MANIFEST,
                                                "claude": helpers.MISSING_MANIFEST}) as path:
            root = project.find_project_root(path)
            row = health.get_integration_status(root, self.CURRENT)
        self.assertEqual(row.status, health.NEEDS_UPDATING)
        self.assertEqual(row.installed, "0.15.1")
        self.assertEqual([part.key for part in row.parts], [None])

    def test_the_fallback_verdicts_match_the_single_record_table(self):
        for recorded, expected in (("0.16.5", health.UP_TO_DATE),
                                   ("0.15.1", health.NEEDS_UPDATING),
                                   ("0.17.0", health.AHEAD)):
            with helpers.temp_project("1.3.1", integration_version=recorded) as path:
                root = project.find_project_root(path)
                self.assertEqual(health.get_integration_status(root, self.CURRENT).status, expected)

    def test_an_unreadable_project_record_with_no_list_is_unknown(self):
        with helpers.temp_project("1.3.1", integration_version=helpers.BAD_JSON) as path:
            root = project.find_project_root(path)
            row = health.get_integration_status(root, self.CURRENT)
        self.assertEqual(row.status, health.UNKNOWN)


class IntegrationStatus(unittest.TestCase):
    """The seven-row state table: the only verdict derived from two inputs."""

    def _status_for(self, integration_version, specify_status):
        with helpers.temp_project("1.3.1", integration_version=integration_version) as path:
            root = project.find_project_root(path)
            return health.get_integration_status(root, specify_status)

    def test_an_unknown_specify_cli_forces_an_unknown_integration(self):
        unknown = _status(health.SPECIFY_CLI, health.UNKNOWN, detail="no specify")
        status = self._status_for("0.16.4", unknown)
        self.assertEqual(status.status, health.UNKNOWN)
        self.assertIn("nothing to compare against", status.detail)

    def test_an_unknown_specify_cli_wins_even_over_an_unreadable_file(self):
        unknown = _status(health.SPECIFY_CLI, health.UNKNOWN, detail="no specify")
        status = self._status_for(helpers.BAD_JSON, unknown)
        self.assertEqual(status.status, health.UNKNOWN)

    def test_a_behind_specify_cli_makes_the_integration_behind_too(self):
        behind = _status(health.SPECIFY_CLI, health.NEEDS_UPDATING,
                         installed="0.16.4", latest="0.16.5")
        status = self._status_for("0.16.4", behind)
        self.assertEqual(status.status, health.NEEDS_UPDATING)

    def test_a_behind_cli_targets_the_clis_latest_not_its_installed(self):
        # The upgrade installs the newer CLI, and the integration follows it there, so the row must
        # read the transition that will actually happen.
        behind = _status(health.SPECIFY_CLI, health.NEEDS_UPDATING,
                         installed="0.16.4", latest="0.16.5")
        status = self._status_for("0.12.14", behind)
        self.assertEqual(status.installed, "0.12.14")
        self.assertEqual(status.latest, "0.16.5")

    def test_a_behind_cli_with_an_unreadable_file_is_unknown(self):
        behind = _status(health.SPECIFY_CLI, health.NEEDS_UPDATING,
                         installed="0.16.4", latest="0.16.5")
        self.assertEqual(self._status_for(helpers.BAD_JSON, behind).status, health.UNKNOWN)

    def test_a_matching_file_against_a_current_cli_is_up_to_date(self):
        current = _status(health.SPECIFY_CLI, health.UP_TO_DATE,
                          installed="0.16.4", latest="0.16.4")
        self.assertEqual(self._status_for("0.16.4", current).status, health.UP_TO_DATE)

    def test_an_older_file_against_a_current_cli_needs_updating(self):
        # The real state of this repository: CLI upgraded, integration never re-run.
        current = _status(health.SPECIFY_CLI, health.UP_TO_DATE,
                          installed="0.16.4", latest="0.16.4")
        status = self._status_for("0.12.14", current)
        self.assertEqual(status.status, health.NEEDS_UPDATING)
        self.assertIn("not re-run", status.detail)

    def test_a_newer_file_against_a_current_cli_is_ahead(self):
        current = _status(health.SPECIFY_CLI, health.UP_TO_DATE,
                          installed="0.16.4", latest="0.16.4")
        self.assertEqual(self._status_for("0.17.0", current).status, health.AHEAD)

    def test_a_current_cli_with_an_unreadable_file_is_unknown(self):
        current = _status(health.SPECIFY_CLI, health.UP_TO_DATE,
                          installed="0.16.4", latest="0.16.4")
        status = self._status_for(helpers.NO_VERSION, current)
        self.assertEqual(status.status, health.UNKNOWN)
        self.assertIn("integration.json", status.detail)


# --------------------------------------------------------------------------- #
# The whole stack
# --------------------------------------------------------------------------- #

class CheckAll(unittest.TestCase):
    def test_it_reports_exactly_four_components_in_canonical_order(self):
        with helpers.temp_project("1.3.1", integration_version="0.16.4") as path, \
                helpers.cwd(path), helpers.raw_base(helpers.UNREACHABLE_BASE):
            report = health.check_all(project.classify(), skip_network=True)
        self.assertEqual([c.key for c in report.components], list(health.ORDER))

    def test_canonical_order_is_the_update_order(self):
        # `outdated` is walked directly, so the ordering guarantee has to live in the list itself.
        self.assertEqual(health.ORDER,
                         (health.SPECIFY_CLI, health.INTEGRATION,
                          health.SPECTRA_CLI, health.SPECTRA_EXTENSION))

    def test_one_components_failure_does_not_suppress_the_others(self):
        with helpers.temp_project("1.3.1", integration_version=helpers.BAD_JSON) as path, \
                helpers.cwd(path), helpers.raw_base(helpers.UNREACHABLE_BASE):
            with helpers.without_specify():
                report = health.check_all(project.classify(), skip_network=True)
        self.assertEqual(len(report.components), 4)
        # Everything is unknown here, but every row is still present and explained.
        for component in report.components:
            self.assertEqual(component.status, health.UNKNOWN)
            self.assertTrue(component.detail, f"{component.key} has no explanation")

    def test_an_unknown_row_never_drops_out_of_the_report(self):
        with helpers.temp_project("1.3.1") as path, helpers.cwd(path), \
                helpers.raw_base(helpers.UNREACHABLE_BASE):
            report = health.check_all(project.classify(), skip_network=True)
        self.assertEqual(len(report.components), 4)

    def test_an_unreachable_published_version_keeps_the_installed_one(self):
        with helpers.temp_project("1.3.1") as path, helpers.cwd(path), \
                helpers.raw_base(helpers.UNREACHABLE_BASE):
            status = health.get_spectra_extension_status(project.classify())
        self.assertEqual(status.status, health.UNKNOWN)
        self.assertEqual(status.installed, "1.3.1")

    def test_an_incomplete_install_needs_updating_so_the_walk_can_repair_it(self):
        # Not UNKNOWN: what is unknown is the version, not the verdict. A half-written install
        # definitely needs fixing, and calling it unknown would make the walk skip the one component
        # it could actually repair.
        with helpers.temp_project(incomplete=True) as path, helpers.cwd(path), \
                helpers.raw_base(helpers.UNREACHABLE_BASE):
            status = health.get_spectra_extension_status(project.classify())
        self.assertEqual(status.status, health.NEEDS_UPDATING)
        self.assertIsNone(status.installed)
        self.assertIn("no readable version", status.detail)

    def test_skipping_the_network_reports_the_local_version_and_says_why(self):
        status = health.get_spectra_cli_status(skip_network=True)
        self.assertEqual(status.status, health.UNKNOWN)
        self.assertIsNotNone(status.installed)
        self.assertIn("no-update-check", status.detail)


class ReportProperties(unittest.TestCase):
    def test_outdated_preserves_canonical_order(self):
        report = health.HealthReport([
            _status(health.SPECIFY_CLI, health.NEEDS_UPDATING, "1", "2"),
            _status(health.INTEGRATION, health.UP_TO_DATE, "1", "1"),
            _status(health.SPECTRA_CLI, health.NEEDS_UPDATING, "1", "2"),
            _status(health.SPECTRA_EXTENSION, health.UNKNOWN, detail="x"),
        ])
        self.assertEqual([c.key for c in report.outdated],
                         [health.SPECIFY_CLI, health.SPECTRA_CLI])
        self.assertTrue(report.needs_update)

    def test_all_unknown_distinguishes_nothing_checkable_from_all_current(self):
        every_current = health.HealthReport(
            [_status(k, health.UP_TO_DATE, "1", "1") for k in health.ORDER])
        nothing_known = health.HealthReport(
            [_status(k, health.UNKNOWN, detail="x") for k in health.ORDER])
        self.assertFalse(every_current.needs_update)
        self.assertFalse(nothing_known.needs_update)
        # Same `needs_update`, opposite situations — which is exactly why the flag exists.
        self.assertFalse(every_current.all_unknown)
        self.assertTrue(nothing_known.all_unknown)

    def test_a_partially_known_report_is_not_all_unknown(self):
        mixed = health.HealthReport([
            _status(health.SPECIFY_CLI, health.UP_TO_DATE, "1", "1"),
            _status(health.INTEGRATION, health.UNKNOWN, detail="x"),
            _status(health.SPECTRA_CLI, health.UP_TO_DATE, "1", "1"),
            _status(health.SPECTRA_EXTENSION, health.UNKNOWN, detail="x"),
        ])
        self.assertFalse(mixed.all_unknown)
        self.assertEqual(len(mixed.unknown), 2)


# --------------------------------------------------------------------------- #
# UpdateResult
# --------------------------------------------------------------------------- #

class Results(unittest.TestCase):
    def test_the_outcome_vocabulary_is_three_values(self):
        self.assertEqual({health.UPDATED, health.FAILED, health.SKIPPED},
                         {"updated", "failed", "skipped"})

    def test_a_failure_always_carries_an_actionable_detail(self):
        results = _walk_with(
            {health.SPECTRA_EXTENSION: lambda component, assume_yes=False: 7},
            outdated=[health.SPECTRA_EXTENSION])
        failure = [r for r in results if r.failed][0]
        self.assertTrue(failure.detail)
        self.assertIn("7", failure.detail)

    def test_a_result_carries_its_display_label(self):
        self.assertEqual(health.UpdateResult(health.SPECIFY_CLI, health.UPDATED).label,
                         "Specify CLI")


# --------------------------------------------------------------------------- #
# The ordered update walk
# --------------------------------------------------------------------------- #

def _report_where(outdated):
    """A four-component report whose `outdated` set is exactly `outdated`."""
    components = []
    for key in health.ORDER:
        if key in outdated:
            components.append(_status(key, health.NEEDS_UPDATING, "1.0.0", "2.0.0"))
        else:
            components.append(_status(key, health.UP_TO_DATE, "1.0.0", "1.0.0"))
    return health.HealthReport(components)


def _walk_with(actions, outdated, report=None):
    """Run `apply_updates` with `_ACTIONS` replaced by `actions`, recording nothing else."""
    original = dict(health._ACTIONS)
    for key in health.ORDER:
        health._ACTIONS[key] = actions.get(key, lambda component, assume_yes=False: 0)
    try:
        return health.apply_updates(report or _report_where(outdated))
    finally:
        health._ACTIONS.clear()
        health._ACTIONS.update(original)


class TheWalkOrder(unittest.TestCase):
    def test_all_four_run_in_canonical_order(self):
        calls = []

        def record(key):
            return lambda component, assume_yes=False: calls.append(key) or 0

        _walk_with({k: record(k) for k in health.ORDER}, outdated=set(health.ORDER))
        self.assertEqual(calls, list(health.ORDER))

    def test_a_subset_preserves_its_relative_order(self):
        calls = []

        def record(key):
            return lambda component, assume_yes=False: calls.append(key) or 0

        subset = {health.SPECTRA_CLI, health.SPECTRA_EXTENSION}
        _walk_with({k: record(k) for k in health.ORDER}, outdated=subset)
        self.assertEqual(calls, [health.SPECTRA_CLI, health.SPECTRA_EXTENSION])

    def test_order_holds_even_when_an_earlier_component_fails(self):
        calls = []

        def record(key, code=0):
            def action(component, assume_yes=False):
                calls.append(key)
                return code
            return action

        _walk_with({
            health.SPECIFY_CLI: record(health.SPECIFY_CLI, code=1),
            health.INTEGRATION: record(health.INTEGRATION),
            health.SPECTRA_CLI: record(health.SPECTRA_CLI),
            health.SPECTRA_EXTENSION: record(health.SPECTRA_EXTENSION),
        }, outdated=set(health.ORDER))
        self.assertEqual(calls, list(health.ORDER))


class PartialFailure(unittest.TestCase):
    """A failing component must not strand the ones behind it."""

    def test_a_failing_early_component_does_not_prevent_later_attempts(self):
        attempted = []

        def action(key, code=0):
            def run(component, assume_yes=False):
                attempted.append(key)
                return code
            return run

        results = _walk_with({
            health.SPECIFY_CLI: action(health.SPECIFY_CLI, code=2),
            health.SPECTRA_CLI: action(health.SPECTRA_CLI),
        }, outdated={health.SPECIFY_CLI, health.SPECTRA_CLI})
        self.assertIn(health.SPECTRA_CLI, attempted)
        by_key = {r.key: r for r in results}
        self.assertEqual(by_key[health.SPECIFY_CLI].outcome, health.FAILED)
        self.assertEqual(by_key[health.SPECTRA_CLI].outcome, health.UPDATED)

    def test_a_delegation_error_is_recorded_and_the_walk_continues(self):
        def explode(component, assume_yes=False):
            raise extension.DelegationError("specify was not found on PATH")

        attempted = []
        results = _walk_with({
            health.SPECIFY_CLI: explode,
            health.SPECTRA_CLI: lambda component, assume_yes=False: attempted.append("x") or 0,
        }, outdated={health.SPECIFY_CLI, health.SPECTRA_CLI})
        by_key = {r.key: r for r in results}
        self.assertEqual(by_key[health.SPECIFY_CLI].outcome, health.FAILED)
        self.assertIn("not found on PATH", by_key[health.SPECIFY_CLI].detail)
        self.assertEqual(attempted, ["x"])

    def test_an_update_error_from_the_uv_reinstall_is_recorded_not_raised(self):
        def explode(component, assume_yes=False):
            raise cli_version.UpdateError("uv exited with code 1")

        results = _walk_with({health.SPECTRA_CLI: explode}, outdated={health.SPECTRA_CLI})
        by_key = {r.key: r for r in results}
        self.assertEqual(by_key[health.SPECTRA_CLI].outcome, health.FAILED)
        self.assertIn("uv exited", by_key[health.SPECTRA_CLI].detail)

    def test_every_component_yields_exactly_one_result(self):
        results = _walk_with({}, outdated={health.SPECIFY_CLI})
        self.assertEqual(len(results), 4)
        self.assertEqual([r.key for r in results], list(health.ORDER))


class Skipping(unittest.TestCase):
    """Anything not established as behind is never touched."""

    def test_an_unknown_component_is_skipped_and_never_attempted(self):
        attempted = []
        report = health.HealthReport([
            _status(health.SPECIFY_CLI, health.UNKNOWN, detail="no specify"),
            _status(health.INTEGRATION, health.UNKNOWN, detail="no specify"),
            _status(health.SPECTRA_CLI, health.NEEDS_UPDATING, "1.0.0", "2.0.0"),
            _status(health.SPECTRA_EXTENSION, health.UP_TO_DATE, "1.3.1", "1.3.1"),
        ])
        results = _walk_with(
            {k: (lambda key: lambda component, assume_yes=False: attempted.append(key) or 0)(k)
             for k in health.ORDER},
            outdated=None, report=report)
        self.assertEqual(attempted, [health.SPECTRA_CLI])
        by_key = {r.key: r for r in results}
        self.assertEqual(by_key[health.SPECIFY_CLI].outcome, health.SKIPPED)
        self.assertIn("could not be determined", by_key[health.SPECIFY_CLI].detail)

    def test_an_ahead_component_is_skipped_with_its_own_reason(self):
        report = health.HealthReport([
            _status(health.SPECIFY_CLI, health.AHEAD, "2.0.0", "1.0.0"),
            _status(health.INTEGRATION, health.UP_TO_DATE, "1", "1"),
            _status(health.SPECTRA_CLI, health.UP_TO_DATE, "1", "1"),
            _status(health.SPECTRA_EXTENSION, health.UP_TO_DATE, "1", "1"),
        ])
        results = _walk_with({}, outdated=None, report=report)
        by_key = {r.key: r for r in results}
        self.assertEqual(by_key[health.SPECIFY_CLI].outcome, health.SKIPPED)
        self.assertIn("ahead", by_key[health.SPECIFY_CLI].detail)

    def test_no_skip_is_ever_a_failure(self):
        report = health.HealthReport(
            [_status(k, health.UNKNOWN, detail="x") for k in health.ORDER])
        results = _walk_with({}, outdated=None, report=report)
        self.assertTrue(all(r.outcome == health.SKIPPED for r in results))
        self.assertFalse(any(r.failed for r in results))


class Interruption(unittest.TestCase):
    """Cancellation stops the walk. It is not a partial failure."""

    def test_exit_130_aborts_rather_than_continuing(self):
        attempted = []

        def interrupt(component, assume_yes=False):
            attempted.append("specify")
            return 130

        def later(component, assume_yes=False):
            attempted.append("later")
            return 0

        with self.assertRaises(health.Interrupted):
            _walk_with({health.SPECIFY_CLI: interrupt, health.SPECTRA_CLI: later},
                       outdated={health.SPECIFY_CLI, health.SPECTRA_CLI})
        self.assertEqual(attempted, ["specify"])

    def test_a_keyboard_interrupt_aborts_rather_than_continuing(self):
        attempted = []

        def interrupt(component, assume_yes=False):
            raise KeyboardInterrupt

        def later(component, assume_yes=False):
            attempted.append("later")
            return 0

        with self.assertRaises(health.Interrupted):
            _walk_with({health.SPECIFY_CLI: interrupt, health.SPECTRA_CLI: later},
                       outdated={health.SPECIFY_CLI, health.SPECTRA_CLI})
        self.assertEqual(attempted, [])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
