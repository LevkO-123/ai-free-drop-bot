"""Read-only probe for freely licensed Pexels stock footage quality variants.

No downloads, no API token, no alterations to TikTok.
Sources confirmed from official Pexels free-download redirects.
"""
from __future__ import annotations
import urllib.request, urllib.error

CLIPS = {
 "beverly_vertical": [
  "https://videos.pexels.com/video-files/37315187/15805297_720_1280_60fps.mp4",
  "https://videos.pexels.com/video-files/37315187/15805297_1080_1920_60fps.mp4",
  "https://videos.pexels.com/video-files/37315187/15805297_2160_3840_60fps.mp4",
 ],
 "dubai_cars": [
  "https://videos.pexels.com/video-files/8747374/8747374-hd_1280_720_30fps.mp4",
  "https://videos.pexels.com/video-files/8747374/8747374-hd_1920_1080_30fps.mp4",
  "https://videos.pexels.com/video-files/8747374/8747374-uhd_3840_2160_30fps.mp4",
 ],
 "urban": [
  "https://videos.pexels.com/video-files/30787543/13168478_1280_720_25fps.mp4",
  "https://videos.pexels.com/video-files/30787543/13168478_1920_1080_25fps.mp4",
  "https://videos.pexels.com/video-files/30787543/13168478_3840_2160_25fps.mp4",
 ],
}
def run():
  for k, urls in CLIPS.items():
    for url in urls:
      try:
        request=urllib.request.Request(url,method="HEAD",headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(request,timeout=9) as resp:
          print(k,resp.status,resp.headers.get("Content-Length"),url)
      except urllib.error.HTTPError as e:
        print(k,"HTTP",e.code,url)
      except Exception as e:
        print(k,type(e).__name__,url)
if __name__=="__main__":
  run()
