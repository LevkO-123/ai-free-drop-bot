"""Render original educational TikTok shorts from our licensed car edits.
No AI-generation claims, no new downloads, no paid APIs. Render only; no uploads.
"""
from pathlib import Path
from io import BytesIO
import subprocess
import tempfile
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

BASE = Path(__file__).resolve().parent
OUT = BASE / "media" / "vaultix_growth"
W, H = 720, 1280
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
CARDS = [
    ("listing", "vaultix_01.mp4", "BUYING A USED CAR?", "Check the listing before you drive.", "COPY THIS AI PROMPT", "Review this listing. Separate seller claims, missing evidence and questions I should ask.", "EXAMPLE CHECKLIST", ["Title and VIN", "Service records", "Independent inspection"]),
    ("quote", "vaultix_02.mp4", "REPAIR QUOTE CONFUSING?", "Turn it into questions, not guesses.", "COPY THIS AI PROMPT", "Explain these repair quote items. Flag unclear labor, parts and warranty. Don't invent prices.", "EXAMPLE CHECKLIST", ["Parts and labor", "Diagnostic evidence", "Written warranty"]),
    ("compare", "vaultix_03.mp4", "TWO CARS. ONE BUDGET.", "Compare facts before deciding.", "COPY THIS AI PROMPT", "Compare these two listings using only documented facts. Flag unknowns and inspection priorities.", "EXAMPLE CHECKLIST", ["Known costs", "Missing history", "What to inspect"]),
    ("drive-away-price", "vaultix_04.mp4", "THE CHEAPER CAR COSTS MORE", "A two-offer example.", "WRITTEN PRICE EXAMPLE", "A: $13,950 + $1,450\nTotal: $15,400\nB: $14,100 + $950\nTotal: $15,050", "BEFORE YOU COMPARE", ["Ask for the full price", "Separate optional extras", "Offer B is $350 lower"]),
    ("seller-screen", "vaultix_06.mp4", "BEFORE YOU DRIVE AN HOUR", "Send this one message.", "COPY THIS TO THE SELLER", "Could you share the VIN and service records? Are you open to an independent inspection before purchase?", "COMPARE THE REPLIES", ["VIN provided?", "Records available?", "Inspection welcome?"]),
    ("service-records", "vaultix_08.mp4", "RECENT SERVICE? ASK FOR PROOF", "One claim. Three checks.", "WHEN THE AD SAYS SERVICED", "Ask for the invoice. Match its date, mileage and listed work to the seller's claim.", "CHECK THE INVOICE", ["Work actually performed", "Mileage and date", "Any follow-up noted?"]),
]
SCORED_SHORTS = {"drive-away-price", "seller-screen", "service-records"}

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
    d.text((60,278), "VAULTIX  /  CAR BUYING", font=font(24,True), fill=(110,235,204,255))
    d.rounded_rectangle((60,330,570,336),radius=3,fill=(48,60,71,255))
    d.rounded_rectangle((60,330,60+170*(page+1),336),radius=3,fill=(110,235,204,255))
    white=(249,250,252,255); muted=(200,214,225,255)
    if page == 0:
        y=wrapped(d,headline,405,57,white,True)
        y=wrapped(d,sub,y+35,35,muted)
    elif page == 1:
        y=wrapped(d,prompt_title,390,32,(110,235,204,255),True)
        y += 24
        for paragraph in prompt.splitlines():
            y = wrapped(d,paragraph,y,37,white)
    else:
        y=wrapped(d,sample_title,390,32,(110,235,204,255),True)
        for check in checks:
            y=wrapped(d,"- "+check,y+18,35,white)
        takeaway = "Example for comparison." if slug == "drive-away-price" else "Verify before you buy."
        if slug not in SCORED_SHORTS:
            takeaway = "AI cannot inspect a car."
        y=wrapped(d,takeaway,y+27,24,muted)
    if y>825:
        raise ValueError("Text overlaps CTA")
    d.line((60,849,600,849),fill=(70,85,92,255),width=2)
    d.text((60,878),"FREE FULL KIT ON TELEGRAM",font=font(25,True),fill=muted)
    d.text((60,917),"@AIFREEDROP",font=font(36,True),fill=(110,235,204,255))
    im.save(out)

def run(args):
    subprocess.run(args,check=True,stdout=subprocess.DEVNULL,timeout=45)

def verified_preview(video, at, page):
    frame = subprocess.check_output(
        [FFMPEG, "-hide_banner", "-loglevel", "error", "-i", str(video),
        "-ss", str(at), "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"],
        timeout=12,
    )
    with Image.open(BytesIO(frame)) as decoded:
        picture = decoded.convert("RGB")
    # The progress bar grows 170 pixels per page. Check distinct positions so
    # that a missing page or a frozen overlay both fail the render.
    for current, x in enumerate((145, 315, 485)):
        red, green, blue = picture.getpixel((x, 332))
        bright_teal = green > 175 and blue > 120 and green > red + 60
        if bright_teal != (current <= page):
            raise ValueError(
                f"{video.name}: wrong lesson progress at {at}s, x={x}: "
                f"RGB={red, green, blue}, expected teal={current <= page}"
            )
    return picture

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for card in CARDS:
        slug, src, *_=card
        out=OUT/f"{slug}.mp4"
        if slug not in SCORED_SHORTS and out.is_file():
            continue
        source=BASE/"media"/"vaultix_series"/src
        with tempfile.TemporaryDirectory() as td:
            tmp=Path(td)
            for p in range(3):
                overlay(card,p,tmp/f"overlay{p}.png")
            # Reset each lesson section to zero before adding its static card.
            # Frame boundaries at 24 fps keep the three cards at fixed durations.
            filters = (
                "[0:v]setsar=1,fps=24,eq=brightness=-0.17,split=3[v0][v1][v2];"
                "[v0]trim=end_frame=84,setpts=PTS-STARTPTS[s0];"
                "[v1]trim=start_frame=84:end_frame=180,setpts=PTS-STARTPTS[s1];"
                "[v2]trim=start_frame=180:end_frame=288,setpts=PTS-STARTPTS[s2];"
                "[s0][1:v]overlay[card0];[s1][2:v]overlay[card1];"
                "[s2][3:v]overlay[card2];"
                "[card0][card1][card2]concat=n=3:v=1:a=0[out]"
            )
            overlays = []
            for page in range(3):
                overlays.extend(["-i", str(tmp / f"overlay{page}.png")])
            audio = (
                ["-map", "0:a:0", "-af", "volume=0.55,afade=t=out:st=11:d=1",
                 "-c:a", "aac", "-b:a", "96k"] if slug in SCORED_SHORTS else ["-an"]
            )
            run([
                FFMPEG, "-hide_banner", "-loglevel", "error", "-y",
                "-stream_loop", "-1", "-i", str(source),
                *overlays,
                "-filter_complex_threads", "1", "-filter_complex", filters,
                "-map", "[out]", *audio, "-t", "12", "-c:v", "libx264",
                "-pix_fmt", "yuv420p", "-threads", "2", "-preset", "veryfast",
                "-crf", "24", "-movflags", "+faststart", str(out),
            ])
            reader=imageio_ffmpeg.read_frames(str(out))
            try:
                meta=next(reader)
                assert meta["size"]==(720,1280)
                assert 11.9<=float(meta["duration"])<=12.1
                if slug in SCORED_SHORTS:
                    assert meta.get("audio_codec") == "aac", "Original soundtrack was not encoded"
                assert len(next(reader))==720*1280*3
            finally:
                reader.close()
            assert 50_000<out.stat().st_size<15_000_000
            print("QA PASS", slug, out.stat().st_size, "720x1280",meta["duration"])
            if slug in SCORED_SHORTS:
                for page, at in enumerate((1, 5, 9)):
                    picture = verified_preview(out,at,page)
                    if page == 1:
                        picture.save(OUT/f"{slug}_preview.jpg", quality=90)
            elif slug == "listing":
                run([FFMPEG,"-hide_banner","-loglevel","error","-y","-ss","5","-i",str(out),"-frames:v","1",str(OUT/f"{slug}_preview.jpg")])

if __name__=="__main__":
    main()
