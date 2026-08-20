"""Reading extension versions without a YAML parser, and delegating to Spec Kit.

The version scan is the risky part of holding the zero-dependency line, so it is tested against the
real manifest shape and against every way a manifest can fail to yield a version.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import helpers as h  # noqa: E402
from spectra_cli import extension, net  # noqa: E402


class VersionScan(unittest.TestCase):
    def test_reads_the_version_from_the_real_committed_manifest(self):
        """If Spec Kit ever changes the manifest shape, this is the test that notices."""
        found = extension.read_manifest_version(h.repo_file("spectra", "extension.yml"))
        self.assertIsNotNone(found)
        self.assertRegex(found, r"^\d+\.\d+\.\d+$")

    def test_reads_the_version_from_a_generated_manifest(self):
        self.assertEqual(extension.parse_manifest_version(h.manifest_yaml("2.5.9")), "2.5.9")

    def test_ignores_a_version_nested_deeper_than_the_extension_block(self):
        """`requires:` and friends carry their own version keys at other indentations."""
        text = 'requires:\n  tools:\n    version: "9.9.9"\n'
        self.assertIsNone(extension.parse_manifest_version(text))

    def test_takes_the_extension_block_version_when_others_follow(self):
        text = h.manifest_yaml("1.4.0") + 'other:\n  version: "8.8.8"\n'
        self.assertEqual(extension.parse_manifest_version(text), "1.4.0")

    def test_tolerates_an_unquoted_version(self):
        self.assertEqual(extension.parse_manifest_version("extension:\n  version: 1.5.0\n"), "1.5.0")

    def test_a_manifest_with_no_version_yields_none(self):
        self.assertIsNone(extension.parse_manifest_version('extension:\n  id: "spectra"\n'))

    def test_an_empty_manifest_yields_none(self):
        self.assertIsNone(extension.parse_manifest_version(""))

    def test_a_missing_file_yields_none_rather_than_raising(self):
        self.assertIsNone(extension.read_manifest_version("/no/such/extension.yml"))

    def test_a_directory_in_place_of_the_manifest_yields_none(self):
        with h.temp_project(incomplete=True) as path:
            folder = path / ".specify" / "extensions" / "spectra"
            self.assertIsNone(extension.read_manifest_version(folder))


class PublishedVersion(unittest.TestCase):
    def test_reads_the_published_manifest(self):
        with h.serve_roster(manifest_version="3.1.4") as base, h.raw_base(base):
            self.assertEqual(extension.published_version(), "3.1.4")

    def test_an_unreachable_manifest_raises_fetch_error(self):
        with h.raw_base(h.UNREACHABLE_BASE):
            with self.assertRaises(net.FetchError):
                extension.published_version()

    def test_a_manifest_without_a_version_raises_fetch_error(self):
        files = {"spectra/extension.yml": 'extension:\n  id: "spectra"\n'}
        with h.serve(files) as base, h.raw_base(base):
            with self.assertRaises(net.FetchError) as caught:
                extension.published_version()
        self.assertIn("did not contain an extension version", str(caught.exception))


class Compare(unittest.TestCase):
    def test_older_installed_is_out_of_date(self):
        self.assertEqual(extension.compare("1.3.0", "1.3.1"), extension.OUT_OF_DATE)

    def test_equal_is_up_to_date(self):
        self.assertEqual(extension.compare("1.3.1", "1.3.1"), extension.UP_TO_DATE)

    def test_newer_installed_is_ahead(self):
        self.assertEqual(extension.compare("2.0.0", "1.3.1"), extension.AHEAD)

    def test_comparison_is_component_wise_not_lexical(self):
        self.assertEqual(extension.compare("1.10.0", "1.9.0"), extension.AHEAD)

    def test_the_three_verdicts_are_distinct(self):
        self.assertEqual(len({extension.UP_TO_DATE, extension.OUT_OF_DATE, extension.AHEAD}), 3)


class RegisteredAgents(unittest.TestCase):
    """Which agents carry Spectra's commands — and every way that can be unknowable."""

    def _read(self, registered):
        with h.temp_project("1.3.1", integration_version="0.16.5",
                                  integrations={"claude": "0.16.5"},
                                  registered_agents=registered) as path:
            return extension.registered_agents(path)

    def test_a_two_agent_map_is_returned_as_a_set(self):
        self.assertEqual(self._read(["kiro-cli", "claude"]), {"kiro-cli", "claude"})

    def test_a_one_agent_map_is_returned(self):
        self.assertEqual(self._read(["kiro-cli"]), {"kiro-cli"})

    def test_a_missing_registry_is_unknown(self):
        with h.temp_project("1.3.1", integration_version="0.16.5",
                                  integrations={"claude": "0.16.5"}) as path:
            self.assertIsNone(extension.registered_agents(path))

    def test_unreadable_json_is_unknown(self):
        self.assertIsNone(self._read(h.BAD_JSON))

    def test_an_empty_command_map_is_unknown_not_uncovered(self):
        self.assertIsNone(self._read([]))

    def test_no_spectra_entry_is_unknown(self):
        with h.temp_project("1.3.1", integration_version="0.16.5",
                                  integrations={"claude": "0.16.5"},
                                  registered_agents=["claude"]) as path:
            registry = path / ".specify" / "extensions" / ".registry"
            registry.write_text('{"schema_version": "1.0", "extensions": {"git": {}}}',
                                encoding="utf-8")
            self.assertIsNone(extension.registered_agents(path))

    def test_no_project_root_is_unknown(self):
        self.assertIsNone(extension.registered_agents(None))


class Delegation(unittest.TestCase):
    def test_update_calls_spec_kit_with_the_extension_id(self):
        with mock.patch.object(extension, "specify_available", return_value=True), \
             mock.patch("subprocess.call", return_value=0) as called:
            self.assertEqual(extension.delegate_update(), 0)
        called.assert_called_once_with(["specify", "extension", "update", "spectra"])

    def test_remove_does_not_force_by_default(self):
        """Spec Kit owns the confirmation prompt, so the default must let it prompt."""
        with mock.patch.object(extension, "specify_available", return_value=True), \
             mock.patch("subprocess.call", return_value=0) as called:
            extension.delegate_remove()
        called.assert_called_once_with(["specify", "extension", "remove", "spectra"])

    def test_remove_forces_only_when_asked(self):
        with mock.patch.object(extension, "specify_available", return_value=True), \
             mock.patch("subprocess.call", return_value=0) as called:
            extension.delegate_remove(force=True)
        called.assert_called_once_with(["specify", "extension", "remove", "spectra", "--force"])

    def test_a_missing_spec_kit_is_reported_and_nothing_is_run(self):
        with mock.patch.object(extension, "specify_available", return_value=False), \
             mock.patch("subprocess.call") as called:
            with self.assertRaises(extension.DelegationError) as caught:
                extension.delegate_update()
        called.assert_not_called()
        self.assertIn("specify", str(caught.exception))

    def test_a_failing_spec_kit_command_returns_its_exit_code(self):
        with mock.patch.object(extension, "specify_available", return_value=True), \
             mock.patch("subprocess.call", return_value=7):
            self.assertEqual(extension.delegate_update(), 7)

    def test_an_unrunnable_spec_kit_is_reported(self):
        with mock.patch.object(extension, "specify_available", return_value=True), \
             mock.patch("subprocess.call", side_effect=OSError("boom")):
            with self.assertRaises(extension.DelegationError):
                extension.delegate_remove()

    def test_interrupting_a_delegated_command_yields_the_conventional_code(self):
        with mock.patch.object(extension, "specify_available", return_value=True), \
             mock.patch("subprocess.call", side_effect=KeyboardInterrupt):
            self.assertEqual(extension.delegate_update(), 130)


if __name__ == "__main__":
    unittest.main()
