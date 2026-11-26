"""Render three original educational TikTok shorts from our licensed car edits.
No AI-generation claims, no new downloads, no paid APIs. Render only; no uploads.
"""
from pathlib import Path
import json, subprocess, tempfile, textwrap
from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).resolve().parent
OUT = BASE / "media" / "vaultix_growth"
W, H = 720, 1280
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
CARDS = [
    ("listing", "vaultix_01.mp4", "BUYING A USED CAR?", "Check the listing before you drive.", "COPY THIS AI PROMPT", "Review this listing. Separate seller claims, missing evidence and questions I should ask.", "EXAMPLE CHECKLIST", ["Title and VIN", "Service records", "Independent inspection"]),
    ("quote", "vaultix_02.mp4", "REPAIR QUOTE CONFUSING?", "Turn it into questions, not guesses.", "COPY THIS AI PROMPT", "Explain these repair quote items. Flag unclear labor, parts and warranty. Don't invent prices.", "EXAMPLE CHECKLIST", ["Parts and labor", "Diagnostic evidence", "Written warranty"]),
    ("compare", "vaultix_03.mp4", "TWO CARS. ONE BUDGET.", "Compare facts before deciding.", "COPY THIS AI PROMPT", "Compare these two listings using only documented facts. Flag unknowns and inspection priorities.", "EXAMPLE CHECKLIST", ["Known costs", "Missing history", "What to inspect"])
]

def font(size, bold=False):
    return ImageFont.truetype(BOLD if bold else FONT, size)

def wrapped(draw, content, y, size, color, bold=False, max_width=555):
    f = font(size, bold)
    line = ""
    lines = []
    for word in content.split():
        attempt = (line + " " + word).strip()
        if draw.textlength(attempt, font=f) > max_width:
            if not line:
                raise ValueError("Text overflow: " + word)
            lines.append(line)
            line = word
        else:
            line = attempt
    if line:
        lines.append(line)
    for item in lines:
        if draw.textlength(item, font=f) > max_width:
            raise ValueError("Text exceeds safe zone")
        draw.text((60,y), item, font=f, fill=color)
        y += size + 12
    return y

def overlay(card, page, out):
    slug, _, headline, sub, prompt_title, prompt, sample_title, checks = card
    im = Image.new("RGBA", (W,H), (0,0,0,0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((34,240,656,986), radius=32, fill=(11,17,26,239), outline=(90,180,164,255), width=2)
    d.text((60,278), "VAULTIX  /  FREE AI", font=font(24,True), fill=(110,235,204,255))
    d.rounded_rectangle((60,330,570,336),radius=3,fill=(48,60,71,255))
    d.rounded_rectangle((60,330,60+170*(page+1),336),radius=3,fill=(110,235,204,255))
    white=(249,250,252,255); muted=(200,214,225,255)
    if page == 0:
        y=wrapped(d,headline,405,57,white,True)
        y=wrapped(d,sub,y+35,35,muted)
    elif page == 1:
        y=wrapped(d,prompt_title,390,32,(110,235,204,255),True)
        y=wrapped(d,prompt,y+24,37,white)
    else:
        y=wrapped(d,sample_title,390,32,(110,235,204,255),True)
        for check in checks:
            y=wrapped(d,"- "+check,y+18,35,white)
        y=wrapped(d,"AI cannot inspect a car.",y+27,24,muted)
    if y>825:
        raise ValueError("Text overlaps CTA")
    d.line((60,849,600,849),fill=(70,85,92,255),width=2)
    d.text((60,878),"FREE FULL KIT ON TELEGRAM",font=font(25,True),fill=muted)
    d.text((60,917),"@AIFREEDROP",font=font(36,True),fill=(110,235,204,255))
    im.save(out)

def run(args):
    subprocess.run(args,check=True,stdout=subprocess.DEVNULL)

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for card in CARDS:
        slug, src, *_=card
        source=BASE/"media"/"vaultix_series"/src
        with tempfile.TemporaryDirectory() as td:
            tmp=Path(td)
            for p in range(3):
                overlay(card,p,tmp/f"overlay{p}.png")
            # Three pages on unique moving background; no borrowed audio.
            filters="[0:v]scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,setsar=1,fps=24,eq=brightness=-0.17[v];[v][1:v]overlay=enable='between(t,0,3.49)'[a];[a][2:v]overlay=enable='between(t,3.5,7.49)'[b];[b][3:v]overlay=enable='gte(t,7.5)'[out]"
            out=OUT/f"{slug}.mp4"
            run(["ffmpeg","-hide_banner","-loglevel","error","-y","-stream_loop","-1","-i",str(source),"-i",str(tmp/"overlay0.png"),"-i",str(tmp/"overlay1.png"),"-i",str(tmp/"overlay2.png"),"-filter_complex",filters,"-map","[out]","-an","-t","12","-c:v","libx264","-pix_fmt","yuv420p","-preset","fast","-crf","24","-movflags","+faststart",str(out)])
            p=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_streams","-show_format","-of","json",str(out)]))
            v=p["streams"][0]
            assert (v["width"],v["height"])==(720,1280)
            assert 11.9<=float(p["format"]["duration"])<=12.1
            assert 50_000<out.stat().st_size<15_000_000
            print("QA PASS", slug, out.stat().st_size, "720x1280",p["format"]["duration"])
            if slug=="listing":
                run(["ffmpeg","-hide_banner","-loglevel","error","-y","-ss","5","-i",str(out),"-frames:v","1",str(OUT/"listing_preview.jpg")])

if __name__=="__main__":
    main()
