"""Read only public directory submit forms to identify standard form methods.

No form is submitted. No login, CAPTCHA solving, bot detection bypass or scraping
of user data. Only form names, action URLs and method are printed for inspection.
"""
from html.parser import HTMLParser
from urllib.request import Request, urlopen

PAGES = ("https://telegramgroups.co/submit",)


class FormScanner(HTMLParser):
    def __init__(self):
        super().__init__()
        self.forms = []
        self.active = None

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "form":
            self.active = {"method": d.get("method", "get"), "action": d.get("action", ""),
                           "fields": [], "form_id": d.get("id", "")}
            self.forms.append(self.active)
        if self.active is not None and tag in ("input", "textarea", "select"):
            self.active["fields"].append({
                "tag": tag, "name": d.get("name", ""), "type": d.get("type", ""),
                "required": "required" in d,
            })

    def handle_endtag(self, tag):
        if tag == "form":
            self.active = None


def inspect():
    for url in PAGES:
        print("\nSITE", url)
        try:
            req = Request(url, headers={"User-Agent": "Mozilla/5.0 (AI-FREE-DROP 1.0)"})
            with urlopen(req, timeout=9) as response:
                body = response.read(850_001)
            if len(body) > 850_000:
                print("SKIP: exceeds 850KB inspection limit")
                continue
            scanner = FormScanner()
            scanner.feed(body.decode("utf-8", errors="replace"))
            if not scanner.forms:
                print("NO STANDARD FORMS: manual/JavaScript UI likely")
            for idx, form in enumerate(scanner.forms[:5]):
                print("FORM", idx + 1, form)
        except Exception as exc:
            print("UNAVAILABLE", type(exc).__name__)


if __name__ == "__main__":
    inspect()
