"""Clean, moving-footage-only VAULTIX edit. Absolutely no on-screen text or stickers.

Sources: licensed free Pexels films already verified in cinematic_v2.py.
Footage is downloaded for rendering then discarded. Output has original
generated percussion; caption/CTA belongs in TikTok text, never on-screen.
"""
from __future__ import annotations

import datetime as dt
import pathlib
import subprocess
import tempfile
import urllib.request

import cinematic_v2 as media

ROOT = pathlib.Path(__file__).resolve().parent
OUTPUT = ROOT / "media" / "vaultix_clean_v3.mp4"

# Fast-cut original luxury automotive edit: no text and no personal footage.
# All cuts source real video, preserving 9:16 full-bleed frame.
SHOTS = [
    ("street", 0.1, 1.35),
    ("cars",   0.5, 1.15),
    ("drive",  0.2, 1.35),
    ("street", 2.7, 1.15),
    ("cars",   3.1, 1.30),
    ("drive",  4.2, 1.20),
    ("street", 4.8, 1.45),
    ("cars",   5.2, 1.25),
    ("drive",  6.5, 1.65),
]
DURATION = sum(shot[2] for shot in SHOTS)
MAX_SOURCE_SIZE = 65_000_000

def ffmpeg_run(args):
    return subprocess.run(args, check=True, stdout=subprocess.DEVNULL)

def build():
    ffmpeg = media.ffbin()
    OUTPUT.parent.mkdir(exist_ok=True, parents=True)
    with tempfile.TemporaryDirectory() as tmp:
        temp = pathlib.Path(tmp)
        sources = {}
        for key, url in media.SOURCES.items():
            dest = temp / (key + ".mp4")
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=45) as resp, dest.open("wb") as out:
                total = 0
                while chunk := resp.read(1024 * 1024):
                    total += len(chunk)
                    if total > MAX_SOURCE_SIZE:
                        raise ValueError("Source larger than capped maximum")
                    out.write(chunk)
            if total < 100_000:
                raise ValueError("Invalid motion footage")
            sources[key] = dest
            print("Verified licensed footage:", key, total, flush=True)

        parts = []
        for i, (source, start, length) in enumerate(SHOTS):
            part = temp / f"scene_{i:02d}.mp4"
            # Slightly desaturated luxury film grade; NO drawtext,
            # overlay, titles, logos, watermarks, banners or stickers.
            grade = (
                "scale=720:1280:force_original_aspect_ratio=increase,"
                "crop=720:1280,"
                "eq=contrast=1.16:saturation=0.88:brightness=-0.025,"
                "vignette=PI/10,"
                "unsharp=3:3:0.4,"
                "fps=30,format=yuv420p"
            )
            ffmpeg_run([
                ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
                "-ss", str(start), "-i", str(sources[source]),
                "-t", str(length), "-an", "-vf", grade,
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
                "-pix_fmt", "yuv420p", str(part),
            ])
            parts.append(part)
            print(f"Clean motion shot {i+1}/{len(SHOTS)}", flush=True)

        concat = temp / "list.txt"
        concat.write_text("".join(f"file '{item}'\n" for item in parts))
        silent = temp / "silent.mp4"
        ffmpeg_run([
            ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
            "-f", "concat", "-safe", "0", "-i", str(concat),
            "-c", "copy", str(silent),
        ])

        audio = temp / "original_beat.wav"
        # Ensure sound duration matches this version, not v2's original cut.
        media.DURATION = DURATION
        media.original_beat(audio)
        ffmpeg_run([
            ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
            "-i", str(silent), "-i", str(audio), "-map", "0:v:0",
            "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
            "-shortest", "-movflags", "+faststart", str(OUTPUT),
        ])
    data = OUTPUT.read_bytes()
    if data[4:8] != b"ftyp" or not 800_000 < len(data) < 30_000_000:
        raise ValueError("MP4 file failed content/size validation")
    print("CLEAN FINAL:", OUTPUT, "bytes", len(data), "seconds", DURATION, flush=True)

if __name__ == "__main__":
    build()
