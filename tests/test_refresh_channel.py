import os
import pathlib
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import refresh_channel


def recording_api(requests):
    def api(_token, method, payload):
        requests.append((method, payload))
        if method == "getChat":
            return {"type": "channel", "username": "AIFREEDROP"}
        return True
    return api


class RefreshTests(unittest.TestCase):
    def test_only_revises_existing_welcome_message(self):
        state={"branding":{"welcome_id":3, "profile_done":True, "pinned":True}}
        requests=[]
        with patch.dict(os.environ,{"TELEGRAM_BOT_TOKEN":"test-token",
                                     "TELEGRAM_CHANNEL":"@AIFREEDROP"}):
            refresh_channel.refresh(api=recording_api(requests),
                                    loader=lambda:state, persist=lambda s:None)
        self.assertEqual([x[0] for x in requests],["getChat","setChatDescription","editMessageText"])
        self.assertEqual(requests[2][1]["message_id"],3)
        self.assertEqual(state["branding"]["version"],4)

    def test_existing_description_is_not_sent_again(self):
        state = {"branding": {"welcome_id": 3, "description_v4": True,
                              "profile_done": True, "version": 3}}
        requests = []
        with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "test-token",
                                     "TELEGRAM_CHANNEL": "@AIFREEDROP"}):
            refresh_channel.refresh(api=recording_api(requests),
                                    loader=lambda: state, persist=lambda s: None)
        self.assertEqual([method for method, _ in requests], ["getChat", "editMessageText"])
        self.assertEqual(state["branding"]["version"], 4)

    def test_no_duplicate_welcome_when_message_id_unknown(self):
        with patch.dict(os.environ,{"TELEGRAM_BOT_TOKEN":"test-token",
                                     "TELEGRAM_CHANNEL":"@AIFREEDROP"}):
            with self.assertRaises(RuntimeError):
                refresh_channel.refresh(api=lambda *args:None,loader=lambda:{"branding":{}},
                                        persist=lambda s:None)

    def test_rejects_other_channel(self):
        with patch.dict(os.environ,{"TELEGRAM_BOT_TOKEN":"test-token",
                                     "TELEGRAM_CHANNEL":"@RandomChannel"}):
            with self.assertRaises(RuntimeError):
                refresh_channel.refresh(api=lambda *args:None)

    def test_description_stays_within_telegram_limit(self):
        import branding
        self.assertLessEqual(len(branding.DESCRIPTION),255)


if __name__ == "__main__":
    unittest.main()
