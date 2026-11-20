"""Read current public Telegram channel member count via configured bot credentials.

Record the latest UTC daily snapshot and a bounded intra-day observation history.
No messages are sent, no credentials are printed, and no other repositories touched.
"""
from __future__ import annotations

import os
import datetime as dt
from bot import telegram, load_state, save_state, iso, UTC


def capture(now=None, api=telegram, persist=save_state, loader=load_state):
    now = now or dt.datetime.now(UTC)
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("Missing TELEGRAM_BOT_TOKEN secret")
    channel = os.environ.get("TELEGRAM_CHANNEL", "@AIFREEDROP") or "@AIFREEDROP"
    if channel != "@AIFREEDROP":
        raise RuntimeError("Metrics task restricted to @AIFREEDROP")
    count = int(api(token, "getChatMemberCount", {"chat_id": channel}))
    if count < 0:
        raise RuntimeError("Invalid member count returned")
    state = loader()
    today = now.date().isoformat()
    observations = state.setdefault("observations", [])
    if not observations or observations[-1].get("members") != count or observations[-1].get("time", "")[:10] != today:
        observations.append({"time": iso(now), "members": count})
        state["observations"] = observations[-120:]
    counts = state.setdefault("counts", [])
    for entry in counts:
        if entry.get("date") == today:
            entry["subscribers"] = count
            break
    else:
        counts.append({"date": today, "subscribers": count})
    state["counts"] = counts[-90:]
    persist(state)
    print("Channel member count (including existing admins if counted by Telegram):", count)
    if counts:
        baseline = counts[0].get("subscribers")
        if isinstance(baseline, int):
            print("Net change since first recorded baseline:", count - baseline)
    return count


if __name__ == "__main__":
    capture()
