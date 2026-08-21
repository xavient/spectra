"""Coverage detection, the plan, the rotation, and the restoration obligation.

The module under test answers one question — *which installed integrations have Spectra's commands?* — and
then performs a rotation to fix the ones that do not. Two things make it testable without a real Spec Kit:

* **Planning is pure**, so every interesting property (what will be activated, in what order, what will be
  restored) is asserted against a data structure with no stub in sight.
* **Executing goes through one delegation**, so the argv log in `helpers.fake_specify` records the exact
  sequence of `specify integration use` calls the rotation made — including the restoring one.

The tests that matter most are the ones about the restore: it must happen after a failed activation, after
an interrupt, and it must be reported as a distinct verdict rather than as a boolean, because "we never
moved it" and "we moved it and put it back" print differently (spec 011 FR-015, FR-016, research R4).
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import helpers as h  # noqa: E402
from spectra_cli import coverage  # noqa: E402


def seed(project_root, *, installed, default, covered):
    """Write the three files coverage reads: the installed list, the default, and the registry."""
    h.write_integration(project_root, "0.16.5", integrations=list(installed),
                        default_integration=default)
    h.write_registry(project_root, list(covered))


def registry_agents(project_root):
    data = json.loads((Path(project_root) / ".specify" / "extensions" / ".registry")
                      .read_text(encoding="utf-8"))
    return sorted(data["extensions"]["spectra"]["registered_commands"])


def recorded_default(project_root):
    data = json.loads((Path(project_root) / ".specify" / "integration.json")
                      .read_text(encoding="utf-8"))
    return data.get("default_integration")


class PlanIsPure(unittest.TestCase):
    """What the plan contains, and what it excludes. No subprocess, no terminal, no writes."""

    def test_targets_exclude_the_default_and_every_covered_key(self):
        """FR-010, FR-011, research R3.

        A covered integration is never re-registered, and the default is never a target — it is covered by
        the restoring activation instead, which is the same call that has to happen anyway.
        """
        with h.temp_project() as root:
            seed(root, installed=["kiro-cli", "claude", "copilot"], default="kiro-cli",
                 covered=["claude"])
            plan = coverage.plan(root)
            self.assertEqual(plan.targets, ("copilot",))
            self.assertEqual(plan.default_key, "kiro-cli")
            self.assertTrue(plan.default_uncovered)

    def test_registry_keys_absent_from_the_installed_list_are_ignored(self):
        """FR-005. Coverage recorded for an agent nobody installed is neither a problem nor coverage."""
        with h.temp_project() as root:
            seed(root, installed=["kiro-cli"], default="kiro-cli", covered=["kiro-cli", "gemini"])
            plan = coverage.plan(root)
            self.assertEqual([state.key for state in plan.states], ["kiro-cli"])
            self.assertFalse(plan.needed)

    def test_activations_always_end_with_the_default(self):
        """FR-015. The last thing a rotation does is put the default back."""
        with h.temp_project() as root:
            seed(root, installed=["kiro-cli", "claude", "copilot"], default="kiro-cli",
                 covered=["kiro-cli"])
            plan = coverage.plan(root)
            self.assertEqual(plan.activations[-1], "kiro-cli")
            self.assertEqual(plan.activations, ("claude", "copilot", "kiro-cli"))

    def test_a_plan_that_only_covers_the_default_does_not_move_it(self):
        """FR-013. One activation, of the key already active, so no transient-default disclosure."""
        with h.temp_project() as root:
            seed(root, installed=["kiro-cli", "claude"], default="kiro-cli", covered=["claude"])
            plan = coverage.plan(root)
            self.assertEqual(plan.targets, ())
            self.assertTrue(plan.needed)
            self.assertFalse(plan.moves_default)
            self.assertEqual(plan.activations, ("kiro-cli",))

    def test_planning_writes_nothing(self):
        """Purity, asserted rather than asserted-in-a-docstring: the tree is byte-identical after."""
        with h.temp_project() as root:
            seed(root, installed=["kiro-cli", "claude"], default="kiro-cli", covered=["kiro-cli"])
            before = {p: p.read_bytes() for p in Path(root).rglob("*") if p.is_file()}
            coverage.plan(root)
            after = {p: p.read_bytes() for p in Path(root).rglob("*") if p.is_file()}
            self.assertEqual(before, after)


class EmptyPlanReasons(unittest.TestCase):
    """Five ways to have nothing to do, each with fixed wording (data-model.md)."""

    def test_every_integration_already_covered(self):
        with h.temp_project() as root:
            seed(root, installed=["kiro-cli", "claude"], default="kiro-cli",
                 covered=["kiro-cli", "claude"])
            plan = coverage.plan(root)
            self.assertFalse(plan.needed)
            self.assertEqual(plan.activations, ())
            self.assertEqual(plan.skip_reason, coverage.REASON_ALL_COVERED)

    def test_unreadable_registry_is_unknown_not_uncovered(self):
        """FR-003, FR-004. The single most important negative: unknown must not mean "nothing covered"."""
        with h.temp_project() as root:
            h.write_integration(root, "0.16.5", integrations=["kiro-cli", "claude"],
                                default_integration="kiro-cli")
            h.write_registry(root, h.BAD_JSON)
            plan = coverage.plan(root)
            self.assertFalse(plan.needed)
            self.assertEqual(plan.activations, ())
            self.assertEqual(plan.skip_reason, coverage.REASON_UNKNOWN)

    def test_registry_with_no_command_map_is_also_unknown(self):
        with h.temp_project() as root:
            h.write_integration(root, "0.16.5", integrations=["kiro-cli", "claude"],
                                default_integration="kiro-cli")
            h.write_registry(root, [])
            self.assertEqual(coverage.plan(root).skip_reason, coverage.REASON_UNKNOWN)

    def test_no_default_recorded_means_nothing_to_restore(self):
        """FR-012. Without a default there is no value to put back, so nothing may be activated."""
        with h.temp_project() as root:
            seed(root, installed=["kiro-cli", "claude"], default=h.NO_DEFAULT, covered=["kiro-cli"])
            plan = coverage.plan(root)
            self.assertFalse(plan.needed)
            self.assertEqual(plan.skip_reason, coverage.REASON_NO_DEFAULT)

    def test_no_installed_integrations_recorded(self):
        with h.temp_project() as root:
            h.write_registry(root, ["kiro-cli"])
            plan = coverage.plan(root)
            self.assertFalse(plan.needed)
            self.assertEqual(plan.skip_reason, coverage.REASON_NO_INTEGRATIONS)

    def test_extension_absent_is_its_own_reason(self):
        """FR-022. "Nothing installed to register" is not "everything is covered"."""
        with h.temp_project() as root:
            seed(root, installed=["kiro-cli", "claude"], default="kiro-cli", covered=["kiro-cli"])
            plan = coverage.plan(root, extension_present=False)
            self.assertFalse(plan.needed)
            self.assertEqual(plan.skip_reason, coverage.REASON_NOT_INSTALLED)

    def test_the_shared_infrastructure_record_is_not_an_integration(self):
        """FR-002. `speckit` sits among the per-integration records without being one."""
        with h.temp_project() as root:
            seed(root, installed=["kiro-cli", "speckit"], default="kiro-cli", covered=["kiro-cli"])
            plan = coverage.plan(root)
            self.assertEqual([state.key for state in plan.states], ["kiro-cli"])
            self.assertFalse(plan.needed)


class RotationOrder(unittest.TestCase):
    """What actually gets invoked, read from the argv log rather than from human output."""

    def test_two_integrations_activate_the_target_then_restore(self):
        with h.temp_project() as root:
            seed(root, installed=["kiro-cli", "claude"], default="kiro-cli", covered=["kiro-cli"])
            log = Path(root) / "argv.log"
            with h.fake_specify(argv_log=log, use_effect=root):
                coverage.apply(coverage.plan(root))
            self.assertEqual(h.integration_use_calls(log), ["claude", "kiro-cli"])

    def test_three_integrations_activate_in_recorded_order_then_restore(self):
        with h.temp_project() as root:
            seed(root, installed=["kiro-cli", "claude", "copilot"], default="kiro-cli",
                 covered=["kiro-cli"])
            log = Path(root) / "argv.log"
            with h.fake_specify(argv_log=log, use_effect=root):
                coverage.apply(coverage.plan(root))
            self.assertEqual(h.integration_use_calls(log), ["claude", "copilot", "kiro-cli"])

    def test_the_default_only_case_activates_exactly_once(self):
        """FR-013. Covering the default *is* activating it; there is no second call to undo."""
        with h.temp_project() as root:
            seed(root, installed=["kiro-cli", "claude"], default="kiro-cli", covered=["claude"])
            log = Path(root) / "argv.log"
            with h.fake_specify(argv_log=log, use_effect=root):
                result = coverage.apply(coverage.plan(root))
            self.assertEqual(h.integration_use_calls(log), ["kiro-cli"])
            self.assertEqual(result.restoration, coverage.NOT_NEEDED)

    def test_no_activation_ever_passes_an_overwrite_flag(self):
        """FR-009, FR-049. Enforced by signature, asserted here as well because it is load-bearing."""
        with h.temp_project() as root:
            seed(root, installed=["kiro-cli", "claude"], default="kiro-cli", covered=["kiro-cli"])
            log = Path(root) / "argv.log"
            with h.fake_specify(argv_log=log, use_effect=root):
                coverage.apply(coverage.plan(root))
            for argv in h.read_argv_log(log):
                self.assertNotIn("--force", argv)


class Verification(unittest.TestCase):
    """Re-read state decides the outcome; an exit code alone never does (FR-006)."""

    def test_success_is_reported_from_the_registry(self):
        with h.temp_project() as root:
            seed(root, installed=["kiro-cli", "claude"], default="kiro-cli", covered=["kiro-cli"])
            with h.fake_specify(use_effect=root):
                result = coverage.apply(coverage.plan(root))
            self.assertEqual(result.outcome, coverage.COVERED)
            self.assertEqual(result.newly_covered, ("claude",))
            self.assertEqual(registry_agents(root), ["claude", "kiro-cli"])

    def test_exit_zero_without_registration_is_a_failure(self):
        """The stub exits 0 but writes nothing, which is exactly the dependency's cheerful no-op."""
        with h.temp_project() as root:
            seed(root, installed=["kiro-cli", "claude"], default="kiro-cli", covered=["kiro-cli"])
            with h.fake_specify():  # no use_effect: nothing is registered
                result = coverage.apply(coverage.plan(root))
            self.assertEqual(result.outcome, coverage.FAILED)
            child = next(c for c in result.parts if c.key == "claude")
            self.assertEqual(child.outcome, coverage.FAILED)
            self.assertEqual(child.detail, coverage.DETAIL_NO_REGISTRATION)

    def test_a_nonzero_activation_reports_its_code(self):
        with h.temp_project() as root:
            seed(root, installed=["kiro-cli", "claude"], default="kiro-cli", covered=["kiro-cli"])
            with h.fake_specify(use_effect=root, use_fails=["claude"]):
                result = coverage.apply(coverage.plan(root))
            child = next(c for c in result.parts if c.key == "claude")
            self.assertEqual(child.outcome, coverage.FAILED)
            self.assertIn("exited with code 1", child.detail)

    def test_already_covered_integrations_are_reported_as_such(self):
        with h.temp_project() as root:
            seed(root, installed=["kiro-cli", "claude", "copilot"], default="kiro-cli",
                 covered=["kiro-cli", "claude"])
            with h.fake_specify(use_effect=root):
                result = coverage.apply(coverage.plan(root))
            outcomes = {c.key: c.outcome for c in result.parts}
            self.assertEqual(outcomes["claude"], coverage.ALREADY_COVERED)
            self.assertEqual(outcomes["copilot"], coverage.NEWLY_COVERED)


class RestorationHolds(unittest.TestCase):
    """The promise: the project's default is what it was, on every path (FR-015, FR-016)."""

    def test_a_successful_rotation_restores_and_says_so(self):
        with h.temp_project() as root:
            seed(root, installed=["kiro-cli", "claude"], default="kiro-cli", covered=["kiro-cli"])
            with h.fake_specify(use_effect=root):
                result = coverage.apply(coverage.plan(root))
            self.assertEqual(result.restoration, coverage.RESTORED)
            self.assertEqual(recorded_default(root), "kiro-cli")

    def test_a_failed_activation_still_restores_and_still_tries_the_rest(self):
        """Story 4 scenario 2. One broken integration cannot strand the others or the default."""
        with h.temp_project() as root:
            seed(root, installed=["kiro-cli", "claude", "copilot"], default="kiro-cli",
                 covered=["kiro-cli"])
            log = Path(root) / "argv.log"
            with h.fake_specify(argv_log=log, use_effect=root, use_fails=["claude"]):
                result = coverage.apply(coverage.plan(root))
            self.assertEqual(h.integration_use_calls(log), ["claude", "copilot", "kiro-cli"])
            self.assertEqual(result.restoration, coverage.RESTORED)
            self.assertEqual(recorded_default(root), "kiro-cli")
            self.assertEqual(result.outcome, coverage.FAILED)

    def test_a_failed_restore_is_its_own_verdict(self):
        """FR-034. The one state where the project ends differently from how it started."""
        with h.temp_project() as root:
            seed(root, installed=["kiro-cli", "claude"], default="kiro-cli", covered=["kiro-cli"])
            with h.fake_specify(use_effect=root, use_fails=["kiro-cli"]):
                result = coverage.apply(coverage.plan(root))
            self.assertEqual(result.restoration, coverage.NOT_RESTORED)
            self.assertEqual(result.original_default, "kiro-cli")
            self.assertEqual(result.current_default, "claude")
            self.assertNotEqual(result.current_default, result.original_default)
            self.assertEqual(result.outcome, coverage.FAILED)

    def test_an_interrupt_restores_before_raising(self):
        """FR-016, FR-036. The user asked us to stop, not to leave their project re-pointed."""
        with h.temp_project() as root:
            seed(root, installed=["kiro-cli", "claude", "copilot"], default="kiro-cli",
                 covered=["kiro-cli"])
            log = Path(root) / "argv.log"
            calls = []
            real = coverage.extension.delegate_integration_use

            def interrupt_on_second(key):
                calls.append(key)
                if len(calls) == 2:
                    raise KeyboardInterrupt
                return real(key)

            with h.fake_specify(argv_log=log, use_effect=root):
                coverage.extension.delegate_integration_use = interrupt_on_second
                try:
                    with self.assertRaises(coverage.Interrupted) as raised:
                        coverage.apply(coverage.plan(root))
                finally:
                    coverage.extension.delegate_integration_use = real
            # The restore ran after the interrupt, so the default is back and the first agent stayed covered.
            self.assertEqual(recorded_default(root), "kiro-cli")
            self.assertIn("claude", registry_agents(root))
            result = raised.exception.args[0]
            unreached = next(c for c in result.parts if c.key == "copilot")
            self.assertEqual(unreached.outcome, coverage.SKIPPED)
            self.assertEqual(unreached.detail, coverage.DETAIL_NOT_REACHED)

    def test_an_exit_code_of_130_is_treated_as_an_interrupt(self):
        with h.temp_project() as root:
            seed(root, installed=["kiro-cli", "claude"], default="kiro-cli", covered=["kiro-cli"])
            real = coverage.extension.delegate_integration_use
            coverage.extension.delegate_integration_use = lambda key: 130
            try:
                with self.assertRaises(coverage.Interrupted):
                    coverage.apply(coverage.plan(root))
            finally:
                coverage.extension.delegate_integration_use = real

    def test_a_delegation_error_during_the_restore_does_not_replace_the_report(self):
        """The restore runs in a `finally`; an exception there would mask what the run was reporting."""
        with h.temp_project() as root:
            seed(root, installed=["kiro-cli", "claude"], default="kiro-cli", covered=["kiro-cli"])
            with h.fake_specify(use_effect=root):
                plan = coverage.plan(root)
                real = coverage.extension.delegate_integration_use

                def fail_on_restore(key):
                    if key == "kiro-cli":
                        raise coverage.extension.DelegationError("specify vanished")
                    return real(key)

                coverage.extension.delegate_integration_use = fail_on_restore
                try:
                    result = coverage.apply(plan)
                finally:
                    coverage.extension.delegate_integration_use = real
            self.assertEqual(result.restoration, coverage.NOT_RESTORED)
            self.assertEqual(result.outcome, coverage.FAILED)


class ConfigurationIsReturnedUnchanged(unittest.TestCase):
    """FR-043, SC-002, SC-013 — the project ends configured exactly as it started."""

    def test_committed_configuration_is_byte_identical_after_a_rotation(self):
        with h.temp_project() as root:
            seed(root, installed=["kiro-cli", "claude"], default="kiro-cli", covered=["kiro-cli"])
            config = Path(root) / ".specify" / "integration.json"
            before = config.read_bytes()
            with h.fake_specify(use_effect=root):
                coverage.apply(coverage.plan(root))
            self.assertEqual(config.read_bytes(), before)

    def test_the_recorded_default_matches_its_pre_run_value(self):
        """Three integrations, two of them uncovered — the longest rotation, same end state.

        The registry always names at least the default (Spec Kit registers it when the extension is
        installed), so "nothing covered at all" is not a representable readable state: an empty command map
        reads as unknown. Two uncovered out of three is the real worst case.
        """
        with h.temp_project() as root:
            seed(root, installed=["kiro-cli", "claude", "copilot"], default="kiro-cli",
                 covered=["kiro-cli"])
            with h.fake_specify(use_effect=root):
                coverage.apply(coverage.plan(root))
            self.assertEqual(recorded_default(root), "kiro-cli")
            self.assertEqual(registry_agents(root), ["claude", "copilot", "kiro-cli"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
