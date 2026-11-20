"""Unit tests: a directory request must be explicit, free and one-channel-only."""
import io
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import submit_directory as sd


class FakeResponse:
    def __init__(self, payload):
        self.body = payload
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self, limit):
        assert limit <= 100_001
        return self.body


class DirectoryTests(unittest.TestCase):
    def test_one_official_channel_with_documented_endpoint(self):
        import json
        seen = []
        def fetch(req, timeout):
            seen.append(req)
            self.assertEqual(timeout, 15)
            return FakeResponse(json.dumps({"ok": True, "results": [
                {"handle": "aifreedrop", "status": "submitted", "statusToken": "KEEP_PRIVATE"}]}).encode())
        self.assertEqual(sd.submit(fetch), "submitted")
        self.assertEqual(len(seen), 1)
        self.assertEqual(seen[0].full_url, "https://telegramchannels.io/api/channels/submit")
        self.assertEqual(seen[0].get_method(), "POST")
        self.assertEqual(json.loads(seen[0].data), {"channel": "@AIFREEDROP"})

    def test_duplicate_is_not_retried(self):
        self.assertEqual(sd.submit(lambda req, timeout: FakeResponse(
            b'{"ok":true,"results":[{"handle":"aifreedrop","status":"duplicate"}]}'
        )), "duplicate")

    def test_unconfirmed_response_fails(self):
        with self.assertRaises(RuntimeError):
            sd.submit(lambda req, timeout: FakeResponse(b'{"ok":true,"results":[]}'))


if __name__ == "__main__":
    unittest.main()
