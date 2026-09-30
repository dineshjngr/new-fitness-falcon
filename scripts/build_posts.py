#!/usr/bin/env python3
"""
The Fitness Falcon - Single Blog Post Compiler & Renderer
Compiles all posts from content/posts/*.json through components/post-template.html.
Ensures zero hardcoded layout duplication across the entire website.
"""
import os, sys, re, json, html
from pathlib import Path
from datetime import datetime
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = ROOT / 'components' / 'post-template.html'
CONTENT_DIR = ROOT / 'content' / 'posts'
BLOGS_DIR = ROOT / 'blogs'

def slugify(text):
    text = re.sub(r'<[^>]+>', '', text)
    text = html.unescape(text).strip().lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s-]+', '-', text)
    return text.strip('-')

def load_posts():
    posts = []
    for f in sorted(CONTENT_DIR.glob('*.json')):
        try:
            data = json.loads(f.read_text(encoding='utf-8'))
            posts.append(data)
        except Exception as e:
            print(f'Error reading {f}: {e}', file=sys.stderr)
    return posts

def generate_schema(post):
    schema = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "BlogPosting",
                "@id": f"{post['canonical_url']}#article",
                "isPartOf": {
                    "@type": "WebPage",
                    "@id": post['canonical_url']
                },
                "headline": post['title'],
                "description": post['description'],
                "inLanguage": "en-US",
                "mainEntityOfPage": post['canonical_url'],
                "datePublished": f"{post['published_iso']}T00:00:00+00:00",
                "dateModified": f"{post['modified_iso']}T00:00:00+00:00",
                "image": {
                    "@type": "ImageObject",
                    "url": f"https://thefitnessfalcon.com{post['featured_image']}",
                    "width": 1200,
                    "height": 675,
                    "caption": post.get('featured_image_alt', post['title'])
                },
                "author": {
                    "@type": "Person",
                    "name": post['author'],
                    "jobTitle": post.get('author_role', 'Health & Fitness Contributor'),
                    "description": post.get('author_bio', '')
                },
                "publisher": {
                    "@type": "Organization",
                    "name": "The Fitness Falcon",
                    "url": "https://thefitnessfalcon.com/",
                    "logo": {
                        "@type": "ImageObject",
                        "url": "https://thefitnessfalcon.com/assets/images/1.svg"
                    }
                },
                "articleSection": post['category'],
                "keywords": ", ".join(post.get('tags', []))
            },
            {
                "@type": "BreadcrumbList",
                "@id": f"{post['canonical_url']}#breadcrumb",
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": 1,
                        "name": "Home",
                        "item": "https://thefitnessfalcon.com/"
                    },
                    {
                        "@type": "ListItem",
                        "position": 2,
                        "name": post['category'],
                        "item": f"https://thefitnessfalcon.com{post['category_url']}"
                    },
                    {
                        "@type": "ListItem",
                        "position": 3,
                        "name": post['title'],
                        "item": post['canonical_url']
                    }
                ]
            }
        ]
    }
    return json.dumps(schema, indent=4, ensure_ascii=False)

def build_toc_and_content(content):
    # Find all h2 headings
    h2_pattern = re.compile(r'<h2([^>]*)>(.*?)</h2>', re.IGNORECASE | re.DOTALL)
    headings = []
    
    used_slugs = set()
    def replace_h2(match):
        attrs = match.group(1)
        inner = match.group(2)
        clean_text = re.sub(r'<[^>]+>', '', inner).strip()
        if not clean_text:
            return match.group(0)
            
        base_slug = slugify(clean_text) or 'section'
        s = base_slug
        idx = 2
        while s in used_slugs:
            s = f"{base_slug}-{idx}"
            idx += 1
        used_slugs.add(s)
        headings.append({'title': clean_text, 'slug': s})
        
        # Keep existing attributes if any, but ensure id is set
        if 'id=' in attrs:
            attrs = re.sub(r'id=[\"\'][^\"\']*[\"\']', f'id="{s}"', attrs)
        else:
            attrs = f' id="{s}"' + attrs
        return f'<h2{attrs}>{inner}</h2>'

    updated_content = h2_pattern.sub(replace_h2, content)

    # Wrap bare tables in .falcon-table-wrapper
    def wrap_table(match):
        start = match.start()
        prefix = updated_content[max(0, start - 80):start]
        if 'falcon-table-wrapper' in prefix:
            return match.group(0)
        return f'<div class="falcon-table-wrapper">\n{match.group(0)}\n</div>'
    
    updated_content = re.sub(r'<table\b[^>]*>.*?</table>', wrap_table, updated_content, flags=re.DOTALL | re.IGNORECASE)

    # Build TOC HTML if 3 or more headings
    if len(headings) >= 3:
        toc_items = '\n'.join([
            f'        <li><a href="#{h["slug"]}">{html.escape(h["title"])}</a></li>'
            for h in headings
        ])
        toc_html = f'''<nav class="falcon-toc" aria-label="Table of Contents">
    <div class="falcon-toc-header">
        <span class="falcon-toc-title"><i class="fal fa-list-ul"></i> Table of Contents</span>
        <button type="button" class="falcon-toc-toggle" id="falconTocToggle" aria-expanded="true" aria-controls="falconTocList">Hide</button>
    </div>
    <ol class="falcon-toc-list" id="falconTocList">
{toc_items}
    </ol>
</nav>'''
    else:
        toc_html = ''

    return toc_html, updated_content

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

def build_related_posts(current_slug, current_cat, all_posts):
    # 1. Match same category
    same_cat = [p for p in all_posts if p['slug'] != current_slug and p['category'] == current_cat]
    # 2. Backfill with recent if needed
    related = same_cat[:3]
    if len(related) < 3:
        seen = {p['slug'] for p in related}
        seen.add(current_slug)
        for p in all_posts:
            if p['slug'] not in seen:
                related.append(p)
                seen.add(p['slug'])
                if len(related) == 3:
                    break
                    
    cards = []
    for rel in related:
        cards.append(f'''        <div class="col-md-4 mb-4">
            <article class="post-card">
                <a href="/blogs/{rel['slug']}/">
                    <img src="{rel['featured_image']}" alt="{html.escape(rel['title'])}" class="post-card-thumb" loading="lazy" />
                </a>
                <div class="post-card-body">
                    <a href="{rel['category_url']}" class="category-badge">{html.escape(rel['category'])}</a>
                    <h4 class="post-card-title"><a href="/blogs/{rel['slug']}/">{html.escape(rel['title'])}</a></h4>
                    <div class="post-card-meta">
                        <span><i class="fal fa-calendar-alt"></i> {rel['published_date']}</span>
                        <span><i class="fal fa-clock"></i> {rel['read_time']} min read</span>
                    </div>
                </div>
            </article>
        </div>''')
    return '\n'.join(cards)

def build_pagination(prev_post, next_post):
    prev_html = ''
    next_html = ''
    if prev_post:
        prev_html = f'''<a href="/blogs/{prev_post['slug']}/" class="falcon-pagination-item falcon-pagination-prev">
    <span class="pagination-label"><i class="fal fa-arrow-left"></i> Previous Post</span>
    <span class="pagination-title">{html.escape(prev_post['title'])}</span>
</a>'''
    if next_post:
        next_html = f'''<a href="/blogs/{next_post['slug']}/" class="falcon-pagination-item falcon-pagination-next">
    <span class="pagination-label">Next Post <i class="fal fa-arrow-right"></i></span>
    <span class="pagination-title">{html.escape(next_post['title'])}</span>
</a>'''
    return prev_html, next_html

def build_tags(tags):
    if not tags:
        return ''
    badges = ' '.join([
        f'<span class="falcon-tag-badge">#{html.escape(t)}</span>'
        for t in tags
    ])
    return f'<div class="falcon-tags-list"><span class="falcon-tags-label"><i class="fal fa-tags"></i> Tags:</span> {badges}</div>'

def render_all_posts():
    template = TEMPLATE_PATH.read_text(encoding='utf-8')
    posts = load_posts()
    if not posts:
        raise ValueError('No posts loaded from content/posts/*.json!')
        
    print(f'Compiling {len(posts)} posts using master template {TEMPLATE_PATH.name}...')

    # Sort chronologically by published_iso, then slug
    posts.sort(key=lambda p: (p.get('published_iso', ''), p['slug']))

    # Sidebar data: recent posts (latest 5)
    recent_posts = list(reversed(posts))[:5]
    sidebar_recent_html = build_recent_widget(recent_posts)

    # Sidebar data: categories with counts
    cat_counts = {}
    cat_slug_map = {}
    for p in posts:
        c = p['category']
        cat_counts[c] = cat_counts.get(c, 0) + 1
        cat_slug_map[c] = p['category_url'].strip('/').split('/')[-1]
    sorted_cats = sorted(cat_counts.items(), key=lambda x: x[1], reverse=True)[:8]
    sidebar_cats_data = [(c, cat_slug_map[c], cnt) for c, cnt in sorted_cats]
    sidebar_categories_html = build_categories_widget(sidebar_cats_data)

    rendered_count = 0
    total = len(posts)

    for i, post in enumerate(posts):
        slug = post['slug']
        post_dir = BLOGS_DIR / slug
        post_dir.mkdir(parents=True, exist_ok=True)
        out_file = post_dir / 'index.html'

        prev_post = posts[i - 1] if i > 0 else None
        next_post = posts[i + 1] if i < total - 1 else None

        prev_html, next_html = build_pagination(prev_post, next_post)
        related_html = build_related_posts(slug, post['category'], list(reversed(posts)))
        tags_html = build_tags(post.get('tags', []))
        toc_html, entry_content = build_toc_and_content(post['content'])
        schema_json = generate_schema(post)

        # Truncate title for breadcrumbs if needed
        breadcrumb_title = post['title']
        if len(breadcrumb_title) > 42:
            breadcrumb_title = breadcrumb_title[:40].rstrip() + '...'

        # Updated date indicator
        updated_date_html = ''
        if post.get('modified_date') and post.get('modified_date') != post.get('published_date'):
            updated_date_html = f'''<span class="falcon-meta-updated">
                            <i class="fal fa-sync-alt"></i> Updated: {post['modified_date']}
                        </span>'''

        # Caption
        caption_html = ''
        if post.get('featured_image_caption'):
            caption_html = f'<figcaption class="falcon-image-caption">{html.escape(post["featured_image_caption"])}</figcaption>'

        # URL encodings for social share
        share_title_enc = quote(post['title'])
        share_url_enc = quote(post['canonical_url'])
        share_img_enc = quote(f"https://thefitnessfalcon.com{post['featured_image']}")

        client_payload = {
            'slug': post['slug'],
            'title': post['title'],
            'category': post['category'],
            'author': post['author'],
            'published_date': post['published_date'],
            'url': post['canonical_url']
        }

        # Replace all placeholders in template
        rendered = template
        rendered = rendered.replace('{{META_TITLE}}', html.escape(post['meta_title']))
        rendered = rendered.replace('{{META_DESCRIPTION}}', html.escape(post['description']))
        rendered = rendered.replace('{{ROBOTS_DIRECTIVES}}', 'index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1')
        rendered = rendered.replace('{{CANONICAL_URL}}', post['canonical_url'])
        rendered = rendered.replace('{{OG_IMAGE_URL}}', f"https://thefitnessfalcon.com{post['featured_image']}")
        rendered = rendered.replace('{{FEATURED_IMAGE}}', post['featured_image'])
        rendered = rendered.replace('{{FEATURED_IMAGE_ALT}}', html.escape(post.get('featured_image_alt', post['title'])))
        rendered = rendered.replace('{{FEATURED_IMAGE_CAPTION_HTML}}', caption_html)
        rendered = rendered.replace('{{PUBLISHED_ISO}}', post['published_iso'])
        rendered = rendered.replace('{{PUBLISHED_DATE}}', post['published_date'])
        rendered = rendered.replace('{{MODIFIED_ISO}}', post['modified_iso'])
        rendered = rendered.replace('{{MODIFIED_DATE}}', post['modified_date'])
        rendered = rendered.replace('{{UPDATED_DATE_HTML}}', updated_date_html)
        rendered = rendered.replace('{{AUTHOR_NAME}}', html.escape(post['author']))
        rendered = rendered.replace('{{AUTHOR_ROLE}}', html.escape(post.get('author_role', 'Health & Fitness Contributor')))
        rendered = rendered.replace('{{AUTHOR_BIO}}', html.escape(post.get('author_bio', '')))
        rendered = rendered.replace('{{AUTHOR_INITIAL}}', html.escape(post.get('author_initial', post['author'][0])))
        rendered = rendered.replace('{{AUTHOR_GRADIENT}}', post.get('author_gradient', 'linear-gradient(135deg, #5541f8 0%, #3b82f6 100%)'))
        rendered = rendered.replace('{{CATEGORY_NAME}}', html.escape(post['category']))
        rendered = rendered.replace('{{CATEGORY_URL}}', post['category_url'])
        rendered = rendered.replace('{{BREADCRUMB_TITLE}}', html.escape(breadcrumb_title))
        rendered = rendered.replace('{{POST_TITLE}}', html.escape(post['title']))
        rendered = rendered.replace('{{READ_TIME}}', str(post['read_time']))
        rendered = rendered.replace('{{COMMENTS_COUNT}}', str(post.get('comments_count', 0)))
        rendered = rendered.replace('{{TABLE_OF_CONTENTS_HTML}}', toc_html)
        rendered = rendered.replace('{{ENTRY_CONTENT}}', entry_content)
        rendered = rendered.replace('{{TAGS_HTML}}', tags_html)
        rendered = rendered.replace('{{SHARE_TITLE_ENCODED}}', share_title_enc)
        rendered = rendered.replace('{{SHARE_URL_ENCODED}}', share_url_enc)
        rendered = rendered.replace('{{SHARE_IMG_ENCODED}}', share_img_enc)
        rendered = rendered.replace('{{PREV_POST_HTML}}', prev_html)
        rendered = rendered.replace('{{NEXT_POST_HTML}}', next_html)
        rendered = rendered.replace('{{RELATED_POSTS_HTML}}', related_html)
        rendered = rendered.replace('{{SIDEBAR_RECENT_POSTS_HTML}}', sidebar_recent_html)
        rendered = rendered.replace('{{SIDEBAR_CATEGORIES_HTML}}', sidebar_categories_html)
        rendered = rendered.replace('{{SCHEMA_JSON_LD}}', schema_json)
        rendered = rendered.replace('{{POST_JSON_DATA}}', json.dumps(client_payload, indent=2))

        out_file.write_text(rendered, encoding='utf-8')
        rendered_count += 1

    print(f'Successfully compiled {rendered_count} single blog post pages.')

if __name__ == '__main__':
    render_all_posts()
