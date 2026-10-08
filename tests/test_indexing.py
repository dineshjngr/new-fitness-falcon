"""Publishing contracts: canonical sitemap membership and import preservation."""
import json
import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from scripts.editorial import clean_article_html

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://thefitnessfalcon.com'

class IndexingTests(unittest.TestCase):
    def test_sitemap_includes_each_article_once_and_only_indexable_canonicals(self):
        urls = [n.text for n in ET.parse(ROOT / 'sitemap.xml').findall('.//{*}loc')]
        self.assertEqual(len(urls), len(set(urls)))
        posts = [json.loads(p.read_text()) for p in (ROOT / 'content/posts').glob('*.json')]
        for post in posts:
            self.assertIn(f'{BASE}/blogs/{post["slug"]}/', urls)
        for url in urls:
            self.assertTrue(url.startswith(BASE + '/'))
            path = ROOT / url.removeprefix(BASE + '/') / 'index.html'
            source = path.read_text()
            self.assertIn(f'rel="canonical" href="{url}"', source)
            robots = re.search(r'''<meta name=["']robots["'] content=["']([^"']+)["']''' , source)
            self.assertIsNotNone(robots)
            self.assertNotIn('noindex', robots[1])
            self.assertNotIn('/tag/', url)

    def test_section_sitemaps_partition_the_main_sitemap(self):
        main = {n.text for n in ET.parse(ROOT / 'sitemap.xml').findall('.//{*}loc')}
        sections = []
        for name in ('post-sitemap.xml', 'page-sitemap.xml', 'category-sitemap.xml'):
            sections.extend(n.text for n in ET.parse(ROOT / name).findall('.//{*}loc'))
        self.assertEqual(set(sections), main)
        self.assertEqual(len(sections), len(main))
        index = {n.text for n in ET.parse(ROOT / 'sitemap_index.xml').findall('.//{*}loc')}
        self.assertEqual(index, {BASE + '/' + n for n in ('post-sitemap.xml', 'page-sitemap.xml', 'category-sitemap.xml')})

    def test_tag_archives_are_crawlable_but_excluded_from_indexing(self):
        for path in (ROOT / 'tag').rglob('index.html'):
            source = path.read_text()
            self.assertIn('<meta name="robots" content="noindex, follow"', source)
            self.assertIn('href="/blogs/', source)
        self.assertNotIn('Disallow: /tag', (ROOT / 'robots.txt').read_text())

    def test_import_cleanup_preserves_evidence_tables_and_deep_links(self):
        source = '<div data-message-author-role="assistant"><h2 id="evidence">Evidence</h2><p>A &amp; B <a href="https://example.org/study">study</a>.</p><table><tr><th scope="col">Item</th><td colspan="2">Data</td></tr></table><img src="/assets/images/food.jpg" alt="Food"><script>privateEditorUI()</script></div>'
        result = clean_article_html(source)
        self.assertNotIn('data-message', result)
        self.assertNotIn('privateEditorUI', result)
        for expected in ('id="evidence"', 'A &amp; B', 'href="https://example.org/study"', 'scope="col"', 'colspan="2"', 'alt="Food"'):
            self.assertIn(expected, result)

    def test_article_metadata_does_not_claim_unverified_people(self):
        for path in (ROOT / 'content/posts').glob('*.json'):
            post = json.loads(path.read_text())
            self.assertIn(post['author'], ('Dinesh Jeengar', 'The Fitness Falcon'))
            source = (ROOT / 'blogs' / post['slug'] / 'index.html').read_text()
            self.assertNotIn('Verified Falcon Contributor', source)
            self.assertNotIn('data-message-author-role', source)

if __name__ == '__main__':
    unittest.main()
