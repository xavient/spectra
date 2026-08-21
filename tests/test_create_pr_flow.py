"""The `create-pr` flow, asserted against the command text that ships.

A command file is a prompt: its text *is* the implementation, so the enforceable surface is what it says. These
assertions pin the behaviours that would be silently lost in an edit — and one that would be silently *wrong*.

The load-bearing one is the closing-keyword rule. GitHub's documentation: the keywords "are interpreted only
when the pull request targets the repository's default branch. If the pull request targets any other branch,
then these keywords are ignored, no links are created, and merging the PR has no effect on the issues." Since
this command exists partly to target a `dev` in a promotion flow, a `Closes #42` written there looks correct
and does nothing at all. Losing that condition is invisible in review and invisible at run time.

Standard library only, like the rest of the suite.
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import helpers as h  # noqa: E402

COMMAND = h.repo_file("spectra", "commands", "create-pr.md")
MANIFEST = h.repo_file("spectra", "extension.yml")


def text() -> str:
    return COMMAND.read_text(encoding="utf-8")


def flat() -> str:
    """Whitespace-flattened, so an assertion survives a reflow of the prose."""
    return " ".join(text().split())


class States:
    """`assertIn` against a whole command file dumps it into the failure; this prints the message only."""

    def assertStates(self, needle, haystack=None):
        hay = flat() if haystack is None else haystack
        self.assertTrue(needle in hay, "create-pr.md no longer states: " + repr(needle))


class TheOptionalIssue(States, unittest.TestCase):
    """Asked for, never required, never invented."""

    def test_the_issue_argument_is_documented(self):
        self.assertStates("`--issue <url-or-number>`", text())

    def test_it_asks_when_no_issue_was_passed(self):
        body = flat().lower()
        self.assertTrue("otherwise ask once" in body, "create-pr.md no longer states: " + repr("otherwise ask once"))

    def test_a_declined_issue_proceeds_without_one(self):
        body = flat().lower()
        self.assertTrue(
            "means **no issue**" in flat(),
            "create-pr.md no longer states: " + repr("means **no issue**"),
        )
        self.assertTrue("do not ask again" in body, "create-pr.md no longer states: " + repr("do not ask again"))

    def test_the_reference_is_validated(self):
        self.assertTrue(
            "gh issue view" in text(),
            "create-pr.md no longer states: " + repr("gh issue view"),
        )

    def test_an_unresolvable_issue_does_not_block_the_pr(self):
        self.assertTrue(
            "continue without" in flat().lower(),
            "create-pr.md no longer states: " + repr("continue without"),
        )

    def test_no_issue_is_ever_fabricated(self):
        self.assertTrue(
            "never fabricate" in flat().lower(),
            "create-pr.md no longer states: " + repr("never fabricate"),
        )


class TheClosingKeywordRule(States, unittest.TestCase):
    """A keyword only where GitHub honours one."""

    def test_the_keyword_is_tied_to_the_default_branch(self):
        body = flat()
        self.assertTrue("Base is the repository's default branch" in body, "create-pr.md no longer states: " + repr("Base is the repository's default branch"))
        self.assertTrue("closing keyword" in body, "create-pr.md no longer states: " + repr("closing keyword"))

    def test_a_non_default_base_uses_a_plain_reference(self):
        body = flat()
        self.assertTrue("Base is any other branch" in body, "create-pr.md no longer states: " + repr("Base is any other branch"))
        self.assertTrue("plain reference" in body, "create-pr.md no longer states: " + repr("plain reference"))

    def test_the_consequence_is_explained_not_just_asserted(self):
        """A rule with no reason gets 'simplified' away by the next editor."""
        body = flat()
        self.assertTrue("interpreted only when the pull request targets the repository's default branch" in body, "create-pr.md no longer states: " + repr("interpreted only when the pull request targets the repository's default branch"))

    def test_a_cross_repository_issue_never_carries_a_keyword(self):
        body = flat()
        self.assertTrue("another repository" in body, "create-pr.md no longer states: " + repr("another repository"))
        self.assertTrue("full URL" in body, "create-pr.md no longer states: " + repr("full URL"))

    def test_the_keyword_decision_is_recomputed_when_the_base_changes(self):
        self.assertTrue(
            "closing-keyword" in flat(),
            "create-pr.md no longer states: " + repr("closing-keyword"),
        )
        self.assertTrue(
            "now that the base has changed" in flat(),
            "create-pr.md no longer states: " + repr("now that the base has changed"),
        )


class TheCommitOffer(States, unittest.TestCase):
    """Uncommitted work is offered a commit, with rails."""

    def test_it_asks_before_committing(self):
        self.assertTrue(
            "There are uncommitted changes. Should I proceed with committing and pushing first?", flat())

    def test_it_lists_the_files_first(self):
        self.assertTrue(
            "list the affected files" in flat().lower(),
            "create-pr.md no longer states: " + repr("list the affected files"),
        )

    def test_it_calls_out_credential_shaped_files(self):
        body = text()
        for token in (".env", "id_rsa", "credentials"):
            with self.subTest(token=token):
                self.assertStates(token, body)

    def test_hooks_are_never_bypassed(self):
        self.assertTrue(
            "Never pass `--no-verify`" in flat(),
            "create-pr.md no longer states: " + repr("Never pass `--no-verify`"),
        )

    def test_declining_excludes_the_changes_and_says_so(self):
        self.assertTrue(
            "only what is already committed" in flat(),
            "create-pr.md no longer states: " + repr("only what is already committed"),
        )

    def test_it_does_not_blindly_stage_everything(self):
        self.assertTrue(
            "git add -A" in text(),
            "create-pr.md no longer states: " + repr("git add -A"),
        )
        self.assertTrue(
            "Do not blind-`git add -A`" in flat(),
            "create-pr.md no longer states: " + repr("Do not blind-`git add -A`"),
        )


class TheBaseBranch(States, unittest.TestCase):
    """Documented intent wins; a guess is confirmed, never assumed."""

    def test_documented_intent_wins(self):
        self.assertTrue(
            "Documented intent wins over anything you can infer" in flat(),
            "create-pr.md no longer states: " + repr("Documented intent wins over anything you can infer"),
        )

    def test_it_reads_both_documented_sources(self):
        body = text()
        self.assertTrue(".specify/memory/constitution.md" in body, "create-pr.md no longer states: " + repr(".specify/memory/constitution.md"))
        self.assertTrue(".specify/extensions/git/git-config.yml" in body, "create-pr.md no longer states: " + repr(".specify/extensions/git/git-config.yml"))

    def test_an_undocumented_base_is_a_proposal_not_a_decision(self):
        self.assertTrue(
            "Do not treat a proposal as agreed" in flat(),
            "create-pr.md no longer states: " + repr("Do not treat a proposal as agreed"),
        )

    def test_the_proposal_is_settled_at_the_final_gate(self):
        self.assertTrue(
            "Is that correct?" in flat(),
            "create-pr.md no longer states: " + repr("Is that correct?"),
        )

    def test_the_inference_caveat_is_recorded(self):
        """Git has no parent-branch pointer; the reason has to survive edits."""
        self.assertTrue(
            "Git records no parent branch" in flat(),
            "create-pr.md no longer states: " + repr("Git records no parent branch"),
        )


class TheFinalGate(States, unittest.TestCase):
    """One summary, one answer, nothing created before it."""

    def test_there_is_a_single_final_confirmation_step(self):
        self.assertTrue(
            "Final confirmation (one summary, one answer)" in text(),
            "create-pr.md no longer states: " + repr("Final confirmation (one summary, one answer)"),
        )

    def test_nothing_is_created_before_an_affirmative(self):
        self.assertTrue(
            "Create nothing before an affirmative answer" in flat(),
            "create-pr.md no longer states: " + repr("Create nothing before an affirmative answer"),
        )

    def test_the_summary_states_what_already_happened(self):
        self.assertTrue(
            "What has already happened" in flat(),
            "create-pr.md no longer states: " + repr("What has already happened"),
        )

    def test_a_declined_gate_reports_the_state_it_left(self):
        self.assertTrue(
            "State what was already done" in flat(),
            "create-pr.md no longer states: " + repr("State what was already done"),
        )

    def test_a_corrected_base_is_revalidated(self):
        self.assertTrue(
            "git ls-remote --heads origin <new-base>" in text(),
            "create-pr.md no longer states: " + repr("git ls-remote --heads origin <new-base>"),
        )


class AnyBranchIsAllowed(States, unittest.TestCase):
    """The spec-branch-only refusal is gone; two refusals remain."""

    def test_the_one_branch_per_spec_refusal_is_gone(self):
        body = flat()
        self.assertNotIn("Never open a PR from a non-spec branch", body)
        self.assertTrue("Any branch is otherwise fair game" in body, "create-pr.md no longer states: " + repr("Any branch is otherwise fair game"))

    def test_detached_head_is_still_refused(self):
        self.assertTrue(
            "detached" in flat().lower(),
            "create-pr.md no longer states: " + repr("detached"),
        )

    def test_a_branch_cannot_target_itself(self):
        self.assertTrue(
            "a branch cannot target itself" in flat().lower(),
            "create-pr.md no longer states: " + repr("a branch cannot target itself"),
        )

    def test_a_spec_branch_still_gives_richer_material(self):
        body = flat()
        self.assertTrue("not permission but **material**" in body, "create-pr.md no longer states: " + repr("not permission but **material**"))


class SurvivingGuarantees(States, unittest.TestCase):
    """Everything earlier releases established must still be stated."""

    def test_the_gh_gate_is_still_a_hard_stop(self):
        body = flat()
        self.assertTrue("This is a hard stop, not a degradation" in body, "create-pr.md no longer states: " + repr("This is a hard stop, not a degradation"))
        self.assertTrue(
            "gh auth status --hostname github.com" in text(),
            "create-pr.md no longer states: " + repr("gh auth status --hostname github.com"),
        )

    def test_the_auth_check_still_refuses_json(self):
        self.assertTrue(
            "Do not add `--json` to the auth check" in flat(),
            "create-pr.md no longer states: " + repr("Do not add `--json` to the auth check"),
        )

    def test_the_body_still_goes_through_stdin(self):
        self.assertTrue(
            "--body-file -" in text(),
            "create-pr.md no longer states: " + repr("--body-file -"),
        )

    def test_head_is_still_always_explicit(self):
        self.assertTrue(
            "`--head` is always passed explicitly" in flat(),
            "create-pr.md no longer states: " + repr("`--head` is always passed explicitly"),
        )

    def test_degradation_still_states_what_was_mutated(self):
        self.assertTrue("State what was mutated, always" in flat(), "create-pr.md no longer states: " + repr("State what was mutated, always"))

    def test_the_duplicate_check_survives(self):
        self.assertTrue(
            "gh pr list --head" in text(),
            "create-pr.md no longer states: " + repr("gh pr list --head"),
        )

    def test_github_only_scope_survives(self):
        self.assertTrue(
            "supports GitHub only" in flat(),
            "create-pr.md no longer states: " + repr("supports GitHub only"),
        )

    def test_no_credentials_of_its_own(self):
        self.assertTrue(
            "no credentials of your own" in flat(),
            "create-pr.md no longer states: " + repr("no credentials of your own"),
        )


class TheIssueLinkIsAnInvariant(States, unittest.TestCase):
    """A template governs shape; whether the PR is linked is the command's obligation.

    Before 1.9.1 the reference was purely presentational, so a project override that trimmed the Related
    Issues section produced an unlinked pull request from `--issue 42` — a silent failure on an artifact that
    looked complete.
    """

    def test_the_reference_survives_a_template_without_a_section(self):
        self.assertStates("append** a short")
        self.assertStates("had no place for it")

    def test_the_carve_out_is_stated_as_scope_not_as_an_exception(self):
        self.assertStates("issue\n  reference is yours, not the template's", text())

    def test_the_reason_is_recorded(self):
        self.assertStates("silently produces an unlinked pull request")

    def test_the_precedent_is_cited(self):
        """`review-pr` drew this line first; naming it stops the carve-out reading as ad hoc."""
        self.assertStates("shape is the template's, functional obligations are the command's")

    def test_a_section_is_judged_by_intent_not_heading_text(self):
        self.assertStates("Judge that by intent rather than by heading text")

    def test_no_issue_means_no_section(self):
        self.assertStates("No placeholder number, no empty heading")


class TheShippedTemplateKeepsItsGuidance(unittest.TestCase):
    """The command owns the rule, but an unexplained rule is one edit from being simplified away."""

    def setUp(self):
        self.template = h.repo_file("spectra", "templates", "pr-template.md").read_text(encoding="utf-8")

    def test_it_has_a_related_issues_section(self):
        self.assertTrue(
            "## Related Issues" in self.template,
            "pr-template.md no longer has a Related Issues section",
        )

    def test_the_default_branch_condition_is_explained(self):
        flat_template = " ".join(self.template.split())
        self.assertTrue(
            "only meaningful when the PR targets the repository's DEFAULT branch" in flat_template,
            "pr-template.md no longer explains that closing keywords are default-branch only",
        )

    def test_it_says_removing_the_section_does_not_unlink_the_pr(self):
        flat_template = " ".join(self.template.split())
        self.assertTrue(
            "the pull request is still linked" in flat_template,
            "pr-template.md no longer tells a team what happens if they trim this section",
        )


class TheManifestAgrees(States, unittest.TestCase):
    """What the manifest advertises has to match what the command does."""

    def test_the_description_mentions_the_issue_argument(self):
        self.assertIn("issue", MANIFEST.read_text(encoding="utf-8").split("create-pr.md")[1][:400])

    def test_the_description_no_longer_claims_the_promotion_strategy_is_the_whole_story(self):
        described = MANIFEST.read_text(encoding="utf-8").split("create-pr.md")[1][:400]
        self.assertNotIn("deriving the base from the promotion strategy", described)


if __name__ == "__main__":
    unittest.main()
