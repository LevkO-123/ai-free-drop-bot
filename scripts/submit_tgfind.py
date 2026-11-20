"""One-time, documented anonymous TGFind MCP submission for @AIFREEDROP.

Uses the public Streamable HTTP JSON-RPC interface; no credentials, billing,
captcha bypass, scraping or unsolicited direct messages.
"""
from __future__ import annotations

import json
import urllib.request
import urllib.error

ENDPOINT = "https://tgfind.net/api/mcp"
PROTOCOL = "2025-03-26"
HANDLE = "@AIFREEDROP"


def parse_reply(raw):
    content = raw.decode("utf-8")
    if content.lstrip().startswith("{"):
        return json.loads(content)
    for line in content.splitlines():
        if line.startswith("data:"):
            data = line[5:].strip()
            if data and data != "[DONE]":
                return json.loads(data)
    raise ValueError("Expected JSON-RPC or Server-Sent Event response")


def rpc(method, params, request_id, *, session=None, opener=urllib.request.urlopen):
    payload = {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "MCP-Protocol-Version": PROTOCOL,
        "User-Agent": "AI-FREE-DROP/1.0",
    }
    if session:
        headers["Mcp-Session-Id"] = session
    req = urllib.request.Request(ENDPOINT, data=json.dumps(payload).encode(), headers=headers, method="POST")
    with opener(req, timeout=15) as response:
        session = response.headers.get("Mcp-Session-Id", session)
        raw = response.read(120_001)
        if len(raw) > 120_000:
            raise ValueError("TGFind reply too large")
    reply = parse_reply(raw)
    if reply.get("error"):
        err = reply["error"]
        raise RuntimeError(f"TGFind MCP returned error code {err.get('code', 'unknown')}")
    return reply.get("result", {}), session


def submit(opener=urllib.request.urlopen):
    info, session = rpc("initialize", {"protocolVersion": PROTOCOL, "capabilities": {},
                "clientInfo": {"name": "ai-free-drop-submitter", "version": "1.0"}},
                1, opener=opener)
    if not isinstance(info, dict):
        raise RuntimeError("TGFind MCP handshake not understood")
    listing, session = rpc("tools/list", {}, 2, session=session, opener=opener)
    names = {item.get("name") for item in listing.get("tools", [])}
    if "submit_listing" not in names:
        raise RuntimeError("TGFind MCP submit_listing tool not available")
    result, _ = rpc("tools/call", {"name": "submit_listing",
            "arguments": {"handle": HANDLE, "type": "channel"}}, 3,
            session=session, opener=opener)
    if result.get("isError"):
        raise RuntimeError("TGFind did not accept directory submission")
    strings = [entry.get("text", "") for entry in result.get("content", [])
               if isinstance(entry, dict) and entry.get("type") == "text"]
    if not strings:
        raise RuntimeError("TGFind returned no submission acknowledgement")
    summary = " ".join(strings)
    print("TGFind response (public, truncated):", summary[:1100])
    return summary


if __name__ == "__main__":
    submit()
