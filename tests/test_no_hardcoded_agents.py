"""The roster is data, not code (FR-042, SC-002).

Principle VI's promise — that a new agent reaches every installed CLI with no CLI release — only holds
if the CLI never carries its own copy of the roster. `spectra_cli/install.py` already refuses to
hard-code the set of extensions it installs, reading `catalog.json` at run time; these tests hold the
same line for agents.

The checks are deliberately structural rather than keyword-based. Single words like "Testing" and
"Implementation" are ordinary English and appear in docstrings; what would signal a hard-coded roster
is a *listing* — several agents named together, a command string, or a description copied across.
"""

from __future__ import annotations

import ast
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import helpers as h  # noqa: E402
from spectra_cli import roster  # noqa: E402

PACKAGE = h.repo_file("spectra_cli")


def package_sources():
    """Every shipped Python source file, as (name, text)."""
    return [(path.name, path.read_text(encoding="utf-8")) for path in sorted(PACKAGE.glob("*.py"))]


class RosterIsNotInTheCode(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parsed = roster.load(h.repo_file("agents-list.json"))
        cls.sources = package_sources()

    def test_no_agent_description_is_copied_into_the_package(self):
        """A description in the code is a second source of truth by definition."""
        for name, text in self.sources:
            for agent in self.parsed.agents:
                self.assertNotIn(agent.description, text,
                                 f"{name} carries the description of {agent.id!r}")

    def test_no_agent_command_string_is_hard_coded(self):
        for name, text in self.sources:
            for agent in self.parsed.agents:
                if agent.command:
                    self.assertNotIn(agent.command, text,
                                     f"{name} hard-codes the command for {agent.id!r}")

    def test_no_module_enumerates_several_agents(self):
        """One generic word is prose; three agent titles in one file is a list."""
        titles = [agent.title for agent in self.parsed.agents]
        for name, text in self.sources:
            found = [title for title in titles if title in text]
            self.assertLess(len(found), 3, f"{name} appears to enumerate agents: {found}")

    def test_no_module_hard_codes_the_agent_count(self):
        """The count is derived from the fetched roster, never asserted in the code."""
        total = str(len(self.parsed.agents))
        for name, text in self.sources:
            for phrase in (f"{total} agents", f"= {total}  #", f"AGENT_COUNT = {total}"):
                self.assertNotIn(phrase, text, f"{name} hard-codes the agent count")

    def test_no_module_hard_codes_an_agent_id_list(self):
        ids = [agent.id for agent in self.parsed.agents]
        for name, text in self.sources:
            found = [value for value in ids if f'"{value}"' in text or f"'{value}'" in text]
            self.assertLess(len(found), 3, f"{name} appears to hard-code agent ids: {found}")


class TheRosterIsReadAtRunTime(unittest.TestCase):
    def test_the_roster_path_is_a_published_location_not_a_bundled_file(self):
        self.assertEqual(roster.ROSTER_PATH, "agents-list.json")

    def test_no_copy_of_the_roster_ships_inside_the_package(self):
        self.assertEqual(list(PACKAGE.glob("*.json")), [],
                         "the package must not carry a bundled roster")

    def test_the_command_reads_the_roster_over_the_network(self):
        """If `agent-list` ever stopped fetching, this fails: the served roster is the only source."""
        import contextlib
        import io

        from spectra_cli import cli

        served = h.roster()
        h.agent(served, "brd")["title"] = "Invented By The Test Only"
        buffer = io.StringIO()
        with h.serve_roster(served) as base, h.raw_base(base), \
             h.temp_project(is_project=False) as path, h.cwd(path):
            with contextlib.redirect_stdout(buffer):
                code = cli.main(["agent-list"])
        self.assertEqual(code, 0)
        self.assertIn("Invented By The Test Only", buffer.getvalue())


# --- helpers for the f-string floor check ---------------------------------------------------------------
# Deliberately textual. The point of this check is to hold on an interpreter whose tokenizer disagrees with
# the floor, so it cannot delegate to that tokenizer.

_F_PREFIX = re.compile(r"""(?<![\w"'])(?:[fF][rRbB]?|[rRbB][fF])('''|\"\"\"|'|")""")


def _f_string_literals(line):
    """(delimiter, body) for each f-string literal on one line; unterminated literals are skipped."""
    found = []
    position = 0
    while True:
        match = _F_PREFIX.search(line, position)
        if match is None:
            return found
        delimiter = match.group(1)
        start = match.end()
        index = start
        while index < len(line):
            if line[index] == "\\":
                index += 2
                continue
            if line.startswith(delimiter, index):
                found.append((delimiter[0], line[start:index]))
                break
            index += 1
        position = max(index, start) + 1


def _replacement_fields(body):
    """`(text, terminated)` for each `{...}` field of an f-string body; `{{`/`}}` escapes ignored.

    `terminated` is the interesting half. When a field's `}` is missing, the literal was almost certainly
    closed early by a same-type quote *inside* the field — the PEP 701 construct that parses on 3.12+ and is a
    `SyntaxError` on 3.9. A genuinely unclosed brace is a bug either way.
    """
    fields = []
    index = 0
    while index < len(body):
        if body[index] == "{":
            if body.startswith("{{", index):
                index += 2
                continue
            depth = 1
            index += 1
            start = index
            terminated = False
            while index < len(body):
                if body[index] == "{":
                    depth += 1
                elif body[index] == "}":
                    depth -= 1
                    if depth == 0:
                        terminated = True
                        break
                index += 1
            fields.append((body[start:index], terminated))
        index += 1
    return fields


class EverySourceFileParsesOnTheOldestSupportedPython(unittest.TestCase):
    """`pyproject.toml` claims `>=3.9`, and CI runs 3.9 — so the *grammar* has to hold there too.

    This exists because of a real escape: a test fixture used escaped quotes inside an f-string expression,
    which PEP 701 legalized in 3.12. It parsed on the developer's 3.14 and was a `SyntaxError` on 3.9, taking
    down fifteen test modules at import time — a failure the whole local suite could not see. `ast.parse`
    with `feature_version` reproduces the older grammar without needing the older interpreter.
    """

    ROOTS = ("spectra_cli", "tests", "tools")
    OLDEST = (3, 9)

    def test_no_file_uses_syntax_newer_than_the_declared_floor(self):
        offences = []
        for root in self.ROOTS:
            for path in sorted(h.repo_file(root).glob("*.py")):
                try:
                    ast.parse(path.read_text(encoding="utf-8"), filename=str(path),
                              feature_version=self.OLDEST)
                except SyntaxError as exc:
                    offences.append(f"{path.name}:{exc.lineno}: {exc.msg}")
        self.assertEqual(offences, [],
                         "these files need syntax that Python "
                         f"{'.'.join(map(str, self.OLDEST))} does not have:\n"
                         + "\n".join(offences))

    def test_the_floor_matches_what_the_package_declares(self):
        """If `requires-python` moves, this test must move with it — not be quietly outgrown."""
        declared = h.repo_file("pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('requires-python = ">=3.9"', declared)

    def test_no_f_string_nests_its_own_quote_or_a_backslash(self):
        """The one thing `feature_version` cannot see, checked textually instead.

        `ast.parse(..., feature_version=(3, 9))` does not reproduce the *old f-string tokenizer*: on 3.12+
        the new one accepts same-type nested quotes and backslashes inside replacement fields (PEP 701) no
        matter what `feature_version` says. So the sibling test above passes on a modern machine and fails in
        CI on 3.9 — which is exactly what happened twice: once with an escaped quote in a fixture, once with a
        message whose replacement field re-used the enclosing double quote around a literal, each taking down
        whole modules at import time.

        This check does not need an interpreter's opinion. It reads the f-string literals and asserts their
        replacement fields are closed on the line, and contain neither the delimiter that ends the literal nor
        a backslash. (It cannot carry a worked example: written out, the example would trip the check — which
        is itself the demonstration.)
        """
        offences = []
        for root in self.ROOTS:
            for path in sorted(h.repo_file(root).glob("*.py")):
                source = path.read_text(encoding="utf-8")
                for line_no, line in enumerate(source.splitlines(), 1):
                    for delimiter, body in _f_string_literals(line):
                        for field, terminated in _replacement_fields(body):
                            where = "%s:%d" % (path.name, line_no)
                            if not terminated:
                                offences.append(
                                    "%s: f-string field %r is not closed on this line — usually a "
                                    "same-type quote inside it (PEP 701, Python 3.12+)" % (where, field)
                                )
                            elif delimiter in field:
                                offences.append(
                                    "%s: f-string field %r reuses its own %s quote "
                                    "(PEP 701, Python 3.12+)" % (where, field, delimiter)
                                )
                            elif "\\" in field:
                                offences.append(
                                    "%s: f-string field %r contains a backslash "
                                    "(PEP 701, Python 3.12+)" % (where, field)
                                )
        self.assertEqual(
            offences,
            [],
            "these f-strings only parse on 3.12+, and the floor is "
            + ".".join(map(str, self.OLDEST))
            + ":\n"
            + "\n".join(offences),
        )


class CoverageCarriesNoAgentKnowledge(unittest.TestCase):
    """`coverage.py` acts on integrations it was told about, and does nothing else to them.

    Four prohibitions from spec 011, each cheap to assert at the source level and expensive to discover by
    hand once broken. The module rotates a project's default integration, so what it *cannot* do matters as
    much as what it does.
    """

    KNOWN_INTEGRATION_KEYS = ("kiro-cli", "claude", "copilot", "cursor", "gemini", "codex",
                              "windsurf", "qwen", "opencode", "roo", "codebuddy", "amp", "vibe")

    @classmethod
    def setUpClass(cls):
        cls.source = (PACKAGE / "coverage.py").read_text(encoding="utf-8")
        # Docstrings name agents as examples, which is prose rather than a roster. Strip them so the
        # assertions below read the executable code only.
        cls.code = re.sub(r'""".*?"""', "", cls.source, flags=re.S)

    def test_no_integration_key_appears_as_a_literal(self):
        """FR-046. The set of integrations comes from project state at run time, never from constants."""
        for key in self.KNOWN_INTEGRATION_KEYS:
            self.assertNotIn(f'"{key}"', self.code, f"coverage.py hard-codes the {key!r} key")
            self.assertNotIn(f"'{key}'", self.code, f"coverage.py hard-codes the {key!r} key")

    def test_it_never_installs_removes_or_switches_an_integration(self):
        """FR-045. Spectra covers the integrations a project has; it does not curate them."""
        for forbidden in ("integration\", \"install", "integration\", \"remove",
                          "integration\", \"switch", "integration\", \"uninstall"):
            self.assertNotIn(forbidden, self.code)
        # The one delegation it is allowed to reach for, named explicitly so a second one stands out.
        self.assertIn("delegate_integration_use", self.code)
        self.assertNotIn("delegate_integration_upgrade", self.code)
        self.assertNotIn("delegate_remove", self.code)

    def test_it_makes_no_network_call_and_holds_no_credential(self):
        """FR-048. Coverage is a local question about local files."""
        for forbidden in ("urllib", "http", "requests", "socket", "token", "Authorization"):
            self.assertNotIn(forbidden, self.code)

    def test_it_cannot_express_an_overwrite(self):
        """FR-009, FR-049 — enforced by `delegate_integration_use` having no such parameter."""
        self.assertNotIn("force", self.code)
        signature = (PACKAGE / "extension.py").read_text(encoding="utf-8")
        self.assertIn("def delegate_integration_use(key: str) -> int:", signature)

    def test_it_never_consults_the_dependency_version(self):
        """FR-051. Support is decided by the presence of state, not by a version comparison."""
        self.assertNotIn("compare_versions", self.code)
        self.assertNotIn("speckit_version", self.code)


if __name__ == "__main__":
    unittest.main()
