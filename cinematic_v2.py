"""Real cinematic VAULTIX TikTok using licensed moving Pexels car footage.

Clip attribution (optional under Pexels license):
https://www.pexels.com/video/luxury-cars-on-palm-lined-beverly-hills-street-37315187/
https://www.pexels.com/video/luxury-cars-passing-by-8747374/
https://www.pexels.com/video/luxury-car-driving-through-busy-urban-streets-30787543/
Sources are downloaded only temporarily, not committed.
"""
import math, random, shutil, subprocess, tempfile, urllib.request, wave
from array import array
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT=Path(__file__).resolve().parent/"media/vaultix_cinematic_v2.mp4"
SOURCES={
"street":"https://videos.pexels.com/video-files/37315187/15805297_2160_3840_60fps.mp4",
"cars":"https://videos.pexels.com/video-files/8747374/8747374-hd_1920_1080_30fps.mp4",
"drive":"https://videos.pexels.com/video-files/30787543/13168478_3840_2160_25fps.mp4",
}
SHOTS=[
("street",0.2,1.7,"DON'T BUY","THAT CAR YET."),
("cars",0.5,1.6,"AI CAN'T","INSPECT IT."),
("drive",0.2,1.8,"BUT IT CAN","PREPARE YOU."),
("street",3.0,1.8,"ASK FOR A","CHECKLIST."),
("cars",3.2,1.7,"RED FLAGS.","SELLER QUESTIONS."),
("drive",3.8,1.8,"THEN GET A","REAL INSPECTION."),
("street",6.5,2.7,"FREE AI PROMPTS","@AIFREEDROP"),
]
DURATION=sum(x[2] for x in SHOTS)
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def ffbin():
    x=shutil.which("ffmpeg")
    if x:return x
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()

def original_beat(path):
    rate=16000
    rng=random.Random(19)
    audio=array("h")
    interval=60/110
    for i in range(int(DURATION*rate)):
        t=i/rate
        p=t%interval
        kick=math.sin(2*math.pi*(56+92*math.exp(-22*p))*p)*math.exp(-18*p)*.60 if p<.17 else 0
        hp=t%(interval/2)
        hat=(rng.random()*2-1)*math.exp(-115*hp)*.035 if hp<.06 else 0
        sub=.10*math.sin(2*math.pi*55*t)
        envelope=min(1,t*3,(DURATION-t)*3)
        v=max(-1,min(1,(kick+hat+sub)*.55*envelope))
        audio.append(int(32767*v))
    with wave.open(str(path),"wb") as out:
        out.setnchannels(1);out.setsampwidth(2);out.setframerate(rate)
        out.writeframes(audio.tobytes())


def make_overlay(index,first,second,file):
    image=Image.new("RGBA",(720,1280),(0,0,0,0))
    d=ImageDraw.Draw(image)
    fontpath=FONT if Path(FONT).exists() else "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"
    def line(text,y,size,color):
        f=ImageFont.truetype(fontpath,size)
        while d.textbbox((0,0),text,font=f)[2]>630 and size>20:
            size-=2;f=ImageFont.truetype(fontpath,size)
        width=d.textbbox((0,0),text,font=f)[2]
        x=(720-width)//2
        d.text((x+3,y+4),text,font=f,fill=(0,0,0,230))
        d.text((x,y),text,font=f,fill=color)
    d.rounded_rectangle((18,276,702,620),radius=22,fill=(0,0,0,130))
    d.rounded_rectangle((43,65,223,112),radius=10,fill=(0,0,0,130))
    f=ImageFont.truetype(fontpath,24)
    d.text((62,72),"VAULTIX",font=f,fill=(245,240,230,240))
    d.rectangle((44,125,115,130),fill=(225,183,108,240))
    line(first,372,68,(234,190,110,255) if index in (2,4,6) else (255,255,255,255))
    line(second,464,53,(255,255,255,255))
    if index==6:
        d.rounded_rectangle((40,870,680,960),radius=14,fill=(0,0,0,205))
        line("TELEGRAM: @AIFREEDROP",889,35,(234,190,110,255))
    image.save(file)

def main():
    ff=ffbin()
    with tempfile.TemporaryDirectory() as tmp:
        scratch=Path(tmp)
        fetched={}
        for key,url in SOURCES.items():
            target=scratch/(key+".mp4")
            req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"})
            with urllib.request.urlopen(req,timeout=40) as response,target.open("wb") as dst:
                n=0
                while data:=response.read(1024*1024):
                    n+=len(data)
                    if n>65_000_000:raise RuntimeError("Footage exceeds capped download")
                    dst.write(data)
            if n<100_000:raise RuntimeError("Empty footage")
            fetched[key]=target
            print("Footage",key,n,flush=True)
        segments=[]
        for i,(key,seek,duration,line1,line2) in enumerate(SHOTS):
            video=scratch/(f"shot{i}.mp4")
            overlay=scratch/(f"overlay{i}.png")
            make_overlay(i,line1,line2,overlay)
            vf=(
              "[0:v]scale=720:1280:force_original_aspect_ratio=increase,"
              "crop=720:1280,eq=contrast=1.12:saturation=0.88:brightness=-0.04,"
              "vignette=PI/7[background];"
              "[background][1:v]overlay=x=0:y=0:shortest=1:format=auto[v]"
            )
            args=[ff,"-hide_banner","-loglevel","error","-y",
                  "-ss",str(seek),"-i",str(fetched[key]),
                  "-loop","1","-framerate","30","-i",str(overlay),
                  "-filter_complex",vf,"-map","[v]","-t",str(duration),
                  "-an","-r","30","-c:v","libx264","-preset","ultrafast",
                  "-crf","23","-pix_fmt","yuv420p",str(video)]
            subprocess.run(args,check=True)
            segments.append(video)
            print("Rendered shot",i+1,flush=True)
        playlist=scratch/"list.txt"
        playlist.write_text("".join("file '"+str(x)+"'\n" for x in segments))
        joined=scratch/"joined.mp4"
        subprocess.run([ff,"-hide_banner","-loglevel","error","-y","-f","concat",
            "-safe","0","-i",str(playlist),"-c","copy",str(joined)],check=True)
        audio=scratch/"beat.wav"
        original_beat(audio)
        OUT.parent.mkdir(parents=True,exist_ok=True)
        subprocess.run([ff,"-hide_banner","-loglevel","error","-y",
            "-i",str(joined),"-i",str(audio),"-c:v","copy",
            "-c:a","aac","-b:a","96k","-shortest",
            "-movflags","+faststart",str(OUT)],check=True)
    if OUT.stat().st_size<800_000 or OUT.stat().st_size>30_000_000:
        raise RuntimeError("Unexpected output size")
    print("Cinematic TikTok complete",OUT,OUT.stat().st_size,flush=True)

if __name__=="__main__": main()
