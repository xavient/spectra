"""Constitution Principle VIII, asserted against the files that ship.

Principle VIII says a document command's structure comes from a **registered** template **resolved through
Spec Kit's stack**, with an inline skeleton as the last resort — never from a literal baked into the command
and never from a hard-coded path. Before 1.7.0 both halves were broken: `adr` carried its structure as a
fenced block inside the command, and `brd` read one hard-coded path, so a project override at
`.specify/templates/overrides/brd-template.md` was silently ignored.

These are text assertions on the shipped artifacts, which is the enforceable surface for prompt files. The
invariant worth the most here is the last one: a shipped template and an inline skeleton that disagree is a bug
nobody notices, because the skeleton only runs in the rare no-`.specify/` case.

Standard library only, like the rest of the suite.
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import helpers as h  # noqa: E402

TEMPLATES_DIR = h.repo_file("spectra", "templates")
COMMANDS_DIR = h.repo_file("spectra", "commands")
MANIFEST = h.repo_file("spectra", "extension.yml")
CONSTITUTION = h.repo_file(".specify", "memory", "constitution.md")

# Each document command and the template it is shaped by.
DOCUMENT_COMMANDS = {
    "adr.md": "adr-template",
    "brd.md": "brd-template",
    "create-pr.md": "pr-template",
}

# The resolution stack, in priority order. Every document command must name all of it.
LAYERS = (
    ".specify/templates/overrides/",
    ".specify/presets/",
    ".specify/extensions/spectra/templates/",
    ".specify/templates/",
)

# The constitution states the same stack generically — `<ext-id>`, not `spectra`.
CONSTITUTION_LAYERS = (
    ".specify/templates/overrides/",
    ".specify/presets/",
    ".specify/extensions/",
    ".specify/templates/",
)

# A manifest entry looks like:
#     - name: "adr-template"
#       file: "templates/adr-template.md"
TEMPLATE_ENTRY = re.compile(
    r'^    - name: "([a-z0-9-]+)"\n      file: "([^"]+)"', re.M
)
# Sections are H2s. The H1 is the document title, whose placeholder style differs by design between a
# fill-in template (`[PRODUCT / FEATURE NAME]`) and a skeleton (`<Title>`), and subsections come and go.
SECTION = re.compile(r"^## +(.+?)\s*$", re.M)
# Guidance that trails a section name is annotation, not structure: the BRD template writes
# `## 6. User Journeys *(feeds the spec's prioritized user stories)*` where the skeleton writes
# `## 6. User Journeys   <!-- prioritized; actor/trigger/… -->`. Same section, different hint.
ANNOTATION = re.compile(r"\s*(?:<!--|\*\().*$", re.S)
# Executable or binary content has no business in a Markdown-only package.
FORBIDDEN_SUFFIXES = {".sh", ".ps1", ".py", ".bash", ".zsh", ".exe", ".bin", ".dylib", ".so"}


def manifest_templates() -> dict:
    """`provides.templates` as {name: file}, parsed without a YAML dependency.

    The repository is zero-dependency by constitution, and `yaml` is not importable here — the CLI's own
    manifest reader is regex-based for the same reason.
    """
    text = MANIFEST.read_text(encoding="utf-8")
    block = text.split("\n  templates:\n", 1)
    if len(block) == 1:
        return {}
    # Stop at the next top-level key (a line with no leading whitespace).
    tail = re.split(r"\n(?=\S)", block[1], maxsplit=1)[0]
    return {name: file for name, file in TEMPLATE_ENTRY.findall(tail)}


def sections(text: str) -> list:
    """H2 section names, with trailing guidance annotations stripped.

    Comparing whole heading lines would fail on cosmetics — a template writes
    `## 3. Business Objectives & Goals` while the skeleton annotates the same heading with
    `<!-- G1, G2, … -->`. The invariant that matters is the section *list*, in order.
    """
    return [ANNOTATION.sub("", name).strip() for name in SECTION.findall(text)]


def inline_skeleton(command_text: str) -> str:
    """The fenced block under the command's 'Inline template skeleton' section."""
    _, _, tail = command_text.partition("Inline template skeleton")
    fences = re.findall(r"```(?:markdown)?\n(.*?)```", tail, re.S)
    return fences[0] if fences else ""


class TemplatesAreShipped(unittest.TestCase):
    """One asset per document type, under spectra/templates/."""

    def test_each_document_command_has_a_shipped_template(self):
        for command, name in DOCUMENT_COMMANDS.items():
            with self.subTest(command=command):
                path = TEMPLATES_DIR / f"{name}.md"
                self.assertTrue(
                    path.is_file(),
                    f"{command} is shaped by {name}, but spectra/templates/{name}.md does not exist",
                )

    def test_no_shipped_template_is_empty(self):
        for path in sorted(TEMPLATES_DIR.glob("*.md")):
            with self.subTest(template=path.name):
                self.assertTrue(
                    path.read_text(encoding="utf-8").strip(),
                    f"{path.name} is empty; a template with no structure shapes nothing",
                )

    def test_the_package_stays_markdown_only(self):
        """Principle VIII keeps resolution in prose precisely so no script has to ship."""
        for path in sorted(h.repo_file("spectra").rglob("*")):
            if path.is_dir():
                continue
            with self.subTest(path=str(path.relative_to(h.repo_file("spectra")))):
                self.assertNotIn(
                    path.suffix.lower(),
                    FORBIDDEN_SUFFIXES,
                    f"{path.name} would ship an executable in a package documented as Markdown-only",
                )


class TemplatesAreRegistered(unittest.TestCase):
    """`provides.templates` and the directory must describe the same set, both ways."""

    @classmethod
    def setUpClass(cls):
        cls.registered = manifest_templates()

    def test_the_manifest_declares_templates_at_all(self):
        self.assertTrue(
            self.registered,
            "spectra/extension.yml has no provides.templates block; Principle VIII requires templates "
            "to be declared, not merely present",
        )

    def test_every_shipped_template_is_registered(self):
        for path in sorted(TEMPLATES_DIR.glob("*.md")):
            with self.subTest(template=path.name):
                self.assertIn(
                    path.stem,
                    self.registered,
                    f"spectra/templates/{path.name} ships but is not declared in provides.templates",
                )

    def test_every_registered_template_exists(self):
        for name, file in sorted(self.registered.items()):
            with self.subTest(template=name):
                self.assertTrue(
                    (h.repo_file("spectra") / file).is_file(),
                    f"provides.templates declares {name} -> {file}, which does not exist",
                )

    def test_registered_names_match_their_filenames(self):
        """The resolver keys on the name; a mismatch would make the override path a lie."""
        for name, file in sorted(self.registered.items()):
            with self.subTest(template=name):
                self.assertEqual(
                    f"templates/{name}.md",
                    file,
                    f"{name} points at {file}; the stack resolves <name>.md, so they must agree",
                )


class CommandsResolveThroughTheStack(unittest.TestCase):
    """No hard-coded path, and every layer named."""

    def test_each_command_names_every_resolution_layer(self):
        for command in DOCUMENT_COMMANDS:
            text = (COMMANDS_DIR / command).read_text(encoding="utf-8")
            for layer in LAYERS:
                with self.subTest(command=command, layer=layer):
                    self.assertTrue(
                        layer in text,
                        f"{command} no longer names the {layer} layer of the template stack",
                    )

    def test_each_command_names_the_override_layer_first(self):
        """Priority is the whole point: the project's own template has to win."""
        for command, name in DOCUMENT_COMMANDS.items():
            text = (COMMANDS_DIR / command).read_text(encoding="utf-8")
            override = text.find(f".specify/templates/overrides/{name}.md")
            extension = text.find(f".specify/extensions/spectra/templates/{name}.md")
            with self.subTest(command=command):
                self.assertNotEqual(-1, override, f"{command} does not name the project override path")
                self.assertNotEqual(-1, extension, f"{command} does not name the extension template path")
                self.assertLess(
                    override,
                    extension,
                    f"{command} lists the extension copy before the project override; the override "
                    "must be resolved first",
                )

    def test_each_command_reports_the_template_it_used(self):
        for command in DOCUMENT_COMMANDS:
            text = (COMMANDS_DIR / command).read_text(encoding="utf-8").lower()
            with self.subTest(command=command):
                self.assertTrue(
                    "template you used" in text or "which template you used" in text,
                    f"{command} no longer reports which template it resolved; an override that failed "
                    "to apply would be invisible",
                )

    def test_each_command_keeps_an_inline_last_resort(self):
        for command in DOCUMENT_COMMANDS:
            text = (COMMANDS_DIR / command).read_text(encoding="utf-8")
            with self.subTest(command=command):
                self.assertIn("Inline template skeleton", text)
                self.assertTrue(
                    inline_skeleton(text).strip(),
                    f"{command} has an inline-skeleton section with no skeleton in it",
                )

    def test_no_command_treats_one_path_as_the_only_template(self):
        """The 1.6.0 bug: `brd` read the extension copy and nothing else."""
        for command in DOCUMENT_COMMANDS:
            text = (COMMANDS_DIR / command).read_text(encoding="utf-8")
            with self.subTest(command=command):
                self.assertNotIn(
                    "load the canonical template shipped with this extension at",
                    text,
                    f"{command} reads a single hard-coded template path again",
                )


class ShippedAndInlineStructuresAgree(unittest.TestCase):
    """The invariant nobody would notice breaking, because the skeleton rarely runs."""

    def test_sections_match_in_order(self):
        for command, name in DOCUMENT_COMMANDS.items():
            template = (TEMPLATES_DIR / f"{name}.md").read_text(encoding="utf-8")
            skeleton = inline_skeleton((COMMANDS_DIR / command).read_text(encoding="utf-8"))
            with self.subTest(command=command, template=name):
                self.assertEqual(
                    sections(template),
                    sections(skeleton),
                    f"spectra/templates/{name}.md and the inline skeleton in {command} declare "
                    "different sections; a project without .specify/ would get a differently-shaped "
                    "document",
                )


class TheConstitutionStatesTheRule(unittest.TestCase):
    """The guard above is only legitimate because the constitution says so."""

    @classmethod
    def setUpClass(cls):
        text = CONSTITUTION.read_text(encoding="utf-8")
        cls.full = text
        principle = text.split("### VIII. Documents Are Shaped by Overridable Templates")[1]
        cls.principle = principle.split("## Publishing & Distribution Standards")[0]

    def test_principle_viii_exists(self):
        self.assertIn("### VIII. Documents Are Shaped by Overridable Templates", self.full)

    def test_principle_viii_requires_registration(self):
        self.assertIn("provides.templates", self.principle)

    def test_principle_viii_names_the_stack(self):
        for layer in CONSTITUTION_LAYERS:
            with self.subTest(layer=layer):
                self.assertTrue(
                    layer in self.principle,
                    f"Principle VIII no longer names the {layer} layer",
                )

    def test_principle_viii_forbids_a_hard_coded_path(self):
        flat = " ".join(self.principle.split())
        self.assertTrue(
            "MUST NOT hard-code a single template path" in flat,
            "Principle VIII no longer forbids hard-coding a template path",
        )

    def test_principle_viii_requires_honouring_the_template(self):
        self.assertTrue(
            "honoured, not repaired" in self.principle,
            "Principle VIII no longer requires a resolved template to be honoured as authored",
        )

    def test_principle_viii_keeps_resolution_in_prose(self):
        self.assertTrue(
            "prompt instructions" in self.principle,
            "Principle VIII no longer requires resolution to be prompt-expressed",
        )


if __name__ == "__main__":
    unittest.main()
