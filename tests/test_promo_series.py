"""Validate new VAULTIX series before burning GitHub Actions minutes."""
import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
import promo_series as p

class SeriesTests(unittest.TestCase):
 def test_exactly_ten_distinct_clips(self):
  self.assertEqual(len(p.STORYBOARDS),10)
  self.assertEqual(len({tuple(s[2]) for s in p.STORYBOARDS}),10)
  self.assertEqual(len({s[0] for s in p.STORYBOARDS}),10)
 def test_creative_ab_groups_are_balanced(self):
  self.assertEqual(sum(s[1]=="car" for s in p.STORYBOARDS),5)
  self.assertEqual(sum(s[1]=="prompt" for s in p.STORYBOARDS),5)
 def test_all_clips_from_licensed_pexels_and_are_used(self):
  self.assertGreaterEqual(len(p.SOURCE_URLS),10)
  for key,url in p.SOURCE_URLS.items():
   self.assertTrue(url.startswith("https://videos.pexels.com/video-files/"),key)
   self.assertTrue(url.endswith(".mp4"),key)
  self.assertTrue(set(k for b in p.STORYBOARDS for k in b[2])==set(p.SOURCE_URLS))
 def test_no_on_video_text_watermarks_or_brand_overlays(self):
  source=pathlib.Path(p.__file__).read_text(encoding="utf8")
  self.assertNotIn('"drawtext=',source)
  self.assertNotIn('"overlay=',source)
  self.assertNotIn('"drawbox=',source)
 def test_duration_and_size_bounds(self):
  self.assertLess(p.MAX_BYTES,75_000_000)
  for name,mode,keys in p.STORYBOARDS:
   self.assertEqual(len(keys),5)
   self.assertIn(mode,("car","prompt"))
   self.assertTrue(name)

if __name__=="__main__":unittest.main()
