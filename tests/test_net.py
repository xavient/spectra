"""Bounded fetches and the failure taxonomy behind them (FR-041, FR-041a)."""

from __future__ import annotations

import os
import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import helpers as h  # noqa: E402
from spectra_cli import net  # noqa: E402


class RawBase(unittest.TestCase):
    def test_defaults_to_the_published_location(self):
        with h.raw_base(""):
            os.environ.pop("SPECTRA_RAW_BASE", None)
            self.assertEqual(net.raw_base(), net.DEFAULT_RAW_BASE)

    def test_env_var_overrides_and_trailing_slash_is_ignored(self):
        with h.raw_base("http://example.test/base/"):
            self.assertEqual(net.raw_base(), "http://example.test/base")
            self.assertEqual(net.url_for("agents-list.json"),
                             "http://example.test/base/agents-list.json")

    def test_leading_slash_on_path_does_not_double_up(self):
        with h.raw_base("http://example.test"):
            self.assertEqual(net.url_for("/spectra/extension.yml"),
                             "http://example.test/spectra/extension.yml")


class Success(unittest.TestCase):
    def test_fetch_text_returns_the_body(self):
        with h.serve({"note.txt": "hello"}) as base, h.raw_base(base):
            self.assertEqual(net.fetch_text("note.txt"), "hello")

    def test_fetch_json_returns_a_dict(self):
        with h.serve({"a.json": '{"k": 1}'}) as base, h.raw_base(base):
            self.assertEqual(net.fetch_json("a.json"), {"k": 1})


class Failures(unittest.TestCase):
    """Each mode gets its own sentence, because they send a user to different places."""

    def test_unreachable_host_says_so(self):
        with h.raw_base(h.UNREACHABLE_BASE):
            with self.assertRaises(net.FetchError) as caught:
                net.fetch_text("agents-list.json")
        self.assertIn("could not be reached", str(caught.exception))

    def test_unreachable_host_fails_fast_rather_than_waiting_out_the_timeout(self):
        started = time.time()
        with h.raw_base(h.UNREACHABLE_BASE):
            with self.assertRaises(net.FetchError):
                net.fetch_text("agents-list.json")
        self.assertLess(time.time() - started, net.TIMEOUT,
                        "a refused connection must not burn the full timeout")

    def test_missing_file_reports_the_http_status(self):
        with h.serve({"present.txt": "x"}) as base, h.raw_base(base):
            with self.assertRaises(net.FetchError) as caught:
                net.fetch_text("absent.txt")
        self.assertIn("HTTP 404", str(caught.exception))

    def test_malformed_json_is_a_fetch_failure_not_a_crash(self):
        with h.serve({"a.json": "{not json"}) as base, h.raw_base(base):
            with self.assertRaises(net.FetchError) as caught:
                net.fetch_json("a.json")
        self.assertIn("not valid JSON", str(caught.exception))

    def test_json_that_is_not_an_object_is_rejected(self):
        with h.serve({"a.json": "[1, 2, 3]"}) as base, h.raw_base(base):
            with self.assertRaises(net.FetchError) as caught:
                net.fetch_json("a.json")
        self.assertIn("did not contain a JSON object", str(caught.exception))

    def test_every_failure_message_names_the_url(self):
        """A user who cannot reach the data needs to know which URL to check in their proxy."""
        with h.raw_base(h.UNREACHABLE_BASE):
            with self.assertRaises(net.FetchError) as caught:
                net.fetch_text("agents-list.json")
        self.assertIn("agents-list.json", str(caught.exception))


class Bounds(unittest.TestCase):
    def test_the_default_timeout_is_ten_seconds(self):
        """SC-013: no command may stay silent for longer than this before explaining itself."""
        self.assertEqual(net.TIMEOUT, 10)


if __name__ == "__main__":
    unittest.main()
