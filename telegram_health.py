"""Check the public AIFREEDROP feed independently of the publishing API."""

import argparse
import datetime as dt
import json
import time
import urllib.request
from html.parser import HTMLParser

from bot import CHANNEL, MAX_POSTS, STATE, now_utc, parse_date


PUBLIC_FEED = "https://t.me/s/AIFREEDROP"
MAX_PAGE = 2_000_000


class FeedPosts(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag != "div" or "tgme_widget_message" not in attrs.get("class", "").split():
            return
        channel, _, message_id = attrs.get("data-post", "").partition("/")
        if channel.casefold() == CHANNEL[1:].casefold() and message_id.isdecimal():
            self.ids.add(int(message_id))


def fetch_public_ids():
    request = urllib.request.Request(PUBLIC_FEED, headers={"User-Agent": "AIFreeDrop/1.0"})
    with urllib.request.urlopen(request, timeout=20) as response:
        if response.geturl().rstrip("/") != PUBLIC_FEED:
            raise ValueError("Unexpected public-feed redirect")
        body = response.read(MAX_PAGE + 1)
    if len(body) > MAX_PAGE:
        raise ValueError("Public feed response was unexpectedly large")
    parser = FeedPosts()
    parser.feed(body.decode("utf-8"))
    if not parser.ids:
        raise ValueError("Telegram did not return recognizable public messages")
    return parser.ids


def receipt_times(state, now):
    ledger = {}
    for post in state.get("posted", []):
        message_id = post.get("message_id")
        published_at = parse_date(post.get("time"))
        if type(message_id) is int and message_id > 0 and published_at and published_at <= now:
            ledger[message_id] = published_at
    return ledger


def verify_recent_receipts(state, now, *, fetch=fetch_public_ids, pause=time.sleep):
    cutoff = now - dt.timedelta(minutes=25)
    recent_ids = {mid for mid, sent in receipt_times(state, now).items() if sent >= cutoff}
    if not recent_ids:
        print("No recent Telegram send receipt to verify.")
        return 0

    missing = recent_ids.copy()
    for delay in (0, 8, 20):
        if delay:
            pause(delay)
        try:
            missing &= recent_ids - fetch()
        except (OSError, ValueError):
            continue
        if not missing:
            print("Public Telegram delivery verified:", ", ".join(map(str, sorted(recent_ids))))
            return 0

    print("::error::Unable to verify public Telegram delivery for stored receipt IDs: "
          + ", ".join(map(str, sorted(missing))))
    return 1


def audit(state, public_ids, now):
    yesterday = now.date() - dt.timedelta(days=1)
    ledger = receipt_times(state, now)

    yesterday_ids = {mid for mid, published_at in ledger.items() if published_at.date() == yesterday}
    visible_yesterday = yesterday_ids & public_ids
    errors = []
    if len(visible_yesterday) < MAX_POSTS:
        errors.append(f"{yesterday} UTC: {len(visible_yesterday)}/{MAX_POSTS} bot posts verified public")
    unexpected = yesterday_ids - public_ids
    if unexpected:
        errors.append("Telegram feed is missing recorded messages: " + ", ".join(map(str, sorted(unexpected))))
    if not any(published_at > now - dt.timedelta(hours=26) and mid in public_ids
               for mid, published_at in ledger.items()):
        errors.append("No recorded bot publication was verified public in the last 26 hours")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recent", action="store_true", help="Verify recent sends after a publisher run.")
    args = parser.parse_args()
    state = json.loads(STATE.read_text(encoding="utf-8"))
    now = now_utc()
    if args.recent:
        return verify_recent_receipts(state, now)
    errors = audit(state, fetch_public_ids(), now)
    if errors:
        for error in errors:
            print(f"::error::{error}")
        return 1
    print("Telegram public feed matched the previous UTC day's publication ledger.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as error:
        print(f"::error::Telegram public-feed check could not complete: {type(error).__name__}")
        raise SystemExit(1) from None
