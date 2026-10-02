"""Heading navigation checks: hierarchy, unique anchors, and existing deep links."""
import json
import unittest
from pathlib import Path
from urllib.parse import unquote
from html.parser import HTMLParser

from scripts.build_posts import build_toc_and_content

ROOT = Path(__file__).resolve().parents[1]


class HeadingParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.headings = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in {'h2', 'h3', 'h4', 'h5', 'h6'}:
            self.headings.append((tag, attrs.get('id')))
        if tag == 'a' and attrs.get('href', '').startswith('#'):
            self.links.append(unquote(attrs['href'][1:]))


def parse(markup):
    parser = HeadingParser()
    parser.feed(markup)
    return parser


class ArticleTocTests(unittest.TestCase):
    def test_heading_hierarchy_and_entities(self):
        toc, body = build_toc_and_content(
            '<h2>Food &amp; Health</h2><h3><em>Protein</em></h3>'
            '<h4>Details</h4><h5>Sources</h5><h6>Notes</h6><h2>Recovery</h2>'
        )
        self.assertEqual(parse(toc).links, [id for tag, id in parse(body).headings if tag in ('h2', 'h3')])
        self.assertIn('<ol><li><a href="#protein">Protein</a></li></ol>', toc)
        for label in ('Details', 'Sources', 'Notes'):
            self.assertNotIn(label, toc)
            self.assertIn(label, body)
        self.assertIn('Food &amp; Health', toc)
        self.assertNotIn('&amp;amp;', toc)

    def test_collision_does_not_change_h2_links(self):
        toc, body = build_toc_and_content(
            '<h2>Overview</h2><h3 data-id="untouched">Overview</h3>'
            '<h2>Overview</h2><h3 id="custom-anchor">Detail</h3>'
            '<div id="section"></div><h4>Section</h4>'
        )
        self.assertEqual(parse(body).headings, [
            ('h2', 'overview'), ('h3', 'overview-3'), ('h2', 'overview-2'),
            ('h3', 'custom-anchor'), ('h4', 'section-2'),
        ])
        self.assertIn('data-id="untouched"', body)
        self.assertEqual(len(parse(toc).links), 4)

    def test_short_and_empty_articles(self):
        self.assertTrue(build_toc_and_content('<h3>Only section</h3>')[0])
        self.assertEqual(build_toc_and_content('<p>No headings.</p>')[0], '')
        self.assertEqual(build_toc_and_content('<h4>Detail only</h4><h5>Note</h5>')[0], '')
        toc, body = build_toc_and_content('<h1>Imported heading</h1><h2> </h2>')
        self.assertNotIn('<h1', body)
        self.assertEqual(parse(toc).links, ['imported-heading'])

    def test_every_article_has_unique_resolvable_toc_links(self):
        for source in sorted((ROOT / 'content/posts').glob('*.json')):
            with self.subTest(article=source.stem):
                post = json.loads(source.read_text())
                toc, body = build_toc_and_content(post['content'])
                anchors = [id for tag, id in parse(body).headings if id and tag in ('h2', 'h3')]
                self.assertEqual(parse(toc).links, anchors)
                self.assertEqual(len(anchors), len(set(anchors)))


if __name__ == '__main__':
    unittest.main()
