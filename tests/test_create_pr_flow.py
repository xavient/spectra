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


class TheOptionalIssue(unittest.TestCase):
    """Asked for, never required, never invented."""

    def test_the_issue_argument_is_documented(self):
        self.assertTrue(
            "`--issue <url-or-number>`" in text(),
            f"create-pr.md no longer states: {"`--issue <url-or-number>`"!r}",
        )

    def test_it_asks_when_no_issue_was_passed(self):
        body = flat().lower()
        self.assertTrue("otherwise ask once" in body, f"create-pr.md no longer states: {"otherwise ask once"!r}")

    def test_a_declined_issue_proceeds_without_one(self):
        body = flat().lower()
        self.assertTrue(
            "means **no issue**" in flat(),
            f"create-pr.md no longer states: {"means **no issue**"!r}",
        )
        self.assertTrue("do not ask again" in body, f"create-pr.md no longer states: {"do not ask again"!r}")

    def test_the_reference_is_validated(self):
        self.assertTrue(
            "gh issue view" in text(),
            f"create-pr.md no longer states: {"gh issue view"!r}",
        )

    def test_an_unresolvable_issue_does_not_block_the_pr(self):
        self.assertTrue(
            "continue without" in flat().lower(),
            f"create-pr.md no longer states: {"continue without"!r}",
        )

    def test_no_issue_is_ever_fabricated(self):
        self.assertTrue(
            "never fabricate" in flat().lower(),
            f"create-pr.md no longer states: {"never fabricate"!r}",
        )


class TheClosingKeywordRule(unittest.TestCase):
    """A keyword only where GitHub honours one."""

    def test_the_keyword_is_tied_to_the_default_branch(self):
        body = flat()
        self.assertTrue("Base is the repository's default branch" in body, f"create-pr.md no longer states: {"Base is the repository's default branch"!r}")
        self.assertTrue("closing keyword" in body, f"create-pr.md no longer states: {"closing keyword"!r}")

    def test_a_non_default_base_uses_a_plain_reference(self):
        body = flat()
        self.assertTrue("Base is any other branch" in body, f"create-pr.md no longer states: {"Base is any other branch"!r}")
        self.assertTrue("plain reference" in body, f"create-pr.md no longer states: {"plain reference"!r}")

    def test_the_consequence_is_explained_not_just_asserted(self):
        """A rule with no reason gets 'simplified' away by the next editor."""
        body = flat()
        self.assertTrue("interpreted only when the pull request targets the repository's default branch" in body, f"create-pr.md no longer states: {"interpreted only when the pull request targets the repository's default branch"!r}")

    def test_a_cross_repository_issue_never_carries_a_keyword(self):
        body = flat()
        self.assertTrue("another repository" in body, f"create-pr.md no longer states: {"another repository"!r}")
        self.assertTrue("full URL" in body, f"create-pr.md no longer states: {"full URL"!r}")

    def test_the_keyword_decision_is_recomputed_when_the_base_changes(self):
        self.assertTrue(
            "closing-keyword" in flat(),
            f"create-pr.md no longer states: {"closing-keyword"!r}",
        )
        self.assertTrue(
            "now that the base has changed" in flat(),
            f"create-pr.md no longer states: {"now that the base has changed"!r}",
        )


class TheCommitOffer(unittest.TestCase):
    """Uncommitted work is offered a commit, with rails."""

    def test_it_asks_before_committing(self):
        self.assertTrue(
            "There are uncommitted changes. Should I proceed with committing and pushing first?" in flat(),
            "create-pr.md no longer states that requirement",
        )

    def test_it_lists_the_files_first(self):
        self.assertTrue(
            "list the affected files" in flat().lower(),
            f"create-pr.md no longer states: {"list the affected files"!r}",
        )

    def test_it_calls_out_credential_shaped_files(self):
        body = text()
        for token in (".env", "id_rsa", "credentials"):
            with self.subTest(token=token):
                self.assertTrue(token in body, f"create-pr.md no longer states: {token!r}")

    def test_hooks_are_never_bypassed(self):
        self.assertTrue(
            "Never pass `--no-verify`" in flat(),
            f"create-pr.md no longer states: {"Never pass `--no-verify`"!r}",
        )

    def test_declining_excludes_the_changes_and_says_so(self):
        self.assertTrue(
            "only what is already committed" in flat(),
            f"create-pr.md no longer states: {"only what is already committed"!r}",
        )

    def test_it_does_not_blindly_stage_everything(self):
        self.assertTrue(
            "git add -A" in text(),
            f"create-pr.md no longer states: {"git add -A"!r}",
        )
        self.assertTrue(
            "Do not blind-`git add -A`" in flat(),
            f"create-pr.md no longer states: {"Do not blind-`git add -A`"!r}",
        )


class TheBaseBranch(unittest.TestCase):
    """Documented intent wins; a guess is confirmed, never assumed."""

    def test_documented_intent_wins(self):
        self.assertTrue(
            "Documented intent wins over anything you can infer" in flat(),
            f"create-pr.md no longer states: {"Documented intent wins over anything you can infer"!r}",
        )

    def test_it_reads_both_documented_sources(self):
        body = text()
        self.assertTrue(".specify/memory/constitution.md" in body, f"create-pr.md no longer states: {".specify/memory/constitution.md"!r}")
        self.assertTrue(".specify/extensions/git/git-config.yml" in body, f"create-pr.md no longer states: {".specify/extensions/git/git-config.yml"!r}")

    def test_an_undocumented_base_is_a_proposal_not_a_decision(self):
        self.assertTrue(
            "Do not treat a proposal as agreed" in flat(),
            f"create-pr.md no longer states: {"Do not treat a proposal as agreed"!r}",
        )

    def test_the_proposal_is_settled_at_the_final_gate(self):
        self.assertTrue(
            "Is that correct?" in flat(),
            f"create-pr.md no longer states: {"Is that correct?"!r}",
        )

    def test_the_inference_caveat_is_recorded(self):
        """Git has no parent-branch pointer; the reason has to survive edits."""
        self.assertTrue(
            "Git records no parent branch" in flat(),
            f"create-pr.md no longer states: {"Git records no parent branch"!r}",
        )


class TheFinalGate(unittest.TestCase):
    """One summary, one answer, nothing created before it."""

    def test_there_is_a_single_final_confirmation_step(self):
        self.assertTrue(
            "Final confirmation (one summary, one answer)" in text(),
            f"create-pr.md no longer states: {"Final confirmation (one summary, one answer)"!r}",
        )

    def test_nothing_is_created_before_an_affirmative(self):
        self.assertTrue(
            "Create nothing before an affirmative answer" in flat(),
            f"create-pr.md no longer states: {"Create nothing before an affirmative answer"!r}",
        )

    def test_the_summary_states_what_already_happened(self):
        self.assertTrue(
            "What has already happened" in flat(),
            f"create-pr.md no longer states: {"What has already happened"!r}",
        )

    def test_a_declined_gate_reports_the_state_it_left(self):
        self.assertTrue(
            "State what was already done" in flat(),
            f"create-pr.md no longer states: {"State what was already done"!r}",
        )

    def test_a_corrected_base_is_revalidated(self):
        self.assertTrue(
            "git ls-remote --heads origin <new-base>" in text(),
            f"create-pr.md no longer states: {"git ls-remote --heads origin <new-base>"!r}",
        )


class AnyBranchIsAllowed(unittest.TestCase):
    """The spec-branch-only refusal is gone; two refusals remain."""

    def test_the_one_branch_per_spec_refusal_is_gone(self):
        body = flat()
        self.assertNotIn("Never open a PR from a non-spec branch", body)
        self.assertTrue("Any branch is otherwise fair game" in body, f"create-pr.md no longer states: {"Any branch is otherwise fair game"!r}")

    def test_detached_head_is_still_refused(self):
        self.assertTrue(
            "detached" in flat().lower(),
            f"create-pr.md no longer states: {"detached"!r}",
        )

    def test_a_branch_cannot_target_itself(self):
        self.assertTrue(
            "a branch cannot target itself" in flat().lower(),
            f"create-pr.md no longer states: {"a branch cannot target itself"!r}",
        )

    def test_a_spec_branch_still_gives_richer_material(self):
        body = flat()
        self.assertTrue("not permission but **material**" in body, f"create-pr.md no longer states: {"not permission but **material**"!r}")


class SurvivingGuarantees(unittest.TestCase):
    """Everything earlier releases established must still be stated."""

    def test_the_gh_gate_is_still_a_hard_stop(self):
        body = flat()
        self.assertTrue("This is a hard stop, not a degradation" in body, f"create-pr.md no longer states: {"This is a hard stop, not a degradation"!r}")
        self.assertTrue(
            "gh auth status --hostname github.com" in text(),
            f"create-pr.md no longer states: {"gh auth status --hostname github.com"!r}",
        )

    def test_the_auth_check_still_refuses_json(self):
        self.assertTrue(
            "Do not add `--json` to the auth check" in flat(),
            f"create-pr.md no longer states: {"Do not add `--json` to the auth check"!r}",
        )

    def test_the_body_still_goes_through_stdin(self):
        self.assertTrue(
            "--body-file -" in text(),
            f"create-pr.md no longer states: {"--body-file -"!r}",
        )

    def test_head_is_still_always_explicit(self):
        self.assertTrue(
            "`--head` is always passed explicitly" in flat(),
            f"create-pr.md no longer states: {"`--head` is always passed explicitly"!r}",
        )

    def test_degradation_still_states_what_was_mutated(self):
        self.assertTrue("State what was mutated, always" in flat(), f"create-pr.md no longer states: {"State what was mutated, always"!r}")

    def test_the_duplicate_check_survives(self):
        self.assertTrue(
            "gh pr list --head" in text(),
            f"create-pr.md no longer states: {"gh pr list --head"!r}",
        )

    def test_github_only_scope_survives(self):
        self.assertTrue(
            "supports GitHub only" in flat(),
            f"create-pr.md no longer states: {"supports GitHub only"!r}",
        )

    def test_no_credentials_of_its_own(self):
        self.assertTrue(
            "no credentials of your own" in flat(),
            f"create-pr.md no longer states: {"no credentials of your own"!r}",
        )


class TheManifestAgrees(unittest.TestCase):
    """What the manifest advertises has to match what the command does."""

    def test_the_description_mentions_the_issue_argument(self):
        self.assertIn("issue", MANIFEST.read_text(encoding="utf-8").split("create-pr.md")[1][:400])

    def test_the_description_no_longer_claims_the_promotion_strategy_is_the_whole_story(self):
        described = MANIFEST.read_text(encoding="utf-8").split("create-pr.md")[1][:400]
        self.assertNotIn("deriving the base from the promotion strategy", described)


if __name__ == "__main__":
    unittest.main()
