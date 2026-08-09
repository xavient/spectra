"""`spectra version` and `spectra update` — staleness, and the one-command fix (User Story 3).

The exit-code contract is the part worth defending: every verdict exits 0 because the command answered
the question it was asked. Non-zero means it could not answer, which is what makes `spectra version`
safe to drop into a shell without `|| true`.
"""

from __future__ import annotations

import contextlib
import io
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import helpers as h  # noqa: E402
from spectra_cli import cli, extension  # noqa: E402


def run(argv):
    buffer = io.StringIO()
    try:
        with contextlib.redirect_stdout(buffer):
            code = cli.main(argv)
    except SystemExit as exc:  # pragma: no cover
        code = exc.code
    return code, buffer.getvalue()


@contextlib.contextmanager
def project_at(installed, published="1.3.1", **project_kwargs):
    """A project with `installed` agents, against a published `published`."""
    with h.serve_roster(manifest_version=published) as base, h.raw_base(base):
        with h.temp_project(installed, **project_kwargs) as path, h.cwd(path):
            yield path


class Verdicts(unittest.TestCase):
    def test_equal_versions_report_up_to_date(self):
        with project_at("1.3.1", "1.3.1"):
            code, out = run(["version"])
        self.assertEqual(code, cli.EXIT_OK)
        self.assertIn("up to date", out)

    def test_an_older_install_reports_both_versions_and_names_the_fix(self):
        with project_at("1.0.0", "1.3.1"):
            code, out = run(["version"])
        self.assertEqual(code, cli.EXIT_OK)
        self.assertIn("1.0.0", out)
        self.assertIn("1.3.1", out)
        self.assertIn("spectra update", out)

    def test_a_newer_install_reports_ahead_and_offers_no_update(self):
        with project_at("9.9.9", "1.3.1"):
            code, out = run(["version"])
        self.assertEqual(code, cli.EXIT_OK)
        self.assertIn("ahead of what is published", out)
        self.assertNotIn("Update them with", out)

    def test_every_verdict_exits_zero(self):
        """FR-032a: a delivered verdict is a success, whatever the verdict says."""
        for installed in ("1.3.1", "1.0.0", "9.9.9"):
            with project_at(installed, "1.3.1"):
                code, _ = run(["version"])
            self.assertEqual(code, cli.EXIT_OK, installed)

    def test_it_distinguishes_the_extension_version_from_the_tools_own(self):
        """Two version numbers exist; the output must say which one it just reported."""
        with project_at("1.3.1", "1.3.1"):
            _, out = run(["version"])
        self.assertIn("spectra cli version", out)


class CannotAnswer(unittest.TestCase):
    def test_an_unreachable_published_version_exits_three_without_implying_currency(self):
        with h.raw_base(h.UNREACHABLE_BASE), h.temp_project("1.3.1") as path, h.cwd(path):
            code, out = run(["version"])
        self.assertEqual(code, cli.EXIT_UNREACHABLE)
        self.assertNotIn("up to date", out)
        self.assertIn("could not be fetched", out)

    def test_it_still_reports_what_is_installed_when_the_published_version_is_unknown(self):
        with h.raw_base(h.UNREACHABLE_BASE), h.temp_project("1.2.3") as path, h.cwd(path):
            _, out = run(["version"])
        self.assertIn("1.2.3", out)

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

    def test_the_bad_state_messages_all_differ(self):
        lines = []
        for kwargs in (dict(is_project=False), dict(installed_version=None), dict(incomplete=True)):
            with h.temp_project(**kwargs) as path, h.cwd(path):
                _, out = run(["version"])
            lines.append(out.strip().splitlines()[0])
        self.assertEqual(len(set(lines)), 3, lines)

    def test_no_network_call_is_made_when_the_project_state_is_wrong(self):
        """Fetching before checking state would make a local mistake look like a network problem."""
        with h.temp_project(installed_version=None) as path, h.cwd(path):
            with mock.patch.object(extension, "published_version") as published:
                run(["version"])
        published.assert_not_called()


class FromASubdirectory(unittest.TestCase):
    def test_the_verdict_is_the_same_from_root_and_from_a_nested_folder(self):
        with h.serve_roster(manifest_version="1.3.1") as base, h.raw_base(base):
            with h.temp_project("1.0.0", subdir="a/b") as nested:
                with h.cwd(nested):
                    nested_result = run(["version"])
                with h.cwd(nested.parents[1]):
                    root_result = run(["version"])
        self.assertEqual(nested_result, root_result)


class Update(unittest.TestCase):
    def test_an_out_of_date_install_delegates_to_spec_kit(self):
        with project_at("1.0.0", "1.3.1"):
            with mock.patch.object(extension, "delegate_update", return_value=0) as delegated:
                code, out = run(["update"])
        delegated.assert_called_once_with()
        self.assertEqual(code, cli.EXIT_OK)
        self.assertIn("Updating agents", out)

    def test_an_already_current_install_changes_nothing(self):
        """The spec leaves forced reinstall open; a no-op with a message is the chosen answer."""
        with project_at("1.3.1", "1.3.1"):
            with mock.patch.object(extension, "delegate_update") as delegated:
                code, out = run(["update"])
        delegated.assert_not_called()
        self.assertEqual(code, cli.EXIT_OK)
        self.assertIn("already up to date", out)

    def test_an_install_ahead_of_published_changes_nothing(self):
        with project_at("9.9.9", "1.3.1"):
            with mock.patch.object(extension, "delegate_update") as delegated:
                code, out = run(["update"])
        delegated.assert_not_called()
        self.assertEqual(code, cli.EXIT_OK)
        self.assertIn("ahead of published", out)

    def test_an_incomplete_install_is_repaired_without_a_version_comparison(self):
        """There is no readable version to compare, so update is the documented repair path."""
        with h.temp_project(incomplete=True) as path, h.cwd(path):
            with mock.patch.object(extension, "published_version") as published, \
                 mock.patch.object(extension, "delegate_update", return_value=0) as delegated:
                code, out = run(["update"])
        published.assert_not_called()
        delegated.assert_called_once()
        self.assertEqual(code, cli.EXIT_OK)
        self.assertIn("Repairing", out)

    def test_an_unreachable_published_version_makes_no_changes(self):
        with h.raw_base(h.UNREACHABLE_BASE), h.temp_project("1.0.0") as path, h.cwd(path):
            with mock.patch.object(extension, "delegate_update") as delegated:
                code, out = run(["update"])
        delegated.assert_not_called()
        self.assertEqual(code, cli.EXIT_UNREACHABLE)
        self.assertIn("nothing was changed", out)

    def test_a_failing_spec_kit_is_reported_as_a_delegation_failure(self):
        with project_at("1.0.0", "1.3.1"):
            with mock.patch.object(extension, "delegate_update", return_value=2):
                code, out = run(["update"])
        self.assertEqual(code, cli.EXIT_DELEGATION)
        self.assertIn("unchanged", out)

    def test_a_missing_spec_kit_is_explained_and_nothing_changes(self):
        with project_at("1.0.0", "1.3.1"):
            with mock.patch.object(extension, "delegate_update",
                                   side_effect=extension.DelegationError("Spec Kit not found")):
                code, out = run(["update"])
        self.assertEqual(code, cli.EXIT_DELEGATION)
        self.assertIn("Spec Kit not found", out)

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

    def test_an_interrupted_delegation_returns_the_conventional_code(self):
        with project_at("1.0.0", "1.3.1"):
            with mock.patch.object(extension, "delegate_update", return_value=130):
                code, _ = run(["update"])
        self.assertEqual(code, 130)

    def test_the_reported_version_after_an_update_is_re_read_from_the_project(self):
        """The new version comes from the manifest Spec Kit just wrote, not from what we expected."""
        with h.serve_roster(manifest_version="1.3.1") as base, h.raw_base(base):
            with h.temp_project("1.0.0") as path, h.cwd(path):
                manifest = path / ".specify" / "extensions" / "spectra" / "extension.yml"

                def fake_update():
                    manifest.write_text(h.manifest_yaml("1.3.1"), encoding="utf-8")
                    return 0

                with mock.patch.object(extension, "delegate_update", side_effect=fake_update):
                    code, out = run(["update"])
        self.assertEqual(code, cli.EXIT_OK)
        self.assertIn("1.3.1", out)


class TheLoopCloses(unittest.TestCase):
    def test_the_command_named_by_version_is_the_one_that_fixes_it(self):
        """SC-007: told out of date, fixed in one command, and that command was named."""
        with h.serve_roster(manifest_version="1.3.1") as base, h.raw_base(base):
            with h.temp_project("1.0.0") as path, h.cwd(path):
                manifest = path / ".specify" / "extensions" / "spectra" / "extension.yml"
                _, before = run(["version"])
                self.assertIn("spectra update", before)

                def fake_update():
                    manifest.write_text(h.manifest_yaml("1.3.1"), encoding="utf-8")
                    return 0

                with mock.patch.object(extension, "delegate_update", side_effect=fake_update):
                    run(["update"])
                code, after = run(["version"])
        self.assertEqual(code, cli.EXIT_OK)
        self.assertIn("up to date", after)


if __name__ == "__main__":
    unittest.main()
