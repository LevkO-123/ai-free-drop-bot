"""Submit AI FREE DROP once per site to clearly opt-in free public channel directories.

Use only published HTML form endpoints with no authentication or CAPTCHA.
This script is invoked manually once by an explicitly tagged GitHub commit.
It never uses a Telegram credential and never contacts other channels/users.
"""
from __future__ import annotations

import datetime as dt
import http.cookiejar
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from html import unescape
from pathlib import Path

CHANNEL = "https://t.me/AIFREEDROP"
RESULTS = Path("data/directory_submissions.json")

SITES = (
    {"key": "TGMetrix", "form": "https://tgmetrix.com/en/add-channel/",
     "action": "https://tgmetrix.com/api/submit/",
     "data": {"username": "@AIFREEDROP", "locale": "en", "website": ""}},
    {"key": "TeleSeeker", "form": "https://teleseeker.com/submit",
     "action": "https://teleseeker.com/submit",
     "data": {"link": CHANNEL}},
)


def interpret(body, location):
    try:
        obj = json.loads(body)
    except (ValueError, UnicodeDecodeError):
        obj = None
    if isinstance(obj, dict):
        if obj.get("success") is True or obj.get("ok") is True:
            return "accepted"
        if obj.get("status") in ("submitted", "added", "queued", "pending", "duplicate"):
            return obj["status"]
        if obj.get("success") is False or obj.get("ok") is False:
            return "rejected"
    path = urllib.parse.urlsplit(location).path.lower()
    if any(word in path for word in ("/success", "/thank-you", "/submitted", "/added")):
        return "accepted"
    match = re.search(r"<(?:h1|h2)[^>]*>(.*?)</(?:h1|h2)>", body, re.I | re.S)
    if match:
        heading = unescape(re.sub(r"<[^>]*>", "", match.group(1))).strip().lower()
        if any(phrase in heading for phrase in ("thank you", "successfully submitted", "submission received", "channel added")):
            return "accepted"
    return "unconfirmed"


def submit(site, opener=None):
    if opener is None:
        opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    get = urllib.request.Request(site["form"], headers={
        "User-Agent": "AIFREEDROP/1.0 (+https://t.me/AIFREEDROP)", "Accept": "text/html"})
    with opener.open(get, timeout=12) as response:
        if response.status != 200:
            raise RuntimeError("directory form GET did not return 200")
        response.read(200_000)
    encoded = urllib.parse.urlencode(site["data"]).encode("utf-8")
    post = urllib.request.Request(site["action"], method="POST", data=encoded, headers={
        "User-Agent": "AIFREEDROP/1.0 (+https://t.me/AIFREEDROP)",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json, text/html",
        "Referer": site["form"],
    })
    with opener.open(post, timeout=15) as response:
        url = response.geturl()
        if urllib.parse.urlsplit(url).hostname != urllib.parse.urlsplit(site["action"]).hostname:
            raise RuntimeError("unexpected cross-site redirect")
        if not 200 <= response.status < 300:
            raise RuntimeError(f"directory returned HTTP {response.status}")
        body = response.read(100_001)
        if len(body) > 100_000:
            raise ValueError("directory response too large")
    return interpret(body.decode("utf-8", errors="replace"), url)


def main():
    existing = {}
    if RESULTS.exists():
        existing = json.loads(RESULTS.read_text(encoding="utf-8"))
    for site in SITES:
        key = site["key"]
        if key in existing:
            print(key + ": previously attempted; do not resubmit.")
            continue
        try:
            status = submit(site)
        except urllib.error.HTTPError as err:
            status = "http_" + str(err.code)
        except Exception as err:
            status = "error_" + type(err).__name__
        existing[key] = {
            "status": status, "checked_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "submitted_channel": CHANNEL,
        }
        print(key + ": " + status)
    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    RESULTS.write_text(json.dumps(existing, indent=2) + "\n", encoding="utf-8")
    # A rejection or unconfirmed response is not a verified listing.
    return existing


if __name__ == "__main__":
    main()
