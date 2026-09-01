# Copyright 2026 TELUS Digital
# SPDX-License-Identifier: Apache-2.0

"""Bounded, anonymous reads of Spectra's published data.

Two artifacts are published from `main` over raw links and read at run time: the agent roster
(`agents-list.json`) and the extension manifest (`spectra/extension.yml`). Reading them at run time
rather than baking them in is what keeps the two release channels independent — a new agent reaches
every installed CLI with no CLI release at all (constitution Principle VI).

Every fetch here is:

* **anonymous** — the repository is public, so there is no token, no `gh`, and no login;
* **bounded** — 10 seconds, because the realistic failure in a locked-down corporate network is a
  socket that hangs rather than one that refuses, and an unbounded wait turns a clear error message
  into an apparently frozen terminal;
* **explicit on failure** — :class:`FetchError` carries a reason written for a user, because a command
  that cannot reach the published data must say so rather than present a stale or empty result as
  authoritative.
"""

from __future__ import annotations

import json
import os
import socket
import urllib.error
import urllib.request

DEFAULT_RAW_BASE = "https://raw.githubusercontent.com/xavient/spectra/main"

# Ten seconds: long enough for a slow proxy handshake, short enough that a user waits for the answer
# instead of reaching for Ctrl-C.
TIMEOUT = 10

UA = {"User-Agent": "spectra-cli"}


class FetchError(Exception):
    """Published data could not be retrieved. The message is safe to show a user verbatim."""


def raw_base() -> str:
    """The base URL published data is read from.

    `SPECTRA_RAW_BASE` overrides it. That exists as a test seam — it lets the fetch failure,
    timeout, and schema-version paths be exercised against a local server without publishing
    anything — and mirrors the existing `SPECTRA_UPDATE_REPO` seam in :mod:`spectra_cli.version`. It
    is intentionally absent from `--help`.
    """
    return os.environ.get("SPECTRA_RAW_BASE", "").strip().rstrip("/") or DEFAULT_RAW_BASE


def url_for(path: str) -> str:
    """The full URL for a repository-relative path, e.g. `agents-list.json`."""
    return f"{raw_base()}/{path.lstrip('/')}"


def fetch_text(path: str, timeout: int = TIMEOUT) -> str:
    """Return the decoded body of a published file, or raise :class:`FetchError`.

    Each failure mode gets its own sentence. "Could not be reached" and "did not respond within 10
    seconds" send a user to different places — a proxy setting versus a retry — so collapsing them
    into one message would cost them the diagnosis.
    """
    url = url_for(path)
    request = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:  # must precede URLError; HTTPError subclasses it
        # HTTPError is itself a response object holding an open socket. Closing it here keeps a
        # failed fetch from leaking a file descriptor — which shows up as a ResourceWarning in any
        # process that makes several failed requests, such as the test suite.
        exc.close()
        raise FetchError(f"{url} returned HTTP {exc.code} ({exc.reason}).") from exc
    except urllib.error.URLError as exc:
        if isinstance(exc.reason, (socket.timeout, TimeoutError)):
            raise FetchError(f"{url} did not respond within {timeout} seconds.") from exc
        raise FetchError(f"{url} could not be reached ({exc.reason}).") from exc
    except (socket.timeout, TimeoutError) as exc:  # read timeout, raised bare on some versions
        raise FetchError(f"{url} did not respond within {timeout} seconds.") from exc
    except OSError as exc:  # DNS failure, refused connection, TLS problem
        raise FetchError(f"{url} could not be reached ({exc}).") from exc
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise FetchError(f"{url} was not valid UTF-8 text.") from exc


def fetch_json(path: str, timeout: int = TIMEOUT) -> dict:
    """Return a published JSON document as a dict, or raise :class:`FetchError`.

    A body that arrives but does not parse is a failure of the same kind as one that never arrives:
    the caller has nothing trustworthy to show. Reporting it as a fetch failure keeps every caller's
    error handling to one branch.
    """
    text = fetch_text(path, timeout=timeout)
    try:
        data = json.loads(text)
    except ValueError as exc:
        raise FetchError(f"{url_for(path)} was not valid JSON ({exc}).") from exc
    if not isinstance(data, dict):
        raise FetchError(f"{url_for(path)} did not contain a JSON object.")
    return data
