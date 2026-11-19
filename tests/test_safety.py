"""Integration-style regression tests using only deterministic mock responses."""
import datetime as dt
import pathlib
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import bot

ATOM = b'''<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry><title>Release 1.0</title><updated>2026-11-19T21:00:00Z</updated>
    <link rel="alternate" href="https://github.com/ollama/ollama/releases/tag/v1.0"/></entry>
  <entry><title>Unexpected domain</title><updated>2026-11-19T21:00:00Z</updated>
    <link rel="alternate" href="https://evil.example/claim"/></entry>
  <entry><title>Version 1.2 rc1</title><updated>2026-11-19T21:00:00Z</updated>
    <link rel="alternate" href="https://github.com/ollama/ollama/releases/tag/v1.2-rc1"/></entry>
</feed>'''


class FakeResponse:
    def __init__(self, body=ATOM, url="https://github.com/ollama/ollama/releases.atom"):
        self.body = body
        self.url = url
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return None
    def geturl(self):
        return self.url
    def read(self, n=9999999):
        return self.body[:n]


class SafetyTests(unittest.TestCase):
    @patch.object(bot.urllib.request, "urlopen")
    def test_only_official_stable_release(self, fetch):
        fetch.return_value = FakeResponse()
        items = bot.read_feed("ollama/ollama", "Ollama", "local AI")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["title"], "Release 1.0")
        self.assertTrue(items[0]["url"].startswith("https://github.com/ollama/ollama/releases/tag/"))

    @patch.object(bot.urllib.request, "urlopen")
    def test_refuses_feed_redirect_to_untrusted_host(self, fetch):
        fetch.return_value = FakeResponse(url="https://attacker.example/feed")
        with self.assertRaises(ValueError):
            bot.read_feed("ollama/ollama", "Ollama", "local AI")

    @patch.object(bot.urllib.request, "urlopen")
    def test_rejects_oversized_source(self, fetch):
        fetch.return_value = FakeResponse(body=b"x" * 1_000_001)
        with self.assertRaises(ValueError):
            bot.read_feed("ollama/ollama", "Ollama", "local AI")

    @patch.object(bot, "request_json", side_effect=OSError("network token LEAKED_TEST_TOKEN"))
    def test_errors_never_display_api_token(self, fetch):
        with self.assertRaises(RuntimeError) as ctx:
            bot.telegram("LEAKED_TEST_TOKEN", "sendMessage", {"chat_id": "@AIFREEDROP", "text": "hi"})
        self.assertNotIn("LEAKED_TEST_TOKEN", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
