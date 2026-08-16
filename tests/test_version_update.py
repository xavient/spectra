"""`spectra version` and `spectra update` — the whole stack, and the one-command fix.

Two contracts are worth defending here, and both are about exit codes.

`spectra version` exits 0 for **every** delivered verdict, including an unknown one. With four
components there is always something to report, so unreachable data degrades one row rather than failing
the command — which is what makes this safe to drop into a shell without `|| true`. Non-zero is reserved
for a project state in which the question cannot be asked at all.

`spectra update` exits 0 when everything it *attempted* succeeded. A component it skipped — because the
status could not be established, or was already current — is neither a success nor a failure, so it
cannot turn a clean run into a failed one.
"""

from __future__ import annotations

import contextlib
import io
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import helpers as h  # noqa: E402
from spectra_cli import cli, extension, health, version as cli_version  # noqa: E402


def run(argv):
    buffer = io.StringIO()
    try:
        with contextlib.redirect_stdout(buffer):
            code = cli.main(argv)
    except SystemExit as exc:  # pragma: no cover
        code = exc.code
    return code, buffer.getvalue()


def _spectra_cli(status=health.UP_TO_DATE, installed="5.0.0", latest="5.0.0", detail=None):
    """A fixed verdict for this command's own version.

    Patched rather than exercised for real in most tests: it is the one component that would otherwise
    reach GitHub, and a suite that depended on the live release feed would fail for reasons having
    nothing to do with the code under test. Its own logic is covered in `test_health.py`.
    """
    return health.ComponentStatus(health.SPECTRA_CLI, status, installed=installed,
                                  latest=latest, detail=detail)


@contextlib.contextmanager
def stack(installed="1.3.1", published="1.3.1", *, integration="0.16.4",
          self_check=h.SELF_CHECK_UP_TO_DATE, spectra_cli=None, **project_kwargs):
    """A whole stack in a known state, so a test can vary exactly one component.

    Defaults put three components at "current" and leave the fourth (`installed` vs `published`) to the
    test — which is how a four-component report stays legible to assert against.
    """
    resolved = spectra_cli if spectra_cli is not None else _spectra_cli()
    with h.serve_roster(manifest_version=published) as base, h.raw_base(base), \
            h.fake_specify(self_check), \
            mock.patch.object(health, "get_spectra_cli_status", return_value=resolved):
        with h.temp_project(installed, integration_version=integration, **project_kwargs) as path, \
                h.cwd(path):
            yield path


# --------------------------------------------------------------------------- #
# version — the four-component report
# --------------------------------------------------------------------------- #

class Verdicts(unittest.TestCase):
    """All four components are reported, every time."""

    def test_all_four_components_appear(self):
        with stack("1.3.1", "1.3.1"):
            code, out = run(["version"])
        self.assertEqual(code, cli.EXIT_OK)
        for label in ("Specify CLI", "Core agents", "Spectra CLI", "Spectra agents"):
            self.assertIn(label, out)

    def test_the_rows_are_in_canonical_order(self):
        with stack("1.3.1", "1.3.1"):
            _, out = run(["version"])
        positions = [out.index(label) for label in
                     ("Specify CLI", "Core agents", "Spectra CLI", "Spectra agents")]
        self.assertEqual(positions, sorted(positions))

    def test_an_all_current_stack_says_so(self):
        with stack("1.3.1", "1.3.1"):
            code, out = run(["version"])
        self.assertEqual(code, cli.EXIT_OK)
        self.assertIn("up to date", out)
        self.assertNotIn("spectra update", out)

    def test_an_older_extension_reports_both_versions_and_names_the_fix(self):
        with stack("1.0.0", "1.3.1"):
            code, out = run(["version"])
        self.assertEqual(code, cli.EXIT_OK)
        self.assertIn("1.0.0", out)
        self.assertIn("1.3.1", out)
        self.assertIn("spectra update", out)

    def test_a_newer_extension_reports_ahead_and_offers_no_update(self):
        with stack("9.9.9", "1.3.1"):
            code, out = run(["version"])
        self.assertEqual(code, cli.EXIT_OK)
        self.assertIn("ahead of published", out)
        self.assertNotIn("You can update by running", out)

    def test_only_the_component_under_test_moves(self):
        with stack("1.0.0", "1.3.1"):
            _, out = run(["version"])
        self.assertEqual(out.count("needs updating"), 1)

    def test_every_verdict_exits_zero(self):
        for installed in ("1.3.1", "1.0.0", "9.9.9"):
            with stack(installed, "1.3.1"):
                code, _ = run(["version"])
            self.assertEqual(code, cli.EXIT_OK, installed)

    def test_the_update_hint_appears_only_when_something_is_behind(self):
        with stack("1.0.0", "1.3.1"):
            _, behind = run(["version"])
        with stack("1.3.1", "1.3.1"):
            _, current = run(["version"])
        self.assertIn("You can update by running", behind)
        self.assertNotIn("You can update by running", current)

    def test_the_retired_tool_command_is_no_longer_advertised(self):
        with stack("1.3.1", "1.3.1"):
            _, out = run(["version"])
        self.assertNotIn("spectra cli version", out)


class TheSpecifyCliRow(unittest.TestCase):
    def test_a_behind_specify_cli_carries_the_core_agents_with_it(self):
        """The integration version tracks the CLI, so a behind CLI means a behind integration."""
        with stack("1.3.1", "1.3.1", self_check=h.SELF_CHECK_UPDATE_AVAILABLE):
            code, out = run(["version"])
        self.assertEqual(code, cli.EXIT_OK)
        self.assertEqual(out.count("needs updating"), 2)
        self.assertIn("spectra update", out)

    def test_a_current_cli_with_a_stale_integration_flags_only_the_integration(self):
        with stack("1.3.1", "1.3.1", integration="0.12.14"):
            _, out = run(["version"])
        self.assertEqual(out.count("needs updating"), 1)
        self.assertIn("0.12.14", out)

    def test_specify_absent_degrades_two_rows_and_still_exits_zero(self):
        with h.serve_roster(manifest_version="1.3.1") as base, h.raw_base(base), \
                mock.patch.object(health, "get_spectra_cli_status", return_value=_spectra_cli()):
            with h.temp_project("1.3.1", integration_version="0.16.4") as path, h.cwd(path), \
                    h.without_specify():
                code, out = run(["version"])
        self.assertEqual(code, cli.EXIT_OK)
        # Count the row marker, not the bare word: one detail legitimately contains "unknown".
        self.assertEqual(out.count("unknown ("), 2)
        self.assertIn("not on PATH", out)

    def test_a_malformed_integration_file_degrades_only_that_row(self):
        with stack("1.3.1", "1.3.1", integration=h.BAD_JSON):
            code, out = run(["version"])
        self.assertEqual(code, cli.EXIT_OK)
        self.assertEqual(out.count("unknown ("), 1)
        self.assertIn("integration.json", out)


class WhenDataIsUnreachable(unittest.TestCase):
    """Unreachable published data degrades a row. It no longer fails the command."""

    def test_an_unreachable_published_version_exits_zero_with_an_unknown_row(self):
        with h.raw_base(h.UNREACHABLE_BASE), h.fake_specify(), \
                mock.patch.object(health, "get_spectra_cli_status", return_value=_spectra_cli()):
            with h.temp_project("1.3.1", integration_version="0.16.4") as path, h.cwd(path):
                code, out = run(["version"])
        # Deliberate change from the single-component command, which exited 3 here: with four
        # components there is still a report to deliver, so one row goes unknown and the rest stand.
        self.assertEqual(code, cli.EXIT_OK)
        self.assertIn("unknown", out)
        self.assertIn("could not be fetched", out)

    def test_it_still_reports_what_is_installed_when_the_published_version_is_unknown(self):
        with h.raw_base(h.UNREACHABLE_BASE), h.fake_specify(), \
                mock.patch.object(health, "get_spectra_cli_status", return_value=_spectra_cli()):
            with h.temp_project("1.2.3", integration_version="0.16.4") as path, h.cwd(path):
                _, out = run(["version"])
        self.assertIn("1.2.3", out)

    def test_nothing_checkable_at_all_says_so_rather_than_claiming_currency(self):
        unknown_cli = _spectra_cli(health.UNKNOWN, installed="5.0.0", latest=None,
                                   detail="the latest release could not be fetched")
        with h.raw_base(h.UNREACHABLE_BASE), h.without_specify(), \
                mock.patch.object(health, "get_spectra_cli_status", return_value=unknown_cli):
            with h.temp_project("1.3.1", integration_version=h.BAD_JSON) as path, h.cwd(path):
                code, out = run(["version"])
        self.assertEqual(code, cli.EXIT_OK)
        self.assertIn("could not be verified", out)
        self.assertNotIn("whole Spectra stack is up to date", out)

    def test_a_partially_known_stack_names_what_it_could_not_check(self):
        with stack("1.3.1", "1.3.1", integration=h.BAD_JSON):
            code, out = run(["version"])
        self.assertEqual(code, cli.EXIT_OK)
        self.assertIn("Unverified", out)
        self.assertIn("Core agents", out)


class NoUpdateCheck(unittest.TestCase):
    """`--no-update-check` suppresses exactly one lookup: this command's own release."""

    def test_it_suppresses_the_spectra_cli_release_lookup(self):
        with h.serve_roster(manifest_version="1.3.1") as base, h.raw_base(base), h.fake_specify():
            with h.temp_project("1.3.1", integration_version="0.16.4") as path, h.cwd(path):
                with mock.patch.object(cli_version, "resolve_latest") as resolve:
                    code, out = run(["version", "--no-update-check"])
        resolve.assert_not_called()
        self.assertEqual(code, cli.EXIT_OK)
        self.assertIn("no-update-check", out)

    def test_it_does_not_suppress_the_delegated_specify_check(self):
        with h.serve_roster(manifest_version="1.3.1") as base, h.raw_base(base), \
                h.fake_specify(h.SELF_CHECK_UP_TO_DATE):
            with h.temp_project("1.3.1", integration_version="0.16.4") as path, h.cwd(path):
                _, out = run(["version", "--no-update-check"])
        # Spec Kit's own check is Spec Kit's to manage; it still runs and still yields a verdict.
        self.assertIn("Specify CLI", out)
        self.assertIn("0.16.4", out)

    def test_the_environment_variable_behaves_the_same_way(self):
        with h.serve_roster(manifest_version="1.3.1") as base, h.raw_base(base), h.fake_specify():
            with h.temp_project("1.3.1", integration_version="0.16.4") as path, h.cwd(path):
                with mock.patch.dict("os.environ", {"SPECTRA_NO_UPDATE_CHECK": "1"}):
                    with mock.patch.object(cli_version, "resolve_latest") as resolve:
                        run(["version"])
        resolve.assert_not_called()


class CannotAnswer(unittest.TestCase):
    """Project states in which the question cannot be asked at all."""

    def test_not_installed_exits_five_with_its_own_message(self):
        with h.temp_project(installed_version=None) as path, h.cwd(path):
            code, out = run(["version"])
        self.assertEqual(code, cli.EXIT_PROJECT_STATE)
        self.assertIn("not installed in this project", out)

    def test_not_a_project_exits_five_and_says_something_different(self):
        with h.temp_project(is_project=False) as path, h.cwd(path):
            code, out = run(["version"])
        self.assertEqual(code, cli.EXIT_PROJECT_STATE)
        self.assertIn("not a Spec Kit project", out)

    def test_an_incomplete_install_exits_five_and_points_at_the_repair(self):
        with h.temp_project(incomplete=True) as path, h.cwd(path):
            code, out = run(["version"])
        self.assertEqual(code, cli.EXIT_PROJECT_STATE)
        self.assertIn("spectra update", out)

    def test_no_component_table_is_printed_in_a_bad_state(self):
        for kwargs in (dict(is_project=False), dict(installed_version=None)):
            with h.temp_project(**kwargs) as path, h.cwd(path):
                _, out = run(["version"])
            self.assertNotIn("Specify CLI", out)

    def test_the_bad_state_messages_all_differ(self):
        lines = []
        for kwargs in (dict(is_project=False), dict(installed_version=None), dict(incomplete=True)):
            with h.temp_project(**kwargs) as path, h.cwd(path):
                _, out = run(["version"])
            lines.append(out.strip().splitlines()[0])
        self.assertEqual(len(set(lines)), 3, lines)

    def test_no_work_is_done_when_the_project_state_is_wrong(self):
        """Checking before acting keeps a local mistake from looking like a network problem."""
        with h.temp_project(installed_version=None) as path, h.cwd(path):
            with mock.patch.object(health, "check_all") as checked:
                run(["version"])
        checked.assert_not_called()


class FromASubdirectory(unittest.TestCase):
    def test_the_verdict_is_the_same_from_root_and_from_a_nested_folder(self):
        with h.serve_roster(manifest_version="1.3.1") as base, h.raw_base(base), h.fake_specify(), \
                mock.patch.object(health, "get_spectra_cli_status", return_value=_spectra_cli()):
            with h.temp_project("1.0.0", integration_version="0.16.4", subdir="a/b") as nested:
                with h.cwd(nested):
                    nested_result = run(["version"])
                with h.cwd(nested.parents[1]):
                    root_result = run(["version"])
        self.assertEqual(nested_result, root_result)


# --------------------------------------------------------------------------- #
# update — the unified walk
# --------------------------------------------------------------------------- #

class NothingToDo(unittest.TestCase):
    def test_an_all_current_stack_prompts_for_nothing_and_exits_zero(self):
        with stack("1.3.1", "1.3.1"):
            with mock.patch.object(extension, "delegate_update") as delegated:
                code, out = run(["update"])
        delegated.assert_not_called()
        self.assertEqual(code, cli.EXIT_OK)
        self.assertIn("Everything is up to date", out)
        self.assertNotIn("Proceed?", out)

    def test_an_extension_ahead_of_published_changes_nothing(self):
        with stack("9.9.9", "1.3.1"):
            with mock.patch.object(extension, "delegate_update") as delegated:
                code, out = run(["update"])
        delegated.assert_not_called()
        self.assertEqual(code, cli.EXIT_OK)

    def test_nothing_checkable_does_not_claim_everything_is_up_to_date(self):
        """FR-027: exit 0 must not be allowed to imply 'verified current'."""
        unknown_cli = _spectra_cli(health.UNKNOWN, installed="5.0.0", latest=None,
                                   detail="the latest release could not be fetched")
        with h.raw_base(h.UNREACHABLE_BASE), h.without_specify(), \
                mock.patch.object(health, "get_spectra_cli_status", return_value=unknown_cli):
            with h.temp_project("1.3.1", integration_version=h.BAD_JSON) as path, h.cwd(path):
                code, out = run(["update"])
        self.assertEqual(code, cli.EXIT_OK)
        self.assertIn("Nothing could be checked", out)
        self.assertNotIn("Everything is up to date", out)
        self.assertIn("Unverified", out)

    def test_a_partially_checkable_stack_reports_both_facts(self):
        with stack("1.3.1", "1.3.1", integration=h.BAD_JSON):
            code, out = run(["update"])
        self.assertEqual(code, cli.EXIT_OK)
        self.assertIn("could be checked", out)
        self.assertIn("Unverified", out)
        self.assertIn("Core agents", out)


class Confirmation(unittest.TestCase):
    def test_the_prompt_lists_what_will_change(self):
        with stack("1.0.0", "1.3.1"):
            with mock.patch("sys.stdin.isatty", return_value=True), \
                 mock.patch.object(cli.ui, "confirm", return_value=False) as confirm:
                code, out = run(["update"])
        confirm.assert_called_once()
        self.assertIn("need updating", out)
        self.assertIn("Spectra agents", out)
        self.assertEqual(code, cli.EXIT_DECLINED)

    def test_declining_changes_nothing_and_exits_one(self):
        with stack("1.0.0", "1.3.1"):
            with mock.patch("sys.stdin.isatty", return_value=True), \
                 mock.patch.object(cli.ui, "confirm", return_value=False), \
                 mock.patch.object(extension, "delegate_update") as delegated:
                code, out = run(["update"])
        delegated.assert_not_called()
        self.assertEqual(code, cli.EXIT_DECLINED)
        self.assertIn("Nothing was changed", out)

    def test_yes_skips_the_prompt(self):
        with stack("1.0.0", "1.3.1"):
            with mock.patch.object(cli.ui, "confirm") as confirm, \
                 mock.patch.object(extension, "delegate_update", return_value=0):
                code, _ = run(["update", "--yes"])
        confirm.assert_not_called()
        self.assertEqual(code, cli.EXIT_OK)

    def test_an_unknown_component_is_not_offered_for_update(self):
        """FR-024: nothing that will not be touched appears in the list to approve."""
        with stack("1.0.0", "1.3.1", integration=h.BAD_JSON):
            with mock.patch("sys.stdin.isatty", return_value=True), \
                 mock.patch.object(cli.ui, "confirm", return_value=False):
                _, out = run(["update"])
        listed = out.split("need updating:")[1].split("Proceed")[0]
        self.assertIn("Spectra agents", listed)
        self.assertNotIn("Core agents", listed)


class TheWalk(unittest.TestCase):
    def test_an_out_of_date_extension_delegates_to_spec_kit(self):
        with stack("1.0.0", "1.3.1"):
            with mock.patch.object(extension, "delegate_update", return_value=0) as delegated:
                code, out = run(["update", "--yes"])
        delegated.assert_called_once_with()
        self.assertEqual(code, cli.EXIT_OK)
        self.assertIn("updated", out)

    def test_a_behind_specify_cli_upgrades_the_cli_then_the_integration(self):
        calls = []
        with stack("1.3.1", "1.3.1", self_check=h.SELF_CHECK_UPDATE_AVAILABLE):
            with mock.patch.object(extension, "delegate_self_upgrade",
                                   side_effect=lambda: calls.append("cli") or 0), \
                 mock.patch.object(extension, "delegate_integration_upgrade",
                                   side_effect=lambda: calls.append("integration") or 0):
                code, _ = run(["update", "--yes"])
        self.assertEqual(calls, ["cli", "integration"])
        self.assertEqual(code, cli.EXIT_OK)

    def test_all_four_run_in_canonical_order(self):
        calls = []
        behind_cli = _spectra_cli(health.NEEDS_UPDATING, installed="5.0.0", latest="6.0.0")
        with stack("1.0.0", "1.3.1", self_check=h.SELF_CHECK_UPDATE_AVAILABLE,
                   spectra_cli=behind_cli):
            with mock.patch.object(extension, "delegate_self_upgrade",
                                   side_effect=lambda: calls.append("specify") or 0), \
                 mock.patch.object(extension, "delegate_integration_upgrade",
                                   side_effect=lambda: calls.append("integration") or 0), \
                 mock.patch.object(cli_version, "perform_update",
                                   side_effect=lambda tag: calls.append("spectra_cli")), \
                 mock.patch.object(extension, "delegate_update",
                                   side_effect=lambda: calls.append("extension") or 0):
                code, _ = run(["update", "--yes"])
        self.assertEqual(calls, ["specify", "integration", "spectra_cli", "extension"])
        self.assertEqual(code, cli.EXIT_OK)

    def test_a_failing_delegation_is_reported_as_a_delegation_failure(self):
        with stack("1.0.0", "1.3.1"):
            with mock.patch.object(extension, "delegate_update", return_value=2):
                code, out = run(["update", "--yes"])
        self.assertEqual(code, cli.EXIT_DELEGATION)
        self.assertIn("failed", out)
        self.assertIn("2", out)

    def test_a_missing_spec_kit_is_explained_and_the_run_still_reports(self):
        with stack("1.0.0", "1.3.1"):
            with mock.patch.object(extension, "delegate_update",
                                   side_effect=extension.DelegationError("Spec Kit not found")):
                code, out = run(["update", "--yes"])
        self.assertEqual(code, cli.EXIT_DELEGATION)
        self.assertIn("Spec Kit not found", out)

    def test_a_partial_failure_still_attempts_the_rest(self):
        attempted = []
        behind_cli = _spectra_cli(health.NEEDS_UPDATING, installed="5.0.0", latest="6.0.0")
        with stack("1.0.0", "1.3.1", self_check=h.SELF_CHECK_UPDATE_AVAILABLE,
                   spectra_cli=behind_cli):
            with mock.patch.object(extension, "delegate_self_upgrade", return_value=1), \
                 mock.patch.object(extension, "delegate_integration_upgrade",
                                   side_effect=lambda: attempted.append("integration") or 0), \
                 mock.patch.object(cli_version, "perform_update",
                                   side_effect=lambda tag: attempted.append("spectra_cli")), \
                 mock.patch.object(extension, "delegate_update",
                                   side_effect=lambda: attempted.append("extension") or 0):
                code, out = run(["update", "--yes"])
        self.assertEqual(attempted, ["integration", "spectra_cli", "extension"])
        self.assertEqual(code, cli.EXIT_DELEGATION)
        self.assertIn("still updated", out)

    def test_skips_alongside_successes_exit_zero(self):
        """A component we could not establish must not turn a clean run into a failed one."""
        with stack("1.0.0", "1.3.1", integration=h.BAD_JSON):
            with mock.patch.object(extension, "delegate_update", return_value=0):
                code, out = run(["update", "--yes"])
        self.assertEqual(code, cli.EXIT_OK)
        self.assertIn("skipped", out)

    def test_an_interrupted_delegation_returns_the_conventional_code(self):
        with stack("1.0.0", "1.3.1"):
            with mock.patch.object(extension, "delegate_update", return_value=130):
                code, out = run(["update", "--yes"])
        self.assertEqual(code, 130)
        self.assertIn("Interrupted", out)

    def test_the_final_report_has_a_row_per_component(self):
        with stack("1.0.0", "1.3.1"):
            with mock.patch.object(extension, "delegate_update", return_value=0):
                _, out = run(["update", "--yes"])
        tail = out.split("Updating Spectra agents")[-1]
        for label in ("Specify CLI", "Core agents", "Spectra CLI", "Spectra agents"):
            self.assertIn(label, tail)


class BadStates(unittest.TestCase):
    def test_not_installed_exits_five_rather_than_delegating(self):
        with h.temp_project(installed_version=None) as path, h.cwd(path):
            with mock.patch.object(extension, "delegate_update") as delegated:
                code, _ = run(["update"])
        delegated.assert_not_called()
        self.assertEqual(code, cli.EXIT_PROJECT_STATE)

    def test_not_a_project_exits_five_rather_than_delegating(self):
        with h.temp_project(is_project=False) as path, h.cwd(path):
            with mock.patch.object(extension, "delegate_update") as delegated:
                code, _ = run(["update"])
        delegated.assert_not_called()
        self.assertEqual(code, cli.EXIT_PROJECT_STATE)

    def test_an_incomplete_install_is_repaired_rather_than_refused(self):
        """The one component this command can fix outright, so it is not gated away."""
        with h.serve_roster(manifest_version="1.3.1") as base, h.raw_base(base), h.fake_specify(), \
                mock.patch.object(health, "get_spectra_cli_status", return_value=_spectra_cli()):
            with h.temp_project(incomplete=True, integration_version="0.16.4") as path, \
                    h.cwd(path):
                with mock.patch.object(extension, "delegate_update", return_value=0) as delegated:
                    code, out = run(["update", "--yes"])
        delegated.assert_called_once()
        self.assertEqual(code, cli.EXIT_OK)
        self.assertIn("Spectra agents", out)


class TheLoopCloses(unittest.TestCase):
    def test_the_command_named_by_version_is_the_one_that_fixes_it(self):
        """Told out of date, fixed in one command, and that command was named."""
        with stack("1.0.0", "1.3.1") as path:
            manifest = path / ".specify" / "extensions" / "spectra" / "extension.yml"
            _, before = run(["version"])
            self.assertIn("spectra update", before)

            def fake_update():
                manifest.write_text(h.manifest_yaml("1.3.1"), encoding="utf-8")
                return 0

            with mock.patch.object(extension, "delegate_update", side_effect=fake_update):
                run(["update", "--yes"])
            code, after = run(["version"])
        self.assertEqual(code, cli.EXIT_OK)
        self.assertIn("up to date", after)
        self.assertNotIn("You can update by running", after)


if __name__ == "__main__":
    unittest.main()
