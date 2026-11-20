"""One-time public AI FREE DROP live post and chat verification.

Intentionally separate from the normal 3-posts/day news feed, because
the operator requested a real live visibility test. Send only to the
verified @AIFREEDROP public channel; never repost on a retry.
"""
from __future__ import annotations
import datetime as dt
import json
import os
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from bot import telegram

CHANNEL="@AIFREEDROP"
MARKER=Path("data/live_channel_check_20261120.json")
MESSAGE=(
    "🚗 <b>FREE AI PROMPT: USED-CAR BUYER'S CHECKLIST</b>\n\n"
    "Before viewing a used car, copy this into your favorite AI assistant:\n\n"
    "<pre>Build a pre-purchase inspection checklist for a "
    "[YEAR] [MAKE] [MODEL] with [MILEAGE] miles in [LOCATION]. "
    "Include seller questions, documents to verify, safety recalls "
    "to check, warning signs on a test drive, and what a qualified "
    "mechanic should inspect. Separate verified facts from assumptions. "
    "Don't invent model-specific defects or current prices.</pre>\n\n"
    "⚠️ AI does not replace a physical inspection, diagnosis, or recall lookup.\n\n"
    "🎁 More free copy-ready prompts: "
    "<a href='https://github.com/LevkO-123/ai-free-drop-bot/blob/main/FREE_PROMPTS.md'>"
    "Open the free prompt pack</a>\n"
    "📌 Save this and send it to someone shopping for a car.\n"
    "#UsedCars #FreeAI #CarBuying"
)
def run(api=telegram):
    token=os.environ.get("TELEGRAM_BOT_TOKEN","").strip()
    channel=os.environ.get("TELEGRAM_CHANNEL",CHANNEL).strip() or CHANNEL
    if not token or channel!=CHANNEL:
        raise RuntimeError("Missing bot secret or unexpected channel")
    if MARKER.exists():
        print("Already published; will not send again")
        return
    chat=api(token,"getChat",{"chat_id":CHANNEL})
    if not isinstance(chat,dict) or chat.get("type")!="channel" or (chat.get("username") or "").lower()!="aifreedrop":
        raise RuntimeError("Expected public @AIFREEDROP channel not verified")
    result=api(token,"sendMessage",{
        "chat_id":chat["id"],"text":MESSAGE,"parse_mode":"HTML",
        "disable_web_page_preview":True
    })
    if not isinstance(result,dict) or not isinstance(result.get("message_id"),int):
        raise RuntimeError("Telegram did not confirm the message ID")
    post_id=result["message_id"]
    if not isinstance(result.get("chat"),dict) or result["chat"].get("id")!=chat["id"]:
        raise RuntimeError("Telegram response chat ID mismatch; do not retry")
    subscribers=None
    try:
        count=api(token,"getChatMemberCount",{"chat_id":chat["id"]})
        if isinstance(count,int):subscribers=count
    except Exception:
        pass
    row={"channel":CHANNEL,"chat_id":chat["id"],"message_id":post_id,
         "post_url":f"https://t.me/AIFREEDROP/{post_id}",
         "subscribers":subscribers,
         "published_at":dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}
    MARKER.parent.mkdir(parents=True,exist_ok=True)
    MARKER.write_text(json.dumps(row,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("VERIFIED LIVE:",row["post_url"],"members:",subscribers)

if __name__=="__main__":run()
