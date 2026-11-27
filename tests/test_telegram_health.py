import datetime as dt
import unittest

from unittest.mock import Mock

from telegram_health import FeedPosts, audit, verify_recent_receipts


NOW = dt.datetime(2026, 11, 28, 8, 43, tzinfo=dt.timezone.utc)


def recorded(message_id, day=27):
    return {"message_id": message_id, "time": f"2026-11-{day}T18:00:00Z"}


class TelegramHealthTests(unittest.TestCase):
    def test_only_counts_real_channel_message_elements(self):
        parser = FeedPosts()
        parser.feed("""
            <div class="tgme_widget_message" data-post="AIFREEDROP/17"></div>
            <div class="wrap tgme_widget_message x" data-post="aifreedrop/18"></div>
            <a href="https://t.me/AIFREEDROP/19">Link</a>
            <div class="tgme_widget_message" data-post="other/20"></div>
        """)
        self.assertEqual(parser.ids, {17, 18})

    def test_a_complete_public_daily_run_passes(self):
        state = {"posted": [recorded(mid) for mid in range(1, 6)]}
        self.assertEqual(audit(state, {1, 2, 3, 4, 5}, NOW), [])

    def test_accepted_api_send_is_not_public_confirmation(self):
        state = {"posted": [recorded(mid) for mid in range(1, 6)]}
        errors = audit(state, {1, 2, 3, 4, 6}, NOW)
        self.assertIn("4/5", errors[0])
        self.assertIn("missing recorded messages: 5", errors[1])

    def test_old_public_post_does_not_mask_stalled_publisher(self):
        state = {"posted": [recorded(1, day=26), {"time": "invalid"}, recorded(2, day=29)]}
        self.assertIn("last 26 hours", audit(state, {1, 2}, NOW)[-1])

    def test_verifies_recent_receipt_after_public_feed_propagation(self):
        state = {"posted": [{"message_id": 18, "time": "2026-11-28T08:41:00Z"}]}
        fetch = Mock(side_effect=[{17}, OSError(), {17, 18}])
        pause = Mock()
        self.assertEqual(verify_recent_receipts(state, NOW, fetch=fetch, pause=pause), 0)
        self.assertEqual(fetch.call_count, 3)
        self.assertEqual([call.args[0] for call in pause.call_args_list], [8, 20])

    def test_missing_recent_receipt_fails_without_resending(self):
        state = {"posted": [{"message_id": 18, "time": "2026-11-28T08:41:00Z"}]}
        fetch = Mock(return_value={17})
        self.assertEqual(verify_recent_receipts(state, NOW, fetch=fetch, pause=Mock()), 1)
        self.assertEqual(fetch.call_count, 3)

    def test_no_recent_receipts_skips_the_public_request(self):
        fetch = Mock()
        self.assertEqual(verify_recent_receipts({"posted": [recorded(17)]}, NOW, fetch=fetch), 0)
        fetch.assert_not_called()
