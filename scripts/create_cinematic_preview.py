"""Create a review contact sheet from the actual final VAULTIX mp4, not mock frames."""
from __future__ import annotations
import io, shutil, subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
VIDEO=ROOT/"media/vaultix_cinematic_v2.mp4"
OUT=ROOT/"media/vaultix_v2_contact.jpg"
TIMES=(.7,2.35,4.2,5.9,7.8,9.6,11.1,12.6)
def main():
    ff=shutil.which("ffmpeg")
    if not ff:
        import imageio_ffmpeg
        ff=imageio_ffmpeg.get_ffmpeg_exe()
    width,height=240,426
    sheet=Image.new("RGB",(width*4,height*2),(12,12,16))
    d=ImageDraw.Draw(sheet)
    for n,t in enumerate(TIMES):
        args=[ff,"-hide_banner","-loglevel","error","-ss",str(t),"-i",str(VIDEO),
              "-frames:v","1","-vf",f"scale={width}:{height}","-f","image2pipe","-vcodec","mjpeg","pipe:1"]
        data=subprocess.check_output(args)
        img=Image.open(io.BytesIO(data)).convert("RGB")
        x,y=n%4*width,n//4*height
        sheet.paste(img,(x,y))
        d.rectangle((x+3,y+3,x+75,y+30),fill=(16,16,16))
        d.text((x+9,y+6),f"{t:.1f}s",fill=(230,230,230))
    OUT.parent.mkdir(parents=True,exist_ok=True)
    sheet.save(OUT,quality=72,optimize=True)
    print("Preview contact:",OUT,OUT.stat().st_size)
if __name__=="__main__":main()
