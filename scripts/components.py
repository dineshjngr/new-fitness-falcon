#!/usr/bin/env python3
"""
The Fitness Falcon - Centralized Shared Components Library
Provides standardized rendering functions for all 19 global blog components.
Reuses existing design tokens, components, and templates without repeating markup.
"""
import html, re
from urllib.parse import quote

AUTHOR_INFO = {
    'Dinesh': {
        'role': 'Senior Health & Fitness Editor',
        'bio': 'Senior contributor at The Fitness Falcon. Passionate about strength training, endurance performance, and evidence-based wellness strategies that empower everyday athletes.',
        'gradient': 'linear-gradient(135deg, #5541f8 0%, #3b82f6 100%)',
        'initial': 'D'
    },
    'Alex': {
        'role': 'Health Tech & Wearables Analyst',
        'bio': 'Fitness technology specialist and gear reviewer at The Fitness Falcon. Dedicated to demystifying biometric tracking, heart rate variability, and performance recovery tools.',
        'gradient': 'linear-gradient(135deg, #0ea5e9 0%, #2563eb 100%)',
        'initial': 'A'
    },
    'Riya Verma': {
        'role': 'Holistic Health & Nutrition Contributor',
        'bio': 'Nutrition and mindful living contributor at The Fitness Falcon. Specializes in whole-food recipes, gut health, stress resilience, and balanced daily wellness habits.',
        'gradient': 'linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%)',
        'initial': 'R'
    }
}

# 1. Category Badge
def render_category_badge(name, url=None, size='md'):
    safe_name = html.escape(name)
    size_cls = f' category-badge-{size}' if size in ('sm', 'lg') else ''
    if url:
        return f'<a href="{url}" class="category-badge{size_cls}">{safe_name}</a>'
    return f'<span class="category-badge{size_cls}">{safe_name}</span>'

# 2. Tag Badge
def render_tag_badge(tag):
    clean_tag = tag.lstrip('#').strip()
    return f'<span class="falcon-tag-badge">#{html.escape(clean_tag)}</span>'

# 3. Author Information (Inline Meta & Box)
def render_author_meta(author_name):
    safe_author = html.escape(author_name)
    return f'''<span class="meta-author" itemprop="author" itemscope itemtype="https://schema.org/Person">
  <i class="fal fa-user"></i> By <span itemprop="name">{safe_author}</span>
</span>'''

def render_author_box(author_name, role=None, bio=None, initial=None, gradient=None):
    author = AUTHOR_INFO.get(author_name, AUTHOR_INFO.get('Dinesh', {}))
    safe_name = html.escape(author_name)
    safe_role = html.escape(role or author.get('role', 'Health & Fitness Contributor'))
    safe_bio = html.escape(bio or author.get('bio', ''))
    init = html.escape(initial or author.get('initial', author_name[0] if author_name else 'F'))
    grad = gradient or author.get('gradient', 'linear-gradient(135deg, #5541f8 0%, #3b82f6 100%)')
    return f'''<div class="falcon-author-box">
  <div class="falcon-author-avatar" style="background: {grad};">
    {init}
  </div>
  <div class="falcon-author-info">
    <span class="falcon-author-badge">Verified Falcon Contributor</span>
    <h4 class="falcon-author-name">Written by {safe_name}</h4>
    <div class="falcon-author-role">{safe_role}</div>
    <p class="falcon-author-bio">{safe_bio}</p>
  </div>
</div>'''

# 4. Published / Updated Date
def render_date_meta(date_str, iso_date=None, modified_str=None, modified_iso=None):
    # Support (pub_iso, pub_date, mod_iso, mod_date) if called in reverse
    if date_str and re.match(r'^\d{4}-\d{2}-\d{2}', date_str):
        date_str, iso_date = iso_date, date_str
    if modified_str and re.match(r'^\d{4}-\d{2}-\d{2}', modified_str):
        modified_str, modified_iso = modified_iso, modified_str

    safe_date = html.escape(date_str or '')
    iso_attr = f' datetime="{iso_date}" itemprop="datePublished"' if iso_date else ' itemprop="datePublished"'
    date_html = f'<span><i class="fal fa-calendar-alt"></i> <time{iso_attr}>{safe_date}</time></span>'
    if modified_str and modified_str != date_str:
        mod_iso_attr = f' datetime="{modified_iso or iso_date}" itemprop="dateModified"' if (modified_iso or iso_date) else ' itemprop="dateModified"'
        date_html += f'\n<span class="falcon-meta-updated"><i class="fal fa-sync-alt"></i> Updated: <time{mod_iso_attr}>{html.escape(modified_str)}</time></span>'
    return date_html

# 5. Reading Time
def render_reading_time(read_time):
    return f'<span class="falcon-meta-read"><i class="fal fa-clock"></i> {read_time} min read</span>'

# 6. Featured Image
def render_featured_image(image_url, alt_text, caption=None, loading="lazy", eager=None):
    if eager is True or loading == "eager":
        loading_attr = 'loading="eager" fetchpriority="high"'
    else:
        loading_attr = 'loading="lazy"'
    safe_alt = html.escape(alt_text)
    caption_html = f'\n  <figcaption class="falcon-image-caption">{html.escape(caption)}</figcaption>' if caption else ''
    return f'''<figure class="falcon-featured-image-wrapper">
  <img src="{image_url}" alt="{safe_alt}" class="falcon-featured-image" {loading_attr} itemprop="image" />{caption_html}
</figure>'''

# 7. Breadcrumbs
def render_breadcrumbs(items):
    links = []
    total = len(items)
    for idx, item in enumerate(items):
        if isinstance(item, dict):
            label = item.get('name') or item.get('label') or ''
            url = item.get('url') or '/'
        elif isinstance(item, (tuple, list)):
            label = item[0]
            url = item[1] if len(item) > 1 else '/'
        else:
            label = str(item)
            url = '/'
        safe_label = html.escape(label)
        if idx == total - 1:
            links.append(f'<span class="current" aria-current="page">{safe_label}</span>')
        else:
            links.append(f'<a href="{url}">{safe_label}</a>')
            links.append('<span class="separator" aria-hidden="true">/</span>')
    return f'''<nav class="falcon-breadcrumb" aria-label="Breadcrumb">
  {' '.join(links)}
</nav>'''

# 8. Standard Article Card
def render_article_card(post, col_class="col-md-6 col-lg-4 mb-4", show_excerpt=True):
    slug = post['slug']
    title = html.escape(post['title'])
    image = post.get('featured_image', '/assets/images/1-1.png')
    alt = html.escape(post.get('featured_image_alt', post['title']))
    cat = html.escape(post.get('category', 'Fitness'))
    cat_url = post.get('category_url', '/category/fitness/')
    author = html.escape(post.get('author', 'Dinesh'))
    date = html.escape(post.get('published_date', ''))
    read_time = post.get('read_time', 4)

    excerpt_html = ''
    if show_excerpt and post.get('description'):
        clean_desc = html.escape(post['description'])
        if len(clean_desc) > 130:
            clean_desc = clean_desc[:126].rstrip() + '...'
        excerpt_html = f'<p class="post-card-excerpt">{clean_desc}</p>'

    card_markup = f'''<div class="{col_class}">
  <article class="falcon-card post-card" data-slug="{slug}">
    <a href="/blogs/{slug}/" class="falcon-card-media" aria-label="{title}">
      <img src="{image}" alt="{alt}" class="post-card-thumb" loading="lazy" />
    </a>
    <div class="post-card-body">
      <a href="{cat_url}" class="category-badge category-badge-sm">{cat}</a>
      <h3 class="post-card-title"><a href="/blogs/{slug}/">{title}</a></h3>
      {excerpt_html}
      <div class="post-card-meta">
        <span class="falcon-meta-author"><i class="fal fa-user"></i> {author}</span>
        <span class="falcon-meta-date"><i class="fal fa-calendar-alt"></i> {date}</span>
        <span class="falcon-meta-read"><i class="fal fa-clock"></i> {read_time} min read</span>
      </div>
    </div>
  </article>
</div>'''
    return card_markup

# 9. Featured Article Card
def render_featured_card(post):
    slug = post['slug']
    title = html.escape(post['title'])
    image = post.get('featured_image', '/assets/images/1-1.png')
    alt = html.escape(post.get('featured_image_alt', post['title']))
    cat = html.escape(post.get('category', 'Fitness'))
    cat_url = post.get('category_url', '/category/fitness/')
    author_name = post.get('author', 'Dinesh')
    author = AUTHOR_INFO.get(author_name, AUTHOR_INFO['Dinesh'])
    date = html.escape(post.get('published_date', ''))
    read_time = post.get('read_time', 4)
    excerpt = html.escape(post.get('description', ''))

    return f'''<article class="falcon-featured-card">
  <div class="falcon-featured-media">
    <a href="/blogs/{slug}/" aria-label="{title}">
      <img src="{image}" alt="{alt}" class="falcon-featured-thumb" loading="eager" />
    </a>
    <span class="falcon-featured-badge"><i class="far fa-star"></i> Featured Story</span>
  </div>
  <div class="falcon-featured-body">
    <a href="{cat_url}" class="category-badge category-badge-sm">{cat}</a>
    <h2 class="falcon-featured-title">
      <a href="/blogs/{slug}/">{title}</a>
    </h2>
    <p class="falcon-featured-excerpt">{excerpt}</p>
    <div class="falcon-featured-meta">
      <div class="falcon-author-compact">
        <span class="falcon-author-avatar-sm" style="background: {author['gradient']};">{author['initial']}</span>
        <span class="falcon-author-name-sm">By {html.escape(author_name)}</span>
      </div>
      <span class="falcon-meta-date"><i class="fal fa-calendar-alt"></i> {date}</span>
      <span class="falcon-meta-read"><i class="fal fa-clock"></i> {read_time} min read</span>
    </div>
    <div class="falcon-featured-action">
      <a href="/blogs/{slug}/" class="falcon-btn falcon-btn-primary falcon-btn-sm">Read Article <i class="fal fa-arrow-right"></i></a>
    </div>
  </div>
</article>'''

# 10. Related Post Card
def render_related_card(post, col_class="col-md-4 mb-4"):
    slug = post['slug']
    title = html.escape(post['title'])
    image = post.get('featured_image', '/assets/images/1-1.png')
    alt = html.escape(post.get('featured_image_alt', post['title']))
    cat = html.escape(post.get('category', 'Fitness'))
    cat_url = post.get('category_url', '/category/fitness/')
    date = html.escape(post.get('published_date', ''))
    read_time = post.get('read_time', 4)

    return f'''<div class="{col_class}">
  <article class="falcon-related-card post-card" data-slug="{slug}">
    <a href="/blogs/{slug}/" class="falcon-card-media" aria-label="{title}">
      <img src="{image}" alt="{alt}" class="post-card-thumb" loading="lazy" />
    </a>
    <div class="post-card-body">
      <a href="{cat_url}" class="category-badge category-badge-sm">{cat}</a>
      <h4 class="post-card-title"><a href="/blogs/{slug}/">{title}</a></h4>
      <div class="post-card-meta">
        <span class="falcon-meta-date"><i class="fal fa-calendar-alt"></i> {date}</span>
        <span class="falcon-meta-read"><i class="fal fa-clock"></i> {read_time} min read</span>
      </div>
    </div>
  </article>
</div>'''

# 11. Pagination (Archive)
def render_pagination(current_page, total_pages, base_url="/blogs/", page_path_pattern="/blogs/page/{page}/"):
    if total_pages <= 1:
        return ''

    def get_url(p):
        if p == 1:
            return base_url if base_url.endswith('/') else f"{base_url}/"
        return page_path_pattern.replace('{page}', str(p))

    items = []
    # Prev link
    prev_class = 'disabled' if current_page <= 1 else ''
    prev_url = get_url(current_page - 1) if current_page > 1 else "javascript:void(0)"
    items.append(f'<li class="{prev_class}"><a href="{prev_url}" aria-label="Previous page"><i class="fal fa-arrow-left"></i> Previous</a></li>')

    # Calculate page numbers with ellipsis window
    if total_pages <= 7:
        page_numbers = list(range(1, total_pages + 1))
    else:
        if current_page <= 4:
            page_numbers = [1, 2, 3, 4, 5, '...', total_pages]
        elif current_page >= total_pages - 3:
            page_numbers = [1, '...', total_pages - 4, total_pages - 3, total_pages - 2, total_pages - 1, total_pages]
        else:
            page_numbers = [1, '...', current_page - 1, current_page, current_page + 1, '...', total_pages]

    for p in page_numbers:
        if p == '...':
            items.append('<li class="pagination-ellipsis"><span aria-hidden="true">&hellip;</span></li>')
        elif p == current_page:
            items.append(f'<li class="active"><span aria-current="page">{p}</span></li>')
        else:
            items.append(f'<li><a href="{get_url(p)}">{p}</a></li>')

    # Next link
    next_class = 'disabled' if current_page >= total_pages else ''
    next_url = get_url(current_page + 1) if current_page < total_pages else "javascript:void(0)"
    items.append(f'<li class="{next_class}"><a href="{next_url}" aria-label="Next page">Next <i class="fal fa-arrow-right"></i></a></li>')

    return f'''<nav class="falcon-pagination" aria-label="Page navigation">
  <ul class="falcon-pagination-list">
    {' '.join(items)}
  </ul>
</nav>'''

# 12. Post Pagination (Previous / Next Article)
def render_post_pagination(prev_post, next_post):
    prev_html = ''
    next_html = ''
    if prev_post:
        prev_title = html.escape(prev_post['title'])
        prev_html = f'''<a href="/blogs/{prev_post['slug']}/" class="falcon-pagination-item falcon-pagination-prev">
  <span class="pagination-label"><i class="fal fa-arrow-left"></i> Previous Post</span>
  <span class="pagination-title">{prev_title}</span>
</a>'''
    if next_post:
        next_title = html.escape(next_post['title'])
        next_html = f'''<a href="/blogs/{next_post['slug']}/" class="falcon-pagination-item falcon-pagination-next">
  <span class="pagination-label">Next Post <i class="fal fa-arrow-right"></i></span>
  <span class="pagination-title">{next_title}</span>
</a>'''
    return f'''<nav class="falcon-post-pagination" aria-label="Article navigation">
  {prev_html}
  {next_html}
</nav>'''

# 13. Table of Contents
def render_toc(headings):
    if len(headings) < 3:
        return ''
    items = '\n'.join([
        f'    <li><a href="#{h["slug"]}">{html.escape(h["title"])}</a></li>'
        for h in headings
    ])
    return f'''<nav class="falcon-toc" aria-label="Table of Contents">
  <div class="falcon-toc-header">
    <span class="falcon-toc-title"><i class="fal fa-list-ul"></i> Table of Contents</span>
    <button type="button" class="falcon-toc-toggle" id="falconTocToggle" aria-expanded="true" aria-controls="falconTocList">Hide</button>
  </div>
  <ol class="falcon-toc-list" id="falconTocList">
{items}
  </ol>
</nav>'''

# 14. Social Sharing Toolbar
def render_social_share(title, canonical_url, image_url=None):
    share_title = quote(title)
    share_url = quote(canonical_url)
    share_img = quote(image_url or "https://thefitnessfalcon.com/assets/images/1.svg")
    return f'''<div class="falcon-social-share" aria-label="Share this article">
  <div class="falcon-social-share-title">
    <i class="fal fa-share-alt"></i>
    <span>Share this article:</span>
  </div>
  <div class="falcon-social-buttons">
    <a href="https://twitter.com/intent/tweet?text={share_title}&url={share_url}" target="_blank" rel="noopener noreferrer" class="falcon-share-btn share-x" aria-label="Share on X (Twitter)">
      <i class="fab fa-x-twitter"></i>
    </a>
    <a href="https://www.facebook.com/sharer/sharer.php?u={share_url}" target="_blank" rel="noopener noreferrer" class="falcon-share-btn share-facebook" aria-label="Share on Facebook">
      <i class="fab fa-facebook-f"></i>
    </a>
    <a href="https://www.linkedin.com/sharing/share-offsite/?url={share_url}" target="_blank" rel="noopener noreferrer" class="falcon-share-btn share-linkedin" aria-label="Share on LinkedIn">
      <i class="fab fa-linkedin-in"></i>
    </a>
    <a href="https://pinterest.com/pin/create/button/?url={share_url}&media={share_img}&description={share_title}" target="_blank" rel="noopener noreferrer" class="falcon-share-btn share-pinterest" aria-label="Pin on Pinterest">
      <i class="fab fa-pinterest-p"></i>
    </a>
    <a href="https://api.whatsapp.com/send?text={share_title}%20{share_url}" target="_blank" rel="noopener noreferrer" class="falcon-share-btn share-whatsapp" aria-label="Share via WhatsApp">
      <i class="fab fa-whatsapp"></i>
    </a>
    <button type="button" class="falcon-share-btn share-copy" id="falconCopyLinkBtn" data-url="{canonical_url}" aria-label="Copy article link">
      <i class="fal fa-link"></i>
      <span class="falcon-copy-tooltip" id="falconCopyTooltip">Link copied!</span>
    </button>
  </div>
</div>'''

# 15. CTA Banner
def render_cta_banner(eyebrow, title, description, button_text="Get Started", button_url="/blogs/"):
    return f'''<section class="falcon-cta" aria-label="Call to action">
  <div class="container">
    <div class="falcon-cta-inner">
      <span class="falcon-cta-eyebrow">{html.escape(eyebrow)}</span>
      <h2 class="falcon-cta-title">{html.escape(title)}</h2>
      <p class="falcon-cta-description">{html.escape(description)}</p>
      <div class="falcon-cta-actions">
        <a href="{button_url}" class="falcon-btn falcon-btn-primary falcon-btn-lg">{html.escape(button_text)}</a>
      </div>
    </div>
  </div>
</section>'''

# 16. Newsletter Block (Sidebar / Footer)
def render_newsletter_block(title="Daily Fitness Digest", description="Get top health tips, workouts, and wellness guides straight to your inbox.", button_text="Subscribe Free"):
    return f'''<div class="falcon-newsletter-card falcon-sidebar-cta" aria-label="Newsletter subscription">
  <i class="far fa-envelope-open-text" aria-hidden="true"></i>
  <h3 class="falcon-newsletter-title">{html.escape(title)}</h3>
  <p class="falcon-newsletter-description">{html.escape(description)}</p>
  <form class="falcon-newsletter-form-box" onsubmit="event.preventDefault(); var m = this.querySelector('.falcon-newsletter-msg'); if(m) m.style.display='block';">
    <div style="display: flex; gap: 8px; width: 100%;">
      <input type="email" placeholder="Your email address" required aria-label="Email address" style="flex: 1;" />
      <button type="submit">{html.escape(button_text)}</button>
    </div>
    <span class="falcon-newsletter-msg" style="display: none; font-size: 13px; color: #e2e8f0; margin-top: 10px; line-height: 1.4;">Newsletter delivery integration is currently being configured for production. Reach out directly to <a href="mailto:info@thefitnessfalcon.com" style="color: #fff; text-decoration: underline;">info@thefitnessfalcon.com</a> to stay updated.</span>
  </form>
</div>'''

# 17. FAQ Block
def render_faq_block(faqs):
    items = []
    for idx, f in enumerate(faqs):
        q = html.escape(f['question'])
        a = html.escape(f['answer'])
        items.append(f'''    <div class="falcon-faq-item">
      <button type="button" class="falcon-faq-question" aria-expanded="false" aria-controls="faq-ans-{idx}">
        <span>{q}</span>
        <i class="fal fa-chevron-down" aria-hidden="true"></i>
      </button>
      <div class="falcon-faq-answer" id="faq-ans-{idx}">
        <p>{a}</p>
      </div>
    </div>''')
    return f'''<section class="falcon-faq-section" aria-label="Frequently Asked Questions">
  <div class="falcon-faq-header">
    <h3 class="falcon-faq-title"><i class="fal fa-question-circle"></i> Frequently Asked Questions</h3>
  </div>
  <div class="falcon-faq-list">
{chr(10).join(items)}
  </div>
</section>'''

# 18. Related Articles Section
def render_related_section(related_posts, title="Related Articles"):
    cards = [render_related_card(p) for p in related_posts]
    return f'''<section class="falcon-related-section" aria-label="Related articles">
  <h3 class="falcon-section-heading">{html.escape(title)}</h3>
  <div class="row">
    {''.join(cards)}
  </div>
</section>'''

# 19. Empty State
def render_empty_state(title="No articles found", description="Try another search term or browse our categories to explore more.", action_text="Browse All Articles", action_url="/blogs/", icon="fal fa-search"):
    return f'''<div class="falcon-empty-state" role="status">
  <div class="falcon-empty-icon">
    <i class="{icon}" aria-hidden="true"></i>
  </div>
  <h3 class="falcon-empty-title">{html.escape(title)}</h3>
  <p class="falcon-empty-description">{html.escape(description)}</p>
  <a href="{action_url}" class="falcon-btn falcon-btn-primary falcon-btn-sm">{html.escape(action_text)}</a>
</div>'''

# 20. Search Result Card
def render_search_result_card(post):
    slug = post['slug']
    title = html.escape(post['title'])
    thumb = html.escape(post.get('thumb', '1-1.png'))
    cat = html.escape(post.get('cat', 'Fitness'))
    date = html.escape(post.get('date', ''))
    return f'''<a href="/blogs/{slug}/" class="falcon-search-card" aria-label="{title}">
  <img src="/assets/images/{thumb}" alt="" class="falcon-search-thumb" loading="lazy" width="54" height="54" />
  <div class="falcon-search-content">
    <h4 class="falcon-search-title">{title}</h4>
    <div class="falcon-search-meta">
      <span class="falcon-search-cat">{cat}</span>
      <span class="falcon-search-separator">&bull;</span>
      <span class="falcon-search-date">{date}</span>
    </div>
  </div>
</a>'''
