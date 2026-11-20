"""One-time TeleAdda free listing. No login, CAPTCHA bypass or retries."""
from __future__ import annotations
import datetime as dt, http.cookiejar, json, pathlib
import urllib.request, urllib.error, urllib.parse
from html.parser import HTMLParser

URL="https://www.teleadda.com/add"
OUT=pathlib.Path("data/teleadda_submission.json")
CHANNEL="https://t.me/AIFREEDROP"

class Form(HTMLParser):
 def __init__(self):
  super().__init__(); self.forms=[]; self.f=None; self.s=None; self.o=None
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=="form":
   self.f={"method":a.get("method","get").lower(),"action":urllib.parse.urljoin(URL,a.get("action","")),"fields":{},"options":{}}
   self.forms.append(self.f)
  if self.f is None:return
  if tag in ("input","textarea","select") and a.get("name"):
   name=a["name"];self.f["fields"][name]=a.get("value","")
   if tag=="select":self.s=name;self.f["options"][name]=[]
  if tag=="option" and self.s:self.o={"v":a.get("value",""),"t":""}
 def handle_data(self,s):
  if self.o is not None:self.o["t"]+=s
 def handle_endtag(self,tag):
  if tag=="option" and self.o is not None and self.s:self.f["options"][self.s].append(self.o);self.o=None
  if tag=="select":self.s=None
  if tag=="form":self.f=None

def choose(f,k,value):
 for o in f["options"].get(k,[]):
  if " ".join(o["t"].lower().split())==value and o["v"]:return o["v"]
 raise RuntimeError("Required public selector missing: "+k)

def submit():
 browser=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
 headers={"User-Agent":"Mozilla/5.0"}
 with browser.open(urllib.request.Request(URL,headers=headers),timeout=20) as r:html=r.read(450001)
 if len(html)>450000:raise ValueError("Form too large")
 parser=Form();parser.feed(html.decode("utf-8","replace"))
 forms=[f for f in parser.forms if f["method"]=="post" and "links" in f["fields"]]
 if len(forms)!=1:raise RuntimeError("No unambiguous listing form")
 f=forms[0]
 if urllib.parse.urlsplit(f["action"]).hostname!="www.teleadda.com":raise ValueError("Wrong destination")
 data=f["fields"].copy()
 data.update({"links":CHANNEL,"categoryId":choose(f,"categoryId","technology"),
              "languageId":choose(f,"languageId","english"),
              "countryId":"","website":"","contact":""})
 request=urllib.request.Request(f["action"],data=urllib.parse.urlencode(data).encode(),method="POST",
   headers={"User-Agent":"Mozilla/5.0","Content-Type":"application/x-www-form-urlencoded",
            "Referer":URL,"Origin":"https://www.teleadda.com"})
 with browser.open(request,timeout=25) as r:
  body=r.read(140001);status=r.status
 if len(body)>140000:raise ValueError("Response too long")
 response=body.decode("utf-8","replace").lower()
 accepted=status==200 and any(x in response for x in ('"ok":true','"success":true','successfully added','listing has been added'))
 return {"status":"accepted" if accepted else "unconfirmed","http":status}

def main():
 if OUT.exists():print("Not resubmitting previous attempt");return
 try:result=submit()
 except urllib.error.HTTPError as e:result={"status":"http_error","http":e.code}
 except Exception as e:result={"status":"unconfirmed_error","reason":type(e).__name__}
 result.update(channel=CHANNEL, checked_at=dt.datetime.now(dt.timezone.utc).isoformat())
 OUT.write_text(json.dumps(result,indent=2)+"\n")
 print("TeleAdda:",result["status"],"HTTP",result.get("http"))

if __name__=="__main__":main()
