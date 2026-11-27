"""Safely refresh the existing pinned @AIFREEDROP welcome to campaign v4.

No new posts, no external project edits. Retries are idempotent.
"""
from __future__ import annotations

import os
from bot import telegram, load_state, save_state
from branding import DESCRIPTION, WELCOME

PROFILE_TITLE = "VAULTIX"
PROFILE_DESCRIPTION = (
    "Luxury cars, smart used-car buying and practical automotive tech. "
    "Free buyer kit: https://t.me/AIFREEDROP/3\n"
    "YouTube: https://www.youtube.com/channel/UCvbGy3iGHLNcJAnmZeya6XQ\n"
    "TikTok: https://www.tiktok.com/@vaultixstyle"
)

CHANNEL = "@AIFREEDROP"
VERSION = 4


def refresh(api=telegram, loader=load_state, persist=save_state):
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("Missing configured Telegram secret")
    if os.environ.get("TELEGRAM_CHANNEL", CHANNEL) not in ("", CHANNEL):
        raise RuntimeError("Refusing to edit any other channel")
    state = loader()
    status = state.setdefault("branding", {})
    if status.get("version", 0) >= VERSION:
        print("AI FREE DROP welcome v4 already applied.")
        return
    if len(DESCRIPTION) > 255 or len(WELCOME) > 4096:
        raise ValueError("Telegram text limit exceeded")
    message_id = status.get("welcome_id")
    if not isinstance(message_id, int) or isinstance(message_id, bool) or message_id <= 0:
        raise RuntimeError("Original pinned welcome message id missing; do not create duplicate")
    chat = api(token, "getChat", {"chat_id": CHANNEL})
    if (not isinstance(chat, dict) or chat.get("type") != "channel"
            or (chat.get("username") or "").lower() != "aifreedrop"):
        raise RuntimeError("Expected public AIFREEDROP channel was not verified")
    if not status.get("description_v4"):
        api(token, "setChatDescription", {"chat_id": CHANNEL, "description": DESCRIPTION})
        status["description_v4"] = True
        persist(state)
    api(token, "editMessageText", {
        "chat_id": CHANNEL, "message_id": message_id,
        "text": WELCOME, "parse_mode": "HTML",
        "disable_web_page_preview": True
    })
    status["version"] = VERSION
    persist(state)
    print("AIFREEDROP welcome v4 edited in place; no new post created.")


def refresh_profile(api=telegram):
    """Apply the public VAULTIX profile without changing the channel handle."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("Missing configured Telegram secret")
    if os.environ.get("TELEGRAM_CHANNEL", CHANNEL) not in ("", CHANNEL):
        raise RuntimeError("Refusing to edit any other channel")
    payload = {"chat_id": CHANNEL}
    chat = api(token, "getChat", payload)
    if (not isinstance(chat, dict) or chat.get("type") != "channel"
            or (chat.get("username") or "").lower() != "aifreedrop"):
        raise RuntimeError("Expected public AIFREEDROP channel was not verified")
    if len(PROFILE_DESCRIPTION) > 255:
        raise ValueError("Telegram description limit exceeded")
    if chat.get("title") != PROFILE_TITLE:
        api(token, "setChatTitle", {**payload, "title": PROFILE_TITLE})
    if chat.get("description") != PROFILE_DESCRIPTION:
        api(token, "setChatDescription", {**payload, "description": PROFILE_DESCRIPTION})
    verified = api(token, "getChat", payload)
    if (verified.get("title"), verified.get("description")) != (PROFILE_TITLE, PROFILE_DESCRIPTION):
        raise RuntimeError("The VAULTIX channel profile could not be verified")
    print("Verified VAULTIX title and description on @AIFREEDROP.")


if __name__ == "__main__":
    refresh()
    refresh_profile()
