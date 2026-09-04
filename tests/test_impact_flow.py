"""The `impact` flow, asserted against the command text that ships.

A command file is a prompt: its text *is* the implementation, so the enforceable surface is what it says.
These assertions cannot prove an agent behaves correctly at run time — that is the manual pass in
`test/README.md`. What they prove is that the rules it is supposed to follow have not been quietly deleted,
which is the regression that actually happens to prompt files.

This agent is the third Spectra document producer, so Principles VII and VIII are already enforced for it by
`test_doc_output_paths.py` and `test_document_templates.py`; nothing here duplicates those. What is left is
the part that makes an impact analysis usable at a stakeholder gate, and every one of these rules is the kind
a well-meaning edit removes without anyone noticing:

- **It makes no network request and accepts no repository URL.** This is the one an agent will violate with
  good intentions — handed a GitHub URL with `gh` already authenticated, fetching it is *helpful*. It is also
  the rule that keeps the whole extension inside the claim that Spectra opens no channel the host agent does
  not already use, so losing it changes Spectra's security posture, not just this command's behaviour.
- **It never reproduces a secret value.** The command is required to cite `path:line` for every finding, its
  security lens fires exactly when the scan touches secrets, and its default output folder is one some
  projects publish. Remove this rule and those three facts compose into a live credential in a committed file.
- **It never reports absence of evidence as absence of impact**, and it always states coverage. A confident
  report with a hole in it is the failure mode this command exists to prevent.
- **It writes once, at the end, and never overwrites.** That is what makes an interrupted run harmless and a
  re-run non-destructive.
- **The rating and the confidence levels are lookups, not judgements**, so two runs on the same change agree.
- **It creates no link to a specification.** Impact analysis and specification are deliberately independent.

Standard library only, like the rest of the suite.
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import helpers as h  # noqa: E402

COMMAND = h.repo_file("spectra", "commands", "impact.md")
TEMPLATE = h.repo_file("spectra", "templates", "impact-analysis-template.md")
MANIFEST = h.repo_file("spectra", "extension.yml")

COMMAND_NAME = "speckit.spectra.impact"
WRITE_TARGET = "docs/impact-analysis/NNN-<name>.md"


def text() -> str:
    return COMMAND.read_text(encoding="utf-8")


def flat() -> str:
    """Whitespace-flattened, so an assertion survives a reflow of the prose."""
    return " ".join(text().split())


def lower() -> str:
    return flat().lower()


class TheCommandIsRegistered(unittest.TestCase):
    """Principles II and III: one file, under the existing extension, correctly namespaced."""

    def test_the_command_file_exists(self):
        self.assertTrue(COMMAND.is_file(), "spectra/commands/impact.md does not exist")

    def test_it_carries_front_matter_with_a_description(self):
        head = text().split("---", 2)
        self.assertEqual("", head[0].strip(), "the file does not open with YAML front matter")
        self.assertIn("description:", head[1], "front matter carries no description key")

    def test_the_manifest_registers_the_command(self):
        manifest = MANIFEST.read_text(encoding="utf-8")
        self.assertIn(f'- name: "{COMMAND_NAME}"', manifest)
        self.assertIn('file: "commands/impact.md"', manifest)

    def test_the_manifest_registers_the_template(self):
        manifest = MANIFEST.read_text(encoding="utf-8")
        self.assertIn('- name: "impact-analysis-template"', manifest)
        self.assertIn('file: "templates/impact-analysis-template.md"', manifest)

    def test_it_hard_codes_no_agent_invocation_syntax(self):
        """Principle III: one generic source, translated per agent at install time."""
        for trigger in ("/speckit-spectra-impact", "/speckit.spectra.impact", "$speckit-", "/skill:"):
            with self.subTest(trigger=trigger):
                self.assertNotIn(trigger, text(), f"the command file hard-codes the {trigger} form")

    def test_it_names_the_arguments_placeholder(self):
        self.assertIn("$ARGUMENTS", text())


class ItNeverReachesTheNetwork(unittest.TestCase):
    """The rule a helpful agent breaks: handed a URL with gh authenticated, fetching it seems kind."""

    def test_it_states_that_it_makes_no_network_request(self):
        self.assertIn("no network request of any kind", flat())

    def test_it_refuses_urls_credentials_and_logins(self):
        body = lower()
        for term in ("repository url", "credential", "token", "login"):
            with self.subTest(term=term):
                self.assertIn(term, body, f"the command no longer says anything about a {term}")

    def test_it_refuses_to_clone_or_download(self):
        body = lower()
        self.assertIn("no clone", body)
        self.assertIn("no download", body)

    def test_it_says_what_to_do_when_offered_a_url(self):
        """Not a prohibition in the abstract — an instruction at the moment of temptation."""
        body = flat()
        self.assertIn("read only local directories", body)
        self.assertIn("fetch nothing", body)

    def test_it_reads_a_declared_path_in_place(self):
        body = flat()
        self.assertIn("read where it is", body)
        for verb in ("modify", "delete", "copy"):
            with self.subTest(verb=verb):
                self.assertIn(verb, lower())

    def test_it_never_writes_outside_the_project(self):
        self.assertIn("outside the project", flat())


class ItNeverReproducesASecret(unittest.TestCase):
    """FR-042a. The citation rule plus the security trigger plus a publishable folder is a live path."""

    def test_it_forbids_reproducing_a_secret_value(self):
        body = flat()
        self.assertIn("Never reproduce a secret value", body)
        self.assertIn("in whole or in fragment", body)

    def test_it_names_the_kinds_it_will_not_quote(self):
        body = lower()
        for kind in ("credential", "key", "token", "password", "connection string"):
            with self.subTest(kind=kind):
                self.assertIn(kind, body)

    def test_it_states_what_to_write_instead(self):
        body = flat()
        self.assertIn("location and the kind", body)
        self.assertIn("value was withheld", body)

    def test_it_prefers_over_withholding(self):
        """An imperfect detector must fail in the safe direction."""
        self.assertIn("Over-withholding is the correct error to make", flat())

    def test_the_session_output_is_covered_too(self):
        """A secret spoken in chat is as leaked as one written to the file."""
        self.assertIn("anything you say in this session", flat())


class TheTrustworthinessRulesSurvive(unittest.TestCase):
    """R1 to R5. A confident report with a hole in it has failed even if every sentence is true."""

    def test_it_forbids_claiming_absence_of_impact(self):
        body = flat()
        self.assertIn('"No downstream impact" is not', body)
        self.assertIn("No consumers found in what was scanned", body)

    def test_it_requires_a_citation_on_every_finding(self):
        self.assertRegex(flat(), r"path/to/file\.\w+:\d+")

    def test_it_keeps_the_evidenced_absence_exception(self):
        """Without it, a High rating could never be stated as a finding."""
        body = flat()
        self.assertIn("Evidenced absence is the one exception", body)
        self.assertIn("no viable rollback path identified", body)

    def test_it_escalates_every_external_contract_change(self):
        body = flat()
        self.assertIn("human verification required", body)
        self.assertIn("regardless", body)

    def test_it_states_coverage_per_system(self):
        body = lower()
        self.assertIn("files you read out of how many exist", body)
        self.assertIn("i did not", body)

    def test_it_degrades_loudly(self):
        body = flat()
        self.assertIn("Never silently truncate", body)


class RatingAndConfidenceAreLookups(unittest.TestCase):
    """Two runs on the same change have to agree, so neither may be a judgement."""

    def test_confidence_has_exactly_three_levels(self):
        body = text()
        for level in ("`confirmed`", "`probable`", "`possible`"):
            with self.subTest(level=level):
                self.assertIn(level, body)

    def test_a_document_only_finding_is_never_confirmed(self):
        """A spec records intent and drifts from code; the cheaper scan mode must not sound more certain."""
        self.assertIn("never** `confirmed`", flat())

    def test_a_dynamic_pattern_hit_is_only_possible(self):
        self.assertIn("never rises above `possible`", flat())

    def test_the_rating_is_derived_not_judged(self):
        body = flat()
        self.assertIn("Do not judge the rating", body)
        self.assertIn("name the trigger that fired", body)

    def test_every_rating_band_is_defined(self):
        body = flat()
        for band in ("**High**", "**Medium**", "**Low**"):
            with self.subTest(band=band):
                self.assertIn(band, body)

    def test_the_high_triggers_are_all_present(self):
        body = lower()
        for trigger in ("irreversible data change", "external contract change",
                        "security & privacy lens fired", "compliance lens fired",
                        "no viable rollback path"):
            with self.subTest(trigger=trigger):
                self.assertIn(trigger, body)


class TheWriteIsBoundedAndAtomic(unittest.TestCase):
    """Three writes, once, at the end — which is what makes an interrupted run harmless."""

    def test_it_names_its_write_target(self):
        self.assertIn(WRITE_TARGET, text())

    def test_it_writes_once_as_the_final_act(self):
        self.assertIn("written once, as this run's final act", flat())

    def test_an_interrupted_run_leaves_nothing_behind(self):
        body = flat()
        self.assertIn("no partial document", body)
        self.assertIn("no number consumed", body)

    def test_the_number_is_highest_plus_one_not_a_count(self):
        """Counting collides after a deletion: 001 and 003 on disk makes count-plus-one 003."""
        body = flat()
        self.assertIn("one greater than the highest number already in the folder", body)
        self.assertIn("never a count of the files", body)

    def test_it_never_overwrites_an_earlier_analysis(self):
        body = flat()
        self.assertIn("Every run writes a new document", body)
        for forbidden in ("overwrite", "amend", "diff"):
            with self.subTest(verb=forbidden):
                self.assertIn(forbidden, body)

    def test_identical_input_still_produces_a_report(self):
        self.assertIn("identical to a previous one", flat())

    def test_the_sequence_is_independent_of_specs(self):
        self.assertIn("independent of `specs/`", flat())

    def test_it_lists_exactly_its_permitted_writes(self):
        body = flat()
        self.assertIn("Nothing else, anywhere, ever", body)
        for forbidden in ("Edit the constitution", "create a branch", "commit"):
            with self.subTest(action=forbidden):
                self.assertIn(forbidden, body)


class TheStatusStaysDraft(unittest.TestCase):
    """The approval gate is a conversation with stakeholders, which the command does not witness."""

    def test_it_writes_draft_on_every_run(self):
        self.assertIn("`status` is `draft` on every run", flat())

    def test_it_sets_no_other_status_except_superseded(self):
        body = flat()
        self.assertIn("Never set, prompt for, or infer any other status", body)
        self.assertIn("superseded", body)

    def test_the_supersede_write_touches_exactly_two_fields(self):
        body = flat()
        self.assertIn("exactly two fields of the prior document change", body)
        self.assertIn("only non-additive write", body)

    def test_the_index_is_rebuilt_rather_than_appended(self):
        """Otherwise a hand-recorded approval never reaches the index."""
        body = flat()
        self.assertIn("Refresh it, do not append to it", body)
        self.assertIn("Modify no document in order to do it", body)


class ThereIsNoLinkToASpecification(unittest.TestCase):
    """Two independent processes. Reading a spec is evidence; it is not a relationship."""

    def test_it_carries_no_spec_reference_field(self):
        self.assertIn("no `spec_refs` key, in any form", flat())

    def test_it_creates_no_specification_link(self):
        self.assertIn("Create, reference, or link a specification", flat())

    def test_reading_a_spec_creates_no_relationship(self):
        self.assertIn("creates no relationship to it", flat())

    def test_a_spec_that_disagrees_with_the_code_is_a_finding(self):
        self.assertIn("that disagreement is itself a finding", flat().lower())


class TheInteractionIsBounded(unittest.TestCase):
    """Five questions, never padded, never blocking — and pre-flight does not spend the budget."""

    def test_the_question_cap_is_five_and_is_not_overridable(self):
        body = flat()
        self.assertIn("Maximum five", body)
        self.assertIn("**not overridable**", body)

    def test_it_refuses_to_pad(self):
        self.assertIn("Never pad to five", flat())

    def test_pre_flight_does_not_consume_the_budget(self):
        self.assertIn("none of them counts against the five", flat())

    def test_it_never_asks_what_the_repository_answers(self):
        self.assertIn("Never ask a question the repository answers", flat())

    def test_every_question_offers_other_and_a_reasoned_recommendation(self):
        body = flat()
        self.assertIn('"Other"', body)
        self.assertIn("recommendation with its reasoning", body)

    def test_a_skip_never_blocks(self):
        body = flat()
        self.assertIn("Skipping never blocks", body)
        self.assertIn("defaulted — not confirmed", body)

    def test_three_categories_are_promoted_when_defaulted(self):
        body = lower()
        for category in ("scope boundary", "data lifecycle", "contract compatibility"):
            with self.subTest(category=category):
                self.assertIn(category, body)


class EveryCapIsStatedAndOverridable(unittest.TestCase):
    """Bounded on purpose: an analysis that arrives tomorrow is not a decision input."""

    CAPS = {
        "--seed-cap": "30",
        "--hops": "2 hops",
        "--max-files": "80",
        "--identifier-cap": "50",
        "--per-system-cap": "20",
    }

    def test_each_cap_has_a_default_and_a_flag(self):
        body = text()
        for flag, default in self.CAPS.items():
            with self.subTest(cap=flag):
                self.assertIn(flag, body)
                self.assertIn(default, body)

    def test_a_non_default_value_is_disclosed(self):
        self.assertIn("stated in Sources consulted", flat())

    def test_the_identifier_sweep_is_ranked_before_it_is_capped(self):
        """A cap without a ranking is a coin flip; with one, the tail is the least valuable part."""
        body = flat()
        self.assertIn("Contract-bearing", body)
        self.assertIn("Config-bearing", body)
        self.assertIn("how many went unswept", body)


class TheScanIsAgentAgnostic(unittest.TestCase):
    """Principle III: no tool named, no script shipped, and a stated fallback when search is absent."""

    # Named tools, matched on word boundaries. `ack` as a bare substring hits "rollback" and "backfill",
    # which is why this is a regex rather than a containment check.
    NAMED_TOOLS = (r"\bripgrep\b", r"`rg`", r"\bgrep\b", r"\back\b", r"\bag\b", r"git clone",
                   r"\bfd\b", r"\bfind \.", r"\bawk\b", r"\bsed\b")

    def test_it_names_no_search_tool(self):
        """Principle III: state the capability, never the binary. A named tool breaks a whole agent."""
        body = text()
        for pattern in self.NAMED_TOOLS:
            with self.subTest(tool=pattern):
                self.assertIsNone(
                    re.search(pattern, body),
                    f"the command names {pattern} instead of stating the capability it needs",
                )

    def test_gh_appears_only_as_a_temptation_to_refuse(self):
        """`gh` is mentioned on purpose — at the moment an agent would reach for it — and nowhere else."""
        mentions = [line for line in text().splitlines() if "`gh`" in line]
        self.assertTrue(mentions, "the command no longer names the gh temptation it is refusing")
        for line in mentions:
            with self.subTest(line=line.strip()[:60]):
                self.assertIn("authenticated", line, "`gh` appears outside the URL-refusal instruction")

    def test_it_states_the_capability_it_needs(self):
        self.assertIn("find a literal string anywhere in the project", flat())

    def test_it_degrades_when_project_wide_search_is_missing(self):
        body = flat()
        self.assertIn("If you have no project-wide text search", body)
        self.assertIn("reduced coverage", body)

    def test_both_scan_modes_are_defined_and_disclosed(self):
        body = flat()
        self.assertIn("Spec-informed", body)
        self.assertIn("Source-only", body)
        self.assertIn("State which mode you ran", body)


class TheLensesRouteRatherThanJudge(unittest.TestCase):
    """Thin command, coherent roster: name the agent that owns the question."""

    def test_all_five_core_lenses_are_present(self):
        body = flat()
        for lens in ("Blast radius", "Data", "Behavioural change", "Risk & reversibility",
                     "Effort & sequencing"):
            with self.subTest(lens=lens):
                self.assertIn(lens, body)

    def test_effort_is_labelled_a_heuristic_not_an_estimate(self):
        self.assertIn("coupling-depth heuristic, not an estimate", flat())

    def test_it_renders_no_compliance_verdict(self):
        self.assertIn("Never render a compliance verdict", flat())

    def test_an_untriggered_conditional_section_is_absent(self):
        self.assertIn("not present and empty", flat())

    def test_it_flags_rather_than_writes_about_what_it_cannot_see(self):
        body = flat()
        self.assertIn("human follow-up", body.lower())
        self.assertIn("generate no prose about it", body)


class NonInteractiveModeIsHonest(unittest.TestCase):
    """A batch-produced draft must not be mistakable for a reviewed one."""

    def test_the_switch_suppresses_every_prompt(self):
        self.assertIn("no prompt of any kind", flat())

    def test_defaulted_answers_are_tagged(self):
        self.assertIn("logged as `defaulted — not confirmed`", flat())

    def test_three_or_more_defaults_raise_a_banner(self):
        body = flat()
        self.assertIn("three or more answers were defaulted", body)
        self.assertIn("materially unconfirmed", body)

    def test_it_leaves_the_prior_document_alone_without_a_confirmation(self):
        self.assertIn("gated on a confirmation CI cannot give", flat())

    def test_it_neither_hangs_nor_proceeds_silently(self):
        body = flat()
        self.assertIn("do not hang on input that cannot arrive", body)
        self.assertIn("do not proceed silently", body)


class TheKnownLimitsAreStated(unittest.TestCase):
    """The boundary of the evidence is part of the output, not a disclaimer."""

    def test_it_admits_what_the_sweeps_cannot_find(self):
        self.assertIn("neither imported nor named anywhere in the source", flat())

    def test_it_admits_that_repository_scope_is_not_system_scope(self):
        self.assertIn("Repository scope is not system scope", flat())

    def test_it_explains_why_co_change_history_was_excluded(self):
        self.assertIn("Git co-change analysis", flat())


class TheTemplateAndSkeletonAgree(unittest.TestCase):
    """test_document_templates.py checks heading parity; this checks the section list is the agreed one."""

    SECTIONS = (
        "Change statement",
        "Inputs",
        "Impact rating",
        "Findings",
        "External contract changes",
        "Human follow-up required",
        "Open risks and rollback",
        "Clarifications",
        "Assumptions and unknowns",
        "Sources consulted",
    )

    def test_the_shipped_template_has_the_ten_agreed_sections(self):
        headings = re.findall(r"^## +(.+?)\s*$", TEMPLATE.read_text(encoding="utf-8"), re.M)
        self.assertEqual(10, len(headings), f"expected ten H2 sections, found {headings}")
        for expected, found in zip(self.SECTIONS, headings):
            with self.subTest(section=expected):
                self.assertTrue(found.startswith(expected), f"expected {expected!r}, found {found!r}")

    def test_the_template_cannot_override_the_standards(self):
        body = flat()
        self.assertIn("What a template cannot change", body)
        self.assertIn("Honour the resolved template; do not repair it", body)

    def test_an_omitted_section_is_noted_not_reinstated(self):
        self.assertIn("note the omission and move on", flat())


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
