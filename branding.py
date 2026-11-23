"""Apply channel profile, upload avatar and pin welcome once; idempotent."""
from __future__ import annotations

import json
import sys
import urllib.request
import uuid

from avatar import render

TITLE = "AI FREE DROP | Tools & Workflows"
DESCRIPTION = "Free AI checklists for buying used cars, copy-paste prompts, practical AI workflows and source-linked tools. Start with the free car buyer kit. No fake giveaways or income promises."
WELCOME = (
    "🎁 <b>START HERE — FREE USED-CAR AI KIT</b>\n"
    "\n"
    "🚗 Buying a used car? Get inspection questions, compare cars, challenge seller claims and understand repair quotes.\n"
    "\n"
    "👉 <a href=\"https://github.com/LevkO-123/ai-free-drop-bot/blob/main/CAR_BUYER_AI_KIT.md\">OPEN THE FREE KIT — no signup</a>\n"
    "\n"
    "🧠 Want more? <a href=\"https://github.com/LevkO-123/ai-free-drop-bot/blob/main/FREE_PROMPTS.md\">25 free copy-ready AI prompts</a> plus official AI tool updates.\n"
    "\n"
    "Try one prompt. Save the result. Share this channel with someone shopping for a car.\n"
    "\n"
    "AI cannot physically inspect a vehicle. Always verify important claims. No fake freebies or guaranteed income.\n"
    "\n"
    "#CarBuying #FreeAI #AIPrompts"
)


def upload_avatar(token, channel, *, image=None):
    image = image if image is not None else render()
    if len(image) > 2_000_000 or not image.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("Avatar must be a small PNG")
    boundary = "----aifreedrop-" + uuid.uuid4().hex
    payload = b"".join([
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"chat_id\"\r\n\r\n{channel}\r\n".encode(),
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"photo\"; filename=\"avatar.png\"\r\nContent-Type: image/png\r\n\r\n".encode(),
        image, f"\r\n--{boundary}--\r\n".encode(),
    ])
    req = urllib.request.Request(
        "https://api.telegram.org/bot" + token + "/setChatPhoto",
        data=payload, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            ok = json.loads(response.read(4096)).get("ok", False)
    except Exception:
        raise RuntimeError("Channel avatar upload failed; check admin permissions") from None
    if not ok:
        raise RuntimeError("Telegram refused channel avatar; check Change Channel Info right")


def configure(token, channel, state, now, *, api, persist, photo=upload_avatar):
    status = state.setdefault("branding", {})
    today = now.date().isoformat()
    if not status.get("profile_done") and status.get("last_profile_attempt") != today:
        status["last_profile_attempt"] = today
        persist(state)
        try:
            api(token, "setChatTitle", {"chat_id": channel, "title": TITLE})
            api(token, "setChatDescription", {"chat_id": channel, "description": DESCRIPTION})
            photo(token, channel)
            status["profile_done"] = True
            persist(state)
            print("Channel profile and avatar configured.")
        except Exception:
            print("Profile configuration unavailable: check Change Channel Info permission.", file=sys.stderr)

    if not status.get("welcome_done"):
        try:
            message = api(token, "sendMessage", {"chat_id": channel, "text": WELCOME, "parse_mode": "HTML"})
            status["welcome_id"] = message.get("message_id") if isinstance(message, dict) else None
            status["welcome_done"] = True
            persist(state)
            print("Welcome message published.")
        except Exception:
            print("Welcome not posted: check Post Messages permission.", file=sys.stderr)

    if status.get("welcome_id") and not status.get("pinned") and status.get("last_pin_attempt") != today:
        status["last_pin_attempt"] = today
        persist(state)
        try:
            api(token, "pinChatMessage", {
                "chat_id": channel, "message_id": status["welcome_id"],
                "disable_notification": True})
            status["pinned"] = True
            persist(state)
            print("Welcome pinned.")
        except Exception:
            print("Pin unavailable: check Edit Messages right.", file=sys.stderr)
