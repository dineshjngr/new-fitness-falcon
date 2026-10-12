#!/usr/bin/env python3
"""Structured data for the homepage and archive pages (articles get theirs in build_posts).

- Homepage: WebSite (with SearchAction) + Organization (publisher).
- Blog, category and author archives: CollectionPage / ProfilePage with an
  ItemList of the articles shown, plus BreadcrumbList.
Idempotent: each run replaces the block marked id="ff-schema".
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = 'https://thefitnessfalcon.com'
LOGO = f'{BASE}/assets/images/cropped-Untitled-design-14-192x192.png'
SAME_AS = [
    'https://www.facebook.com/people/The-Fitness-Falcon/61553645405177/',
    'https://twitter.com/fitnessfalcon_',
    'https://www.instagram.com/thefitnessfalconofficial/',
    'https://www.youtube.com/@TheFitnessFalcon',
    'https://www.pinterest.com/thefitnessfalcon/',
]
ORG = {
    '@type': 'Organization',
    '@id': f'{BASE}/#organization',
    'name': 'The Fitness Falcon',
    'url': f'{BASE}/',
    'logo': {'@type': 'ImageObject', 'url': LOGO, 'width': 192, 'height': 192},
    'sameAs': SAME_AS,
    'publishingPrinciples': f'{BASE}/pages/editorial-policy/',
    'correctionsPolicy': f'{BASE}/pages/editorial-policy/',
}


def _script(data):
    return ('<script type="application/ld+json" id="ff-schema">'
            + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + '</script>')


def _inject(path, data):
    source = path.read_text()
    block = _script(data)
    if 'id="ff-schema"' in source:
        updated = re.sub(r'<script type="application/ld\+json" id="ff-schema">.*?</script>', lambda _: block, source, count=1, flags=re.S)
    else:
        updated = source.replace('</head>', block + '\n</head>', 1)
    if updated != source:
        path.write_text(updated)


def _homepage():
    path = ROOT / 'index.html'
    source = path.read_text()
    # Drop the legacy blocks: a local-business profile (address, phone, opening
    # hours) that does not describe a publication, and an empty Organization.
    source = re.sub(r'<script type="application/ld\+json">\s*\{\s*"@context": "https://schema.org",\s*"@type": "HealthAndBeautyBusiness".*?</script>\s*', '', source, flags=re.S)
    source = re.sub(r'<script type="application/ld\+json"[^>]*>\s*\[\{"@context":"https:\\/\\/schema.org\\/","@type":"Organization".*?</script>\s*', '', source, flags=re.S)
    path.write_text(source)
    _inject(path, {'@context': 'https://schema.org', '@graph': [
        {'@type': 'WebSite', '@id': f'{BASE}/#website', 'url': f'{BASE}/', 'name': 'The Fitness Falcon',
         'inLanguage': 'en-US', 'publisher': {'@id': f'{BASE}/#organization'},
         'potentialAction': {'@type': 'SearchAction',
                             'target': {'@type': 'EntryPoint', 'urlTemplate': f'{BASE}/search/?q={{search_term_string}}'},
                             'query-input': 'required name=search_term_string'}},
        ORG,
    ]})


def _archive(path, kind):
    source = path.read_text()
    if re.search(r'name="robots" content="[^"]*noindex', source):
        return
    canonical = re.search(r'rel="canonical" href="([^"]+)"', source)
    h1 = re.search(r'<h1[^>]*>(.*?)</h1>', source, re.S)
    if not canonical or not h1:
        return
    url = canonical.group(1)
    name = html.unescape(re.sub(r'<[^>]+>', '', h1.group(1))).strip()
    desc = re.search(r'<meta name="description" content="([^"]*)"', source)
    crumbs = []
    nav = re.search(r'<(?:nav|ol) class="falcon-breadcrumb"[^>]*>(.*?)</(?:nav|ol)>', source, re.S)
    if nav:
        parts = re.findall(r'<a href="([^"]+)"[^>]*>(.*?)</a>|<span[^>]*aria-current="page"[^>]*>(.*?)</span>', nav.group(1), re.S)
        for i, (href, link_text, current) in enumerate(parts, 1):
            label = html.unescape(re.sub(r'<[^>]+>', '', link_text or current)).strip()
            item = {'@type': 'ListItem', 'position': i, 'name': label,
                    'item': BASE + href if href.startswith('/') else url}
            crumbs.append(item)
    links = list(dict.fromkeys(re.findall(r'<h3 class="post-card-title"><a href="(/blogs/[^"]+/)"', source)))
    page = {'@type': 'ProfilePage' if kind == 'author' else 'CollectionPage', '@id': url, 'url': url,
            'name': name, 'inLanguage': 'en-US', 'isPartOf': {'@id': f'{BASE}/#website'},
            'publisher': {'@id': f'{BASE}/#organization'}}
    if desc:
        page['description'] = html.unescape(desc.group(1))
    if links:
        page['mainEntity'] = {'@type': 'ItemList', 'itemListElement': [
            {'@type': 'ListItem', 'position': i, 'url': BASE + href} for i, href in enumerate(links, 1)]}
    graph = [page, ORG]
    if crumbs:
        graph.append({'@type': 'BreadcrumbList', 'itemListElement': crumbs})
    _inject(path, {'@context': 'https://schema.org', '@graph': graph})


def generate_schema():
    _homepage()
    targets = [(ROOT / 'blogs/index.html', 'blog')]
    targets += [(p, 'blog') for p in (ROOT / 'blogs/page').glob('*/index.html')]
    targets += [(p, 'category') for p in (ROOT / 'category').glob('*/index.html')]
    targets += [(p, 'author') for p in (ROOT / 'author').rglob('index.html')]
    for path, kind in targets:
        _archive(path, kind)
    print(f'Structured data written for the homepage and {len(targets)} archive pages.')


if __name__ == '__main__':
    generate_schema()
