#!/usr/bin/env python3
"""Maintain old article/archive URLs and one public canonical host."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def generate_redirects():
    redirects = {}
    def aliases(slug, target):
        for suffix in ('', '/', '.html', '/index.html'):
            old = '/' + slug + suffix
            if old != target:
                redirects[old] = target
    for path in sorted((ROOT / 'content/posts').glob('*.json')):
        post = json.loads(path.read_text())
        aliases(post['slug'], '/blogs/' + post['slug'] + '/')
    for path in (ROOT / 'pages').glob('*/index.html'):
        aliases(path.parent.name, '/pages/' + path.parent.name + '/')
    aliases('about', '/pages/about-us/')
    aliases('blog', '/blogs/')
    author_aliases = {'dinesh': 'dinesh-jeengar', 'alex': 'the-fitness-falcon', 'riya-verma': 'the-fitness-falcon'}
    for old, new in author_aliases.items():
        aliases('author/' + old, '/author/' + new + '/')
        for page in range(1, 25):
            redirects[f'/author/{old}/page/{page}/'] = f'/author/{new}/'
    last_page = max([1] + [int(p.parent.name) for p in (ROOT / 'blogs/page').glob('*/index.html')])
    for page in range(1, 25):
        destination = '/blogs/' if page == 1 else f'/blogs/page/{min(page, last_page)}/'
        for base in ('blog/page', 'page'):
            aliases(f'{base}/{page}', destination)
    aliases('blogs/page/1', '/blogs/')
    parents = {'weight': 'health', 'nutrition': 'food-and-recipes', 'recipes': 'food-and-recipes', 'gym': 'fitness', 'yoga': 'fitness', 'sports': 'fitness', 'workout': 'fitness/gym', 'swimming': 'fitness/sports', 'trekking': 'fitness/sports', 'beauty': 'health', 'skincare': 'health'}
    for slug, parent in parents.items():
        if (ROOT / 'category' / slug / 'index.html').exists():
            aliases(f'category/{parent}/{slug}', f'/category/{slug}/')
    redirects['/wp-sitemap.xml'] = '/sitemap_index.xml'
    rules = ['# Generated canonical and compatibility routes', 'DirectoryIndex index.html', 'ErrorDocument 404 /404.html', '<IfModule mod_rewrite.c>', 'RewriteEngine On',
             'RewriteCond %{HTTP_HOST} ^www\\.thefitnessfalcon\\.com$ [NC]',
             'RewriteRule ^ https://thefitnessfalcon.com%{REQUEST_URI} [R=301,L,NE]',
             'RewriteCond %{HTTPS} !=on',
             'RewriteCond %{HTTP:X-Forwarded-Proto} !https [NC]',
             'RewriteRule ^ https://thefitnessfalcon.com%{REQUEST_URI} [R=301,L,NE]']
    for old, new in sorted(redirects.items()):
        rules.append(f'RewriteRule ^{re.escape(old.lstrip("/"))}$ {new} [R=301,L,NE]')
    rules.extend([
        '# Normalize explicit index.html only for browser requests, not DirectoryIndex subrequests.',
        'RewriteCond %{THE_REQUEST} \\s/+[^\\s?]*index\\.html(?:[?\\s]) [NC]',
        'RewriteRule ^(.*/)?index\\.html$ /$1 [R=301,L,NE]',
        'RewriteRule ^(?:\\.git|\\.hostinger|old-website|content|scripts|tests|audit|scratch|components)(?:/.*)?$ - [F,L]',
        '</IfModule>',
        '# Retained WordPress PHP endpoints must not compete with the static site.',
        '<IfModule mod_headers.c>',
        '<FilesMatch "\\.php$">',
        'Header set X-Robots-Tag "noindex, follow"',
        '</FilesMatch>',
        '</IfModule>',
    ])
    (ROOT / '.htaccess').write_text('\n'.join(rules) + '\n')
    netlify = [f'{old} {new} 301' for old, new in sorted(redirects.items())]
    for path in [ROOT / 'index.html'] + [p for folder in ('blogs', 'category', 'tag', 'author', 'pages') for p in (ROOT / folder).rglob('index.html')]:
        old = '/' + path.relative_to(ROOT).as_posix()
        new = old.removesuffix('index.html')
        if old not in redirects:
            netlify.append(f'{old} {new} 301')
    (ROOT / '_redirects').write_text('\n'.join(netlify) + '\n')
    (ROOT / 'audit/routes.json').write_text(json.dumps({'redirects': redirects}, indent=2) + '\n')
    print(f'Generated {len(redirects)} compatibility routes.')

if __name__ == '__main__':
    generate_redirects()
