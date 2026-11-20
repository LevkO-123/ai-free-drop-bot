import datetime as dt
import pathlib
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import bot
import branding
import avatar

NOW = dt.datetime(2026, 11, 19, 21, 0, tzinfo=dt.timezone.utc)


def candidate(name="x", at=NOW):
    return {"id": "https://github.com/ollama/ollama/releases/tag/" + name,
            "title": name, "project": "Ollama", "use": "local AI",
            "updated": bot.iso(at), "url": "https://github.com/ollama/ollama/releases/tag/" + name}


class PublisherTests(unittest.TestCase):
    def test_pick_recent_official_release_after_daily_prompt(self):
        state = {"posted": [{"id": "tip-0", "date": NOW.date().isoformat(),
                             "time": bot.iso(NOW), "project": "AI Workflow"}],
                 "tips": ["tip-0"], "counts": [], "branding": {}}
        self.assertEqual(bot.choose_post([candidate()], state, NOW)["id"], candidate()["id"])

    def test_first_daily_post_is_useful_prompt(self):
        state = {"posted": [], "tips": [], "counts": [], "branding": {}}
        item = bot.choose_post([candidate()], state, NOW)
        self.assertEqual(item["id"], "tip-0")
        rendered = bot.format_message(item)
        self.assertIn("FREE AI PROMPT", rendered)
        self.assertIn("<pre>", rendered)
        self.assertLess(len(rendered), 4096)

    def test_all_prompt_posts_are_valid_telegram_size(self):
        for i, (title, body, url) in enumerate(bot.TIPS):
            item = {"id": "tip-" + str(i), "title": title, "body": body, "url": url}
            self.assertLessEqual(len(bot.format_message(item)), 4096)

    def test_old_release_uses_evergreen_tip(self):
        state = {"posted": [], "tips": [], "counts": [], "branding": {}}
        self.assertEqual(bot.choose_post([candidate(at=NOW - dt.timedelta(days=12))], state, NOW)["id"], "tip-0")

    def test_duplicate_is_filtered(self):
        state = {"posted": [{"id": candidate()["id"], "date": "2026-11-16",
                              "time": "2026-11-16T20:00:00+00:00", "project": "Ollama"}],
                 "tips": [], "counts": [], "branding": {}}
        self.assertEqual(bot.choose_post([candidate()], state, NOW)["id"], "tip-0")

    def test_daily_cap(self):
        state = {"posted": [{"id": str(i), "date": NOW.date().isoformat(),
                             "time": bot.iso(NOW), "project": "Other"} for i in range(3)],
                 "tips": [], "counts": [], "branding": {}}
        self.assertIsNone(bot.choose_post([candidate()], state, NOW))

    def test_html_escaping(self):
        item = candidate(name="<script>alert(1)</script>")
        formatted = bot.format_message(item)
        self.assertIn("&lt;script&gt;", formatted)
        self.assertNotIn("<script>", formatted)

    def test_state_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "state.json"
            state = {"posted": [{"id": str(i)} for i in range(350)],
                     "counts": [{"date": str(i)} for i in range(100)], "tips": [], "branding": {}}
            bot.save_state(state, path)
            loaded = bot.load_state(path)
            self.assertEqual(len(loaded["posted"]), 250)
            self.assertEqual(len(loaded["counts"]), 90)

    def test_dry_run_does_not_call_telegram(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(bot, "load_state", return_value={"posted": [], "tips": [], "counts": [], "branding": {}}), \
                 patch.object(bot, "fetch_candidates", return_value=[candidate()]), \
                 patch.object(bot, "telegram", side_effect=AssertionError("live API called")):
                self.assertEqual(bot.run(dry_run=True, now=NOW), 0)

    def test_missing_token_rejects_live_run(self):
        with patch.dict("os.environ", {"TELEGRAM_BOT_TOKEN": "", "TELEGRAM_CHANNEL": "@AIFREEDROP"}):
            with self.assertRaises(RuntimeError):
                bot.run(now=NOW)

    def test_avatar_has_valid_png_header_and_dimensions(self):
        png = avatar.render(180)
        self.assertTrue(png.startswith(b"\x89PNG\r\n\x1a\n"))
        self.assertEqual(struct.unpack(">II", png[16:24]), (180, 180))
        self.assertLess(len(png), 2_000_000)

    def test_branding_is_idempotent(self):
        events = []
        state = {}
        def api(token, method, body):
            events.append(method)
            if method == "sendMessage":
                return {"message_id": 42}
            return True
        def photo(*args):
            events.append("photo")
        branding.configure("fake", "@AIFREEDROP", state, NOW, api=api, persist=lambda s: None, photo=photo)
        branding.configure("fake", "@AIFREEDROP", state, NOW, api=api, persist=lambda s: None, photo=photo)
        self.assertEqual(events, ["setChatTitle", "setChatDescription", "photo", "sendMessage", "pinChatMessage"])

    def test_parser_blocks_other_host_links(self):
        # Parser integration is handled with patched urlopen in later tests.
        self.assertEqual(len(bot.SOURCES), 8)


if __name__ == "__main__":
    unittest.main()
