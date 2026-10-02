#!/usr/bin/env python3
"""
The Fitness Falcon - XML Sitemap & robots.txt Generator
Generates a standard-compliant, search-engine crawlable sitemap.xml and robots.txt
covering all canonical indexable pages on https://thefitnessfalcon.com/.
"""
import json, re, sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / 'content' / 'posts'
SITEMAP_FILE = ROOT / 'sitemap.xml'
ROBOTS_FILE = ROOT / 'robots.txt'

BASE_URL = 'https://thefitnessfalcon.com'

def slugify(text):
    return re.sub(r'-+', '-', re.sub(r'[^a-z0-9]+', '-', text.lower().strip())).strip('-')

def generate_sitemap_and_robots():
    print('Generating sitemap.xml and robots.txt...')
    urls = []

    # 1. Homepage
    today_iso = datetime.now().strftime('%Y-%m-%d')
    urls.append({
        'loc': f'{BASE_URL}/',
        'lastmod': today_iso,
        'changefreq': 'daily',
        'priority': '1.0'
    })

    # 2. Main Blog Archive
    urls.append({
        'loc': f'{BASE_URL}/blogs/',
        'lastmod': today_iso,
        'changefreq': 'daily',
        'priority': '0.9'
    })

    # 3. Single Blog Posts
    posts = []
    tags_set = set()
    authors_set = set()
    categories_set = set()

    for f in sorted(CONTENT_DIR.glob('*.json')):
        try:
            data = json.loads(f.read_text(encoding='utf-8'))
            posts.append(data)
            for t in data.get('tags', []):
                s = slugify(str(t))
                if s:
                    tags_set.add(s)
            author = data.get('author')
            if author:
                authors_set.add(slugify(author))
            cat = data.get('category_url', '').strip('/').split('/')[-1]
            if cat:
                categories_set.add(cat)
        except Exception as e:
            print(f'Error reading {f}: {e}', file=sys.stderr)

    for p in posts:
        slug = p['slug']
        mod_date = p.get('modified_iso') or p.get('published_iso') or today_iso
        urls.append({
            'loc': f"{BASE_URL}/blogs/{slug}/",
            'lastmod': mod_date,
            'changefreq': 'weekly',
            'priority': '0.8'
        })

    # 4. Categories
    for cat in sorted(categories_set):
        urls.append({
            'loc': f"{BASE_URL}/category/{cat}/",
            'lastmod': today_iso,
            'changefreq': 'weekly',
            'priority': '0.7'
        })

    # 5. Tags
    for tag in sorted(tags_set):
        urls.append({
            'loc': f"{BASE_URL}/tag/{tag}/",
            'lastmod': today_iso,
            'changefreq': 'weekly',
            'priority': '0.6'
        })

    # 6. Authors
    for author in sorted(authors_set):
        urls.append({
            'loc': f"{BASE_URL}/author/{author}/",
            'lastmod': today_iso,
            'changefreq': 'monthly',
            'priority': '0.6'
        })

    # 7. Static & Legal Pages
    static_pages = ['team', 'contact-us', 'write-for-us', 'privacy-policy']
    for sp in static_pages:
        urls.append({
            'loc': f"{BASE_URL}/pages/{sp}/",
            'lastmod': today_iso,
            'changefreq': 'monthly',
            'priority': '0.5'
        })

    # Build XML
    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]

    for item in urls:
        xml_lines.append('  <url>')
        xml_lines.append(f"    <loc>{item['loc']}</loc>")
        xml_lines.append(f"    <lastmod>{item['lastmod']}</lastmod>")
        xml_lines.append(f"    <changefreq>{item['changefreq']}</changefreq>")
        xml_lines.append(f"    <priority>{item['priority']}</priority>")
        xml_lines.append('  </url>')

    xml_lines.append('</urlset>')
    xml_content = '\n'.join(xml_lines) + '\n'

    SITEMAP_FILE.write_text(xml_content, encoding='utf-8')
    print(f'Successfully generated {SITEMAP_FILE.name} with {len(urls)} URLs.')

    # Build robots.txt
    robots_content = f"""# robots.txt for https://thefitnessfalcon.com/
User-agent: *
Allow: /
Disallow: /search/
Disallow: /404.html

# Sitemap
Sitemap: {BASE_URL}/sitemap.xml
"""
    ROBOTS_FILE.write_text(robots_content, encoding='utf-8')
    print(f'Successfully generated {ROBOTS_FILE.name}.')

if __name__ == '__main__':
    generate_sitemap_and_robots()
