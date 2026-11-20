"""Generate the original VAULTIX x AI FREE DROP vertical car-purchase prompt video.
No external media, paid generation APIs, stock footage or copyrighted music.
"""
from __future__ import annotations
import math, os, random, shutil, subprocess, sys, wave
from array import array
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W,H,FPS,DURATION=720,1280,24,16
HERE=Path(__file__).resolve().parent
OUTPUT=HERE / "media" / "used_car_ai_prompt.mp4"
FONT_PATH=next((x for x in (
    "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
) if Path(x).is_file()),None)
if not FONT_PATH:
    raise RuntimeError("No local free font found")
FONT_CACHE={}

def font(size):
    size=int(size)
    if size not in FONT_CACHE:
        FONT_CACHE[size]=ImageFont.truetype(FONT_PATH,size)
    return FONT_CACHE[size]

def txt(d,content,x,y,size,color="#f5fafc",maximum=570):
    while size>21 and d.textbbox((0,0),content,font=font(size))[2]>maximum:
        size-=1
    d.text((x,y),content,font=font(size),fill=color)

def backdrop():
    image=Image.new("RGB",(W,H))
    d=ImageDraw.Draw(image)
    for y in range(H):
        f=y/H
        d.line((0,y,W,y),fill=(int(7+7*f),int(17+7*f),int(25+9*f)))
    d.ellipse((-300,-130,510,720),fill="#0d242a")
    d.ellipse((365,100,1100,950),fill="#10252a")
    for i in range(12):
        x=70+i*67
        d.line((x,0,x-170,H),fill="#1d323a",width=1)
    return image

BASE=backdrop()
GREEN="#d7ff43"

def car(d,t,y=560):
    y=int(y+3*math.sin(t*3))
    d.ellipse((65,y+100,660,y+245),fill="#08141a")
    d.polygon([(125,y+148),(166,y+61),(264,y+11),(468,y+11),
               (556,y+61),(600,y+146),(623,y+176),(104,y+176)],fill="#1a3139")
    d.polygon([(196,y+68),(282,y+26),(455,y+26),(527,y+68),
               (552,y+110),(174,y+110)],fill="#09191d")
    d.line([(120,y+147),(151,y+88),(198,y+57),(541,y+57),
            (571,y+94),(608,y+146)],fill=GREEN,width=5)
    d.rounded_rectangle((112,y+143,619,y+193),radius=18,
                        fill="#19323b",outline=GREEN,width=3)
    d.polygon([(122,y+137),(234,y+135),(222,y+154),(112,y+153)],fill="#dbffe3")
    d.polygon([(499,y+135),(610,y+137),(623,y+153),(512,y+154)],fill="#dbffe3")
    d.rounded_rectangle((312,y+145,408,y+177),4,fill="#101a22",outline="#798d86",width=2)
    for x in (164,545):
        d.ellipse((x-7,y+186,x+31,y+225),fill="#0b141b",outline="#95a4a1",width=3)
    for x in (125,280,430,572):
        d.line((x,y+253,x+55,y+253),fill="#345152",width=3)

def frame(t):
    image=BASE.copy()
    d=ImageDraw.Draw(image)
    d.rounded_rectangle((55,74,409,122),14,fill="#1a3138",outline="#354f59",width=2)
    txt(d,"AI FREE DROP / VAULTIX",75,83,23,GREEN)
    d.line((56,1130,663,1130),fill="#354e56",width=2)
    txt(d,"START WITH QUESTIONS. VERIFY WITH A MECHANIC.",57,1150,18,"#afbfca")
    d.rounded_rectangle((55,1197,666,1204),4,fill="#344450")
    d.rounded_rectangle((55,1197,55+int(609*t/DURATION),1204),4,fill=GREEN)
    # Motion stripe changes over time
    x=(t*88)%820-155
    d.polygon(((x,165),(x+15,165),(x-210,1100),(x-224,1100)),fill="#132a2b")
    if t<4.0:
        txt(d,"BUYING A",76,233,86)
        txt(d,"USED CAR?",76,341,94,GREEN)
        car(d,t,576)
        txt(d,"ONE FREE AI PROMPT",76,966,47)
        txt(d,"COULD IMPROVE YOUR CHECKLIST",76,1033,30,"#b0bfcb")
    elif t<6.5:
        txt(d,"DON'T ASK AI:",76,286,67)
        txt(d,'"IS THIS CAR GOOD?"',76,384,49,"#b7c3cc")
        car(d,t,562)
        d.rounded_rectangle((64,938,651,1026),18,fill=GREEN)
        txt(d,"ASK FOR A CHECKLIST.",84,957,49,"#0c1c22")
    elif t<12.3:
        txt(d,"COPY THIS PROMPT",72,219,60,GREEN)
        d.rounded_rectangle((58,324,651,968),24,fill="#142732",outline="#3c6066",width=3)
        d.rounded_rectangle((79,348,328,394),10,fill="#29423d")
        txt(d,"CHATGPT / AI CHAT",96,356,23,GREEN)
        lines=[
            ("Build a pre-purchase",49),("checklist for a",50),
            ("[YEAR / MODEL /",47),("MILEAGE].",55),("",10),
            ("Include warning signs,",41),("questions for the seller,",39),
            ("and what a mechanic",43),("must inspect.",45),("",10),
            ("Do NOT invent facts.",43),
        ]
        y=436
        for word,size in lines:
            if not word:
                y+=14;continue
            txt(d,word,92,y,size,GREEN if word.startswith("Do NOT") else "#f5fafc",510)
            y+=55 if size>40 else 48
        txt(d,"SAVE BEFORE YOUR NEXT PURCHASE.",66,1018,30,"#b1beca")
    else:
        car(d,t,260)
        txt(d,"SAVE THIS",74,706,95,GREEN)
        txt(d,"FREE PROMPT.",74,814,77)
        txt(d,"MORE FREE AI TOOLS + PROMPTS",74,930,32,"#b1bfca")
        d.rounded_rectangle((64,991,648,1090),20,fill=GREEN)
        txt(d,"TELEGRAM: @AIFREEDROP",84,1014,47,"#101c21",550)
    return image

def original_audio(file):
    rate=22050
    rng=random.Random(777)
    samples=array("h")
    for i in range(DURATION*rate):
        t=i/rate
        p=t%0.5
        kick=math.sin(2*math.pi*(55+100*math.exp(-22*p))*p)*math.exp(-21*p)*0.42 if p<0.17 else 0.0
        hat_p=t%0.25
        hat=(rng.random()*2-1)*math.exp(-100*hat_p)*0.05 if hat_p<0.03 else 0.0
        bass=0.07*math.sin(2*math.pi*55*t)*math.exp(-p*5)
        samples.append(int(max(-1,min(1,0.48*(kick+hat+bass)))*32767))
    with wave.open(str(file),"wb") as obj:
        obj.setnchannels(1);obj.setsampwidth(2);obj.setframerate(rate)
        obj.writeframes(samples.tobytes())

def generate():
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg must be installed")
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    audio=OUTPUT.with_suffix(".wav")
    original_audio(audio)
    cmd=["ffmpeg","-hide_banner","-loglevel","error","-y",
         "-f","rawvideo","-pixel_format","rgb24","-video_size",f"{W}x{H}",
         "-framerate",str(FPS),"-i","pipe:0","-i",str(audio),
         "-c:v","libx264","-pix_fmt","yuv420p","-preset","ultrafast",
         "-crf","25","-movflags","+faststart","-c:a","aac","-b:a","96k",
         "-t",str(DURATION),str(OUTPUT)]
    p=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    try:
        for i in range(FPS*DURATION):
            p.stdin.write(frame(i/FPS).tobytes())
        p.stdin.close()
        if p.wait()!=0:raise RuntimeError("video encode failed")
    finally:
        if p.poll() is None:p.kill()
        audio.unlink(missing_ok=True)
    if OUTPUT.stat().st_size > 15_000_000:
        raise RuntimeError("Unexpected file growth")
    print("Original TikTok video ready:",OUTPUT,OUTPUT.stat().st_size,"bytes")

if __name__=="__main__":
    generate()
