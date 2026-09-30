#!/usr/bin/env python3
"""
Migrate all 180 canonical pages to use the unified global architecture:
- 1 shared global header (<!-- shared:header:start --> ... <!-- shared:header:end -->)
- 1 shared global footer (<!-- shared:footer:start --> ... <!-- shared:footer:end -->)
- 1 global layout system (<main id="main-content" class="falcon-main-layout">)
- Shared design system & tokens in assets/css/custom-style.css
- Shared search data in assets/js/falcon-search-data.js
- Shared core scripts in assets/js/falcon-core.js
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXCLUDED = {'components', 'old-website', 'node_modules', '.git'}

def migrate_index():
    index_path = ROOT / 'index.html'
    content = index_path.read_text()

    # 1. Add skip link if not present
    if 'skip-link' not in content:
        content = re.sub(
            r'(<body[^>]*>\s*)(<div class="pfy-main-wrapper">)?',
            r'\1<a href="#main-content" class="skip-link">Skip to main content</a>\n<div class="falcon-site-wrapper">\n',
            content,
            count=1
        )
        if '</div><!-- falcon-site-wrapper -->' not in content:
            content = content.replace('</body>', '</div><!-- falcon-site-wrapper -->\n</body>')

    # 2. Wrap content between header and footer with <main>
    if '<main' not in content:
        start_pat = '<!-- shared:header:end -->'
        end_pat = '<!-- shared:footer:start -->'
        if start_pat in content and end_pat in content:
            before, rest = content.split(start_pat, 1)
            mid, after = rest.split(end_pat, 1)
            mid = mid.strip()
            mid = f'\n\n<main id="main-content" class="falcon-main-layout home-main">\n{mid}\n</main>\n\n'
            content = before + start_pat + mid + end_pat + after

    # 3. Replace duplicate inline ALL_POSTS script with shared falcon-search-data.js and falcon-core.js
    if 'const ALL_POSTS =' in content:
        content = re.sub(
            r'<script>\s*const ALL_POSTS = \[.*?\n\s*</script>',
            '<script src="/assets/js/falcon-search-data.js"></script>\n<script src="/assets/js/falcon-core.js"></script>',
            content,
            flags=re.DOTALL
        )

    # Clean up duplicate scripts if present
    content = re.sub(r'(<script src="/assets/js/falcon-search-data\.js"></script>\s*)+', '<script src="/assets/js/falcon-search-data.js"></script>\n', content)
    content = re.sub(r'(<script src="/assets/js/falcon-core\.js"></script>\s*)+', '<script src="/assets/js/falcon-core.js"></script>\n', content)

    index_path.write_text(content)
    print('Updated index.html to use global layout and shared scripts.')

def migrate_page(page_path):
    content = page_path.read_text()

    # Check if page already has shared:header:start
    if '<!-- shared:header:start -->' in content and '<!-- shared:footer:start -->' in content:
        return False

    # Extract head
    m_head = re.search(r'(.*?)(?:</head>\s*<body>)', content, flags=re.DOTALL | re.IGNORECASE)
    if not m_head:
        print(f'Warning: Could not parse head in {page_path}')
        return False
    head_part = m_head.group(1).strip()

    # Remove inline style from head (now unified in custom-style.css)
    head_part = re.sub(r'\s*<style>.*?</style>', '', head_part, flags=re.DOTALL)

    # Extract main content
    m_main = re.search(r'<main[^>]*>(.*?)</main>', content, flags=re.DOTALL | re.IGNORECASE)
    if not m_main:
        print(f'Warning: Could not parse main in {page_path}')
        return False
    main_inner = m_main.group(1).strip()

    depth = len(page_path.relative_to(ROOT).parts) - 1
    prefix = '../' * depth

    new_content = f'''{head_part}
</head>
<body>
<a href="#main-content" class="skip-link">Skip to main content</a>
<div class="falcon-site-wrapper">
<!-- shared:header:start -->
<!-- shared:header:end -->

<main id="main-content" class="falcon-main-layout">
{main_inner}
</main>

<!-- shared:footer:start -->
<!-- shared:footer:end -->
</div>

<!-- JS Dependencies -->
<script src="/assets/js/jquery.min.js"></script>
<script src="/assets/js/popper.min.js"></script>
<script src="/assets/js/bootstrap.min.js"></script>
<script src="/assets/js/owl.carousel.min.js"></script>
<script src="/assets/js/search-results.js"></script>
<script src="/assets/js/falcon-search-data.js"></script>
<script src="/assets/js/falcon-core.js"></script>
</body>
</html>
'''
    page_path.write_text(new_content)
    return True

def main():
    migrate_index()

    pages = sorted(p for p in ROOT.rglob('*.html') if not EXCLUDED.intersection(p.relative_to(ROOT).parts) and p != (ROOT / 'index.html'))
    updated = sum(migrate_page(p) for p in pages)
    print(f'Migrated {updated} / {len(pages)} canonical pages.')

if __name__ == '__main__':
    main()
