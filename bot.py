"""AI FREE DROP: source-linked, autonomous Telegram publisher.

No third-party AI API, purchases, unsolicited DMs, or speculative deals.
Never put credentials in source control; only environment variables are used.
"""
from __future__ import annotations

import datetime as dt
import html
import json
import os
import re
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

UTC = dt.timezone.utc
ROOT = Path(__file__).resolve().parent
STATE = ROOT / "data/state.json"
CHANNEL = "@AIFREEDROP"
ATOM = "{http://www.w3.org/2005/Atom}"
MAX_POSTS = 5
SOURCES = (
    ("ollama/ollama", "Ollama", "Run AI models locally"),
    ("open-webui/open-webui", "Open WebUI", "A self-hosted AI chat interface"),
    ("ggml-org/llama.cpp", "llama.cpp", "Efficient model inference"),
    ("Comfy-Org/ComfyUI", "ComfyUI", "Visual generative AI workflows"),
    ("huggingface/transformers", "Transformers", "Machine-learning model tooling"),
    ("vllm-project/vllm", "vLLM", "High-throughput AI model serving"),
    ("continuedev/continue", "Continue", "Open-source coding assistance"),
    ("langgenius/dify", "Dify", "AI workflows and applications"),
)
TIPS = (
    ("Turn messy notes into a plan", "You are my operations assistant. Turn the notes below into: (1) a concise summary, (2) 5 prioritized actions, (3) deadlines marked UNKNOWN unless provided, and (4) questions I must answer. Notes: [PASTE NOTES]", "https://help.openai.com/en/articles/4936848-how-do-i-create-a-good-prompt-for-an-ai-model"),
    ("Write a message that gets a reply", "Rewrite this message so a busy person wants to respond. Keep it under 70 words, human and polite. Include one simple question. Don't invent details. Message: [PASTE TEXT]", "https://help.openai.com/en/articles/4936848-how-do-i-create-a-good-prompt-for-an-ai-model"),
    ("Learn anything in 15 minutes", "Teach me [TOPIC] in plain English. Start with a real-life analogy, then explain 3 key concepts, one common mistake and a 5-question mini quiz. Adapt to a beginner.", "https://help.openai.com/en/articles/4936848-how-do-i-create-a-good-prompt-for-an-ai-model"),
    ("Spot risky wording in a car listing", "Review this used-car listing: [PASTE TEXT]. Separate verified details, seller claims, missing documents and questions I should ask. Do not assert fraud or hidden mechanical problems without evidence.", "https://github.com/LevkO-123/ai-free-drop-bot/blob/main/CAR_BUYER_AI_KIT.md"),
    ("Plan a smarter used-BMW inspection", "I am considering a [YEAR] [BMW MODEL] with [MILES]. Build a buyer checklist for documents, cold start, road test, electronic faults and a mechanic's inspection. Label every model-specific risk UNVERIFIED unless supported by an authoritative source.", "https://github.com/LevkO-123/ai-free-drop-bot/blob/main/CAR_BUYER_AI_KIT.md"),
    ("Check the paperwork before buying", "Make a checklist of used-car paperwork to verify in [STATE]: title status, VIN match, lien release, service records, mileage history and open recalls. Explain what each document can and cannot prove. Don't pretend to access private records.", "https://github.com/LevkO-123/ai-free-drop-bot/blob/main/CAR_BUYER_AI_KIT.md"),
    ("Negotiate a used-car price with evidence", "Write a short respectful offer for [YEAR MAKE MODEL] priced at [ASKING PRICE]. Base it only on these verifiable facts: [INSPECTION FINDINGS AND COMPARABLE LISTINGS]. Do not invent defects, competing bids or market prices.", "https://github.com/LevkO-123/ai-free-drop-bot/blob/main/CAR_BUYER_AI_KIT.md"),
    ("Understand a dashboard warning safely", "Help me prepare questions for a mechanic about this dashboard warning: [EXACT MESSAGE], car [YEAR MAKE MODEL], symptoms [SYMPTOMS]. List what should be scanned or inspected without claiming a diagnosis, and identify signs that make driving unsafe.", "https://github.com/LevkO-123/ai-free-drop-bot/blob/main/CAR_BUYER_AI_KIT.md"),
    ("Compare two car listings", "Compare these two used vehicles: [LISTING A] and [LISTING B]. Make a table for price, mileage, known history, open questions, inspection steps and total ownership cost categories. Mark all unsupported reliability claims UNKNOWN.", "https://github.com/LevkO-123/ai-free-drop-bot/blob/main/CAR_BUYER_AI_KIT.md"),
    ("Turn a pre-purchase inspection into a decision", "Summarize this actual pre-purchase inspection report: [PASTE REPORT WITH PERSONAL DETAILS REMOVED]. Distinguish urgent safety issues, routine maintenance, and uncertain findings. Suggest follow-up questions and avoid inventing repair quotes.", "https://github.com/LevkO-123/ai-free-drop-bot/blob/main/CAR_BUYER_AI_KIT.md"),
    ("Turn feedback into a better product", "Analyze this customer feedback: [PASTE FEEDBACK]. Separate facts from opinions. Cluster issues, rank by frequency and severity, and suggest 3 small experiments with success metrics.", "https://help.openai.com/en/articles/4936848-how-do-i-create-a-good-prompt-for-an-ai-model"),
    ("Check AI claims before sharing", "Fact-check the following AI-related claim: [PASTE CLAIM]. Identify exactly what needs verification, suggest primary sources to check, and label anything you cannot confirm. Do not invent citations or dates.", "https://help.openai.com/en/articles/4936848-how-do-i-create-a-good-prompt-for-an-ai-model"),
    ("Before leaving to see a used car", "Turn this actual listing [TEXT] into a 10-minute screening checklist: title, VIN, seller identity, service records, price, known defects, inspection permission. Separate listing claims from verified facts.", "https://github.com/LevkO-123/ai-free-drop-bot/blob/main/CAR_BUYER_AI_KIT.md"),
    ("Compare private seller vs dealer", "Compare these two offers [OFFERS], including stated fees, warranty terms, paperwork, inspection access and unknowns. Do not invent legal requirements or market values; identify what to verify locally.", "https://github.com/LevkO-123/ai-free-drop-bot/blob/main/CAR_BUYER_AI_KIT.md"),
    ("Cold-start questions to ask", "Draft questions to arrange a genuine cold start before inspecting [VEHICLE]. Explain what a mechanic should observe, without diagnosing from a sound or inventing defects.", "https://github.com/LevkO-123/ai-free-drop-bot/blob/main/CAR_BUYER_AI_KIT.md"),
    ("Read a repair quote line by line", "Turn [QUOTE WITHOUT PERSONAL DETAILS] into a table of labor, parts, tax, fees, warranty and unresolved diagnosis. Identify questions rather than judging the shop without evidence.", "https://github.com/LevkO-123/ai-free-drop-bot/blob/main/CAR_BUYER_AI_KIT.md"),
    ("Make an inspection appointment", "Draft a short message to a qualified mechanic requesting a pre-purchase inspection for [YEAR MAKE MODEL]. Include mileage, known symptoms, requested written findings and a price confirmation.", "https://github.com/LevkO-123/ai-free-drop-bot/blob/main/CAR_BUYER_AI_KIT.md"),
    ("Spot missing service history", "Organize [SERVICE RECORDS] by date, mileage and documented service. Flag gaps and discrepancies for verification. Do not infer skipped maintenance just because a record is missing.", "https://github.com/LevkO-123/ai-free-drop-bot/blob/main/CAR_BUYER_AI_KIT.md"),
    ("Check a recall the right way", "Create a checklist to verify open recalls using official manufacturer and government sources for [YEAR MAKE MODEL]. Explain why VIN-specific confirmation matters. Do not claim you checked a VIN.", "https://github.com/LevkO-123/ai-free-drop-bot/blob/main/CAR_BUYER_AI_KIT.md"),
    ("Compare two monthly car costs", "Use only my numbers [PRICE, DOWN PAYMENT, APR, TERM, INSURANCE, MILES, MPG, FUEL PRICE] to compare monthly and total costs. Show formulas, missing costs and sensitivity to fuel prices.", "https://github.com/LevkO-123/ai-free-drop-bot/blob/main/CAR_BUYER_AI_KIT.md"),
    ("Avoid the monthly-payment trap", "Given this financing offer [PRICE, APR, TERM, FEES, DOWN PAYMENT], separate financed principal, estimated interest and total repayment. Flag missing terms and independently verify against the written contract.", "https://github.com/LevkO-123/ai-free-drop-bot/blob/main/CAR_BUYER_AI_KIT.md"),
    ("Prepare questions about a rebuilt title", "List practical questions for the seller, insurer, state title office and independent inspector about this [TITLE DESCRIPTION]. Do not assume the vehicle is safe or eligible for registration or insurance.", "https://github.com/LevkO-123/ai-free-drop-bot/blob/main/CAR_BUYER_AI_KIT.md"),
    ("Document intermittent symptoms", "Create a symptom diary for [ISSUE] with time, temperature, speed, warning lights and conditions. Distinguish what I observed from guesses. Include when to stop driving and seek professional help.", "https://github.com/LevkO-123/ai-free-drop-bot/blob/main/CAR_BUYER_AI_KIT.md"),
    ("Ask about an engine warning", "Write a concise note for a mechanic describing [EXACT WARNING, SYMPTOMS, WHEN IT OCCURS]. Ask what tests would verify the fault; do not recommend replacing parts based on a code alone.", "https://github.com/LevkO-123/ai-free-drop-bot/blob/main/CAR_BUYER_AI_KIT.md"),
    ("Evaluate a seller's new-parts claim", "Extract the claimed repairs from [LISTING]. Prepare questions requesting receipts, exact part descriptions, date, mileage and warranty. Do not assume new parts prove the underlying problem is resolved.", "https://github.com/LevkO-123/ai-free-drop-bot/blob/main/CAR_BUYER_AI_KIT.md"),
    ("Build a vehicle comparison scorecard", "Create a scorecard for [VEHICLES] with my priorities [BUDGET, USE, SPACE, WEATHER, RELIABILITY]. Score only documented facts and leave unknowns unscored.", "https://github.com/LevkO-123/ai-free-drop-bot/blob/main/CAR_BUYER_AI_KIT.md"),
    ("Prepare for a test drive", "Create a safe, legal test-drive observation list for [CAR]. Include basic controls, warning lights, braking feel, steering and unusual sounds. Do not suggest unsafe maneuvers or a diagnosis.", "https://github.com/LevkO-123/ai-free-drop-bot/blob/main/CAR_BUYER_AI_KIT.md"),
    ("Check the real ownership budget", "Build a monthly ownership worksheet with known payment, insurance, registration, fuel, tires and maintenance reserve. Use my inputs [NUMBERS] and label any missing amounts.", "https://github.com/LevkO-123/ai-free-drop-bot/blob/main/CAR_BUYER_AI_KIT.md"),
    ("Turn a listing into a seller message", "Write a friendly message about [CAR] asking whether it is available, title status, known issues, service records and whether a professional inspection is allowed. No accusations or invented offers.", "https://github.com/LevkO-123/ai-free-drop-bot/blob/main/CAR_BUYER_AI_KIT.md"),
    ("Ask about repair warranty", "Draft five questions to clarify the warranty on [REPAIR QUOTE], covering written terms, parts and labor, exclusions, who handles a failure and any required follow-up.", "https://github.com/LevkO-123/ai-free-drop-bot/blob/main/CAR_BUYER_AI_KIT.md"),
    ("Understand a diagnostic code", "Explain the general meaning of [CODE] for [YEAR MAKE MODEL] using official sources if available. Distinguish possible causes from confirmed failure and suggest questions for a qualified technician.", "https://github.com/LevkO-123/ai-free-drop-bot/blob/main/CAR_BUYER_AI_KIT.md"),
    ("Summarize actual inspection findings", "Sort [REPORT] into verified defects, recommended maintenance, items needing further diagnosis and cosmetic observations. Explain what evidence supports each category and flag unknown costs.", "https://github.com/LevkO-123/ai-free-drop-bot/blob/main/CAR_BUYER_AI_KIT.md"),
    ("Check accessories before purchasing", "Compare [ACCESSORY OPTIONS] for this [YEAR MAKE MODEL TRIM]. Identify exact part number, connector, fitment, power and installation requirements to verify from the manufacturer. Do not guess compatibility.", "https://github.com/LevkO-123/ai-free-drop-bot/blob/main/CAR_BUYER_AI_KIT.md"),
    ("Organize a car maintenance history", "Convert these receipts [TEXT] into a date and mileage table with completed service and unknown intervals. Recommend checking the official maintenance schedule rather than inventing one.", "https://github.com/LevkO-123/ai-free-drop-bot/blob/main/CAR_BUYER_AI_KIT.md"),
    ("Decide whether to walk away", "Given [LISTING, INSPECTION REPORT, BUDGET], make a decision table with verified safety concerns, financial risks, unknowns and questions. Do not imply that a checklist guarantees the car is safe.", "https://github.com/LevkO-123/ai-free-drop-bot/blob/main/CAR_BUYER_AI_KIT.md"),
    ("Compare two mechanic estimates", "Compare [ESTIMATE A] and [ESTIMATE B] by scope, parts, labor, warranty and diagnostic evidence. Flag operations that are not directly comparable rather than assuming the cheaper quote is better.", "https://github.com/LevkO-123/ai-free-drop-bot/blob/main/CAR_BUYER_AI_KIT.md"),
    ("Draft a written repair authorization", "Draft a message approving only the listed scope and price [SCOPE AND AMOUNT], requesting notice and separate approval before additional work. Keep it factual and polite.", "https://github.com/LevkO-123/ai-free-drop-bot/blob/main/CAR_BUYER_AI_KIT.md"),
    ("Check a used EV or hybrid listing", "Create questions about documented battery health, charging equipment, warranty, recalls and service history for [VEHICLE]. Identify what requires professional testing; never invent battery capacity or condition.", "https://github.com/LevkO-123/ai-free-drop-bot/blob/main/CAR_BUYER_AI_KIT.md"),
    ("Compare towing claims", "Identify official sources needed to verify towing and payload limits for [VEHICLE CONFIGURATION]. Explain the importance of door-label ratings, loading and equipment. Do not estimate a safe limit from an advertisement.", "https://github.com/LevkO-123/ai-free-drop-bot/blob/main/CAR_BUYER_AI_KIT.md"),
    ("Make a final purchase checklist", "Turn my verified documents, inspection and financing terms [DETAILS] into a final review checklist. List remaining missing evidence and actions before money changes hands.", "https://github.com/LevkO-123/ai-free-drop-bot/blob/main/CAR_BUYER_AI_KIT.md"),
    ("Explain an AI answer skeptically", "Review this AI-generated vehicle advice [ANSWER]. Identify unsupported claims, risky assumptions and official sources needed for verification. Rewrite it as questions for a qualified mechanic.", "https://github.com/LevkO-123/ai-free-drop-bot/blob/main/CAR_BUYER_AI_KIT.md"),
    ("Get a useful second opinion", "Create a concise second-opinion request from [SYMPTOMS, SCAN RESULTS, QUOTE], separating measurements from assumptions. Ask for independent diagnostic confirmation and a written estimate.", "https://github.com/LevkO-123/ai-free-drop-bot/blob/main/CAR_BUYER_AI_KIT.md"),
)


def now_utc():
    return dt.datetime.now(UTC)


def iso(value):
    return value.astimezone(UTC).isoformat(timespec="seconds")


def parse_date(value):
    try:
        date = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        return date.replace(tzinfo=UTC) if date.tzinfo is None else date.astimezone(UTC)
    except (AttributeError, TypeError, ValueError):
        return None


def request_json(url, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json", "User-Agent": "AIFreeDrop/1.0"})
    with urllib.request.urlopen(req, timeout=18) as resp:
        return json.loads(resp.read(200_000))


def telegram(token, method, payload):
    try:
        result = request_json("https://api.telegram.org/bot" + token + "/" + method, payload)
    except Exception:
        raise RuntimeError("Telegram request failed: check bot admin rights and deployment secrets") from None
    if not result.get("ok"):
        raise RuntimeError("Telegram rejected request: check channel permissions") from None
    return result.get("result")


def read_feed(repo, label, use):
    req = urllib.request.Request("https://github.com/" + repo + "/releases.atom",
                                 headers={"User-Agent": "AIFreeDrop/1.0", "Accept": "application/atom+xml"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        if urllib.parse.urlsplit(resp.geturl()).hostname != "github.com":
            raise ValueError("Untrusted feed redirect")
        raw = resp.read(1_000_001)
    if len(raw) > 1_000_000:
        raise ValueError("Oversized feed")
    root = ET.fromstring(raw)
    result = []
    for e in root.findall(ATOM + "entry")[:20]:
        title = (e.findtext(ATOM + "title") or "").strip()
        updated = parse_date(e.findtext(ATOM + "updated") or e.findtext(ATOM + "published"))
        href = next((x.get("href", "") for x in e.findall(ATOM + "link") if x.get("rel", "alternate") == "alternate"), "")
        prefix = "https://github.com/" + repo + "/releases/tag/"
        if not title or updated is None or not href.startswith(prefix):
            continue
        if re.search(r"(?:^|[-_ .])(alpha|beta|rc|nightly|preview)(?:\d|[-_ .]|$)", title + " " + href.rsplit("/", 1)[-1], re.I):
            continue
        result.append({"id": href, "title": re.sub(r"\s+", " ", title)[:120],
                       "project": label, "use": use, "updated": iso(updated), "url": href})
    return result


def fetch_candidates():
    items = []
    for repo, label, use in SOURCES:
        try:
            items.extend(read_feed(repo, label, use))
        except (OSError, ValueError, ET.ParseError) as e:
            print("Feed unavailable:", label, type(e).__name__, file=sys.stderr)
    return items


def load_state(path=STATE):
    if path.exists():
        state = json.loads(path.read_text(encoding="utf-8"))
    else:
        state = {}
    for key, value in (("posted", []), ("tips", []), ("counts", []), ("branding", {})):
        state.setdefault(key, value)
    return state


def save_state(state, path=STATE):
    path.parent.mkdir(parents=True, exist_ok=True)
    state["posted"] = state["posted"][-250:]
    state["counts"] = state["counts"][-90:]
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as tmp:
        json.dump(state, tmp, indent=2, ensure_ascii=False)
        tmp.write("\n")
        path_tmp = Path(tmp.name)
    path_tmp.replace(path)


def choose_post(items, state, now):
    today = now.date().isoformat()
    recent = [p for p in state["posted"] if p.get("date") == today]
    if len(recent) >= MAX_POSTS:
        return None
    prior = {p["id"] for p in state["posted"]}
    most_recent = {}
    for p in state["posted"]:
        t = parse_date(p.get("time"))
        if t and p.get("project"):
            most_recent[p["project"]] = max(t, most_recent.get(p["project"], dt.datetime.min.replace(tzinfo=UTC)))
    candidates = []
    for item in items:
        age = parse_date(item.get("updated"))
        if item["id"] in prior or not age or not now - dt.timedelta(hours=120) <= age <= now + dt.timedelta(hours=1):
            continue
        if item["project"] in most_recent and now - most_recent[item["project"]] < dt.timedelta(hours=22):
            continue
        candidates.append(item)
    def next_tip():
        for i, (title, body, url) in enumerate(TIPS):
            tip_id = "tip-" + str(i)
            if tip_id not in state["tips"] and tip_id not in prior:
                return {"id": tip_id, "project": "AI Workflow", "title": title, "body": body, "url": url}
        return None

    # Lead with useful evergreen content; keep fresh release news to at most
    # two of the five daily slots. Never invent a release or recycle a tip.
    if not recent:
        tip = next_tip()
        if tip:
            return tip
    release_count = sum(not p["id"].startswith("tip-") for p in recent)
    if candidates and release_count < 2:
        return max(candidates, key=lambda item: item["updated"])
    return next_tip()


def format_message(item):
    escape = html.escape
    url = escape(item["url"], quote=True)
    title = escape(item["title"])
    if item["id"].startswith("tip-"):
        resource_label = "Free used-car AI kit" if "CAR_BUYER_AI_KIT.md" in item["url"] else "Official prompt-writing guide"
        return (f"🎁 <b>FREE AI PROMPT — SAVE THIS</b>\n\n<b>{title}</b>\n\n"
                f"<pre>{escape(item['body'])}</pre>\n\n"
                "📌 Save it, try it, and share with someone who needs it.\n"
                f"📚 <a href=\"{url}\">{escape(resource_label)}</a>\n\n"
                "#FreeAI #AIPrompts")
    return (f"🧰 <b>OPEN-SOURCE AI RELEASE</b>\n\n<b>{escape(item['project'])} — {title}</b>\n\n"
            f"Useful for: {escape(item['use'])}.\n\n🔗 <a href=\"{url}\">Official release notes</a>\n\n"
            "Software can be free to download while models, hosting or hardware still cost money.\n\n#AITools #OpenSource")


def configure_channel(token, channel, state, now):
    from branding import configure
    configure(token, channel, state, now, api=telegram, persist=save_state)


def run(*, dry_run=False, now=None):
    now = now or now_utc()
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    channel = os.environ.get("TELEGRAM_CHANNEL", CHANNEL).strip()
    if not dry_run and (not token or not re.fullmatch(r"@[A-Za-z0-9_]{5,32}", channel)):
        raise RuntimeError("Configure a fresh TELEGRAM_BOT_TOKEN secret and TELEGRAM_CHANNEL variable")
    state = load_state()
    if not dry_run:
        configure_channel(token, channel, state, now)
    item = choose_post(fetch_candidates(), state, now)
    if not item:
        print("No new post (daily cap, duplicate filter or no suitable news).")
    elif dry_run:
        print("DRY RUN, no changes:\n" + format_message(item))
    else:
        telegram(token, "sendMessage", {"chat_id": channel, "text": format_message(item), "parse_mode": "HTML"})
        state["posted"].append({"id": item["id"], "date": now.date().isoformat(), "time": iso(now), "project": item["project"]})
        if item["id"].startswith("tip-"):
            state["tips"].append(item["id"])
        save_state(state)
        print("Posted:", item["project"], item["id"])
    today = now.date().isoformat()
    if not dry_run and not any(x.get("date") == today for x in state["counts"]):
        try:
            count = telegram(token, "getChatMemberCount", {"chat_id": channel})
            state["counts"].append({"date": today, "subscribers": int(count)})
            save_state(state)
            print("Subscriber count:", int(count))
        except Exception:
            print("Subscriber count unavailable; check bot rights.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(run(dry_run="--dry-run" in sys.argv))
    except Exception as e:
        print("FAILED:", str(e), file=sys.stderr)
        sys.exit(1)
