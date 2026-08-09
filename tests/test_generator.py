"""The documentation generator and its five classes of verification (User Story 4).

Every test runs against a *copy* of the real committed documents, with the generator's paths patched
into a sandbox. That way the tests assert on the structure actually shipped — markers, anchors,
headings — while never risking the working tree.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import helpers as h  # noqa: E402

DOCUMENTS = ("README.md", "AGENTS_LIST.md", "spectra/README.md",
             "agents-list.json", "spectra/extension.yml")


def _load_generator():
    """Import `tools/generate_agent_docs.py` by path — it is a script, not a package."""
    path = h.repo_file("tools", "generate_agent_docs.py")
    spec = importlib.util.spec_from_file_location("generate_agent_docs", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


@contextlib.contextmanager
def sandbox():
    """A throwaway copy of the documents the generator owns, with its paths pointed at them."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for relative in DOCUMENTS:
            destination = root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(h.repo_file(*relative.split("/")), destination)
        with mock.patch.object(gen, "REPO_ROOT", root), \
             mock.patch.object(gen, "ROSTER", root / "agents-list.json"), \
             mock.patch.object(gen, "MANIFEST", root / "spectra" / "extension.yml"):
            yield root


def run(root, argv=None):
    """Run the generator, returning (exit code, stdout + stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = gen.main(argv or [])
    return code, out.getvalue() + err.getvalue()


def snapshot(root):
    return {relative: (root / relative).read_text(encoding="utf-8") for relative in DOCUMENTS}


def edit_roster(root, mutate):
    path = root / "agents-list.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    mutate(data)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def agent_in(data, agent_id):
    for entry in data["agents"]:
        if entry["id"] == agent_id:
            return entry
    raise KeyError(agent_id)


def outside_regions(text):
    """Everything a human owns: the file with every generated region removed."""
    return re.sub(r"<!-- SPECTRA:GENERATED START.*?<!-- SPECTRA:GENERATED END id=[a-z0-9-]+ -->",
                  "", text, flags=re.S)


class CommittedStateIsCurrent(unittest.TestCase):
    def test_the_repository_as_committed_passes_check(self):
        """If this fails, someone edited a generated region by hand and did not regenerate."""
        code, out = run(None, ["--check"])
        self.assertEqual(code, 0, out)


class Determinism(unittest.TestCase):
    def test_two_consecutive_runs_produce_identical_files(self):
        """FR-016, SC-011."""
        with sandbox() as root:
            run(root)
            first = snapshot(root)
            run(root)
            self.assertEqual(snapshot(root), first)

    def test_running_on_already_current_documents_changes_nothing(self):
        with sandbox() as root:
            run(root)
            before = snapshot(root)
            code, out = run(root)
            self.assertEqual(code, 0)
            self.assertIn("already current", out)
            self.assertEqual(before, snapshot(root))


class RegionIsolation(unittest.TestCase):
    def test_hand_authored_content_outside_regions_is_byte_identical(self):
        """FR-015 — the guarantee that makes generated and hand-written content safe to interleave."""
        with sandbox() as root:
            before = {name: outside_regions(text) for name, text in snapshot(root).items()}
            run(root)
            after = {name: outside_regions(text) for name, text in snapshot(root).items()}
        self.assertEqual(before, after)

    def test_the_prose_blocks_survive_a_run_unchanged(self):
        with sandbox() as root:
            path = root / "AGENTS_LIST.md"
            before = path.read_text(encoding="utf-8")
            marker = before.index("<!-- SPECTRA:AGENT id=adr -->")
            prose_before = before[marker:before.index("## Spec Kit core agents")]
            run(root)
            after = path.read_text(encoding="utf-8")
        self.assertIn(prose_before, after)

    def test_a_marker_line_is_never_duplicated_by_a_run(self):
        with sandbox() as root:
            run(root)
            run(root)
            text = (root / "AGENTS_LIST.md").read_text(encoding="utf-8")
        self.assertEqual(text.count("SPECTRA:GENERATED START id=agents-list-roadmap"), 1)


class RegionFreshness(unittest.TestCase):
    def test_a_hand_edit_inside_a_region_fails_check_and_names_the_file(self):
        """SC-006 — the whole point of committing generated output."""
        with sandbox() as root:
            path = root / "README.md"
            path.write_text(path.read_text(encoding="utf-8")
                            .replace("| Guardrails |", "| Guardrails EDITED |", 1), encoding="utf-8")
            code, out = run(root, ["--check"])
        self.assertEqual(code, 1)
        self.assertIn("README.md", out)
        self.assertIn("does not match agents-list.json", out)

    def test_a_roster_change_without_regeneration_fails_check(self):
        with sandbox() as root:
            edit_roster(root, lambda d: agent_in(d, "gdpr").update(title="Renamed In Roster Only"))
            code, out = run(root, ["--check"])
        self.assertEqual(code, 1)
        self.assertIn("README.md", out)

    def test_check_never_writes(self):
        with sandbox() as root:
            edit_roster(root, lambda d: agent_in(d, "gdpr").update(title="Not Written"))
            before = snapshot(root)
            run(root, ["--check"])
            self.assertEqual(before, snapshot(root))


class ProseAnchors(unittest.TestCase):
    def test_a_shipped_agent_without_a_prose_block_fails_and_names_it(self):
        """FR-018 — the safety net that lets the prose stay hand-authored."""
        with sandbox() as root:
            path = root / "AGENTS_LIST.md"
            path.write_text(path.read_text(encoding="utf-8")
                            .replace("<!-- SPECTRA:AGENT id=adr -->", "", 1), encoding="utf-8")
            code, out = run(root, ["--check"])
        self.assertEqual(code, 1)
        self.assertIn("'adr'", out)
        self.assertIn("no prose block", out)

    def test_an_orphan_prose_block_fails_and_names_it(self):
        with sandbox() as root:
            path = root / "AGENTS_LIST.md"
            path.write_text(path.read_text(encoding="utf-8")
                            + "\n<!-- SPECTRA:AGENT id=not-a-real-agent -->\n### Ghost\n",
                            encoding="utf-8")
            code, out = run(root, ["--check"])
        self.assertEqual(code, 1)
        self.assertIn("not-a-real-agent", out)
        self.assertIn("not in the roster", out)

    def test_a_prose_block_for_a_planned_agent_fails(self):
        with sandbox() as root:
            path = root / "AGENTS_LIST.md"
            path.write_text(path.read_text(encoding="utf-8")
                            + "\n<!-- SPECTRA:AGENT id=gdpr -->\n### Early\n", encoding="utf-8")
            code, out = run(root, ["--check"])
        self.assertEqual(code, 1)
        self.assertIn("not listed as shipped", out)

    def test_a_duplicated_prose_anchor_fails(self):
        with sandbox() as root:
            path = root / "AGENTS_LIST.md"
            path.write_text(path.read_text(encoding="utf-8")
                            + "\n<!-- SPECTRA:AGENT id=brd -->\n### Again\n", encoding="utf-8")
            code, out = run(root, ["--check"])
        self.assertEqual(code, 1)
        self.assertIn("more than once", out)

    def test_writing_mode_also_reports_a_missing_prose_block(self):
        """A maintainer should learn this at their desk, not from CI."""
        with sandbox() as root:
            path = root / "AGENTS_LIST.md"
            path.write_text(path.read_text(encoding="utf-8")
                            .replace("<!-- SPECTRA:AGENT id=brd -->", "", 1), encoding="utf-8")
            code, out = run(root)
        self.assertEqual(code, 1)
        self.assertIn("'brd'", out)


class TitleContainment(unittest.TestCase):
    def test_a_drifted_heading_in_the_extension_readme_fails(self):
        """FR-018a — the check that closes the gap the analysis found."""
        with sandbox() as root:
            path = root / "spectra" / "README.md"
            path.write_text(path.read_text(encoding="utf-8")
                            .replace("GitHub (PR)", "GitHub PR delivery"), encoding="utf-8")
            code, out = run(root, ["--check"])
        self.assertEqual(code, 1)
        self.assertIn("create-pr", out)
        self.assertIn("spectra/README.md", out)

    def test_renaming_a_title_in_the_roster_alone_is_caught(self):
        with sandbox() as root:
            edit_roster(root, lambda d: agent_in(d, "brd").update(title="Requirements Doc Writer"))
            run(root)  # regenerate the tables, but the hand-written heading still says the old name
            code, out = run(root, ["--check"])
        self.assertEqual(code, 1)
        self.assertIn("Requirements Doc Writer", out)


class ManifestAgreement(unittest.TestCase):
    def test_a_command_mismatch_fails_and_names_both_sides(self):
        with sandbox() as root:
            edit_roster(root, lambda d: agent_in(d, "adr").update(command="speckit.spectra.wrong"))
            code, out = run(root, ["--check"])
        self.assertEqual(code, 1)
        self.assertIn("speckit.spectra.wrong", out)
        self.assertIn("speckit.spectra.adr", out)

    def test_an_agent_the_manifest_does_not_register_fails(self):
        def add(data):
            data["agents"].append({
                "id": "invented", "title": "Invented Agent",
                "description": "Not registered anywhere.", "status": "available",
                "phase": data["phases"][0]["id"], "type": "add-on", "provider": "spectra",
                "command": "speckit.spectra.invented",
            })
        with sandbox() as root:
            edit_roster(root, add)
            code, out = run(root, ["--check"])
        self.assertEqual(code, 1)
        self.assertIn("speckit.spectra.invented", out)
        self.assertIn("does not register", out)

    def test_a_command_the_roster_omits_fails(self):
        with sandbox() as root:
            edit_roster(root, lambda d: d["agents"].remove(agent_in(d, "adr")))
            code, out = run(root, ["--check"])
        self.assertEqual(code, 1)
        self.assertIn("speckit.spectra.adr", out)
        self.assertIn("does not list", out)

    def test_descriptions_are_deliberately_not_compared(self):
        """FR-019a — the two address different audiences, so forcing them equal makes one worse."""
        with sandbox() as root:
            edit_roster(root, lambda d: agent_in(d, "adr").update(
                description="Wording chosen for a table, not for an install-time prompt."))
            run(root)
            code, out = run(root, ["--check"])
        self.assertEqual(code, 0, out)


class MalformedMarkers(unittest.TestCase):
    def test_a_missing_end_marker_fails_and_leaves_the_file_unwritten(self):
        """FR-020 — silently skipping is how a "successful" run leaves docs stale."""
        with sandbox() as root:
            path = root / "README.md"
            broken = path.read_text(encoding="utf-8").replace(
                "<!-- SPECTRA:GENERATED END id=readme-agents-table -->", "", 1)
            path.write_text(broken, encoding="utf-8")
            code, out = run(root)
            self.assertEqual(code, 1)
            self.assertIn("README.md", out)
            self.assertIn("missing end marker", out)
            self.assertEqual(path.read_text(encoding="utf-8"), broken,
                             "a document the generator cannot parse must be left untouched")

    def test_a_missing_start_marker_fails(self):
        with sandbox() as root:
            path = root / "README.md"
            path.write_text(path.read_text(encoding="utf-8").replace(
                "<!-- SPECTRA:GENERATED START id=readme-agents-table -->", "", 1), encoding="utf-8")
            code, out = run(root)
        self.assertEqual(code, 1)
        self.assertIn("missing start marker", out)

    def test_a_duplicated_region_fails(self):
        with sandbox() as root:
            path = root / "README.md"
            text = path.read_text(encoding="utf-8")
            path.write_text(text + "\n<!-- SPECTRA:GENERATED START id=readme-agents-table -->\n"
                                   "<!-- SPECTRA:GENERATED END id=readme-agents-table -->\n",
                            encoding="utf-8")
            code, out = run(root)
        self.assertEqual(code, 1)
        self.assertIn("appears 2 times", out)

    def test_an_unknown_region_id_fails_rather_than_being_ignored(self):
        with sandbox() as root:
            path = root / "README.md"
            path.write_text(path.read_text(encoding="utf-8")
                            + "\n<!-- SPECTRA:GENERATED START id=invented-region -->\n"
                              "<!-- SPECTRA:GENERATED END id=invented-region -->\n",
                            encoding="utf-8")
            code, out = run(root)
        self.assertEqual(code, 1)
        self.assertIn("invented-region", out)

    def test_a_malformed_roster_is_reported_before_anything_is_written(self):
        with sandbox() as root:
            before = (root / "README.md").read_text(encoding="utf-8")
            (root / "agents-list.json").write_text("{not json", encoding="utf-8")
            code, out = run(root)
            self.assertEqual(code, 1)
            self.assertIn("agents-list.json", out)
            self.assertEqual((root / "README.md").read_text(encoding="utf-8"), before)


class RenameSurvives(unittest.TestCase):
    def test_a_title_change_keeping_the_id_propagates_and_still_verifies(self):
        """FR-003b and SC-005: renaming is editorial, and must not break any machinery."""
        with sandbox() as root:
            edit_roster(root, lambda d: agent_in(d, "gdpr").update(title="GDPR Readiness"))
            code, _ = run(root)
            self.assertEqual(code, 0)
            readme = (root / "README.md").read_text(encoding="utf-8")
            agents_list = (root / "AGENTS_LIST.md").read_text(encoding="utf-8")
            self.assertIn("GDPR Readiness", readme)
            self.assertIn("GDPR Readiness", agents_list)
            self.assertNotIn("GDPR Compliance", readme)
            self.assertNotIn("GDPR Compliance", agents_list)
            code, out = run(root, ["--check"])
        self.assertEqual(code, 0, out)

    def test_renaming_a_shipped_agent_keeps_its_prose_matched(self):
        with sandbox() as root:
            edit_roster(root, lambda d: agent_in(d, "domain-analyzer").update(title="Domain Inference"))
            # The hand-written headings still say the old name in spectra/README.md, which the
            # containment check reports — but the prose block itself stays matched by id.
            run(root)
            _, out = run(root, ["--check"])
        self.assertNotIn("no prose block", out)


class Renderers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from spectra_cli import roster as roster_module
        cls.roster = roster_module.load(h.repo_file("agents-list.json"), strict=True)

    def test_the_readme_table_has_one_row_per_agent(self):
        rows = [line for line in gen.render_readme_table(self.roster) if line.startswith("| ")]
        self.assertEqual(len(rows) - 2, len(self.roster.agents))  # minus header and separator

    def test_the_readme_table_names_every_spec_kit_agent_in_its_sentence(self):
        rendered = "\n".join(gen.render_readme_table(self.roster))
        for agent in self.roster.agents:
            if agent.provider == "speckit" and agent.available:
                self.assertIn(agent.title, rendered)

    def test_the_roadmap_lists_only_planned_agents(self):
        rendered = "\n".join(gen.render_roadmap(self.roster))
        for agent in self.roster.agents:
            if agent.available:
                self.assertNotIn(f"**{agent.title}**", rendered)
            else:
                self.assertIn(f"**{agent.title}**", rendered)

    def test_the_speckit_section_lists_only_spec_kit_agents(self):
        rendered = "\n".join(gen.render_speckit_core(self.roster))
        for agent in self.roster.agents:
            if agent.provider == "spectra":
                self.assertNotIn(f"### {agent.title} —", rendered)

    def test_the_claude_trigger_uses_dashes(self):
        self.assertEqual(gen._claude_trigger("speckit.spectra.adr"), "/speckit-spectra-adr")

    def test_the_extension_readme_table_lists_only_shipped_agents(self):
        rendered = "\n".join(gen.render_spectra_commands(self.roster))
        self.assertEqual(rendered.count("| `speckit."), len(self.roster.shipped()))

    def test_every_region_writes_unix_line_endings(self):
        """FR-050: a Windows checkout must not look drifted to CI."""
        for region in gen.REGIONS:
            self.assertNotIn("\r", gen.render_region(region, self.roster))


if __name__ == "__main__":
    unittest.main()
