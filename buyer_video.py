"""Create platform-ready VAULTIX buyer videos from the existing buyer queue."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from bot import BUYER_CAMPAIGN_START, BUYER_POSTS

SIZE = (720, 1280)
FONT = Path("/usr/share/fonts/truetype/dejavu")
INK = "#f3f6ef"
GREEN = "#b8f776"
BORDER = "#425346"


def font(size, bold=False):
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype(str(FONT / name), size)


def wrap(draw, text, face, width):
    lines = [""]
    for word in text.split():
        candidate = f"{lines[-1]} {word}".strip()
        if lines[-1] and draw.textlength(candidate, font=face) > width:
            lines.append(word)
        else:
            lines[-1] = candidate
    return lines


def paragraph(draw, text, left, top, width, sizes, color, max_height, bold=False):
    for size in sizes:
        face = font(size, bold)
        lines = wrap(draw, text, face, width)
        step = round(size * 1.26)
        if step * len(lines) <= max_height:
            for index, line in enumerate(lines):
                draw.text((left, top + index * step), line, font=face, fill=color)
            return
    raise ValueError(f"Text will not fit the video card: {text!r}")


def frame(path, section, headline, body):
    image = Image.new("RGB", SIZE, "#101913")
    draw = ImageDraw.Draw(image)
    for y in range(SIZE[1]):
        shade = max(0, 13 - y // 66)
        draw.line((0, y, SIZE[0], y), fill=(13 + shade, 23 + shade, 17 + shade))
    draw.text((54, 146), "VAULTIX", font=font(35, True), fill=INK)
    draw.line((54, 213, 617, 213), fill=BORDER, width=2)
    draw.text((55, 239), section, font=font(24, True), fill=GREEN)
    paragraph(draw, headline, 54, 315, 560, range(74, 47, -2), INK, 295, bold=True)
    if body:
        draw.rounded_rectangle((54, 645, 623, 978), radius=22, fill="#1f3025", outline=BORDER, width=2)
        paragraph(draw, body, 78, 676, 520, range(43, 26, -2), INK, 275)
    image.save(path)


def cards(index, title, body):
    if index == 0:
        return (
            ("DEALER QUOTE", "Get the real price before you visit", "Ask for the written out-the-door total for the exact VIN.", 5),
            ("COPY THIS TEXT", "Ask for an itemized quote", "“Can you send the full total with taxes, registration, fees and required add-ons?”", 7),
            ("COMPARE THE OFFERS", "Put two quotes side by side", "Keep trade-in and financing separate. Find the VAULTIX Deal Sheet on our profile.", 6),
        )
    sections = re.split(r"(?<=[.!?])\s+(?=[A-Z“])", body, maxsplit=1)
    return (
        ("USED-CAR BUYING", title, sections[0], 7),
        ("BEFORE YOU COMMIT", "What to check next", sections[-1] if len(sections) > 1 else "Save the seller’s written answer with the VIN and your quote.", 8),
        ("VAULTIX DEAL SHEET", "Compare both written quotes", "Keep exact prices, fees and unanswered questions together. See the link on our profile.", 6),
    )


def render(index, output):
    title, body = BUYER_POSTS[index]
    output.mkdir(parents=True, exist_ok=True)
    name = f"vaultix-{index + 1:02d}"
    target = output / f"{name}.mp4"
    with tempfile.TemporaryDirectory(dir=output) as temp:
        folder = Path(temp)
        segments = []
        for position, (heading, headline, copy, seconds) in enumerate(cards(index, title, body)):
            still = folder / f"{position}.png"
            segment = folder / f"{position}.mp4"
            frame(still, heading, headline, copy)
            subprocess.run([
                "ffmpeg", "-loglevel", "error", "-y", "-threads", "1", "-i", str(still),
                "-vf", f"zoompan=z='min(1.03,1+on*0.00018)':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d={seconds * 24}:s=720x1280:fps=24",
                "-an", "-c:v", "libx264", "-threads", "2", "-preset", "veryfast",
                "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(segment),
            ], check=True, timeout=30)
            segments.append(segment.name)
        playlist = folder / "segments.txt"
        playlist.write_text("".join(f"file '{segment}'\n" for segment in segments), encoding="ascii")
        ready = folder / "ready.mp4"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-f", "concat", "-safe", "1",
                        "-i", str(playlist), "-c", "copy", "-movflags", "+faststart", str(ready)],
                       check=True, timeout=10)
        probe = json.loads(subprocess.check_output([
            "ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(ready)
        ], timeout=10))
        stream = probe["streams"][0]
        duration = float(probe["format"]["duration"])
        if (stream["width"], stream["height"], stream["codec_name"]) != (720, 1280, "h264") or not 17 <= duration <= 22:
            raise ValueError("Video failed format or duration verification")
        subprocess.run(["ffmpeg", "-v", "error", "-xerror", "-i", str(ready), "-f", "null", "-"],
                       check=True, timeout=20)
        ready.replace(target)
    return {
        "id": name,
        "date": (BUYER_CAMPAIGN_START + dt.timedelta(days=index)).isoformat(),
        "file": target.name,
        "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        "seconds": duration,
        "youtube_title": title,
        "youtube_description": body + "\n\nVAULTIX Used-Car Deal Sheet: "
        + "https://chornyilev.gumroad.com/l/xqfrfgk?utm_source=youtube&utm_medium=social"
        + f"&utm_campaign=buyer_video&utm_content={name}",
        "tiktok_caption": body + "\n\nVAULTIX buyer kit via the profile. #UsedCarBuying #CarShopping #VAULTIX",
    }


def main():
    cli = argparse.ArgumentParser()
    group = cli.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true")
    group.add_argument("--day", type=int, choices=range(1, len(BUYER_POSTS) + 1))
    group.add_argument("--date", type=dt.date.fromisoformat)
    cli.add_argument("--output", type=Path, required=True)
    args = cli.parse_args()
    if args.all:
        indices = range(len(BUYER_POSTS))
    else:
        index = args.day - 1 if args.day else (args.date - BUYER_CAMPAIGN_START).days
        if not 0 <= index < len(BUYER_POSTS):
            cli.error("No editorial brief exists for that date")
        indices = [index]
    manifest = [render(index, args.output) for index in indices]
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Verified {len(manifest)} video(s), {args.output / 'manifest.json'}")


if __name__ == "__main__":
    main()
