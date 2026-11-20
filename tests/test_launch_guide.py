import json, os, pathlib, sys, tempfile, unittest
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"scripts"))
import post_ai_car_guide as guide

class LaunchGuideTests(unittest.TestCase):
    def test_live_publication_once_and_message_url(self):
        with tempfile.TemporaryDirectory() as tmp:
            mark=pathlib.Path(tmp)/"guide.json"
            calls=[]
            def fake(_token,method,params):
                calls.append((method,params));return {"message_id":141}
            with patch.dict(os.environ,{"TELEGRAM_BOT_TOKEN":"test","TELEGRAM_CHANNEL":"@AIFREEDROP"}), patch.object(guide,"MARK",mark):
                guide.run(api=fake)
                guide.run(api=fake)
            self.assertEqual(len(calls),1)
            self.assertEqual(calls[0][0],"sendMessage")
            self.assertIn("CAR PHOTO",calls[0][1]["text"])
            self.assertEqual(json.loads(mark.read_text())["url"],"https://t.me/AIFREEDROP/141")
    def test_no_other_channel(self):
        with patch.dict(os.environ,{"TELEGRAM_BOT_TOKEN":"test","TELEGRAM_CHANNEL":"@other_channel"}):
            with self.assertRaises(RuntimeError):guide.run(api=lambda *args:None)
    def test_requires_real_message_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ,{"TELEGRAM_BOT_TOKEN":"test","TELEGRAM_CHANNEL":"@AIFREEDROP"}),patch.object(guide,"MARK",pathlib.Path(tmp)/"new.json"):
                with self.assertRaises(RuntimeError):guide.run(api=lambda *args:{"ok":True})

if __name__=="__main__":unittest.main()
