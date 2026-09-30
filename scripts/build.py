#!/usr/bin/env python3
"""
Render the shared site shell into every marked HTML page.
Supports 1 shared global header, 1 shared global footer, and 1 global layout system.
"""
import re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
COMPONENTS = ('header', 'footer')
EXCLUDED = {'components', 'old-website', 'node_modules', '.git'}

def render_page(path):
    path = path.resolve()
    source = path.read_text()
    depth = len(path.relative_to(ROOT).parts) - 1
    prefix = '../' * depth

    for name in COMPONENTS:
        start = f'<!-- shared:{name}:start -->'
        end = f'<!-- shared:{name}:end -->'
        if start not in source and end not in source:
            continue
        pattern = re.compile(re.escape(start) + r'.*?' + re.escape(end), re.DOTALL)
        if source.count(start) != 1 or source.count(end) != 1 or not pattern.search(source):
            raise ValueError(f'{path}: expected one complete {name} include')
        
        markup = (ROOT / 'components' / f'{name}.html').read_text().rstrip()
        # Resolve component assets correctly for nested article/category pages
        markup = re.sub(r'((?:src|href)=["\'])(?:/)?assets/', lambda m: m[1] + prefix + 'assets/', markup)
        source = pattern.sub(lambda _: start + '\n' + markup + '\n' + end, source)

    # Install the shared footer stylesheet once, with the correct page-relative URL
    if '<!-- shared:footer:start -->' in source:
        source = re.sub(r'<link\b[^>]*href=["\'][^"\']*assets/css/footer\.css["\'][^>]*>\s*', '', source)
        if '</head>' not in source:
            raise ValueError(f'{path}: missing </head>')
        source = source.replace('</head>', f'<link rel="stylesheet" href="{prefix}assets/css/footer.css">\n</head>', 1)

    if source != path.read_text():
        path.write_text(source)
        return True
    return False

from scripts.build_posts import render_all_posts

def main():
    # 1. Render all blog posts through the single master template components/post-template.html
    render_all_posts()

    # 2. Sync shared shell components (header and footer) into all canonical HTML pages
    pages = sorted(p for p in ROOT.rglob('*.html') if not EXCLUDED.intersection(p.relative_to(ROOT).parts))
    changed = sum(render_page(page) for page in pages)
    print(f'Built {len(pages)} page(s); updated {changed}.')

if __name__ == '__main__':
    main()
