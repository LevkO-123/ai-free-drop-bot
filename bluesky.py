"""Optional one-post-per-day Bluesky referral to the Telegram channel."""
import datetime as dt
import json
import os
import sys
import urllib.request

from bot import load_state, save_state

UTC = dt.timezone.utc


def api(url, data, token=None):
    body = json.dumps(data).encode("utf-8")
    headers = {"Content-Type": "application/json", "User-Agent": "AIFreeDrop/1.0"}
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(url, data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read(200_000))


def post(now=None):
    now = now or dt.datetime.now(UTC)
    today = now.date().isoformat()
    handle = os.environ.get("BSKY_HANDLE", "").strip()
    password = os.environ.get("BSKY_APP_PASSWORD", "").strip()
    if not handle or not password:
        print("Bluesky optional distribution not configured.")
        return 0
    state = load_state()
    if state.get("bluesky_day") == today:
        print("Already distributed to Bluesky today.")
        return 0
    posts = [p for p in state.get("posted", []) if p.get("date") == today]
    if not posts:
        print("Nothing new to cross-post today.")
        return 0
    newest = posts[-1]
    source = newest["id"] if newest["id"].startswith("https://github.com/") else ""
    channel = "https://t.me/AIFREEDROP"
    text = ("🧰 Fresh AI workflow & open-source tools from AI FREE DROP.\n"
            + ("Latest release: " + source + "\n" if source else "")
            + "Follow the curated updates: " + channel + "\n#AITools")
    facets = []
    for url in (source, channel):
        if not url:
            continue
        start = text.index(url)
        first = len(text[:start].encode("utf-8"))
        facets.append({"index": {"byteStart": first, "byteEnd": first + len(url.encode("utf-8"))},
                       "features": [{"$type": "app.bsky.richtext.facet#link", "uri": url}]})
    try:
        session = api("https://bsky.social/xrpc/com.atproto.server.createSession",
                      {"identifier": handle, "password": password})
        api("https://bsky.social/xrpc/com.atproto.repo.createRecord",
            {"repo": session["did"], "collection": "app.bsky.feed.post",
             "record": {"$type": "app.bsky.feed.post", "text": text, "facets": facets,
                        "createdAt": now.isoformat(timespec="milliseconds").replace("+00:00", "Z")}},
            token=session["accessJwt"])
    except Exception:
        print("Bluesky distribution failed; check app password and account.", file=sys.stderr)
        return 1
    state["bluesky_day"] = today
    save_state(state)
    print("Published one daily Bluesky referral post.")
    return 0


if __name__ == "__main__":
    sys.exit(post())
