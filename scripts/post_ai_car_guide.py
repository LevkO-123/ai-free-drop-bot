"""One-time authentic AI FREE DROP tutorial publication.

Telegram Bot API only, no invented AI rendering, no spam, no other channels.
Uses a small repository state marker for idempotency.
"""
from __future__ import annotations
import datetime as dt
import json, os
from pathlib import Path
from bot import telegram

MARK=Path("data/launch_guide.json")
CHANNEL="@AIFREEDROP"
URL="https://github.com/LevkO-123/ai-free-drop-bot/blob/main/CAR_IMAGE_TO_AI_VIDEO.md"
MESSAGE=(
    "🎬 <b>TURN ONE CAR PHOTO INTO A CINEMATIC AI VIDEO</b>\n\n"
    "Want to animate a real car photo instead of making another generic slideshow?\n\n"
    "We prepared a <b>free, step-by-step image-to-video workflow</b> with "
    "official LTX-2.5 / ComfyUI resources and two original automotive prompts.\n\n"
    "What you'll learn:\n"
    "• How to keep a consistent car and background\n"
    "• Camera-motion prompts for a premium reveal\n"
    "• Why model/compute costs and license checks still matter\n"
    "• How to show an honest before/after\n\n"
    "📖 <a href='"+URL+"'>Open the free workflow and prompts</a>\n\n"
    "🔖 Save this tutorial and share it with a car-video creator.\n"
    "#AIvideo #ComfyUI #CarTok #FreeAI"
)

def run(api=telegram):
    token=os.environ.get("TELEGRAM_BOT_TOKEN","").strip()
    target=os.environ.get("TELEGRAM_CHANNEL","") or CHANNEL
    if target!=CHANNEL:raise RuntimeError("Wrong channel; refusing post")
    if not token:raise RuntimeError("Missing Telegram token secret")
    if MARK.exists():
        print("Launch guide previously posted; no duplicate.")
        return
    result=api(token,"sendMessage",{"chat_id":CHANNEL,"text":MESSAGE,
              "parse_mode":"HTML","disable_web_page_preview":False})
    if not isinstance(result,dict) or not isinstance(result.get("message_id"),int):
        raise RuntimeError("Telegram did not return a verified message ID")
    MARK.parent.mkdir(parents=True,exist_ok=True)
    MARK.write_text(json.dumps({"channel":CHANNEL,
        "message_id":result["message_id"],
        "url":f"https://t.me/AIFREEDROP/{result['message_id']}",
        "posted_at":dt.datetime.now(dt.timezone.utc).isoformat()},indent=2)+"\n")
    print("Launch tutorial sent to Telegram, message:",result["message_id"])

if __name__=="__main__":run()
