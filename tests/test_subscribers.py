import contextlib
import io
import datetime as dt
import os
import pathlib
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import bot

NOW = dt.datetime(2026, 11, 19, 18, 30, tzinfo=dt.timezone.utc)


class SubscriberCountTests(unittest.TestCase):
    def test_first_live_run_records_subscribers_without_waiting_for_20utc(self):
        state = {"posted": [], "tips": [], "counts": [], "branding": {}}
        with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "dummy", "TELEGRAM_CHANNEL": "@AIFREEDROP"}), \
             patch.object(bot, "load_state", return_value=state), \
             patch.object(bot, "save_state"), \
             patch.object(bot, "configure_channel"), \
             patch.object(bot, "fetch_candidates", return_value=[]), \
             patch.object(bot, "choose_post", return_value=None), \
             patch.object(bot, "telegram", return_value=7) as tg:
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(bot.run(now=NOW), 0)
            self.assertEqual(state["counts"], [{"date": "2026-11-19", "subscribers": 7}])
            tg.assert_called_once_with("dummy", "getChatMemberCount", {"chat_id": "@AIFREEDROP"})
            # Multiple runs on the same day must not inflate history.
            with contextlib.redirect_stdout(io.StringIO()):
                bot.run(now=NOW + dt.timedelta(hours=1))
            self.assertEqual(len(state["counts"]), 1)
            tg.assert_called_once()

    def test_dry_run_does_not_query_or_save_subscriber_counts(self):
        state = {"posted": [], "tips": [], "counts": [], "branding": {}}
        with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "", "TELEGRAM_CHANNEL": "@AIFREEDROP"}), \
             patch.object(bot, "load_state", return_value=state), \
             patch.object(bot, "save_state") as persist, \
             patch.object(bot, "fetch_candidates", return_value=[]), \
             patch.object(bot, "choose_post", return_value=None), \
             patch.object(bot, "telegram") as tg:
            self.assertEqual(bot.run(dry_run=True, now=NOW), 0)
            self.assertEqual(state["counts"], [])
            persist.assert_not_called()
            tg.assert_not_called()


if __name__ == "__main__":
    unittest.main()
