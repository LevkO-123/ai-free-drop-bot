import os
import unittest
from unittest.mock import patch

import refresh_channel


def initial_state():
    return {"branding": {"version": 3, "welcome_id": 3, "description_v2": True}}


class RefreshGrowthWelcomeTests(unittest.TestCase):
    def test_edit_existing_welcome_only_once(self):
        state = initial_state()
        actions = []
        saved = []
        def api(token, method, payload):
            actions.append((method, payload))
            if method == "getChat":
                return {"type": "channel", "username": "AIFREEDROP"}
            return True
        with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "test", "TELEGRAM_CHANNEL": "@AIFREEDROP"}):
            for _ in range(2):
                refresh_channel.refresh(api=api, loader=lambda: state,
                                        persist=lambda s: saved.append(s["branding"]["version"]))
        self.assertEqual([x[0] for x in actions],
                         ["getChat", "setChatDescription", "editMessageText"])
        self.assertEqual(actions[-1][1]["message_id"], 3)
        self.assertEqual(state["branding"]["version"], 4)
        self.assertEqual(len(saved), 2)
        self.assertTrue(all(x[0] != "sendMessage" for x in actions))

    def test_wrong_channel_is_blocked(self):
        with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "test", "TELEGRAM_CHANNEL": "@OTHER"}):
            with self.assertRaisesRegex(RuntimeError, "other channel"):
                refresh_channel.refresh(loader=initial_state)

    def test_unverified_chat_is_blocked(self):
        state = initial_state()
        with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "test", "TELEGRAM_CHANNEL": "@AIFREEDROP"}):
            with self.assertRaisesRegex(RuntimeError, "not verified"):
                refresh_channel.refresh(api=lambda t, m, p: {"type": "supergroup", "username": "AIFREEDROP"},
                                        loader=lambda: state, persist=lambda s: None)
        self.assertEqual(state["branding"]["version"], 3)

    def test_retry_after_edit_failure_skips_duplicate_description(self):
        state = initial_state()
        seen = []
        fail = [True]
        def api(token, method, payload):
            seen.append(method)
            if method == "getChat":
                return {"type": "channel", "username": "AIFREEDROP"}
            if method == "editMessageText" and fail[0]:
                fail[0] = False
                raise RuntimeError("temporary failure")
            return True
        with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "test", "TELEGRAM_CHANNEL": "@AIFREEDROP"}):
            with self.assertRaises(RuntimeError):
                refresh_channel.refresh(api=api, loader=lambda: state, persist=lambda s: None)
            self.assertEqual(state["branding"]["version"], 3)
            refresh_channel.refresh(api=api, loader=lambda: state, persist=lambda s: None)
        self.assertEqual(seen.count("setChatDescription"), 1)
        self.assertEqual(seen.count("editMessageText"), 2)
        self.assertEqual(state["branding"]["version"], 4)


if __name__ == "__main__":
    unittest.main()
