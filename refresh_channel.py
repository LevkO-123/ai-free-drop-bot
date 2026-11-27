"""Safely refresh the existing pinned @AIFREEDROP welcome to campaign v4.

Update the channel profile and pinned buyer resource in place.
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

SALES_PIN = (
    "<b>VAULTIX | Compare used-car offers before you commit</b>\n\n"
    "Example: $13,950 + $1,450 in taxes and fees = $15,400. "
    "$14,100 + $950 = $15,050. The higher advertised price wins by $350.\n\n"
    "Ask each seller for the written, itemized out-the-door price. "
    "Keep trade-in and financing separate, and flag optional add-ons.\n\n"
    '<a href="https://chornyilev.gumroad.com/l/xqfrfgk?utm_source=telegram&amp;utm_medium=social&amp;utm_campaign=used_car_deal_sheet">'
    "Get the VAULTIX Used-Car Deal Sheet ($12.99)</a> to compare two quotes and save the result.\n\n"
    '<a href="https://github.com/LevkO-123/ai-free-drop-bot/blob/main/CAR_BUYER_AI_KIT.md">'
    "Open the free used-car buyer kit</a> for the inspection checklist and seller questions."
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


def refresh_sales_pin(api=telegram, loader=load_state):
    """Update the verified pinned buyer resource without creating a duplicate."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token or os.environ.get("TELEGRAM_CHANNEL", CHANNEL) not in ("", CHANNEL):
        raise RuntimeError("Verified Telegram configuration is required")
    chat = api(token, "getChat", {"chat_id": CHANNEL})
    if chat.get("type") != "channel" or chat.get("username", "").lower() != "aifreedrop":
        raise RuntimeError("Expected public AIFREEDROP channel was not verified")
    pinned = chat.get("pinned_message") or {}
    message_id = loader().get("branding", {}).get("welcome_id")
    if not isinstance(message_id, int) or message_id <= 0 or pinned.get("message_id") != message_id:
        raise RuntimeError("The original buyer kit is not the current pinned message")
    expected_url = "https://chornyilev.gumroad.com/l/xqfrfgk?utm_source=telegram"
    for entity in pinned.get("entities", []):
        if entity.get("url", "").startswith(expected_url):
            print("VAULTIX sales link already present in the pinned buyer resource.")
            return
    updated = api(token, "editMessageText", {
        "chat_id": CHANNEL, "message_id": message_id, "text": SALES_PIN,
        "parse_mode": "HTML", "disable_web_page_preview": True,
    })
    if updated.get("message_id") != message_id or not any(
        item.get("url", "").startswith(expected_url) for item in updated.get("entities", [])
    ):
        raise RuntimeError("Telegram did not confirm the sales link on the pinned message")
    print(f"VAULTIX sales link confirmed: https://t.me/AIFREEDROP/{message_id}")


if __name__ == "__main__":
    refresh()
    refresh_profile()
    refresh_sales_pin()
