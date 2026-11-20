"""Regression tests for public release discovery files."""
import json
import pathlib
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import discovery


class GrowthTests(unittest.TestCase):
    def setUp(self):
        self.release = {
            "id": "https://github.com/ggml-org/llama.cpp/releases/tag/b12556",
            "project": "llama.cpp",
            "date": "2026-11-20",
            "time": "2026-11-20T00:04:49+00:00",
        }

    def test_archive_only_contains_official_release_links(self):
        s = {"posted": [self.release, {"id": "https://evil.example/offer", "project": "Fake"}]}
        md, xml = discovery.render(s)
        self.assertIn(self.release["id"], md)
        self.assertNotIn("evil.example", md)
        self.assertIn("https://t.me/AIFREEDROP", md)
        self.assertEqual(len(ET.fromstring(xml).findall("{http://www.w3.org/2005/Atom}entry")), 1)

    def test_rejects_github_url_with_host_or_path_trick(self):
        for url in (
            "https://github.com.evil.example/ggml-org/llama.cpp/releases/tag/v1",
            "https://github.com/ggml-org/llama.cpp/pulls/100",
            "https://github.com/ggml-org/llama.cpp/releases/tag/v1?q=private",
            "http://github.com/ggml-org/llama.cpp/releases/tag/v1",
        ):
            self.assertIsNone(discovery.official_release({"id": url}))

    def test_latest_first_and_idempotent(self):
        a = self.release
        b = {"id": "https://github.com/Comfy-Org/ComfyUI/releases/tag/v0.46.1",
             "project": "ComfyUI", "date": "2026-11-20", "time": "2026-11-20T00:12:01+00:00"}
        md, feed = discovery.render({"posted": [a, b, b]})
        self.assertLess(md.index("ComfyUI"), md.index("llama.cpp"))
        self.assertEqual(feed.count("<entry>"), 2)
        self.assertEqual((md, feed), discovery.render({"posted": [a, b, b]}))

    def test_build_outputs_index_and_valid_feed(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = pathlib.Path(tmp)
            state = base / "state.json"
            state.write_text(json.dumps({"posted": [self.release]}), encoding="utf-8")
            discovery.build(state, base / "DROPS.md", base / "feed.xml")
            self.assertTrue((base / "DROPS.md").is_file())
            ET.parse(base / "feed.xml")


if __name__ == "__main__":
    unittest.main()
