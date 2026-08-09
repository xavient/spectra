"""`spectra check` — is Spectra available here? (User Story 2)

Four states must produce four *different sentences*, not one sentence with a swapped noun, because the
remedy differs in each case. SC-009 is what these tests measure.
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
from spectra_cli import cli  # noqa: E402


def run(argv):
    buffer = io.StringIO()
    try:
        with contextlib.redirect_stdout(buffer):
            code = cli.main(argv)
    except SystemExit as exc:  # pragma: no cover
        code = exc.code
    return code, buffer.getvalue()


class States(unittest.TestCase):
    def test_installed_reports_success_with_the_version(self):
        with h.temp_project("1.3.1") as path, h.cwd(path):
            code, out = run(["check"])
        self.assertEqual(code, cli.EXIT_OK)
        self.assertIn("installed here", out)
        self.assertIn("1.3.1", out)

    def test_not_a_spec_kit_project_names_specify_init(self):
        with h.temp_project(is_project=False) as path, h.cwd(path):
            code, out = run(["check"])
        self.assertEqual(code, cli.EXIT_PROJECT_STATE)
        self.assertIn("not a Spec Kit project", out)
        self.assertIn("specify init", out)

    def test_an_incomplete_install_is_named_as_such_and_points_at_update(self):
        with h.temp_project(incomplete=True) as path, h.cwd(path):
            code, out = run(["check"])
        self.assertEqual(code, cli.EXIT_PROJECT_STATE)
        self.assertIn("interrupted", out)
        self.assertIn("spectra update", out)

    def test_not_installed_offers_to_install(self):
        with h.temp_project(installed_version=None) as path, h.cwd(path):
            with mock.patch.object(sys.stdin, "isatty", return_value=False):
                code, out = run(["check"])
        self.assertEqual(code, cli.EXIT_DECLINED)
        self.assertIn("not installed in this project", out)
        self.assertIn("spectra install", out)

    def test_the_four_states_produce_four_different_first_lines(self):
        """SC-009, stated as a test: four distinguishable, actionable messages."""
        first_lines = []
        cases = [dict(is_project=False), dict(installed_version=None),
                 dict(incomplete=True), dict(installed_version="1.3.1")]
        for kwargs in cases:
            with h.temp_project(**kwargs) as path, h.cwd(path):
                with mock.patch.object(sys.stdin, "isatty", return_value=False):
                    _, out = run(["check"])
            first_lines.append(out.strip().splitlines()[0])
        self.assertEqual(len(set(first_lines)), 4, first_lines)


class TheInstallOffer(unittest.TestCase):
    def test_declining_changes_nothing_and_exits_one(self):
        with h.temp_project(installed_version=None) as path, h.cwd(path):
            with mock.patch.object(sys.stdin, "isatty", return_value=True), \
                 mock.patch.object(cli.ui, "confirm", return_value=False), \
                 mock.patch.object(cli, "cmd_install") as install:
                code, out = run(["check"])
        install.assert_not_called()
        self.assertEqual(code, cli.EXIT_DECLINED)
        self.assertIn("Nothing was changed", out)

    def test_accepting_runs_the_existing_install_flow(self):
        """FR-029: reuse the install flow rather than reimplementing any of it."""
        with h.temp_project(installed_version=None) as path, h.cwd(path):
            with mock.patch.object(sys.stdin, "isatty", return_value=True), \
                 mock.patch.object(cli.ui, "confirm", return_value=True), \
                 mock.patch.object(cli, "cmd_install", return_value=0) as install:
                code, _ = run(["check"])
        install.assert_called_once()
        self.assertEqual(code, cli.EXIT_OK)

    def test_yes_accepts_without_prompting(self):
        with h.temp_project(installed_version=None) as path, h.cwd(path):
            with mock.patch.object(cli.ui, "confirm") as confirm, \
                 mock.patch.object(cli, "cmd_install", return_value=0):
                code, _ = run(["check", "--yes"])
        confirm.assert_not_called()
        self.assertEqual(code, cli.EXIT_OK)

    def test_a_failed_install_is_reported_as_a_delegation_failure(self):
        with h.temp_project(installed_version=None) as path, h.cwd(path):
            with mock.patch.object(cli, "cmd_install", return_value=1):
                code, _ = run(["check", "--yes"])
        self.assertEqual(code, cli.EXIT_DELEGATION)

    def test_a_non_interactive_session_does_not_prompt(self):
        """Prompting where nobody can answer would hang a CI job."""
        with h.temp_project(installed_version=None) as path, h.cwd(path):
            with mock.patch.object(sys.stdin, "isatty", return_value=False), \
                 mock.patch.object(cli.ui, "confirm") as confirm:
                code, _ = run(["check"])
        confirm.assert_not_called()
        self.assertEqual(code, cli.EXIT_DECLINED)


class FromASubdirectory(unittest.TestCase):
    def test_it_reports_on_the_enclosing_project(self):
        """FR-040: the command is about the project, not about the folder you happen to stand in."""
        with h.temp_project("1.3.1", subdir="a/b/c") as nested, h.cwd(nested):
            code, out = run(["check"])
        self.assertEqual(code, cli.EXIT_OK)
        self.assertIn("installed here", out)

    def test_root_and_subdirectory_give_the_same_verdict(self):
        with h.temp_project("1.3.1", subdir="deep/deeper") as nested:
            with h.cwd(nested):
                nested_code, _ = run(["check"])
            with h.cwd(nested.parents[1]):
                root_code, _ = run(["check"])
        self.assertEqual(nested_code, root_code)


class NoNetwork(unittest.TestCase):
    def test_check_never_touches_the_network(self):
        """Answering "is it here?" is a local question; it must work offline."""
        with h.raw_base(h.UNREACHABLE_BASE), h.temp_project("1.3.1") as path, h.cwd(path):
            code, _ = run(["check"])
        self.assertEqual(code, cli.EXIT_OK)


if __name__ == "__main__":
    unittest.main()
