"""Project discovery and the four installation states (FR-040, FR-044, FR-045).

The four states exist because a user needs a different sentence and a different remedy for each.
`INCOMPLETE` is the one worth defending: an extension folder left half-written by an interrupted
install is neither installed nor absent, and reporting it as either would be a lie.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import helpers as h  # noqa: E402
from spectra_cli import project  # noqa: E402


class States(unittest.TestCase):
    def test_no_specify_directory_is_not_a_project(self):
        with h.temp_project(is_project=False) as path, h.cwd(path):
            state = project.classify()
        self.assertEqual(state.state, project.NOT_A_PROJECT)
        self.assertIsNone(state.project_root)
        self.assertFalse(state.is_project)

    def test_a_project_without_the_extension_folder_is_not_installed(self):
        with h.temp_project(installed_version=None) as path, h.cwd(path):
            state = project.classify()
        self.assertEqual(state.state, project.NOT_INSTALLED)
        self.assertTrue(state.is_project)
        self.assertFalse(state.is_installed)

    def test_a_folder_with_no_readable_version_is_incomplete(self):
        with h.temp_project(incomplete=True) as path, h.cwd(path):
            state = project.classify()
        self.assertEqual(state.state, project.INCOMPLETE)
        self.assertIsNone(state.installed_version)

    def test_a_manifest_present_but_unparseable_is_incomplete_not_installed(self):
        with h.temp_project(incomplete=True) as path:
            manifest = path / ".specify" / "extensions" / "spectra" / "extension.yml"
            manifest.write_text('extension:\n  id: "spectra"\n', encoding="utf-8")
            with h.cwd(path):
                state = project.classify()
        self.assertEqual(state.state, project.INCOMPLETE)

    def test_a_readable_manifest_is_installed_and_reports_its_version(self):
        with h.temp_project("1.2.3") as path, h.cwd(path):
            state = project.classify()
        self.assertEqual(state.state, project.INSTALLED)
        self.assertEqual(state.installed_version, "1.2.3")
        self.assertTrue(state.is_installed)

    def test_incomplete_does_not_count_as_installed(self):
        """Callers branch on `is_installed`; a half-written folder must not slip through it."""
        with h.temp_project(incomplete=True) as path, h.cwd(path):
            self.assertFalse(project.classify().is_installed)

    def test_all_four_states_are_distinct_values(self):
        """SC-009 needs four distinguishable outcomes, so the constants must not collide."""
        values = {project.NOT_A_PROJECT, project.NOT_INSTALLED,
                  project.INCOMPLETE, project.INSTALLED}
        self.assertEqual(len(values), 4)


class Discovery(unittest.TestCase):
    def test_the_project_root_is_found_from_a_nested_subdirectory(self):
        with h.temp_project("1.3.1", subdir="a/b/c") as nested, h.cwd(nested):
            state = project.classify()
        self.assertEqual(state.state, project.INSTALLED)
        self.assertEqual(state.installed_version, "1.3.1")

    def test_a_subdirectory_resolves_to_the_same_root_as_the_project_top(self):
        """FR-040 and SC-012: running from anywhere inside the project gives one answer."""
        with h.temp_project("1.3.1", subdir="deep/deeper") as nested:
            root = nested.parents[1]
            with h.cwd(nested):
                from_nested = project.classify()
            with h.cwd(root):
                from_root = project.classify()
        self.assertEqual(from_nested.state, from_root.state)
        self.assertEqual(from_nested.project_root, from_root.project_root)
        self.assertEqual(from_nested.installed_version, from_root.installed_version)

    def test_find_project_root_accepts_an_explicit_start(self):
        with h.temp_project("1.3.1", subdir="x/y") as nested:
            # Compared resolved: discovery resolves symlinks so the parent walk is reliable, and on
            # macOS the temp directory sits under /var, itself a symlink to /private/var.
            self.assertEqual(project.find_project_root(nested), nested.parents[1].resolve())

    def test_find_project_root_returns_none_outside_a_project(self):
        with h.temp_project(is_project=False) as path:
            # A temp dir has no `.specify/` anywhere beneath the filesystem root.
            self.assertIsNone(project.find_project_root(path))

    def test_extension_dir_is_none_outside_a_project(self):
        with h.temp_project(is_project=False) as path, h.cwd(path):
            self.assertIsNone(project.classify().extension_dir)

    def test_extension_dir_points_at_the_installed_folder(self):
        with h.temp_project("1.3.1") as path, h.cwd(path):
            state = project.classify()
        self.assertEqual(state.extension_dir.name, "spectra")
        self.assertTrue(str(state.extension_dir).endswith(str(project.EXTENSION_DIR)))


if __name__ == "__main__":
    unittest.main()
