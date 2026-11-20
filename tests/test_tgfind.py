import json
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import submit_tgfind as tgfind


class MockResponse:
    headers = {}
    def __init__(self, reply):
        self.data = json.dumps(reply).encode()
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return None
    def read(self, limit):
        return self.data[:limit]


class MCPSubmissionTests(unittest.TestCase):
    def test_one_submission_to_allowed_documented_endpoint(self):
        calls = []
        def fake(req, timeout=15):
            payload = json.loads(req.data)
            calls.append((req.full_url, payload))
            if payload["method"] == "initialize":
                return MockResponse({"jsonrpc": "2.0", "id": 1,
                    "result": {"protocolVersion": tgfind.PROTOCOL}})
            if payload["method"] == "tools/list":
                return MockResponse({"jsonrpc": "2.0", "id": 2,
                    "result": {"tools": [{"name": "submit_listing"}]}})
            return MockResponse({"jsonrpc": "2.0", "id": 3, "result": {
                "content": [{"type": "text", "text": "Listed for indexing"}]}})
        self.assertEqual(tgfind.submit(opener=fake), "Listed for indexing")
        self.assertEqual([x[1]["method"] for x in calls],
                         ["initialize", "tools/list", "tools/call"])
        self.assertTrue(all(x[0] == tgfind.ENDPOINT for x in calls))
        self.assertEqual(calls[2][1]["params"], {
            "name": "submit_listing", "arguments": {"handle": "@AIFREEDROP", "type": "channel"}})

    def test_abort_if_submit_tool_is_not_advertised(self):
        def fake(req, timeout=15):
            payload = json.loads(req.data)
            if payload["method"] == "initialize":
                return MockResponse({"jsonrpc": "2.0", "id": 1,
                    "result": {"protocolVersion": tgfind.PROTOCOL}})
            return MockResponse({"jsonrpc": "2.0", "id": 2, "result": {"tools": []}})
        with self.assertRaises(RuntimeError):
            tgfind.submit(opener=fake)

    def test_sse_reply_parsing(self):
        data = b'event: message\ndata: {"jsonrpc":"2.0","id":3,"result":{"content":[]}}\n\n'
        self.assertEqual(tgfind.parse_reply(data)["id"], 3)


if __name__ == "__main__":
    unittest.main()
