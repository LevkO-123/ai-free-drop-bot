import json,os,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import live_channel_check_20261120 as check

class LiveChannelCheckTests(unittest.TestCase):
    def test_send_once_only_to_verified_public_channel(self):
        with tempfile.TemporaryDirectory() as folder:
            calls=[]
            def fake(token,method,payload):
                calls.append((method,payload))
                if method=="getChat":return {"id":-10011223344,"type":"channel","username":"AIFREEDROP"}
                if method=="sendMessage":return {"message_id":55,"chat":{"id":-10011223344}}
                if method=="getChatMemberCount":return 2
                self.fail(method)
            mark=Path(folder)/"live.json"
            with patch.object(check,"MARKER",mark),patch.dict(os.environ,{"TELEGRAM_BOT_TOKEN":"test","TELEGRAM_CHANNEL":"@AIFREEDROP"}):
                check.run(api=fake)
                check.run(api=fake)
            self.assertEqual([name for name,_ in calls],["getChat","sendMessage","getChatMemberCount"])
            self.assertEqual(json.loads(mark.read_text())["post_url"],"https://t.me/AIFREEDROP/55")
    def test_refuse_other_channel(self):
        with patch.dict(os.environ,{"TELEGRAM_BOT_TOKEN":"test","TELEGRAM_CHANNEL":"@OTHER"}):
            with self.assertRaises(RuntimeError):
                check.run(api=lambda *args:None)
    def test_wrong_channel_username_prevents_post(self):
        calls=[]
        def fake(token,method,payload):
            calls.append(method)
            return {"type":"channel","id":-10011,"username":"OTHER"}
        with tempfile.TemporaryDirectory() as folder,patch.object(check,"MARKER",Path(folder)/"marker"),patch.dict(os.environ,{"TELEGRAM_BOT_TOKEN":"test","TELEGRAM_CHANNEL":"@AIFREEDROP"}):
            with self.assertRaises(RuntimeError):
                check.run(api=fake)
        self.assertEqual(calls,["getChat"])

if __name__=="__main__":unittest.main()
