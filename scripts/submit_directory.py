"""Submit @AIFREEDROP once to TGDirectory via its documented free REST API.

This action is run explicitly by a specially tagged GitHub commit, not on a cron.
The channel remains pending until the directory reviews and approves it.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request

API = "https://telegramchannels.io/api/channels/submit"
CHANNEL = "@AIFREEDROP"


def submit(fetch=None):
    opener = fetch or urllib.request.urlopen
    payload = json.dumps({"channel": CHANNEL}).encode("utf-8")
    req = urllib.request.Request(
        API, data=payload, method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/json",
                 "User-Agent": "AIFreeDrop/1.0"})
    with opener(req, timeout=15) as resp:
        raw = resp.read(100_001)
    if len(raw) > 100_000:
        raise ValueError("Directory response too large")
    response = json.loads(raw)
    if not isinstance(response, dict) or not response.get("ok"):
        raise RuntimeError("Directory did not accept the request")
    statuses = [item.get("status") for item in response.get("results", [])
                if isinstance(item, dict) and item.get("handle", "").lower() == "aifreedrop"]
    if not statuses:
        raise RuntimeError("Directory gave no confirmed status for AIFREEDROP")
    if statuses[0] == "submitted":
        print("TGDirectory: request accepted; listing pending review, not yet live.")
    elif statuses[0] == "duplicate":
        print("TGDirectory: channel already submitted/listed; no new submission.")
    else:
        raise RuntimeError("TGDirectory rejected or did not recognize the channel")
    # Do not print a statusToken. It is a lookup credential, not a public link.
    return statuses[0]


if __name__ == "__main__":
    submit()
