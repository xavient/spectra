"""The `flaky-test-detector` flow, asserted against the command text that ships.

A command file is a prompt: its text *is* the implementation, so the enforceable surface is what it says.
These assertions cannot prove an agent behaves correctly at run time — that is the manual pass in
`test/README.md`. What they prove is that the rules it is supposed to follow have not been quietly
deleted, which is the regression that actually happens to prompt files.

This agent is the first Spectra command that **edits files the user wrote**, so the load-bearing
assertions are the ones that bound that: it never executes anything (including to verify a fix it just
applied), it never touches production source, it cannot "fix" a test by weakening it, and it acts only on
rows a human left in the file after reviewing it. Losing any one of those is invisible in review and
catastrophic at run time — an agent free to run the suite it just edited can iterate until green, and
iterating until green is how a test ends up asserting nothing.

Standard library only, like the rest of the suite.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import helpers as h  # noqa: E402

COMMAND = h.repo_file("spectra", "commands", "flaky-test-detector.md")
MANIFEST = h.repo_file("spectra", "extension.yml")
CANONICAL_FILE = ".specify/memory/flaky-test-analysis.md"


def text() -> str:
    return COMMAND.read_text(encoding="utf-8")


def flat() -> str:
    """Whitespace-flattened, so an assertion survives a reflow of the prose."""
    return " ".join(text().split())


class States:
    """`assertIn` against a whole command file dumps it into the failure; this prints the message only."""

    def assertStates(self, needle, haystack=None):
        hay = flat() if haystack is None else haystack
        self.assertTrue(needle in hay, "flaky-test-detector.md no longer states: " + repr(needle))

    def assertStatesAny(self, needles, haystack=None):
        hay = flat() if haystack is None else haystack
        self.assertTrue(
            any(n in hay for n in needles),
            "flaky-test-detector.md no longer states any of: " + repr(needles),
        )


class TheCommandExists(States, unittest.TestCase):
    """Registration and interface."""

    def test_the_command_file_ships(self):
        self.assertTrue(COMMAND.exists(), "spectra/commands/flaky-test-detector.md is missing")

    def test_it_has_front_matter_with_a_description(self):
        body = text()
        self.assertTrue(body.startswith("---\n"), "no YAML front matter")
        self.assertIn("description:", body.split("---")[1])

    def test_the_manifest_registers_it(self):
        manifest = MANIFEST.read_text(encoding="utf-8")
        self.assertIn('- name: "speckit.spectra.flaky-test-detector"', manifest)
        self.assertIn('file: "commands/flaky-test-detector.md"', manifest)

    def test_it_takes_the_generic_arguments_placeholder(self):
        """Principle III: agent-agnostic input, never one agent's syntax."""
        self.assertStates("$ARGUMENTS")

    def test_an_unresolvable_scope_does_not_widen_to_the_whole_tree(self):
        """A plan the developer did not ask for is a plan they will not read."""
        self.assertStates("Do not silently widen back to the whole tree")


class TheCanonicalFile(States, unittest.TestCase):
    """One file, one path, and it is inside Spec Kit's own directory (Principle VII)."""

    def test_it_names_the_canonical_path(self):
        self.assertStates(CANONICAL_FILE)

    def test_it_writes_no_other_analysis_file(self):
        """A second location would break the single-file invariant the resume flow rests on."""
        body = flat()
        for wrong in (
            "docs/flaky-test-analysis",
            ".specify/flaky-test-analysis.md",
            "flaky_test_analysis",
        ):
            self.assertNotIn(wrong, body, f"an analysis path other than the canonical one appears: {wrong}")

    def test_the_single_file_invariant_is_stated(self):
        self.assertStates("There is **exactly one** analysis file")
        self.assertStates("Never create a second file, a dated variant, or a `.bak`")

    def test_replacement_is_the_only_route_that_removes_it(self):
        self.assertStates("only** way the file is replaced is by writing a newly accepted plan")


class TheHardLimits(States, unittest.TestCase):
    """The refusals. Each of these is a rule an agent would otherwise talk itself out of."""

    def test_it_never_executes_anything(self):
        self.assertStates("Run tests, builds, or package commands")
        self.assertStatesAny(["You never run anything", "**You never run anything.**"])

    def test_it_does_not_run_the_suite_to_verify_its_own_fix(self):
        """The exception an agent is most likely to grant itself, and the one that weakens tests."""
        self.assertStates("verify a fix you just applied")
        self.assertStates("iterating until green is how tests get weakened")

    def test_it_installs_nothing_and_never_reaches_the_network(self):
        self.assertStates("Install a dependency or add a test library")
        self.assertStates("Reach the network")

    def test_it_never_commits_or_pushes(self):
        self.assertStates("Commit, stage, push, create a branch, or open a pull request")
        self.assertStates("Nothing committed")

    def test_it_never_edits_production_source(self):
        self.assertStates("Create or edit production source code")
        self.assertStates("Out of scope, always**: production source code")

    def test_it_never_edits_governance(self):
        self.assertStates("Edit the project's constitution or any governance file")

    def test_the_refusals_are_not_overridable(self):
        self.assertStates("These are not defaults that an argument can change")


class WhatIsNeverAFix(States, unittest.TestCase):
    """FR-033. Without this list, 'make the flaky test pass' has an easy degenerate solution."""

    def test_the_governing_sentence_survives(self):
        self.assertStates("A fix removes the cause of the flakiness")

    def test_every_prohibited_remedy_is_named(self):
        for remedy in (
            "deleting an assertion",
            "loosening an assertion so it passes regardless of behaviour",
            "skipping the test, or marking it expected-to-fail",
            "adding a retry wrapper or retry configuration",
            "lengthening a sleep",
        ):
            self.assertStates(remedy)

    def test_an_unfixable_row_is_left_open_rather_than_weakened(self):
        self.assertStates("you cannot fix that row. Say so and move on")

    def test_it_says_why_a_silent_test_is_worse(self):
        self.assertStates("a test that passes always and checks nothing is a worse one")


class WhatAFixMayTouch(States, unittest.TestCase):
    """FR-032 and FR-032a — the write scope, and the disclosure when a change is wider than one row."""

    def test_edits_are_confined_to_test_and_test_support_files(self):
        self.assertStates("fixtures, helpers, factories, mocks, test\nconfiguration".replace("\n", " "))

    def test_creating_a_test_support_file_is_permitted(self):
        self.assertStates("a mock with nowhere\nto live is a fix that never lands".replace("\n", " "))

    def test_adding_a_dependency_is_not(self):
        self.assertStates("**Never**: adding a dependency")

    def test_a_change_reaching_past_its_row_is_declared_twice(self):
        self.assertStates("in the run report and in an outcome entry against that\nrow".replace("\n", " "))
        self.assertStates("Never let a suite-wide change appear in the")


class TheTwoGates(States, unittest.TestCase):
    """FR-021 and FR-030. Two consents, no bypass, and declining is always safe."""

    def test_gate_one_precedes_any_write(self):
        self.assertStates("Gate 1: ask before writing anything")
        self.assertStates("No code changes at this step")

    def test_gate_two_precedes_any_edit(self):
        self.assertStates("Gate 2: ask before touching any code")

    def test_neither_gate_has_a_bypass(self):
        self.assertStates("There is no argument, flag, or phrasing that skips this gate")
        self.assertStates("No argument skips this gate either")

    def test_declining_leaves_the_tree_byte_identical(self):
        self.assertStates("byte-for-byte unchanged")
        self.assertStates("Declining\nis always safe".replace("\n", " "))

    def test_a_narrower_run_names_what_it_would_drop(self):
        self.assertStates("Name the pending rows that fall outside your new\nscope".replace("\n", " "))
        self.assertStates("Never merge two analyses into one file")


class TheFixRun(States, unittest.TestCase):
    """FR-031, FR-031a, FR-034, FR-035."""

    def test_it_re_reads_the_file_from_disk(self):
        self.assertStates("Re-read the file from disk first")

    def test_a_deleted_row_is_never_opened(self):
        self.assertStates("A row the developer deleted does not exist")

    def test_it_re_checks_the_evidence_before_editing(self):
        self.assertStates("Before each edit, re-check the evidence")
        self.assertStates("you are\nediting code the analysis never saw".replace("\n", " "))

    def test_the_re_check_is_not_a_re_analysis(self):
        self.assertStates("Do not derive a new fix for that row inside a fix run")

    def test_progress_is_checkpointed_per_item(self):
        self.assertStates("Tick it off before moving on")
        self.assertStates("Not at the end of the run")

    def test_it_says_why_batching_progress_is_wrong(self):
        self.assertStates("A file that says `0 of 7` while three")

    def test_an_unfixable_item_does_not_stop_the_run(self):
        self.assertStates("One item you\ncannot do is not a reason to stop".replace("\n", " "))

    def test_a_missing_test_is_never_swapped_for_a_similar_one(self):
        self.assertStates("**Never** edit a similarly-named test")


class TheFourStates(States, unittest.TestCase):
    """FR-006. The first act of every run, and the branch that protects a triage session."""

    def test_the_state_check_comes_first(self):
        self.assertStates("Before anything else: what state is this project in?")
        self.assertStates("on every run, before discovering suites and before analyzing anything")

    def test_all_four_branches_exist(self):
        body = text()
        for heading in (
            "## Step 1a — There is unfinished work",
            "## Step 1b — The last run finished everything",
            "## Step 1c — The file is there but you cannot read it",
        ):
            self.assertIn(heading, body, f"missing branch: {heading}")
        self.assertStates("**Absent** | No prior analysis")

    def test_resuming_does_not_re_analyze(self):
        self.assertStates("Do **not** re-analyze")
        self.assertStates("regenerating it throws that work away")

    def test_a_completed_list_is_not_replaced_without_asking(self):
        self.assertStates("Do not analyze first and ask afterwards, and do not overwrite silently")

    def test_an_unreadable_file_is_never_overwritten_silently(self):
        self.assertStates("Never overwrite an unreadable file without being asked")

    def test_developer_edits_win(self):
        self.assertStates("Their version wins over anything you wrote earlier")

    def test_a_missing_memory_directory_is_reported_not_created(self):
        self.assertStates("Do\nnot create the directory tree unannounced".replace("\n", " "))


class TheAnalysisIsHonest(States, unittest.TestCase):
    """FR-015, FR-017, FR-018, FR-020 — the rules that make the report worth reading."""

    def test_the_confidence_rubric_is_stated(self):
        for level in ("**High** | Assign when", "**Medium** |", "**Low** |"):
            self.assertStates(level.split(" |")[0])
        self.assertStates("High is unavailable without direct evidence in the test source")

    def test_confidence_is_not_a_failure_rate(self):
        self.assertStates("Never emit a percentage, a score, a flakiness index")
        self.assertStates("you have no run history", flat().lower())

    def test_it_does_not_fabricate_candidates(self):
        self.assertStates("Never\nreport a candidate from a file you did not read".replace("\n", " "))

    def test_it_does_not_lower_the_bar_to_avoid_an_empty_result(self):
        self.assertStates("Do not lower the rubric to produce a non-empty list")

    def test_coverage_is_mandatory_and_partial_passes_are_disclosed(self):
        self.assertStates("Coverage and limits — mandatory, every time")
        self.assertStates("A partial analysis presented as complete is a **defect, not a degradation**")

    def test_an_existing_flaky_annotation_is_evidence_not_an_excuse(self):
        self.assertStates("corroborating evidence, never a reason to skip the test")


class TheProjectsGuardrails(States, unittest.TestCase):
    """FR-033a. The constitution read is the consumer's, and it binds."""

    def test_it_reads_the_invoking_projects_constitution(self):
        self.assertStates("of the project you are running in")

    def test_it_is_explicitly_not_spectras_own(self):
        self.assertStates("never Spectra's own")

    def test_a_guardrail_can_block_a_fix(self):
        self.assertStates("When a guardrail blocks the fix")
        self.assertStates("name\nthe rule that blocked it".replace("\n", " "))

    def test_absence_is_reported_rather_than_assumed(self):
        self.assertStates("say plainly that the project declared no")
        self.assertStates("do not invent rules")


class DeliberateAbsences(States, unittest.TestCase):
    """Two things this command must NOT have. Both are decisions, and both are easy to undo by accident."""

    def test_no_template_is_registered_for_the_analysis_file(self):
        """R-002: the file's structure is a parse contract, not a document whose shape is taste.

        Principle VIII's honour-don't-repair rule would force this command to accept an override that
        renamed `## Tasks` — which would not restyle the output, it would make the file unreadable to
        the run that has to resume from it.
        """
        manifest = MANIFEST.read_text(encoding="utf-8")
        self.assertNotIn("flaky-test-analysis-template", manifest)
        self.assertNotIn("flaky-test-detector-template", manifest)

    def test_it_gates_on_no_external_binary(self):
        """Unlike create-pr and review-pr, this command must run with neither `gh` nor `git` present."""
        body = flat()
        for binary in ("`gh`", "gh auth status", "`git`"):
            self.assertNotIn(
                binary,
                body,
                f"flaky-test-detector.md references {binary}; it must not depend on any external tool",
            )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
