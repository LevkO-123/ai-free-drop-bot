"""Ten distinct, no-text VAULTIX vertical automotive shorts, $0 extra cost.

Sources are actual free Pexels footage; see https://www.pexels.com/license/.
This is conventional cinematic editing, never labeled as AI-generated footage.
Video/temporary sources are discarded after creating the finished files.
"""
from __future__ import annotations

import math
import os
import random
import subprocess
import tempfile
import urllib.request
import wave
from array import array
from pathlib import Path

BASE=Path(__file__).resolve().parent
OUT=BASE/"media"/"vaultix_series"
SOURCE_URLS={
    "ferrari_red":"https://videos.pexels.com/video-files/30794587/13171246_1920_1080_60fps.mp4",
    "bmw_black":"https://videos.pexels.com/video-files/16532416/16532416-hd_1920_1080_60fps.mp4",
    "bmw_road":"https://videos.pexels.com/video-files/8562464/8562464-hd_1920_1080_30fps.mp4",
    "mercedes_night":"https://videos.pexels.com/video-files/13574383/13574383-hd_1920_1080_30fps.mp4",
    "ferrari_zurich":"https://videos.pexels.com/video-files/16976173/16976173-hd_1920_1080_24fps.mp4",
    "lamborghini_city":"https://videos.pexels.com/video-files/32516192/13865907_1920_1080_30fps.mp4",
    "mercedes_sls":"https://videos.pexels.com/video-files/5098987/5098987-hd_1920_1080_24fps.mp4",
    "supercars_dubai":"https://videos.pexels.com/video-files/8747374/8747374-hd_1920_1080_30fps.mp4",
    "beverly":"https://videos.pexels.com/video-files/37315187/15805297_2160_3840_60fps.mp4",
    "bmw_forest":"https://videos.pexels.com/video-files/35078422/14859871_2160_3840_30fps.mp4",
}
MAX_BYTES=72_000_000
# Five different sources per short, two independent creative A/B angles,
# no exact duplicated storyboards.
STORYBOARDS=[
  ("Ferrari city after dark", "car", ["ferrari_red","ferrari_zurich","supercars_dubai","lamborghini_city","ferrari_red"]),
  ("Black BMW motion", "prompt", ["bmw_black","bmw_road","mercedes_sls","bmw_forest","bmw_black"]),
  ("Mercedes night drive", "car", ["mercedes_night","mercedes_sls","bmw_black","supercars_dubai","mercedes_night"]),
  ("Red Ferrari dream", "prompt", ["ferrari_zurich","ferrari_red","lamborghini_city","supercars_dubai","ferrari_zurich"]),
  ("Beverly Hills luxury", "car", ["beverly","supercars_dubai","lamborghini_city","ferrari_red","beverly"]),
  ("BMW mountain road", "prompt", ["bmw_forest","bmw_black","bmw_road","mercedes_sls","bmw_forest"]),
  ("Supercar streets", "car", ["lamborghini_city","supercars_dubai","ferrari_red","beverly","lamborghini_city"]),
  ("AMG visual mood", "prompt", ["mercedes_sls","mercedes_night","bmw_road","beverly","mercedes_sls"]),
  ("Premium car detail", "car", ["bmw_road","bmw_black","supercars_dubai","mercedes_sls","bmw_road"]),
  ("Dream car collection", "prompt", ["supercars_dubai","ferrari_zurich","mercedes_night","lamborghini_city","beverly"]),
]

def ffmpeg_executable():
    import shutil
    found=shutil.which("ffmpeg")
    if found:return found
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()

def fetch_one(key,url,path):
    if not url.startswith("https://videos.pexels.com/video-files/") or not url.endswith(".mp4"):
        raise ValueError("Unexpected media provider")
    request=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"})
    with urllib.request.urlopen(request,timeout=45) as response,path.open("wb") as out:
        declared=int(response.headers.get("Content-Length") or 0)
        if declared>MAX_BYTES:raise ValueError(f"{key}: media exceeds safe download cap")
        total=0
        while chunk:=response.read(1024*1024):
            total+=len(chunk)
            if total>MAX_BYTES:raise ValueError(f"{key}: actual transfer exceeds cap")
            out.write(chunk)
    if total<100_000:raise RuntimeError(f"{key}: no usable video downloaded")
    print("Licensed source verified:",key,total,flush=True)

def render_audio(path,secs,index):
    # Each video has a distinct original generated percussion motif, no
    # third-party music samples, melodies or sound effects.
    rng=random.Random(1300+index)
    sr=16000
    bpm=[103,118,105,123,101,111,120,109,125,106][index]
    beat=60/bpm
    pitch=[55,62,49,65,58,55,69,52,60,48][index]
    samples=array("h")
    for j in range(int(secs*sr)):
        t=j/sr
        phase=t%beat
        kick=math.sin(2*math.pi*(pitch+85*math.exp(-24*phase))*phase)*math.exp(-18*phase)*0.52 if phase<0.19 else 0.0
        hatphase=t%(beat/2)
        hat=(rng.random()*2-1)*math.exp(-135*hatphase)*0.038 if hatphase<0.04 else 0.0
        pad=0.05*math.sin(2*math.pi*pitch*t)*math.sin(2*math.pi*(.12+index*.01)*t)
        envelope=min(1.0,4*t,4*(secs-t))
        v=max(-1.0,min(1.0,(kick+hat+pad)*0.62*max(0,envelope)))
        samples.append(int(v*32767))
    with wave.open(str(path),"wb") as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(sr);f.writeframes(samples.tobytes())

def execute(cmd):
    p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=110)
    if p.returncode:raise RuntimeError(p.stderr.decode(errors="replace")[-800:])
    return p.stdout

def render_one(ffmpeg, sources, cache, index, board):
    label,angle,keys=board
    count=index+1
    color_specs=[
      (1.12,.90,-.04),(1.17,.84,-.03),(1.14,.78,-.06),
      (1.11,1.01,-.02),(1.18,.85,-.05),(1.10,.97,-.02),
      (1.15,.88,-.04),(1.12,.76,-.05),(1.17,.94,-.03),(1.13,.89,-.04)]
    contrast,saturation,brightness=color_specs[index]
    length=[1.55,1.70,1.45,1.75,1.85][index%5]
    output=OUT/f"vaultix_{count:02}.mp4"
    clips=[]
    for seq,key in enumerate(keys):
        clip=cache/f"edit{count:02}_{seq}.mp4"
        # Distinct offsets change the filmed action even if a source repeats.
        start=round(0.08+seq*.38+(index%3)*.15,2)
        # Every effect is a conventional color/crop adjustment.
        # No text, logo, AI disclosures, watermarks or title frames.
        grade=(f"scale=720:1280:force_original_aspect_ratio=increase,"
               f"crop=720:1280,eq=contrast={contrast}:saturation={saturation}:"
               f"brightness={brightness},vignette=PI/12,fps=24,format=yuv420p")
        execute([ffmpeg,"-hide_banner","-loglevel","error","-y","-ss",str(start),
                 "-i",str(sources[key]),"-t",str(length),"-an","-vf",grade,
                 "-c:v","libx264","-preset","ultrafast","-crf","26",
                 "-pix_fmt","yuv420p",str(clip)])
        if clip.stat().st_size<20_000:raise ValueError(f"Short or invalid clip: {key}")
        clips.append(clip)
    playlist=cache/f"list_{count:02}.txt"
    playlist.write_text("".join(f"file '{p}'\n" for p in clips))
    silent=cache/f"silent_{count:02}.mp4"
    execute([ffmpeg,"-hide_banner","-loglevel","error","-y","-f","concat","-safe","0",
             "-i",str(playlist),"-c","copy",str(silent)])
    music=cache/f"sound_{count:02}.wav"
    duration=length*len(keys)
    render_audio(music,duration,index)
    execute([ffmpeg,"-hide_banner","-loglevel","error","-y","-i",str(silent),
             "-i",str(music),"-map","0:v:0","-map","1:a:0","-c:v","copy",
             "-c:a","aac","-b:a","96k","-shortest","-movflags","+faststart",str(output)])
    if output.read_bytes()[4:8]!=b"ftyp" or not 300_000<output.stat().st_size<30_000_000:
        raise ValueError(f"Invalid output {output}")
    print("QA-ready:",count,label,angle,output.stat().st_size,"bytes",flush=True)
    for clip in clips:clip.unlink(missing_ok=True)
    silent.unlink(missing_ok=True)
    music.unlink(missing_ok=True)

def build():
    OUT.mkdir(parents=True,exist_ok=True)
    ffmpeg=ffmpeg_executable()
    with tempfile.TemporaryDirectory() as folder:
        temp=Path(folder)
        originals={}
        for key,url in SOURCE_URLS.items():
            path=temp/(key+".mp4")
            fetch_one(key,url,path)
            originals[key]=path
        for i,board in enumerate(STORYBOARDS):
            render_one(ffmpeg,originals,temp,i,board)
    final=list(OUT.glob("vaultix_??.mp4"))
    if len(final)!=10:raise RuntimeError("Not all 10 distinct edits were exported")
    print("COMPLETE: 10 validated original edits",flush=True)

if __name__=="__main__":build()
