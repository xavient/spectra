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
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import helpers as h  # noqa: E402
from spectra_cli import cli, extension, health, ui, version as cli_version  # noqa: E402


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


COMPONENT_LABELS = ("Specify CLI", "Core agents", "Spectra CLI", "Spectra agents")


def _is_component_row(line: str) -> bool:
    """Whether `line` is one of the four component rows.

    Matches on the labels rather than on indentation plus a colon: the coverage advisory is also indented
    and also contains a colon ("To scaffold them: ..."), so a looser test would count it as a fifth row and
    fail for the wrong reason.
    """
    return (line.startswith("  ") and not line.startswith("    ")
            and any(line.lstrip().startswith(label + ":") for label in COMPONENT_LABELS))


def moving_manifest(path, version="1.3.1"):
    """A `delegate_update` stand-in that actually writes the new version, as a real update would.

    A stub that returns 0 and changes nothing is precisely what `cmd_update` now flags — it re-reads the
    state rather than trusting an exit code — so a test asserting a successful update has to move the
    version too.
    """
    manifest = path / ".specify" / "extensions" / "spectra" / "extension.yml"

    def delegate(*args, **kwargs):
        manifest.write_text(h.manifest_yaml(version), encoding="utf-8")
        return 0

    return delegate


def moving_integration(path, version):
    """A `delegate_integration_upgrade` stand-in that rewrites the recorded integration version."""
    def delegate(*args, **kwargs):
        h.write_integration(path, version)
        return 0

    return delegate


@contextlib.contextmanager
def stack(installed="1.3.1", published="1.3.1", *, integration="0.16.4",
          self_check=h.SELF_CHECK_UP_TO_DATE, spectra_cli=None, modified=None,
          cover_effect=False, use_fails=(), argv_log="argv.log", **project_kwargs):
    """A whole stack in a known state, so a test can vary exactly one component.

    Defaults put three components at "current" and leave the fourth (`installed` vs `published`) to the
    test — which is how a four-component report stays legible to assert against.

    `project_kwargs` reach `temp_project`, so `integrations={...}` builds a multi-integration project and
    the stubbed `specify` is told the same membership — otherwise the report and the modification probe
    would disagree about which integrations exist. `modified` seeds the probe's per-integration and
    shared file lists.

    `cover_effect` makes the stub's `integration use` *act*: it registers the activated agent and rewrites
    the recorded default, the way the real command does. Without it a rotation exits 0 while nothing
    changes, so the coverage step would appear to succeed while its verification had nothing to verify.
    `use_fails` names integrations whose activation fails, which is how the failed-activation and
    failed-restore paths are reached. The project is created *before* the stub so its root can be handed to
    the effect.
    """
    resolved = spectra_cli if spectra_cli is not None else _spectra_cli()
    integrations = project_kwargs.get("integrations")
    keys = tuple(integrations) if integrations else ("claude",)
    default = project_kwargs.get("default_integration") or keys[0]
    with h.serve_roster(manifest_version=published) as base, h.raw_base(base):
        with h.temp_project(installed, integration_version=integration, **project_kwargs) as path, \
                h.cwd(path):
            with h.fake_specify(self_check, installed=keys, default=default, modified=modified,
                                argv_log=(Path(path) / argv_log) if argv_log else None,
                                use_effect=path if cover_effect else None,
                                use_fails=use_fails), \
                    mock.patch.object(health, "get_spectra_cli_status", return_value=resolved):
                yield path


def use_calls(path, name="argv.log"):
    """The integration keys the stubbed `specify integration use` was called with, in order."""
    return h.integration_use_calls(Path(path) / name)


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


class MultiIntegrationRows(unittest.TestCase):
    """One row for many integrations, with children only when they earn their place."""

    TWO = {"kiro-cli": "0.16.4", "claude": "0.16.4"}

    def test_the_report_still_prints_exactly_four_components(self):
        with stack("1.3.1", "1.3.1", integrations=self.TWO, default_integration="kiro-cli"):
            code, out = run(["version"])
        self.assertEqual(code, cli.EXIT_OK)
        labels = ("Specify CLI", "Core agents", "Spectra CLI", "Spectra agents")
        for label in labels:
            self.assertIn(label, out)
        # Four component rows, whatever the integrations do beneath them (FR-011). A component row is
        # indented two spaces; a child is indented four.
        rows = [line for line in out.splitlines() if _is_component_row(line)]
        self.assertEqual(len(rows), 4)

    def test_a_behind_integration_is_named_on_the_row(self):
        with stack("1.3.1", "1.3.1",
                   integrations={"kiro-cli": "0.16.4", "claude": "0.15.1"},
                   default_integration="kiro-cli"):
            code, out = run(["version"])
        self.assertEqual(code, cli.EXIT_OK)
        self.assertIn("needs updating", out)
        self.assertIn("claude", out)

    def test_the_row_shows_the_oldest_version_of_the_two(self):
        with stack("1.3.1", "1.3.1",
                   integrations={"kiro-cli": "0.16.4", "claude": "0.15.1"},
                   default_integration="kiro-cli"):
            _, out = run(["version"])
        core = [line for line in out.splitlines() if "Core agents" in line][0]
        self.assertIn("0.15.1", core)

    def test_non_uniform_integrations_are_broken_out_beneath_the_row(self):
        with stack("1.3.1", "1.3.1",
                   integrations={"kiro-cli": "0.16.4", "claude": "0.15.1"},
                   default_integration="kiro-cli"):
            _, out = run(["version"])
        children = [line for line in out.splitlines() if line.startswith("    ")]
        self.assertEqual(len(children), 2)
        self.assertTrue(any("kiro-cli" in line for line in children))
        self.assertTrue(any("claude" in line for line in children))

    def test_uniform_integrations_print_no_children(self):
        with stack("1.3.1", "1.3.1", integrations=self.TWO, default_integration="kiro-cli"):
            _, out = run(["version"])
        self.assertEqual([line for line in out.splitlines() if line.startswith("    ")], [])

    def test_integrations_behind_at_the_same_version_are_still_named_on_the_row(self):
        # The drifted-project shape: both integrations behind at the same version, so the children are
        # uniform and the breakdown is correctly suppressed. The row itself must carry the names, or
        # FR-008 has no place left to be satisfied.
        with stack("1.3.1", "1.3.1",
                   integrations={"kiro-cli": "0.15.1", "claude": "0.15.1"},
                   default_integration="kiro-cli"):
            _, out = run(["version"])
        core = [line for line in out.splitlines() if "Core agents" in line][0]
        self.assertIn("kiro-cli", core)
        self.assertIn("claude", core)
        self.assertEqual([line for line in out.splitlines() if line.startswith("    ")], [])

    def test_a_single_integration_row_names_nothing(self):
        with stack("1.3.1", "1.3.1", integration="0.15.1"):
            _, out = run(["version"])
        core = [line for line in out.splitlines() if "Core agents" in line][0]
        self.assertNotIn("—", core)

    def test_one_run_names_every_behind_integration_without_opening_a_file(self):
        # SC-009: the developer learns which integrations are behind, and by how much, from one run.
        with stack("1.3.1", "1.3.1",
                   integrations={"kiro-cli": "0.15.1", "claude": "0.12.14"},
                   default_integration="kiro-cli"):
            _, out = run(["version"])
        self.assertIn("kiro-cli", out)
        self.assertIn("claude", out)
        self.assertIn("0.12.14", out)
        self.assertIn("0.15.1", out)


class SingleIntegrationUnchanged(unittest.TestCase):
    """The majority case must pay nothing for a minority-case feature (FR-012, SC-005)."""

    def test_no_children_and_no_advisory_for_one_integration(self):
        with stack("1.3.1", "1.3.1", integration="0.16.4"):
            code, out = run(["version"])
        self.assertEqual(code, cli.EXIT_OK)
        self.assertEqual([line for line in out.splitlines() if line.startswith("    ")], [])
        self.assertNotIn("registered for", out)

    def test_a_recorded_single_integration_still_prints_one_row(self):
        with stack("1.3.1", "1.3.1", integration="0.16.4",
                   integrations={"claude": "0.16.4"}):
            _, out = run(["version"])
        self.assertEqual([line for line in out.splitlines() if line.startswith("    ")], [])
        self.assertIn("Core agents", out)


class CoverageAdvisory(unittest.TestCase):
    """An installed integration with no Spectra commands is named, and nothing is changed."""

    BOTH = {"kiro-cli": "0.16.4", "claude": "0.16.4"}

    def test_an_uncovered_integration_is_named_with_its_remedy(self):
        """The remedy is `spectra install` since feature 011 — the install now closes the gap itself.

        It used to name the dependency's `integration use`, warning in the same breath that it changes the
        project's default for everyone. That warning was correct, which is what made the advice useless: a
        remedy nobody should run is not a remedy (FR-039, FR-040).
        """
        with stack("1.3.1", "1.3.1", integrations=self.BOTH, default_integration="kiro-cli",
                   registered_agents=["kiro-cli"]):
            code, out = run(["version"])
        self.assertEqual(code, cli.EXIT_OK)
        self.assertIn("claude is installed here but has no Spectra commands", out)
        self.assertIn("Add them with: spectra install", out)
        self.assertNotIn("specify integration use", out)
        self.assertNotIn("changes the project's default integration", out)

    def test_full_coverage_says_nothing(self):
        with stack("1.3.1", "1.3.1", integrations=self.BOTH, default_integration="kiro-cli",
                   registered_agents=["kiro-cli", "claude"]):
            code, out = run(["version"])
        self.assertEqual(code, cli.EXIT_OK)
        self.assertNotIn("has no Spectra commands", out)

    def test_an_unreadable_registry_says_nothing(self):
        with stack("1.3.1", "1.3.1", integrations=self.BOTH, default_integration="kiro-cli",
                   registered_agents=h.BAD_JSON):
            code, out = run(["version"])
        self.assertEqual(code, cli.EXIT_OK)
        self.assertNotIn("has no Spectra commands", out)

    def test_an_absent_registry_says_nothing(self):
        with stack("1.3.1", "1.3.1", integrations=self.BOTH, default_integration="kiro-cli"):
            code, out = run(["version"])
        self.assertEqual(code, cli.EXIT_OK)
        self.assertNotIn("has no Spectra commands", out)

    def test_a_single_integration_project_never_shows_it(self):
        with stack("1.3.1", "1.3.1", integration="0.16.4", registered_agents=["kiro-cli"]):
            code, out = run(["version"])
        self.assertEqual(code, cli.EXIT_OK)
        self.assertNotIn("has no Spectra commands", out)

    def test_it_is_rendered_outside_the_four_rows_and_changes_no_state(self):
        with stack("1.3.1", "1.3.1", integrations=self.BOTH, default_integration="kiro-cli",
                   registered_agents=["kiro-cli"]) as path:
            registry = (path / ".specify" / "extensions" / ".registry").read_text()
            recorded = (path / ".specify" / "integration.json").read_text()
            code, out = run(["version"])
            self.assertEqual(registry, (path / ".specify" / "extensions" / ".registry").read_text())
            self.assertEqual(recorded, (path / ".specify" / "integration.json").read_text())
        rows = [line for line in out.splitlines() if _is_component_row(line)]
        self.assertEqual(len(rows), 4)
        self.assertEqual(code, cli.EXIT_OK)

    def test_it_appears_even_when_the_stack_is_fully_current(self):
        with stack("1.3.1", "1.3.1", integrations=self.BOTH, default_integration="kiro-cli",
                   registered_agents=["kiro-cli"]):
            _, out = run(["version"])
        self.assertIn("up to date", out)
        self.assertIn("has no Spectra commands", out)


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
        with stack("1.0.0", "1.3.1") as path:
            with mock.patch.object(cli.ui, "confirm") as confirm, \
                 mock.patch.object(extension, "delegate_update",
                                   side_effect=moving_manifest(path)):
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


def moving_integrations(path, versions):
    """A `delegate_integration_upgrade` stand-in that rewrites the named manifests, as an upgrade would.

    `versions` maps integration key to the version its manifest should read afterwards. Records the argv
    it was called with, so a test can assert both the sequence and that the key was actually passed.
    """
    calls = []

    def delegate(key=None, force=False):
        calls.append((key, force))
        if key in versions:
            manifest = path / ".specify" / "integrations" / f"{key}.manifest.json"
            manifest.write_text(h.integration_manifest(key, versions[key]), encoding="utf-8")
        return 0

    delegate.calls = calls
    return delegate


class IntegrationWalk(unittest.TestCase):
    """Every behind integration is upgraded in one run, and nothing else is touched."""

    BOTH_BEHIND = {"kiro-cli": "0.15.1", "claude": "0.15.1"}
    ONE_BEHIND = {"kiro-cli": "0.16.4", "claude": "0.15.1"}

    def test_every_behind_integration_is_upgraded(self):
        with stack("1.3.1", "1.3.1", integrations=self.BOTH_BEHIND,
                   default_integration="kiro-cli") as path:
            delegate = moving_integrations(path, {"kiro-cli": "0.16.4", "claude": "0.16.4"})
            with mock.patch.object(extension, "delegate_integration_upgrade",
                                   side_effect=delegate):
                code, out = run(["update", "--yes"])
        self.assertEqual(code, cli.EXIT_OK)
        self.assertEqual(sorted(key for key, _ in delegate.calls), ["claude", "kiro-cli"])

    def test_an_already_current_integration_is_skipped_not_attempted(self):
        with stack("1.3.1", "1.3.1", integrations=self.ONE_BEHIND,
                   default_integration="kiro-cli") as path:
            delegate = moving_integrations(path, {"claude": "0.16.4"})
            with mock.patch.object(extension, "delegate_integration_upgrade",
                                   side_effect=delegate):
                code, out = run(["update", "--yes"])
        self.assertEqual(code, cli.EXIT_OK)
        self.assertEqual([key for key, _ in delegate.calls], ["claude"])
        self.assertIn("skipped", out)

    def test_the_key_is_named_and_the_default_is_never_switched(self):
        with stack("1.3.1", "1.3.1", integrations=self.ONE_BEHIND,
                   default_integration="kiro-cli") as path:
            recorded = (path / ".specify" / "integration.json").read_text()
            delegate = moving_integrations(path, {"claude": "0.16.4"})
            with mock.patch.object(extension, "delegate_integration_upgrade",
                                   side_effect=delegate):
                run(["update", "--yes"])
            after = (path / ".specify" / "integration.json").read_text()
        # The integration was named rather than made default first, and no force was requested.
        self.assertEqual(delegate.calls, [("claude", False)])
        self.assertEqual(recorded, after)

    def test_no_invocation_re_points_or_rescaffolds_an_agent(self):
        """FR-017, FR-040: naming the key is the whole mechanism; nothing else may be run.

        Captures `subprocess.call`, which is what the delegation helper uses, rather than patching the
        helper itself — the point is the argv actually constructed. `subprocess.run` is deliberately left
        alone: the Specify CLI probe uses it, and patching it would blind the check that decides whether
        the walk runs at all.
        """
        argv = []
        with stack("1.3.1", "1.3.1", integrations=self.BOTH_BEHIND,
                   default_integration="kiro-cli"):
            with mock.patch.object(extension, "specify_available", return_value=True), \
                 mock.patch("subprocess.call", side_effect=lambda a, **k: argv.append(a) or 0):
                run(["update", "--yes"])
        flat = " ".join(" ".join(call) for call in argv)
        self.assertIn("integration upgrade", flat)
        for forbidden in ("integration use", "integration switch", "extension add",
                          "extension update"):
            self.assertNotIn(forbidden, flat)

    def test_the_default_integration_goes_last(self):
        with stack("1.3.1", "1.3.1", integrations=self.BOTH_BEHIND,
                   default_integration="kiro-cli") as path:
            delegate = moving_integrations(path, {"kiro-cli": "0.16.4", "claude": "0.16.4"})
            with mock.patch.object(extension, "delegate_integration_upgrade",
                                   side_effect=delegate):
                run(["update", "--yes"])
        # kiro-cli is the default, so it is upgraded after claude: its own upgrade is the only one that
        # refreshes shared infrastructure as its own (research R3).
        self.assertEqual([key for key, _ in delegate.calls], ["claude", "kiro-cli"])

    def test_a_failing_integration_does_not_stop_the_others(self):
        attempted = []

        def delegate(key=None, force=False):
            attempted.append(key)
            return 1 if key == "claude" else 0

        with stack("1.3.1", "1.3.1", integrations=self.BOTH_BEHIND,
                   default_integration="kiro-cli"):
            with mock.patch.object(extension, "delegate_integration_upgrade",
                                   side_effect=delegate):
                code, out = run(["update", "--yes"])
        self.assertEqual(sorted(attempted), ["claude", "kiro-cli"])
        self.assertEqual(code, cli.EXIT_DELEGATION)
        self.assertIn("failed", out)

    def test_the_component_reports_the_worst_of_its_children(self):
        self.assertEqual(health.worst_outcome([health.UPDATED, health.FAILED]), health.FAILED)
        self.assertEqual(health.worst_outcome([health.SKIPPED, health.UPDATED]), health.UPDATED)
        self.assertEqual(health.worst_outcome([health.SKIPPED, health.SKIPPED]), health.SKIPPED)
        self.assertEqual(health.worst_outcome([]), health.SKIPPED)

    def test_an_unknown_integration_is_never_attempted(self):
        with stack("1.3.1", "1.3.1",
                   integrations={"kiro-cli": "0.15.1", "claude": h.MISSING_MANIFEST},
                   default_integration="kiro-cli") as path:
            delegate = moving_integrations(path, {"kiro-cli": "0.16.4"})
            with mock.patch.object(extension, "delegate_integration_upgrade",
                                   side_effect=delegate):
                code, out = run(["update", "--yes"])
        self.assertEqual([key for key, _ in delegate.calls], ["kiro-cli"])
        self.assertEqual(code, cli.EXIT_OK)

    def test_an_interrupt_aborts_the_whole_walk(self):
        attempted = []

        def delegate(key=None, force=False):
            attempted.append(key)
            return 130

        with stack("1.3.1", "1.3.1", integrations=self.BOTH_BEHIND,
                   default_integration="kiro-cli"):
            with mock.patch.object(extension, "delegate_integration_upgrade",
                                   side_effect=delegate), \
                 mock.patch.object(extension, "delegate_update") as later:
                code, out = run(["update", "--yes"])
        self.assertEqual(len(attempted), 1)
        later.assert_not_called()
        self.assertEqual(code, cli.EXIT_INTERRUPTED)
        self.assertIn("Interrupted", out)

    def test_each_integration_is_verified_on_its_own_manifest(self):
        """FR-022: one integration moving does not vouch for the other."""
        with stack("1.3.1", "1.3.1", integrations=self.BOTH_BEHIND,
                   default_integration="kiro-cli") as path:
            delegate = moving_integrations(path, {"claude": "0.16.4"})  # kiro-cli reports 0 but stalls
            with mock.patch.object(extension, "delegate_integration_upgrade",
                                   side_effect=delegate):
                code, out = run(["update", "--yes"])
        self.assertIn("unchanged", out)
        self.assertEqual(code, cli.EXIT_DELEGATION)

    def test_the_plan_names_each_integration_it_will_upgrade(self):
        with stack("1.3.1", "1.3.1", integrations=self.BOTH_BEHIND,
                   default_integration="kiro-cli"):
            with mock.patch("sys.stdin.isatty", return_value=True), \
                 mock.patch.object(cli.ui, "confirm", return_value=False):
                _, out = run(["update"])
        listed = out.split("need updating:")[1].split("Proceed")[0]
        self.assertIn("kiro-cli", listed)
        self.assertIn("claude", listed)

    def test_the_round_trip_leaves_every_integration_current(self):
        """SC-001: update, then ask again, and the row says so."""
        with stack("1.3.1", "1.3.1", integrations=self.BOTH_BEHIND,
                   default_integration="kiro-cli") as path:
            delegate = moving_integrations(path, {"kiro-cli": "0.16.4", "claude": "0.16.4"})
            with mock.patch.object(extension, "delegate_integration_upgrade",
                                   side_effect=delegate):
                code, _ = run(["update", "--yes"])
            self.assertEqual(code, cli.EXIT_OK)
            _, out = run(["version"])
        core = [line for line in out.splitlines() if "Core agents" in line][0]
        self.assertIn("up to date", core)
        self.assertEqual([line for line in out.splitlines() if line.startswith("    ")], [])


class Disclosure(unittest.TestCase):
    """Nothing is overwritten without the exact files being shown first, and one informed yes."""

    BEHIND = {"kiro-cli": "0.16.4", "claude": "0.15.1"}
    BOTH_BEHIND = {"kiro-cli": "0.15.1", "claude": "0.15.1"}
    CLAUDE_FILES = [".claude/skills/speckit-plan/SKILL.md", ".claude/skills/speckit-tasks/SKILL.md"]
    SHARED_FILES = [".specify/templates/spec-template.md", ".specify/templates/plan-template.md"]

    def _seeded(self, integrations=None, modified=None, **kwargs):
        return stack("1.3.1", "1.3.1", integrations=integrations or self.BEHIND,
                     default_integration="kiro-cli", modified=modified, **kwargs)

    def test_version_never_runs_the_probe(self):
        """FR-012, research R1: the report stays a pure local read."""
        argv = []
        real = health.modification_report

        def spy(*a, **k):
            argv.append("called")
            return real(*a, **k)

        with self._seeded():
            with mock.patch.object(health, "modification_report", side_effect=spy):
                run(["version"])
        self.assertEqual(argv, [])

    def test_a_current_integration_with_modified_files_asks_nothing(self):
        """FR-034: an integration nobody is upgrading cannot trigger a prompt."""
        with self._seeded(modified={"kiro-cli": [".kiro/prompts/speckit.plan.md"]}) as path:
            delegate = moving_integrations(path, {"claude": "0.16.4"})
            with mock.patch.object(cli.ui, "confirm") as confirm, \
                 mock.patch.object(extension, "delegate_integration_upgrade",
                                   side_effect=delegate):
                code, out = run(["update", "--yes"])
        confirm.assert_not_called()
        self.assertNotIn("Modified files detected", out)
        self.assertEqual(code, cli.EXIT_OK)

    def test_shared_only_modifications_with_everything_current_ask_nothing(self):
        with stack("1.3.1", "1.3.1", integrations={"kiro-cli": "0.16.4", "claude": "0.16.4"},
                   default_integration="kiro-cli", modified={"speckit": self.SHARED_FILES}):
            with mock.patch.object(cli.ui, "confirm") as confirm:
                code, out = run(["update", "--yes"])
        confirm.assert_not_called()
        self.assertNotIn("Modified files detected", out)
        self.assertEqual(code, cli.EXIT_OK)

    def test_the_files_are_listed_before_any_question_is_asked(self):
        with self._seeded(modified={"claude": self.CLAUDE_FILES, "speckit": self.SHARED_FILES}):
            with mock.patch("sys.stdin.isatty", return_value=True), \
                 mock.patch.object(cli.ui, "confirm", side_effect=[True, False]) as confirm:
                _, out = run(["update"])
        # Two questions: the plan, then the overwrite. Never more.
        self.assertEqual(confirm.call_count, 2)
        for path in self.CLAUDE_FILES + self.SHARED_FILES:
            self.assertIn(path, out)
        # Grouped: the integration by name, shared infrastructure as its own group.
        self.assertIn("claude", out)
        self.assertIn("Shared Spec Kit infrastructure", out)
        # The files are on screen before the question is put: the disclosure is printed, and the question
        # that follows is the overwrite one (`ui.confirm` is mocked, so its prompt never reaches stdout).
        self.assertIn("Modified files detected", out)
        self.assertIn("Overwrite these files?", confirm.call_args_list[-1].args[0])
        self.assertLess(out.index("Modified files detected"),
                        out.index("There is no way to show what changed"))

    def test_shared_files_are_disclosed_even_though_they_did_not_cause_the_block(self):
        """Finding F6: the overwrite is not scoped to the files that blocked the upgrade."""
        with self._seeded(modified={"claude": self.CLAUDE_FILES, "speckit": self.SHARED_FILES}):
            with mock.patch("sys.stdin.isatty", return_value=True), \
                 mock.patch.object(cli.ui, "confirm", side_effect=[True, False]):
                _, out = run(["update"])
        for path in self.SHARED_FILES:
            self.assertIn(path, out)

    def test_every_file_is_listed_even_when_there_are_many(self):
        many = [f".claude/skills/speckit-{n}/SKILL.md" for n in range(30)]
        with self._seeded(modified={"claude": many}):
            with mock.patch("sys.stdin.isatty", return_value=True), \
                 mock.patch.object(cli.ui, "confirm", side_effect=[True, False]):
                _, out = run(["update"])
        for path in many:
            self.assertIn(path, out)

    def test_the_prompt_defaults_to_no(self):
        with self._seeded(modified={"claude": self.CLAUDE_FILES}):
            with mock.patch("sys.stdin.isatty", return_value=True), \
                 mock.patch.object(cli.ui, "confirm") as confirm:
                confirm.side_effect = lambda prompt, default_yes=True: default_yes
                code, out = run(["update"])
        # The overwrite prompt is the second confirm (the first approves the plan); both must be asked
        # with the default at no for the overwrite.
        overwrite_call = confirm.call_args_list[-1]
        self.assertEqual(overwrite_call.kwargs.get("default_yes"), False)

    def test_declining_still_updates_what_needs_no_overwrite(self):
        with stack("1.3.1", "1.3.1", integrations=self.BOTH_BEHIND,
                   default_integration="kiro-cli",
                   modified={"claude": self.CLAUDE_FILES}) as path:
            delegate = moving_integrations(path, {"kiro-cli": "0.16.4"})
            with mock.patch("sys.stdin.isatty", return_value=True), \
                 mock.patch.object(cli.ui, "confirm", side_effect=[True, False]), \
                 mock.patch.object(extension, "delegate_integration_upgrade",
                                   side_effect=delegate):
                code, out = run(["update"])
        self.assertEqual([key for key, _ in delegate.calls], ["kiro-cli"])
        self.assertIn("overwrite not authorized", out)
        self.assertEqual(code, cli.EXIT_OK)

    def test_authorization_is_limited_to_the_integrations_that_need_it(self):
        """FR-029: an integration upgradeable without an overwrite is never forced."""
        with stack("1.3.1", "1.3.1", integrations=self.BOTH_BEHIND,
                   default_integration="kiro-cli",
                   modified={"claude": self.CLAUDE_FILES}) as path:
            delegate = moving_integrations(path, {"kiro-cli": "0.16.4", "claude": "0.16.4"})
            with mock.patch("sys.stdin.isatty", return_value=True), \
                 mock.patch.object(cli.ui, "confirm", return_value=True), \
                 mock.patch.object(extension, "delegate_integration_upgrade",
                                   side_effect=delegate):
                run(["update"])
        self.assertEqual(dict(delegate.calls), {"kiro-cli": False, "claude": True})

    def test_the_closing_message_states_the_options_and_advises_no_diff(self):
        with self._seeded(modified={"claude": self.CLAUDE_FILES}):
            with mock.patch("sys.stdin.isatty", return_value=True), \
                 mock.patch.object(cli.ui, "confirm", side_effect=[True, False]):
                _, out = run(["update"])
        self.assertIn("--force", out)
        self.assertIn("claude", out)
        # FR-035 / finding F9: never advise reviewing a difference that cannot be shown.
        self.assertNotIn("review the changes", out.lower())
        self.assertNotIn("diff", out.lower())

    def test_authorization_is_never_remembered_between_runs(self):
        with self._seeded(modified={"claude": self.CLAUDE_FILES}) as path:
            delegate = moving_integrations(path, {})
            with mock.patch("sys.stdin.isatty", return_value=True), \
                 mock.patch.object(cli.ui, "confirm", return_value=True) as confirm, \
                 mock.patch.object(extension, "delegate_integration_upgrade",
                                   side_effect=delegate):
                run(["update"])
                first = confirm.call_count
                run(["update"])
                self.assertGreater(confirm.call_count, first)

    def test_force_never_reaches_the_delegate_without_an_authorization_act(self):
        """The in-suite form of SC-003, asserted across every no-authorization path."""
        seen = []

        def delegate(key=None, force=False):
            seen.append(force)
            return 0

        # Declined interactively.
        with self._seeded(modified={"claude": self.CLAUDE_FILES}):
            with mock.patch("sys.stdin.isatty", return_value=True), \
                 mock.patch.object(cli.ui, "confirm", side_effect=[True, False]), \
                 mock.patch.object(extension, "delegate_integration_upgrade",
                                   side_effect=delegate):
                run(["update"])
        # Non-interactive with --yes but no --force.
        with self._seeded(modified={"claude": self.CLAUDE_FILES}):
            with mock.patch("sys.stdin.isatty", return_value=False), \
                 mock.patch.object(extension, "delegate_integration_upgrade",
                                   side_effect=delegate):
                run(["update", "--yes"])
        # Probe unavailable, so nothing could be established.
        with self._seeded(modified={"claude": self.CLAUDE_FILES}):
            with mock.patch.object(health, "modification_report",
                                   return_value=health.ModificationReport(established=False)), \
                 mock.patch.object(extension, "delegate_integration_upgrade",
                                   side_effect=delegate):
                run(["update", "--yes"])
        self.assertTrue(seen)
        self.assertNotIn(True, seen)

    def test_an_unestablished_probe_still_attempts_the_upgrade_unforced(self):
        """Research R6: not knowing what would be overwritten means not forcing, not stalling."""
        with self._seeded() as path:
            delegate = moving_integrations(path, {"claude": "0.16.4"})
            with mock.patch.object(health, "modification_report",
                                   return_value=health.ModificationReport(established=False)), \
                 mock.patch.object(extension, "delegate_integration_upgrade",
                                   side_effect=delegate):
                code, out = run(["update", "--yes"])
        self.assertEqual(delegate.calls, [("claude", False)])
        self.assertEqual(code, cli.EXIT_OK)
        self.assertNotIn("Modified files detected", out)


class NonInteractive(unittest.TestCase):
    """Automation updates what it can and destroys nothing (FR-027, FR-031, SC-007)."""

    BEHIND = {"kiro-cli": "0.16.4", "claude": "0.15.1"}
    FILES = [".claude/skills/speckit-plan/SKILL.md"]

    def _seeded(self, **kwargs):
        return stack("1.3.1", "1.3.1", integrations=self.BEHIND, default_integration="kiro-cli",
                     modified={"claude": self.FILES}, **kwargs)

    def test_yes_without_a_terminal_overwrites_nothing_and_names_the_flag(self):
        with self._seeded() as path:
            delegate = moving_integrations(path, {})
            with mock.patch("sys.stdin.isatty", return_value=False), \
                 mock.patch.object(extension, "delegate_integration_upgrade",
                                   side_effect=delegate):
                code, out = run(["update", "--yes"])
        self.assertEqual(delegate.calls, [])
        self.assertIn("--force", out)
        self.assertIn("overwrite not authorized", out)
        self.assertEqual(code, cli.EXIT_OK)

    def test_force_without_a_terminal_proceeds_and_still_discloses(self):
        with self._seeded() as path:
            delegate = moving_integrations(path, {"claude": "0.16.4"})
            with mock.patch("sys.stdin.isatty", return_value=False), \
                 mock.patch.object(extension, "delegate_integration_upgrade",
                                   side_effect=delegate):
                code, out = run(["update", "--yes", "--force"])
        self.assertEqual(delegate.calls, [("claude", True)])
        self.assertIn("Modified files detected", out)
        for path_ in self.FILES:
            self.assertIn(path_, out)
        self.assertEqual(code, cli.EXIT_OK)

    def test_no_prompt_is_attempted_without_a_terminal(self):
        with self._seeded():
            with mock.patch("sys.stdin.isatty", return_value=False), \
                 mock.patch.object(cli.ui, "confirm") as confirm, \
                 mock.patch.object(extension, "delegate_integration_upgrade", return_value=0):
                run(["update", "--yes"])
        confirm.assert_not_called()

    def test_force_with_nothing_to_overwrite_changes_nothing(self):
        with stack("1.3.1", "1.3.1", integrations=self.BEHIND, default_integration="kiro-cli") as path:
            delegate = moving_integrations(path, {"claude": "0.16.4"})
            with mock.patch.object(extension, "delegate_integration_upgrade",
                                   side_effect=delegate):
                code, out = run(["update", "--yes", "--force"])
        self.assertEqual(delegate.calls, [("claude", False)])
        self.assertNotIn("Modified files detected", out)
        self.assertEqual(code, cli.EXIT_OK)

    def test_skipping_for_want_of_authorization_is_not_a_failure(self):
        with self._seeded() as path:
            delegate = moving_integrations(path, {})
            with mock.patch("sys.stdin.isatty", return_value=False), \
                 mock.patch.object(extension, "delegate_integration_upgrade",
                                   side_effect=delegate):
                code, _ = run(["update", "--yes"])
        self.assertEqual(code, cli.EXIT_OK)

    def test_the_closing_line_does_not_claim_an_update_that_did_not_happen(self):
        """Exit 0 is right when everything was skipped; claiming success is not."""
        with self._seeded() as path:
            delegate = moving_integrations(path, {})
            with mock.patch("sys.stdin.isatty", return_value=False), \
                 mock.patch.object(extension, "delegate_integration_upgrade",
                                   side_effect=delegate):
                code, out = run(["update", "--yes"])
        self.assertEqual(code, cli.EXIT_OK)
        self.assertIn("Nothing was updated", out)
        self.assertNotIn("Everything that needed updating was updated", out)

    def test_a_partial_run_says_everything_else_was_updated(self):
        both = {"kiro-cli": "0.15.1", "claude": "0.15.1"}
        with stack("1.3.1", "1.3.1", integrations=both, default_integration="kiro-cli",
                   modified={"claude": self.FILES}) as path:
            delegate = moving_integrations(path, {"kiro-cli": "0.16.4"})
            with mock.patch("sys.stdin.isatty", return_value=False), \
                 mock.patch.object(extension, "delegate_integration_upgrade",
                                   side_effect=delegate):
                code, out = run(["update", "--yes"])
        self.assertEqual(code, cli.EXIT_OK)
        self.assertIn("Everything else was updated", out)

    def test_a_component_row_with_no_attempt_still_gives_a_reason(self):
        with self._seeded() as path:
            delegate = moving_integrations(path, {})
            with mock.patch("sys.stdin.isatty", return_value=False), \
                 mock.patch.object(extension, "delegate_integration_upgrade",
                                   side_effect=delegate):
                _, out = run(["update", "--yes"])
        self.assertNotIn("skipped (None)", out)


class TheWalk(unittest.TestCase):
    def test_an_out_of_date_extension_delegates_to_spec_kit(self):
        with stack("1.0.0", "1.3.1") as path:
            with mock.patch.object(extension, "delegate_update",
                                   side_effect=moving_manifest(path)) as delegated:
                code, out = run(["update", "--yes"])
        delegated.assert_called_once()
        self.assertEqual(code, cli.EXIT_OK)
        self.assertIn("updated", out)

    def test_a_behind_specify_cli_upgrades_the_cli_then_the_integration(self):
        calls = []
        with stack("1.3.1", "1.3.1", self_check=h.SELF_CHECK_UPDATE_AVAILABLE):
            with mock.patch.object(extension, "delegate_self_upgrade",
                                   side_effect=lambda *a, **k: calls.append("cli") or 0), \
                 mock.patch.object(extension, "delegate_integration_upgrade",
                                   side_effect=lambda *a, **k: calls.append("integration") or 0):
                code, _ = run(["update", "--yes"])
        self.assertEqual(calls, ["cli", "integration"])
        # Both stubs report success without the underlying versions moving, which cmd_update correctly
        # refuses to call a win — the order is what this test is about.
        self.assertEqual(code, cli.EXIT_DELEGATION)

    def test_all_four_run_in_canonical_order(self):
        calls = []
        behind_cli = _spectra_cli(health.NEEDS_UPDATING, installed="5.0.0", latest="6.0.0")
        with stack("1.0.0", "1.3.1", self_check=h.SELF_CHECK_UPDATE_AVAILABLE,
                   spectra_cli=behind_cli):
            with mock.patch.object(extension, "delegate_self_upgrade",
                                   side_effect=lambda *a, **k: calls.append("specify") or 0), \
                 mock.patch.object(extension, "delegate_integration_upgrade",
                                   side_effect=lambda *a, **k: calls.append("integration") or 0), \
                 mock.patch.object(cli_version, "perform_update",
                                   side_effect=lambda tag: calls.append("spectra_cli")), \
                 mock.patch.object(extension, "delegate_update",
                                   side_effect=lambda *a, **k: calls.append("extension") or 0):
                code, _ = run(["update", "--yes"])
        self.assertEqual(calls, ["specify", "integration", "spectra_cli", "extension"])
        # Stubs report success without moving versions; the order is the assertion here.
        self.assertIn(code, (cli.EXIT_OK, cli.EXIT_DELEGATION))

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
                                   side_effect=lambda *a, **k: attempted.append("integration") or 0), \
                 mock.patch.object(cli_version, "perform_update",
                                   side_effect=lambda tag: attempted.append("spectra_cli")), \
                 mock.patch.object(extension, "delegate_update",
                                   side_effect=lambda *a, **k: attempted.append("extension") or 0):
                code, out = run(["update", "--yes"])
        self.assertEqual(attempted, ["integration", "spectra_cli", "extension"])
        self.assertEqual(code, cli.EXIT_DELEGATION)
        self.assertIn("still updated", out)

    def test_skips_alongside_successes_exit_zero(self):
        """A component we could not establish must not turn a clean run into a failed one."""
        with stack("1.0.0", "1.3.1", integration=h.BAD_JSON) as path:
            with mock.patch.object(extension, "delegate_update",
                                   side_effect=moving_manifest(path)):
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
        with stack("1.0.0", "1.3.1") as path:
            with mock.patch.object(extension, "delegate_update",
                                   side_effect=moving_manifest(path)):
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

            with mock.patch.object(extension, "delegate_update",
                                   side_effect=moving_manifest(path)):
                run(["update", "--yes"])
            code, after = run(["version"])
        self.assertEqual(code, cli.EXIT_OK)
        self.assertIn("up to date", after)
        self.assertNotIn("You can update by running", after)


class CoverageInTheUpdate(unittest.TestCase):
    """`spectra update` re-establishes coverage after the walk instead of silently deleting it.

    The regression this closes is the dependency's, not ours: updating an extension unregisters it for
    **every** agent and re-registers it for the default alone (BRD-007 F5). So a project a developer had
    fixed by hand lost that work on the next maintenance run, with no message and no failure.
    """

    BOTH = {"kiro-cli": "0.16.4", "claude": "0.16.4"}

    def test_the_question_is_asked_once_and_defaults_to_no(self):
        """FR-025, FR-026 — and the disclosure names both the agents and the default to restore."""
        with stack("1.3.1", "1.3.1", integrations=self.BOTH, default_integration="kiro-cli",
                   registered_agents=["kiro-cli"], cover_effect=True) as path:
            with mock.patch("sys.stdin.isatty", return_value=True), \
                    mock.patch.object(ui, "confirm", return_value=False) as confirm:
                code, out = run(["update"])
            self.assertEqual(confirm.call_count, 1)
            self.assertFalse(confirm.call_args.kwargs.get("default_yes", True))
            self.assertIn("Spectra's commands are missing for: claude", out)
            self.assertIn("the project's default for a moment", out)
            self.assertIn("kiro-cli", out)
            self.assertEqual(use_calls(path), [])
            self.assertEqual(code, cli.EXIT_OK)

    def test_yes_authorizes_without_a_prompt(self):
        """FR-027. And `--force` is never consulted for coverage (FR-009)."""
        with stack("1.3.1", "1.3.1", integrations=self.BOTH, default_integration="kiro-cli",
                   registered_agents=["kiro-cli"], cover_effect=True) as path:
            with mock.patch.object(ui, "confirm",
                                   side_effect=AssertionError("must not prompt with --yes")):
                code, out = run(["update", "--yes"])
            self.assertEqual(code, cli.EXIT_OK)
            self.assertEqual(use_calls(path), ["claude", "kiro-cli"])
            self.assertIn("Agent coverage", out)
            for argv in h.read_argv_log(Path(path) / "argv.log"):
                self.assertNotIn("--force", argv)

    def test_declining_leaves_the_project_alone_and_names_the_remedy(self):
        """FR-029, FR-030, SC-007 — a decline is an abstention, not a failure."""
        with stack("1.3.1", "1.3.1", integrations=self.BOTH, default_integration="kiro-cli",
                   registered_agents=["kiro-cli"], cover_effect=True) as path:
            with mock.patch("sys.stdin.isatty", return_value=True), \
                    mock.patch.object(ui, "confirm", return_value=False):
                code, out = run(["update"])
            self.assertEqual(code, cli.EXIT_OK)
            self.assertEqual(use_calls(path), [])
            self.assertIn("still missing for: claude", out)
            self.assertIn("spectra install", out)
            self.assertEqual(_default_of(path), "kiro-cli")

    def test_no_terminal_and_no_yes_activates_nothing_and_names_the_flag(self):
        """FR-028 — automation authorizes nothing it was not explicitly told to."""
        with stack("1.3.1", "1.3.1", integrations=self.BOTH, default_integration="kiro-cli",
                   registered_agents=["kiro-cli"], cover_effect=True) as path:
            with mock.patch("sys.stdin", io.StringIO("")):
                code, out = run(["update"])
            self.assertEqual(code, cli.EXIT_OK)
            self.assertEqual(use_calls(path), [])
            self.assertIn("--yes", out)

    def test_coverage_is_evaluated_even_when_nothing_needed_updating(self):
        """FR-024. The loss may have been caused by an earlier run, so every run checks."""
        with stack("1.3.1", "1.3.1", integrations=self.BOTH, default_integration="kiro-cli",
                   registered_agents=["kiro-cli"], cover_effect=True) as path:
            code, out = run(["update", "--yes"])
            self.assertEqual(code, cli.EXIT_OK)
            self.assertIn("up to date", out)
            self.assertEqual(use_calls(path), ["claude", "kiro-cli"])
            self.assertEqual(_registered(path), ["claude", "kiro-cli"])
            self.assertEqual(_default_of(path), "kiro-cli")

    def test_coverage_survives_an_extension_update(self):
        """The whole point: an update that moves the extension no longer costs the other agent."""
        with stack("1.0.0", "1.3.1", integrations=self.BOTH, default_integration="kiro-cli",
                   registered_agents=["kiro-cli"], cover_effect=True) as path:
            with mock.patch.object(extension, "delegate_update",
                                   side_effect=moving_manifest(path)):
                code, out = run(["update", "--yes"])
            self.assertEqual(code, cli.EXIT_OK)
            self.assertIn("Agent coverage", out)
            self.assertEqual(_registered(path), ["claude", "kiro-cli"])
            self.assertEqual(_default_of(path), "kiro-cli")

    def test_a_fully_covered_project_adds_no_output_and_no_question(self):
        """FR-037 — and this is the assertion that keeps the majority case free of tax."""
        with stack("1.3.1", "1.3.1", integrations=self.BOTH, default_integration="kiro-cli",
                   registered_agents=["kiro-cli", "claude"], cover_effect=True) as path:
            with mock.patch("sys.stdin.isatty", return_value=True), \
                    mock.patch.object(ui, "confirm",
                                      side_effect=AssertionError("must not prompt")):
                code, out = run(["update"])
            self.assertEqual(code, cli.EXIT_OK)
            self.assertNotIn("Agent coverage", out)
            self.assertNotIn("missing for", out)
            self.assertEqual(use_calls(path), [])

    def test_a_single_integration_project_is_untouched(self):
        """FR-038, SC-006 — one integration, no coverage question, no coverage row."""
        with stack("1.3.1", "1.3.1", integration="0.16.4",
                   registered_agents=["claude"], cover_effect=True) as path:
            code, out = run(["update"])
            self.assertEqual(code, cli.EXIT_OK)
            self.assertNotIn("Agent coverage", out)
            self.assertEqual(use_calls(path), [])

    def test_the_coverage_row_lists_one_child_per_integration(self):
        """FR-032 — reported per integration, in the outcome table."""
        with stack("1.3.1", "1.3.1",
                   integrations={"kiro-cli": "0.16.4", "claude": "0.16.4", "copilot": "0.16.4"},
                   default_integration="kiro-cli", registered_agents=["kiro-cli"],
                   cover_effect=True) as path:
            code, out = run(["update", "--yes"])
            self.assertEqual(code, cli.EXIT_OK)
            self.assertIn("Agent coverage", out)
            for key in ("kiro-cli", "claude", "copilot"):
                self.assertTrue(any(line.strip().startswith(key + ":") for line in out.splitlines()),
                                f"no child row for {key} in:\n{out}")

    def test_no_fifth_row_appears_in_the_health_table(self):
        """FR-031, research R7 — coverage belongs to the outcome table, never to the currency report."""
        with stack("1.3.1", "1.3.1", integrations=self.BOTH, default_integration="kiro-cli",
                   registered_agents=["kiro-cli"], cover_effect=True) as path:
            _, out = run(["version"])
            self.assertNotIn("Agent coverage", out)
            rows = [line for line in out.splitlines() if _is_component_row(line)]
            self.assertEqual(len(rows), 4)

    def test_a_failed_activation_fails_the_run(self):
        """An attempted coverage step that failed is a failure, like any other attempted component."""
        with stack("1.3.1", "1.3.1", integrations=self.BOTH, default_integration="kiro-cli",
                   registered_agents=["kiro-cli"], cover_effect=True,
                   use_fails=("claude",)) as path:
            code, out = run(["update", "--yes"])
            self.assertEqual(code, cli.EXIT_DELEGATION)
            self.assertIn("Agent coverage", out)
            self.assertEqual(_default_of(path), "kiro-cli")

    def test_a_failed_restore_names_the_recovery_command(self):
        """FR-034, SC-008."""
        with stack("1.3.1", "1.3.1", integrations=self.BOTH, default_integration="kiro-cli",
                   registered_agents=["kiro-cli"], cover_effect=True,
                   use_fails=("kiro-cli",)) as path:
            code, out = run(["update", "--yes"])
            self.assertEqual(code, cli.EXIT_DELEGATION)
            self.assertIn("Could not set the default integration back to kiro-cli", out)
            self.assertIn("specify integration use kiro-cli", out)

    def test_the_closing_line_does_not_claim_completeness_after_a_decline(self):
        """The same restraint the declined-overwrite path already observes."""
        with stack("1.0.0", "1.3.1", integrations=self.BOTH, default_integration="kiro-cli",
                   registered_agents=["kiro-cli"], cover_effect=True) as path:
            with mock.patch("sys.stdin.isatty", return_value=True), \
                    mock.patch.object(extension, "delegate_update",
                                      side_effect=moving_manifest(path)), \
                    mock.patch.object(ui, "confirm", side_effect=[True, False]):
                code, out = run(["update"])
            self.assertEqual(code, cli.EXIT_OK)
            self.assertNotIn("Everything that needed updating was updated", out)
            self.assertIn("Everything else was updated", out)


def _default_of(path):
    return json.loads((Path(path) / ".specify" / "integration.json")
                      .read_text(encoding="utf-8")).get("default_integration")


def _registered(path):
    data = json.loads((Path(path) / ".specify" / "extensions" / ".registry")
                      .read_text(encoding="utf-8"))
    return sorted(data["extensions"]["spectra"]["registered_commands"])


if __name__ == "__main__":
    unittest.main()
