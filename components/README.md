# The Fitness Falcon - Global Component & Architecture System

This directory houses the shared global architecture for The Fitness Falcon.

The entire website uses:
- **1 shared global header** (`components/header.html`)
- **1 shared global footer** (`components/footer.html`)
- **1 global layout system** (`components/layout.html` + `assets/css/custom-style.css`)

Individual pages only provide their own page-specific content within `<main id="main-content" class="falcon-main-layout">` and page-specific `<head>` metadata.

## Core Architecture Components & Templates

1. **Header** (`components/header.html`): Global responsive header with breaking news ticker, live date, social links, theme toggle, desktop navigation with dropdowns, mobile navigation drawer, and live search modal.
2. **Footer** (`components/footer.html`): Global responsive 4-column footer with brand intro, explore category links, company/legal links, featured reads, social icons, copyright, and smooth back-to-top button.
3. **Blog Post Template** (`components/post-template.html`): Single master template used by `scripts/build_posts.py` to compile all 155 single blog posts from `content/posts/*.json`.
4. **Category Template** (`components/archive-template.html`): Single master archive template used by `scripts/build_archives.py` to compile all 19 category archives in `category/<slug>/`.
5. **Tag Template** (`components/archive-template.html`): Used by `scripts/build_archives.py` to compile all 136 tag archives across 160 paginated pages in `tag/<slug>/`.
6. **Author Template** (`components/archive-template.html`): Used by `scripts/build_archives.py` to compile all 3 author hubs across 14 paginated pages in `author/<slug>/`.
7. **Blog Archive Template** (`components/archive-template.html`): Used by `scripts/build_archives.py` to compile `blogs/index.html` and 12 paginated pages in `blogs/page/<n>/`.
8. **Search Results Template** (`search/index.html` & `components/search-result-card.html`): Unified search interface powered by `assets/js/search-page.js` with client-side indexing and `noindex, follow` directives.
9. **Standard Page Layout** (`components/layout.html` & `assets/css/page.css`): Shared layout for informational pages (`pages/contact-us`, `pages/privacy-policy`, `pages/team`, `pages/write-for-us`, and `404.html`).
10. **Breadcrumbs** (`components/breadcrumbs.html` & `scripts/components.py:render_breadcrumbs()`): Standardized accessible breadcrumb navigation across posts, archives, and standard pages.
11. **Pagination** (`components/pagination.html` & `scripts/components.py:render_pagination()`): Standardized crawlable page navigation across all blog, tag, and author archives.
12. **Article Cards** (`components/article-card.html` & `scripts/components.py:render_article_card()`): Reusable article cards with thumbnail, category badge, title, excerpt, and author/date/read-time metadata.

## Blog Post Architecture & Content Storage

To eliminate layout duplication across articles:
- **Master Template**: `components/post-template.html` defines the layout, dynamic SEO tags, schema structured data, reading progress bar, table of contents, article meta row, author box, social sharing bar, post pagination (prev/next), related articles grid, and sticky sidebar.
- **Content Store**: Post data and body HTML are stored cleanly in `content/posts/<slug>.json`.
- **Dynamic SEO per Article**:
  - Meta title, description, robots directives
  - Canonical URL (`https://thefitnessfalcon.com/blogs/<slug>/`)
  - Open Graph tags (`og:type="article"`, `og:title`, `og:description`, `og:url`, `og:image`, `article:published_time`, `article:modified_time`, `article:author`, `article:section`)
  - Twitter card tags (`twitter:card="summary_large_image"`)
  - Schema.org JSON-LD structured data (`BlogPosting` and `BreadcrumbList`)
- **Rich Elements Support**:
  - Automatic Table of Contents (`.falcon-toc`) for articles with 3+ headings
  - Responsive tables wrapped in `.falcon-table-wrapper` with mobile horizontal scroll
  - Styled quotes (`blockquote`), video embeds (`.falcon-video-wrapper`), and captions
  - Social sharing toolbar with instant clipboard copy for article URL
  - Contextual Related Articles (3 cards by category) & Chronological Previous/Next post pagination
  - Sticky sidebar with recent posts, category counts, and newsletter subscription

## Build and Post Management

To compile and propagate changes across all pages and blog posts:
```sh
# 1. Compile all posts and propagate global header/footer
python3 scripts/build.py

# 2. Verify all routes, references, and search entries (must be 0 errors)
python3 scripts/check_site.py

# 3. Create a new future blog article
python3 scripts/new_post.py --title "New Health Guide" --category "Health" --author "Dinesh"
```

