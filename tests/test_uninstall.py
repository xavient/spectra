"""`spectra uninstall` — removing the agents, keeping the tool (User Story 6).

Two choices are load-bearing and both are asserted here: the confirmation prompt stays Spec Kit's, and
uninstalling when nothing is installed is a success rather than an error.
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
from spectra_cli import cli, extension, project, version as tool_version  # noqa: E402


def run(argv):
    buffer = io.StringIO()
    try:
        with contextlib.redirect_stdout(buffer):
            code = cli.main(argv)
    except SystemExit as exc:  # pragma: no cover
        code = exc.code
    return code, buffer.getvalue()


def removes(path):
    """A fake delegation that actually removes the folder, so the after-state is real."""
    def fake(force=False):
        import shutil
        shutil.rmtree(path / ".specify" / "extensions" / "spectra")
        return 0
    return fake


class Removal(unittest.TestCase):
    def test_an_installed_extension_is_removed_through_spec_kit(self):
        with h.temp_project("1.3.1") as path, h.cwd(path):
            with mock.patch.object(extension, "delegate_remove",
                                   side_effect=removes(path)) as delegated:
                code, out = run(["uninstall"])
        delegated.assert_called_once()
        self.assertEqual(code, cli.EXIT_OK)
        self.assertIn("were removed", out)

    def test_the_project_is_left_without_the_extension(self):
        with h.temp_project("1.3.1") as path, h.cwd(path):
            with mock.patch.object(extension, "delegate_remove", side_effect=removes(path)):
                run(["uninstall"])
            self.assertEqual(project.classify().state, project.NOT_INSTALLED)

    def test_it_says_the_tool_itself_stays(self):
        with h.temp_project("1.3.1") as path, h.cwd(path):
            with mock.patch.object(extension, "delegate_remove", side_effect=removes(path)):
                _, out = run(["uninstall"])
        self.assertIn("stays installed on this machine", out)

    def test_an_incomplete_install_is_removed_too(self):
        with h.temp_project(incomplete=True) as path, h.cwd(path):
            with mock.patch.object(extension, "delegate_remove",
                                   side_effect=removes(path)) as delegated:
                code, out = run(["uninstall"])
        delegated.assert_called_once()
        self.assertEqual(code, cli.EXIT_OK)
        self.assertIn("unusable", out)


class TheConfirmationIsSpecKits(unittest.TestCase):
    """Spec Kit already prompts and already offers --force; asking twice would be worse."""

    def test_spectra_does_not_add_its_own_prompt(self):
        with h.temp_project("1.3.1") as path, h.cwd(path):
            with mock.patch.object(cli.ui, "confirm") as confirm, \
                 mock.patch.object(extension, "delegate_remove", side_effect=removes(path)):
                run(["uninstall"])
        confirm.assert_not_called()

    def test_force_is_not_passed_by_default(self):
        with h.temp_project("1.3.1") as path, h.cwd(path):
            with mock.patch.object(extension, "delegate_remove",
                                   side_effect=removes(path)) as delegated:
                run(["uninstall"])
        self.assertEqual(delegated.call_args.kwargs.get("force"), False)

    def test_yes_passes_force_through(self):
        with h.temp_project("1.3.1") as path, h.cwd(path):
            with mock.patch.object(extension, "delegate_remove",
                                   side_effect=removes(path)) as delegated:
                run(["uninstall", "--yes"])
        self.assertEqual(delegated.call_args.kwargs.get("force"), True)

    def test_declining_at_spec_kits_prompt_is_reported_as_declined(self):
        with h.temp_project("1.3.1") as path, h.cwd(path):
            with mock.patch.object(extension, "delegate_remove", return_value=1):
                code, out = run(["uninstall"])
        self.assertEqual(code, cli.EXIT_DECLINED)
        self.assertIn("nothing was removed", out)


class Idempotence(unittest.TestCase):
    def test_uninstalling_when_absent_succeeds(self):
        """The requested end state already holds — and `spectra cli uninstall` agrees."""
        with h.temp_project(installed_version=None) as path, h.cwd(path):
            with mock.patch.object(extension, "delegate_remove") as delegated:
                code, out = run(["uninstall"])
        delegated.assert_not_called()
        self.assertEqual(code, cli.EXIT_OK)
        self.assertIn("nothing to remove", out)

    def test_running_it_twice_is_safe(self):
        with h.temp_project("1.3.1") as path, h.cwd(path):
            with mock.patch.object(extension, "delegate_remove", side_effect=removes(path)):
                first, _ = run(["uninstall"])
            second, _ = run(["uninstall"])
        self.assertEqual((first, second), (cli.EXIT_OK, cli.EXIT_OK))

    def test_not_a_spec_kit_project_exits_five(self):
        with h.temp_project(is_project=False) as path, h.cwd(path):
            with mock.patch.object(extension, "delegate_remove") as delegated:
                code, out = run(["uninstall"])
        delegated.assert_not_called()
        self.assertEqual(code, cli.EXIT_PROJECT_STATE)
        self.assertIn("not a Spec Kit project", out)


class Failures(unittest.TestCase):
    def test_a_missing_spec_kit_is_explained_and_nothing_changes(self):
        with h.temp_project("1.3.1") as path, h.cwd(path):
            with mock.patch.object(extension, "delegate_remove",
                                   side_effect=extension.DelegationError("Spec Kit not found")):
                code, out = run(["uninstall"])
            self.assertEqual(project.classify().state, project.INSTALLED)
        self.assertEqual(code, cli.EXIT_DELEGATION)
        self.assertIn("Spec Kit not found", out)

    def test_success_that_leaves_the_folder_behind_is_reported_as_a_failure(self):
        """Trusting an exit code over the filesystem would report a removal that did not happen."""
        with h.temp_project("1.3.1") as path, h.cwd(path):
            with mock.patch.object(extension, "delegate_remove", return_value=0):
                code, out = run(["uninstall"])
        self.assertEqual(code, cli.EXIT_DELEGATION)
        self.assertIn("still present", out)

    def test_an_interrupted_removal_returns_the_conventional_code(self):
        with h.temp_project("1.3.1") as path, h.cwd(path):
            with mock.patch.object(extension, "delegate_remove", return_value=130):
                code, _ = run(["uninstall"])
        self.assertEqual(code, 130)


class TheToolIsUntouched(unittest.TestCase):
    """FR-035 — removing a project's agents must never reach the installed command."""

    def test_no_uv_path_is_exercised(self):
        with h.temp_project("1.3.1") as path, h.cwd(path):
            with mock.patch.object(tool_version, "perform_uninstall") as uninstall_tool, \
                 mock.patch.object(tool_version, "classify_uninstall") as classify_tool, \
                 mock.patch.object(extension, "delegate_remove", side_effect=removes(path)):
                run(["uninstall"])
        uninstall_tool.assert_not_called()
        classify_tool.assert_not_called()

    def test_the_delegated_command_targets_spec_kit_not_uv(self):
        with h.temp_project("1.3.1") as path, h.cwd(path):
            with mock.patch.object(extension, "specify_available", return_value=True), \
                 mock.patch("subprocess.call", return_value=0) as called:
                run(["uninstall"])
        argv = called.call_args.args[0]
        self.assertEqual(argv[:2], ["specify", "extension"])
        self.assertNotIn("uv", argv)


if __name__ == "__main__":
    unittest.main()
