#!/usr/bin/env python3
"""
The Fitness Falcon - Single Blog Post Compiler & Renderer
Compiles all posts from content/posts/*.json through components/post-template.html.
Ensures zero hardcoded layout duplication across the entire website by leveraging
scripts/components.py for all shared UI blocks.
"""
import os, sys, re, json, html
from pathlib import Path
from datetime import datetime
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import scripts.components as components
from scripts.editorial import normalize_author, clean_article_html, author_slug

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
            posts.append(normalize_author(data))
        except Exception as e:
            print(f'Error reading {f}: {e}', file=sys.stderr)
    return posts

def build_cluster_navigation(post, posts):
    """Connect articles sharing an explicitly assigned editorial topic cluster."""
    cluster = post.get('cluster_id')
    if not cluster:
        return ''
    peers = [p for p in posts if p.get('cluster_id') == cluster and p['slug'] != post['slug']]
    peers.sort(key=lambda p: (p.get('cluster_role') != 'hub', p['title']))
    if not peers:
        raise ValueError(f"{post['slug']}: topic cluster has no other articles")
    items = ''.join(f'<li><a href="/blogs/{p["slug"]}/">{html.escape(p["title"])}</a></li>' for p in peers)
    return '<h2>Explore the walking-pad desk guide</h2><p>Choose the next question you want to solve:</p><ul>' + items + '</ul>'

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
                "datePublished": post.get('published_time') or f"{post['published_iso']}T00:00:00+00:00",
                "dateModified": post.get('modified_time') or f"{post['modified_iso']}T00:00:00+00:00",
                "image": {
                    "@type": "ImageObject",
                    "url": f"https://thefitnessfalcon.com{post['featured_image']}",
                    "width": post.get('featured_image_width', 1200),
                    "height": post.get('featured_image_height', 675),
                    "caption": post.get('featured_image_alt', post['title'])
                },
                "author": {
                    "@type": "Person" if post['author'] == "Dinesh Jeengar" else "Organization",
                    "url": "https://thefitnessfalcon.com/author/" + author_slug(post['author']) + "/",
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
    article = schema['@graph'][0]
    if article['author']['@type'] == 'Organization':
        article['author'].pop('jobTitle', None)
    if post.get('sources'):
        article['citation'] = post['sources']
    return json.dumps(schema, indent=4, ensure_ascii=False)


CALLOUT_LABELS = {
    'note': 'note', 'tip': 'tip', 'important': 'warning', 'warning': 'warning',
    'safety': 'warning', 'safety note': 'warning', 'medical note': 'warning',
    'disclaimer': 'info', 'how this review was made': 'info',
    'how we researched this': 'info', 'how this guide was researched': 'info',
    'bottom line': 'tip', 'the bottom line': 'tip',
    'pro tip': 'tip', 'tips': 'tip', 'caution': 'warning', 'warning signs': 'warning',
    'evidence and limitations': 'info', 'myth': 'note', 'fact': 'tip', 'truth': 'tip',
}


def render_key_takeaways(items):
    if not items:
        return ''
    lis = '\n'.join(f'    <li>{html.escape(t)}</li>' for t in items)
    return f'''<aside class="falcon-takeaways" aria-label="Key takeaways">
  <p class="falcon-takeaways-title"><i class="fal fa-bolt" aria-hidden="true"></i> Key takeaways</p>
  <ul>
{lis}
  </ul>
</aside>
'''


def enhance_article_html(content):
    """Presentational upgrades applied at build time; article text is unchanged."""
    # Callouts: paragraphs that open with a bold label such as "Note:".
    def callout(m):
        label = re.sub(r'<[^>]+>', '', m.group(2)).strip().rstrip(':').strip().lower()
        kind = CALLOUT_LABELS.get(label)
        if not kind:
            return m.group(0)
        return f'<div class="falcon-callout falcon-callout--{kind}">{m.group(0)}</div>'
    content = re.sub(r'<p>(<strong>([^<]{2,40}?):?</strong>:?)(.*?)</p>', callout, content, flags=re.S)

    # FAQ accordions: H3 questions under an FAQ H2 become <details> items.
    faq = re.search(r'(<h2[^>]*>[^<]*(?:Frequently asked questions|FAQs?)\b[^<]*</h2>)(.*?)(?=<h2\b|$)', content, flags=re.S | re.I)
    if faq and '<h3' in faq.group(2):
        body = faq.group(2)
        first = body.find('<h3')
        intro, rest = body[:first], body[first:]
        items = re.split(r'(?=<h3\b)', rest)
        out = []
        for item in items:
            if not item.strip():
                continue
            qm = re.match(r'(<h3[^>]*>.*?</h3>)(.*)', item, flags=re.S)
            if not qm:
                out.append(item)
                continue
            out.append(f'<details class="falcon-faq-item"><summary>{qm.group(1)}</summary><div class="falcon-faq-answer">{qm.group(2).strip()}</div></details>\n')
        content = content[:faq.start()] + faq.group(1) + intro + '<div class="falcon-faq-list">\n' + ''.join(out) + '</div>\n' + content[faq.end():]
    return content

def build_toc_and_content(content):
    # Demote any rogue <h1> inside the article content to <h2> to maintain single H1 hierarchy
    content = re.sub(r'<h1\b([^>]*)>(.*?)</h1>', r'<h2\1>\2</h2>', content, flags=re.IGNORECASE | re.DOTALL)

    # Ensure all <img> tags have an alt attribute
    def ensure_img_alt(m):
        tag = m.group(0)
        if 'alt=' not in tag.lower():
            if tag.endswith('/>'):
                return tag[:-2] + ' alt="" />'
            elif tag.endswith('>'):
                return tag[:-1] + ' alt="">'
        return tag
    content = re.sub(r'<img\b[^>]*>', ensure_img_alt, content, flags=re.IGNORECASE)

    # Include the full heading hierarchy and keep existing public h2 anchors stable.
    heading_pattern = re.compile(r'<h([2-6])\b([^>]*)>(.*?)</h\1>', re.IGNORECASE | re.DOTALL)
    id_pattern = re.compile(r'(?<![\w:-])id\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|([^\s>]+))', re.IGNORECASE)
    headings = []
    matches = list(heading_pattern.finditer(content))
    # Reserve IDs outside headings so generated anchors cannot collide with other elements.
    non_heading_content = heading_pattern.sub('', content)
    used_slugs = {html.unescape(next(value for value in m.groups() if value is not None))
                  for m in id_pattern.finditer(non_heading_content)}
    assigned = {}

    def assign_id(match):
        level, attrs, inner = match.groups()
        clean_text = html.unescape(re.sub(r'<[^>]+>', '', inner)).strip()
        if not clean_text:
            return
        existing = id_pattern.search(attrs)
        # h2 links already published by the old builder used title-based slugs.
        base_slug = (html.unescape(next(v for v in existing.groups() if v is not None))
                     if level != '2' and existing else slugify(clean_text)) or 'section'
        section_id = base_slug
        idx = 2
        while section_id in used_slugs:
            section_id = f"{base_slug}-{idx}"
            idx += 1
        used_slugs.add(section_id)
        assigned[match.start()] = {'title': clean_text, 'slug': section_id, 'level': int(level)}

    # Allocate h2 IDs first; adding subheadings must not change existing deep links.
    for match in matches:
        if match.group(1) == '2':
            assign_id(match)
    for match in matches:
        if match.group(1) != '2':
            assign_id(match)

    def replace_heading(match):
        heading = assigned.get(match.start())
        if not heading:
            return match.group(0)
        level, attrs, inner = match.groups()
        attrs = id_pattern.sub('', attrs)
        headings.append(heading)
        return f'<h{level} id="{html.escape(heading["slug"], quote=True)}"{attrs}>{inner}</h{level}>'

    updated_content = heading_pattern.sub(replace_heading, content)

    # Wrap bare tables in .falcon-table-wrapper
    def wrap_table(match):
        start = match.start()
        prefix = updated_content[max(0, start - 80):start]
        if 'falcon-table-wrapper' in prefix:
            return match.group(0)
        return f'<div class="falcon-table-wrapper">\n{match.group(0)}\n</div>'
    
    updated_content = re.sub(r'<table\b[^>]*>.*?</table>', wrap_table, updated_content, flags=re.DOTALL | re.IGNORECASE)

    # Standardized Table of Contents component
    toc_html = components.render_toc(headings)

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

def build_tags(tags):
    if not tags:
        return ''
    badges = ' '.join([components.render_tag_badge(t) for t in tags])
    return f'<div class="falcon-tags-list"><span class="falcon-tags-label"><i class="fal fa-tags"></i> Tags:</span> {badges}</div>'

def render_all_posts():
    template = TEMPLATE_PATH.read_text(encoding='utf-8')
    posts = load_posts()
    if not posts:
        raise ValueError('No posts loaded from content/posts/*.json!')
        
    print(f'Compiling {len(posts)} posts using master template {TEMPLATE_PATH.name}...')

    # Sort chronologically by true published timestamp, then slug
    posts.sort(key=lambda p: (p.get('published_time') or p.get('published_iso', ''), p['slug']))

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
    from scripts.build_archives import category_filter_data_for
    sidebar_cats_data = category_filter_data_for(posts)[:8]
    sidebar_categories_html = build_categories_widget(sidebar_cats_data)
    sidebar_newsletter_html = components.render_newsletter_block()

    rendered_count = 0
    total = len(posts)

    for i, post in enumerate(posts):
        slug = post['slug']
        post_dir = BLOGS_DIR / slug
        post_dir.mkdir(parents=True, exist_ok=True)
        out_file = post_dir / 'index.html'

        prev_post = posts[i - 1] if i > 0 else None
        next_post = posts[i + 1] if i < total - 1 else None

        # Truncate title for breadcrumbs if needed
        breadcrumb_title = post['title']
        if len(breadcrumb_title) > 42:
            breadcrumb_title = breadcrumb_title[:40].rstrip() + '...'

        # Render standardized components
        breadcrumbs_html = components.render_breadcrumbs([
            {'name': 'Home', 'url': '/'},
            {'name': post['category'], 'url': post['category_url']},
            {'name': breadcrumb_title}
        ])
        cat_badge_html = components.render_category_badge(post['category'], post['category_url'])
        author_meta_html = components.render_author_meta(post['author'])
        date_meta_html = components.render_date_meta(
            post['published_date'],
            post.get('published_time') or post.get('published_iso'),
            post.get('modified_date'),
            post.get('modified_time') or post.get('modified_iso')
        )
        reading_time_html = components.render_reading_time(post['read_time'])
        featured_image_html = components.render_featured_image(
            post['featured_image'],
            post.get('featured_image_alt', post['title']),
            post.get('featured_image_caption'),
            loading="eager",
            width=post.get('featured_image_width'),
            height=post.get('featured_image_height')
        )
        tags_html = build_tags(post.get('tags', []))
        article_body = enhance_article_html(clean_article_html(post['content']))
        takeaways = render_key_takeaways(post.get('key_takeaways'))
        if takeaways:
            # After the opening answer paragraph, before the first section.
            cut = article_body.find('</p>')
            cut = cut + 4 if 0 <= cut < article_body.find('<h2') else 0
            article_body = article_body[:cut] + '\n' + takeaways + article_body[cut:]
        article_content = article_body + build_cluster_navigation(post, posts)
        toc_html, entry_content = build_toc_and_content(article_content)
        social_share_html = components.render_social_share(
            post['title'],
            post['canonical_url'],
            f"https://thefitnessfalcon.com{post['featured_image']}"
        )
        author_box_html = components.render_author_box(
            post['author'],
            post.get('author_role', 'Health & Fitness Contributor'),
            post.get('author_bio', ''),
            post.get('author_initial', post['author'][0]),
            post.get('author_gradient')
        )
        post_pagination_html = components.render_post_pagination(prev_post, next_post)

        # Related posts (3 items, prefer same category)
        cluster_peers = [p for p in reversed(posts) if p['slug'] != slug
                         and post.get('cluster_id') and p.get('cluster_id') == post['cluster_id']]
        cluster_peers.sort(key=lambda p: p.get('cluster_role') != 'hub')
        same_cat = [p for p in reversed(posts) if p['slug'] != slug and p['category'] == post['category']]
        related = cluster_peers[:3]
        for candidate in same_cat:
            if len(related) == 3:
                break
            if candidate['slug'] not in {p['slug'] for p in related}:
                related.append(candidate)
        if len(related) < 3:
            seen = {p['slug'] for p in related}
            seen.add(slug)
            for p in reversed(posts):
                if p['slug'] not in seen:
                    related.append(p)
                    seen.add(p['slug'])
                    if len(related) == 3:
                        break
        related_section_html = components.render_related_section(related, "Related Articles")
        schema_json = generate_schema(post)

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
        rendered = rendered.replace('{{OG_IMAGE_WIDTH}}', str(post.get('featured_image_width', 1200)))
        rendered = rendered.replace('{{OG_IMAGE_HEIGHT}}', str(post.get('featured_image_height', 675)))
        rendered = rendered.replace('{{BREADCRUMBS_HTML}}', breadcrumbs_html)
        rendered = rendered.replace('{{CATEGORY_BADGE_HTML}}', cat_badge_html)
        rendered = rendered.replace('{{POST_TITLE}}', html.escape(post['title']))
        rendered = rendered.replace('{{AUTHOR_META_HTML}}', author_meta_html)
        rendered = rendered.replace('{{DATE_META_HTML}}', date_meta_html)
        rendered = rendered.replace('{{READING_TIME_HTML}}', reading_time_html)
        rendered = rendered.replace('{{COMMENTS_COUNT}}', str(post.get('comments_count', 0)))
        rendered = rendered.replace('{{FEATURED_IMAGE_HTML}}', featured_image_html)
        rendered = rendered.replace('{{TOC_CONTAINER_CLASS}}', 'falcon-has-toc' if toc_html else '')
        rendered = rendered.replace('{{TOC_LAYOUT_CLASS}}', 'has-toc' if toc_html else '')
        toc_column = f'<aside class="falcon-toc-column" aria-label="Article navigation">{toc_html}</aside>' if toc_html else ''
        rendered = rendered.replace('{{TABLE_OF_CONTENTS_COLUMN}}', toc_column)
        rendered = rendered.replace('{{ENTRY_CONTENT}}', entry_content)
        rendered = rendered.replace('{{POST_DEK}}', html.escape(post.get('description', '')))
        rendered = rendered.replace('{{AUTHOR_INITIAL}}', html.escape(post.get('author_initial') or post['author'][0]))
        rendered = rendered.replace('{{TAGS_HTML}}', tags_html)
        rendered = rendered.replace('{{SOCIAL_SHARE_HTML}}', social_share_html)
        rendered = rendered.replace('{{AUTHOR_BOX_HTML}}', author_box_html)
        rendered = rendered.replace('{{POST_PAGINATION_HTML}}', post_pagination_html)
        rendered = rendered.replace('{{RELATED_SECTION_HTML}}', related_section_html)
        rendered = rendered.replace('{{SIDEBAR_RECENT_POSTS_HTML}}', sidebar_recent_html)
        rendered = rendered.replace('{{SIDEBAR_CATEGORIES_HTML}}', sidebar_categories_html)
        rendered = rendered.replace('{{SIDEBAR_NEWSLETTER_HTML}}', sidebar_newsletter_html)
        rendered = rendered.replace('{{SCHEMA_JSON_LD}}', schema_json)
        rendered = rendered.replace('{{POST_JSON_DATA}}', json.dumps(client_payload, indent=2))
        rendered = rendered.replace('{{FEATURED_IMAGE_ALT}}', html.escape(post.get('featured_image_alt', post['title'])))
        rendered = rendered.replace('{{PUBLISHED_ISO}}', post.get('published_iso', ''))
        rendered = rendered.replace('{{MODIFIED_ISO}}', post.get('modified_iso', post.get('published_iso', '')))
        rendered = rendered.replace('{{PUBLISHED_TIME}}', post.get('published_time') or f"{post['published_iso']}T00:00:00+00:00")
        rendered = rendered.replace('{{MODIFIED_TIME}}', post.get('modified_time') or f"{post.get('modified_iso', post['published_iso'])}T00:00:00+00:00")
        rendered = rendered.replace('{{AUTHOR_NAME}}', html.escape(post.get('author', 'Dinesh')))
        rendered = rendered.replace('{{CATEGORY_NAME}}', html.escape(post.get('category', 'Fitness')))

        out_file.write_text(rendered, encoding='utf-8')
        rendered_count += 1

    print(f'Successfully compiled {rendered_count} single blog post pages using unified components.')

if __name__ == '__main__':
    render_all_posts()
