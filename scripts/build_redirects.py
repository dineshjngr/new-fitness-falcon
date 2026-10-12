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
    # Trashed WordPress posts that Search Console still reports (2026-10-12).
    # Redirect only where a page covers the same topic; otherwise answer 410.
    aliases('best-gym-workout-routine-for-full-body-strength-and-fitness', '/blogs/best-full-body-workout-gym-for-2026/')
    gone = ['/best-wearable-devices-for-managing-chronic-pain-symptoms',
            '/best-wearable-devices-for-managing-chronic-pain-symptoms/']
    # Removed WordPress posts reported by Search Console: redirect only to a
    # current article on the same topic; everything else answers 410 Gone.
    legacy_same_topic = {
        'how-to-fix-a-damaged-skin-barrier-in-48-hours': 'essential-tips-for-dry-skin-care-how-to-repair-your-skin-barrier',
        'home-remedies-for-weight-loss-the-ultimate-guide-for-2024': 'healthy-eating-tips-for-weight-loss',
        'what-is-menstrual-cycle-period-pain-relief': 'the-four-phases-of-the-menstrual-cycle-and-how-they-impact-your-health',
        '10-harmful-effects-of-cigarette-smoking': '10-serious-diseases-caused-by-smoking',
        'the-art-of-facial-yoga-unlocking-radiant-skin-and-wellness-through-natural-exercise': 'face-yoga-for-anti-aging-and-skin-health',
        'tag/facial-yoga-exercises': 'face-yoga-for-anti-aging-and-skin-health',
    }
    for old_slug, new_slug in legacy_same_topic.items():
        if (ROOT / 'content/posts' / f'{new_slug}.json').exists():
            aliases(old_slug, f'/blogs/{new_slug}/')
            aliases(f'{old_slug}/feed', f'/blogs/{new_slug}/')
    for slug in ('yoga-for-weight-gain-10-effective-poses-to-build-a-healthy-body',
                 'diabetes-causes-symptoms-treatment',
                 'hormonal-imbalance-signs-symptoms-and-treatment',
                 'irregular-periods-causes-symptoms-treament',
                 'what-is-cpr-and-how-is-it-performed',
                 'does-your-period-cause-weight-gain-causes-myths-solutions',
                 'yoga-for-weight-loss-10-powerful-poses',
                 'how-to-quit-smoking-naturally-effective-home-remedies-and-tips'):
        if not (ROOT / 'content/posts' / f'{slug}.json').exists():
            gone.extend([f'/{slug}', f'/{slug}/', f'/{slug}/feed', f'/{slug}/feed/'])
    # Trashed posts whose URLs (and WordPress feeds) Search Console still lists.
    for slug in ('does-kissing-burn-calories-french-kiss-your-way-to-fitness',
                 'working-out-on-ozempic-the-complete-exercise-guide-to-prevent-muscle-loss',
                 'best-seeds-for-hormonal-balance-in-women',
                 'top-tastiest-types-of-food-cuisine-in-the-usa',
                 'can-fasting-reverse-aging'):
        if not (ROOT / 'content/posts' / f'{slug}.json').exists():
            gone.extend([f'/{slug}', f'/{slug}/', f'/{slug}/feed', f'/{slug}/feed/'])
    # Old WordPress per-post RSS feeds: send readers to the article itself.
    for path in sorted((ROOT / 'content/posts').glob('*.json')):
        slug = json.loads(path.read_text())['slug']
        for base in (f'/{slug}/feed', f'/blogs/{slug}/feed'):
            redirects[base] = f'/blogs/{slug}/'
            redirects[base + '/'] = f'/blogs/{slug}/'
    redirects['/feed'] = '/feed.xml'
    redirects['/feed/'] = '/feed.xml'
    redirects['/rss'] = '/feed.xml'
    redirects['/rss/'] = '/feed.xml'
    # The old theme linked the Twitter handle as a relative URL, creating
    # /<page>/@fitnessfalcon_ paths. Send each one back to its page.
    handle = '@fitnessfalcon_'
    for target_old, target_new in list(redirects.items()):
        if target_old.endswith('/') and target_old.count('/') >= 2:
            redirects[f'{target_old}{handle}'] = target_new
            redirects[f'{target_old}{handle}/'] = target_new
    for path in sorted((ROOT / 'content/posts').glob('*.json')):
        slug = json.loads(path.read_text())['slug']
        for base in (f'/{slug}/', f'/blogs/{slug}/'):
            redirects[f'{base}{handle}'] = f'/blogs/{slug}/'
            redirects[f'{base}{handle}/'] = f'/blogs/{slug}/'
    rules = ['# Generated canonical and compatibility routes', 'DirectoryIndex index.html', 'ErrorDocument 404 /404.html', '<IfModule mod_rewrite.c>', 'RewriteEngine On',
             'RewriteCond %{HTTP_HOST} ^www\\.thefitnessfalcon\\.com$ [NC]',
             'RewriteRule ^ https://thefitnessfalcon.com%{REQUEST_URI} [R=301,L,NE]',
             'RewriteCond %{HTTPS} !=on',
             'RewriteCond %{HTTP:X-Forwarded-Proto} !https [NC]',
             'RewriteRule ^ https://thefitnessfalcon.com%{REQUEST_URI} [R=301,L,NE]']
    for old, new in sorted(redirects.items()):
        rules.append(f'RewriteRule ^{re.escape(old.lstrip("/"))}$ {new} [R=301,L,NE]')
    for old in gone:
        rules.append(f'RewriteRule ^{re.escape(old.lstrip("/"))}$ - [G,L]')
    rules.extend([
        '# Any other /<path>/@fitnessfalcon_ URL: strip the malformed handle suffix.',
        'RewriteRule ^(.+?)/@fitnessfalcon_/?$ /$1/ [R=301,L,NE]',
        '# WordPress date archives (/2024/01/, /2024/01/page/2/) and any other feed.',
        'RewriteRule ^20\\d{2}(?:/\\d{2}){0,2}(?:/page/\\d+)?/?$ /blogs/ [R=301,L]',
        'RewriteRule ^(.+?)/feed/?$ /$1/ [R=301,L,NE]',
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
    netlify.extend(f'{old} /404.html 410' for old in gone)
    netlify.extend(f'/{year}/* /blogs/ 301' for year in range(2023, 2027))
    (ROOT / '_redirects').write_text('\n'.join(netlify) + '\n')
    (ROOT / 'audit/routes.json').write_text(json.dumps({'redirects': redirects, 'gone': gone}, indent=2) + '\n')
    print(f'Generated {len(redirects)} compatibility routes.')

if __name__ == '__main__':
    generate_redirects()
