#!/usr/bin/env python3
"""Generate sitemaps from existing, canonical, indexable built pages."""
import json
import re
from pathlib import Path
from xml.sax.saxutils import escape
ROOT = Path(__file__).resolve().parent.parent
BASE_URL = 'https://thefitnessfalcon.com'

def sitemap_xml(entries):
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for url, modified in entries:
        lines.append('  <url><loc>' + escape(url) + '</loc>' + ('<lastmod>' + escape(modified) + '</lastmod>' if modified else '') + '</url>')
    lines.append('</urlset>')
    return '\n'.join(lines) + '\n'

def generate_sitemap_and_robots():
    dates = {}
    for path in (ROOT / 'content/posts').glob('*.json'):
        post = json.loads(path.read_text())
        dates[BASE_URL + '/blogs/' + post['slug'] + '/'] = post.get('modified_time') or post.get('modified_iso') or post.get('published_iso')
    pages = [ROOT / 'index.html']
    for directory in ('blogs', 'category', 'author', 'pages'):
        pages.extend((ROOT / directory).rglob('index.html'))
    entries = {}
    for path in sorted(pages):
        source = path.read_text()
        if re.search(r'<meta\b[^>]*\bname=[\"\']robots[\"\'][^>]*\bcontent=[\"\'][^\"\']*noindex', source, re.I):
            continue
        canonical = re.search(r'<link\b[^>]*\brel=[\"\']canonical[\"\'][^>]*\bhref=[\"\']([^\"\']+)', source, re.I)
        url = BASE_URL + '/' + path.relative_to(ROOT).as_posix().removesuffix('index.html')
        if not canonical or canonical[1] != url:
            raise ValueError(f'{path}: sitemap requires a matching self-canonical URL')
        entries[url] = dates.get(url)
    all_entries = sorted(entries.items())
    (ROOT / 'sitemap.xml').write_text(sitemap_xml(all_entries))
    sections = {
        'post-sitemap.xml': [(u, d) for u, d in all_entries if u in dates],
        'category-sitemap.xml': [(u, d) for u, d in all_entries if '/category/' in u],
        'page-sitemap.xml': [(u, d) for u, d in all_entries if u not in dates and '/category/' not in u],
    }
    for name, section in sections.items():
        (ROOT / name).write_text(sitemap_xml(section))
    index = ['<?xml version="1.0" encoding="UTF-8"?>', '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    index.extend(f'  <sitemap><loc>{BASE_URL}/{name}</loc></sitemap>' for name in sections)
    index.append('</sitemapindex>')
    (ROOT / 'sitemap_index.xml').write_text('\n'.join(index) + '\n')
    (ROOT / 'robots.txt').write_text(f'''# robots.txt for {BASE_URL}/
User-agent: *
Allow: /
Disallow: /search/
Disallow: /404.html

# Archive noindex directives are in HTML so crawlers can read them.
Sitemap: {BASE_URL}/sitemap.xml
''')
    print(f'Generated sitemap.xml with {len(all_entries)} indexable URLs and 3 compatible section sitemaps.')

if __name__ == '__main__':
    generate_sitemap_and_robots()
