import datetime as dt
import os
import pathlib
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import metrics


class MetricsTests(unittest.TestCase):
    def test_records_today_without_creating_duplicate_daily_points(self):
        now = dt.datetime(2026,11,20,3,0,tzinfo=dt.timezone.utc)
        state = {"counts":[{"date":"2026-11-20","subscribers":2}], "posted":[], "branding":{}}
        saved=[]
        with patch.dict(os.environ,{"TELEGRAM_BOT_TOKEN":"test","TELEGRAM_CHANNEL":"@AIFREEDROP"}):
            n=metrics.capture(now, api=lambda *args: 5, persist=lambda x:saved.append(x.copy()), loader=lambda:state)
        self.assertEqual(n,5)
        self.assertEqual(state["counts"],[{"date":"2026-11-20","subscribers":5}])
        self.assertEqual(state["observations"][-1]["members"],5)
        self.assertEqual(len(saved),1)

    def test_does_not_touch_any_wrong_channel(self):
        with patch.dict(os.environ,{"TELEGRAM_BOT_TOKEN":"test","TELEGRAM_CHANNEL":"@UnrelatedChannel"}):
            with self.assertRaises(RuntimeError):
                metrics.capture(api=lambda *args:3)

    def test_requires_secret(self):
        with patch.dict(os.environ,{"TELEGRAM_BOT_TOKEN":""}):
            with self.assertRaises(RuntimeError):
                metrics.capture()


if __name__ == "__main__":
    unittest.main()
