# Security Policy

## Reporting a vulnerability

**Please do not report security issues in a public issue.** Issues on this repository are open and
publicly readable, so a report filed there discloses the vulnerability to everyone before it can be
fixed.

Report privately using **GitHub private vulnerability reporting**: go to the repository's Security
tab and use the **Report a vulnerability** button. This is available to any GitHub user and the
report is visible only to maintainers.

Please include the affected component (the `spectra` extension or the `spectra` CLI), the version,
reproduction steps, and the impact you observed.

We aim to acknowledge reports within five business days.

For anything that is not a security issue, a normal
[issue](https://github.com/xavient/spectra/issues) is the right channel.

## Scope

In scope:

- The `spectra` CLI (`spectra_cli/`), including the install flow and anything it executes
- Shipped agent commands under `spectra/commands/`, including prompt injection, unintended
  destructive file operations, and exfiltration of project contents
- The catalog and package distribution path (`catalog.json`, `docs/packages/spectra.zip`)

Out of scope:

- Vulnerabilities in [Spec Kit](https://github.com/github/spec-kit) itself — report those upstream
- Vulnerabilities in the AI coding agents Spectra runs against (Claude Code, Copilot, Cursor, and
  others) — report those to their vendors
- Output quality issues: an agent producing a wrong or incomplete answer is a bug, not a
  vulnerability. Spectra agents produce drafts for human review

## Supported versions

The extension and the CLI version independently. Security fixes land on the latest version of each.
There are no long-term support branches.
