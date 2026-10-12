#!/usr/bin/env python3
"""Generate an RSS 2.0 feed (/feed.xml) of the newest articles."""
import html
import json
import re
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
BASE_URL = 'https://thefitnessfalcon.com'
LIMIT = 30


def _date(post):
    raw = post.get('published_time') or f"{post['published_iso']}T00:00:00+00:00"
    return datetime.fromisoformat(raw.replace('Z', '+00:00')).astimezone(timezone.utc)


def generate_feed():
    posts = [json.loads(p.read_text()) for p in (ROOT / 'content/posts').glob('*.json')]
    posts = [p for p in posts if p.get('publish', True) is not False]
    posts.sort(key=lambda p: (_date(p), p['slug']), reverse=True)
    items = []
    for post in posts[:LIMIT]:
        url = f"{BASE_URL}/blogs/{post['slug']}/"
        image = BASE_URL + post['featured_image'] if post.get('featured_image') else ''
        summary = post.get('description', '')
        enclosure = ''
        if image:
            kind = 'image/png' if image.endswith('.png') else 'image/jpeg'
            enclosure = f'\n      <enclosure url="{escape(image)}" length="0" type="{kind}" />'
        items.append(f'''    <item>
      <title>{escape(html.unescape(post['title']))}</title>
      <link>{url}</link>
      <guid isPermaLink="true">{url}</guid>
      <pubDate>{format_datetime(_date(post))}</pubDate>
      <dc:creator>{escape(post.get('author', 'The Fitness Falcon'))}</dc:creator>
      <category>{escape(html.unescape(post.get('category', '')))}</category>
      <description>{escape(summary)}</description>{enclosure}
    </item>''')
    built = format_datetime(_date(posts[0])) if posts else format_datetime(datetime.now(timezone.utc))
    feed = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:dc="http://purl.org/dc/elements/1.1/">
  <channel>
    <title>The Fitness Falcon</title>
    <link>{BASE_URL}/</link>
    <description>Research-based fitness, nutrition, wearables and wellness guides.</description>
    <language>en-us</language>
    <lastBuildDate>{built}</lastBuildDate>
    <atom:link href="{BASE_URL}/feed.xml" rel="self" type="application/rss+xml" />
{chr(10).join(items)}
  </channel>
</rss>
'''
    (ROOT / 'feed.xml').write_text(feed)
    print(f'Generated feed.xml with {len(items)} items.')


if __name__ == '__main__':
    generate_feed()
