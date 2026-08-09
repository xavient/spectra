"""The command surface: the project/tool split, and the flags that were removed (User Story 5).

One rule is being defended here: a top-level verb acts on the agents in this project, and only
`spectra cli …` acts on the tool. Everything else in this file is a consequence of it.
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


class RemovedFlags(unittest.TestCase):
    """FR-038, FR-039 — removed, not aliased, and each names its replacement."""

    def test_each_removed_flag_exits_with_a_usage_error(self):
        for flag in ("--version", "-V", "--update", "--uninstall"):
            code, _ = run([flag])
            self.assertEqual(code, cli.EXIT_USAGE, flag)

    def test_each_removed_flag_says_it_was_removed(self):
        for flag in ("--version", "-V", "--update", "--uninstall"):
            _, out = run([flag])
            self.assertIn("was removed in 5.0.0", out, flag)

    def test_each_removed_flag_names_both_replacements(self):
        """The ambiguity between the two is exactly why the flags went away."""
        expected = {
            "--version": ("spectra cli version", "spectra version"),
            "-V": ("spectra cli version", "spectra version"),
            "--update": ("spectra cli update", "spectra update"),
            "--uninstall": ("spectra cli uninstall", "spectra uninstall"),
        }
        for flag, (tool, project) in expected.items():
            _, out = run([flag])
            self.assertIn(tool, out, flag)
            self.assertIn(project, out, flag)

    def test_no_removed_flag_survives_as_an_alias(self):
        parser = cli.build_parser()
        options = set()
        for action in parser._actions:  # noqa: SLF001 - asserting on the parser's own surface
            options.update(action.option_strings)
        for flag in ("--version", "-V", "--update", "--uninstall"):
            self.assertNotIn(flag, options, f"{flag} is still defined on the parser")

    def test_a_removed_flag_is_caught_even_after_a_subcommand(self):
        code, out = run(["check", "--version"])
        self.assertEqual(code, cli.EXIT_USAGE)
        self.assertIn("was removed", out)

    def test_a_removed_flag_never_reaches_a_handler(self):
        handler = mock.Mock(return_value=0)
        with mock.patch.dict(cli.TOOL_DISPATCH, {"version": handler}):
            run(["--version"])
        handler.assert_not_called()

    def test_an_unrelated_bad_flag_still_gets_the_generic_error(self):
        """Only the three removed flags get special treatment; nothing else is special-cased."""
        code, out = run(["--not-a-real-flag"])
        self.assertEqual(code, cli.EXIT_USAGE)
        self.assertNotIn("was removed", out)


class TheToolGroup(unittest.TestCase):
    def test_cli_version_reports_the_tools_own_version_on_the_first_line(self):
        """CI compares this against the committed VERSION, so the format is load-bearing."""
        with h.raw_base(h.UNREACHABLE_BASE):
            code, out = run(["cli", "version", "--no-update-check"])
        self.assertEqual(code, cli.EXIT_OK)
        self.assertEqual(out.splitlines()[0].strip(), h.repo_file("VERSION").read_text().strip())

    def test_cli_version_matches_the_committed_version_file(self):
        from spectra_cli import version as tool_version
        self.assertEqual(tool_version.read_installed_version(),
                         h.repo_file("VERSION").read_text().strip())

    def test_cli_update_dispatches_to_the_tools_own_update(self):
        handler = mock.Mock(return_value=0)
        with mock.patch.dict(cli.TOOL_DISPATCH, {"update": handler}):
            run(["cli", "update"])
        handler.assert_called_once()

    def test_cli_uninstall_dispatches_to_the_tools_own_uninstall(self):
        handler = mock.Mock(return_value=0)
        with mock.patch.dict(cli.TOOL_DISPATCH, {"uninstall": handler}):
            run(["cli", "uninstall"])
        handler.assert_called_once()

    def test_all_three_tool_handlers_share_one_signature(self):
        """The dispatch table holds plain references; a wrapper would mean they had drifted apart."""
        import inspect
        for name, handler in cli.TOOL_DISPATCH.items():
            self.assertEqual(list(inspect.signature(handler).parameters), ["args"], name)

    def test_the_tool_group_with_no_subcommand_shows_its_own_help(self):
        code, out = run(["cli"])
        self.assertEqual(code, cli.EXIT_USAGE)
        self.assertIn("Tool commands", out)

    def test_the_tool_group_help_points_back_at_the_project_commands(self):
        _, out = run(["cli"])
        self.assertIn("spectra --help", out)

    def test_an_unknown_tool_subcommand_is_a_usage_error(self):
        code, _ = run(["cli", "nonsense"])
        self.assertEqual(code, cli.EXIT_USAGE)


class TheSplitIsEvident(unittest.TestCase):
    """FR-043, SC-008 — a first-time reader can tell which commands act on what."""

    def test_the_help_screen_has_a_project_panel_and_a_tool_panel(self):
        _, out = run(["--help"])
        self.assertIn("Project commands", out)
        self.assertIn("Tool commands", out)

    def test_the_panel_titles_say_what_each_group_acts_on(self):
        _, out = run(["--help"])
        self.assertIn("act on the agents in this project", out)
        self.assertIn("act on the spectra command itself", out)

    def test_every_project_command_is_listed_in_the_project_panel(self):
        _, out = run(["--help"])
        for name, _ in cli.PROJECT_COMMANDS:
            self.assertIn(name, out)

    def test_every_tool_command_is_listed_under_cli(self):
        _, out = run(["--help"])
        for label, _ in cli.TOOL_COMMANDS:
            self.assertIn(label, out)

    def test_no_top_level_verb_acts_on_the_tool(self):
        """FR-037 stated as a test: the two dispatch tables must not overlap in intent."""
        self.assertEqual(set(cli.PROJECT_DISPATCH) & {"cli"}, set())
        for name in cli.PROJECT_DISPATCH:
            self.assertNotIn(name, ("cli",))
        self.assertEqual(sorted(cli.TOOL_DISPATCH), ["uninstall", "update", "version"])

    def test_the_project_and_tool_command_names_do_not_collide_at_one_level(self):
        project_names = {name for name, _ in cli.PROJECT_COMMANDS}
        tool_names = {label.split()[1] for label, _ in cli.TOOL_COMMANDS}
        self.assertTrue(tool_names <= {"version", "update", "uninstall"})
        # They deliberately share words — that is why the tool ones live one level down.
        self.assertTrue(tool_names & project_names)


class BareCommand(unittest.TestCase):
    """FR-047 — an orientation step, not a request to modify the current folder."""

    def test_it_exits_zero_and_points_at_help(self):
        with h.temp_project(is_project=False) as path, h.cwd(path):
            code, out = run([])
        self.assertEqual(code, cli.EXIT_OK)
        self.assertIn("spectra --help", out)

    def test_it_writes_nothing_into_the_current_directory(self):
        with h.temp_project(is_project=False) as path, h.cwd(path):
            run([])
            self.assertEqual(list(path.iterdir()), [])

    def test_it_does_not_reach_the_network(self):
        with h.raw_base(h.UNREACHABLE_BASE), h.temp_project(is_project=False) as path, h.cwd(path):
            code, _ = run(["--no-update-check"])
        self.assertEqual(code, cli.EXIT_OK)


class SharedFlags(unittest.TestCase):
    def test_yes_is_accepted_before_or_after_a_subcommand(self):
        parser = cli.build_parser()
        self.assertTrue(parser.parse_args(["--yes", "check"]).yes)
        self.assertTrue(parser.parse_args(["check", "--yes"]).yes)
        self.assertFalse(parser.parse_args(["check"]).yes)

    def test_yes_survives_into_the_tool_group(self):
        parser = cli.build_parser()
        self.assertTrue(parser.parse_args(["cli", "uninstall", "--yes"]).yes)
        self.assertTrue(parser.parse_args(["--yes", "cli", "uninstall"]).yes)

    def test_no_update_check_is_accepted_on_either_side(self):
        parser = cli.build_parser()
        self.assertTrue(parser.parse_args(["--no-update-check", "cli", "version"]).no_update_check)
        self.assertTrue(parser.parse_args(["cli", "version", "--no-update-check"]).no_update_check)

    def test_help_on_a_subcommand_shows_the_help_screen(self):
        code, out = run(["check", "--help"])
        self.assertEqual(code, cli.EXIT_OK)
        self.assertIn("Project commands", out)


class ExitCodes(unittest.TestCase):
    def test_the_documented_codes_are_all_distinct(self):
        codes = [cli.EXIT_OK, cli.EXIT_DECLINED, cli.EXIT_USAGE, cli.EXIT_UNREACHABLE,
                 cli.EXIT_DELEGATION, cli.EXIT_PROJECT_STATE]
        self.assertEqual(len(codes), len(set(codes)))

    def test_usage_errors_keep_argparses_conventional_code(self):
        self.assertEqual(cli.EXIT_USAGE, 2)

    def test_an_interrupt_returns_the_conventional_code(self):
        with mock.patch.object(cli, "build_parser", side_effect=KeyboardInterrupt):
            code, _ = run(["check"])
        self.assertEqual(code, 130)


if __name__ == "__main__":
    unittest.main()
