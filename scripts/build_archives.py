#!/usr/bin/env python3
"""
The Fitness Falcon - Archive Pages Compiler (Blogs, Categories, Tags & Authors)
Compiles blogs/index.html, paginated /blogs/page/*/, category/*/index.html,
tag/*/index.html (paginated), and author/*/index.html (paginated)
using components/archive-template.html and scripts/components.py.
Eliminates all hardcoded card duplications and inline styles across archives.
Generates crawlable, SEO-compliant pagination URLs.
"""
import os, sys, re, json, html, math, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import scripts.components as components

TEMPLATE_PATH = ROOT / 'components' / 'archive-template.html'
CONTENT_DIR = ROOT / 'content' / 'posts'
BLOGS_DIR = ROOT / 'blogs'
BLOGS_INDEX = ROOT / 'blogs' / 'index.html'
CATEGORY_DIR = ROOT / 'category'
CATEGORY_POSTS_JSON = ROOT / 'audit' / 'category_posts.json'
TAG_DIR = ROOT / 'tag'
AUTHOR_DIR = ROOT / 'author'

POSTS_PER_PAGE = 12

def slugify(text):
    """Convert text to a URL-safe slug."""
    return re.sub(r'-+', '-', re.sub(r'[^a-z0-9]+', '-', text.lower().strip())).strip('-')

CATEGORY_META = {
    "beauty": {
        "title": "Beauty Articles - The Fitness Falcon",
        "meta_description": "Explore all health, workout, and wellness articles in Beauty on The Fitness Falcon.",
        "h1": "Beauty"
    },
    "blog": {
        "title": "Blog Articles - The Fitness Falcon",
        "meta_description": "Explore all health, workout, and wellness articles in Blog on The Fitness Falcon.",
        "h1": "Blog"
    },
    "cycling": {
        "title": "Cycling Articles - The Fitness Falcon",
        "meta_description": "Explore all health, workout, and wellness articles in Cycling on The Fitness Falcon.",
        "h1": "Cycling"
    },
    "fitness": {
        "title": "Fitness Articles - The Fitness Falcon",
        "meta_description": "Explore all health, workout, and wellness articles in Fitness on The Fitness Falcon.",
        "h1": "Fitness"
    },
    "food-and-recipes": {
        "title": "Food & Recipes Articles - The Fitness Falcon",
        "meta_description": "Explore all health, workout, and wellness articles in Food & Recipes on The Fitness Falcon.",
        "h1": "Food & Recipes"
    },
    "gym": {
        "title": "Gym Articles - The Fitness Falcon",
        "meta_description": "Explore all health, workout, and wellness articles in Gym on The Fitness Falcon.",
        "h1": "Gym"
    },
    "health": {
        "title": "Health Articles - The Fitness Falcon",
        "meta_description": "Explore all health, workout, and wellness articles in Health on The Fitness Falcon.",
        "h1": "Health"
    },
    "lifestyle": {
        "title": "Lifestyle Articles - The Fitness Falcon",
        "meta_description": "Explore all health, workout, and wellness articles in Lifestyle on The Fitness Falcon.",
        "h1": "Lifestyle"
    },
    "news": {
        "title": "News Articles - The Fitness Falcon",
        "meta_description": "Explore all health, workout, and wellness articles in News on The Fitness Falcon.",
        "h1": "News"
    },
    "nutrition": {
        "title": "Nutrition Articles - The Fitness Falcon",
        "meta_description": "Explore all health, workout, and wellness articles in Nutrition on The Fitness Falcon.",
        "h1": "Nutrition"
    },
    "recipes": {
        "title": "Recipes Articles - The Fitness Falcon",
        "meta_description": "Explore all health, workout, and wellness articles in Recipes on The Fitness Falcon.",
        "h1": "Recipes"
    },
    "skincare": {
        "title": "Skincare Articles - The Fitness Falcon",
        "meta_description": "Explore all health, workout, and wellness articles in Skincare on The Fitness Falcon.",
        "h1": "Skincare"
    },
    "sports": {
        "title": "Sports Articles - The Fitness Falcon",
        "meta_description": "Explore all health, workout, and wellness articles in Sports on The Fitness Falcon.",
        "h1": "Sports"
    },
    "swimming": {
        "title": "Swimming Articles - The Fitness Falcon",
        "meta_description": "Explore all health, workout, and wellness articles in Swimming on The Fitness Falcon.",
        "h1": "Swimming"
    },
    "trekking": {
        "title": "Trekking Articles - The Fitness Falcon",
        "meta_description": "Explore all health, workout, and wellness articles in Trekking on The Fitness Falcon.",
        "h1": "Trekking"
    },
    "wearables-fitness-technology": {
        "title": "Wearables & Fitness Technology Articles - The Fitness Falcon",
        "meta_description": "Explore all health, workout, and wellness articles in Wearables & Fitness Technology on The Fitness Falcon.",
        "h1": "Wearables & Fitness Technology"
    },
    "weight": {
        "title": "Weight Articles - The Fitness Falcon",
        "meta_description": "Explore all health, workout, and wellness articles in Weight on The Fitness Falcon.",
        "h1": "Weight"
    },
    "workout": {
        "title": "Workout Articles - The Fitness Falcon",
        "meta_description": "Explore all health, workout, and wellness articles in Workout on The Fitness Falcon.",
        "h1": "Workout"
    },
    "yoga": {
        "title": "Yoga Articles - The Fitness Falcon",
        "meta_description": "Explore all health, workout, and wellness articles in Yoga on The Fitness Falcon.",
        "h1": "Yoga"
    }
}

def load_posts():
    posts = []
    for f in sorted(CONTENT_DIR.glob('*.json')):
        try:
            data = json.loads(f.read_text(encoding='utf-8'))
            posts.append(data)
        except Exception as e:
            print(f'Error reading {f}: {e}', file=sys.stderr)
    # Sort chronologically (newest first) by true published timestamp
    posts.sort(key=lambda p: (p.get('published_time') or p.get('published_iso', ''), p['slug']), reverse=True)
    return posts

def build_recent_widget(recent_posts):
    items = []
    for p in recent_posts:
        items.append(f'''        <div class="falcon-recent-item">
            <a href="/blogs/{p['slug']}/" class="falcon-recent-thumb" aria-label="{html.escape(p['title'])}">
                <img src="{p['featured_image']}" alt="{html.escape(p['title'])}" loading="lazy" />
            </a>
            <div class="falcon-recent-content">
                <a href="/blogs/{p['slug']}/" class="falcon-recent-title">{html.escape(p['title'])}</a>
                <span class="falcon-recent-date"><i class="fal fa-calendar-alt"></i> {p['published_date']}</span>
            </div>
        </div>''')
    return '\n'.join(items)

def build_categories_widget(categories_counts):
    items = []
    for cat_name, cat_slug, count in categories_counts:
        items.append(f'''        <li class="falcon-cat-item">
            <a href="/category/{cat_slug}/" class="falcon-cat-link">{html.escape(cat_name)}</a>
            <span class="falcon-cat-badge">{count}</span>
        </li>''')
    return '\n'.join(items)

def build_category_filter_bar(categories_data, active_slug=None):
    pills = []
    all_active = ' active' if active_slug is None else ''
    pills.append(f'<a href="/blogs/" class="falcon-filter-pill{all_active}"><i class="fal fa-th-large"></i> All Articles</a>')
    for cat_name, cat_slug, count in categories_data:
        is_active = ' active' if active_slug == cat_slug else ''
        pills.append(f'<a href="/category/{cat_slug}/" class="falcon-filter-pill{is_active}">{html.escape(cat_name)}</a>')
    return f'''<nav class="falcon-archive-filter-bar" aria-label="Browse articles by category">
    <div class="falcon-filter-pills">
        {''.join(pills)}
    </div>
</nav>'''

def build_in_page_filter_row(count_displayed, label="articles"):
    return f'''<div class="falcon-archive-filter-row">
    <div class="falcon-filter-search">
        <i class="fal fa-search" aria-hidden="true"></i>
        <input type="search" id="archiveFilterInput" placeholder="Quick filter articles on this page..." aria-label="Quick filter articles on this page" autocomplete="off" />
    </div>
    <div class="falcon-filter-count">
        Showing <span>{count_displayed}</span> {label}
    </div>
</div>'''

def build_sidebar(recent_posts_html, categories_html, newsletter_html):
    return f'''<div class="col-lg-4">
    <aside class="falcon-sidebar-area" aria-label="Sidebar widgets">
        <div class="falcon-sidebar-widget">
            <h3 class="falcon-sidebar-widget-title">Recent Articles</h3>
            {recent_posts_html}
        </div>
        <div class="falcon-sidebar-widget">
            <h3 class="falcon-sidebar-widget-title">Categories</h3>
            <ul style="list-style: none; padding: 0; margin: 0;">
                {categories_html}
            </ul>
        </div>
        {newsletter_html}
    </aside>
</div>'''

def _render_blogs_and_categories():
    template = TEMPLATE_PATH.read_text(encoding='utf-8')
    posts = load_posts()
    post_by_slug = {p['slug']: p for p in posts}
    total_posts = len(posts)

    cat_posts_map = {}
    if CATEGORY_POSTS_JSON.exists():
        cat_posts_map = json.loads(CATEGORY_POSTS_JSON.read_text(encoding='utf-8'))

    # Calculate category counts across all posts
    cat_counts = {}
    cat_slug_map = {}
    for p in posts:
        c = p['category']
        cat_counts[c] = cat_counts.get(c, 0) + 1
        cat_slug_map[c] = p['category_url'].strip('/').split('/')[-1]
    sorted_cats = sorted(cat_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    category_filter_data = [(c, cat_slug_map[c], cnt) for c, cnt in sorted_cats]

    recent_posts = posts[:5]
    sidebar_recent_html = build_recent_widget(recent_posts)
    sidebar_categories_html = build_categories_widget(category_filter_data)
    sidebar_newsletter_html = components.render_newsletter_block()

    # -------------------------------------------------------------------------
    # 1. Render Main Blog Archive & Crawlable Paginated Pages
    # -------------------------------------------------------------------------
    # Page 1: 1 featured story + 12 grid cards (13 articles)
    # Subsequent pages: 12 grid cards each
    if total_posts <= 13:
        total_pages = 1
    else:
        total_pages = 1 + math.ceil((total_posts - 13) / 12)

    category_filter_bar_html = build_category_filter_bar(category_filter_data, active_slug=None)

    # Clean existing blogs/page/ directory
    page_dir_base = BLOGS_DIR / 'page'
    if page_dir_base.exists():
        shutil.rmtree(page_dir_base)

    for p in range(1, total_pages + 1):
        if p == 1:
            out_file = BLOGS_INDEX
            canonical_url = 'https://thefitnessfalcon.com/blogs/'
            page_title = 'All Articles - Blog - The Fitness Falcon'
            page_desc = 'Read all health, fitness, nutrition, and lifestyle articles on The Fitness Falcon.'
            breadcrumbs_html = components.render_breadcrumbs([
                ('Home', '/'),
                ('All Articles', '/blogs/')
            ])
            top_post = posts[0]
            featured_card_html = components.render_featured_card(top_post)
            page_posts = posts[1:13]
            rel_links = '<link rel="next" href="https://thefitnessfalcon.com/blogs/page/2/" />' if total_pages > 1 else ''
        else:
            page_dir = page_dir_base / str(p)
            page_dir.mkdir(parents=True, exist_ok=True)
            out_file = page_dir / 'index.html'
            canonical_url = f'https://thefitnessfalcon.com/blogs/page/{p}/'
            page_title = f'All Articles - Page {p} of {total_pages} - Blog - The Fitness Falcon'
            page_desc = f'Read all health, fitness, nutrition, and lifestyle articles on The Fitness Falcon. Page {p} of {total_pages}.'
            breadcrumbs_html = components.render_breadcrumbs([
                ('Home', '/'),
                ('All Articles', '/blogs/'),
                (f'Page {p}', f'/blogs/page/{p}/')
            ])
            featured_card_html = ''
            start_idx = 13 + (p - 2) * 12
            end_idx = min(total_posts, start_idx + 12)
            page_posts = posts[start_idx:end_idx]

            prev_url = '/blogs/' if p == 2 else f'/blogs/page/{p - 1}/'
            rel_prev = f'<link rel="prev" href="https://thefitnessfalcon.com{prev_url}" />'
            rel_next = f'<link rel="next" href="https://thefitnessfalcon.com/blogs/page/{p + 1}/" />' if p < total_pages else ''
            rel_links = f"{rel_prev}\n    {rel_next}".strip()

        # Render grid cards using components.py
        cards_html = '\n'.join([
            components.render_article_card(post, col_class="col-md-6 col-lg-4 mb-4")
            for post in page_posts
        ])

        # Render standardized pagination component
        pagination_html = components.render_pagination(
            current_page=p,
            total_pages=total_pages,
            base_url="/blogs/",
            page_path_pattern="/blogs/page/{page}/"
        )

        in_page_filter_html = build_in_page_filter_row(len(page_posts) + (1 if p == 1 else 0))

        archive_header_html = f'''<div style="text-align: center; margin-bottom: 28px;">
    <span class="category-badge" style="margin-bottom: 12px;">Full Library</span>
    <h1 style="font-size: 40px; color: #0f172a; margin-top: 10px;">The Fitness Falcon Blog</h1>
    <p style="font-size: 18px; color: #64748b; max-width: 650px; margin: 12px auto 0;">Explore our collection of {total_posts} articles covering workouts, wellness, recipes, and technology.</p>
</div>'''

        rendered = template
        rendered = rendered.replace('{{META_TITLE}}', html.escape(page_title))
        rendered = rendered.replace('{{META_DESCRIPTION}}', html.escape(page_desc))
        rendered = rendered.replace('{{CANONICAL_URL}}', canonical_url)
        rendered = rendered.replace('{{PAGINATION_REL_LINKS}}', rel_links)
        rendered = rendered.replace('{{BREADCRUMBS_HTML}}', breadcrumbs_html)
        rendered = rendered.replace('{{ARCHIVE_HEADER_HTML}}', archive_header_html)
        rendered = rendered.replace('{{CATEGORY_FILTER_BAR_HTML}}', category_filter_bar_html)
        rendered = rendered.replace('{{FEATURED_CARD_HTML}}', featured_card_html)
        rendered = rendered.replace('{{IN_PAGE_FILTER_HTML}}', in_page_filter_html)
        rendered = rendered.replace('{{GRID_COL_CLASS}}', 'col-12')
        rendered = rendered.replace('{{ARTICLES_GRID_HTML}}', cards_html)
        rendered = rendered.replace('{{PAGINATION_HTML}}', pagination_html)
        rendered = rendered.replace('{{SIDEBAR_HTML}}', '')

        out_file.write_text(rendered, encoding='utf-8')

    print(f'Compiled blogs/index.html and {total_pages - 1} paginated pages with unified components.')

    # -------------------------------------------------------------------------
    # 2. Render All Category Pages
    # -------------------------------------------------------------------------
    rendered_cats = 0
    for slug, meta in CATEGORY_META.items():
        cat_dir = CATEGORY_DIR / slug
        cat_dir.mkdir(parents=True, exist_ok=True)
        cat_file = cat_dir / 'index.html'

        target_slugs = cat_posts_map.get(slug, [])
        cat_posts = [post_by_slug[s] for s in target_slugs if s in post_by_slug]
        if not cat_posts:
            cat_posts = [p for p in posts if p.get('category_url') == f'/category/{slug}/']

        if cat_posts:
            cards_html = '\n'.join([
                components.render_article_card(p, col_class="col-md-6 col-lg-6 mb-4")
                for p in cat_posts
            ])
        else:
            cards_html = components.render_empty_state(
                "No articles found in this category",
                "We are actively drafting guides and workouts for this section. Check back soon!",
                "Browse All Articles",
                "/blogs/"
            )

        cat_title = meta['title']
        cat_desc = meta['meta_description']
        cat_h1 = meta['h1']

        breadcrumbs_html = components.render_breadcrumbs([
            ('Home', '/'),
            ('Categories', '/blogs/'),
            (cat_h1, f'/category/{slug}/')
        ])

        archive_header_html = f'''<div class="falcon-archive-hero" style="background: linear-gradient(135deg, #4f46e5 0%, #3b82f6 100%); border-radius: 20px; padding: 48px 36px; color: #fff; margin-bottom: 30px; box-shadow: 0 10px 30px rgba(79, 70, 229, 0.15);">
    <div style="max-width: 600px;">
        <span style="background: rgba(255,255,255,0.2); padding: 6px 14px; border-radius: 20px; font-size: 13px; font-weight: 700; text-transform: uppercase;">Category Archive</span>
        <h1 style="color: #fff; font-size: 38px; margin: 16px 0 12px;">{html.escape(cat_h1)}</h1>
        <p style="color: rgba(255,255,255,0.9); font-size: 16px; margin: 0;">Browsing {len(cat_posts)} comprehensive articles, research-backed guides, and expert advice.</p>
    </div>
</div>'''

        cat_filter_bar_html = build_category_filter_bar(category_filter_data, active_slug=slug)
        in_page_filter_html = build_in_page_filter_row(len(cat_posts), f"articles in {cat_h1}")
        sidebar_html = build_sidebar(sidebar_recent_html, sidebar_categories_html, sidebar_newsletter_html)

        cat_page = template
        cat_page = cat_page.replace('{{META_TITLE}}', html.escape(cat_title))
        cat_page = cat_page.replace('{{META_DESCRIPTION}}', html.escape(cat_desc))
        cat_page = cat_page.replace('{{CANONICAL_URL}}', f'https://thefitnessfalcon.com/category/{slug}/')
        cat_page = cat_page.replace('{{PAGINATION_REL_LINKS}}', '')
        cat_page = cat_page.replace('{{BREADCRUMBS_HTML}}', breadcrumbs_html)
        cat_page = cat_page.replace('{{ARCHIVE_HEADER_HTML}}', archive_header_html)
        cat_page = cat_page.replace('{{CATEGORY_FILTER_BAR_HTML}}', cat_filter_bar_html)
        cat_page = cat_page.replace('{{FEATURED_CARD_HTML}}', '')
        cat_page = cat_page.replace('{{IN_PAGE_FILTER_HTML}}', in_page_filter_html)
        cat_page = cat_page.replace('{{GRID_COL_CLASS}}', 'col-lg-8')
        cat_page = cat_page.replace('{{ARTICLES_GRID_HTML}}', cards_html)
        cat_page = cat_page.replace('{{PAGINATION_HTML}}', '')
        cat_page = cat_page.replace('{{SIDEBAR_HTML}}', sidebar_html)

        cat_file.write_text(cat_page, encoding='utf-8')
        rendered_cats += 1

    print(f'Successfully compiled {rendered_cats} category archive pages using unified components.')

# -------------------------------------------------------------------------
# 3. Render Tag Archive Pages  (/tag/<slug>/[page/<n>/])
# -------------------------------------------------------------------------

def build_tag_map(posts):
    """Build {tag_slug: {name, posts[]}} from all post data."""
    tag_map = {}
    for post in posts:
        for raw_tag in post.get('tags', []):
            tag_name = str(raw_tag).strip()
            if not tag_name:
                continue
            tag_slug = slugify(tag_name)
            if not tag_slug:
                continue
            if tag_slug not in tag_map:
                tag_map[tag_slug] = {'name': tag_name, 'posts': []}
            if post not in tag_map[tag_slug]['posts']:
                tag_map[tag_slug]['posts'].append(post)
    return tag_map


def render_tag_archives(template, posts, sidebar_recent_html, sidebar_categories_html, sidebar_newsletter_html):
    tag_map = build_tag_map(posts)

    # Clean and recreate /tag/ directory
    if TAG_DIR.exists():
        shutil.rmtree(TAG_DIR)

    rendered_tags = 0
    rendered_pages = 0

    for tag_slug, tag_info in sorted(tag_map.items()):
        tag_name = tag_info['name']
        tag_posts = tag_info['posts']
        total_posts = len(tag_posts)
        total_pages = max(1, math.ceil(total_posts / POSTS_PER_PAGE))

        tag_base_url = f'/tag/{tag_slug}/'
        canonical_base = f'https://thefitnessfalcon.com/tag/{tag_slug}/'
        meta_title_base = f'#{tag_name} Articles - The Fitness Falcon'
        meta_desc = (
            f'Browse all {total_posts} article{"s" if total_posts != 1 else ""} tagged '
            f'#{tag_name} on The Fitness Falcon. Expert health, fitness, and wellness guides.'
        )

        archive_header_html = f'''<div class="falcon-archive-hero" style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); border-radius: 20px; padding: 48px 36px; color: #fff; margin-bottom: 30px; box-shadow: 0 10px 30px rgba(15, 23, 42, 0.2);">
    <div style="max-width: 600px;">
        <span style="background: rgba(255,255,255,0.1); padding: 6px 14px; border-radius: 20px; font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;">Tag Archive</span>
        <h1 style="color: #fff; font-size: 38px; margin: 16px 0 12px;">#{html.escape(tag_name)}</h1>
        <p style="color: rgba(255,255,255,0.8); font-size: 16px; margin: 0;">Browsing {total_posts} article{"s" if total_posts != 1 else ""} tagged with <strong>#{html.escape(tag_name)}</strong>.</p>
    </div>
</div>'''

        breadcrumbs_base = [
            ('Home', '/'),
            ('Tags', '/blogs/'),
            (f'#{tag_name}', tag_base_url)
        ]

        for page_num in range(1, total_pages + 1):
            start_idx = (page_num - 1) * POSTS_PER_PAGE
            end_idx = min(total_posts, start_idx + POSTS_PER_PAGE)
            page_posts = tag_posts[start_idx:end_idx]

            if page_num == 1:
                out_dir = TAG_DIR / tag_slug
                out_dir.mkdir(parents=True, exist_ok=True)
                out_file = out_dir / 'index.html'
                canonical_url = canonical_base
                page_title = meta_title_base
                page_desc = meta_desc
                breadcrumbs_html = components.render_breadcrumbs(breadcrumbs_base)
                rel_prev = ''
                rel_next = f'<link rel="next" href="{canonical_base}page/2/" />' if total_pages > 1 else ''
            else:
                out_dir = TAG_DIR / tag_slug / 'page' / str(page_num)
                out_dir.mkdir(parents=True, exist_ok=True)
                out_file = out_dir / 'index.html'
                canonical_url = f'{canonical_base}page/{page_num}/'
                page_title = f'#{tag_name} Articles - Page {page_num} of {total_pages} - The Fitness Falcon'
                page_desc = (
                    f'Browse all {total_posts} article{"s" if total_posts != 1 else ""} tagged '
                    f'#{tag_name} on The Fitness Falcon. Page {page_num} of {total_pages}.'
                )
                breadcrumbs_html = components.render_breadcrumbs(breadcrumbs_base + [
                    (f'Page {page_num}', f'{tag_base_url}page/{page_num}/')
                ])
                prev_href = canonical_base if page_num == 2 else f'{canonical_base}page/{page_num - 1}/'
                rel_prev = f'<link rel="prev" href="{prev_href}" />'
                rel_next = f'<link rel="next" href="{canonical_base}page/{page_num + 1}/" />' if page_num < total_pages else ''

            rel_links = '\n    '.join(filter(None, [rel_prev, rel_next])).strip()

            if page_posts:
                cards_html = '\n'.join([
                    components.render_article_card(p, col_class='col-md-6 col-lg-6 mb-4')
                    for p in page_posts
                ])
            else:
                cards_html = components.render_empty_state(
                    f'No articles tagged #{tag_name}',
                    'This tag currently has no published articles. Explore our full library.',
                    'Browse All Articles', '/blogs/'
                )

            pagination_html = components.render_pagination(
                current_page=page_num,
                total_pages=total_pages,
                base_url=tag_base_url,
                page_path_pattern=f'{tag_base_url}page/{{page}}/'
            )

            in_page_filter_html = build_in_page_filter_row(len(page_posts), f'articles tagged #{tag_name}')
            sidebar_html = build_sidebar(sidebar_recent_html, sidebar_categories_html, sidebar_newsletter_html)

            rendered = template
            rendered = rendered.replace('{{META_TITLE}}', html.escape(page_title))
            rendered = rendered.replace('{{META_DESCRIPTION}}', html.escape(page_desc))
            rendered = rendered.replace('{{CANONICAL_URL}}', canonical_url)
            rendered = rendered.replace('{{PAGINATION_REL_LINKS}}', rel_links)
            rendered = rendered.replace('{{BREADCRUMBS_HTML}}', breadcrumbs_html)
            rendered = rendered.replace('{{ARCHIVE_HEADER_HTML}}', archive_header_html)
            rendered = rendered.replace('{{CATEGORY_FILTER_BAR_HTML}}', '')
            rendered = rendered.replace('{{FEATURED_CARD_HTML}}', '')
            rendered = rendered.replace('{{IN_PAGE_FILTER_HTML}}', in_page_filter_html)
            rendered = rendered.replace('{{GRID_COL_CLASS}}', 'col-lg-8')
            rendered = rendered.replace('{{ARTICLES_GRID_HTML}}', cards_html)
            rendered = rendered.replace('{{PAGINATION_HTML}}', pagination_html)
            rendered = rendered.replace('{{SIDEBAR_HTML}}', sidebar_html)

            out_file.write_text(rendered, encoding='utf-8')
            rendered_pages += 1

        rendered_tags += 1

    print(f'Successfully compiled {rendered_tags} tag archives ({rendered_pages} total pages).')


# -------------------------------------------------------------------------
# 4. Render Author Archive Pages  (/author/<slug>/[page/<n>/])
# -------------------------------------------------------------------------

def build_author_map(posts):
    """Build {author_slug: {name, info, posts[]}} from all post data."""
    author_map = {}
    for post in posts:
        author_name = post.get('author', 'Dinesh').strip()
        if not author_name:
            continue
        author_slug = slugify(author_name)
        if not author_slug:
            continue
        if author_slug not in author_map:
            info = components.AUTHOR_INFO.get(author_name, {
                'role': 'Health & Fitness Contributor',
                'bio': f'{author_name} is a contributor at The Fitness Falcon.',
                'gradient': 'linear-gradient(135deg, #5541f8 0%, #3b82f6 100%)',
                'initial': author_name[0].upper() if author_name else 'F'
            })
            author_map[author_slug] = {'name': author_name, 'info': info, 'posts': []}
        if post not in author_map[author_slug]['posts']:
            author_map[author_slug]['posts'].append(post)
    return author_map


def render_author_archives(template, posts, sidebar_recent_html, sidebar_categories_html, sidebar_newsletter_html):
    author_map = build_author_map(posts)

    # Clean and recreate /author/ directory
    if AUTHOR_DIR.exists():
        shutil.rmtree(AUTHOR_DIR)

    rendered_authors = 0
    rendered_pages = 0

    for author_slug, author_data in sorted(author_map.items()):
        author_name = author_data['name']
        author_info = author_data['info']
        author_posts = author_data['posts']
        total_posts = len(author_posts)
        total_pages = max(1, math.ceil(total_posts / POSTS_PER_PAGE))

        author_base_url = f'/author/{author_slug}/'
        canonical_base = f'https://thefitnessfalcon.com/author/{author_slug}/'
        meta_title_base = f'{author_name} - Articles & Posts - The Fitness Falcon'
        meta_desc = (
            f'Read all {total_posts} article{"s" if total_posts != 1 else ""} by {author_name} '
            f'on The Fitness Falcon. Expert health, fitness, and wellness content.'
        )

        grad = author_info.get('gradient', 'linear-gradient(135deg, #5541f8 0%, #3b82f6 100%)')
        init = html.escape(author_info.get('initial', author_name[0].upper() if author_name else 'F'))
        safe_role = html.escape(author_info.get('role', 'Health & Fitness Contributor'))
        safe_bio = html.escape(author_info.get('bio', ''))
        safe_name = html.escape(author_name)

        archive_header_html = f'''<div class="falcon-archive-hero" style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); border-radius: 20px; padding: 48px 36px; color: #fff; margin-bottom: 30px; box-shadow: 0 10px 30px rgba(15, 23, 42, 0.2);">
    <div style="display: flex; align-items: center; gap: 28px; flex-wrap: wrap;">
        <div style="width: 80px; height: 80px; border-radius: 50%; background: {grad}; display: flex; align-items: center; justify-content: center; font-size: 32px; font-weight: 900; color: #fff; flex-shrink: 0;">{init}</div>
        <div style="flex: 1; min-width: 200px;">
            <span style="background: rgba(255,255,255,0.1); padding: 6px 14px; border-radius: 20px; font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;">Author</span>
            <h1 style="color: #fff; font-size: 38px; margin: 12px 0 6px;">{safe_name}</h1>
            <p style="color: rgba(255,255,255,0.7); font-size: 14px; font-weight: 600; margin: 0 0 10px; text-transform: uppercase; letter-spacing: 0.05em;">{safe_role}</p>
            <p style="color: rgba(255,255,255,0.85); font-size: 15px; margin: 0 0 12px; max-width: 560px;">{safe_bio}</p>
            <span style="color: rgba(255,255,255,0.6); font-size: 14px;"><i class="fal fa-file-alt" style="margin-right: 6px;"></i>{total_posts} published article{"s" if total_posts != 1 else ""}</span>
        </div>
    </div>
</div>'''

        breadcrumbs_base = [
            ('Home', '/'),
            ('Authors', '/blogs/'),
            (author_name, author_base_url)
        ]

        for page_num in range(1, total_pages + 1):
            start_idx = (page_num - 1) * POSTS_PER_PAGE
            end_idx = min(total_posts, start_idx + POSTS_PER_PAGE)
            page_posts = author_posts[start_idx:end_idx]

            if page_num == 1:
                out_dir = AUTHOR_DIR / author_slug
                out_dir.mkdir(parents=True, exist_ok=True)
                out_file = out_dir / 'index.html'
                canonical_url = canonical_base
                page_title = meta_title_base
                page_desc = meta_desc
                breadcrumbs_html = components.render_breadcrumbs(breadcrumbs_base)
                rel_prev = ''
                rel_next = f'<link rel="next" href="{canonical_base}page/2/" />' if total_pages > 1 else ''
            else:
                out_dir = AUTHOR_DIR / author_slug / 'page' / str(page_num)
                out_dir.mkdir(parents=True, exist_ok=True)
                out_file = out_dir / 'index.html'
                canonical_url = f'{canonical_base}page/{page_num}/'
                page_title = f'{author_name} - Page {page_num} of {total_pages} - The Fitness Falcon'
                page_desc = (
                    f'Read all {total_posts} article{"s" if total_posts != 1 else ""} by {author_name} '
                    f'on The Fitness Falcon. Page {page_num} of {total_pages}.'
                )
                breadcrumbs_html = components.render_breadcrumbs(breadcrumbs_base + [
                    (f'Page {page_num}', f'{author_base_url}page/{page_num}/')
                ])
                prev_href = canonical_base if page_num == 2 else f'{canonical_base}page/{page_num - 1}/'
                rel_prev = f'<link rel="prev" href="{prev_href}" />'
                rel_next = f'<link rel="next" href="{canonical_base}page/{page_num + 1}/" />' if page_num < total_pages else ''

            rel_links = '\n    '.join(filter(None, [rel_prev, rel_next])).strip()

            if page_posts:
                cards_html = '\n'.join([
                    components.render_article_card(p, col_class='col-md-6 col-lg-6 mb-4')
                    for p in page_posts
                ])
            else:
                cards_html = components.render_empty_state(
                    f'No articles by {author_name}',
                    'This author has no published articles yet.',
                    'Browse All Articles', '/blogs/'
                )

            pagination_html = components.render_pagination(
                current_page=page_num,
                total_pages=total_pages,
                base_url=author_base_url,
                page_path_pattern=f'{author_base_url}page/{{page}}/'
            )

            in_page_filter_html = build_in_page_filter_row(len(page_posts), f'articles by {author_name}')
            sidebar_html = build_sidebar(sidebar_recent_html, sidebar_categories_html, sidebar_newsletter_html)

            rendered = template
            rendered = rendered.replace('{{META_TITLE}}', html.escape(page_title))
            rendered = rendered.replace('{{META_DESCRIPTION}}', html.escape(page_desc))
            rendered = rendered.replace('{{CANONICAL_URL}}', canonical_url)
            rendered = rendered.replace('{{PAGINATION_REL_LINKS}}', rel_links)
            rendered = rendered.replace('{{BREADCRUMBS_HTML}}', breadcrumbs_html)
            rendered = rendered.replace('{{ARCHIVE_HEADER_HTML}}', archive_header_html)
            rendered = rendered.replace('{{CATEGORY_FILTER_BAR_HTML}}', '')
            rendered = rendered.replace('{{FEATURED_CARD_HTML}}', '')
            rendered = rendered.replace('{{IN_PAGE_FILTER_HTML}}', in_page_filter_html)
            rendered = rendered.replace('{{GRID_COL_CLASS}}', 'col-lg-8')
            rendered = rendered.replace('{{ARTICLES_GRID_HTML}}', cards_html)
            rendered = rendered.replace('{{PAGINATION_HTML}}', pagination_html)
            rendered = rendered.replace('{{SIDEBAR_HTML}}', sidebar_html)

            out_file.write_text(rendered, encoding='utf-8')
            rendered_pages += 1

        rendered_authors += 1

    print(f'Successfully compiled {rendered_authors} author archives ({rendered_pages} total pages).')


# -------------------------------------------------------------------------
# Main dispatcher
# -------------------------------------------------------------------------

def render_all_archives():
    """Run all archive renderers: blog, categories, tags, authors."""
    # 1 & 2: Blog archive + category archives (original function)
    _render_blogs_and_categories()

    # Shared data needed by tag/author renderers
    template = TEMPLATE_PATH.read_text(encoding='utf-8')
    posts = load_posts()

    cat_counts = {}
    cat_slug_map = {}
    for p in posts:
        c = p['category']
        cat_counts[c] = cat_counts.get(c, 0) + 1
        cat_slug_map[c] = p['category_url'].strip('/').split('/')[-1]
    sorted_cats = sorted(cat_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    category_filter_data = [(c, cat_slug_map[c], cnt) for c, cnt in sorted_cats]

    sidebar_recent_html = build_recent_widget(posts[:5])
    sidebar_categories_html = build_categories_widget(category_filter_data)
    sidebar_newsletter_html = components.render_newsletter_block()

    # 3: Tag archives
    render_tag_archives(template, posts, sidebar_recent_html, sidebar_categories_html, sidebar_newsletter_html)

    # 4: Author archives
    render_author_archives(template, posts, sidebar_recent_html, sidebar_categories_html, sidebar_newsletter_html)


if __name__ == '__main__':
    render_all_archives()
