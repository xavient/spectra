"""Constitution Principle VII, asserted against the files that ship.

Principle VII says every command producing a durable Markdown deliverable writes it to
`<artifact-root>/<artifact>/` — lowercase, project-relative, one artifact type per folder — where the root
is `docs/` unless the project declares another. Before 1.6.0 the two document agents each answered that
question for themselves: `adr` wrote `Docs/ADR/` and `brd` wrote `/brds`. Nothing stopped them, because a
command file is prose and prose does not fail a build.

This file is what stops the next one. It reads the shipped command files as text and holds them to the
principle — including that both still resolve the declared root and check whether `docs/` is a published
site source before defaulting into it. The tricky part is that legacy folders must still be *mentioned* —
the commands are required to read them for numbering continuity, to say they leave them alone, and to offer
a `git mv`. So the assertions are shaped around that: a legacy path may appear only in a line that is
discussing legacy handling, and never on a line that instructs a write.

Standard library only, like the rest of the suite.
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import helpers as h  # noqa: E402

COMMANDS_DIR = h.repo_file("spectra", "commands")
MANIFEST = h.repo_file("spectra", "extension.yml")
CONSTITUTION = h.repo_file(".specify", "memory", "constitution.md")

# The canonical output folder for each document-producing command, per Principle VII.
CANONICAL = {
    "adr.md": "docs/adr/",
    "brd.md": "docs/brd/",
    "impact.md": "docs/impact-analysis/",
}

# Output locations shipped before 1.6.0. Still readable by the commands, never writable.
#
# The ADR pattern is deliberately case-insensitive and then filters out the exact lowercase form:
# `Docs/ADR` and `docs/ADR` are legacy, `docs/adr` is canonical, and on a case-insensitive macOS
# filesystem they are all the same directory — which is the reason the convention is lowercase-only.
LEGACY_ADR = re.compile(r"docs/adr", re.IGNORECASE)
LEGACY_BRD = re.compile(r"(?<![\w/`])brds/")

# A line that tells the agent to put something somewhere. On the same line as a legacy folder, it means
# the command is writing to the legacy folder.
WRITE_INSTRUCTION = re.compile(
    r"\b(write|writes|writing|create the file|Ensure the directory|git add)\b",
    re.IGNORECASE,
)

# Lines that are *about* the old location rather than using it: the legacy-read clause, the "not this,
# that" correction, and the `git mv` the user may run. A legacy path is allowed only in this company,
# and the window below extends it over a wrapped paragraph.
LEGACY_CONTEXT = re.compile(
    r"legacy|before 1\.6\.0|git mv|no longer|not `|read-only|case-insensitiv",
    re.IGNORECASE,
)
CONTEXT_WINDOW = 2

SLUG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
DOCS_REFERENCE = re.compile(r"docs/([A-Za-z0-9][^/`\s)]*)/")
ABSOLUTE_PATHS = ("`/brds", "`/docs/", " /brds/", " /docs/")

# The declared-root machinery. A document command has to read the declaration, honour it, and refuse to
# write it — and it has to check whether `docs/` is published before defaulting there.
ROOT_DECLARATION = "Artifact root:"
PUBLICATION_SIGNALS = (
    "mkdocs.yml",
    "docusaurus.config",
    "docs/_config.yml",
    "docs/.nojekyll",
    "docs/index.html",
    "docs/conf.py",
)
DOCUMENT_COMMANDS = tuple(CANONICAL)


def command_files() -> list[Path]:
    files = sorted(COMMANDS_DIR.glob("*.md"))
    assert files, f"no command files found under {COMMANDS_DIR}"
    return files


def legacy_hits(line: str) -> list[str]:
    """Legacy folder references on this line, canonical `docs/adr` excluded."""
    hits = [m.group(0) for m in LEGACY_ADR.finditer(line) if m.group(0) != "docs/adr"]
    hits += [m.group(0) for m in LEGACY_BRD.finditer(line)]
    return hits


def in_legacy_context(lines: list[str], index: int) -> bool:
    start = max(0, index - CONTEXT_WINDOW)
    return any(LEGACY_CONTEXT.search(line) for line in lines[start : index + 1])


class CanonicalOutputPaths(unittest.TestCase):
    """The two document agents write to `docs/<artifact>/` and say so."""

    def test_each_document_command_names_its_canonical_folder(self):
        for name, folder in CANONICAL.items():
            with self.subTest(command=name):
                text = (COMMANDS_DIR / name).read_text(encoding="utf-8")
                self.assertTrue(folder in text, f"{name} no longer names {folder}")

    def test_the_adr_write_target_is_the_canonical_path(self):
        text = (COMMANDS_DIR / "adr.md").read_text(encoding="utf-8")
        self.assertTrue(
            "docs/adr/ADR-NNN-<kebab-case-title>.md" in text,
            "adr.md no longer shows the default write target docs/adr/ADR-NNN-<kebab-case-title>.md",
        )

    def test_the_brd_write_target_is_the_canonical_path(self):
        text = (COMMANDS_DIR / "brd.md").read_text(encoding="utf-8")
        self.assertTrue(
            "docs/brd/NNN-<kebab-title>.md" in text,
            "brd.md no longer shows the default write target docs/brd/NNN-<kebab-title>.md",
        )

    def test_no_write_instruction_names_a_legacy_folder(self):
        """Mentioning `Docs/ADR/` is required; being told to write there is the regression."""
        for path in command_files():
            lines = path.read_text(encoding="utf-8").splitlines()
            for number, line in enumerate(lines, 1):
                if "git mv" in line:
                    continue  # the migration suggestion names both folders by necessity
                if not legacy_hits(line):
                    continue
                with self.subTest(command=path.name, line=number):
                    self.assertIsNone(
                        WRITE_INSTRUCTION.search(line),
                        f"{path.name}:{number} pairs a write instruction with a pre-1.6.0 output "
                        f"folder; Principle VII requires docs/<artifact>/ — {line.strip()!r}",
                    )

    def test_legacy_folders_are_only_mentioned_as_legacy(self):
        """A stray legacy path outside the legacy-handling clauses is drift."""
        for path in command_files():
            lines = path.read_text(encoding="utf-8").splitlines()
            for index, line in enumerate(lines):
                hits = legacy_hits(line)
                if not hits:
                    continue
                with self.subTest(command=path.name, line=index + 1, hits=tuple(hits)):
                    self.assertTrue(
                        in_legacy_context(lines, index),
                        f"{path.name}:{index + 1} names {hits} outside any legacy-handling clause "
                        f"— {line.strip()!r}",
                    )

    def test_no_command_uses_an_absolute_output_path(self):
        """`/brds` and `/docs/` name the filesystem root, not the project."""
        for path in command_files():
            lines = path.read_text(encoding="utf-8").splitlines()
            for index, line in enumerate(lines):
                if in_legacy_context(lines, index):
                    continue  # e.g. "not `/docs/adr/`", which states the rule by negation
                for token in ABSOLUTE_PATHS:
                    with self.subTest(command=path.name, line=index + 1, token=token):
                        self.assertNotIn(
                            token,
                            line,
                            f"{path.name}:{index + 1} names an absolute path ({token.strip()}); "
                            f"output paths MUST be project-relative — {line.strip()!r}",
                        )

    def test_every_docs_reference_uses_a_lowercase_kebab_slug(self):
        for path in command_files():
            lines = path.read_text(encoding="utf-8").splitlines()
            for index, line in enumerate(lines):
                if in_legacy_context(lines, index):
                    continue
                for slug in DOCS_REFERENCE.findall(line):
                    with self.subTest(command=path.name, line=index + 1, slug=slug):
                        self.assertRegex(
                            slug,
                            SLUG,
                            f"{path.name}:{index + 1} references docs/{slug}/; Principle VII "
                            "requires a lowercase kebab-case slug",
                        )


class TheDeclaredRoot(unittest.TestCase):
    """`docs/` is the default, not a hard-coded path — and defaulting there is checked first."""

    def test_each_document_command_reads_the_declaration(self):
        for name in DOCUMENT_COMMANDS:
            with self.subTest(command=name):
                text = (COMMANDS_DIR / name).read_text(encoding="utf-8")
                self.assertTrue(
                    ROOT_DECLARATION in text,
                    f"{name} no longer resolves the project's declared artifact root; Principle VII "
                    "requires every document command to honour it",
                )

    def test_each_document_command_refuses_to_write_the_declaration(self):
        """Producing a document is not a licence to edit governance."""
        for name in DOCUMENT_COMMANDS:
            with self.subTest(command=name):
                text = (COMMANDS_DIR / name).read_text(encoding="utf-8")
                self.assertTrue(
                    "never write it" in text,
                    f"{name} no longer states that it offers the declaration without writing it",
                )

    def test_each_document_command_checks_for_a_published_docs_folder(self):
        """Pages, MkDocs and Docusaurus all make `docs/` a publishing source."""
        for name in DOCUMENT_COMMANDS:
            text = (COMMANDS_DIR / name).read_text(encoding="utf-8")
            for signal in PUBLICATION_SIGNALS:
                with self.subTest(command=name, signal=signal):
                    self.assertTrue(
                        signal in text,
                        f"{name} no longer looks for {signal} before defaulting into docs/",
                    )

    def test_each_document_command_prefers_the_non_publishing_fallback(self):
        for name in DOCUMENT_COMMANDS:
            with self.subTest(command=name):
                text = (COMMANDS_DIR / name).read_text(encoding="utf-8")
                self.assertTrue(
                    "documents/" in text,
                    f"{name} no longer recommends a non-publishing root when docs/ is published",
                )


class PublishedDescriptions(unittest.TestCase):
    """What the manifest advertises has to match where the command actually writes."""

    def test_the_manifest_names_no_legacy_folder(self):
        for number, line in enumerate(MANIFEST.read_text(encoding="utf-8").splitlines(), 1):
            hits = legacy_hits(line)
            with self.subTest(line=number):
                self.assertEqual(
                    [],
                    hits,
                    f"spectra/extension.yml:{number} still advertises a pre-1.6.0 output folder "
                    f"{hits}",
                )

    def test_the_manifest_advertises_the_canonical_brd_folder(self):
        self.assertIn("docs/brd/", MANIFEST.read_text(encoding="utf-8"))


class TheConstitutionStatesTheRule(unittest.TestCase):
    """The guard above is only legitimate because the constitution says so."""

    @classmethod
    def setUpClass(cls):
        text = CONSTITUTION.read_text(encoding="utf-8")
        cls.full = text
        principle = text.split("### VII. Document Artifacts Live Under")[1]
        cls.principle = principle.split("## Publishing & Distribution Standards")[0]

    def test_principle_vii_exists(self):
        self.assertIn("### VII. Document Artifacts Live Under One Declared Root", self.full)

    def test_principle_vii_carves_out_spec_kit_locations(self):
        """`domain-analyzer` writes `.specify/memory/domain-analysis.md` and stays compliant."""
        self.assertIn(".specify/", self.principle)
        self.assertIn("specs/", self.principle)

    def test_principle_vii_requires_the_legacy_read(self):
        self.assertIn("earlier version wrote to", self.principle)

    def test_principle_vii_makes_the_root_declarable(self):
        self.assertIn(ROOT_DECLARATION, self.principle)
        self.assertIn("defaults to `docs/`", self.principle)

    def test_principle_vii_requires_the_publication_check(self):
        for signal in ("mkdocs.yml", "docusaurus.config", "Pages"):
            with self.subTest(signal=signal):
                self.assertIn(signal, self.principle)

    def test_principle_vii_forbids_writing_the_declaration(self):
        self.assertIn("MUST NOT write that declaration", self.principle)


if __name__ == "__main__":
    unittest.main()
