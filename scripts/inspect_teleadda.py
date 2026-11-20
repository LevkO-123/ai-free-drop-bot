"""Read-only inspection of TeleAdda free public listing form.

Helps submit @AIFREEDROP once without guessing field names, evading
authentication or interacting with unrelated websites.
"""
from __future__ import annotations
from html.parser import HTMLParser
from urllib.request import Request, urlopen
from urllib.parse import urljoin

URL="https://www.teleadda.com/add"

class Forms(HTMLParser):
    def __init__(self):
        super().__init__()
        self.forms=[]
        self.current=None
        self.current_select=None
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if tag=="form":
            self.current={"action":urljoin(URL,a.get("action","")),"method":a.get("method","get"),"inputs":[]}
            self.forms.append(self.current)
        if self.current is not None and tag in ("input","textarea","select"):
            field={k:a.get(k) for k in ("name","type","value","required","id") if k in a}
            field["tag"]=tag
            if tag=="select":
                self.current_select=field
                field["options"]=[]
            self.current["inputs"].append(field)
        if tag=="option" and self.current_select is not None:
            self.current_select["options"].append(a.get("value", ""))
    def handle_endtag(self, tag):
        if tag=="form":self.current=None
        if tag=="select":self.current_select=None

def main():
    request=Request(URL,headers={"User-Agent":"Mozilla/5.0 (compatible; AIFREEDROP/1.0)"})
    with urlopen(request,timeout=15) as response:
        data=response.read(450_001)
        print("HTTP:",response.status,"Bytes:",len(data))
    if len(data)>450_000:raise ValueError("Form response exceeds limit")
    parser=Forms()
    parser.feed(data.decode("utf-8",errors="replace"))
    for f in parser.forms[:4]:
        print("FORM:",f)
    if not parser.forms:
        print("No standard form; stop without submitting")

if __name__=="__main__":main()
