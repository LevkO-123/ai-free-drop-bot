"""No false directory successes, no duplicate forms, no unrelated submissions."""
import json
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import submit_public_forms as forms


class Response:
    status = 200
    def __init__(self, content, url):
        self.content, self.url = content, url
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass
    def read(self, max_bytes):
        return self.content[:max_bytes]
    def geturl(self):
        return self.url


class FakeOpener:
    def __init__(self, value, redirect=None):
        self.value = value
        self.redirect = redirect
        self.calls = []
    def open(self, req, timeout):
        self.calls.append(req)
        if req.get_method() == "GET":
            return Response(b"<html><form></form></html>", req.full_url)
        return Response(self.value, self.redirect or req.full_url)


class PublicFormTests(unittest.TestCase):
    def test_two_auth_free_directory_only(self):
        self.assertEqual([x["key"] for x in forms.SITES], ["TGMetrix", "TeleSeeker"])
        for site in forms.SITES:
            fake = FakeOpener(b'{"ok":true}')
            status = forms.submit(site, opener=fake)
            self.assertEqual(status, "accepted")
            self.assertEqual(len(fake.calls), 2)
            self.assertEqual(fake.calls[1].get_method(), "POST")
            self.assertEqual(fake.calls[1].full_url, site["action"])
            self.assertIn("AIFREEDROP", fake.calls[1].data.decode("utf-8"))

    def test_regular_page_is_not_claimed_as_success(self):
        fake = FakeOpener(b"<html><h1>Submit your channel</h1><form></form></html>")
        self.assertEqual(forms.submit(forms.SITES[0], opener=fake), "unconfirmed")

    def test_wrong_domain_redirect_rejected(self):
        fake = FakeOpener(b'{"ok":true}', redirect="https://external.example/pay")
        with self.assertRaises(RuntimeError):
            forms.submit(forms.SITES[0], opener=fake)

    def test_mark_attempted_site_to_avoid_repeated_submission(self):
        with tempfile.TemporaryDirectory() as d:
            target = pathlib.Path(d) / "result.json"
            with patch.object(forms, "RESULTS", target), \
                 patch.object(forms, "submit", return_value="unconfirmed") as submitted:
                forms.main()
                forms.main()
                self.assertEqual(submitted.call_count, 2)
                result = json.loads(target.read_text())
                self.assertEqual(set(result), {"TeleSeeker", "TGMetrix"})


if __name__ == "__main__":
    unittest.main()
