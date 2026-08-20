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

    def test_each_removed_flag_names_a_live_replacement(self):
        """The ambiguity between two readings is why the flags went away in 5.0.0.

        6.0.0 settled that ambiguity by retiring the tool-scoped pair, so `--version` and `--update`
        now have exactly one answer each. `--uninstall` still has two, because removing a project's
        agents and removing the machine's command remain genuinely different actions.
        """
        expected = {
            "--version": ("spectra version",),
            "-V": ("spectra version",),
            "--update": ("spectra update",),
            "--uninstall": ("spectra uninstall", "spectra cli uninstall"),
        }
        for flag, replacements in expected.items():
            _, out = run([flag])
            for replacement in replacements:
                self.assertIn(replacement, out, flag)

    def test_no_removed_flag_points_at_a_retired_command(self):
        """A replacement that does not exist is worse than no replacement at all."""
        for flag in ("--version", "-V", "--update"):
            _, out = run([flag])
            self.assertNotIn("spectra cli version", out, flag)
            self.assertNotIn("spectra cli update", out, flag)

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


class RetiredToolSubcommands(unittest.TestCase):
    """`cli version` and `cli update` were retired in 6.0.0, absorbed by the top-level commands.

    Hard-removed, following the 5.0.0 pattern for the removed flags: the action is gone, and running one
    names its replacement rather than emitting argparse's "invalid choice".
    """

    RETIRED = {"version": "spectra version", "update": "spectra update"}

    def test_each_retired_subcommand_exits_with_a_usage_error(self):
        for subcommand in self.RETIRED:
            with self.subTest(subcommand=subcommand):
                code, _ = run(["cli", subcommand])
                self.assertEqual(code, cli.EXIT_USAGE)

    def test_each_retired_subcommand_says_it_was_retired(self):
        for subcommand in self.RETIRED:
            with self.subTest(subcommand=subcommand):
                _, out = run(["cli", subcommand])
                self.assertIn("retired", out)

    def test_each_retired_subcommand_names_its_replacement(self):
        for subcommand, replacement in self.RETIRED.items():
            with self.subTest(subcommand=subcommand):
                _, out = run(["cli", subcommand])
                self.assertIn(replacement, out)

    def test_neither_performs_its_old_action(self):
        """A retirement that still did the work would be an alias, not a removal."""
        from spectra_cli import version as tool_version
        with mock.patch.object(tool_version, "resolve_latest") as resolve, \
             mock.patch.object(tool_version, "perform_update") as perform, \
             mock.patch.object(tool_version, "check_update") as checked:
            run(["cli", "version"])
            run(["cli", "update"])
        resolve.assert_not_called()
        perform.assert_not_called()
        checked.assert_not_called()

    def test_neither_reaches_the_network_or_spawns_a_subprocess(self):
        """The substantive form of "responds within a second": it does no work at all."""
        import subprocess
        with mock.patch.object(subprocess, "run") as spawned, \
             mock.patch.object(subprocess, "call") as called:
            run(["cli", "version"])
            run(["cli", "update"])
        spawned.assert_not_called()
        called.assert_not_called()

    def test_they_are_absent_from_the_advertised_tool_commands(self):
        advertised = " ".join(label for label, _ in cli.TOOL_COMMANDS)
        self.assertNotIn("cli version", advertised)
        self.assertNotIn("cli update", advertised)

    def test_the_help_describes_version_and_update_as_whole_stack_commands(self):
        """FR-019: the descriptions have to reflect what the commands now cover.

        Leaving them saying "the agents installed here" would understate them by three components.
        """
        described = dict(cli.PROJECT_COMMANDS)
        for verb in ("version", "update"):
            with self.subTest(verb=verb):
                self.assertIn("stack", described[verb].lower(), verb)
        # `version` names what it checks, so a reader knows before running it.
        self.assertIn("Spec Kit CLI", described["version"])
        self.assertIn("core agents", described["version"].lower())


class TheToolGroup(unittest.TestCase):
    def test_the_committed_version_matches_what_the_package_reports(self):
        """Moved off `cli version` when that retired; this asserts the same parity CI enforces."""
        from spectra_cli import version as tool_version
        self.assertEqual(tool_version.read_installed_version(),
                         h.repo_file("VERSION").read_text().strip())

    def test_cli_uninstall_dispatches_to_the_tools_own_uninstall(self):
        handler = mock.Mock(return_value=0)
        with mock.patch.dict(cli.TOOL_DISPATCH, {"uninstall": handler}):
            run(["cli", "uninstall"])
        handler.assert_called_once()

    def test_uninstall_is_the_only_surviving_tool_command(self):
        """FR-015: it is unchanged, and it is now alone."""
        self.assertEqual([label for label, _ in cli.TOOL_COMMANDS], ["cli uninstall"])

    def test_every_tool_handler_takes_one_argument(self):
        """The dispatch table holds plain references; a wrapper would mean they had drifted apart.

        Retirement handlers included — they default `args` so they can be called either way.
        """
        import inspect
        for name, handler in cli.TOOL_DISPATCH.items():
            parameters = list(inspect.signature(handler).parameters)
            self.assertEqual(parameters, ["args"], name)

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
        self.assertIn("act on the Spectra stack you are standing in", out)
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

    def test_the_banner_reports_the_installed_version_outside_a_project(self):
        """Constitution VI: the CLI's own version MUST stay readable outside a Spec Kit project.

        `spectra version` reports the whole stack and so requires a project with Spectra installed —
        it cannot answer "what version is this command?" in a bare directory. Three checks need that
        answer anyway: CI's VERSION-parity assertion, the release smoke test, and the clean-room check
        that a project uninstall leaves the command intact. All three read this line, and the last one
        runs in exactly the state where `spectra version` correctly refuses. Dropping it would break
        the release procedure without failing loudly, so it is pinned here as well as in CI.
        """
        from spectra_cli import version as tool_version
        installed = tool_version.read_installed_version()
        with h.raw_base(h.UNREACHABLE_BASE), h.temp_project(is_project=False) as path, h.cwd(path):
            _, out = run(["--no-update-check"])
        self.assertIn(f"cli v{installed}", out)


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


class ForceFlag(unittest.TestCase):
    """`--force` belongs to `update` alone, and its help states the consequence (FR-028)."""

    def test_update_accepts_it(self):
        parser = cli.build_parser()
        self.assertTrue(parser.parse_args(["update", "--force"]).force)

    def test_update_without_it_leaves_the_attribute_absent(self):
        parser = cli.build_parser()
        self.assertFalse(getattr(parser.parse_args(["update"]), "force", False))

    def test_it_is_not_accepted_at_the_top_level(self):
        code, _ = run(["--force", "update"])
        self.assertEqual(code, cli.EXIT_USAGE)

    def test_it_is_not_accepted_on_other_commands(self):
        for command in ("uninstall", "check", "install", "version"):
            code, _ = run([command, "--force"])
            self.assertEqual(code, cli.EXIT_USAGE, command)

    def test_the_help_states_the_consequence_not_the_mechanism(self):
        entry = [row for row in cli.OPTIONS if row[0] == "--force"]
        self.assertEqual(len(entry), 1)
        description = entry[0][2].lower()
        self.assertIn("overwrite", description)
        self.assertIn("modified", description)

    def test_it_appears_in_the_help_panel(self):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            cli.print_help()
        self.assertIn("--force", buffer.getvalue())


if __name__ == "__main__":
    unittest.main()
