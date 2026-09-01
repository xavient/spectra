# IP Audit Findings

**Scope:** `xavient/spectra`, audited at commit `1b0cad6` on 2026-08-31 as part of the licensing and
IP remediation described in `CONTRIBUTING.md` → [Licensing and IP](../CONTRIBUTING.md#licensing-and-ip).

**Status: report only.** Nothing in this document was fixed by the change that created it. Every item
here either needs a legal decision, needs a fact only a human can confirm, or is a judgement call
about naming and scope that belongs to the repository owner. The mechanical remediation — the
trademark carve-out, the third-party attributions, the disclaimers, `SECURITY.md`, the SPDX headers —
landed separately and is not repeated here.

*Not legal advice. This document exists to surface issues for TELUS Digital legal and the open source
review process.*

---

## 1. Normative standard text in shipped agents

**Finding: clean. No action needed today, but the rule now needs enforcing as the roadmap ships.**

Every file under `spectra/commands/` (6 files) and `spectra/templates/` (4 files) was checked for
reproduced requirement text from a copyrighted standard. **There is none.** The published package is
16 Markdown and text files with no quoted normative language anywhere.

Standards and regulations are named in exactly three places, all nominative use:

| Location | What it says | Assessment |
|---|---|---|
| `spectra/commands/domain-analyzer.md:63-66` | "health → HIPAA, EU personal data → GDPR, card payments → PCI-DSS" as domain→regime examples, with an explicit "advisory-only … You do **not** implement or enable any compliance framework" | Nominative use of statutory and scheme names. No clause text, no paraphrase of requirements. |
| `spectra/commands/review-pr.md:432,441` | "violates an explicit compliance or regulatory requirement" as an abstract severity category | Names no standard at all. |
| `spectra/templates/adr-template.md:16` | "Compliance Impact" offered as an optional ADR section name | Not a standard reference. |

This is the expected result: most compliance agents are still 🚧 on the roadmap, so the surface that
could carry infringing text does not exist yet. **The exposure is entirely prospective.** The rule
written into `CONTRIBUTING.md` — paraphrase and clause reference, never quotation — needs to hold as
those 31 planned agents are authored, and each one should be reviewed against it before it ships.

---

## 2. Agent naming — certification implications

**Finding: four roadmap agents are named after certification schemes rather than after the work.
Renaming is nearly free now and expensive later.**

`agents-list.json` declares 46 agents: 15 available (13 distinct commands) and 31 planned. **None of
the flagged agents has shipped** — every one below is `"status": "planned"` with no `command` field,
and `README.md` carries an explicit hedge that most are still under development.

### 2a. Titles that are bare standard names

| id | Current title | Concern |
|---|---|---|
| `iso-27001-27701` | ISO 27001 / 27701 | ISO and IEC assert rights in standard designations and restrict use implying conformity assessment. |
| `soc-2` | SOC 2 | AICPA scheme name; "SOC 2" is tied to an attestation performed by a licensed CPA firm. |
| `pci-dss` | PCI-DSS | PCI SSC mark, tied to a qualified-assessor regime. |
| `fda-part-11-iec-62304` | FDA 21 CFR Part 11 & IEC 62304 | Mixes a public-domain US regulation (fine) with an IEC standard designation (not). |

Compare the siblings that already carry a qualifier and read correctly: *GDPR **Compliance***,
*Accessibility & WCAG **Compliance***, *SOX **Change-Management***, *Observability **Readiness***,
*Internationalization **Readiness***. The house style already exists; these four just do not follow
it. Suggested: "ISO 27001/27701 Readiness", "SOC 2 Readiness", "PCI-DSS Readiness", "Medical-Device
Software Readiness (21 CFR Part 11, IEC 62304)".

### 2b. "Audit" as the leading verb

Five descriptions open with "Audit …" — `iso-27001-27701`, `hipaa`, `accessibility-wcag`,
`responsible-ai-bias`, and `architecture-reviewer`. "Audit" is a term of art in SOC 2 and ISO contexts implying an independent assessment by
an accredited party. "Assess", "review", or "check" carry the meaning without the implication.

### 2c. Descriptions promising formal artifacts

| id | Phrase | Owner of the artifact |
|---|---|---|
| `accessibility-wcag` | "scaffold a VPAT" | VPAT is an ITI-owned document format |
| `soc-2` | "Map controls to the AICPA Trust Services Criteria" | AICPA-copyrighted framework |
| `gdpr` | "scaffold Article 30 records" | EU regulation text — public domain, low risk |
| `eu-ai-act` | "Annex IV documentation" | EU regulation text — public domain, low risk |
| `carbon-green-software` | "the ISO-standard SCI methodology" | Green Software Foundation / ISO/IEC 21031 |

### 2d. Clause-level citations in descriptions

`hipaa` cites §164.312; `pci-dss` cites v4.0.1; `iso-27001-27701` cites Annex A; `accessibility-wcag`
cites WCAG 2.2 AA, ADA, Section 508, and EN 301 549. **Citation by reference is not a copyright
problem** — it is the correct way to reference a standard. It does raise the certification
implication, because clause-level citation signals clause-level coverage.

### 2e. Cost of renaming

`agents-list.json` is the single source of truth and the generator propagates a rename to
`README.md`, `AGENTS_LIST.md`, `spectra/README.md`, `docs/agents.html`, and `spectra agent-list`. But
**several tests assert on literal title strings** — for example `tests/test_generator.py:351` asserts
`"GDPR Compliance"`, and `tests/helpers.py:539-540` carries fixture copies. A rename is a roster
change plus a test change, not a roster change alone.

**Decision needed:** whether to rename now, and whether to add a naming rule to the roster schema so
the next author cannot reintroduce the pattern. `CONTRIBUTING.md` item 3 now states the rule in prose;
nothing enforces it.

---

## 3. Asset provenance

**Finding: no provenance is documented for any asset in the repository, anywhere — not in a credits
file, not in the docs, not in a commit message.**

| Asset | Size | First commit | Provenance |
|---|---|---|---|
| `assets/TELUS_Digital_logo.png` | 24 KB | `9719df2` "Initial commit" | undocumented |
| `assets/AI-Native.png` | 122 KB | `9719df2` "Initial commit" | undocumented |
| `assets/SDD.png` | 201 KB | `9719df2` (later touched by `64b423b`) | undocumented |
| `assets/SDLC-to-AIDLC.png` | 341 KB | `9719df2` "Initial commit" | undocumented |

Three of the four entered in a single squashed initial commit with no descriptive message. There is no
`assets/README.md`, no `CREDITS` file, no per-image licence, and no HTML comment or alt text recording
a source. A repo-wide grep for provenance, attribution, credit, or source markers returns no
image-related hit.

### 3a. `SDLC-to-AIDLC.png` — the one to resolve first

This diagram is displayed at `README.md:83`, immediately below a link to the AWS AI-DLC blog post it
depicts. **If it is a redraw of the diagram in that post rather than original work, it is
third-party copyrighted material sitting in an Apache-2.0 repository with no attribution and no
licence.** A redraw of a diagram is a derivative work; being redrawn does not by itself clear it.

One useful comparison point: `docs/capability-brief.html:806` carries an independently authored inline
SVG of the same mapping. If the SVG was drawn from scratch, the PNG can be replaced with it and the
question disappears. **Legal decision required.**

### 3b. `TELUS_Digital_logo.png` — distributed under a licence that does not cover it

The logo is committed to a repository carrying a blanket Apache-2.0 grant and is hot-linked from 11
public pages via `raw.githubusercontent.com` (`docs/index.html`, `docs/agents.html`,
`docs/capability-brief.html`, and the eight `docs/e-learning/*.html` pages). Apache-2.0 §6 withholds
trademark rights, so the logo is arguably *not* covered by the repository's own grant despite being
distributed under it.

The remediation added `TRADEMARK.md` at the root and inside the extension, naming the logo explicitly
as excluded. **That closes the ambiguity but does not change the underlying position:** the file is
still in a public permissively-licensed tree. Whether that is acceptable is a brand decision.

### 3c. Untracked lab archive

`docs/e-learning/lab-codebase.zip` exists in the working tree but is **not tracked by git** — the
`.gitignore` `*.zip` rule catches it and the `!docs/packages/*.zip` negation does not. Its provenance
and licence are unrecorded. If it is meant to be published, it needs both; if it is not meant to be
published, it should be moved out of `docs/`.

---

## 4. `brds/` and `specs/` — published content review

**Finding: overwhelmingly clean, with one derivation that needs confirming.**

Nine BRDs and sixteen spec directories (108 files) are published publicly. Every one describes
Spectra's own development — several are recursively self-referential, such as a BRD about the
BRD-generating agent.

Systematic greps found **none** of the following anywhere in `brds/` or `specs/`:

- Client or competitor names (no `Acme`/`Contoso`-style placeholders either — there is simply nothing)
- Internal hostnames — no `*.telus`, `*.telusinternational`, `*.telusdigital`, `*.xavient`,
  `*.internal`, `*.corp`, `*.intranet`, `*.local`
- Internal system URLs — every example URL is `example.test` (an RFC 6761 reserved TLD) or loopback
- Email addresses — the only matches repo-wide are `git@github.com` in SSH-clone-URL parsing
  instructions, and two `spectra@X.Y.Z` strings that are `uv`/`pip` version-pin syntax
- Any occurrence of `telusdigital.com`

The only individual named anywhere in the repository is the GitHub handle `@alibahaloo` in
`.github/CODEOWNERS`.

### 4a. The one exception — an internal source document

`brds/flaky-test-detector.md:14` records its input as:

> `Flaky_Test_Detector_Analyzer_BRD.docx` (TELUS Digital QE Practice — reference input, scoped down here)

Corroborated at `specs/018-flaky-test-detector/spec.md:14`, which describes scoping down "the TELUS
Digital QE Practice reference document".

This is the only place where internal, non-public TELUS Digital material demonstrably fed a published
artifact. The 53 KB BRD, the 172 KB `specs/018-flaky-test-detector/` tree, and the shipped 27 KB
`spectra/commands/flaky-test-detector.md` all descend from it. The internal document's **filename is
now public**, which is itself a small disclosure.

**Two questions for the owner:**

1. Was the source document cleared for derivative publication? A scoped-down derivative of an
   internal work is still a derivative of it.
2. If it was, should the derivation be disclosed in `NOTICE`, or is the internal provenance itself
   something that should not be stated publicly?

**Report only — nothing was changed.** Note that if remediation is ever required, the filename is in
committed history at `brds/flaky-test-detector.md` and `specs/018-flaky-test-detector/spec.md`, so
removal would mean rewriting history on a public repository. That is the repository owner's decision,
not one to be taken as part of routine cleanup.

### 4b. Stale MIT assertions — resolved

Eight lines across `specs/001-domain-analyzer/` and `specs/002-open-pr/` asserted "MIT (TELUS
Digital)" about Spectra's own files, surviving from before the 1.3.0 relicense. **These were corrected
to Apache-2.0** rather than left as a contradiction a reviewer would find by grep. Recorded here
because the correction edits completed task records, which is a deliberate departure from treating
`specs/` as immutable history.

---

## 5. Copyright entity name

`LICENSE:189` and `NOTICE` both read **`Copyright 2026 TELUS Digital`**. Two things need a human:

1. **Is "TELUS Digital" the correct registered legal entity for a copyright assertion**, or is it a
   brand name? The registered entity may be "TELUS International (Cda) Inc." or similar. A copyright
   notice naming a brand rather than a legal person is weaker than one naming the entity.
2. **The organisation mismatch.** Copyright is asserted to TELUS Digital, but the canonical repository
   org is `xavient` — the acquired entity — and that org name is load-bearing in every
   `raw.githubusercontent.com` install URL. This is understood internally; it is not obvious to an
   outside reviewer, who sees a TELUS copyright on a repo in a differently-named org.

Also worth confirming: the copyright year `2026` matches the commit dates, but should reflect the year
of first publication.

**No edit was made. Legal decides.**

---

## 6. Third-party code carried in the repository

**Finding: an open MIT obligation, addressed by this change but recorded here because it was not
previously visible.**

23 files under `.specify/extensions/git/` and `.specify/extensions/agent-context/` are committed to
this repository. They are authored by `spec-kit-core`, declare `license: MIT` in their own manifests,
and include eight `.sh`/`.ps1` scripts. `.specify/extensions/.cache/catalog-*.json` — a verbatim copy
of GitHub's community catalog — is also committed.

MIT requires that the copyright notice and permission notice be included in all copies or substantial
portions of the software. **Before this change, that text appeared nowhere in the repository**, and
neither vendored directory carried a `LICENSE`.

**Addressed:** `NOTICE` (root and extension) now reproduces the MIT permission notice verbatim with
`Copyright GitHub, Inc.`, naming the vendored directories it covers.

**Still open for review:** whether these directories should be committed at all. They are Spec Kit's
own files, replaced wholesale when Spec Kit updates, so tracking them means the repository carries and
redistributes third-party code it does not maintain. Removing them from version control and letting
Spec Kit install them would eliminate the obligation rather than satisfy it.

---

## 7. "AI-DLC" as an unmarked term

AI-DLC is credited to AWS in prose wherever the concept is introduced — `README.md:77` links the AWS
blog post directly, and `docs/capability-brief.html:804` repeats the attribution. That part is fine.

What is worth a check: **"AI-DLC" is also used as an unmarked structural term throughout the product's
public surface** — as an `aidlc` field in `agents-list.json`, in the roster JSON schema at
`specs/006-agent-roster-cli/contracts/agents-list.schema.json`, in `spectra agent-list` output, and as
a column header in generated documentation. That is a deeper dependency on someone else's term than
prose attribution covers.

**Addressed in part:** `NOTICE` now disclaims affiliation with AWS and identifies "AI-DLC" as a mark of
its owner. **Open:** whether AWS asserts trademark rights in the term, and whether a first-use
attribution marker belongs in the generated column headers.

---

## 8. Smaller items, recorded for completeness

- **The e-learning pages have no licence footer.** Footers were added to `docs/index.html`,
  `docs/agents.html`, and `docs/capability-brief.html`. The eight `docs/e-learning/*.html` pages were
  left alone as out of scope; they carry the TELUS Digital logo and no copyright or licence line.
- **No `CODE_OF_CONDUCT.md`.** Not a legal requirement, and arguably unnecessary given that PR creation
  is collaborator-only, but its absence is conspicuous on a public repository.
- **Documentation drift, now corrected:** `CONTRIBUTING.md` documented `assets/AIDLC-mapping.png`,
  which does not exist, omitted `AI-Native.png`, and listed three of six commands. `README.md` and
  `docs/capability-brief.html` both described the package as "four command files, one template" when it
  is six and four.
- **Nothing shipped is executable.** The published package is 16 Markdown/text files. No scripts, no
  binaries, no post-install hooks — enforced by `tests/test_document_templates.py:125-135`.
- **No telemetry.** The CLI makes only bodyless `GET` requests to `api.github.com` and
  `raw.githubusercontent.com`.

---

## Summary — what needs a human

| # | Item | Who decides | Section |
|---|---|---|---|
| 1 | Was the internal QE Practice `.docx` cleared for derivative publication? | Repo owner + legal | [4a](#4a-the-one-exception--an-internal-source-document) |
| 2 | Is `SDLC-to-AIDLC.png` original work or an AWS redraw? | Legal | [3a](#3a-sdlc-to-aidlcpng--the-one-to-resolve-first) |
| 3 | Is "TELUS Digital" the correct registered entity for copyright? | Legal | [5](#5-copyright-entity-name) |
| 4 | Rename the four certification-named roadmap agents? | Repo owner | [2a](#2a-titles-that-are-bare-standard-names) |
| 5 | Keep vendoring Spec Kit's extensions under `.specify/`? | Repo owner | [6](#6-third-party-code-carried-in-the-repository) |
| 6 | Trademark registration for "Spectra" | Brand + legal | out of scope |
| 7 | Legal review of each compliance agent before 🚧 → ✅ | Legal | [1](#1-normative-standard-text-in-shipped-agents) |
| 8 | Professional liability posture for client engagements using Spectra | Legal + delivery | out of scope |

Item 8 is worth stating plainly: the Apache-2.0 warranty disclaimer governs the open-source
distribution. It does not govern what TELUS Digital contracts with a client who is using Spectra on
an engagement.
