"""Create a ten-video contact sheet from actual final VAULTIX MP4 frames."""
import io, subprocess
from pathlib import Path
from PIL import Image, ImageDraw
import imageio_ffmpeg

ROOT=Path(__file__).resolve().parent
FOLDER=ROOT/"media"/"vaultix_series"
OUT=FOLDER/"series_contact.jpg"
FF=imageio_ffmpeg.get_ffmpeg_exe()

def main():
    files=sorted(FOLDER.glob("vaultix_??.mp4"))
    if len(files)!=10:raise ValueError(f"Expected 10 videos; got {len(files)}")
    w,h=200,355
    sheet=Image.new("RGB",(w*5,h*2),(12,17,21))
    draw=ImageDraw.Draw(sheet)
    for i,p in enumerate(files):
        imgs=[]
        for second in (1.0,4.0,7.0):
            data=subprocess.check_output([FF,"-hide_banner","-loglevel","error","-ss",str(second),
                 "-i",str(p),"-frames:v","1","-vf",f"scale={w}:{h}",
                 "-f","image2pipe","-vcodec","mjpeg","pipe:1"])
            imgs.append(Image.open(io.BytesIO(data)).convert("RGB"))
        thumb=Image.new("RGB",(w,h))
        for j,img in enumerate(imgs):
            top=int(j*h/3);bottom=int((j+1)*h/3)
            thumb.paste(img.crop((0,top,w,bottom)),(0,top))
        x=i%5*w;y=i//5*h
        sheet.paste(thumb,(x,y))
        draw.rectangle((x+4,y+4,x+72,y+28),fill=(8,12,17))
        draw.text((x+11,y+8),f"V{(i+1):02}",fill="#f7f9f4")
    sheet.save(OUT,quality=77,optimize=True)
    print("Visual QA sheet generated:",OUT,OUT.stat().st_size)

if __name__=="__main__":main()
