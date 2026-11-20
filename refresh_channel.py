"""One-time safe Telegram channel profile refresh for the existing pinned post.

No new messages and no profile changes outside @AIFREEDROP.
"""
import os
from bot import telegram, load_state, save_state
from branding import DESCRIPTION, WELCOME

CHANNEL = "@AIFREEDROP"


def refresh(api=telegram, loader=load_state, persist=save_state):
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("Missing configured Telegram secret")
    if os.environ.get("TELEGRAM_CHANNEL", CHANNEL) not in ("", CHANNEL):
        raise RuntimeError("Refusing to edit any other channel")
    state = loader()
    status = state.setdefault("branding", {})
    if status.get("version", 0) >= 3:
        print("AI FREE DROP branding v3 already applied.")
        return
    if len(DESCRIPTION) > 255:
        raise ValueError("Telegram description limit exceeded")
    message_id = status.get("welcome_id")
    if not isinstance(message_id, int) or message_id <= 0:
        raise RuntimeError("Original pinned welcome message id not found; do not create duplicate post")
    if not status.get("description_v2"):
        api(token, "setChatDescription", {"chat_id": CHANNEL, "description": DESCRIPTION})
        status["description_v2"] = True
        persist(state)
    api(token, "editMessageText", {"chat_id": CHANNEL, "message_id": message_id,
                                  "text": WELCOME, "parse_mode": "HTML"})
    status["version"] = 3
    persist(state)
    print("Channel description and existing pinned welcome updated to v3.")


if __name__ == "__main__":
    refresh()
