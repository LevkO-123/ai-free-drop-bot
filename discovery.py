"""Publish source-linked AI release index and Atom feed for discovery.

Only official GitHub releases that were already posted on Telegram are included.
This does not submit to external websites or guarantee referral traffic.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlsplit, unquote
from xml.etree import ElementTree as ET

BASE = "https://github.com/LevkO-123/ai-free-drop-bot"
CHANNEL = "https://t.me/AIFREEDROP"
ATOM_NS = "http://www.w3.org/2005/Atom"
ET.register_namespace("", ATOM_NS)


def official_release(item: dict):
    url = item.get("id", "")
    if not isinstance(url, str):
        return None
    parts = urlsplit(url)
    if parts.scheme != "https" or parts.netloc != "github.com" or parts.query or parts.fragment:
        return None
    components = parts.path.strip("/").split("/")
    if len(components) != 5 or components[2:4] != ["releases", "tag"]:
        return None
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", components[0]) or not re.fullmatch(r"[A-Za-z0-9_.-]+", components[1]):
        return None
    return {"url": url, "repo": f"{components[0]}/{components[1]}",
            "tag": unquote(components[4])[:140], "project": str(item.get("project", components[1]))[:80],
            "time": str(item.get("time", ""))}


def safe_md(value):
    return re.sub(r"([\\*_[\]<>])", r"\\\1", str(value))


def render(state):
    seen = set()
    posts = []
    for raw in reversed(state.get("posted", [])):
        item = official_release(raw)
        if item and item["url"] not in seen:
            seen.add(item["url"])
            posts.append(item)
    lines = [
        "# Free AI Release Tracker — Official Sources",
        "",
        "A regularly updated archive of open-source AI releases shared by **AI FREE DROP**.",
        "Get concise updates and ready-to-use AI workflows on **[Telegram @AIFREEDROP](https://t.me/AIFREEDROP)**.",
        "",
        "Every release below links directly to its publisher on GitHub. Open-source software may still require paid hardware, cloud infrastructure or separate model licenses.",
        "",
        "## Latest release links", "",
    ]
    if not posts:
        lines += ["No release posts published yet.", ""]
    else:
        for p in posts[:60]:
            lines += [f"- **{safe_md(p['project'])}** — [{safe_md(p['tag'])}]({p['url']}) · {safe_md(p['time'][:10])}", ""]
    lines += [
        "## Read the next update", "",
        "- [AI FREE DROP on Telegram](https://t.me/AIFREEDROP)",
        "- [Free AI tools directory](CATALOG.md)",
        "- [Atom release feed](feed.xml)", "",
        "Not affiliated with Telegram or the listed projects. No paid placements, guaranteed earnings, or fake airdrops.", "",
    ]
    tag = lambda x: f"{{{ATOM_NS}}}{x}"
    feed = ET.Element(tag("feed"))
    ET.SubElement(feed, tag("id")).text = BASE + "/blob/main/feed.xml"
    ET.SubElement(feed, tag("title")).text = "AI FREE DROP — Verified AI Releases"
    ET.SubElement(feed, tag("link"), {"href": BASE + "/blob/main/DROPS.md"})
    ET.SubElement(feed, tag("link"), {"rel": "alternate", "href": CHANNEL})
    ET.SubElement(feed, tag("updated")).text = posts[0]["time"] if posts else "2026-11-19T00:00:00+00:00"
    for p in posts[:30]:
        entry = ET.SubElement(feed, tag("entry"))
        ET.SubElement(entry, tag("id")).text = p["url"]
        ET.SubElement(entry, tag("title")).text = f"{p['project']} — {p['tag']}"
        ET.SubElement(entry, tag("link"), {"href": p["url"]})
        ET.SubElement(entry, tag("updated")).text = p["time"]
        ET.SubElement(entry, tag("summary")).text = (
            "Official open-source AI release notes. "
            "Free software may still entail hardware, hosting or model-license costs. "
            "More free AI tools: " + CHANNEL)
    return "\n".join(lines), ET.tostring(feed, encoding="unicode", xml_declaration=True)


def build(state_path=Path("data/state.json"), index_path=Path("DROPS.md"), feed_path=Path("feed.xml")):
    state = json.loads(state_path.read_text(encoding="utf-8"))
    md, atom = render(state)
    index_path.write_text(md, encoding="utf-8")
    feed_path.write_text(atom + "\n", encoding="utf-8")
    print("Discovery archive updated:", len(state.get("posted", [])), "total posts")


if __name__ == "__main__":
    build()
